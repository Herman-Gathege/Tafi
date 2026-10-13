"""Organizations (tenants): onboarding for Tafi staff, and one school's own record."""

import uuid
from datetime import timedelta

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession, PlatformAdmin, memberships_for
from app.core.clock import utcnow
from app.core.config import get_settings
from app.core.security import generate_token, hash_token
from app.models.invitation import Invitation
from app.models.organization import Organization
from app.schemas.organization import (
    InvitationCreate,
    InvitationRead,
    OrganizationCreate,
    OrganizationRead,
)

router = APIRouter(prefix="/api/v1/organizations", tags=["organizations"])
tenant_router = APIRouter(prefix="/api/v1/organization", tags=["organization"])


@router.get("", response_model=list[OrganizationRead])
def list_organizations(admin: PlatformAdmin, db: DbSession) -> list[Organization]:
    """Every tenant on the platform. Tafi staff only."""
    return list(db.scalars(select(Organization).order_by(Organization.created_at)))


@router.post("", response_model=OrganizationRead, status_code=status.HTTP_201_CREATED)
def create_organization(
    payload: OrganizationCreate, admin: PlatformAdmin, db: DbSession
) -> Organization:
    """Onboard a new tenant, before anyone has an account for it."""
    organization = Organization(name=payload.name, type=payload.type)
    db.add(organization)
    db.commit()
    db.refresh(organization)
    return organization


@router.post(
    "/{organization_id}/invitations",
    response_model=InvitationRead,
    status_code=status.HTTP_201_CREATED,
)
def create_invitation(
    organization_id: uuid.UUID,
    payload: InvitationCreate,
    admin: PlatformAdmin,
    db: DbSession,
) -> InvitationRead:
    """Invite the first admin of a school (or a driver, later)."""
    settings = get_settings()
    organization = db.get(Organization, organization_id)
    if organization is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such organization")

    token = generate_token()
    invitation = Invitation(
        organization_id=organization.id,
        email=payload.email,
        role=payload.role,
        token_hash=hash_token(token),
        expires_at=utcnow() + timedelta(days=settings.invite_ttl_days),
        invited_by_user_id=admin.id,
    )
    db.add(invitation)
    db.commit()
    db.refresh(invitation)

    # Nothing can send email yet (Sprint 5), so local development gets the link back.
    invite_url = None
    if settings.app_env == "local":
        invite_url = f"{settings.app_public_url}/accept-invite?token={token}"

    return InvitationRead(
        id=invitation.id,
        email=invitation.email,
        role=invitation.role,
        expires_at=invitation.expires_at,
        invite_url=invite_url,
    )


@tenant_router.get("", response_model=OrganizationRead)
def read_own_organization(user: CurrentUser, db: DbSession) -> Organization:
    """The caller's own tenant. A membership is the only thing that grants access."""
    memberships = memberships_for(db, user)
    if not memberships:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You do not belong to an organization yet")
    organization = db.get(Organization, memberships[0].organization_id)
    if organization is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such organization")
    return organization
