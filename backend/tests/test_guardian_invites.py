"""A guardian confirms their details and consents through their link (S3-05, S3-06, D-22)."""

import uuid
from datetime import timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.clock import utcnow
from app.models.guardian import ConsentMethod, GuardianConsent, GuardianInvite
from app.models.organization import Organization
from app.models.transport import Route, Stop
from app.models.user import MembershipRole
from app.services.consent import (
    CONSENT_VERSION,
    can_message,
    record_consent,
    withdraw_consent,
)
from tests.helpers import (
    PASSWORD,
    make_guardian,
    make_membership,
    make_organization,
    make_route,
    make_stop,
    make_user,
)

API = "/api/v1/school"
PUBLIC = "/api/v1/guardian-invites"


def sign_in(client: TestClient, email: str, password: str = PASSWORD):
    return client.post("/api/v1/auth/sign-in", json={"email": email, "password": password})


def school_admin(client: TestClient, db: Session) -> Organization:
    school = make_organization(db)
    make_membership(db, make_user(db, "grace@example.com"), school)
    assert sign_in(client, "grace@example.com").status_code == 200
    return school


def add_child(
    client: TestClient, first_name: str = "Wanjiru", number: str = "0712 345 678"
) -> dict[str, Any]:
    response = client.post(
        f"{API}/students",
        json={
            "first_name": first_name,
            "last_name": "Otieno",
            "guardians": [
                {"full_name": "Achieng Otieno", "whatsapp_number": number, "relationship": "mother"}
            ],
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def on_route(
    client: TestClient, db: Session, school: Organization, child: dict[str, Any]
) -> tuple[Route, Stop, Stop]:
    route = make_route(db, school)
    gate, shops = make_stop(db, route, "Main gate", 1), make_stop(db, route, "Shops", 2)
    response = client.put(
        f"{API}/students/{child['id']}/route",
        json={"route_id": str(route.id), "pickup_stop_id": str(gate.id)},
    )
    assert response.status_code == 200, response.text
    return route, gate, shops


def invite(client: TestClient, guardian_id: str) -> str:
    response = client.post(f"{API}/guardians/{guardian_id}/invite")
    assert response.status_code == 201, response.text
    return response.json()["invite_url"].split("token=")[1]


def confirm_body(**extra: object) -> dict[str, Any]:
    return {
        "full_name": "Achieng A. Otieno",
        "email": "Achieng@Example.com",
        "consent": True,
        "consent_version": CONSENT_VERSION,
        **extra,
    }


# --- The guardian's journey ------------------------------------------------------------------


def test_the_link_shows_the_guardian_their_own_details_only(
    client: TestClient, db_session: Session
) -> None:
    school = school_admin(client, db_session)
    child = add_child(client)
    client.post(
        f"{API}/students/{child['id']}/guardians",
        json={
            "full_name": "Otieno Senior",
            "whatsapp_number": "0722 000 111",
            "relationship": "father",
        },
    )
    on_route(client, db_session, school, child)
    mother_id = child["guardians"][0]["guardian_id"]
    token = invite(client, mother_id)
    client.cookies.clear()  # the guardian has no account

    page = client.get(f"{PUBLIC}/{token}")

    assert page.status_code == 200
    body = page.json()
    assert body["school_name"] == "Riverside Academy"
    assert (body["full_name"], body["whatsapp_number"]) == ("Achieng Otieno", "+254712345678")
    [kid] = body["children"]
    assert kid["first_name"] == "Wanjiru"
    assert kid["route"]["pickup_stop"]["name"] == "Main gate"
    assert [s["name"] for s in kid["stops_on_route"]] == ["Main gate", "Shops"]
    assert "Riverside Academy" in body["consent_text"]
    assert body["consent_version"] == CONSENT_VERSION
    assert "+254722000111" not in page.text  # never another guardian's number


def test_confirming_records_consent_and_everything_the_guardian_added(
    client: TestClient, db_session: Session
) -> None:
    school = school_admin(client, db_session)
    child = add_child(client)
    _, _, shops = on_route(client, db_session, school, child)
    mother_id = child["guardians"][0]["guardian_id"]
    token = invite(client, mother_id)
    client.cookies.clear()

    done = client.post(
        f"{PUBLIC}/{token}/confirm",
        json=confirm_body(
            second_guardian={
                "full_name": "Otieno Senior",
                "whatsapp_number": "0722 000 111",
                "relationship": "father",
            },
            emergency_contacts=[
                {"student_id": child["id"], "name": "Aunt Njeri", "phone": "020 123 4567"}
            ],
            stop_changes=[
                {"student_id": child["id"], "requested_stop_id": str(shops.id)},
                {"student_id": child["id"], "requested_location": "Kilimani, near the church"},
            ],
        ),
    )
    assert done.status_code == 200, done.text
    assert done.json()["school_name"] == "Riverside Academy"

    # The link is used up.
    assert client.get(f"{PUBLIC}/{token}").status_code == 400
    assert client.post(f"{PUBLIC}/{token}/confirm", json=confirm_body()).status_code == 400

    assert sign_in(client, "grace@example.com").status_code == 200
    detail = client.get(f"{API}/students/{child['id']}").json()
    by_name = {g["full_name"]: g for g in detail["guardians"]}
    assert by_name["Achieng A. Otieno"]["status"] == "confirmed"
    assert by_name["Achieng A. Otieno"]["has_consent"] is True
    assert by_name["Achieng A. Otieno"]["email"] == "achieng@example.com"
    assert by_name["Otieno Senior"]["status"] == "invited"
    assert by_name["Otieno Senior"]["has_consent"] is False  # needs their own link
    assert detail["emergency_contacts"][0]["phone"] == "+254201234567"

    requests = client.get(f"{API}/stop-change-requests").json()
    assert [(r["requested_stop"] or {}).get("name") for r in requests] == ["Shops", None]
    assert requests[1]["requested_location"] == "Kilimani, near the church"
    assert all(r["status"] == "pending" for r in requests)


def test_consent_must_be_given_to_the_current_wording(
    client: TestClient, db_session: Session
) -> None:
    school_admin(client, db_session)
    child = add_child(client)
    token = invite(client, child["guardians"][0]["guardian_id"])
    client.cookies.clear()

    refused = client.post(f"{PUBLIC}/{token}/confirm", json=confirm_body(consent=False))
    assert refused.status_code == 422
    stale = client.post(f"{PUBLIC}/{token}/confirm", json=confirm_body(consent_version="2025-old"))
    assert stale.status_code == 409
    assert client.get(f"{PUBLIC}/{token}").status_code == 200  # still usable


def test_a_guardian_can_only_act_for_their_own_children_and_route(
    client: TestClient, db_session: Session
) -> None:
    school = school_admin(client, db_session)
    child = add_child(client)
    on_route(client, db_session, school, child)
    other_child = add_child(client, "Baraka", number="0733 999 888")
    other_route = make_route(db_session, school, "R2")
    elsewhere = make_stop(db_session, other_route, "Far away")
    token = invite(client, child["guardians"][0]["guardian_id"])
    client.cookies.clear()

    not_theirs = client.post(
        f"{PUBLIC}/{token}/confirm",
        json=confirm_body(
            emergency_contacts=[
                {"student_id": other_child["id"], "name": "X", "phone": "0711111111"}
            ]
        ),
    )
    assert not_theirs.status_code == 422
    wrong_route = client.post(
        f"{PUBLIC}/{token}/confirm",
        json=confirm_body(
            stop_changes=[{"student_id": child["id"], "requested_stop_id": str(elsewhere.id)}]
        ),
    )
    assert wrong_route.status_code == 422


def test_a_new_link_replaces_the_old_one_and_links_expire(
    client: TestClient, db_session: Session
) -> None:
    school_admin(client, db_session)
    child = add_child(client)
    guardian_id = child["guardians"][0]["guardian_id"]
    first = invite(client, guardian_id)
    second = invite(client, guardian_id)

    assert client.get(f"{PUBLIC}/{first}").status_code == 400
    assert client.get(f"{PUBLIC}/{second}").status_code == 200

    for record in db_session.scalars(select(GuardianInvite)):
        record.expires_at = utcnow() - timedelta(minutes=1)
    db_session.commit()
    assert client.get(f"{PUBLIC}/{second}").status_code == 400
    assert client.get(f"{PUBLIC}/not-a-real-token").status_code == 400


def test_invite_everyone_still_to_confirm(client: TestClient, db_session: Session) -> None:
    school_admin(client, db_session)
    first = add_child(client, "Wanjiru")
    add_child(client, "Baraka", number="0733 999 888")
    leaver = add_child(client, "Juma", number="0744 555 666")
    client.patch(f"{API}/students/{leaver['id']}", json={"status": "inactive"})

    token = invite(client, first["guardians"][0]["guardian_id"])
    client.post(f"{PUBLIC}/{token}/confirm", json=confirm_body())
    assert sign_in(client, "grace@example.com").status_code == 200

    sent = client.post(f"{API}/guardians/invite-pending")

    assert sent.status_code == 201
    # Not the confirmed mother, not the guardian of a child who left.
    assert [i["full_name"] for i in sent.json()] == ["Achieng Otieno"]
    assert sent.json()[0]["whatsapp_number"] == "+254733999888"


# --- Consent rules (S3-06) -------------------------------------------------------------------


def test_can_message_follows_consent(db_session: Session) -> None:
    school = make_organization(db_session)
    guardian = make_guardian(db_session, school)
    assert can_message(db_session, guardian) is False

    record_consent(db_session, guardian, method=ConsentMethod.SCHOOL_RECORDED)
    record_consent(db_session, guardian, method=ConsentMethod.INVITE_LINK)  # no duplicate
    assert can_message(db_session, guardian) is True

    assert withdraw_consent(db_session, guardian) is True
    assert can_message(db_session, guardian) is False
    assert withdraw_consent(db_session, guardian) is False

    record_consent(db_session, guardian, method=ConsentMethod.INVITE_LINK)
    db_session.commit()
    assert can_message(db_session, guardian) is True
    history = db_session.scalars(select(GuardianConsent)).all()
    assert [(c.method, c.withdrawn_at is None) for c in history] == [
        (ConsentMethod.SCHOOL_RECORDED, False),
        (ConsentMethod.INVITE_LINK, True),
    ]


def test_consent_to_new_wording_supersedes_the_old(db_session: Session) -> None:
    school = make_organization(db_session)
    guardian = make_guardian(db_session, school)
    record_consent(db_session, guardian, method=ConsentMethod.INVITE_LINK, version="v1")
    record_consent(db_session, guardian, method=ConsentMethod.INVITE_LINK, version="v2")
    db_session.commit()

    rows = db_session.scalars(select(GuardianConsent).order_by(GuardianConsent.given_at)).all()
    assert [(c.consent_version, c.withdrawn_at is None) for c in rows] == [
        ("v1", False),
        ("v2", True),
    ]


def test_the_school_records_paper_consent_and_withdrawals(
    client: TestClient, db_session: Session
) -> None:
    school_admin(client, db_session)
    child = add_child(client)
    guardian_id = child["guardians"][0]["guardian_id"]

    given = client.post(f"{API}/guardians/{guardian_id}/consent")
    assert given.json()["has_consent"] is True
    withdrawn = client.delete(f"{API}/guardians/{guardian_id}/consent")
    assert withdrawn.json()["has_consent"] is False
    assert client.delete(f"{API}/guardians/{guardian_id}/consent").status_code == 404

    consent = db_session.scalars(select(GuardianConsent)).one()
    assert consent.recorded_by_user_id is not None


# --- Stop-change requests ---------------------------------------------------------------------


def test_the_school_approves_or_declines_stop_changes(
    client: TestClient, db_session: Session
) -> None:
    school = school_admin(client, db_session)
    child = add_child(client)
    route, gate, shops = on_route(client, db_session, school, child)
    token = invite(client, child["guardians"][0]["guardian_id"])
    client.post(
        f"{PUBLIC}/{token}/confirm",
        json=confirm_body(
            stop_changes=[
                {"student_id": child["id"], "requested_stop_id": str(shops.id)},
                {"student_id": child["id"], "requested_location": "Near the market"},
            ]
        ),
    )
    assert sign_in(client, "grace@example.com").status_code == 200
    to_shops, to_market = client.get(f"{API}/stop-change-requests").json()

    approved = client.post(
        f"{API}/stop-change-requests/{to_shops['id']}/approve",
        json={"route_id": str(route.id), "pickup_stop_id": str(shops.id)},
    )
    assert approved.status_code == 200
    assert approved.json()["route"]["pickup_stop"]["name"] == "Shops"

    declined = client.post(f"{API}/stop-change-requests/{to_market['id']}/decline")
    assert declined.json()["status"] == "declined"

    assert client.get(f"{API}/stop-change-requests").json() == []
    decided = client.get(f"{API}/stop-change-requests", params={"status": "approved"}).json()
    assert [r["id"] for r in decided] == [to_shops["id"]]
    again = client.post(f"{API}/stop-change-requests/{to_market['id']}/decline")
    assert again.status_code == 409


# --- Tenancy and roles ----------------------------------------------------------------------


def test_another_schools_guardians_and_requests_are_out_of_reach(
    client: TestClient, db_session: Session
) -> None:
    hilltop = make_organization(db_session, "Hilltop School")
    theirs = make_guardian(db_session, hilltop)
    school_admin(client, db_session)

    assert client.post(f"{API}/guardians/{theirs.id}/invite").status_code == 404
    assert client.post(f"{API}/guardians/{theirs.id}/consent").status_code == 404
    assert client.post(f"{API}/stop-change-requests/{uuid.uuid4()}/decline").status_code == 404


@pytest.mark.parametrize("role", [MembershipRole.DRIVER, MembershipRole.CONDUCTOR])
def test_crew_cannot_invite_or_record_consent(
    client: TestClient, db_session: Session, role: MembershipRole
) -> None:
    school = make_organization(db_session)
    guardian = make_guardian(db_session, school)
    make_membership(db_session, make_user(db_session, "crew@example.com"), school, role)
    assert sign_in(client, "crew@example.com").status_code == 200

    assert client.post(f"{API}/guardians/{guardian.id}/invite").status_code == 403
    assert client.post(f"{API}/guardians/{guardian.id}/consent").status_code == 403
    assert client.get(f"{API}/stop-change-requests").status_code == 403
