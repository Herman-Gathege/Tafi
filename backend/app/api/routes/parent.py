"""What a parent can see and do for their own children."""

from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import DbSession, ParentGuardian
from app.models.guardian import StudentGuardian
from app.models.organization import Organization
from app.models.student import Student
from app.models.transport import Route, Stop, StopChangeRequest, StudentRouteAssignment
from app.schemas.parent import ParentChild, ParentMe, ParentStopRequest
from app.services.consent import can_message

router = APIRouter(prefix="/api/v1/parent", tags=["parent"])


def _stop_name(db: DbSession, stop_id) -> str | None:
    if stop_id is None:
        return None
    stop = db.get(Stop, stop_id)
    return stop.name if stop else None


@router.get("/me", response_model=ParentMe)
def my_family(guardian: ParentGuardian, db: DbSession) -> ParentMe:
    """The signed-in parent's own children only — never another family's (D-26)."""
    organization = db.get(Organization, guardian.organization_id)

    children: list[ParentChild] = []
    links = db.scalars(
        select(StudentGuardian).where(StudentGuardian.guardian_id == guardian.id)
    ).all()
    for link in links:
        student = db.get(Student, link.student_id)
        if student is None:
            continue
        assignment = db.scalar(
            select(StudentRouteAssignment).where(
                StudentRouteAssignment.student_id == student.id,
                StudentRouteAssignment.active_to.is_(None),
            )
        )
        route = db.get(Route, assignment.route_id) if assignment else None
        children.append(
            ParentChild(
                student_id=student.id,
                first_name=student.first_name,
                last_name=student.last_name,
                grade=student.grade,
                route_code=route.code if route else None,
                route_name=route.name if route else None,
                pickup_stop=_stop_name(db, assignment.pickup_stop_id) if assignment else None,
                dropoff_stop=_stop_name(db, assignment.dropoff_stop_id) if assignment else None,
            )
        )

    requests = db.scalars(
        select(StopChangeRequest)
        .where(StopChangeRequest.guardian_id == guardian.id)
        .order_by(StopChangeRequest.created_at.desc())
    ).all()

    return ParentMe(
        guardian_id=guardian.id,
        full_name=guardian.full_name,
        whatsapp_number=guardian.whatsapp_number,
        status=guardian.status.value,
        has_consent=can_message(db, guardian),
        school_name=organization.name if organization else "",
        children=children,
        stop_requests=[
            ParentStopRequest(
                id=request.id,
                student_id=request.student_id,
                status=request.status.value,
                requested_at=request.created_at,
            )
            for request in requests
        ],
    )
