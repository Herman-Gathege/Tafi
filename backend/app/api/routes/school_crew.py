"""A school's crew: drivers and conductors (Sprint 3: S3-08, D-21).

School admins invite crew with the same single-use, expiring invitation as Sprint 2 (D-18); the
invitee accepts it at /accept-invite and joins the school with the invited role.
"""

import uuid
from datetime import timedelta

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import DbSession, SchoolAdmin, get_owned_or_404
from app.core.clock import is_expired, utcnow
from app.core.config import get_settings
from app.core.security import generate_token, hash_token
from app.models.invitation import Invitation
from app.models.transport import RouteRun
from app.models.user import CREW_ROLES, Membership, User
from app.schemas.crew import CrewInvitationCreate, CrewInvitationRead, CrewMemberRead, CrewRead

router = APIRouter(prefix="/api/v1/school/crew", tags=["school"])


@router.get("", response_model=CrewRead)
def list_crew(admin: SchoolAdmin, db: DbSession) -> CrewRead:
    """Everyone on the school's crew, and invitations not yet accepted."""
    rows = db.execute(
        select(Membership, User)
        .join(User, User.id == Membership.user_id)
        .where(
            Membership.organization_id == admin.organization_id,
            Membership.role.in_(CREW_ROLES),
        )
        .order_by(User.name)
    ).all()
    invitations = db.scalars(
        select(Invitation)
        .where(
            Invitation.organization_id == admin.organization_id,
            Invitation.role.in_(CREW_ROLES),
            Invitation.accepted_at.is_(None),
        )
        .order_by(Invitation.created_at)
    )
    return CrewRead(
        members=[
            CrewMemberRead(
                membership_id=membership.id,
                name=user.name,
                email=user.email,
                role=membership.role,
                joined_at=membership.created_at,
            )
            for membership, user in rows
        ],
        pending_invitations=[
            CrewInvitationRead(
                id=invitation.id,
                email=invitation.email,
                role=invitation.role,
                expires_at=invitation.expires_at,
            )
            for invitation in invitations
            if not is_expired(invitation.expires_at)
        ],
    )


@router.post("/invitations", response_model=CrewInvitationRead, status_code=status.HTTP_201_CREATED)
def invite_crew(
    payload: CrewInvitationCreate, admin: SchoolAdmin, db: DbSession
) -> CrewInvitationRead:
    """Invite a driver or a conductor. Sending again simply issues a fresh link."""
    settings = get_settings()
    already_member = db.scalar(
        select(Membership.id)
        .join(User, User.id == Membership.user_id)
        .where(Membership.organization_id == admin.organization_id, User.email == payload.email)
    )
    if already_member is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, f"{payload.email} is already at your school")

    token = generate_token()
    invitation = Invitation(
        organization_id=admin.organization_id,
        email=payload.email,
        role=payload.role,
        token_hash=hash_token(token),
        expires_at=utcnow() + timedelta(days=settings.invite_ttl_days),
        invited_by_user_id=admin.user_id,
    )
    db.add(invitation)
    db.commit()
    db.refresh(invitation)

    # Nothing can send email or WhatsApp yet (Sprint 5), so local development gets the link back.
    invite_url = None
    if settings.app_env == "local":
        invite_url = f"{settings.app_public_url}/accept-invite?token={token}"

    return CrewInvitationRead(
        id=invitation.id,
        email=invitation.email,
        role=invitation.role,
        expires_at=invitation.expires_at,
        invite_url=invite_url,
    )


@router.delete("/members/{membership_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_crew_member(membership_id: uuid.UUID, admin: SchoolAdmin, db: DbSession) -> None:
    """Take someone off the crew. A driver who still drives a run must be replaced first."""
    membership = get_owned_or_404(db, Membership, membership_id, admin, what="crew member")
    if membership.role not in CREW_ROLES:
        # School admins are managed by Tafi staff, not from the crew page.
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such crew member")

    driving = db.scalar(
        select(RouteRun.id).where(RouteRun.driver_membership_id == membership.id).limit(1)
    )
    if driving is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "This driver still drives a run. Choose another driver for it first.",
        )
    # A conductor's runs keep going without one (the foreign key sets it to null).
    for run in db.scalars(
        select(RouteRun).where(RouteRun.conductor_membership_id == membership.id)
    ):
        run.conductor_membership_id = None
    db.delete(membership)
    db.commit()
