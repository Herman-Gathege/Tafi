"""Small factories shared by the auth and tenancy tests."""

from datetime import timedelta

from sqlalchemy.orm import Session

from app.core.clock import utcnow
from app.core.security import generate_token, hash_password, hash_token
from app.models.invitation import Invitation
from app.models.organization import Organization, OrganizationType
from app.models.user import Membership, MembershipRole, User

PASSWORD = "correct-horse-battery"


def make_user(
    db: Session,
    email: str,
    *,
    password: str = PASSWORD,
    name: str = "Test Person",
    platform_admin: bool = False,
) -> User:
    user = User(
        email=email,
        name=name,
        password_hash=hash_password(password),
        is_platform_admin=platform_admin,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def make_organization(
    db: Session, name: str = "Riverside Academy", type_: OrganizationType = OrganizationType.SCHOOL
) -> Organization:
    organization = Organization(name=name, type=type_)
    db.add(organization)
    db.commit()
    db.refresh(organization)
    return organization


def make_membership(
    db: Session,
    user: User,
    organization: Organization,
    role: MembershipRole = MembershipRole.SCHOOL_ADMIN,
) -> Membership:
    membership = Membership(user_id=user.id, organization_id=organization.id, role=role)
    db.add(membership)
    db.commit()
    db.refresh(membership)
    return membership


def make_invitation(
    db: Session, organization: Organization, email: str, *, expired: bool = False
) -> tuple[Invitation, str]:
    token = generate_token()
    invitation = Invitation(
        organization_id=organization.id,
        email=email,
        role=MembershipRole.SCHOOL_ADMIN,
        token_hash=hash_token(token),
        expires_at=utcnow() + (timedelta(days=-1) if expired else timedelta(days=7)),
    )
    db.add(invitation)
    db.commit()
    db.refresh(invitation)
    return invitation, token
