"""Who may act in a school, and in which one — enforced by the API, not the UI.

Sprint 3's real routes arrive task by task; these tests exercise the guards through a small
probe router so the rules are pinned down before any route depends on them.
"""

import uuid
from collections.abc import Iterator

import pytest
from fastapi import APIRouter
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.deps import (
    ORGANIZATION_HEADER,
    Crew,
    DbSession,
    SchoolAdmin,
    get_owned_or_404,
)
from app.db.session import get_db
from app.main import create_app
from app.models.organization import OrganizationType
from app.models.student import Student
from app.models.user import MembershipRole
from tests.helpers import PASSWORD, make_membership, make_organization, make_student, make_user

probe = APIRouter(prefix="/probe")


@probe.get("/school")
def school_only(membership: SchoolAdmin) -> dict[str, str]:
    return {"organization_id": str(membership.organization_id)}


@probe.get("/crew")
def crew_only(membership: Crew) -> dict[str, str]:
    return {"role": membership.role.value}


@probe.get("/students/{student_id}")
def read_student(student_id: uuid.UUID, membership: SchoolAdmin, db: DbSession) -> dict[str, str]:
    student = get_owned_or_404(db, Student, student_id, membership, what="student")
    return {"id": str(student.id)}


@pytest.fixture
def probe_client(db_session: Session) -> Iterator[TestClient]:
    app = create_app()
    app.include_router(probe)
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def sign_in(client: TestClient, email: str, password: str = PASSWORD):
    return client.post("/api/v1/auth/sign-in", json={"email": email, "password": password})


def member(
    db: Session, email: str, role: MembershipRole, *, school_name: str = "Riverside Academy"
) -> uuid.UUID:
    """Create a person with one membership and return the organization id."""
    school = make_organization(db, school_name)
    make_membership(db, make_user(db, email), school, role)
    return school.id


def test_signed_out_visitors_are_turned_away(probe_client: TestClient) -> None:
    assert probe_client.get("/probe/school").status_code == 401
    assert probe_client.get("/probe/crew").status_code == 401


def test_a_school_admin_acts_in_their_school(probe_client: TestClient, db_session: Session) -> None:
    school_id = member(db_session, "grace@example.com", MembershipRole.SCHOOL_ADMIN)
    assert sign_in(probe_client, "grace@example.com").status_code == 200

    response = probe_client.get("/probe/school")

    assert response.status_code == 200
    assert response.json()["organization_id"] == str(school_id)
    assert probe_client.get("/probe/crew").status_code == 403


@pytest.mark.parametrize("role", [MembershipRole.DRIVER, MembershipRole.CONDUCTOR])
def test_crew_cannot_reach_school_admin_routes(
    probe_client: TestClient, db_session: Session, role: MembershipRole
) -> None:
    member(db_session, "crew@example.com", role)
    assert sign_in(probe_client, "crew@example.com").status_code == 200

    assert probe_client.get("/probe/school").status_code == 403
    crew = probe_client.get("/probe/crew")
    assert crew.status_code == 200
    assert crew.json()["role"] == role.value


def test_an_operator_admin_is_not_a_school_admin(
    probe_client: TestClient, db_session: Session
) -> None:
    operator = make_organization(db_session, "Swift Shuttles", OrganizationType.OPERATOR)
    make_membership(db_session, make_user(db_session, "ops@example.com"), operator)
    assert sign_in(probe_client, "ops@example.com").status_code == 200

    assert probe_client.get("/probe/school").status_code == 403


def test_someone_in_two_schools_must_choose_one(
    probe_client: TestClient, db_session: Session
) -> None:
    riverside = make_organization(db_session, "Riverside Academy")
    hilltop = make_organization(db_session, "Hilltop School")
    elsewhere = make_organization(db_session, "Elsewhere School")
    user = make_user(db_session, "grace@example.com")
    make_membership(db_session, user, riverside)
    make_membership(db_session, user, hilltop)
    assert sign_in(probe_client, "grace@example.com").status_code == 200

    assert probe_client.get("/probe/school").status_code == 400

    chosen = probe_client.get("/probe/school", headers={ORGANIZATION_HEADER: str(hilltop.id)})
    assert chosen.status_code == 200
    assert chosen.json()["organization_id"] == str(hilltop.id)

    # The header picks among the caller's own schools; it never grants access to another.
    refused = probe_client.get("/probe/school", headers={ORGANIZATION_HEADER: str(elsewhere.id)})
    assert refused.status_code == 403


def test_another_schools_record_is_reported_missing(
    probe_client: TestClient, db_session: Session
) -> None:
    riverside = make_organization(db_session, "Riverside Academy")
    hilltop = make_organization(db_session, "Hilltop School")
    make_membership(db_session, make_user(db_session, "grace@example.com"), riverside)
    ours = make_student(db_session, riverside)
    theirs = make_student(db_session, hilltop, "Brian", "Otieno")
    assert sign_in(probe_client, "grace@example.com").status_code == 200

    assert probe_client.get(f"/probe/students/{ours.id}").status_code == 200
    assert probe_client.get(f"/probe/students/{theirs.id}").status_code == 404
    assert probe_client.get(f"/probe/students/{uuid.uuid4()}").status_code == 404
