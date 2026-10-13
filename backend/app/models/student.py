"""Children who ride, their emergency contacts, and (later) the cards the crew scans."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import (
    CreatedAtMixin,
    IdMixin,
    OrganizationScopedMixin,
    TimestampsMixin,
    string_enum,
)


class StudentStatus(enum.StrEnum):
    """Whether the child currently uses school transport."""

    ACTIVE = "active"
    INACTIVE = "inactive"


class Student(IdMixin, OrganizationScopedMixin, TimestampsMixin, Base):
    """A child on the school's transport. The school owns this record (D-22).

    Collect the minimum: no date of birth and no photo in MVP 1.
    """

    __tablename__ = "students"

    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    grade: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[StudentStatus] = mapped_column(
        string_enum(StudentStatus),
        nullable=False,
        default=StudentStatus.ACTIVE,
        server_default=StudentStatus.ACTIVE.value,
    )


class EmergencyContact(IdMixin, OrganizationScopedMixin, TimestampsMixin, Base):
    """Someone to call when no guardian answers. Added by the school or a guardian."""

    __tablename__ = "emergency_contacts"

    student_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    relationship: Mapped[str | None] = mapped_column(String(64), nullable=True)


class CardStatus(enum.StrEnum):
    """Life of a child's ID card."""

    ACTIVE = "active"
    LOST = "lost"
    REVOKED = "revoked"


class ChildCard(IdMixin, OrganizationScopedMixin, CreatedAtMixin, Base):
    """A card or tag the crew will scan (D-24). Created now, unused until scanning ships.

    `code` is random and means nothing on its own: never encode a name, school or number in it.
    """

    __tablename__ = "child_cards"

    student_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    status: Mapped[CardStatus] = mapped_column(
        string_enum(CardStatus),
        nullable=False,
        default=CardStatus.ACTIVE,
        server_default=CardStatus.ACTIVE.value,
    )
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
