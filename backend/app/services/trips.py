"""Trip rules: what may happen on a trip, and who may make it happen (Sprint 4, D-21)."""

import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.clock import as_utc, utcnow
from app.models.student import Student, StudentStatus
from app.models.transport import RouteRun, StudentRouteAssignment
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

# Decision A: a driver working alone must have confirmed they are stopped recently.
# The window is deliberately short; the crew member re-confirms as they move on.
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


def load_trip(db: Session, trip_id: uuid.UUID, membership: Membership) -> Trip:
    """A trip this crew member is actually on."""
    trip = db.get(Trip, trip_id)
    if trip is None or trip.organization_id != membership.organization_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such trip")
    run = db.get(RouteRun, trip.route_run_id)
    if run is None or not is_crew_on_run(run, membership):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such trip")
    return trip


def trip_for_run(db: Session, run: RouteRun, service_date: date) -> Trip | None:
    """The trip for this run on this day, if it exists."""
    return db.scalar(
        select(Trip).where(Trip.route_run_id == run.id, Trip.service_date == service_date)
    )


def start_trip(db: Session, membership: Membership, run: RouteRun, service_date: date) -> Trip:
    """Start today's trip for a run. Starting twice returns the same trip."""
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


def assignments_for_run(db: Session, run: RouteRun) -> list[StudentRouteAssignment]:
    """The children currently riding this route (D-28: at most one assignment each)."""
    return list(
        db.scalars(
            select(StudentRouteAssignment)
            .join(Student, Student.id == StudentRouteAssignment.student_id)
            .where(
                StudentRouteAssignment.organization_id == run.organization_id,
                StudentRouteAssignment.route_id == run.route_id,
                StudentRouteAssignment.active_to.is_(None),
                Student.status == StudentStatus.ACTIVE,
            )
            .order_by(StudentRouteAssignment.created_at)
        )
    )


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


def require_stopped_confirmation(confirmed_at: datetime | None) -> None:
    """A driver working alone may only mark children while the vehicle is stopped (D-21).

    The browser gives no reliable motion signal, so the crew member confirms it and the
    server checks how recent that confirmation is. Enforcement lives here, not in the UI.
    """
    if confirmed_at is None:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Confirm you are stopped before marking children."
        )
    moment = as_utc(confirmed_at)
    now = utcnow()
    if moment > now + timedelta(seconds=30):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "That confirmation is in the future.")
    if now - moment > timedelta(seconds=STOPPED_CONFIRMATION_SECONDS):
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Confirm you are stopped again before marking."
        )


def record_event(
    db: Session,
    membership: Membership,
    trip: Trip,
    run: RouteRun,
    *,
    student_id: uuid.UUID,
    kind: BoardingKind,
    stopped_confirmed_at: datetime | None,
    latitude: Decimal | None = None,
    longitude: Decimal | None = None,
) -> BoardingEvent:
    """Record one child's state change, enforcing the rules that make the record trustworthy."""
    if trip.status != TripStatus.ACTIVE:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "The trip is not running, so children cannot be marked."
        )

    assigned = any(a.student_id == student_id for a in assignments_for_run(db, run))
    if not assigned:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "That child is not on this route today.")

    if driver_is_alone(run) and membership.id == run.driver_membership_id:
        require_stopped_confirmation(stopped_confirmed_at)

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
    location = TripLocation(
        organization_id=trip.organization_id,
        trip_id=trip.id,
        latitude=latitude,
        longitude=longitude,
        accuracy_m=accuracy_m,
        recorded_at=as_utc(recorded_at) if recorded_at is not None else utcnow(),
        recorded_by_membership_id=membership.id,
    )
    db.add(location)
    db.flush()
    return location
