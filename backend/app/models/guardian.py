"""Guardians, their link to children, their consent, and the invite link they confirm with."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import (
    CreatedAtMixin,
    IdMixin,
    OrganizationScopedMixin,
    TimestampsMixin,
    string_enum,
)


class GuardianStatus(enum.StrEnum):
    """`invited` until the guardian confirms through their link (D-22)."""

    INVITED = "invited"
    CONFIRMED = "confirmed"


class Guardian(IdMixin, OrganizationScopedMixin, TimestampsMixin, Base):
    """A parent or guardian who receives WhatsApp updates.

    The guardian owns their own contact details (D-22). One guardian can be linked to several
    children in the same school.
    """

    __tablename__ = "guardians"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "whatsapp_number", name="uq_guardian_organization_whatsapp"
        ),
    )

    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    # E.164, e.g. +254712345678. Validated in the API schemas.
    whatsapp_number: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    status: Mapped[GuardianStatus] = mapped_column(
        string_enum(GuardianStatus),
        nullable=False,
        default=GuardianStatus.INVITED,
        server_default=GuardianStatus.INVITED.value,
    )


class GuardianRelationship(enum.StrEnum):
    """How a guardian is related to a child."""

    MOTHER = "mother"
    FATHER = "father"
    GUARDIAN = "guardian"
    OTHER = "other"


class StudentGuardian(IdMixin, OrganizationScopedMixin, CreatedAtMixin, Base):
    """Links a child to a guardian. Every active child needs at least one."""

    __tablename__ = "student_guardians"
    __table_args__ = (UniqueConstraint("student_id", "guardian_id", name="uq_student_guardian"),)

    student_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    guardian_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("guardians.id", ondelete="CASCADE"), nullable=False, index=True
    )
    relationship: Mapped[GuardianRelationship] = mapped_column(
        string_enum(GuardianRelationship), nullable=False
    )
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    receives_messages: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class ConsentMethod(enum.StrEnum):
    """How consent was given."""

    INVITE_LINK = "invite_link"
    SCHOOL_RECORDED = "school_recorded"


class GuardianConsent(IdMixin, OrganizationScopedMixin, CreatedAtMixin, Base):
    """A guardian's consent to WhatsApp messages. No messages without a current one (D-22).

    Append-only: withdrawing sets `withdrawn_at`; giving consent again adds a new row.
    """

    __tablename__ = "guardian_consents"

    guardian_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("guardians.id", ondelete="CASCADE"), nullable=False, index=True
    )
    consent_version: Mapped[str] = mapped_column(String(32), nullable=False)
    method: Mapped[ConsentMethod] = mapped_column(string_enum(ConsentMethod), nullable=False)
    given_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    withdrawn_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    recorded_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )


class GuardianInvite(IdMixin, OrganizationScopedMixin, CreatedAtMixin, Base):
    """A single-use, expiring link for a guardian to confirm their details (D-18 pattern)."""

    __tablename__ = "guardian_invites"

    guardian_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("guardians.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    invited_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
