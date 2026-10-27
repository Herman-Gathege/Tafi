"""What a parent sees about their own children (no other family's data)."""

import uuid
from datetime import datetime

from pydantic import BaseModel


class ParentChild(BaseModel):
    """One child of the signed-in parent, and how they get to school."""

    student_id: uuid.UUID
    first_name: str
    last_name: str
    grade: str | None = None
    route_code: str | None = None
    route_name: str | None = None
    pickup_stop: str | None = None
    dropoff_stop: str | None = None


class ParentStopRequest(BaseModel):
    """A stop change this parent has asked the school for."""

    id: uuid.UUID
    student_id: uuid.UUID
    status: str
    requested_at: datetime | None = None


class ParentMe(BaseModel):
    """The signed-in guardian, their children and their consent state."""

    guardian_id: uuid.UUID
    full_name: str
    whatsapp_number: str
    status: str
    has_consent: bool
    school_name: str
    children: list[ParentChild] = []
    stop_requests: list[ParentStopRequest] = []
