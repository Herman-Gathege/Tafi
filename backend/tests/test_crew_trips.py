"""The crew app: trips, marks, the driver-alone rule and location (Sprint 4)."""

from datetime import date, time

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.student import Student, StudentStatus
from app.models.transport import (
    Route,
    RouteRun,
    RunDirection,
    Stop,
    StudentRouteAssignment,
    Vehicle,
)
from app.models.trip import TripStatus
from app.models.user import MembershipRole
from tests.helpers import PASSWORD, make_membership, make_organization, make_user


def build_school(db: Session, *, with_conductor: bool = False):
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
        direction=RunDirection.MORNING,
        departure_time=time(6, 30),
        vehicle_id=vehicle.id,
        driver_membership_id=driver.id,
        conductor_membership_id=conductor.id if conductor else None,
    )
    db.add(run)
    db.flush()

    student = Student(
        organization_id=organization.id,
        first_name="Wanjiru",
        last_name="Otieno",
        grade="Grade 4",
        status=StudentStatus.ACTIVE,
    )
    db.add(student)
    db.flush()
    db.add(
        StudentRouteAssignment(
            organization_id=organization.id,
            student_id=student.id,
            route_id=route.id,
            pickup_stop_id=stops[0].id,
            dropoff_stop_id=stops[1].id,
            active_from=date.today(),
        )
    )
    db.commit()
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


def test_starting_twice_returns_the_same_trip(client: TestClient, db_session: Session) -> None:
    _, _, run, _, _, _ = build_school(db_session)
    sign_in(client, "driver@example.test")
    first = start_trip(client, run)
    second = start_trip(client, run)
    assert first["id"] == second["id"]
    assert client.get("/api/v1/crew/trips/today").json()[0]["status"] == "active"


def test_a_driver_alone_must_confirm_stopped_before_marking(
    client: TestClient, db_session: Session
) -> None:
    _, _, run, student, _, _ = build_school(db_session)
    sign_in(client, "driver@example.test")
    trip = start_trip(client, run)

    refused = client.post(
        f"/api/v1/crew/trips/{trip['id']}/events",
        json={"student_id": str(student.id), "kind": "boarded"},
    )
    assert refused.status_code == 409
    assert "stopped" in refused.json()["detail"].lower()

    confirmation = client.post(f"/api/v1/crew/trips/{trip['id']}/stopped")
    assert confirmation.status_code == 200
    confirmed_at = confirmation.json()["confirmed_at"]

    marked = client.post(
        f"/api/v1/crew/trips/{trip['id']}/events",
        json={
            "student_id": str(student.id),
            "kind": "boarded",
            "stopped_confirmed_at": confirmed_at,
        },
    )
    assert marked.status_code == 201, marked.text
    assert marked.json()["recorded_by_membership_id"]
    assert marked.json()["method"] == "manual"


def test_a_stale_stopped_confirmation_is_refused(client: TestClient, db_session: Session) -> None:
    _, _, run, student, _, _ = build_school(db_session)
    sign_in(client, "driver@example.test")
    trip = start_trip(client, run)

    stale = "2020-01-01T06:00:00+00:00"
    response = client.post(
        f"/api/v1/crew/trips/{trip['id']}/events",
        json={
            "student_id": str(student.id),
            "kind": "boarded",
            "stopped_confirmed_at": stale,
        },
    )
    assert response.status_code == 409


def test_a_conductor_marks_without_confirming_stopped(
    client: TestClient, db_session: Session
) -> None:
    _, _, run, student, _, _ = build_school(db_session, with_conductor=True)
    sign_in(client, "conductor@example.test")
    trip = start_trip(client, run)

    marked = client.post(
        f"/api/v1/crew/trips/{trip['id']}/events",
        json={"student_id": str(student.id), "kind": "boarded"},
    )
    assert marked.status_code == 201, marked.text


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
    organization, route, run, _, _, _ = build_school(db_session, with_conductor=True)
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

    detail = client.get(f"/api/v1/crew/trips/{trip['id']}").json()
    assert detail["location_count"] == 1
    assert detail["last_location_at"] is not None

    client.post(f"/api/v1/crew/trips/{trip['id']}/end")
    after = client.post(f"/api/v1/crew/trips/{trip['id']}/locations", json=body)
    assert after.status_code == 409


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
    other_vehicle = Vehicle(organization_id=other_org.id, plate="KDB1", seats=14)
    db_session.add(other_vehicle)
    db_session.flush()
    other_run = RouteRun(
        organization_id=other_org.id,
        route_id=other_route.id,
        direction=RunDirection.MORNING,
        departure_time=time(7, 0),
        vehicle_id=other_vehicle.id,
        driver_membership_id=other_driver.id,
    )
    db_session.add(other_run)
    db_session.commit()

    client.post("/api/v1/auth/sign-out")
    sign_in(client, "other-driver@example.test")

    assert client.get(f"/api/v1/crew/trips/{trip['id']}").status_code == 404
    assert client.post("/api/v1/crew/trips", json={"route_run_id": str(run.id)}).status_code == 404
    # The other driver sees their own run, and only their own (D-26).
    theirs = client.get("/api/v1/crew/trips/today").json()
    assert [item["route_code"] for item in theirs] == ["X1"]
    assert all(item["route_run_id"] != str(run.id) for item in theirs)


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


def test_trip_states_are_only_ever_valid(client: TestClient, db_session: Session) -> None:
    """A trip starts scheduled, runs, ends completed — and never goes backwards."""
    _, _, run, _, _, _ = build_school(db_session)
    sign_in(client, "driver@example.test")
    trip = start_trip(client, run)
    assert trip["status"] == TripStatus.ACTIVE.value
    ended = client.post(f"/api/v1/crew/trips/{trip['id']}/end").json()
    assert ended["status"] == TripStatus.COMPLETED.value
