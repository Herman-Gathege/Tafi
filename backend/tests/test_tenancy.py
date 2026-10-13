"""Roles and tenant isolation, enforced by the API rather than the UI."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.helpers import PASSWORD, make_membership, make_organization, make_user


def sign_in(client: TestClient, email: str, password: str = PASSWORD):
    return client.post("/api/v1/auth/sign-in", json={"email": email, "password": password})


def test_signed_out_visitors_cannot_reach_protected_routes(client: TestClient) -> None:
    assert client.get("/api/v1/organizations").status_code == 401
    assert client.post("/api/v1/organizations", json={"name": "X"}).status_code == 401
    assert client.get("/api/v1/organization").status_code == 401


def test_platform_admin_onboards_a_school_and_invites_its_first_admin(
    client: TestClient, db_session: Session
) -> None:
    make_user(db_session, "staff@tafi.co.ke", platform_admin=True)
    assert sign_in(client, "staff@tafi.co.ke").status_code == 200

    created = client.post(
        "/api/v1/organizations", json={"name": "Riverside Academy", "type": "school"}
    )
    assert created.status_code == 201
    organization_id = created.json()["id"]
    assert len(client.get("/api/v1/organizations").json()) == 1

    invited = client.post(
        f"/api/v1/organizations/{organization_id}/invitations",
        json={"email": "grace@example.com", "role": "school_admin"},
    )
    assert invited.status_code == 201
    assert invited.json()["email"] == "grace@example.com"
    assert invited.json()["invite_url"].startswith("http")


def test_school_admin_is_forbidden_from_platform_routes(
    client: TestClient, db_session: Session
) -> None:
    organization = make_organization(db_session)
    user = make_user(db_session, "grace@example.com")
    make_membership(db_session, user, organization)
    assert sign_in(client, "grace@example.com").status_code == 200

    assert client.get("/api/v1/organizations").status_code == 403
    assert client.post("/api/v1/organizations", json={"name": "Elsewhere"}).status_code == 403
    assert (
        client.post(
            f"/api/v1/organizations/{organization.id}/invitations",
            json={"email": "someone@example.com"},
        ).status_code
        == 403
    )


def test_school_admin_only_ever_sees_their_own_organization(
    client: TestClient, db_session: Session
) -> None:
    theirs = make_organization(db_session, "Riverside Academy")
    other = make_organization(db_session, "Hilltop School")
    user = make_user(db_session, "grace@example.com")
    make_membership(db_session, user, theirs)
    assert sign_in(client, "grace@example.com").status_code == 200

    response = client.get("/api/v1/organization")

    assert response.status_code == 200
    assert response.json()["id"] == str(theirs.id)
    assert response.json()["id"] != str(other.id)


def test_platform_admin_without_a_membership_has_no_school(
    client: TestClient, db_session: Session
) -> None:
    make_user(db_session, "staff@tafi.co.ke", platform_admin=True)
    assert sign_in(client, "staff@tafi.co.ke").status_code == 200
    assert client.get("/api/v1/organization").status_code == 403
