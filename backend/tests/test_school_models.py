"""The school's data holds together, and the database refuses the obvious mistakes."""

import uuid
from datetime import date

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.clock import utcnow
from app.core.security import generate_token
from app.models.guardian import (
    ConsentMethod,
    GuardianConsent,
    GuardianRelationship,
    GuardianStatus,
    StudentGuardian,
)
from app.models.student import CardStatus, ChildCard, EmergencyContact, StudentStatus
from app.models.transport import RouteRun, RunDirection, StudentRouteAssignment
from app.models.user import CREW_ROLES, MembershipRole
from tests.helpers import (
    make_guardian,
    make_membership,
    make_organization,
    make_route,
    make_run,
    make_stop,
    make_student,
    make_user,
    make_vehicle,
)


def test_a_school_can_hold_its_full_roster(db_session: Session) -> None:
    school = make_organization(db_session)
    driver = make_membership(
        db_session, make_user(db_session, "driver@example.com"), school, MembershipRole.DRIVER
    )
    conductor = make_membership(
        db_session, make_user(db_session, "mercy@example.com"), school, MembershipRole.CONDUCTOR
    )
    route = make_route(db_session, school)
    gate = make_stop(db_session, route, "Main gate", 1)
    shops = make_stop(db_session, route, "Shops", 2)
    vehicle = make_vehicle(db_session, school)
    make_run(db_session, route, driver, conductor=conductor, vehicle=vehicle)
    make_run(db_session, route, driver, direction=RunDirection.AFTERNOON)

    student = make_student(db_session, school)
    guardian = make_guardian(db_session, school)
    db_session.add_all(
        [
            StudentGuardian(
                organization_id=school.id,
                student_id=student.id,
                guardian_id=guardian.id,
                relationship=GuardianRelationship.MOTHER,
                is_primary=True,
            ),
            GuardianConsent(
                organization_id=school.id,
                guardian_id=guardian.id,
                consent_version="2026-10",
                method=ConsentMethod.INVITE_LINK,
                given_at=utcnow(),
            ),
            EmergencyContact(
                organization_id=school.id,
                student_id=student.id,
                name="Aunt",
                phone="+254700000002",
            ),
            StudentRouteAssignment(
                organization_id=school.id,
                student_id=student.id,
                route_id=route.id,
                pickup_stop_id=gate.id,
                dropoff_stop_id=shops.id,
                active_from=date(2027, 1, 6),
            ),
            ChildCard(organization_id=school.id, student_id=student.id, code=generate_token()),
        ]
    )
    db_session.commit()

    assert db_session.scalar(select(func.count()).select_from(RouteRun)) == 2
    assert student.status == StudentStatus.ACTIVE
    assert guardian.status == GuardianStatus.INVITED
    card = db_session.scalars(select(ChildCard)).one()
    assert card.status == CardStatus.ACTIVE
    assert student.first_name not in card.code


def test_conductor_is_a_crew_role(db_session: Session) -> None:
    school = make_organization(db_session)
    membership = make_membership(
        db_session, make_user(db_session, "mercy@example.com"), school, MembershipRole.CONDUCTOR
    )
    db_session.expire_all()

    assert membership.role == MembershipRole.CONDUCTOR
    assert MembershipRole.CONDUCTOR in CREW_ROLES
    assert MembershipRole.SCHOOL_ADMIN not in CREW_ROLES


def test_a_run_needs_a_driver_but_not_a_conductor(db_session: Session) -> None:
    school = make_organization(db_session)
    route = make_route(db_session, school)
    driver = make_membership(
        db_session, make_user(db_session, "driver@example.com"), school, MembershipRole.DRIVER
    )

    alone = make_run(db_session, route, driver)
    assert alone.conductor_membership_id is None

    db_session.add(
        RouteRun(
            organization_id=school.id,
            route_id=route.id,
            direction=RunDirection.AFTERNOON,
            departure_time=alone.departure_time,
        )
    )
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_a_whatsapp_number_is_unique_within_a_school_only(db_session: Session) -> None:
    riverside = make_organization(db_session, "Riverside Academy")
    hilltop = make_organization(db_session, "Hilltop School")
    make_guardian(db_session, riverside, number="+254700000010")

    # The same parent can have children at two schools.
    make_guardian(db_session, hilltop, number="+254700000010")

    with pytest.raises(IntegrityError):
        make_guardian(db_session, riverside, number="+254700000010")


def test_a_child_has_only_one_current_route(db_session: Session) -> None:
    school = make_organization(db_session)
    student = make_student(db_session, school)
    first = make_route(db_session, school, "R1")
    second = make_route(db_session, school, "R2")

    def assign(route_id: uuid.UUID, *, ended: bool = False) -> None:
        db_session.add(
            StudentRouteAssignment(
                organization_id=school.id,
                student_id=student.id,
                route_id=route_id,
                active_from=date(2027, 1, 6),
                active_to=date(2027, 2, 1) if ended else None,
            )
        )
        db_session.commit()

    assign(first.id, ended=True)  # history is kept
    assign(second.id)  # the current one

    with pytest.raises(IntegrityError):
        assign(first.id)


def test_a_route_code_and_a_plate_are_unique_within_a_school(db_session: Session) -> None:
    school = make_organization(db_session)
    make_route(db_session, school, "R1")
    make_vehicle(db_session, school, "KDA 213A")

    with pytest.raises(IntegrityError):
        make_route(db_session, school, "R1")
    db_session.rollback()

    with pytest.raises(IntegrityError):
        make_vehicle(db_session, school, "KDA 213A")
