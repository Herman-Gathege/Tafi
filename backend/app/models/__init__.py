"""ORM models. Import them here so Alembic autoload sees the metadata."""

from app.models.guardian import (
    ConsentMethod,
    Guardian,
    GuardianConsent,
    GuardianInvite,
    GuardianRelationship,
    GuardianStatus,
    StudentGuardian,
)
from app.models.invitation import Invitation
from app.models.organization import Organization, OrganizationType
from app.models.password_reset import PasswordResetToken
from app.models.student import CardStatus, ChildCard, EmergencyContact, Student, StudentStatus
from app.models.transport import (
    RequestStatus,
    Route,
    RouteRun,
    RunDirection,
    Stop,
    StopChangeRequest,
    StudentRouteAssignment,
    Vehicle,
)
from app.models.trip import (
    BoardingEvent,
    BoardingKind,
    BoardingMethod,
    Trip,
    TripLocation,
    TripStatus,
)
from app.models.user import CREW_ROLES, Membership, MembershipRole, User

__all__ = [
    "BoardingEvent",
    "BoardingKind",
    "BoardingMethod",
    "CREW_ROLES",
    "CardStatus",
    "ChildCard",
    "ConsentMethod",
    "EmergencyContact",
    "Guardian",
    "GuardianConsent",
    "GuardianInvite",
    "GuardianRelationship",
    "GuardianStatus",
    "Invitation",
    "Membership",
    "MembershipRole",
    "Organization",
    "OrganizationType",
    "PasswordResetToken",
    "RequestStatus",
    "Route",
    "RouteRun",
    "RunDirection",
    "Stop",
    "StopChangeRequest",
    "Student",
    "StudentGuardian",
    "StudentRouteAssignment",
    "StudentStatus",
    "Trip",
    "TripLocation",
    "TripStatus",
    "User",
    "Vehicle",
]
