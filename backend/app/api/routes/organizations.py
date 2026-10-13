"""Organization (tenant) endpoints — the first end-to-end slice of the API."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.organization import Organization
from app.schemas.organization import OrganizationCreate, OrganizationRead

router = APIRouter(prefix="/api/v1/organizations", tags=["organizations"])

DbSession = Annotated[Session, Depends(get_db)]


@router.get("", response_model=list[OrganizationRead])
def list_organizations(db: DbSession) -> list[Organization]:
    """List every organization. Scoping by tenant arrives with auth in Sprint 2."""
    return list(db.scalars(select(Organization).order_by(Organization.created_at)))


@router.post("", response_model=OrganizationRead, status_code=status.HTTP_201_CREATED)
def create_organization(payload: OrganizationCreate, db: DbSession) -> Organization:
    """Create an organization."""
    organization = Organization(name=payload.name, type=payload.type)
    db.add(organization)
    db.commit()
    db.refresh(organization)
    return organization
