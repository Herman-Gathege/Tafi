"""Typed contracts for the organizations endpoints."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.organization import OrganizationType


class OrganizationCreate(BaseModel):
    """Payload for creating an organization."""

    name: str = Field(min_length=1, max_length=255)
    type: OrganizationType = OrganizationType.SCHOOL


class OrganizationRead(BaseModel):
    """Organization as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    type: OrganizationType
    created_at: datetime
    updated_at: datetime
