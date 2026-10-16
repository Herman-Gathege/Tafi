"""The crew app's API: today's trips, starting and ending them, marks and location (Sprint 4)."""

import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import Crew, DbSession
from app.models.student import Student
from app.models.transport import Route, RouteRun, Stop, Vehicle
from app.models.trip import BoardingEvent, TripLocation, TripStatus
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


def _stop_name(db: DbSession, stop_id) -> str | None:
    if stop_id is None:
        return None
    stop = db.get(Stop, stop_id)
    return stop.name if stop else None


def _detail(db: DbSession, membership, trip) -> TripDetail:
    run = db.get(RouteRun, trip.route_run_id)
    if run is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such trip")
    route = db.get(Route, run.route_id)
    vehicle = db.get(Vehicle, run.vehicle_id) if run.vehicle_id else None
    assignments = trip_service.assignments_for_run(db, run)
    states = trip_service.current_states(db, trip)

    children = []
    for assignment in assignments:
        student = db.get(Student, assignment.student_id)
        if student is None:
            continue
        state = states.get(student.id)
        children.append(
            ChildOnTrip(
                student_id=student.id,
                first_name=student.first_name,
                last_name=student.last_name,
                grade=student.grade,
                pickup_stop=_stop_name(db, assignment.pickup_stop_id),
                dropoff_stop=_stop_name(db, assignment.dropoff_stop_id),
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
    boarded = sum(1 for c in children if c.state == "boarded")
    dropped = sum(1 for c in children if c.state == "dropped_off")
    absent = sum(1 for c in children if c.state == "absent")
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
        boarded_count=boarded,
        dropped_off_count=dropped,
        absent_count=absent,
        location_count=len(locations),
        last_location_at=locations[-1].recorded_at if locations else None,
        my_role=("driver" if membership.id == run.driver_membership_id else "conductor"),
        driver_alone=trip_service.driver_is_alone(run),
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
        boarded = dropped = absent = expected = 0
        if trip is not None:
            detail = _detail(db, membership, trip)
            boarded, dropped, absent, expected = (
                detail.boarded_count,
                detail.dropped_off_count,
                detail.absent_count,
                len(detail.children),
            )
        else:
            expected = len(trip_service.assignments_for_run(db, run))
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
    service_date = payload.service_date or trip_service.kenya_today()
    trip = trip_service.start_trip(db, membership, run, service_date)
    db.commit()
    db.refresh(trip)
    return _detail(db, membership, trip)


@router.post("/trips/{trip_id}/end", response_model=TripDetail)
def end_trip(trip_id: uuid.UUID, membership: Crew, db: DbSession) -> TripDetail:
    """Finish a running trip."""
    trip = trip_service.load_trip(db, trip_id, membership)
    trip_service.end_trip(db, membership, trip)
    db.commit()
    db.refresh(trip)
    return _detail(db, membership, trip)


@router.get("/trips/{trip_id}", response_model=TripDetail)
def trip_detail(trip_id: uuid.UUID, membership: Crew, db: DbSession) -> TripDetail:
    """One trip: the children expected, where they are up to, and the location trail."""
    trip = trip_service.load_trip(db, trip_id, membership)
    return _detail(db, membership, trip)


@router.post(
    "/trips/{trip_id}/events", response_model=BoardingEventRead, status_code=status.HTTP_201_CREATED
)
def mark_child(
    trip_id: uuid.UUID, payload: BoardingEventCreate, membership: Crew, db: DbSession
) -> BoardingEvent:
    """Mark a child boarded, dropped off or absent (D-21)."""
    trip = trip_service.load_trip(db, trip_id, membership)
    run = db.get(RouteRun, trip.route_run_id)
    if run is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such trip")
    event = trip_service.record_event(
        db,
        membership,
        trip,
        run,
        student_id=payload.student_id,
        kind=payload.kind,
        stopped_confirmed_at=payload.stopped_confirmed_at,
        latitude=payload.latitude,
        longitude=payload.longitude,
    )
    db.commit()
    db.refresh(event)
    return event


@router.post("/trips/{trip_id}/stopped", response_model=StoppedConfirmation)
def confirm_stopped(trip_id: uuid.UUID, membership: Crew, db: DbSession) -> StoppedConfirmation:
    """A driver working alone confirms the vehicle is stopped; the app shows the time."""
    trip_service.load_trip(db, trip_id, membership)
    return StoppedConfirmation(confirmed_at=trip_service.utcnow())


@router.post(
    "/trips/{trip_id}/locations",
    response_model=TripLocationRead,
    status_code=status.HTTP_201_CREATED,
)
def share_location(
    trip_id: uuid.UUID, payload: TripLocationCreate, membership: Crew, db: DbSession
) -> TripLocation:
    """Share a position while the trip is running (MVP-11)."""
    trip = trip_service.load_trip(db, trip_id, membership)
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
