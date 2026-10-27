"""Typed contracts for a school's crew: drivers and conductors (D-21)."""

import uuid
from datetime import datetime

from pydantic import BaseModel, field_validator

from app.models.user import CREW_ROLES, MembershipRole
from app.schemas.common import Email


class CrewInvitationCreate(BaseModel):
    """Invite a driver or a conductor. School admins are invited by Tafi staff only."""

    email: Email
    role: MembershipRole

    @field_validator("role")
    @classmethod
    def _crew_only(cls, role: MembershipRole) -> MembershipRole:
        if role not in CREW_ROLES:
            raise ValueError("Invite a driver or a conductor")
        return role


class CrewInvitationRead(BaseModel):
    """An invitation as returned to the school admin who sent it.

    `restored` is true when the person was on the crew before and removed: they are put
    back straight away with their history intact (D-34), and no link is needed.
    """

    id: uuid.UUID
    email: str
    role: MembershipRole
    expires_at: datetime
    # Only in `local`, until messages can be sent (D-18).
    invite_url: str | None = None
    restored: bool = False


class CrewMemberRead(BaseModel):
    """Someone on the school's crew."""

    membership_id: uuid.UUID
    name: str
    email: str
    role: MembershipRole
    joined_at: datetime


class CrewRead(BaseModel):
    """The crew page: who is on it, and who has been invited."""

    members: list[CrewMemberRead]
    pending_invitations: list[CrewInvitationRead]
