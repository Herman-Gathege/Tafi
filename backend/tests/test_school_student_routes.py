"""Children are put on routes with their stops, moved, and taken off — with history (S3-09)."""

from datetime import date
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.routes import school_students
from app.models.organization import Organization
from app.models.transport import Route, Stop
from tests.helpers import (
    PASSWORD,
    make_membership,
    make_organization,
    make_route,
    make_stop,
    make_user,
)

API = "/api/v1/school"


def sign_in(client: TestClient, email: str, password: str = PASSWORD):
    return client.post("/api/v1/auth/sign-in", json={"email": email, "password": password})


def school_admin(client: TestClient, db: Session) -> Organization:
    school = make_organization(db)
    make_membership(db, make_user(db, "grace@example.com"), school)
    assert sign_in(client, "grace@example.com").status_code == 200
    return school


def add_child(client: TestClient, first_name: str = "Wanjiru") -> dict[str, Any]:
    response = client.post(
        f"{API}/students",
        json={
            "first_name": first_name,
            "last_name": "Otieno",
            "guardians": [
                {
                    "full_name": "Achieng Otieno",
                    "whatsapp_number": "0712 345 678",
                    "relationship": "mother",
                }
            ],
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def route_with_stops(db: Session, school: Organization, code: str) -> tuple[Route, Stop, Stop]:
    route = make_route(db, school, code)
    return route, make_stop(db, route, f"{code} gate", 1), make_stop(db, route, f"{code} shops", 2)


def put_on(
    client: TestClient,
    child: dict[str, Any],
    route: Route,
    pickup: Stop | None,
    dropoff: Stop | None,
):
    return client.put(
        f"{API}/students/{child['id']}/route",
        json={
            "route_id": str(route.id),
            "pickup_stop_id": str(pickup.id) if pickup else None,
            "dropoff_stop_id": str(dropoff.id) if dropoff else None,
        },
    )


@pytest.fixture
def on_day(monkeypatch: pytest.MonkeyPatch):
    """Set the school's 'today'."""

    def set_day(day: date) -> None:
        monkeypatch.setattr(school_students, "today", lambda: day)

    set_day(date(2027, 1, 6))
    return set_day


def history(client: TestClient, child: dict[str, Any]) -> list[tuple[str, str, str | None]]:
    rows = client.get(f"{API}/students/{child['id']}/route-history").json()
    return [(row["route_code"], row["active_from"], row["active_to"]) for row in rows]


def test_put_a_child_on_a_route(client: TestClient, db_session: Session, on_day) -> None:
    school = school_admin(client, db_session)
    route, gate, shops = route_with_stops(db_session, school, "R1")
    child = add_child(client)
    other = add_child(client, "Baraka")
    assert child["route"] is None

    response = put_on(client, child, route, gate, shops)

    assert response.status_code == 200
    current = response.json()["route"]
    assert (current["route_code"], current["active_from"]) == ("R1", "2027-01-06")
    assert current["pickup_stop"]["name"] == "R1 gate"
    assert current["dropoff_stop"]["name"] == "R1 shops"

    listed = {s["first_name"]: s["route"] for s in client.get(f"{API}/students").json()}
    assert listed["Wanjiru"]["route_code"] == "R1"
    assert listed["Baraka"] is None

    riders = client.get(f"{API}/students", params={"route_id": str(route.id)}).json()
    assert [s["first_name"] for s in riders] == ["Wanjiru"]
    assert other["id"] not in [s["id"] for s in riders]


def test_a_child_may_ride_one_way_only(client: TestClient, db_session: Session, on_day) -> None:
    school = school_admin(client, db_session)
    route, gate, _ = route_with_stops(db_session, school, "R1")
    child = add_child(client)

    morning_only = put_on(client, child, route, gate, None).json()["route"]
    assert morning_only["pickup_stop"]["name"] == "R1 gate"
    assert morning_only["dropoff_stop"] is None

    assert put_on(client, child, route, None, None).status_code == 422


def test_stops_must_belong_to_the_route(client: TestClient, db_session: Session, on_day) -> None:
    school = school_admin(client, db_session)
    route, gate, _ = route_with_stops(db_session, school, "R1")
    _, elsewhere, _ = route_with_stops(db_session, school, "R2")
    child = add_child(client)

    assert put_on(client, child, route, gate, elsewhere).status_code == 422

    client.patch(f"{API}/routes/{route.id}", json={"is_active": False})
    assert put_on(client, child, route, gate, None).status_code == 422


def test_moving_route_keeps_history(client: TestClient, db_session: Session, on_day) -> None:
    school = school_admin(client, db_session)
    first, first_gate, _ = route_with_stops(db_session, school, "R1")
    second, second_gate, second_shops = route_with_stops(db_session, school, "R2")
    child = add_child(client)

    put_on(client, child, first, first_gate, None)
    on_day(date(2027, 2, 1))
    moved = put_on(client, child, second, second_gate, second_shops).json()

    assert moved["route"]["route_code"] == "R2"
    assert history(client, child) == [
        ("R2", "2027-02-01", None),
        ("R1", "2027-01-06", "2027-02-01"),
    ]


def test_moving_twice_in_a_day_leaves_one_record(
    client: TestClient, db_session: Session, on_day
) -> None:
    school = school_admin(client, db_session)
    first, first_gate, _ = route_with_stops(db_session, school, "R1")
    second, second_gate, _ = route_with_stops(db_session, school, "R2")
    child = add_child(client)

    put_on(client, child, first, first_gate, None)
    put_on(client, child, second, second_gate, None)  # a same-day correction

    assert history(client, child) == [("R2", "2027-01-06", None)]


def test_new_stops_on_the_same_route_change_in_place(
    client: TestClient, db_session: Session, on_day
) -> None:
    school = school_admin(client, db_session)
    route, gate, shops = route_with_stops(db_session, school, "R1")
    child = add_child(client)

    put_on(client, child, route, gate, gate)
    on_day(date(2027, 2, 1))
    changed = put_on(client, child, route, shops, shops).json()["route"]

    assert changed["pickup_stop"]["name"] == "R1 shops"
    assert history(client, child) == [("R1", "2027-01-06", None)]


def test_take_a_child_off_transport(client: TestClient, db_session: Session, on_day) -> None:
    school = school_admin(client, db_session)
    route, gate, _ = route_with_stops(db_session, school, "R1")
    child = add_child(client)
    put_on(client, child, route, gate, None)
    on_day(date(2027, 3, 1))

    off = client.delete(f"{API}/students/{child['id']}/route")

    assert off.status_code == 200
    assert off.json()["route"] is None
    assert history(client, child) == [("R1", "2027-01-06", "2027-03-01")]
    assert client.delete(f"{API}/students/{child['id']}/route").status_code == 404


def test_deactivating_a_child_takes_them_off_their_route(
    client: TestClient, db_session: Session, on_day
) -> None:
    school = school_admin(client, db_session)
    route, gate, _ = route_with_stops(db_session, school, "R1")
    child = add_child(client)
    put_on(client, child, route, gate, None)
    on_day(date(2027, 3, 1))

    inactive = client.patch(f"{API}/students/{child['id']}", json={"status": "inactive"}).json()

    assert inactive["route"] is None
    assert put_on(client, child, route, gate, None).status_code == 409


def test_a_stop_only_past_riders_used_can_be_removed(
    client: TestClient, db_session: Session, on_day
) -> None:
    school = school_admin(client, db_session)
    first, first_gate, _ = route_with_stops(db_session, school, "R1")
    second, second_gate, _ = route_with_stops(db_session, school, "R2")
    child = add_child(client)
    put_on(client, child, first, first_gate, None)

    assert client.delete(f"{API}/stops/{first_gate.id}").status_code == 409  # a current rider

    on_day(date(2027, 2, 1))
    put_on(client, child, second, second_gate, None)  # R1 is now history
    assert client.delete(f"{API}/stops/{first_gate.id}").status_code == 200

    rows = client.get(f"{API}/students/{child['id']}/route-history").json()
    past = rows[1]
    assert (past["route_code"], past["pickup_stop_id"], past["active_to"]) == (
        "R1",
        None,
        "2027-02-01",
    )


def test_another_schools_route_cannot_be_used(
    client: TestClient, db_session: Session, on_day
) -> None:
    hilltop = make_organization(db_session, "Hilltop School")
    their_route, their_gate, _ = route_with_stops(db_session, hilltop, "R1")
    school_admin(client, db_session)
    child = add_child(client)

    assert put_on(client, child, their_route, their_gate, None).status_code == 404
