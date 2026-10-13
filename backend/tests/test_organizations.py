"""Tests for the organizations endpoints."""

from fastapi.testclient import TestClient


def test_create_and_list_organizations(client: TestClient) -> None:
    created = client.post(
        "/api/v1/organizations",
        json={"name": "Kilimani Primary School", "type": "school"},
    )

    assert created.status_code == 201
    body = created.json()
    assert body["name"] == "Kilimani Primary School"
    assert body["type"] == "school"
    assert body["id"]

    listed = client.get("/api/v1/organizations")

    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [body["id"]]


def test_create_organization_defaults_to_school(client: TestClient) -> None:
    created = client.post("/api/v1/organizations", json={"name": "Mombasa Road Academy"})

    assert created.status_code == 201
    assert created.json()["type"] == "school"


def test_create_organization_rejects_blank_name(client: TestClient) -> None:
    response = client.post("/api/v1/organizations", json={"name": ""})

    assert response.status_code == 422
