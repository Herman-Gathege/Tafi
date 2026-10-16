"""Routes and their stops, vehicles, who drives each run, and which child rides where."""

import enum
import uuid
from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Time,
    UniqueConstraint,
    Uuid,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import IdMixin, OrganizationScopedMixin, TimestampsMixin, string_enum


class Route(IdMixin, OrganizationScopedMixin, TimestampsMixin, Base):
    """A named route, e.g. "Route 1 · Kileleshwa". The school owns it (D-22)."""

    __tablename__ = "routes"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_route_organization_code"),
    )

    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Stop(IdMixin, OrganizationScopedMixin, TimestampsMixin, Base):
    """A pickup or drop-off point on a route.

    `sequence` is the morning order; afternoon runs use the reverse. Not unique in the database,
    so stops can be reordered in one request; the API keeps it tidy.
    """

    __tablename__ = "stops"

    route_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("routes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    landmark: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6), nullable=True)
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6), nullable=True)


class Vehicle(IdMixin, OrganizationScopedMixin, TimestampsMixin, Base):
    """A bus or van, identified by its number plate."""

    __tablename__ = "vehicles"
    __table_args__ = (
        UniqueConstraint("organization_id", "plate", name="uq_vehicle_organization_plate"),
    )

    plate: Mapped[str] = mapped_column(String(16), nullable=False)
    seats: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class RunDirection(enum.StrEnum):
    """Which run of the day."""

    MORNING = "morning"
    AFTERNOON = "afternoon"


class RouteRun(IdMixin, OrganizationScopedMixin, TimestampsMixin, Base):
    """One run of a route (morning or afternoon): its vehicle and crew.

    D-21: a driver is required; a conductor is optional. A driver's membership cannot be
    deleted while it drives a run (the foreign key has no ON DELETE action): reassign first.
    """

    __tablename__ = "route_runs"
    __table_args__ = (
        UniqueConstraint("route_id", "direction", name="uq_route_run_route_direction"),
    )

    route_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("routes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    direction: Mapped[RunDirection] = mapped_column(string_enum(RunDirection), nullable=False)
    departure_time: Mapped[time] = mapped_column(Time, nullable=False)
    vehicle_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("vehicles.id", ondelete="SET NULL"), nullable=True, index=True
    )
    driver_membership_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("memberships.id"), nullable=False, index=True
    )
    conductor_membership_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("memberships.id", ondelete="SET NULL"), nullable=True, index=True
    )


class StudentRouteAssignment(IdMixin, OrganizationScopedMixin, TimestampsMixin, Base):
    """Which route a child rides, where they are picked up and where they are dropped off.

    A child has at most one current assignment (`active_to` is null). Ending one and starting
    another keeps the history. Either stop may be empty for a child who rides one way only.
    """

    __tablename__ = "student_route_assignments"
    __table_args__ = (
        Index(
            "uq_student_route_assignments_current",
            "student_id",
            unique=True,
            postgresql_where=text("active_to IS NULL"),
            sqlite_where=text("active_to IS NULL"),
        ),
    )

    student_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    route_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("routes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    pickup_stop_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("stops.id"), nullable=True, index=True
    )
    dropoff_stop_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("stops.id"), nullable=True, index=True
    )
    active_from: Mapped[date] = mapped_column(Date, nullable=False)
    active_to: Mapped[date | None] = mapped_column(Date, nullable=True)


class RequestStatus(enum.StrEnum):
    """Where a guardian's stop-change request stands."""

    PENDING = "pending"
    APPROVED = "approved"
    DECLINED = "declined"


class StopChangeRequest(IdMixin, OrganizationScopedMixin, TimestampsMixin, Base):
    """A guardian asks for a different stop; the school decides (D-22)."""

    __tablename__ = "stop_change_requests"

    student_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    guardian_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("guardians.id", ondelete="CASCADE"), nullable=False, index=True
    )
    requested_stop_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("stops.id", ondelete="SET NULL"), nullable=True
    )
    # Free text when the guardian's place is not an existing stop.
    requested_location: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[RequestStatus] = mapped_column(
        string_enum(RequestStatus),
        nullable=False,
        default=RequestStatus.PENDING,
        server_default=RequestStatus.PENDING.value,
    )
    decided_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
