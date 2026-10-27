"""Operational commands. Run with `python -m app.cli --help`."""

import argparse
from collections.abc import Sequence
from datetime import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.guardian import (
    ConsentMethod,
    Guardian,
    GuardianRelationship,
    GuardianStatus,
    StudentGuardian,
)
from app.models.organization import Organization, OrganizationType
from app.models.student import Student, StudentStatus
from app.models.transport import (
    Route,
    RouteRun,
    RunDirection,
    Stop,
    StudentRouteAssignment,
    Vehicle,
)
from app.models.user import Membership, MembershipRole, User
from app.schemas.common import normalise_email
from app.services.consent import record_consent
from app.services.trips import kenya_today

# Development only. The password is in the repository, so `seed-demo` refuses to run
# anywhere but `APP_ENV=local` (D-35).
DEMO_PASSWORD = "TafiDemo2026!"
DEMO_SCHOOL = "Riverside Academy (demo)"
DEMO_ACCOUNTS = [
    ("demo.platform@tafi.test", "Demo Platform Admin", "platform admin"),
    ("demo.admin@tafi.test", "Demo School Admin", "school admin"),
    ("demo.driver@tafi.test", "Demo Driver", "driver"),
    ("demo.conductor@tafi.test", "Demo Conductor", "conductor"),
    ("demo.parent@tafi.test", "Demo Parent", "parent"),
]


class NotLocalError(RuntimeError):
    """A development-only command was run outside `APP_ENV=local`."""


def create_platform_admin(email: str, password: str, name: str | None = None) -> str:
    """Create the first Tafi account, or promote an existing one.

    Self-signup is available for schools (D-37); this remains the platform-admin path.
    """
    address = normalise_email(email)
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == address))
        if user is None:
            user = User(
                email=address,
                name=name or address.split("@")[0],
                password_hash=hash_password(password),
                is_platform_admin=True,
            )
            db.add(user)
            action = "created"
        else:
            user.is_platform_admin = True
            user.is_active = True
            user.password_hash = hash_password(password)
            if name:
                user.name = name
            action = "promoted"
        db.commit()
        return f"Platform admin {action}: {address}"


def _demo_user(db: Session, email: str, name: str, *, platform: bool = False) -> User:
    """One account per role, with a known development password."""
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(
            email=email,
            name=name,
            password_hash=hash_password(DEMO_PASSWORD),
            is_platform_admin=platform,
        )
        db.add(user)
        db.flush()
        return user
    user.name = name
    user.password_hash = hash_password(DEMO_PASSWORD)
    user.is_active = True
    user.is_platform_admin = platform or user.is_platform_admin
    return user


def _demo_membership(
    db: Session, user: User, org: Organization, role: MembershipRole
) -> Membership:
    membership = db.scalar(
        select(Membership).where(
            Membership.user_id == user.id, Membership.organization_id == org.id
        )
    )
    if membership is None:
        membership = Membership(user_id=user.id, organization_id=org.id, role=role)
        db.add(membership)
        db.flush()
    else:
        membership.role = role
        membership.is_active = True
    return membership


def seed_demo() -> list[str]:
    """Create a demo school with one account per role. Safe to run repeatedly. Local only."""
    if get_settings().app_env != "local":
        raise NotLocalError(
            "seed-demo only runs with APP_ENV=local: its passwords are in the repository."
        )

    with SessionLocal() as db:
        org = db.scalar(select(Organization).where(Organization.name == DEMO_SCHOOL))
        if org is None:
            org = Organization(name=DEMO_SCHOOL, type=OrganizationType.SCHOOL)
            db.add(org)
            db.flush()

        _demo_user(db, "demo.platform@tafi.test", "Demo Platform Admin", platform=True)
        admin = _demo_user(db, "demo.admin@tafi.test", "Demo School Admin")
        driver = _demo_user(db, "demo.driver@tafi.test", "Demo Driver")
        conductor = _demo_user(db, "demo.conductor@tafi.test", "Demo Conductor")
        parent = _demo_user(db, "demo.parent@tafi.test", "Demo Parent")

        _demo_membership(db, admin, org, MembershipRole.SCHOOL_ADMIN)
        driver_membership = _demo_membership(db, driver, org, MembershipRole.DRIVER)
        conductor_membership = _demo_membership(db, conductor, org, MembershipRole.CONDUCTOR)
        _demo_membership(db, parent, org, MembershipRole.PARENT)

        # The parent login is for dashboard testing until Sprint 5 replaces it with a
        # one-time WhatsApp code (D-20, D-37).
        guardian = db.scalar(
            select(Guardian).where(
                Guardian.organization_id == org.id, Guardian.whatsapp_number == "+254700000001"
            )
        )
        if guardian is None:
            guardian = Guardian(
                organization_id=org.id,
                full_name="Demo Parent",
                whatsapp_number="+254700000001",
                email="demo.parent@tafi.test",
                status=GuardianStatus.CONFIRMED,
                user_id=parent.id,
            )
            db.add(guardian)
            db.flush()
        else:
            guardian.email = "demo.parent@tafi.test"
            guardian.status = GuardianStatus.CONFIRMED
            guardian.user_id = parent.id
        record_consent(db, guardian, method=ConsentMethod.SCHOOL_RECORDED)

        route = db.scalar(select(Route).where(Route.organization_id == org.id, Route.code == "R1"))
        if route is None:
            route = Route(organization_id=org.id, code="R1", name="Kileleshwa")
            db.add(route)
            db.flush()

        stops: list[Stop] = []
        for sequence, name in enumerate(["Main gate", "Shops", "Church"], start=1):
            stop = db.scalar(select(Stop).where(Stop.route_id == route.id, Stop.name == name))
            if stop is None:
                stop = Stop(organization_id=org.id, route_id=route.id, name=name, sequence=sequence)
                db.add(stop)
                db.flush()
            stops.append(stop)

        vehicle = db.scalar(
            select(Vehicle).where(Vehicle.organization_id == org.id, Vehicle.plate == "KDA 213A")
        )
        if vehicle is None:
            vehicle = Vehicle(organization_id=org.id, plate="KDA 213A", seats=26)
            db.add(vehicle)
            db.flush()

        # Morning: driver and conductor. Afternoon: driver alone, to show the stopped rule.
        for direction, departure, with_conductor in (
            (RunDirection.MORNING, time(6, 30), True),
            (RunDirection.AFTERNOON, time(16, 10), False),
        ):
            run = db.scalar(
                select(RouteRun).where(
                    RouteRun.route_id == route.id, RouteRun.direction == direction
                )
            )
            if run is None:
                run = RouteRun(
                    organization_id=org.id,
                    route_id=route.id,
                    direction=direction,
                    departure_time=departure,
                    driver_membership_id=driver_membership.id,
                )
                db.add(run)
            run.vehicle_id = vehicle.id
            run.driver_membership_id = driver_membership.id
            run.conductor_membership_id = conductor_membership.id if with_conductor else None
            db.flush()

        for first, last, grade in [
            ("Wanjiru", "Otieno", "Grade 4"),
            ("Kamau", "Otieno", "Grade 1"),
        ]:
            student = db.scalar(
                select(Student).where(
                    Student.organization_id == org.id,
                    Student.first_name == first,
                    Student.last_name == last,
                )
            )
            if student is None:
                student = Student(
                    organization_id=org.id,
                    first_name=first,
                    last_name=last,
                    grade=grade,
                    status=StudentStatus.ACTIVE,
                )
                db.add(student)
                db.flush()
            link = db.scalar(
                select(StudentGuardian).where(
                    StudentGuardian.student_id == student.id,
                    StudentGuardian.guardian_id == guardian.id,
                )
            )
            if link is None:
                db.add(
                    StudentGuardian(
                        organization_id=org.id,
                        student_id=student.id,
                        guardian_id=guardian.id,
                        relationship=GuardianRelationship.MOTHER,
                        is_primary=True,
                    )
                )
            assignment = db.scalar(
                select(StudentRouteAssignment).where(
                    StudentRouteAssignment.student_id == student.id,
                    StudentRouteAssignment.active_to.is_(None),
                )
            )
            if assignment is None:
                db.add(
                    StudentRouteAssignment(
                        organization_id=org.id,
                        student_id=student.id,
                        route_id=route.id,
                        pickup_stop_id=stops[0].id,
                        dropoff_stop_id=stops[2].id,
                        active_from=kenya_today(),
                    )
                )

        db.commit()

    lines = [f"Demo school: {DEMO_SCHOOL}", "", f"{'role':<16}{'email':<28}password"]
    for email, _name, role in DEMO_ACCOUNTS:
        lines.append(f"{role:<16}{email:<28}{DEMO_PASSWORD}")
    lines += ["", "Development only — never use these accounts outside local."]
    return lines


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="app.cli", description="Tafi operations")
    subcommands = parser.add_subparsers(dest="command", required=True)

    admin = subcommands.add_parser(
        "create-platform-admin", help="create (or promote) a Tafi staff account"
    )
    admin.add_argument("--email", required=True)
    admin.add_argument("--password", required=True)
    admin.add_argument("--name", default=None)

    subcommands.add_parser("seed-demo", help="local only: one demo account per role")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "create-platform-admin":
        print(create_platform_admin(args.email, args.password, args.name))
    elif args.command == "seed-demo":
        try:
            for line in seed_demo():
                print(line)
        except NotLocalError as error:
            print(error)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
