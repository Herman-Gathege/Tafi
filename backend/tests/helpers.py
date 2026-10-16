"""Small factories shared by the auth, tenancy and school-data tests."""

from datetime import time, timedelta

from sqlalchemy.orm import Session

from app.core.clock import utcnow
from app.core.security import generate_token, hash_password, hash_token
from app.models.guardian import Guardian
from app.models.invitation import Invitation
from app.models.organization import Organization, OrganizationType
from app.models.student import Student
from app.models.transport import Route, RouteRun, RunDirection, Stop, Vehicle
from app.models.user import Membership, MembershipRole, User

PASSWORD = "correct-horse-battery"

# Made-up numbers only: never put a real phone number in test or seed data.
TEST_NUMBER = "+254700000001"


def make_user(
    db: Session,
    email: str,
    *,
    password: str = PASSWORD,
    name: str = "Test Person",
    platform_admin: bool = False,
) -> User:
    user = User(
        email=email,
        name=name,
        password_hash=hash_password(password),
        is_platform_admin=platform_admin,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def make_organization(
    db: Session, name: str = "Riverside Academy", type_: OrganizationType = OrganizationType.SCHOOL
) -> Organization:
    organization = Organization(name=name, type=type_)
    db.add(organization)
    db.commit()
    db.refresh(organization)
    return organization


def make_membership(
    db: Session,
    user: User,
    organization: Organization,
    role: MembershipRole = MembershipRole.SCHOOL_ADMIN,
) -> Membership:
    membership = Membership(user_id=user.id, organization_id=organization.id, role=role)
    db.add(membership)
    db.commit()
    db.refresh(membership)
    return membership


def make_invitation(
    db: Session, organization: Organization, email: str, *, expired: bool = False
) -> tuple[Invitation, str]:
    token = generate_token()
    invitation = Invitation(
        organization_id=organization.id,
        email=email,
        role=MembershipRole.SCHOOL_ADMIN,
        token_hash=hash_token(token),
        expires_at=utcnow() + (timedelta(days=-1) if expired else timedelta(days=7)),
    )
    db.add(invitation)
    db.commit()
    db.refresh(invitation)
    return invitation, token


def make_student(
    db: Session, organization: Organization, first_name: str = "Wanjiru", last_name: str = "Kamau"
) -> Student:
    student = Student(
        organization_id=organization.id, first_name=first_name, last_name=last_name, grade="4"
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


def make_guardian(
    db: Session,
    organization: Organization,
    *,
    number: str = TEST_NUMBER,
    full_name: str = "Test Guardian",
) -> Guardian:
    guardian = Guardian(
        organization_id=organization.id, full_name=full_name, whatsapp_number=number
    )
    db.add(guardian)
    db.commit()
    db.refresh(guardian)
    return guardian


def make_route(db: Session, organization: Organization, code: str = "R1") -> Route:
    route = Route(organization_id=organization.id, code=code, name=f"Route {code}")
    db.add(route)
    db.commit()
    db.refresh(route)
    return route


def make_stop(db: Session, route: Route, name: str = "Main gate", sequence: int = 1) -> Stop:
    stop = Stop(
        organization_id=route.organization_id, route_id=route.id, name=name, sequence=sequence
    )
    db.add(stop)
    db.commit()
    db.refresh(stop)
    return stop


def make_vehicle(db: Session, organization: Organization, plate: str = "KDA 213A") -> Vehicle:
    vehicle = Vehicle(organization_id=organization.id, plate=plate, seats=26)
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return vehicle


def make_run(
    db: Session,
    route: Route,
    driver: Membership,
    *,
    conductor: Membership | None = None,
    vehicle: Vehicle | None = None,
    direction: RunDirection = RunDirection.MORNING,
) -> RouteRun:
    run = RouteRun(
        organization_id=route.organization_id,
        route_id=route.id,
        direction=direction,
        departure_time=time(6, 30),
        vehicle_id=vehicle.id if vehicle else None,
        driver_membership_id=driver.id,
        conductor_membership_id=conductor.id if conductor else None,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run
