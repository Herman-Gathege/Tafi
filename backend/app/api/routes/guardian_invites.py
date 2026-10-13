"""The guardian's side of the invite link: public, no account (S3-05, D-22).

The token is the only credential. It is single-use, expires, and shows the holder only their
own details and their own children — never another guardian.
"""

import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import DbSession
from app.api.routes.school_students import current_routes, set_primary
from app.core.clock import is_expired, utcnow
from app.core.security import hash_token
from app.models.guardian import (
    ConsentMethod,
    Guardian,
    GuardianInvite,
    GuardianStatus,
    StudentGuardian,
)
from app.models.organization import Organization
from app.models.student import EmergencyContact, Student, StudentStatus
from app.models.transport import Stop, StopChangeRequest
from app.schemas.guardian_invites import (
    GuardianConfirm,
    GuardianConfirmed,
    GuardianInvitePreview,
    InvitedChild,
    SecondGuardian,
)
from app.schemas.students import StopBrief
from app.services.consent import CONSENT_VERSION, consent_text, record_consent

router = APIRouter(prefix="/api/v1/guardian-invites", tags=["guardian invites"])

UNPROCESSABLE = 422
LINK_NOT_VALID = "This link is not valid any more. Ask the school to send you a new one."


def load_invite(db: Session, token: str) -> tuple[GuardianInvite, Guardian, Organization]:
    invite = db.scalar(select(GuardianInvite).where(GuardianInvite.token_hash == hash_token(token)))
    if invite is None or invite.used_at is not None or is_expired(invite.expires_at):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, LINK_NOT_VALID)
    guardian = db.get(Guardian, invite.guardian_id)
    organization = db.get(Organization, invite.organization_id)
    if guardian is None or organization is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, LINK_NOT_VALID)
    return invite, guardian, organization


def children_of(db: Session, guardian: Guardian) -> list[Student]:
    """The guardian's active children."""
    return list(
        db.scalars(
            select(Student)
            .join(StudentGuardian, StudentGuardian.student_id == Student.id)
            .where(
                StudentGuardian.guardian_id == guardian.id,
                Student.status == StudentStatus.ACTIVE,
            )
            .order_by(Student.first_name)
        )
    )


@router.get("/{token}", response_model=GuardianInvitePreview)
def preview(token: str, db: DbSession) -> GuardianInvitePreview:
    """What the registration page shows."""
    _, guardian, organization = load_invite(db, token)
    children = children_of(db, guardian)
    routes = current_routes(db, [child.id for child in children])
    route_ids = {route.route_id for route in routes.values()}
    stops_by_route: dict[uuid.UUID, list[StopBrief]] = {route_id: [] for route_id in route_ids}
    for stop in db.scalars(
        select(Stop).where(Stop.route_id.in_(route_ids)).order_by(Stop.sequence)
    ):
        stops_by_route[stop.route_id].append(
            StopBrief(id=stop.id, name=stop.name, sequence=stop.sequence)
        )
    return GuardianInvitePreview(
        school_name=organization.name,
        full_name=guardian.full_name,
        whatsapp_number=guardian.whatsapp_number,
        email=guardian.email,
        children=[
            InvitedChild(
                id=child.id,
                first_name=child.first_name,
                last_name=child.last_name,
                grade=child.grade,
                route=routes.get(child.id),
                stops_on_route=(
                    stops_by_route[routes[child.id].route_id] if child.id in routes else []
                ),
            )
            for child in children
        ],
        consent_version=CONSENT_VERSION,
        consent_text=consent_text(organization.name),
    )


def add_second_guardian(
    db: Session, guardian: Guardian, children: list[Student], data: SecondGuardian
) -> None:
    """Link another guardian to every one of this guardian's children. They get their own link."""
    if data.whatsapp_number == guardian.whatsapp_number:
        raise HTTPException(UNPROCESSABLE, "The second guardian needs their own WhatsApp number")
    other = db.scalar(
        select(Guardian).where(
            Guardian.organization_id == guardian.organization_id,
            Guardian.whatsapp_number == data.whatsapp_number,
        )
    )
    if other is None:
        other = Guardian(
            organization_id=guardian.organization_id,
            full_name=data.full_name,
            whatsapp_number=data.whatsapp_number,
        )
        db.add(other)
        db.flush()
    for child in children:
        linked = db.scalar(
            select(StudentGuardian).where(
                StudentGuardian.student_id == child.id, StudentGuardian.guardian_id == other.id
            )
        )
        if linked is None:
            link = StudentGuardian(
                organization_id=guardian.organization_id,
                student_id=child.id,
                guardian_id=other.id,
                relationship=data.relationship,
                is_primary=False,
                receives_messages=True,
            )
            db.add(link)
            db.flush()
            has_primary = db.scalar(
                select(StudentGuardian.id).where(
                    StudentGuardian.student_id == child.id, StudentGuardian.is_primary.is_(True)
                )
            )
            if has_primary is None:
                set_primary(db, child.id, link)


@router.post("/{token}/confirm", response_model=GuardianConfirmed)
def confirm(token: str, payload: GuardianConfirm, db: DbSession) -> GuardianConfirmed:
    """Confirm details and agree to messages. Uses up the link."""
    invite, guardian, organization = load_invite(db, token)
    if payload.consent_version != CONSENT_VERSION:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "The wording you agreed to has changed. Reload the page and read it again.",
        )
    children = children_of(db, guardian)
    child_ids = {child.id for child in children}
    routes = current_routes(db, list(child_ids))

    named = [c.student_id for c in payload.emergency_contacts] + [
        c.student_id for c in payload.stop_changes
    ]
    if any(student_id not in child_ids for student_id in named):
        raise HTTPException(UNPROCESSABLE, "That child is not linked to you")
    for change in payload.stop_changes:
        if change.requested_stop_id is not None:
            stop = db.get(Stop, change.requested_stop_id)
            route = routes.get(change.student_id)
            if stop is None or route is None or stop.route_id != route.route_id:
                raise HTTPException(UNPROCESSABLE, "Choose a stop on your child's route")

    guardian.full_name = payload.full_name
    guardian.email = payload.email
    guardian.status = GuardianStatus.CONFIRMED
    record_consent(db, guardian, method=ConsentMethod.INVITE_LINK, version=payload.consent_version)
    if payload.second_guardian is not None:
        add_second_guardian(db, guardian, children, payload.second_guardian)
    for contact in payload.emergency_contacts:
        db.add(
            EmergencyContact(
                organization_id=guardian.organization_id,
                student_id=contact.student_id,
                name=contact.name,
                phone=contact.phone,
                relationship=contact.relationship or None,
            )
        )
    for change in payload.stop_changes:
        db.add(
            StopChangeRequest(
                organization_id=guardian.organization_id,
                student_id=change.student_id,
                guardian_id=guardian.id,
                requested_stop_id=change.requested_stop_id,
                requested_location=change.requested_location,
            )
        )
    invite.used_at = utcnow()
    db.commit()
    return GuardianConfirmed(
        message="Thank you. You will now get WhatsApp updates about your child's trips.",
        school_name=organization.name,
    )
