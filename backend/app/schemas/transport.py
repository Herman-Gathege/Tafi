"""Typed contracts for a school's routes, stops, vehicles and runs."""

import re
import uuid
from datetime import time
from decimal import ROUND_HALF_UP, Decimal
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, StringConstraints

from app.models.transport import RunDirection

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]
OptionalText = Annotated[str, StringConstraints(strip_whitespace=True, max_length=255)]
RouteCode = Annotated[
    str, StringConstraints(strip_whitespace=True, to_upper=True, min_length=1, max_length=32)
]

_PLATE = re.compile(r"^[A-Z0-9 ]{2,16}$")
_SIX_PLACES = Decimal("0.000001")


def normalise_plate(value: str) -> str:
    """Upper-case and single-space a number plate: " kda  213a " becomes "KDA 213A"."""
    plate = " ".join(value.upper().split())
    if not _PLATE.match(plate):
        raise ValueError("Enter a number plate using letters, numbers and spaces")
    return plate


def round_coordinate(value: Decimal) -> Decimal:
    """Six decimal places (about 10 cm) is plenty; map apps paste far more."""
    return value.quantize(_SIX_PLACES, rounding=ROUND_HALF_UP)


Plate = Annotated[str, AfterValidator(normalise_plate)]
Latitude = Annotated[Decimal, Field(ge=-90, le=90), AfterValidator(round_coordinate)]
Longitude = Annotated[Decimal, Field(ge=-180, le=180), AfterValidator(round_coordinate)]


# --- Routes ---------------------------------------------------------------------------------


class RouteCreate(BaseModel):
    """A new route, e.g. code "R1", name "Kileleshwa"."""

    code: RouteCode
    name: Name


class RouteUpdate(BaseModel):
    """Change any of a route's details. Deactivate instead of deleting."""

    code: RouteCode | None = None
    name: Name | None = None
    is_active: bool | None = None


class RouteSummary(BaseModel):
    """A route in the list."""

    id: uuid.UUID
    code: str
    name: str
    is_active: bool
    stop_count: int


# --- Stops ----------------------------------------------------------------------------------


class StopCreate(BaseModel):
    """A stop added to the end of a route."""

    name: Name
    landmark: OptionalText | None = None
    latitude: Latitude | None = None
    longitude: Longitude | None = None


class StopUpdate(BaseModel):
    """Change a stop's details. Use the order endpoint to move it."""

    name: Name | None = None
    landmark: OptionalText | None = None
    latitude: Latitude | None = None
    longitude: Longitude | None = None


class StopOrder(BaseModel):
    """Every stop on the route, in the new morning order."""

    stop_ids: list[uuid.UUID] = Field(min_length=1)


class StopRead(BaseModel):
    """A stop as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    landmark: str | None
    sequence: int
    latitude: float | None
    longitude: float | None


# --- Runs -----------------------------------------------------------------------------------


class RunUpsert(BaseModel):
    """Who runs a route in the morning or afternoon (D-21: driver required, conductor optional)."""

    departure_time: time
    vehicle_id: uuid.UUID | None = None
    driver_membership_id: uuid.UUID
    conductor_membership_id: uuid.UUID | None = None


class RunRead(BaseModel):
    """A run as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    direction: RunDirection
    departure_time: time
    vehicle_id: uuid.UUID | None
    driver_membership_id: uuid.UUID
    conductor_membership_id: uuid.UUID | None


class RouteDetail(BaseModel):
    """One route with its stops (in order) and its runs."""

    id: uuid.UUID
    code: str
    name: str
    is_active: bool
    stops: list[StopRead]
    runs: list[RunRead]


# --- Vehicles -------------------------------------------------------------------------------


class VehicleCreate(BaseModel):
    """A bus or van."""

    plate: Plate
    seats: int = Field(ge=1, le=100)


class VehicleUpdate(BaseModel):
    """Change a vehicle's details. Deactivate instead of deleting."""

    plate: Plate | None = None
    seats: int | None = Field(default=None, ge=1, le=100)
    is_active: bool | None = None


class VehicleRead(BaseModel):
    """A vehicle as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    plate: str
    seats: int
    is_active: bool
