"""Accounts and their membership of a tenant."""

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    String,
    UniqueConstraint,
    Uuid,
    func,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.organization import Organization


class MembershipRole(enum.StrEnum):
    """What someone may do inside one organization.

    Stored as plain text (VARCHAR 32), so adding a role needs no migration. Parents sign in
    with a one-time WhatsApp code in Sprint 5 (D-20), not through a membership role.
    """

    SCHOOL_ADMIN = "school_admin"
    DRIVER = "driver"
    # D-21: optional second crew member; marks children on and off the bus.
    CONDUCTOR = "conductor"


CREW_ROLES = frozenset({MembershipRole.DRIVER, MembershipRole.CONDUCTOR})


class User(Base):
    """A person who can sign in. Platform admins work for Tafi, not for a tenant."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_platform_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    memberships: Mapped[list["Membership"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Membership(Base):
    """A user's role inside one organization — the tenant boundary.

    A membership is deactivated, never deleted, once its holder may have done work for the
    school: trips, boarding events and locations point at it (D-34). An inactive membership
    grants nothing; `memberships_for` ignores it.
    """

    __tablename__ = "memberships"
    __table_args__ = (
        UniqueConstraint("user_id", "organization_id", name="uq_membership_user_organization"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[MembershipRole] = mapped_column(
        Enum(
            MembershipRole,
            native_enum=False,
            length=32,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=true(), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped[User] = relationship(back_populates="memberships")
    organization: Mapped["Organization"] = relationship(lazy="joined")
