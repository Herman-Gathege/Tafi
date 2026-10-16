"""A school admin invites, lists and removes drivers and conductors (D-21)."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.models.user import MembershipRole
from tests.helpers import (
    PASSWORD,
    make_membership,
    make_organization,
    make_route,
    make_run,
    make_user,
)

CREW = "/api/v1/school/crew"


def sign_in(client: TestClient, email: str, password: str = PASSWORD):
    return client.post("/api/v1/auth/sign-in", json={"email": email, "password": password})


def school_admin(client: TestClient, db: Session) -> Organization:
    school = make_organization(db)
    make_membership(db, make_user(db, "grace@example.com"), school)
    assert sign_in(client, "grace@example.com").status_code == 200
    return school


def test_invite_a_conductor_who_then_joins_the_crew(
    client: TestClient, db_session: Session
) -> None:
    school_admin(client, db_session)

    invited = client.post(
        f"{CREW}/invitations", json={"email": "Mercy@Example.com", "role": "conductor"}
    )
    assert invited.status_code == 201
    assert invited.json()["email"] == "mercy@example.com"
    assert invited.json()["role"] == "conductor"
    token = invited.json()["invite_url"].split("token=")[1]

    pending = client.get(CREW).json()
    assert pending["members"] == []
    assert [i["email"] for i in pending["pending_invitations"]] == ["mercy@example.com"]

    accepted = client.post(
        "/api/v1/auth/accept-invite",
        json={"token": token, "name": "Mercy Wanjiku", "password": "a-long-password"},
    )
    assert accepted.status_code == 200
    assert accepted.json()["memberships"][0]["role"] == "conductor"

    assert sign_in(client, "grace@example.com").status_code == 200
    crew = client.get(CREW).json()
    assert [(m["name"], m["role"]) for m in crew["members"]] == [("Mercy Wanjiku", "conductor")]
    assert crew["pending_invitations"] == []


def test_only_drivers_and_conductors_can_be_invited(
    client: TestClient, db_session: Session
) -> None:
    school_admin(client, db_session)
    response = client.post(
        f"{CREW}/invitations", json={"email": "boss@example.com", "role": "school_admin"}
    )
    assert response.status_code == 422


def test_someone_already_at_the_school_is_not_invited_again(
    client: TestClient, db_session: Session
) -> None:
    school = school_admin(client, db_session)
    make_membership(
        db_session, make_user(db_session, "peter@example.com"), school, MembershipRole.DRIVER
    )
    response = client.post(
        f"{CREW}/invitations", json={"email": "peter@example.com", "role": "driver"}
    )
    assert response.status_code == 409


def test_a_driver_on_a_run_must_be_replaced_before_removal(
    client: TestClient, db_session: Session
) -> None:
    school = school_admin(client, db_session)
    driver = make_membership(
        db_session, make_user(db_session, "peter@example.com"), school, MembershipRole.DRIVER
    )
    conductor = make_membership(
        db_session, make_user(db_session, "mercy@example.com"), school, MembershipRole.CONDUCTOR
    )
    run = make_run(db_session, make_route(db_session, school), driver, conductor=conductor)

    assert client.delete(f"{CREW}/members/{driver.id}").status_code == 409

    # A conductor can go; the run continues with the driver alone.
    assert client.delete(f"{CREW}/members/{conductor.id}").status_code == 204
    db_session.refresh(run)
    assert run.conductor_membership_id is None
    assert [m["role"] for m in client.get(CREW).json()["members"]] == ["driver"]


def test_school_admins_and_other_schools_crew_are_not_removable_here(
    client: TestClient, db_session: Session
) -> None:
    school = school_admin(client, db_session)
    other_admin = make_membership(db_session, make_user(db_session, "jane@example.com"), school)
    hilltop = make_organization(db_session, "Hilltop School")
    their_driver = make_membership(
        db_session,
        make_user(db_session, "driver@hilltop.example.com"),
        hilltop,
        MembershipRole.DRIVER,
    )

    assert client.delete(f"{CREW}/members/{other_admin.id}").status_code == 404
    assert client.delete(f"{CREW}/members/{their_driver.id}").status_code == 404
