"""Self-signup and the parent's own view (D-37)."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.guardian import Guardian, GuardianRelationship, GuardianStatus, StudentGuardian
from app.models.student import Student, StudentStatus
from app.models.transport import Route, Stop, StudentRouteAssignment
from app.models.user import MembershipRole
from app.services.trips import kenya_today
from tests.helpers import PASSWORD, make_membership, make_organization, make_user


def test_signup_creates_a_school_and_its_admin(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "school_name": "Hilltop Academy",
            "name": "New Admin",
            "email": "new-admin@example.test",
            "password": "a-good-password",
        },
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["user"]["email"] == "new-admin@example.test"
    assert body["user"]["is_platform_admin"] is False
    assert body["memberships"][0]["organization_name"] == "Hilltop Academy"
    assert body["memberships"][0]["role"] == "school_admin"
    assert client.get("/api/v1/auth/me").status_code == 200
    assert client.get("/api/v1/organization").json()["name"] == "Hilltop Academy"


def test_signup_refuses_an_email_that_already_exists(
    client: TestClient, db_session: Session
) -> None:
    make_user(db_session, "taken@example.test")
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "school_name": "Another School",
            "name": "Someone",
            "email": "taken@example.test",
            "password": "a-good-password",
        },
    )
    assert response.status_code == 409


def build_family(db: Session):
    """A school with one child, one guardian who has a login, and a route."""
    organization = make_organization(db, "Family School")
    parent_user = make_user(db, "parent@example.test")
    make_membership(db, parent_user, organization, MembershipRole.PARENT)

    guardian = Guardian(
        organization_id=organization.id,
        full_name="Parent One",
        whatsapp_number="+254700000010",
        email="parent@example.test",
        status=GuardianStatus.CONFIRMED,
        user_id=parent_user.id,
    )
    db.add(guardian)
    db.flush()

    route = Route(organization_id=organization.id, code="R1", name="Kileleshwa")
    db.add(route)
    db.flush()
    pickup = Stop(organization_id=organization.id, route_id=route.id, name="Main gate", sequence=1)
    dropoff = Stop(organization_id=organization.id, route_id=route.id, name="School", sequence=2)
    db.add_all([pickup, dropoff])
    db.flush()

    child = Student(
        organization_id=organization.id,
        first_name="Wanjiru",
        last_name="Otieno",
        grade="Grade 4",
        status=StudentStatus.ACTIVE,
    )
    db.add(child)
    db.flush()
    db.add(
        StudentGuardian(
            organization_id=organization.id,
            student_id=child.id,
            guardian_id=guardian.id,
            relationship=GuardianRelationship.MOTHER,
            is_primary=True,
        )
    )
    db.add(
        StudentRouteAssignment(
            organization_id=organization.id,
            student_id=child.id,
            route_id=route.id,
            pickup_stop_id=pickup.id,
            dropoff_stop_id=dropoff.id,
            active_from=kenya_today(),
        )
    )
    db.commit()
    return organization, child


def test_a_parent_sees_only_their_own_children(client: TestClient, db_session: Session) -> None:
    organization, child = build_family(db_session)

    assert (
        client.post(
            "/api/v1/auth/sign-in",
            json={"email": "parent@example.test", "password": PASSWORD},
        ).status_code
        == 200
    )

    response = client.get("/api/v1/parent/me")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["school_name"] == "Family School"
    assert [c["student_id"] for c in body["children"]] == [str(child.id)]
    assert body["children"][0]["route_code"] == "R1"
    assert body["children"][0]["pickup_stop"] == "Main gate"
    assert body["has_consent"] is False


def test_a_parent_without_a_child_sees_an_empty_family(
    client: TestClient, db_session: Session
) -> None:
    organization = make_organization(db_session, "Empty School")
    user = make_user(db_session, "lonely@example.test")
    make_membership(db_session, user, organization, MembershipRole.PARENT)
    db_session.add(
        Guardian(
            organization_id=organization.id,
            full_name="Lonely Parent",
            whatsapp_number="+254700000011",
            status=GuardianStatus.INVITED,
            user_id=user.id,
        )
    )
    db_session.commit()

    client.post("/api/v1/auth/sign-in", json={"email": "lonely@example.test", "password": PASSWORD})
    response = client.get("/api/v1/parent/me")
    assert response.status_code == 200
    assert response.json()["children"] == []


def test_school_staff_cannot_use_the_parent_api(client: TestClient, db_session: Session) -> None:
    organization = make_organization(db_session, "Staff School")
    make_membership(
        db_session,
        make_user(db_session, "staff-admin@example.test"),
        organization,
        MembershipRole.SCHOOL_ADMIN,
    )
    client.post(
        "/api/v1/auth/sign-in", json={"email": "staff-admin@example.test", "password": PASSWORD}
    )
    assert client.get("/api/v1/parent/me").status_code == 403
