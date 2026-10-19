"""Shared dependencies: who is calling, and what they are allowed to do."""

import uuid
from typing import Annotated

import jwt
from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import decode_session_token
from app.db.base import Base
from app.db.session import get_db
from app.models.guardian import Guardian
from app.models.organization import OrganizationType
from app.models.user import CREW_ROLES, Membership, MembershipRole, User

DbSession = Annotated[Session, Depends(get_db)]

ORGANIZATION_HEADER = "X-Organization-Id"


def get_current_user(request: Request, db: DbSession) -> User:
    """Resolve the signed-in user from the session cookie."""
    settings = get_settings()
    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not signed in")
    try:
        user_id = decode_session_token(token)
    except (jwt.InvalidTokenError, ValueError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session is no longer valid") from None

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not signed in")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_platform_admin(user: CurrentUser) -> User:
    """Tafi staff only."""
    if not user.is_platform_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Platform admins only")
    return user


PlatformAdmin = Annotated[User, Depends(require_platform_admin)]


def memberships_for(db: Session, user: User) -> list[Membership]:
    """Every tenant the user belongs to, oldest first."""
    return list(
        db.scalars(
            select(Membership).where(Membership.user_id == user.id).order_by(Membership.created_at)
        )
    )


def get_current_membership(
    user: CurrentUser,
    db: DbSession,
    x_organization_id: Annotated[uuid.UUID | None, Header()] = None,
) -> Membership:
    """The tenant this request acts in.

    One membership: that one. Several: the client names one in the `X-Organization-Id` header.
    The header can only pick a tenant the caller already belongs to; it never grants access.
    """
    memberships = memberships_for(db, user)
    if x_organization_id is not None:
        for membership in memberships:
            if membership.organization_id == x_organization_id:
                return membership
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You do not belong to that organization")

    if not memberships:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You do not belong to an organization yet")
    if len(memberships) > 1:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"You belong to more than one organization: choose one with {ORGANIZATION_HEADER}",
        )
    return memberships[0]


CurrentMembership = Annotated[Membership, Depends(get_current_membership)]


def require_school_admin(membership: CurrentMembership) -> Membership:
    """A school admin, acting in a school. Every Sprint 3 school-data route uses this."""
    if (
        membership.role != MembershipRole.SCHOOL_ADMIN
        or membership.organization.type != OrganizationType.SCHOOL
    ):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "School admins only")
    return membership


SchoolAdmin = Annotated[Membership, Depends(require_school_admin)]


def require_crew(membership: CurrentMembership) -> Membership:
    """A driver or conductor (D-21). Used by the crew app from Sprint 4."""
    if membership.role not in CREW_ROLES:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Drivers and conductors only")
    return membership


Crew = Annotated[Membership, Depends(require_crew)]


def require_parent(membership: CurrentMembership, db: DbSession) -> Guardian:
    """A guardian who has been given a login, resolved to their guardian record."""
    if membership.role != MembershipRole.PARENT:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Parents only")
    guardian = db.scalar(select(Guardian).where(Guardian.user_id == membership.user_id))
    if guardian is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "No guardian record for this account")
    return guardian


ParentGuardian = Annotated[Guardian, Depends(require_parent)]


def get_owned_or_404[ModelT: Base](
    db: Session,
    model: type[ModelT],
    row_id: uuid.UUID,
    membership: Membership,
    *,
    what: str,
) -> ModelT:
    """Load a row only if it belongs to the caller's organization.

    Another school's row is reported as missing (404), not forbidden, so ids cannot be probed.
    Use this for every id that arrives in a path or a payload.
    """
    row = db.get(model, row_id)
    if row is None or getattr(row, "organization_id", None) != membership.organization_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"No such {what}")
    return row
