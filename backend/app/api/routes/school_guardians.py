"""School side of guardian onboarding: invites, consent and stop-change requests (S3-05, S3-06).

Rules (D-22):
- A guardian confirms their details and consents through a single-use, expiring link. A new
  link replaces any earlier unused one.
- The school can record consent given another way (on paper) and record a withdrawal.
- A guardian may ask for a different stop; the school decides.
"""

import uuid
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import DbSession, SchoolAdmin, get_owned_or_404
from app.api.routes.school_students import current_routes, guardian_read, set_route
from app.core.clock import is_expired, utcnow
from app.core.config import get_settings
from app.core.security import generate_token, hash_token
from app.models.guardian import (
    ConsentMethod,
    Guardian,
    GuardianInvite,
    GuardianStatus,
    StudentGuardian,
)
from app.models.student import Student, StudentStatus
from app.models.transport import RequestStatus, Stop, StopChangeRequest
from app.models.user import Membership
from app.schemas.guardian_invites import GuardianInviteRead, StopChangeRequestRead
from app.schemas.students import (
    ChildBrief,
    GuardianRead,
    RouteAssignmentSet,
    StopBrief,
    StudentDetail,
)
from app.services.consent import record_consent, withdraw_consent

router = APIRouter(prefix="/api/v1/school", tags=["school"])


def invite_url(token: str) -> str | None:
    """The link for the guardian. Returned only in `local` until messages can be sent (D-18)."""
    settings = get_settings()
    if settings.app_env != "local":
        return None
    return f"{settings.app_public_url}/guardian-invite?token={token}"


def create_invite(db: Session, admin: Membership, guardian: Guardian) -> GuardianInviteRead:
    """Issue a fresh link and retire any earlier unused one."""
    now = utcnow()
    for earlier in db.scalars(
        select(GuardianInvite).where(
            GuardianInvite.guardian_id == guardian.id, GuardianInvite.used_at.is_(None)
        )
    ):
        if not is_expired(earlier.expires_at):
            earlier.expires_at = now
    token = generate_token()
    invite = GuardianInvite(
        organization_id=admin.organization_id,
        guardian_id=guardian.id,
        token_hash=hash_token(token),
        expires_at=now + timedelta(days=get_settings().invite_ttl_days),
        invited_by_user_id=admin.user_id,
    )
    db.add(invite)
    db.flush()
    return GuardianInviteRead(
        guardian_id=guardian.id,
        full_name=guardian.full_name,
        whatsapp_number=guardian.whatsapp_number,
        expires_at=invite.expires_at,
        invite_url=invite_url(token),
    )


# --- Invites --------------------------------------------------------------------------------


@router.post(
    "/guardians/{guardian_id}/invite",
    response_model=GuardianInviteRead,
    status_code=status.HTTP_201_CREATED,
)
def invite_guardian(
    guardian_id: uuid.UUID, admin: SchoolAdmin, db: DbSession
) -> GuardianInviteRead:
    """Send (or resend) one guardian their link. Confirmed guardians can be sent one to update."""
    guardian = get_owned_or_404(db, Guardian, guardian_id, admin, what="guardian")
    invite = create_invite(db, admin, guardian)
    db.commit()
    return invite


@router.post(
    "/guardians/invite-pending",
    response_model=list[GuardianInviteRead],
    status_code=status.HTTP_201_CREATED,
)
def invite_pending_guardians(admin: SchoolAdmin, db: DbSession) -> list[GuardianInviteRead]:
    """Send a link to every guardian still to confirm who has a child on transport."""
    guardians = db.scalars(
        select(Guardian)
        .where(
            Guardian.organization_id == admin.organization_id,
            Guardian.status == GuardianStatus.INVITED,
            Guardian.id.in_(
                select(StudentGuardian.guardian_id)
                .join(Student, Student.id == StudentGuardian.student_id)
                .where(Student.status == StudentStatus.ACTIVE)
            ),
        )
        .order_by(Guardian.full_name)
    ).all()
    invites = [create_invite(db, admin, guardian) for guardian in guardians]
    db.commit()
    return invites


# --- Consent --------------------------------------------------------------------------------


@router.post("/guardians/{guardian_id}/consent", response_model=GuardianRead)
def record_consent_given_elsewhere(
    guardian_id: uuid.UUID, admin: SchoolAdmin, db: DbSession
) -> GuardianRead:
    """The guardian agreed on paper or in person, to the current wording."""
    guardian = get_owned_or_404(db, Guardian, guardian_id, admin, what="guardian")
    record_consent(
        db, guardian, method=ConsentMethod.SCHOOL_RECORDED, recorded_by_user_id=admin.user_id
    )
    db.commit()
    return guardian_read(db, [guardian])[0]


@router.delete("/guardians/{guardian_id}/consent", response_model=GuardianRead)
def record_withdrawal(guardian_id: uuid.UUID, admin: SchoolAdmin, db: DbSession) -> GuardianRead:
    """The guardian asked to stop the messages. Takes effect at once."""
    guardian = get_owned_or_404(db, Guardian, guardian_id, admin, what="guardian")
    if not withdraw_consent(db, guardian):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "This guardian has not consented")
    db.commit()
    return guardian_read(db, [guardian])[0]


# --- Stop-change requests -------------------------------------------------------------------


def request_reads(db: Session, requests: list[StopChangeRequest]) -> list[StopChangeRequestRead]:
    if not requests:
        return []
    students = {
        student.id: student
        for student in db.scalars(
            select(Student).where(Student.id.in_({r.student_id for r in requests}))
        )
    }
    guardians = {
        guardian.id: guardian
        for guardian in db.scalars(
            select(Guardian).where(Guardian.id.in_({r.guardian_id for r in requests}))
        )
    }
    stop_ids = {r.requested_stop_id for r in requests if r.requested_stop_id is not None}
    stops = {stop.id: stop for stop in db.scalars(select(Stop).where(Stop.id.in_(stop_ids)))}
    routes = current_routes(db, list(students))
    reads = []
    for request in requests:
        student = students[request.student_id]
        stop = stops.get(request.requested_stop_id) if request.requested_stop_id else None
        reads.append(
            StopChangeRequestRead(
                id=request.id,
                student=ChildBrief(
                    id=student.id, first_name=student.first_name, last_name=student.last_name
                ),
                guardian_id=request.guardian_id,
                guardian_name=guardians[request.guardian_id].full_name,
                current_route=routes.get(student.id),
                requested_stop=(
                    StopBrief(id=stop.id, name=stop.name, sequence=stop.sequence) if stop else None
                ),
                requested_location=request.requested_location,
                status=request.status,
                created_at=request.created_at,
                decided_at=request.decided_at,
            )
        )
    return reads


@router.get("/stop-change-requests", response_model=list[StopChangeRequestRead])
def list_stop_change_requests(
    admin: SchoolAdmin,
    db: DbSession,
    request_status: Annotated[RequestStatus | None, Query(alias="status")] = RequestStatus.PENDING,
) -> list[StopChangeRequestRead]:
    """Pending requests by default, oldest first."""
    query = select(StopChangeRequest).where(
        StopChangeRequest.organization_id == admin.organization_id
    )
    if request_status is not None:
        query = query.where(StopChangeRequest.status == request_status)
    return request_reads(db, list(db.scalars(query.order_by(StopChangeRequest.created_at))))


def pending_request(db: Session, admin: Membership, request_id: uuid.UUID) -> StopChangeRequest:
    request = get_owned_or_404(db, StopChangeRequest, request_id, admin, what="request")
    if request.status != RequestStatus.PENDING:
        raise HTTPException(status.HTTP_409_CONFLICT, f"This request was already {request.status}")
    return request


@router.post("/stop-change-requests/{request_id}/approve", response_model=StudentDetail)
def approve_stop_change(
    request_id: uuid.UUID, payload: RouteAssignmentSet, admin: SchoolAdmin, db: DbSession
) -> StudentDetail:
    """Approve by choosing the child's route and stops (the school may add a new stop first)."""
    request = pending_request(db, admin, request_id)
    request.status = RequestStatus.APPROVED
    request.decided_by_user_id = admin.user_id
    request.decided_at = utcnow()
    # set_route validates the route and stops, applies the change and commits.
    return set_route(request.student_id, payload, admin, db)


@router.post("/stop-change-requests/{request_id}/decline", response_model=StopChangeRequestRead)
def decline_stop_change(
    request_id: uuid.UUID, admin: SchoolAdmin, db: DbSession
) -> StopChangeRequestRead:
    request = pending_request(db, admin, request_id)
    request.status = RequestStatus.DECLINED
    request.decided_by_user_id = admin.user_id
    request.decided_at = utcnow()
    db.commit()
    return request_reads(db, [request])[0]
