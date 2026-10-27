"""The crew app: trips, marks, the driver-alone rule and location (Sprint 4)."""

from datetime import date, time, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.clock import utcnow
from app.models.organization import Organization
from app.models.student import Student, StudentStatus
from app.models.transport import (
    Route,
    RouteRun,
    RunDirection,
    Stop,
    StudentRouteAssignment,
    Vehicle,
)
from app.models.trip import BoardingEvent, Trip, TripStatus
from app.models.user import Membership, MembershipRole
from app.services import trips as trip_service
from tests.helpers import PASSWORD, make_membership, make_organization, make_user


def add_rider(
    db: Session,
    organization: Organization,
    route: Route,
    first_name: str,
    *,
    pickup: Stop | None,
    dropoff: Stop | None,
) -> Student:
    student = Student(
        organization_id=organization.id,
        first_name=first_name,
        last_name="Otieno",
        status=StudentStatus.ACTIVE,
    )
    db.add(student)
    db.flush()
    db.add(
        StudentRouteAssignment(
            organization_id=organization.id,
            student_id=student.id,
            route_id=route.id,
            pickup_stop_id=pickup.id if pickup else None,
            dropoff_stop_id=dropoff.id if dropoff else None,
            active_from=date(2026, 1, 1),
        )
    )
    db.commit()
    return student


def build_school(
    db: Session, *, with_conductor: bool = False, direction: RunDirection = RunDirection.MORNING
):
    """A school with one route, one child on it, one run, and its crew."""
    organization = make_organization(db, "Crew Test School")

    route = Route(organization_id=organization.id, code="R1", name="Kileleshwa")
    db.add(route)
    db.flush()

    stops = []
    for sequence, name in enumerate(["Main gate", "Shops"], start=1):
        stop = Stop(
            organization_id=organization.id, route_id=route.id, name=name, sequence=sequence
        )
        db.add(stop)
        stops.append(stop)
    db.flush()

    vehicle = Vehicle(organization_id=organization.id, plate="KDA213A", seats=26)
    db.add(vehicle)
    db.flush()

    driver = make_membership(
        db, make_user(db, "driver@example.test"), organization, MembershipRole.DRIVER
    )
    conductor = None
    if with_conductor:
        conductor = make_membership(
            db, make_user(db, "conductor@example.test"), organization, MembershipRole.CONDUCTOR
        )

    run = RouteRun(
        organization_id=organization.id,
        route_id=route.id,
        direction=direction,
        departure_time=time(6, 30),
        vehicle_id=vehicle.id,
        driver_membership_id=driver.id,
        conductor_membership_id=conductor.id if conductor else None,
    )
    db.add(run)
    db.flush()

    student = add_rider(db, organization, route, "Wanjiru", pickup=stops[0], dropoff=stops[1])
    return organization, route, run, student, driver, conductor


def sign_in(client: TestClient, email: str):
    return client.post("/api/v1/auth/sign-in", json={"email": email, "password": PASSWORD})


def start_trip(client: TestClient, run) -> dict:
    response = client.post("/api/v1/crew/trips", json={"route_run_id": str(run.id)})
    assert response.status_code == 201, response.text
    return response.json()


def test_crew_sees_their_run_and_starts_a_trip(client: TestClient, db_session: Session) -> None:
    _, _, run, _, _, _ = build_school(db_session)
    assert sign_in(client, "driver@example.test").status_code == 200

    today = client.get("/api/v1/crew/trips/today")
    assert today.status_code == 200
    assert len(today.json()) == 1
    assert today.json()[0]["status"] == "scheduled"
    assert today.json()[0]["expected_count"] == 1

    trip = start_trip(client, run)
    assert trip["status"] == "active"
    assert trip["route_code"] == "R1"
    assert trip["children"][0]["state"] == "pending"
    assert trip["children"][0]["stop"] == "Main gate"


def test_starting_twice_returns_the_same_trip(client: TestClient, db_session: Session) -> None:
    _, _, run, _, _, _ = build_school(db_session)
    sign_in(client, "driver@example.test")
    first = start_trip(client, run)
    second = start_trip(client, run)
    assert first["id"] == second["id"]
    assert client.get("/api/v1/crew/trips/today").json()[0]["status"] == "active"


# --- Fix 7: the trip date is always today, Kenya time ------------------------------------------


def test_the_phone_cannot_choose_the_trip_date(client: TestClient, db_session: Session) -> None:
    _, _, run, _, _, _ = build_school(db_session)
    sign_in(client, "driver@example.test")

    response = client.post(
        "/api/v1/crew/trips", json={"route_run_id": str(run.id), "service_date": "2020-01-01"}
    )

    assert response.status_code == 201
    assert response.json()["service_date"] == trip_service.kenya_today().isoformat()


# --- Fix 3: "I am stopped" is recorded by the server -----------------------------------------


def test_a_driver_alone_must_press_i_am_stopped_before_marking(
    client: TestClient, db_session: Session
) -> None:
    _, _, run, student, _, _ = build_school(db_session)
    sign_in(client, "driver@example.test")
    trip = start_trip(client, run)
    assert trip["must_confirm_stopped"] is True
    assert trip["stopped_confirmed_at"] is None
    events = f"/api/v1/crew/trips/{trip['id']}/events"

    refused = client.post(events, json={"student_id": str(student.id), "kind": "boarded"})
    assert refused.status_code == 409
    assert "stopped" in refused.json()["detail"].lower()

    confirmation = client.post(f"/api/v1/crew/trips/{trip['id']}/stopped")
    assert confirmation.status_code == 200
    assert confirmation.json()["valid_for_seconds"] == 120

    marked = client.post(events, json={"student_id": str(student.id), "kind": "boarded"})
    assert marked.status_code == 201, marked.text
    assert marked.json()["method"] == "manual"
    assert marked.json()["recorded_by_membership_id"]
    # The mark carries the confirmation it relied on, as the server recorded it.
    assert marked.json()["stopped_confirmed_at"] is not None
    assert client.get(f"/api/v1/crew/trips/{trip['id']}").json()["stopped_confirmed_at"]


def test_a_time_sent_by_the_phone_is_never_trusted(client: TestClient, db_session: Session) -> None:
    """Herman's version accepted any recent timestamp from the phone. Now it is ignored."""
    _, _, run, student, _, _ = build_school(db_session)
    sign_in(client, "driver@example.test")
    trip = start_trip(client, run)

    forged = client.post(
        f"/api/v1/crew/trips/{trip['id']}/events",
        json={
            "student_id": str(student.id),
            "kind": "boarded",
            "stopped_confirmed_at": utcnow().isoformat(),
        },
    )

    assert forged.status_code == 409


def test_an_old_stopped_confirmation_must_be_renewed(
    client: TestClient, db_session: Session
) -> None:
    _, _, run, student, _, _ = build_school(db_session)
    sign_in(client, "driver@example.test")
    trip = start_trip(client, run)
    client.post(f"/api/v1/crew/trips/{trip['id']}/stopped")

    stored = db_session.scalars(select(Trip)).one()
    stored.stopped_confirmed_at = utcnow() - timedelta(minutes=5)
    db_session.commit()

    response = client.post(
        f"/api/v1/crew/trips/{trip['id']}/events",
        json={"student_id": str(student.id), "kind": "boarded"},
    )
    assert response.status_code == 409


def test_a_conductor_marks_without_confirming_stopped(
    client: TestClient, db_session: Session
) -> None:
    _, _, run, student, _, _ = build_school(db_session, with_conductor=True)
    sign_in(client, "conductor@example.test")
    trip = start_trip(client, run)
    assert trip["must_confirm_stopped"] is False

    marked = client.post(
        f"/api/v1/crew/trips/{trip['id']}/events",
        json={"student_id": str(student.id), "kind": "boarded"},
    )
    assert marked.status_code == 201, marked.text
    assert marked.json()["stopped_confirmed_at"] is None


# --- Fix 5: each run carries its own riders, in stop order -----------------------------------


@pytest.mark.parametrize(
    ("direction", "expected"),
    [
        # Morning: children with a pickup stop, first stop first.
        (
            RunDirection.MORNING,
            [("Baraka", "Main gate"), ("Wanjiru", "Main gate"), ("Amani", "Shops")],
        ),
        # Afternoon: children with a drop-off stop, last stop first (same stop: by name).
        (RunDirection.AFTERNOON, [("Juma", "Shops"), ("Wanjiru", "Shops"), ("Amani", "Main gate")]),
    ],
)
def test_each_run_carries_its_own_riders_in_stop_order(
    client: TestClient, db_session: Session, direction: RunDirection, expected: list
) -> None:
    organization, route, run, _, _, _ = build_school(
        db_session, with_conductor=True, direction=direction
    )
    gate, shops = db_session.scalars(select(Stop).order_by(Stop.sequence)).all()
    add_rider(db_session, organization, route, "Amani", pickup=shops, dropoff=gate)
    add_rider(db_session, organization, route, "Baraka", pickup=gate, dropoff=None)  # morning only
    add_rider(db_session, organization, route, "Juma", pickup=None, dropoff=shops)  # afternoon only
    sign_in(client, "conductor@example.test")

    trip = start_trip(client, run)

    assert [(c["first_name"], c["stop"]) for c in trip["children"]] == expected
    summary = client.get("/api/v1/crew/trips/today").json()[0]
    assert summary["expected_count"] == len(expected)


def test_a_child_who_does_not_ride_this_run_cannot_be_marked(
    client: TestClient, db_session: Session
) -> None:
    organization, route, run, _, _, _ = build_school(
        db_session, with_conductor=True, direction=RunDirection.AFTERNOON
    )
    gate = db_session.scalars(select(Stop).where(Stop.sequence == 1)).one()
    morning_only = add_rider(db_session, organization, route, "Baraka", pickup=gate, dropoff=None)
    sign_in(client, "conductor@example.test")
    trip = start_trip(client, run)

    response = client.post(
        f"/api/v1/crew/trips/{trip['id']}/events",
        json={"student_id": str(morning_only.id), "kind": "boarded"},
    )
    assert response.status_code == 400


# --- The boarding rules ------------------------------------------------------------------------


def test_boarded_then_dropped_off_and_the_rules_between(
    client: TestClient, db_session: Session
) -> None:
    _, _, run, student, _, _ = build_school(db_session, with_conductor=True)
    sign_in(client, "conductor@example.test")
    trip = start_trip(client, run)
    events = f"/api/v1/crew/trips/{trip['id']}/events"

    before_boarding = client.post(
        events, json={"student_id": str(student.id), "kind": "dropped_off"}
    )
    assert before_boarding.status_code == 400

    boarded = client.post(events, json={"student_id": str(student.id), "kind": "boarded"})
    assert boarded.status_code == 201

    duplicate = client.post(events, json={"student_id": str(student.id), "kind": "boarded"})
    assert duplicate.status_code == 409

    absent_after = client.post(events, json={"student_id": str(student.id), "kind": "absent"})
    assert absent_after.status_code == 409

    dropped = client.post(events, json={"student_id": str(student.id), "kind": "dropped_off"})
    assert dropped.status_code == 201

    detail = client.get(f"/api/v1/crew/trips/{trip['id']}")
    assert detail.status_code == 200
    assert detail.json()["children"][0]["state"] == "dropped_off"
    assert detail.json()["dropped_off_count"] == 1


def test_a_child_not_on_the_route_cannot_be_marked(client: TestClient, db_session: Session) -> None:
    organization, _, run, _, _, _ = build_school(db_session, with_conductor=True)
    stranger = Student(
        organization_id=organization.id,
        first_name="Other",
        last_name="Child",
        status=StudentStatus.ACTIVE,
    )
    db_session.add(stranger)
    db_session.commit()

    sign_in(client, "conductor@example.test")
    trip = start_trip(client, run)
    response = client.post(
        f"/api/v1/crew/trips/{trip['id']}/events",
        json={"student_id": str(stranger.id), "kind": "boarded"},
    )
    assert response.status_code == 400


def test_ending_a_trip_stops_further_marks(client: TestClient, db_session: Session) -> None:
    _, _, run, student, _, _ = build_school(db_session, with_conductor=True)
    sign_in(client, "conductor@example.test")
    trip = start_trip(client, run)

    ended = client.post(f"/api/v1/crew/trips/{trip['id']}/end")
    assert ended.status_code == 200
    assert ended.json()["status"] == "completed"

    late = client.post(
        f"/api/v1/crew/trips/{trip['id']}/events",
        json={"student_id": str(student.id), "kind": "boarded"},
    )
    assert late.status_code == 409
    assert client.post(f"/api/v1/crew/trips/{trip['id']}/stopped").status_code == 409

    twice = client.post(f"/api/v1/crew/trips/{trip['id']}/end")
    assert twice.status_code == 409


def test_location_is_recorded_only_while_running(client: TestClient, db_session: Session) -> None:
    _, _, run, _, _, _ = build_school(db_session)
    sign_in(client, "driver@example.test")
    trip = start_trip(client, run)
    body = {"latitude": -1.2921, "longitude": 36.8219, "accuracy_m": 12.5}

    shared = client.post(f"/api/v1/crew/trips/{trip['id']}/locations", json=body)
    assert shared.status_code == 201, shared.text
    assert shared.json()["recorded_by_membership_id"]

    future = (utcnow() + timedelta(hours=2)).isoformat()
    clamped = client.post(
        f"/api/v1/crew/trips/{trip['id']}/locations", json={**body, "recorded_at": future}
    )
    assert clamped.json()["recorded_at"] < future  # never stored in the future

    detail = client.get(f"/api/v1/crew/trips/{trip['id']}").json()
    assert detail["location_count"] == 2
    assert detail["last_location_at"] is not None

    client.post(f"/api/v1/crew/trips/{trip['id']}/end")
    after = client.post(f"/api/v1/crew/trips/{trip['id']}/locations", json=body)
    assert after.status_code == 409


# --- Who may reach a trip ----------------------------------------------------------------------


def test_another_schools_crew_cannot_reach_the_trip(
    client: TestClient, db_session: Session
) -> None:
    _, _, run, _, _, _ = build_school(db_session)
    sign_in(client, "driver@example.test")
    trip = start_trip(client, run)

    other_org = make_organization(db_session, "Other School")
    other_driver = make_membership(
        db_session,
        make_user(db_session, "other-driver@example.test"),
        other_org,
        MembershipRole.DRIVER,
    )
    other_route = Route(organization_id=other_org.id, code="X1", name="Elsewhere")
    db_session.add(other_route)
    db_session.flush()
    other_run = RouteRun(
        organization_id=other_org.id,
        route_id=other_route.id,
        direction=RunDirection.MORNING,
        departure_time=time(7, 0),
        driver_membership_id=other_driver.id,
    )
    db_session.add(other_run)
    db_session.commit()

    client.post("/api/v1/auth/sign-out")
    sign_in(client, "other-driver@example.test")

    assert client.get(f"/api/v1/crew/trips/{trip['id']}").status_code == 404
    assert client.post("/api/v1/crew/trips", json={"route_run_id": str(run.id)}).status_code == 404
    assert client.post(f"/api/v1/crew/trips/{trip['id']}/stopped").status_code == 404
    theirs = client.get("/api/v1/crew/trips/today").json()
    assert [item["route_code"] for item in theirs] == ["X1"]


def test_a_school_admin_is_refused_the_crew_api(client: TestClient, db_session: Session) -> None:
    organization, _, _, _, _, _ = build_school(db_session)
    make_membership(
        db_session,
        make_user(db_session, "admin@example.test"),
        organization,
        MembershipRole.SCHOOL_ADMIN,
    )
    sign_in(client, "admin@example.test")
    assert client.get("/api/v1/crew/trips/today").status_code == 403


# --- Fix 4: a removed driver keeps their history ------------------------------------------------


def test_a_removed_driver_keeps_their_trips_and_loses_access(
    client: TestClient, db_session: Session
) -> None:
    organization, _, run, student, driver, _ = build_school(db_session, with_conductor=True)
    sign_in(client, "conductor@example.test")
    trip = start_trip(client, run)
    client.post(
        f"/api/v1/crew/trips/{trip['id']}/events",
        json={"student_id": str(student.id), "kind": "boarded"},
    )

    # The school gives the run to a new driver and takes the old one off the crew.
    replacement = make_membership(
        db_session,
        make_user(db_session, "new-driver@example.test"),
        organization,
        MembershipRole.DRIVER,
    )
    run.driver_membership_id = replacement.id
    db_session.commit()
    make_membership(db_session, make_user(db_session, "grace@example.test"), organization)
    sign_in(client, "grace@example.test")
    conductor = db_session.scalars(
        select(Membership).where(Membership.role == MembershipRole.CONDUCTOR)
    ).one()

    removed = client.delete(f"/api/v1/school/crew/members/{conductor.id}")
    assert removed.status_code == 204

    db_session.expire_all()
    assert db_session.get(Membership, conductor.id) is not None  # kept, not deleted
    event = db_session.scalars(select(BoardingEvent)).one()
    assert event.recorded_by_membership_id == conductor.id  # history still attributed

    sign_in(client, "conductor@example.test")
    assert client.get("/api/v1/crew/trips/today").status_code == 403
    assert client.get("/api/v1/auth/me").json()["memberships"] == []
    assert driver.id != replacement.id
    assert TripStatus.ACTIVE.value == trip["status"]
