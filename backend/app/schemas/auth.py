"""Typed contracts for the auth endpoints."""

import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.models.user import MembershipRole
from app.schemas.common import Email


class UserRead(BaseModel):
    """A signed-in person."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    name: str
    is_platform_admin: bool


class MembershipRead(BaseModel):
    """Which tenant a person belongs to, and in what role."""

    organization_id: uuid.UUID
    organization_name: str
    role: MembershipRole


class SessionRead(BaseModel):
    """Everything the client needs to render the signed-in shell."""

    user: UserRead
    memberships: list[MembershipRead]


class SignInRequest(BaseModel):
    """Email and password."""

    email: Email
    password: str = Field(min_length=1, max_length=128)


class AcceptInviteRequest(BaseModel):
    """Set a name and password against an invitation token."""

    token: str = Field(min_length=8, max_length=256)
    name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class InvitationPreview(BaseModel):
    """What the accept-invite page may show before the account exists."""

    email: str
    organization_name: str
    role: MembershipRole


class ForgotPasswordRequest(BaseModel):
    """Ask for a reset link."""

    email: Email


class ResetPasswordRequest(BaseModel):
    """Set a new password with a reset token."""

    token: str = Field(min_length=8, max_length=256)
    password: str = Field(min_length=8, max_length=128)


class MessageResponse(BaseModel):
    """A human-readable result."""

    message: str
    reset_url: str | None = None
