"""Trips and what happens on them: who boarded, and where the vehicle was (Sprint 4)."""

import enum
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Index, Numeric, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import (
    CreatedAtMixin,
    IdMixin,
    OrganizationScopedMixin,
    TimestampsMixin,
    string_enum,
)


class TripStatus(enum.StrEnum):
    """A trip's life: it exists for the day, runs, then finishes."""

    SCHEDULED = "scheduled"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Trip(IdMixin, OrganizationScopedMixin, TimestampsMixin, Base):
    """One run of one route on one day — always today, Kenya time, when it starts.

    The run (`route_runs`) says who drives and which vehicle; the trip says what happened
    today: when it started, when it ended, and who did that (D-21).
    """

    __tablename__ = "trips"
    __table_args__ = (
        UniqueConstraint("route_run_id", "service_date", name="uq_trip_run_service_date"),
        Index("ix_trips_organization_service_date", "organization_id", "service_date"),
    )

    route_run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("route_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    service_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[TripStatus] = mapped_column(
        string_enum(TripStatus), nullable=False, default=TripStatus.SCHEDULED
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("memberships.id", ondelete="SET NULL"), nullable=True
    )
    ended_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("memberships.id", ondelete="SET NULL"), nullable=True
    )
    # The latest "I am stopped" from a driver working alone (D-32), recorded by the server
    # when the driver presses the button. Marks check this, never a time the phone sends.
    stopped_confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    stopped_confirmed_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("memberships.id", ondelete="SET NULL"), nullable=True
    )


class BoardingKind(enum.StrEnum):
    """What happened to a child on a trip."""

    BOARDED = "boarded"
    DROPPED_OFF = "dropped_off"
    ABSENT = "absent"


class BoardingMethod(enum.StrEnum):
    """How it was recorded. `scan` arrives with the child cards (D-24)."""

    MANUAL = "manual"
    SCAN = "scan"


class BoardingEvent(IdMixin, OrganizationScopedMixin, CreatedAtMixin, Base):
    """One child's state change on one trip, with who recorded it and how (D-21, D-24)."""

    __tablename__ = "boarding_events"
    __table_args__ = (Index("ix_boarding_events_trip_student", "trip_id", "student_id"),)

    trip_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    kind: Mapped[BoardingKind] = mapped_column(string_enum(BoardingKind), nullable=False)
    recorded_by_membership_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("memberships.id", ondelete="RESTRICT"), nullable=False
    )
    method: Mapped[BoardingMethod] = mapped_column(
        string_enum(BoardingMethod), nullable=False, default=BoardingMethod.MANUAL
    )
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6), nullable=True)
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6), nullable=True)
    # Set when a driver working alone marked this child: the stopped confirmation the mark
    # relied on, so the record shows the rule was followed (D-32).
    stopped_confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class TripLocation(IdMixin, OrganizationScopedMixin, CreatedAtMixin, Base):
    """A position the crew shared while the trip was running (MVP-11).

    A phone browser cannot keep sending these with the screen locked (T1-11), so a trail
    may have gaps. Nothing downstream may assume it is continuous.
    """

    __tablename__ = "trip_locations"
    __table_args__ = (Index("ix_trip_locations_trip_recorded", "trip_id", "recorded_at"),)

    trip_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True
    )
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    latitude: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    longitude: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    accuracy_m: Mapped[Decimal | None] = mapped_column(Numeric(7, 2), nullable=True)
    recorded_by_membership_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("memberships.id", ondelete="RESTRICT"), nullable=False
    )
