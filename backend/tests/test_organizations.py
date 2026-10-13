"""The organizations endpoints keep validating their input."""

import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.helpers import PASSWORD, make_user


def sign_in(client: TestClient, email: str, password: str = PASSWORD):
    return client.post("/api/v1/auth/sign-in", json={"email": email, "password": password})


def test_create_organization_returns_a_usable_record(
    client: TestClient, db_session: Session
) -> None:
    make_user(db_session, "staff@tafi.co.ke", platform_admin=True)
    assert sign_in(client, "staff@tafi.co.ke").status_code == 200

    response = client.post(
        "/api/v1/organizations", json={"name": "Riverside Academy", "type": "school"}
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Riverside Academy"
    assert body["type"] == "school"
    assert uuid.UUID(body["id"])


def test_create_organization_rejects_an_unknown_type(
    client: TestClient, db_session: Session
) -> None:
    make_user(db_session, "staff@tafi.co.ke", platform_admin=True)
    assert sign_in(client, "staff@tafi.co.ke").status_code == 200

    response = client.post("/api/v1/organizations", json={"name": "Bad", "type": "university"})

    assert response.status_code == 422
