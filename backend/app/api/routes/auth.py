"""Sign in, sign out, invitations and password resets."""

from datetime import timedelta

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, DbSession, memberships_for
from app.core.clock import is_expired, utcnow
from app.core.config import get_settings
from app.core.security import (
    create_session_token,
    generate_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.invitation import Invitation
from app.models.organization import Organization, OrganizationType
from app.models.password_reset import PasswordResetToken
from app.models.user import Membership, MembershipRole, User
from app.schemas.auth import (
    AcceptInviteRequest,
    ForgotPasswordRequest,
    InvitationPreview,
    MembershipRead,
    MessageResponse,
    ResetPasswordRequest,
    SessionRead,
    SignInRequest,
    SignupRequest,
    UserRead,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def build_session(db: Session, user: User) -> SessionRead:
    """The signed-in payload: the person plus every tenant they belong to."""
    return SessionRead(
        user=UserRead.model_validate(user),
        memberships=[
            MembershipRead(
                organization_id=membership.organization_id,
                organization_name=membership.organization.name,
                role=membership.role,
            )
            for membership in memberships_for(db, user)
        ],
    )


def set_session_cookie(response: Response, user: User) -> None:
    """Start a session."""
    settings = get_settings()
    response.set_cookie(
        key=settings.session_cookie_name,
        value=create_session_token(user.id),
        max_age=settings.session_ttl_hours * 3600,
        httponly=True,
        samesite="lax",
        secure=settings.session_cookie_secure,
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    """End a session."""
    settings = get_settings()
    response.delete_cookie(
        key=settings.session_cookie_name,
        path="/",
        httponly=True,
        samesite="lax",
        secure=settings.session_cookie_secure,
    )


def load_invitation(db: Session, token: str) -> Invitation:
    """Fetch a usable invitation or raise 400."""
    invitation = db.scalar(select(Invitation).where(Invitation.token_hash == hash_token(token)))
    if (
        invitation is None
        or invitation.accepted_at is not None
        or is_expired(invitation.expires_at)
    ):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "That invitation link is not valid any more."
        )
    return invitation


def build_invite_url(token: str) -> str:
    return f"{get_settings().app_public_url}/accept-invite?token={token}"


def build_reset_url(token: str) -> str:
    return f"{get_settings().app_public_url}/reset-password?token={token}"


@router.post("/sign-in", response_model=SessionRead)
def sign_in(payload: SignInRequest, response: Response, db: DbSession) -> SessionRead:
    """Start a session with an email and password."""
    user = db.scalar(select(User).where(User.email == payload.email))
    if (
        user is None
        or not user.is_active
        or not verify_password(user.password_hash, payload.password)
    ):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password")
    set_session_cookie(response, user)
    return build_session(db, user)


@router.post("/signup", response_model=SessionRead, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, response: Response, db: DbSession) -> SessionRead:
    """Create a school and its first admin in one step (D-37)."""
    if db.scalar(select(User).where(User.email == payload.email)) is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "That email already has an account. Sign in instead."
        )

    organization = Organization(name=payload.school_name.strip(), type=OrganizationType.SCHOOL)
    db.add(organization)
    db.flush()

    user = User(
        email=payload.email,
        name=payload.name.strip(),
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.flush()
    db.add(
        Membership(
            user_id=user.id,
            organization_id=organization.id,
            role=MembershipRole.SCHOOL_ADMIN,
        )
    )
    db.commit()
    db.refresh(user)

    set_session_cookie(response, user)
    return build_session(db, user)


@router.post("/sign-out", status_code=status.HTTP_204_NO_CONTENT)
def sign_out(response: Response) -> None:
    """End the session."""
    clear_session_cookie(response)


@router.get("/me", response_model=SessionRead)
def me(user: CurrentUser, db: DbSession) -> SessionRead:
    """Who is signed in, if anyone."""
    return build_session(db, user)


@router.get("/invitations/{token}", response_model=InvitationPreview)
def invitation_preview(token: str, db: DbSession) -> InvitationPreview:
    """What an invite link points at. Public: the account does not exist yet."""
    invitation = load_invitation(db, token)
    organization = db.get(Organization, invitation.organization_id)
    return InvitationPreview(
        email=invitation.email,
        organization_name=organization.name if organization else "your school",
        role=invitation.role,
    )


@router.post("/accept-invite", response_model=SessionRead)
def accept_invite(payload: AcceptInviteRequest, response: Response, db: DbSession) -> SessionRead:
    """Create the account an invitation was for, and sign it in."""
    invitation = load_invitation(db, payload.token)

    if db.scalar(select(User).where(User.email == invitation.email)) is not None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "That email already has an account. Sign in instead.",
        )

    user = User(
        email=invitation.email,
        name=payload.name,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.flush()
    db.add(
        Membership(
            user_id=user.id,
            organization_id=invitation.organization_id,
            role=invitation.role,
        )
    )
    invitation.accepted_at = utcnow()
    db.commit()
    db.refresh(user)

    set_session_cookie(response, user)
    return build_session(db, user)


@router.post(
    "/forgot-password", status_code=status.HTTP_202_ACCEPTED, response_model=MessageResponse
)
def forgot_password(payload: ForgotPasswordRequest, db: DbSession) -> MessageResponse:
    """Always the same answer, so the endpoint cannot be used to probe for accounts."""
    settings = get_settings()
    message = "If that address belongs to an account, a reset link is on its way."
    user = db.scalar(select(User).where(User.email == payload.email))
    if user is None or not user.is_active:
        return MessageResponse(message=message)

    token = generate_token()
    db.add(
        PasswordResetToken(
            user_id=user.id,
            token_hash=hash_token(token),
            expires_at=utcnow() + timedelta(hours=settings.reset_ttl_hours),
        )
    )
    db.commit()

    # Nothing can send email yet (Sprint 5), so local development gets the link back.
    reset_url = build_reset_url(token) if settings.app_env == "local" else None
    return MessageResponse(message=message, reset_url=reset_url)


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
def reset_password(payload: ResetPasswordRequest, db: DbSession) -> None:
    """Set a new password with a single-use token."""
    record = db.scalar(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == hash_token(payload.token))
    )
    if record is None or record.used_at is not None or is_expired(record.expires_at):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "That reset link is not valid any more.")

    user = db.get(User, record.user_id)
    if user is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "That reset link is not valid any more.")

    user.password_hash = hash_password(payload.password)
    record.used_at = utcnow()
    db.commit()
