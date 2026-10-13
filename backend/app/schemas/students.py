"""Typed contracts for a school's students, guardians and emergency contacts."""

import uuid
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.models.guardian import GuardianRelationship, GuardianStatus
from app.models.student import StudentStatus
from app.schemas.common import Email, Phone, WhatsAppNumber

PersonName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
FullName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]
Grade = Annotated[str, StringConstraints(strip_whitespace=True, max_length=50)]
ShortText = Annotated[str, StringConstraints(strip_whitespace=True, max_length=64)]


# --- Guardians on a child -------------------------------------------------------------------


class GuardianInput(BaseModel):
    """A guardian for a child. An existing guardian with the same number is linked, not copied."""

    full_name: FullName
    whatsapp_number: WhatsAppNumber
    email: Email | None = None
    relationship: GuardianRelationship
    is_primary: bool = False
    receives_messages: bool = True


class GuardianLinkUpdate(BaseModel):
    """Change how a guardian relates to one child."""

    relationship: GuardianRelationship | None = None
    is_primary: bool | None = None
    receives_messages: bool | None = None


class LinkedGuardian(BaseModel):
    """A guardian as seen from one child."""

    guardian_id: uuid.UUID
    full_name: str
    whatsapp_number: str
    email: str | None
    status: GuardianStatus
    relationship: GuardianRelationship
    is_primary: bool
    receives_messages: bool


# --- Emergency contacts ---------------------------------------------------------------------


class EmergencyContactCreate(BaseModel):
    """Someone to call when no guardian answers. Any phone, landlines included."""

    name: FullName
    phone: Phone
    relationship: ShortText | None = None


class EmergencyContactUpdate(BaseModel):
    """Change an emergency contact."""

    name: FullName | None = None
    phone: Phone | None = None
    relationship: ShortText | None = None


class EmergencyContactRead(BaseModel):
    """An emergency contact as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    phone: str
    relationship: str | None


# --- Students -------------------------------------------------------------------------------


class StudentCreate(BaseModel):
    """A new child, with at least one guardian (an active child always has one)."""

    first_name: PersonName
    last_name: PersonName
    grade: Grade | None = None
    guardians: list[GuardianInput] = Field(min_length=1, max_length=4)

    @model_validator(mode="after")
    def _guardians_make_sense(self) -> Self:
        numbers = [guardian.whatsapp_number for guardian in self.guardians]
        if len(numbers) != len(set(numbers)):
            raise ValueError("Each guardian needs their own WhatsApp number")
        if sum(guardian.is_primary for guardian in self.guardians) > 1:
            raise ValueError("Choose one primary guardian")
        return self


class StudentUpdate(BaseModel):
    """Change a child's details, or deactivate them. Send null to clear the grade."""

    first_name: PersonName | None = None
    last_name: PersonName | None = None
    grade: Grade | None = None
    status: StudentStatus | None = None


class StudentSummary(BaseModel):
    """A child in the list, with their guardians."""

    id: uuid.UUID
    first_name: str
    last_name: str
    grade: str | None
    status: StudentStatus
    guardians: list[LinkedGuardian]


class StudentDetail(StudentSummary):
    """One child, with guardians and emergency contacts."""

    emergency_contacts: list[EmergencyContactRead]


# --- Guardians on their own -----------------------------------------------------------------


class GuardianUpdate(BaseModel):
    """Correct a guardian's details. Only until they confirm them themselves (D-22)."""

    full_name: FullName | None = None
    whatsapp_number: WhatsAppNumber | None = None
    email: Email | None = None


class ChildBrief(BaseModel):
    """A child as seen from a guardian."""

    id: uuid.UUID
    first_name: str
    last_name: str


class GuardianRead(BaseModel):
    """A guardian with the children they are linked to."""

    id: uuid.UUID
    full_name: str
    whatsapp_number: str
    email: str | None
    status: GuardianStatus
    children: list[ChildBrief]
