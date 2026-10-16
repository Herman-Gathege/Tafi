"""Typed contracts for the crew app (Sprint 4)."""

import uuid
from datetime import date, datetime, time
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.transport import RunDirection
from app.models.trip import BoardingKind, BoardingMethod, TripStatus


class TripSummary(BaseModel):
    """A run the crew is on today, and the trip so far if it has started."""

    id: uuid.UUID | None = None
    route_run_id: uuid.UUID
    route_code: str
    route_name: str
    direction: RunDirection
    departure_time: time
    vehicle_plate: str | None = None
    status: TripStatus
    service_date: date
    started_at: datetime | None = None
    ended_at: datetime | None = None
    boarded_count: int = 0
    dropped_off_count: int = 0
    absent_count: int = 0
    expected_count: int = 0


class ChildOnTrip(BaseModel):
    """One child expected on the trip, and where they are up to."""

    student_id: uuid.UUID
    first_name: str
    last_name: str
    grade: str | None = None
    pickup_stop: str | None = None
    dropoff_stop: str | None = None
    state: str  # pending | boarded | dropped_off | absent


class TripDetail(BaseModel):
    """Everything the crew screen shows for one trip."""

    id: uuid.UUID
    route_run_id: uuid.UUID
    route_code: str
    route_name: str
    direction: RunDirection
    departure_time: time
    vehicle_plate: str | None = None
    status: TripStatus
    service_date: date
    started_at: datetime | None = None
    ended_at: datetime | None = None
    children: list[ChildOnTrip] = []
    boarded_count: int = 0
    dropped_off_count: int = 0
    absent_count: int = 0
    location_count: int = 0
    last_location_at: datetime | None = None
    # What this crew member may do here (D-21).
    my_role: str = "driver"
    driver_alone: bool = False


class TripStart(BaseModel):
    """Start the trip for a run."""

    route_run_id: uuid.UUID
    service_date: date | None = None


class StoppedConfirmation(BaseModel):
    """A driver alone confirms the vehicle is stopped. The timestamp is what the API trusts."""

    confirmed_at: datetime


class BoardingEventCreate(BaseModel):
    """Mark one child on one trip."""

    student_id: uuid.UUID
    kind: BoardingKind
    # Required when the driver is alone on the run (D-21); the server checks the age of this.
    stopped_confirmed_at: datetime | None = None
    latitude: Decimal | None = Field(default=None, ge=-90, le=90)
    longitude: Decimal | None = Field(default=None, ge=-180, le=180)


class BoardingEventRead(BaseModel):
    """A recorded event, with the attribution D-21 requires."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    trip_id: uuid.UUID
    student_id: uuid.UUID
    kind: BoardingKind
    method: BoardingMethod
    recorded_by_membership_id: uuid.UUID
    recorded_at: datetime


class TripLocationCreate(BaseModel):
    """A position shared while the trip is running."""

    latitude: Decimal = Field(ge=-90, le=90)
    longitude: Decimal = Field(ge=-180, le=180)
    accuracy_m: Decimal | None = Field(default=None, ge=0)
    recorded_at: datetime | None = None


class TripLocationRead(BaseModel):
    """A stored position."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    trip_id: uuid.UUID
    recorded_by_membership_id: uuid.UUID
    latitude: Decimal
    longitude: Decimal
    accuracy_m: Decimal | None = None
    recorded_at: datetime
