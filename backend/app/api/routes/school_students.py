"""A school's children, their guardians and emergency contacts (Sprint 3: S3-03, S3-04).

Rules (D-22):
- An active child always has at least one guardian, and exactly one primary guardian.
- A guardian is one person per WhatsApp number per school: a second child with the same number
  is linked to the existing guardian, never copied.
- The school can correct a guardian's details until the guardian confirms them; after that the
  guardian owns them.

Route assignment (S3-09): a child has at most one current route. Changes take effect today
(Kenya time). Moving to another route ends the current assignment and keeps it as history.
"""

import uuid
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, aliased

from app.api.deps import DbSession, SchoolAdmin, get_owned_or_404
from app.models.guardian import Guardian, GuardianStatus, StudentGuardian
from app.models.student import EmergencyContact, Student, StudentStatus
from app.models.transport import Route, Stop, StudentRouteAssignment
from app.models.user import Membership
from app.schemas.students import (
    ChildBrief,
    CurrentRoute,
    EmergencyContactCreate,
    EmergencyContactRead,
    EmergencyContactUpdate,
    GuardianInput,
    GuardianLinkUpdate,
    GuardianRead,
    GuardianUpdate,
    LinkedGuardian,
    RouteAssignmentRead,
    RouteAssignmentSet,
    StopBrief,
    StudentCreate,
    StudentDetail,
    StudentSummary,
    StudentUpdate,
)

router = APIRouter(prefix="/api/v1/school", tags=["school"])

# Written as a number: Starlette renamed the 422 constant, and both spellings exist in the wild.
UNPROCESSABLE = 422

# Kenya is UTC+3 all year (no daylight saving), so a fixed offset needs no time-zone database.
SCHOOL_TIMEZONE = timezone(timedelta(hours=3), "EAT")


def today() -> date:
    """The school's date. Pilot schools are in Kenya; make this per-school if that changes."""
    return datetime.now(SCHOOL_TIMEZONE).date()


# --- Helpers --------------------------------------------------------------------------------


def guardians_by_student(
    db: Session, student_ids: list[uuid.UUID]
) -> dict[uuid.UUID, list[LinkedGuardian]]:
    """Every child's guardians in one query: primary first, then oldest link first."""
    grouped: dict[uuid.UUID, list[LinkedGuardian]] = defaultdict(list)
    if not student_ids:
        return grouped
    rows = db.execute(
        select(StudentGuardian, Guardian)
        .join(Guardian, Guardian.id == StudentGuardian.guardian_id)
        .where(StudentGuardian.student_id.in_(student_ids))
        .order_by(StudentGuardian.is_primary.desc(), StudentGuardian.created_at)
    ).all()
    for link, guardian in rows:
        grouped[link.student_id].append(
            LinkedGuardian(
                guardian_id=guardian.id,
                full_name=guardian.full_name,
                whatsapp_number=guardian.whatsapp_number,
                email=guardian.email,
                status=guardian.status,
                relationship=link.relationship,
                is_primary=link.is_primary,
                receives_messages=link.receives_messages,
            )
        )
    return grouped


def current_routes(db: Session, student_ids: list[uuid.UUID]) -> dict[uuid.UUID, CurrentRoute]:
    """Every child's current route and stops, in one query."""
    if not student_ids:
        return {}
    pickup = aliased(Stop)
    dropoff = aliased(Stop)
    rows = db.execute(
        select(StudentRouteAssignment, Route, pickup, dropoff)
        .join(Route, Route.id == StudentRouteAssignment.route_id)
        .outerjoin(pickup, pickup.id == StudentRouteAssignment.pickup_stop_id)
        .outerjoin(dropoff, dropoff.id == StudentRouteAssignment.dropoff_stop_id)
        .where(
            StudentRouteAssignment.student_id.in_(student_ids),
            StudentRouteAssignment.active_to.is_(None),
        )
    ).all()

    def brief(stop: Stop | None) -> StopBrief | None:
        return StopBrief(id=stop.id, name=stop.name, sequence=stop.sequence) if stop else None

    return {
        assignment.student_id: CurrentRoute(
            route_id=route.id,
            route_code=route.code,
            route_name=route.name,
            pickup_stop=brief(pickup_stop),
            dropoff_stop=brief(dropoff_stop),
            active_from=assignment.active_from,
        )
        for assignment, route, pickup_stop, dropoff_stop in rows
    }


def current_assignment(db: Session, student_id: uuid.UUID) -> StudentRouteAssignment | None:
    return db.scalar(
        select(StudentRouteAssignment).where(
            StudentRouteAssignment.student_id == student_id,
            StudentRouteAssignment.active_to.is_(None),
        )
    )


def end_assignment(db: Session, assignment: StudentRouteAssignment) -> None:
    """Close an assignment today. One that started today leaves no history worth keeping."""
    if assignment.active_from >= today():
        db.delete(assignment)
    else:
        assignment.active_to = today()
    db.flush()


def student_detail(db: Session, student: Student) -> StudentDetail:
    contacts = db.scalars(
        select(EmergencyContact)
        .where(EmergencyContact.student_id == student.id)
        .order_by(EmergencyContact.created_at)
    )
    return StudentDetail(
        id=student.id,
        first_name=student.first_name,
        last_name=student.last_name,
        grade=student.grade,
        status=student.status,
        guardians=guardians_by_student(db, [student.id])[student.id],
        route=current_routes(db, [student.id]).get(student.id),
        emergency_contacts=[EmergencyContactRead.model_validate(c) for c in contacts],
    )


def links_of(db: Session, student_id: uuid.UUID) -> list[StudentGuardian]:
    return list(
        db.scalars(
            select(StudentGuardian)
            .where(StudentGuardian.student_id == student_id)
            .order_by(StudentGuardian.created_at)
        )
    )


def find_or_create_guardian(db: Session, admin: Membership, data: GuardianInput) -> Guardian:
    """One guardian per number per school. An existing guardian keeps their own details."""
    guardian = db.scalar(
        select(Guardian).where(
            Guardian.organization_id == admin.organization_id,
            Guardian.whatsapp_number == data.whatsapp_number,
        )
    )
    if guardian is None:
        guardian = Guardian(
            organization_id=admin.organization_id,
            full_name=data.full_name,
            whatsapp_number=data.whatsapp_number,
            email=data.email,
        )
        db.add(guardian)
        db.flush()
    return guardian


def set_primary(db: Session, student_id: uuid.UUID, primary: StudentGuardian) -> None:
    for link in links_of(db, student_id):
        link.is_primary = link.id == primary.id


def link_guardian(
    db: Session, admin: Membership, student: Student, data: GuardianInput
) -> StudentGuardian:
    guardian = find_or_create_guardian(db, admin, data)
    existing = db.scalar(
        select(StudentGuardian).where(
            StudentGuardian.student_id == student.id,
            StudentGuardian.guardian_id == guardian.id,
        )
    )
    if existing is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT, f"{guardian.full_name} is already linked to this child"
        )
    link = StudentGuardian(
        organization_id=admin.organization_id,
        student_id=student.id,
        guardian_id=guardian.id,
        relationship=data.relationship,
        is_primary=False,
        receives_messages=data.receives_messages,
    )
    db.add(link)
    db.flush()
    if data.is_primary or not any(other.is_primary for other in links_of(db, student.id)):
        set_primary(db, student.id, link)
    return link


def student_link(db: Session, student: Student, guardian_id: uuid.UUID) -> StudentGuardian:
    link = db.scalar(
        select(StudentGuardian).where(
            StudentGuardian.student_id == student.id,
            StudentGuardian.guardian_id == guardian_id,
        )
    )
    if link is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "That guardian is not linked to this child")
    return link


# --- Students -------------------------------------------------------------------------------


@router.get("/students", response_model=list[StudentSummary])
def list_students(
    admin: SchoolAdmin,
    db: DbSession,
    q: Annotated[str | None, Query(max_length=100)] = None,
    student_status: Annotated[StudentStatus | None, Query(alias="status")] = None,
    route_id: uuid.UUID | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 200,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[StudentSummary]:
    """Children in the school.

    `q` searches child names, guardian names and numbers; `route_id` keeps the children who
    ride that route now.
    """
    query = select(Student).where(Student.organization_id == admin.organization_id)
    if student_status is not None:
        query = query.where(Student.status == student_status)
    if route_id is not None:
        query = query.where(
            Student.id.in_(
                select(StudentRouteAssignment.student_id).where(
                    StudentRouteAssignment.route_id == route_id,
                    StudentRouteAssignment.active_to.is_(None),
                )
            )
        )
    if q and q.strip():
        like = f"%{q.strip()}%"
        digits = "".join(character for character in q if character.isdigit()).lstrip("0")
        guardian_match = [Guardian.full_name.ilike(like)]
        if digits:
            guardian_match.append(Guardian.whatsapp_number.like(f"%{digits}%"))
        matching_students = (
            select(StudentGuardian.student_id)
            .join(Guardian, Guardian.id == StudentGuardian.guardian_id)
            .where(or_(*guardian_match))
        )
        query = query.where(
            or_(
                (Student.first_name + " " + Student.last_name).ilike(like),
                Student.id.in_(matching_students),
            )
        )
    students = list(
        db.scalars(
            query.order_by(Student.last_name, Student.first_name).limit(limit).offset(offset)
        )
    )
    ids = [student.id for student in students]
    guardians = guardians_by_student(db, ids)
    routes = current_routes(db, ids)
    return [
        StudentSummary(
            id=student.id,
            first_name=student.first_name,
            last_name=student.last_name,
            grade=student.grade,
            status=student.status,
            guardians=guardians[student.id],
            route=routes.get(student.id),
        )
        for student in students
    ]


@router.post("/students", response_model=StudentDetail, status_code=status.HTTP_201_CREATED)
def create_student(payload: StudentCreate, admin: SchoolAdmin, db: DbSession) -> StudentDetail:
    student = Student(
        organization_id=admin.organization_id,
        first_name=payload.first_name,
        last_name=payload.last_name,
        grade=payload.grade or None,
    )
    db.add(student)
    db.flush()
    for guardian in payload.guardians:
        link_guardian(db, admin, student, guardian)
    db.commit()
    db.refresh(student)
    return student_detail(db, student)


@router.get("/students/{student_id}", response_model=StudentDetail)
def read_student(student_id: uuid.UUID, admin: SchoolAdmin, db: DbSession) -> StudentDetail:
    student = get_owned_or_404(db, Student, student_id, admin, what="child")
    return student_detail(db, student)


@router.patch("/students/{student_id}", response_model=StudentDetail)
def update_student(
    student_id: uuid.UUID, payload: StudentUpdate, admin: SchoolAdmin, db: DbSession
) -> StudentDetail:
    student = get_owned_or_404(db, Student, student_id, admin, what="child")
    changes = payload.model_dump(exclude_unset=True)
    if (
        changes.get("status") == StudentStatus.ACTIVE
        and student.status != StudentStatus.ACTIVE
        and not links_of(db, student.id)
    ):
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Add a guardian before making this child active again"
        )
    for field in ("first_name", "last_name", "status"):
        if changes.get(field) is not None:
            setattr(student, field, changes[field])
    if "grade" in changes:
        student.grade = changes["grade"] or None
    if changes.get("status") == StudentStatus.INACTIVE:
        assignment = current_assignment(db, student.id)
        if assignment is not None:
            end_assignment(db, assignment)
    db.commit()
    db.refresh(student)
    return student_detail(db, student)


# --- A child's guardians --------------------------------------------------------------------


@router.post(
    "/students/{student_id}/guardians",
    response_model=StudentDetail,
    status_code=status.HTTP_201_CREATED,
)
def add_guardian(
    student_id: uuid.UUID, payload: GuardianInput, admin: SchoolAdmin, db: DbSession
) -> StudentDetail:
    student = get_owned_or_404(db, Student, student_id, admin, what="child")
    link_guardian(db, admin, student, payload)
    db.commit()
    return student_detail(db, student)


@router.patch("/students/{student_id}/guardians/{guardian_id}", response_model=StudentDetail)
def update_guardian_link(
    student_id: uuid.UUID,
    guardian_id: uuid.UUID,
    payload: GuardianLinkUpdate,
    admin: SchoolAdmin,
    db: DbSession,
) -> StudentDetail:
    student = get_owned_or_404(db, Student, student_id, admin, what="child")
    link = student_link(db, student, guardian_id)
    changes = payload.model_dump(exclude_unset=True)
    if changes.get("is_primary") is False and link.is_primary:
        raise HTTPException(
            UNPROCESSABLE, "Make another guardian primary instead; a child always has one"
        )
    if changes.get("relationship") is not None:
        link.relationship = changes["relationship"]
    if changes.get("receives_messages") is not None:
        link.receives_messages = changes["receives_messages"]
    if changes.get("is_primary"):
        set_primary(db, student.id, link)
    db.commit()
    return student_detail(db, student)


@router.delete("/students/{student_id}/guardians/{guardian_id}", response_model=StudentDetail)
def remove_guardian_link(
    student_id: uuid.UUID, guardian_id: uuid.UUID, admin: SchoolAdmin, db: DbSession
) -> StudentDetail:
    """Unlink a guardian from a child. The guardian's record (and consent history) stays."""
    student = get_owned_or_404(db, Student, student_id, admin, what="child")
    link = student_link(db, student, guardian_id)
    remaining = [other for other in links_of(db, student.id) if other.id != link.id]
    if student.status == StudentStatus.ACTIVE and not remaining:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "An active child needs at least one guardian. Add another guardian first.",
        )
    was_primary = link.is_primary
    db.delete(link)
    db.flush()
    if was_primary and remaining:
        set_primary(db, student.id, remaining[0])
    db.commit()
    return student_detail(db, student)


# --- A child's route (S3-09) ----------------------------------------------------------------


@router.put("/students/{student_id}/route", response_model=StudentDetail)
def set_route(
    student_id: uuid.UUID, payload: RouteAssignmentSet, admin: SchoolAdmin, db: DbSession
) -> StudentDetail:
    """Put a child on a route with their stops, or move them. Takes effect today."""
    student = get_owned_or_404(db, Student, student_id, admin, what="child")
    if student.status != StudentStatus.ACTIVE:
        raise HTTPException(status.HTTP_409_CONFLICT, "Make this child active first")
    route = get_owned_or_404(db, Route, payload.route_id, admin, what="route")
    if not route.is_active:
        raise HTTPException(UNPROCESSABLE, f"Route {route.code} is not running")
    for stop_id in (payload.pickup_stop_id, payload.dropoff_stop_id):
        if stop_id is not None:
            stop = get_owned_or_404(db, Stop, stop_id, admin, what="stop")
            if stop.route_id != route.id:
                raise HTTPException(UNPROCESSABLE, f"{stop.name} is not on route {route.code}")

    current = current_assignment(db, student.id)
    if current is not None and current.route_id == route.id:
        # Same route, different stops: no new history.
        current.pickup_stop_id = payload.pickup_stop_id
        current.dropoff_stop_id = payload.dropoff_stop_id
    else:
        if current is not None:
            end_assignment(db, current)
        db.add(
            StudentRouteAssignment(
                organization_id=admin.organization_id,
                student_id=student.id,
                route_id=route.id,
                pickup_stop_id=payload.pickup_stop_id,
                dropoff_stop_id=payload.dropoff_stop_id,
                active_from=today(),
            )
        )
    db.commit()
    return student_detail(db, student)


@router.delete("/students/{student_id}/route", response_model=StudentDetail)
def remove_from_route(student_id: uuid.UUID, admin: SchoolAdmin, db: DbSession) -> StudentDetail:
    """Take a child off school transport from today."""
    student = get_owned_or_404(db, Student, student_id, admin, what="child")
    current = current_assignment(db, student.id)
    if current is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "This child is not on a route")
    end_assignment(db, current)
    db.commit()
    return student_detail(db, student)


@router.get("/students/{student_id}/route-history", response_model=list[RouteAssignmentRead])
def route_history(
    student_id: uuid.UUID, admin: SchoolAdmin, db: DbSession
) -> list[RouteAssignmentRead]:
    """Every route the child has been on, newest first."""
    student = get_owned_or_404(db, Student, student_id, admin, what="child")
    rows = db.execute(
        select(StudentRouteAssignment, Route)
        .join(Route, Route.id == StudentRouteAssignment.route_id)
        .where(StudentRouteAssignment.student_id == student.id)
        .order_by(StudentRouteAssignment.active_from.desc())
    ).all()
    return [
        RouteAssignmentRead(
            route_id=route.id,
            route_code=route.code,
            route_name=route.name,
            pickup_stop_id=assignment.pickup_stop_id,
            dropoff_stop_id=assignment.dropoff_stop_id,
            active_from=assignment.active_from,
            active_to=assignment.active_to,
        )
        for assignment, route in rows
    ]


# --- Emergency contacts ---------------------------------------------------------------------


@router.post(
    "/students/{student_id}/emergency-contacts",
    response_model=StudentDetail,
    status_code=status.HTTP_201_CREATED,
)
def add_emergency_contact(
    student_id: uuid.UUID, payload: EmergencyContactCreate, admin: SchoolAdmin, db: DbSession
) -> StudentDetail:
    student = get_owned_or_404(db, Student, student_id, admin, what="child")
    db.add(
        EmergencyContact(
            organization_id=admin.organization_id,
            student_id=student.id,
            name=payload.name,
            phone=payload.phone,
            relationship=payload.relationship or None,
        )
    )
    db.commit()
    return student_detail(db, student)


@router.patch("/emergency-contacts/{contact_id}", response_model=StudentDetail)
def update_emergency_contact(
    contact_id: uuid.UUID, payload: EmergencyContactUpdate, admin: SchoolAdmin, db: DbSession
) -> StudentDetail:
    contact = get_owned_or_404(db, EmergencyContact, contact_id, admin, what="emergency contact")
    changes = payload.model_dump(exclude_unset=True)
    for field in ("name", "phone"):
        if changes.get(field) is not None:
            setattr(contact, field, changes[field])
    if "relationship" in changes:
        contact.relationship = changes["relationship"] or None
    db.commit()
    student = get_owned_or_404(db, Student, contact.student_id, admin, what="child")
    return student_detail(db, student)


@router.delete("/emergency-contacts/{contact_id}", response_model=StudentDetail)
def remove_emergency_contact(
    contact_id: uuid.UUID, admin: SchoolAdmin, db: DbSession
) -> StudentDetail:
    contact = get_owned_or_404(db, EmergencyContact, contact_id, admin, what="emergency contact")
    student = get_owned_or_404(db, Student, contact.student_id, admin, what="child")
    db.delete(contact)
    db.commit()
    return student_detail(db, student)


# --- Guardians ------------------------------------------------------------------------------


def guardian_read(db: Session, guardians: list[Guardian]) -> list[GuardianRead]:
    children: dict[uuid.UUID, list[ChildBrief]] = defaultdict(list)
    if guardians:
        rows = db.execute(
            select(StudentGuardian.guardian_id, Student)
            .join(Student, Student.id == StudentGuardian.student_id)
            .where(StudentGuardian.guardian_id.in_([guardian.id for guardian in guardians]))
            .order_by(Student.first_name)
        ).all()
        for guardian_id, student in rows:
            children[guardian_id].append(
                ChildBrief(
                    id=student.id, first_name=student.first_name, last_name=student.last_name
                )
            )
    return [
        GuardianRead(
            id=guardian.id,
            full_name=guardian.full_name,
            whatsapp_number=guardian.whatsapp_number,
            email=guardian.email,
            status=guardian.status,
            children=children[guardian.id],
        )
        for guardian in guardians
    ]


@router.get("/guardians", response_model=list[GuardianRead])
def list_guardians(
    admin: SchoolAdmin,
    db: DbSession,
    q: Annotated[str | None, Query(max_length=100)] = None,
    guardian_status: Annotated[GuardianStatus | None, Query(alias="status")] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 200,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[GuardianRead]:
    """Guardians in the school, e.g. `?status=invited` for those still to confirm."""
    query = select(Guardian).where(Guardian.organization_id == admin.organization_id)
    if guardian_status is not None:
        query = query.where(Guardian.status == guardian_status)
    if q and q.strip():
        digits = "".join(character for character in q if character.isdigit()).lstrip("0")
        conditions = [Guardian.full_name.ilike(f"%{q.strip()}%")]
        if digits:
            conditions.append(Guardian.whatsapp_number.like(f"%{digits}%"))
        query = query.where(or_(*conditions))
    guardians = list(db.scalars(query.order_by(Guardian.full_name).limit(limit).offset(offset)))
    return guardian_read(db, guardians)


@router.get("/guardians/{guardian_id}", response_model=GuardianRead)
def read_guardian(guardian_id: uuid.UUID, admin: SchoolAdmin, db: DbSession) -> GuardianRead:
    guardian = get_owned_or_404(db, Guardian, guardian_id, admin, what="guardian")
    return guardian_read(db, [guardian])[0]


@router.patch("/guardians/{guardian_id}", response_model=GuardianRead)
def update_guardian(
    guardian_id: uuid.UUID, payload: GuardianUpdate, admin: SchoolAdmin, db: DbSession
) -> GuardianRead:
    guardian = get_owned_or_404(db, Guardian, guardian_id, admin, what="guardian")
    if guardian.status == GuardianStatus.CONFIRMED:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "This guardian has confirmed their details. Ask them to update them from their link.",
        )
    changes = payload.model_dump(exclude_unset=True)
    number = changes.get("whatsapp_number")
    if number is not None and number != guardian.whatsapp_number:
        taken = db.scalar(
            select(Guardian.id).where(
                Guardian.organization_id == admin.organization_id,
                Guardian.whatsapp_number == number,
            )
        )
        if taken is not None:
            raise HTTPException(
                status.HTTP_409_CONFLICT, "Another guardian at your school has that number"
            )
    for field in ("full_name", "whatsapp_number"):
        if changes.get(field) is not None:
            setattr(guardian, field, changes[field])
    if "email" in changes:
        guardian.email = changes["email"]
    db.commit()
    db.refresh(guardian)
    return guardian_read(db, [guardian])[0]
