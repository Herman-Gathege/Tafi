"""Trip rules: what may happen on a trip, and who may make it happen (Sprint 4, D-21).

Every rule that makes the boarding record trustworthy lives here and is enforced by the API,
whatever the screen shows:
- a trip is always today's, Kenya time (D-28); the phone cannot choose the date;
- the morning run carries the children with a pickup stop, in stop order; the afternoon run
  carries the children with a drop-off stop, in reverse stop order (D-28: one-way riders);
- a driver working alone may only mark children after pressing "I am stopped", which the
  server records; a time sent by the phone is never trusted (D-21, D-32).
"""

import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.clock import as_utc, utcnow
from app.models.student import Student, StudentStatus
from app.models.transport import RouteRun, RunDirection, Stop, StudentRouteAssignment
from app.models.trip import (
    BoardingEvent,
    BoardingKind,
    BoardingMethod,
    Trip,
    TripLocation,
    TripStatus,
)
from app.models.user import Membership

# Kenya is UTC+3 all year, and route changes already take effect on that clock (D-28).
KENYA_OFFSET = timedelta(hours=3)

# A driver working alone must have pressed "I am stopped" this recently (D-32). Short on
# purpose: one press covers the children at one stop, and the driver presses again at the next.
STOPPED_CONFIRMATION_SECONDS = 120


def kenya_today() -> date:
    """The service date in Kenya, whatever the server clock says."""
    return (datetime.now(UTC) + KENYA_OFFSET).date()


def is_crew_on_run(run: RouteRun, membership: Membership) -> bool:
    """Is this crew member the driver or the conductor of this run?"""
    return membership.id in {run.driver_membership_id, run.conductor_membership_id}


def driver_is_alone(run: RouteRun) -> bool:
    """True when the run has no conductor, so the driver is the only crew (D-21)."""
    return run.conductor_membership_id is None


def must_confirm_stopped(run: RouteRun, membership: Membership) -> bool:
    """Only a driver working alone needs to confirm they are stopped before marking."""
    return driver_is_alone(run) and membership.id == run.driver_membership_id


def runs_for_crew(db: Session, membership: Membership) -> list[RouteRun]:
    """Every run this crew member is on, in departure order."""
    return list(
        db.scalars(
            select(RouteRun)
            .where(
                RouteRun.organization_id == membership.organization_id,
                (RouteRun.driver_membership_id == membership.id)
                | (RouteRun.conductor_membership_id == membership.id),
            )
            .order_by(RouteRun.departure_time)
        )
    )


def load_run(db: Session, route_run_id: uuid.UUID, membership: Membership) -> RouteRun:
    """A run this crew member is actually on. Anything else is reported as missing (D-26)."""
    run = db.get(RouteRun, route_run_id)
    if (
        run is None
        or run.organization_id != membership.organization_id
        or not is_crew_on_run(run, membership)
    ):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such run")
    return run


def load_trip(db: Session, trip_id: uuid.UUID, membership: Membership) -> tuple[Trip, RouteRun]:
    """A trip this crew member is actually on, with its run."""
    trip = db.get(Trip, trip_id)
    if trip is None or trip.organization_id != membership.organization_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such trip")
    run = db.get(RouteRun, trip.route_run_id)
    if run is None or not is_crew_on_run(run, membership):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such trip")
    return trip, run


def trip_for_run(db: Session, run: RouteRun, service_date: date) -> Trip | None:
    """The trip for this run on this day, if it exists."""
    return db.scalar(
        select(Trip).where(Trip.route_run_id == run.id, Trip.service_date == service_date)
    )


def start_trip(db: Session, membership: Membership, run: RouteRun) -> Trip:
    """Start today's trip for a run. Starting twice returns the same trip."""
    service_date = kenya_today()
    trip = trip_for_run(db, run, service_date)
    if trip is not None:
        if trip.status == TripStatus.SCHEDULED:
            trip.status = TripStatus.ACTIVE
            trip.started_at = utcnow()
            trip.started_by_membership_id = membership.id
            db.flush()
        return trip

    trip = Trip(
        organization_id=membership.organization_id,
        route_run_id=run.id,
        service_date=service_date,
        status=TripStatus.ACTIVE,
        started_at=utcnow(),
        started_by_membership_id=membership.id,
    )
    db.add(trip)
    db.flush()
    return trip


def end_trip(db: Session, membership: Membership, trip: Trip) -> Trip:
    """Finish a running trip. Only a running trip can be ended."""
    if trip.status != TripStatus.ACTIVE:
        raise HTTPException(status.HTTP_409_CONFLICT, "Only a trip that is running can be ended.")
    trip.status = TripStatus.COMPLETED
    trip.ended_at = utcnow()
    trip.ended_by_membership_id = membership.id
    db.flush()
    return trip


@dataclass
class Rider:
    """A child on this run, and the stop that matters for it."""

    student: Student
    assignment: StudentRouteAssignment
    stop: Stop


def riders_for_run(db: Session, run: RouteRun) -> list[Rider]:
    """The children this run carries, in the order the vehicle reaches them.

    Morning: children with a pickup stop, first stop first. Afternoon: children with a
    drop-off stop, last stop first. A child who rides one way only appears on that run alone.
    """
    morning = run.direction == RunDirection.MORNING
    stop_column = (
        StudentRouteAssignment.pickup_stop_id if morning else StudentRouteAssignment.dropoff_stop_id
    )
    rows = db.execute(
        select(StudentRouteAssignment, Student, Stop)
        .join(Student, Student.id == StudentRouteAssignment.student_id)
        .join(Stop, Stop.id == stop_column)
        .where(
            StudentRouteAssignment.organization_id == run.organization_id,
            StudentRouteAssignment.route_id == run.route_id,
            StudentRouteAssignment.active_to.is_(None),
            Student.status == StudentStatus.ACTIVE,
        )
        .order_by(
            Stop.sequence.asc() if morning else Stop.sequence.desc(),
            Student.last_name,
            Student.first_name,
        )
    ).all()
    return [
        Rider(student=student, assignment=assignment, stop=stop)
        for assignment, student, stop in rows
    ]


def events_for_trip(db: Session, trip: Trip) -> list[BoardingEvent]:
    """Every boarding event on a trip, in the order they were recorded."""
    return list(
        db.scalars(
            select(BoardingEvent)
            .where(BoardingEvent.trip_id == trip.id)
            .order_by(BoardingEvent.recorded_at, BoardingEvent.created_at)
        )
    )


def current_states(db: Session, trip: Trip) -> dict[uuid.UUID, BoardingKind]:
    """Where each child is up to: the latest event wins."""
    states: dict[uuid.UUID, BoardingKind] = {}
    for event in events_for_trip(db, trip):
        states[event.student_id] = event.kind
    return states


def confirm_stopped(db: Session, membership: Membership, trip: Trip) -> datetime:
    """Record, on the server, that this crew member says the vehicle is stopped (D-32)."""
    if trip.status != TripStatus.ACTIVE:
        raise HTTPException(status.HTTP_409_CONFLICT, "The trip is not running.")
    trip.stopped_confirmed_at = utcnow()
    trip.stopped_confirmed_by_membership_id = membership.id
    db.flush()
    return trip.stopped_confirmed_at


def fresh_stopped_confirmation(trip: Trip, membership: Membership) -> datetime | None:
    """This crew member's own stopped confirmation, if it is recent enough to mark with."""
    if (
        trip.stopped_confirmed_at is None
        or trip.stopped_confirmed_by_membership_id != membership.id
    ):
        return None
    confirmed_at = as_utc(trip.stopped_confirmed_at)
    if utcnow() - confirmed_at > timedelta(seconds=STOPPED_CONFIRMATION_SECONDS):
        return None
    return confirmed_at


def record_event(
    db: Session,
    membership: Membership,
    trip: Trip,
    run: RouteRun,
    *,
    student_id: uuid.UUID,
    kind: BoardingKind,
    latitude: Decimal | None = None,
    longitude: Decimal | None = None,
) -> BoardingEvent:
    """Record one child's state change, enforcing the rules that make the record trustworthy."""
    if trip.status != TripStatus.ACTIVE:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "The trip is not running, so children cannot be marked."
        )

    if not any(rider.student.id == student_id for rider in riders_for_run(db, run)):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "That child is not on this run today.")

    confirmed_at = None
    if must_confirm_stopped(run, membership):
        confirmed_at = fresh_stopped_confirmation(trip, membership)
        if confirmed_at is None:
            raise HTTPException(
                status.HTTP_409_CONFLICT, "Press 'I am stopped' before marking children."
            )

    current = current_states(db, trip).get(student_id)
    if kind is BoardingKind.BOARDED and current is BoardingKind.BOARDED:
        raise HTTPException(status.HTTP_409_CONFLICT, "That child has already boarded.")
    if kind is BoardingKind.BOARDED and current is BoardingKind.DROPPED_OFF:
        raise HTTPException(status.HTTP_409_CONFLICT, "That child has already been dropped off.")
    if kind is BoardingKind.DROPPED_OFF and current is not BoardingKind.BOARDED:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "A child must board before they are dropped off."
        )
    if kind is BoardingKind.ABSENT and current is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "That child already has a state on this trip."
        )

    event = BoardingEvent(
        organization_id=trip.organization_id,
        trip_id=trip.id,
        student_id=student_id,
        kind=kind,
        recorded_by_membership_id=membership.id,
        method=BoardingMethod.MANUAL,
        recorded_at=utcnow(),
        latitude=latitude,
        longitude=longitude,
        stopped_confirmed_at=confirmed_at,
    )
    db.add(event)
    db.flush()
    return event


def record_location(
    db: Session,
    membership: Membership,
    trip: Trip,
    *,
    latitude: Decimal,
    longitude: Decimal,
    accuracy_m: Decimal | None,
    recorded_at: datetime | None,
) -> TripLocation:
    """Store a position shared during the trip. Gaps are expected (T1-11)."""
    if trip.status != TripStatus.ACTIVE:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Location is only recorded while the trip is running."
        )
    now = utcnow()
    # A phone may send a queued position late, but never one from the future.
    moment = min(as_utc(recorded_at), now) if recorded_at is not None else now
    location = TripLocation(
        organization_id=trip.organization_id,
        trip_id=trip.id,
        latitude=latitude,
        longitude=longitude,
        accuracy_m=accuracy_m,
        recorded_at=moment,
        recorded_by_membership_id=membership.id,
    )
    db.add(location)
    db.flush()
    return location
