"""Building blocks shared by the school data models (Sprint 3)."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Uuid, func
from sqlalchemy.orm import Mapped, declared_attr, mapped_column


def string_enum(enum_cls: type[enum.StrEnum]) -> Enum:
    """Store a StrEnum as its value in a VARCHAR(32), the same way the auth models do."""
    return Enum(
        enum_cls,
        native_enum=False,
        length=32,
        values_callable=lambda cls: [member.value for member in cls],
    )


class IdMixin:
    """A random UUID primary key."""

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)


class OrganizationScopedMixin:
    """Every school-data row belongs to exactly one organization (D-10).

    Rows that point at each other must share an organization. The database does not
    enforce that across tables; the API does, with `get_owned_or_404` in `app.api.deps`.
    """

    @declared_attr
    def organization_id(cls) -> Mapped[uuid.UUID]:
        return mapped_column(
            Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
        )


class CreatedAtMixin:
    """When the row was created."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class TimestampsMixin(CreatedAtMixin):
    """When the row was created and last changed."""

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
