"""Typed contracts for guardian invites, consent and stop-change requests (S3-05, S3-06)."""

import uuid
from datetime import datetime
from typing import Annotated, Self

from pydantic import BaseModel, Field, StringConstraints, model_validator

from app.models.guardian import GuardianRelationship
from app.models.transport import RequestStatus
from app.schemas.common import Email, Phone, WhatsAppNumber
from app.schemas.students import ChildBrief, CurrentRoute, StopBrief

FullName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]
Location = Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=500)]
ShortText = Annotated[str, StringConstraints(strip_whitespace=True, max_length=64)]


# --- School side ----------------------------------------------------------------------------


class GuardianInviteRead(BaseModel):
    """An invite the school just created."""

    guardian_id: uuid.UUID
    full_name: str
    whatsapp_number: str
    expires_at: datetime
    # Only in `local`, until WhatsApp messages can be sent (D-18, Sprint 5).
    invite_url: str | None = None


class StopChangeRequestRead(BaseModel):
    """A guardian's request for a different stop."""

    id: uuid.UUID
    student: ChildBrief
    guardian_id: uuid.UUID
    guardian_name: str
    current_route: CurrentRoute | None
    requested_stop: StopBrief | None
    requested_location: str | None
    status: RequestStatus
    created_at: datetime
    decided_at: datetime | None


# --- Guardian side (public, reached from the invite link) ----------------------------------


class InvitedChild(BaseModel):
    """One of the guardian's children, with where they ride and the stops on their route."""

    id: uuid.UUID
    first_name: str
    last_name: str
    grade: str | None
    route: CurrentRoute | None
    stops_on_route: list[StopBrief]


class GuardianInvitePreview(BaseModel):
    """What the registration page shows. Nothing about any other guardian."""

    school_name: str
    full_name: str
    whatsapp_number: str
    email: str | None
    children: list[InvitedChild]
    consent_version: str
    consent_text: str


class SecondGuardian(BaseModel):
    """Another guardian for all of this guardian's children."""

    full_name: FullName
    whatsapp_number: WhatsAppNumber
    relationship: GuardianRelationship


class EmergencyContactInput(BaseModel):
    """An emergency contact for one child."""

    student_id: uuid.UUID
    name: FullName
    phone: Phone
    relationship: ShortText | None = None


class StopChangeInput(BaseModel):
    """Ask for a different stop: one on the child's route, or a place described in words."""

    student_id: uuid.UUID
    requested_stop_id: uuid.UUID | None = None
    requested_location: Location | None = None

    @model_validator(mode="after")
    def _one_place(self) -> Self:
        if (self.requested_stop_id is None) == (self.requested_location is None):
            raise ValueError("Choose a stop or describe the place, not both")
        return self


class GuardianConfirm(BaseModel):
    """The guardian confirms their details and agrees to messages.

    The WhatsApp number cannot be changed here: the link was sent to it. To use another number,
    the guardian asks the school.
    """

    full_name: FullName
    email: Email | None = None
    consent: bool
    consent_version: str = Field(min_length=1, max_length=32)
    second_guardian: SecondGuardian | None = None
    emergency_contacts: list[EmergencyContactInput] = Field(default_factory=list, max_length=4)
    stop_changes: list[StopChangeInput] = Field(default_factory=list, max_length=8)

    @model_validator(mode="after")
    def _must_agree(self) -> Self:
        if not self.consent:
            raise ValueError("Tick the box to agree to WhatsApp updates")
        return self


class GuardianConfirmed(BaseModel):
    """What the page shows after confirming."""

    message: str
    school_name: str
