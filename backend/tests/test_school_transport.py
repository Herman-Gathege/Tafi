"""A school admin sets up routes, stops, vehicles and runs — and only ever their own."""

import uuid
from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.models.transport import StudentRouteAssignment
from app.models.user import Membership, MembershipRole
from tests.helpers import (
    PASSWORD,
    make_membership,
    make_organization,
    make_route,
    make_stop,
    make_student,
    make_user,
)

API = "/api/v1/school"


def sign_in(client: TestClient, email: str, password: str = PASSWORD):
    return client.post("/api/v1/auth/sign-in", json={"email": email, "password": password})


def school_admin(client: TestClient, db: Session, name: str = "Riverside Academy") -> Organization:
    """A school with a signed-in admin."""
    school = make_organization(db, name)
    email = f"admin@{name.split()[0].lower()}.example.com"
    make_membership(db, make_user(db, email), school)
    assert sign_in(client, email).status_code == 200
    return school


def crew(db: Session, school: Organization, email: str, role: MembershipRole) -> Membership:
    return make_membership(db, make_user(db, email), school, role)


# --- Routes and stops -----------------------------------------------------------------------


def test_create_a_route_and_build_its_stops(client: TestClient, db_session: Session) -> None:
    school_admin(client, db_session)

    created = client.post(f"{API}/routes", json={"code": " r1 ", "name": "Kileleshwa"})
    assert created.status_code == 201
    route_id = created.json()["id"]
    assert created.json()["code"] == "R1"

    client.post(f"{API}/routes/{route_id}/stops", json={"name": "Main gate"})
    client.post(f"{API}/routes/{route_id}/stops", json={"name": "Shops", "landmark": "Naivas"})
    detail = client.post(
        f"{API}/routes/{route_id}/stops",
        json={"name": "Church", "latitude": "-1.28333312345", "longitude": 36.8167},
    ).json()

    assert [stop["name"] for stop in detail["stops"]] == ["Main gate", "Shops", "Church"]
    assert [stop["sequence"] for stop in detail["stops"]] == [1, 2, 3]
    assert detail["stops"][2]["latitude"] == -1.283333

    listing = client.get(f"{API}/routes").json()
    assert listing == [
        {"id": route_id, "code": "R1", "name": "Kileleshwa", "is_active": True, "stop_count": 3}
    ]


def test_route_codes_are_unique_within_a_school(client: TestClient, db_session: Session) -> None:
    school_admin(client, db_session)
    assert client.post(f"{API}/routes", json={"code": "R1", "name": "One"}).status_code == 201
    duplicate = client.post(f"{API}/routes", json={"code": "r1", "name": "Again"})
    assert duplicate.status_code == 409


def test_reorder_and_remove_stops(client: TestClient, db_session: Session) -> None:
    school_admin(client, db_session)
    route_id = client.post(f"{API}/routes", json={"code": "R1", "name": "One"}).json()["id"]
    for name in ("A", "B", "C"):
        client.post(f"{API}/routes/{route_id}/stops", json={"name": name})
    stops = client.get(f"{API}/routes/{route_id}").json()["stops"]
    a, b, c = (stop["id"] for stop in stops)

    reordered = client.put(f"{API}/routes/{route_id}/stops/order", json={"stop_ids": [c, a, b]})
    assert [stop["name"] for stop in reordered.json()["stops"]] == ["C", "A", "B"]

    missing_one = client.put(f"{API}/routes/{route_id}/stops/order", json={"stop_ids": [c, a]})
    assert missing_one.status_code == 422
    repeated = client.put(f"{API}/routes/{route_id}/stops/order", json={"stop_ids": [c, a, a]})
    assert repeated.status_code == 422

    after_removal = client.delete(f"{API}/stops/{a}").json()
    assert [(stop["name"], stop["sequence"]) for stop in after_removal["stops"]] == [
        ("C", 1),
        ("B", 2),
    ]


def test_a_stop_children_use_cannot_be_removed(client: TestClient, db_session: Session) -> None:
    school = school_admin(client, db_session)
    route = make_route(db_session, school)
    stop = make_stop(db_session, route)
    db_session.add(
        StudentRouteAssignment(
            organization_id=school.id,
            student_id=make_student(db_session, school).id,
            route_id=route.id,
            pickup_stop_id=stop.id,
            active_from=date(2027, 1, 6),
        )
    )
    db_session.commit()

    assert client.delete(f"{API}/stops/{stop.id}").status_code == 409


def test_edit_a_stop_and_deactivate_a_route(client: TestClient, db_session: Session) -> None:
    school = school_admin(client, db_session)
    route = make_route(db_session, school)
    stop = make_stop(db_session, route, "Gate")

    edited = client.patch(f"{API}/stops/{stop.id}", json={"name": "Main gate", "landmark": ""})
    assert edited.json()["name"] == "Main gate"
    assert edited.json()["landmark"] is None

    deactivated = client.patch(f"{API}/routes/{route.id}", json={"is_active": False})
    assert deactivated.json()["is_active"] is False


# --- Vehicles -------------------------------------------------------------------------------


def test_vehicles_have_tidy_unique_plates(client: TestClient, db_session: Session) -> None:
    school_admin(client, db_session)

    added = client.post(f"{API}/vehicles", json={"plate": " kda  213a ", "seats": 26})
    assert added.status_code == 201
    assert added.json()["plate"] == "KDA 213A"

    assert (
        client.post(f"{API}/vehicles", json={"plate": "KDA 213A", "seats": 14}).status_code == 409
    )
    assert (
        client.post(f"{API}/vehicles", json={"plate": "KDA-213A", "seats": 14}).status_code == 422
    )
    assert client.post(f"{API}/vehicles", json={"plate": "KCB 448Q", "seats": 0}).status_code == 422
    assert [v["plate"] for v in client.get(f"{API}/vehicles").json()] == ["KDA 213A"]


# --- Runs -----------------------------------------------------------------------------------


def test_a_run_needs_a_driver_and_may_have_a_conductor(
    client: TestClient, db_session: Session
) -> None:
    school = school_admin(client, db_session)
    route = make_route(db_session, school)
    driver = crew(db_session, school, "peter@example.com", MembershipRole.DRIVER)
    conductor = crew(db_session, school, "mercy@example.com", MembershipRole.CONDUCTOR)
    vehicle_id = client.post(f"{API}/vehicles", json={"plate": "KDA 213A", "seats": 26}).json()[
        "id"
    ]
    url = f"{API}/routes/{route.id}/runs/morning"

    alone = client.put(
        url, json={"departure_time": "06:30", "driver_membership_id": str(driver.id)}
    )
    assert alone.status_code == 200
    assert alone.json()["conductor_membership_id"] is None

    with_conductor = client.put(
        url,
        json={
            "departure_time": "06:35",
            "vehicle_id": vehicle_id,
            "driver_membership_id": str(driver.id),
            "conductor_membership_id": str(conductor.id),
        },
    )
    assert with_conductor.json()["id"] == alone.json()["id"]  # replaced, not duplicated
    assert with_conductor.json()["conductor_membership_id"] == str(conductor.id)

    no_driver = client.put(url, json={"departure_time": "06:30"})
    assert no_driver.status_code == 422

    conductor_as_driver = client.put(
        url, json={"departure_time": "06:30", "driver_membership_id": str(conductor.id)}
    )
    assert conductor_as_driver.status_code == 422

    runs = client.get(f"{API}/routes/{route.id}").json()["runs"]
    assert [run["direction"] for run in runs] == ["morning"]

    assert client.delete(url).status_code == 204
    assert client.get(f"{API}/routes/{route.id}").json()["runs"] == []


def test_a_retired_vehicle_cannot_be_given_a_run(client: TestClient, db_session: Session) -> None:
    school = school_admin(client, db_session)
    route = make_route(db_session, school)
    driver = crew(db_session, school, "peter@example.com", MembershipRole.DRIVER)
    vehicle_id = client.post(f"{API}/vehicles", json={"plate": "KDA 213A", "seats": 26}).json()[
        "id"
    ]
    client.patch(f"{API}/vehicles/{vehicle_id}", json={"is_active": False})

    response = client.put(
        f"{API}/routes/{route.id}/runs/afternoon",
        json={
            "departure_time": "16:10",
            "vehicle_id": vehicle_id,
            "driver_membership_id": str(driver.id),
        },
    )
    assert response.status_code == 422


# --- Tenancy --------------------------------------------------------------------------------


def test_another_schools_routes_vehicles_and_crew_are_out_of_reach(
    client: TestClient, db_session: Session
) -> None:
    hilltop = make_organization(db_session, "Hilltop School")
    their_route = make_route(db_session, hilltop)
    their_stop = make_stop(db_session, their_route)
    their_driver = crew(db_session, hilltop, "driver@hilltop.example.com", MembershipRole.DRIVER)

    riverside = school_admin(client, db_session)
    our_route = make_route(db_session, riverside)

    assert client.get(f"{API}/routes").json() == [
        {
            "id": str(our_route.id),
            "code": "R1",
            "name": "Route R1",
            "is_active": True,
            "stop_count": 0,
        }
    ]
    assert client.get(f"{API}/routes/{their_route.id}").status_code == 404
    assert client.patch(f"{API}/routes/{their_route.id}", json={"name": "x"}).status_code == 404
    assert (
        client.post(f"{API}/routes/{their_route.id}/stops", json={"name": "x"}).status_code == 404
    )
    assert client.patch(f"{API}/stops/{their_stop.id}", json={"name": "x"}).status_code == 404
    assert client.delete(f"{API}/stops/{their_stop.id}").status_code == 404
    assert client.get(f"{API}/routes/{uuid.uuid4()}").status_code == 404

    # Their driver cannot be put on our run.
    borrowed = client.put(
        f"{API}/routes/{our_route.id}/runs/morning",
        json={"departure_time": "06:30", "driver_membership_id": str(their_driver.id)},
    )
    assert borrowed.status_code == 404


def test_crew_cannot_manage_routes(client: TestClient, db_session: Session) -> None:
    school = make_organization(db_session)
    crew(db_session, school, "peter@example.com", MembershipRole.DRIVER)
    assert sign_in(client, "peter@example.com").status_code == 200

    assert client.get(f"{API}/routes").status_code == 403
    assert (
        client.post(f"{API}/vehicles", json={"plate": "KDA 213A", "seats": 26}).status_code == 403
    )
