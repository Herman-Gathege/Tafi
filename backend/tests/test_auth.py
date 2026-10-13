"""Sign in, sign out, invitations and password resets."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.helpers import (
    PASSWORD,
    make_invitation,
    make_organization,
    make_user,
)


def sign_in(client: TestClient, email: str, password: str = PASSWORD):
    return client.post("/api/v1/auth/sign-in", json={"email": email, "password": password})


def test_sign_in_starts_a_session(client: TestClient, db_session: Session) -> None:
    make_user(db_session, "anne@example.com")

    response = sign_in(client, "anne@example.com")

    assert response.status_code == 200
    body = response.json()
    assert body["user"]["email"] == "anne@example.com"
    assert body["user"]["is_platform_admin"] is False
    assert body["memberships"] == []
    assert client.get("/api/v1/auth/me").status_code == 200


def test_sign_in_ignores_email_case(client: TestClient, db_session: Session) -> None:
    make_user(db_session, "anne@example.com")
    assert sign_in(client, "  ANNE@Example.com ").status_code == 200


def test_sign_in_rejects_a_wrong_password(client: TestClient, db_session: Session) -> None:
    make_user(db_session, "anne@example.com")
    assert sign_in(client, "anne@example.com", "not-the-password").status_code == 401
    assert client.get("/api/v1/auth/me").status_code == 401


def test_me_without_a_session_is_unauthorised(client: TestClient) -> None:
    assert client.get("/api/v1/auth/me").status_code == 401


def test_sign_out_ends_the_session(client: TestClient, db_session: Session) -> None:
    make_user(db_session, "anne@example.com")
    assert sign_in(client, "anne@example.com").status_code == 200
    assert client.post("/api/v1/auth/sign-out").status_code == 204
    assert client.get("/api/v1/auth/me").status_code == 401


def test_invitation_preview_shows_the_school(client: TestClient, db_session: Session) -> None:
    organization = make_organization(db_session)
    _, token = make_invitation(db_session, organization, "grace@example.com")

    response = client.get(f"/api/v1/auth/invitations/{token}")

    assert response.status_code == 200
    assert response.json() == {
        "email": "grace@example.com",
        "organization_name": "Riverside Academy",
        "role": "school_admin",
    }


def test_invitation_preview_rejects_an_unknown_token(client: TestClient) -> None:
    assert client.get("/api/v1/auth/invitations/nope-not-a-token").status_code == 400


def test_accept_invite_creates_the_account_and_signs_in(
    client: TestClient, db_session: Session
) -> None:
    organization = make_organization(db_session)
    _, token = make_invitation(db_session, organization, "grace@example.com")

    response = client.post(
        "/api/v1/auth/accept-invite",
        json={"token": token, "name": "Grace M", "password": "a-good-password"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["user"]["email"] == "grace@example.com"
    assert body["memberships"] == [
        {
            "organization_id": str(organization.id),
            "organization_name": "Riverside Academy",
            "role": "school_admin",
        }
    ]
    assert client.get("/api/v1/auth/me").status_code == 200

    client.post("/api/v1/auth/sign-out")
    assert sign_in(client, "grace@example.com", "a-good-password").status_code == 200


def test_accept_invite_refuses_a_used_token(client: TestClient, db_session: Session) -> None:
    organization = make_organization(db_session)
    _, token = make_invitation(db_session, organization, "grace@example.com")
    payload = {"token": token, "name": "Grace M", "password": "a-good-password"}

    assert client.post("/api/v1/auth/accept-invite", json=payload).status_code == 200
    assert client.post("/api/v1/auth/accept-invite", json=payload).status_code == 400


def test_accept_invite_refuses_an_expired_token(client: TestClient, db_session: Session) -> None:
    organization = make_organization(db_session)
    _, token = make_invitation(db_session, organization, "grace@example.com", expired=True)

    response = client.post(
        "/api/v1/auth/accept-invite",
        json={"token": token, "name": "Grace M", "password": "a-good-password"},
    )

    assert response.status_code == 400


def test_accept_invite_refuses_an_email_that_already_has_an_account(
    client: TestClient, db_session: Session
) -> None:
    organization = make_organization(db_session)
    make_user(db_session, "grace@example.com")
    _, token = make_invitation(db_session, organization, "grace@example.com")

    response = client.post(
        "/api/v1/auth/accept-invite",
        json={"token": token, "name": "Grace M", "password": "a-good-password"},
    )

    assert response.status_code == 400


def test_forgot_password_answers_the_same_way_for_an_unknown_address(
    client: TestClient, db_session: Session
) -> None:
    response = client.post("/api/v1/auth/forgot-password", json={"email": "nobody@example.com"})
    assert response.status_code == 202
    assert response.json()["reset_url"] is None


def test_reset_password_works_once(client: TestClient, db_session: Session) -> None:
    make_user(db_session, "anne@example.com")
    asked = client.post("/api/v1/auth/forgot-password", json={"email": "anne@example.com"})
    reset_url = asked.json()["reset_url"]
    assert reset_url is not None
    token = reset_url.split("token=", 1)[1]

    payload = {"token": token, "password": "a-brand-new-password"}
    assert client.post("/api/v1/auth/reset-password", json=payload).status_code == 204
    assert sign_in(client, "anne@example.com", "a-brand-new-password").status_code == 200
    assert client.post("/api/v1/auth/reset-password", json=payload).status_code == 400
