"""The crew app's API: today's trips, starting and ending them, marks and location (Sprint 4).

Every rule lives in `app.services.trips`; these handlers only load, call and shape.
"""

import uuid

from fastapi import APIRouter, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import Crew, DbSession
from app.models.transport import Route, RouteRun, Stop, Vehicle
from app.models.trip import BoardingEvent, Trip, TripLocation, TripStatus
from app.models.user import Membership
from app.schemas.crew_trips import (
    BoardingEventCreate,
    BoardingEventRead,
    ChildOnTrip,
    StoppedConfirmation,
    TripDetail,
    TripLocationCreate,
    TripLocationRead,
    TripStart,
    TripSummary,
)
from app.services import trips as trip_service

router = APIRouter(prefix="/api/v1/crew", tags=["crew"])


def _detail(db: Session, membership: Membership, trip: Trip, run: RouteRun) -> TripDetail:
    route = db.get(Route, run.route_id)
    vehicle = db.get(Vehicle, run.vehicle_id) if run.vehicle_id else None
    riders = trip_service.riders_for_run(db, run)
    states = trip_service.current_states(db, trip)
    stop_names = {
        stop.id: stop.name for stop in db.scalars(select(Stop).where(Stop.route_id == run.route_id))
    }

    children = []
    for rider in riders:
        state = states.get(rider.student.id)
        pickup_id = rider.assignment.pickup_stop_id
        dropoff_id = rider.assignment.dropoff_stop_id
        children.append(
            ChildOnTrip(
                student_id=rider.student.id,
                first_name=rider.student.first_name,
                last_name=rider.student.last_name,
                grade=rider.student.grade,
                stop=rider.stop.name,
                stop_sequence=rider.stop.sequence,
                pickup_stop=stop_names.get(pickup_id) if pickup_id else None,
                dropoff_stop=stop_names.get(dropoff_id) if dropoff_id else None,
                state=state.value if state is not None else "pending",
            )
        )

    locations = list(
        db.scalars(
            select(TripLocation)
            .where(TripLocation.trip_id == trip.id)
            .order_by(TripLocation.recorded_at)
        )
    )
    return TripDetail(
        id=trip.id,
        route_run_id=trip.route_run_id,
        route_code=route.code if route else "",
        route_name=route.name if route else "",
        direction=run.direction,
        departure_time=run.departure_time,
        vehicle_plate=vehicle.plate if vehicle else None,
        status=trip.status,
        service_date=trip.service_date,
        started_at=trip.started_at,
        ended_at=trip.ended_at,
        children=children,
        boarded_count=sum(1 for child in children if child.state == "boarded"),
        dropped_off_count=sum(1 for child in children if child.state == "dropped_off"),
        absent_count=sum(1 for child in children if child.state == "absent"),
        location_count=len(locations),
        last_location_at=locations[-1].recorded_at if locations else None,
        my_role="driver" if membership.id == run.driver_membership_id else "conductor",
        driver_alone=trip_service.driver_is_alone(run),
        must_confirm_stopped=trip_service.must_confirm_stopped(run, membership),
        stopped_confirmed_at=trip_service.fresh_stopped_confirmation(trip, membership),
        stopped_window_seconds=trip_service.STOPPED_CONFIRMATION_SECONDS,
    )


@router.get("/trips/today", response_model=list[TripSummary])
def todays_trips(membership: Crew, db: DbSession) -> list[TripSummary]:
    """Every run this crew member is on today, with the trip if it has started."""
    service_date = trip_service.kenya_today()
    summaries = []
    for run in trip_service.runs_for_crew(db, membership):
        trip = trip_service.trip_for_run(db, run, service_date)
        route = db.get(Route, run.route_id)
        vehicle = db.get(Vehicle, run.vehicle_id) if run.vehicle_id else None
        boarded = dropped = absent = 0
        if trip is not None:
            detail = _detail(db, membership, trip, run)
            boarded, dropped, absent = (
                detail.boarded_count,
                detail.dropped_off_count,
                detail.absent_count,
            )
            expected = len(detail.children)
        else:
            expected = len(trip_service.riders_for_run(db, run))
        summaries.append(
            TripSummary(
                id=trip.id if trip else None,
                route_run_id=run.id,
                route_code=route.code if route else "",
                route_name=route.name if route else "",
                direction=run.direction,
                departure_time=run.departure_time,
                vehicle_plate=vehicle.plate if vehicle else None,
                status=trip.status if trip else TripStatus.SCHEDULED,
                service_date=service_date,
                started_at=trip.started_at if trip else None,
                ended_at=trip.ended_at if trip else None,
                boarded_count=boarded,
                dropped_off_count=dropped,
                absent_count=absent,
                expected_count=expected,
            )
        )
    return summaries


@router.post("/trips", response_model=TripDetail, status_code=status.HTTP_201_CREATED)
def start_trip(payload: TripStart, membership: Crew, db: DbSession) -> TripDetail:
    """Start today's trip for a run. Starting it twice returns the same trip."""
    run = trip_service.load_run(db, payload.route_run_id, membership)
    trip = trip_service.start_trip(db, membership, run)
    db.commit()
    db.refresh(trip)
    return _detail(db, membership, trip, run)


@router.post("/trips/{trip_id}/end", response_model=TripDetail)
def end_trip(trip_id: uuid.UUID, membership: Crew, db: DbSession) -> TripDetail:
    """Finish a running trip."""
    trip, run = trip_service.load_trip(db, trip_id, membership)
    trip_service.end_trip(db, membership, trip)
    db.commit()
    db.refresh(trip)
    return _detail(db, membership, trip, run)


@router.get("/trips/{trip_id}", response_model=TripDetail)
def trip_detail(trip_id: uuid.UUID, membership: Crew, db: DbSession) -> TripDetail:
    """One trip: the children this run carries, where they are up to, and the location trail."""
    trip, run = trip_service.load_trip(db, trip_id, membership)
    return _detail(db, membership, trip, run)


@router.post("/trips/{trip_id}/stopped", response_model=StoppedConfirmation)
def confirm_stopped(trip_id: uuid.UUID, membership: Crew, db: DbSession) -> StoppedConfirmation:
    """'I am stopped': recorded by the server, and required before a lone driver marks (D-32)."""
    trip, _ = trip_service.load_trip(db, trip_id, membership)
    confirmed_at = trip_service.confirm_stopped(db, membership, trip)
    db.commit()
    return StoppedConfirmation(
        confirmed_at=confirmed_at, valid_for_seconds=trip_service.STOPPED_CONFIRMATION_SECONDS
    )


@router.post(
    "/trips/{trip_id}/events", response_model=BoardingEventRead, status_code=status.HTTP_201_CREATED
)
def mark_child(
    trip_id: uuid.UUID, payload: BoardingEventCreate, membership: Crew, db: DbSession
) -> BoardingEvent:
    """Mark a child boarded, dropped off or absent (D-21)."""
    trip, run = trip_service.load_trip(db, trip_id, membership)
    event = trip_service.record_event(
        db,
        membership,
        trip,
        run,
        student_id=payload.student_id,
        kind=payload.kind,
        latitude=payload.latitude,
        longitude=payload.longitude,
    )
    db.commit()
    db.refresh(event)
    return event


@router.post(
    "/trips/{trip_id}/locations",
    response_model=TripLocationRead,
    status_code=status.HTTP_201_CREATED,
)
def share_location(
    trip_id: uuid.UUID, payload: TripLocationCreate, membership: Crew, db: DbSession
) -> TripLocation:
    """Share a position while the trip is running (MVP-11)."""
    trip, _ = trip_service.load_trip(db, trip_id, membership)
    location = trip_service.record_location(
        db,
        membership,
        trip,
        latitude=payload.latitude,
        longitude=payload.longitude,
        accuracy_m=payload.accuracy_m,
        recorded_at=payload.recorded_at,
    )
    db.commit()
    db.refresh(location)
    return location
