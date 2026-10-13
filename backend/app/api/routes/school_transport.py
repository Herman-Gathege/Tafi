"""A school's routes, stops, vehicles and runs (Sprint 3: S3-07, S3-08).

Every endpoint is for school admins (`SchoolAdmin`), and every id from a path or a payload is
loaded with `get_owned_or_404`, so one school can never read or change another's rows.
"""

import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import DbSession, SchoolAdmin, get_owned_or_404
from app.models.transport import (
    Route,
    RouteRun,
    RunDirection,
    Stop,
    StudentRouteAssignment,
    Vehicle,
)
from app.models.user import Membership, MembershipRole
from app.schemas.transport import (
    RouteCreate,
    RouteDetail,
    RouteSummary,
    RouteUpdate,
    RunRead,
    RunUpsert,
    StopCreate,
    StopOrder,
    StopRead,
    StopUpdate,
    VehicleCreate,
    VehicleRead,
    VehicleUpdate,
)

router = APIRouter(prefix="/api/v1/school", tags=["school"])

# Written as a number: Starlette renamed the 422 constant, and both spellings exist in the wild.
UNPROCESSABLE = 422


# --- Helpers --------------------------------------------------------------------------------


def stops_of(db: Session, route_id: uuid.UUID) -> list[Stop]:
    """A route's stops in their morning order."""
    return list(
        db.scalars(
            select(Stop).where(Stop.route_id == route_id).order_by(Stop.sequence, Stop.created_at)
        )
    )


def route_detail(db: Session, route: Route) -> RouteDetail:
    runs = db.scalars(
        select(RouteRun).where(RouteRun.route_id == route.id).order_by(RouteRun.direction.desc())
    )
    return RouteDetail(
        id=route.id,
        code=route.code,
        name=route.name,
        is_active=route.is_active,
        stops=[StopRead.model_validate(stop) for stop in stops_of(db, route.id)],
        runs=[RunRead.model_validate(run) for run in runs],
    )


def renumber(stops: list[Stop]) -> None:
    """Sequence 1, 2, 3… with no gaps."""
    for position, stop in enumerate(stops, start=1):
        stop.sequence = position


def ensure_route_code_free(
    db: Session, organization_id: uuid.UUID, code: str, *, except_id: uuid.UUID | None = None
) -> None:
    query = select(Route.id).where(Route.organization_id == organization_id, Route.code == code)
    if except_id is not None:
        query = query.where(Route.id != except_id)
    if db.scalar(query) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, f"Route {code} already exists")


def ensure_plate_free(
    db: Session, organization_id: uuid.UUID, plate: str, *, except_id: uuid.UUID | None = None
) -> None:
    query = select(Vehicle.id).where(
        Vehicle.organization_id == organization_id, Vehicle.plate == plate
    )
    if except_id is not None:
        query = query.where(Vehicle.id != except_id)
    if db.scalar(query) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, f"{plate} is already on your list")


def crew_member(
    db: Session, admin: Membership, membership_id: uuid.UUID, role: MembershipRole
) -> Membership:
    """A membership in the admin's school that holds the expected crew role."""
    membership = get_owned_or_404(db, Membership, membership_id, admin, what="crew member")
    if membership.role != role:
        raise HTTPException(UNPROCESSABLE, f"That person is not a {role.value}")
    return membership


# --- Routes ---------------------------------------------------------------------------------


@router.get("/routes", response_model=list[RouteSummary])
def list_routes(admin: SchoolAdmin, db: DbSession) -> list[RouteSummary]:
    """Every route in the school, with how many stops each has."""
    stop_counts = (
        select(Stop.route_id, func.count(Stop.id).label("stop_count"))
        .group_by(Stop.route_id)
        .subquery()
    )
    rows = db.execute(
        select(Route, func.coalesce(stop_counts.c.stop_count, 0))
        .outerjoin(stop_counts, stop_counts.c.route_id == Route.id)
        .where(Route.organization_id == admin.organization_id)
        .order_by(Route.code)
    ).all()
    return [
        RouteSummary(
            id=route.id,
            code=route.code,
            name=route.name,
            is_active=route.is_active,
            stop_count=stop_count,
        )
        for route, stop_count in rows
    ]


@router.post("/routes", response_model=RouteDetail, status_code=status.HTTP_201_CREATED)
def create_route(payload: RouteCreate, admin: SchoolAdmin, db: DbSession) -> RouteDetail:
    ensure_route_code_free(db, admin.organization_id, payload.code)
    route = Route(organization_id=admin.organization_id, code=payload.code, name=payload.name)
    db.add(route)
    db.commit()
    db.refresh(route)
    return route_detail(db, route)


@router.get("/routes/{route_id}", response_model=RouteDetail)
def read_route(route_id: uuid.UUID, admin: SchoolAdmin, db: DbSession) -> RouteDetail:
    route = get_owned_or_404(db, Route, route_id, admin, what="route")
    return route_detail(db, route)


@router.patch("/routes/{route_id}", response_model=RouteDetail)
def update_route(
    route_id: uuid.UUID, payload: RouteUpdate, admin: SchoolAdmin, db: DbSession
) -> RouteDetail:
    route = get_owned_or_404(db, Route, route_id, admin, what="route")
    changes = payload.model_dump(exclude_unset=True)
    if changes.get("code") is not None:
        ensure_route_code_free(db, admin.organization_id, changes["code"], except_id=route.id)
    for field, value in changes.items():
        if value is not None:
            setattr(route, field, value)
    db.commit()
    db.refresh(route)
    return route_detail(db, route)


# --- Stops ----------------------------------------------------------------------------------


@router.post(
    "/routes/{route_id}/stops", response_model=RouteDetail, status_code=status.HTTP_201_CREATED
)
def add_stop(
    route_id: uuid.UUID, payload: StopCreate, admin: SchoolAdmin, db: DbSession
) -> RouteDetail:
    """Add a stop at the end of the route."""
    route = get_owned_or_404(db, Route, route_id, admin, what="route")
    last = db.scalar(select(func.max(Stop.sequence)).where(Stop.route_id == route.id)) or 0
    db.add(
        Stop(
            organization_id=admin.organization_id,
            route_id=route.id,
            name=payload.name,
            landmark=payload.landmark or None,
            sequence=last + 1,
            latitude=payload.latitude,
            longitude=payload.longitude,
        )
    )
    db.commit()
    return route_detail(db, route)


@router.put("/routes/{route_id}/stops/order", response_model=RouteDetail)
def reorder_stops(
    route_id: uuid.UUID, payload: StopOrder, admin: SchoolAdmin, db: DbSession
) -> RouteDetail:
    """Set the morning order. Every stop on the route must appear exactly once."""
    route = get_owned_or_404(db, Route, route_id, admin, what="route")
    by_id = {stop.id: stop for stop in stops_of(db, route.id)}
    if len(payload.stop_ids) != len(set(payload.stop_ids)) or set(payload.stop_ids) != set(by_id):
        raise HTTPException(
            UNPROCESSABLE,
            "List every stop on this route exactly once",
        )
    renumber([by_id[stop_id] for stop_id in payload.stop_ids])
    db.commit()
    return route_detail(db, route)


@router.patch("/stops/{stop_id}", response_model=StopRead)
def update_stop(stop_id: uuid.UUID, payload: StopUpdate, admin: SchoolAdmin, db: DbSession) -> Stop:
    stop = get_owned_or_404(db, Stop, stop_id, admin, what="stop")
    for field, value in payload.model_dump(exclude_unset=True).items():
        if field == "name":
            if value is not None:
                stop.name = value
        elif field == "landmark":
            stop.landmark = value or None
        else:
            setattr(stop, field, value)  # latitude/longitude: null clears them
    db.commit()
    db.refresh(stop)
    return stop


@router.delete("/stops/{stop_id}", response_model=RouteDetail)
def remove_stop(stop_id: uuid.UUID, admin: SchoolAdmin, db: DbSession) -> RouteDetail:
    """Remove a stop no child uses, and close the gap in the order."""
    stop = get_owned_or_404(db, Stop, stop_id, admin, what="stop")
    in_use = db.scalar(
        select(func.count(StudentRouteAssignment.id)).where(
            or_(
                StudentRouteAssignment.pickup_stop_id == stop.id,
                StudentRouteAssignment.dropoff_stop_id == stop.id,
            )
        )
    )
    if in_use:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Children are assigned to this stop. Move them to another stop first.",
        )
    route = get_owned_or_404(db, Route, stop.route_id, admin, what="route")
    db.delete(stop)
    db.flush()
    renumber(stops_of(db, route.id))
    db.commit()
    return route_detail(db, route)


# --- Runs -----------------------------------------------------------------------------------


@router.put("/routes/{route_id}/runs/{direction}", response_model=RunRead)
def set_run(
    route_id: uuid.UUID,
    direction: RunDirection,
    payload: RunUpsert,
    admin: SchoolAdmin,
    db: DbSession,
) -> RouteRun:
    """Create or replace the morning or afternoon run: time, vehicle and crew (D-21)."""
    route = get_owned_or_404(db, Route, route_id, admin, what="route")
    driver = crew_member(db, admin, payload.driver_membership_id, MembershipRole.DRIVER)
    conductor = (
        crew_member(db, admin, payload.conductor_membership_id, MembershipRole.CONDUCTOR)
        if payload.conductor_membership_id is not None
        else None
    )
    vehicle = None
    if payload.vehicle_id is not None:
        vehicle = get_owned_or_404(db, Vehicle, payload.vehicle_id, admin, what="vehicle")
        if not vehicle.is_active:
            raise HTTPException(UNPROCESSABLE, f"{vehicle.plate} is not in service")

    run = db.scalar(
        select(RouteRun).where(RouteRun.route_id == route.id, RouteRun.direction == direction)
    )
    if run is None:
        run = RouteRun(
            organization_id=admin.organization_id, route_id=route.id, direction=direction
        )
        db.add(run)
    run.departure_time = payload.departure_time
    run.vehicle_id = vehicle.id if vehicle else None
    run.driver_membership_id = driver.id
    run.conductor_membership_id = conductor.id if conductor else None
    db.commit()
    db.refresh(run)
    return run


@router.delete("/routes/{route_id}/runs/{direction}", status_code=status.HTTP_204_NO_CONTENT)
def remove_run(
    route_id: uuid.UUID, direction: RunDirection, admin: SchoolAdmin, db: DbSession
) -> None:
    route = get_owned_or_404(db, Route, route_id, admin, what="route")
    run = db.scalar(
        select(RouteRun).where(RouteRun.route_id == route.id, RouteRun.direction == direction)
    )
    if run is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such run")
    db.delete(run)
    db.commit()


# --- Vehicles -------------------------------------------------------------------------------


@router.get("/vehicles", response_model=list[VehicleRead])
def list_vehicles(admin: SchoolAdmin, db: DbSession) -> list[Vehicle]:
    return list(
        db.scalars(
            select(Vehicle)
            .where(Vehicle.organization_id == admin.organization_id)
            .order_by(Vehicle.plate)
        )
    )


@router.post("/vehicles", response_model=VehicleRead, status_code=status.HTTP_201_CREATED)
def add_vehicle(payload: VehicleCreate, admin: SchoolAdmin, db: DbSession) -> Vehicle:
    ensure_plate_free(db, admin.organization_id, payload.plate)
    vehicle = Vehicle(
        organization_id=admin.organization_id, plate=payload.plate, seats=payload.seats
    )
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return vehicle


@router.patch("/vehicles/{vehicle_id}", response_model=VehicleRead)
def update_vehicle(
    vehicle_id: uuid.UUID, payload: VehicleUpdate, admin: SchoolAdmin, db: DbSession
) -> Vehicle:
    vehicle = get_owned_or_404(db, Vehicle, vehicle_id, admin, what="vehicle")
    changes = payload.model_dump(exclude_unset=True)
    if changes.get("plate") is not None:
        ensure_plate_free(db, admin.organization_id, changes["plate"], except_id=vehicle.id)
    for field, value in changes.items():
        if value is not None:
            setattr(vehicle, field, value)
    db.commit()
    db.refresh(vehicle)
    return vehicle
