"""A school admin manages children, guardians and emergency contacts (D-22)."""

import uuid
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.guardian import Guardian, GuardianStatus
from app.models.organization import Organization
from app.models.user import MembershipRole
from tests.helpers import (
    PASSWORD,
    make_guardian,
    make_membership,
    make_organization,
    make_student,
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


def mother(number: str = "0712 345 678", **extra: object) -> dict[str, Any]:
    return {
        "full_name": "Achieng Otieno",
        "whatsapp_number": number,
        "relationship": "mother",
        **extra,
    }


def add_child(client: TestClient, first_name: str = "Wanjiru", **extra: object) -> dict[str, Any]:
    body: dict[str, Any] = {
        "first_name": first_name,
        "last_name": "Otieno",
        "grade": "Grade 4",
        **extra,
    }
    body.setdefault("guardians", [mother()])
    response = client.post(f"{API}/students", json=body)
    assert response.status_code == 201, response.text
    return response.json()


# --- Children and their guardians -----------------------------------------------------------


def test_add_a_child_with_a_guardian(client: TestClient, db_session: Session) -> None:
    school_admin(client, db_session)

    child = add_child(client)

    assert child["first_name"] == "Wanjiru"
    assert child["status"] == "active"
    [guardian] = child["guardians"]
    assert guardian["whatsapp_number"] == "+254712345678"
    assert guardian["is_primary"] is True
    assert guardian["status"] == "invited"
    assert child["emergency_contacts"] == []


def test_a_child_needs_at_least_one_guardian(client: TestClient, db_session: Session) -> None:
    school_admin(client, db_session)
    response = client.post(
        f"{API}/students", json={"first_name": "A", "last_name": "B", "guardians": []}
    )
    assert response.status_code == 422


def test_guardian_numbers_must_be_whatsapp_mobiles(client: TestClient, db_session: Session) -> None:
    school_admin(client, db_session)
    for number in ("020 123 4567", "12345", "not a number"):
        response = client.post(
            f"{API}/students",
            json={"first_name": "A", "last_name": "B", "guardians": [mother(number)]},
        )
        assert response.status_code == 422, number


def test_siblings_share_one_guardian_record(client: TestClient, db_session: Session) -> None:
    school_admin(client, db_session)
    add_child(client, "Wanjiru")
    second = add_child(client, "Baraka", guardians=[mother("+254 712 345 678")])

    assert second["guardians"][0]["full_name"] == "Achieng Otieno"
    assert db_session.scalar(select(func.count()).select_from(Guardian)) == 1

    [guardian] = client.get(f"{API}/guardians").json()
    assert sorted(child["first_name"] for child in guardian["children"]) == ["Baraka", "Wanjiru"]


def test_one_primary_guardian_at_all_times(client: TestClient, db_session: Session) -> None:
    school_admin(client, db_session)
    child = add_child(client)
    url = f"{API}/students/{child['id']}/guardians"

    with_father = client.post(
        url,
        json={
            "full_name": "Otieno Senior",
            "whatsapp_number": "0722 000 111",
            "relationship": "father",
            "is_primary": True,
        },
    ).json()
    primaries = [g["full_name"] for g in with_father["guardians"] if g["is_primary"]]
    assert primaries == ["Otieno Senior"]
    father_id = with_father["guardians"][0]["guardian_id"]
    mother_id = with_father["guardians"][1]["guardian_id"]

    # The primary cannot simply be switched off; another must be chosen.
    assert client.patch(f"{url}/{father_id}", json={"is_primary": False}).status_code == 422
    switched = client.patch(f"{url}/{mother_id}", json={"is_primary": True}).json()
    assert [g["guardian_id"] for g in switched["guardians"] if g["is_primary"]] == [mother_id]

    # Removing the primary promotes the remaining guardian.
    after = client.delete(f"{url}/{mother_id}").json()
    assert [(g["guardian_id"], g["is_primary"]) for g in after["guardians"]] == [(father_id, True)]

    # The last guardian of an active child stays.
    assert client.delete(f"{url}/{father_id}").status_code == 409

    # Linking the same guardian twice is refused.
    again = client.post(url, json={**mother("0722 000 111"), "relationship": "father"})
    assert again.status_code == 409


def test_an_inactive_child_can_lose_their_last_guardian_but_not_come_back_without_one(
    client: TestClient, db_session: Session
) -> None:
    school_admin(client, db_session)
    child = add_child(client)
    guardian_id = child["guardians"][0]["guardian_id"]

    client.patch(f"{API}/students/{child['id']}", json={"status": "inactive"})
    removed = client.delete(f"{API}/students/{child['id']}/guardians/{guardian_id}")
    assert removed.status_code == 200
    assert removed.json()["guardians"] == []

    reactivate = client.patch(f"{API}/students/{child['id']}", json={"status": "active"})
    assert reactivate.status_code == 409


def test_edit_a_child_and_search(client: TestClient, db_session: Session) -> None:
    school_admin(client, db_session)
    child = add_child(client, "Wanjiru")
    add_child(client, "Baraka", guardians=[mother("0733 999 888", full_name="Mary Kamau")])

    edited = client.patch(
        f"{API}/students/{child['id']}", json={"last_name": "Kamau", "grade": None}
    ).json()
    assert (edited["last_name"], edited["grade"]) == ("Kamau", None)

    def names(query: str) -> list[str]:
        return [s["first_name"] for s in client.get(f"{API}/students", params={"q": query}).json()]

    assert names("wanjiru kamau") == ["Wanjiru"]
    assert names("mary") == ["Baraka"]
    assert names("0733 999") == ["Baraka"]
    assert names("nobody") == []

    client.patch(f"{API}/students/{child['id']}", json={"status": "inactive"})
    active = client.get(f"{API}/students", params={"status": "active"}).json()
    assert [s["first_name"] for s in active] == ["Baraka"]


# --- Emergency contacts ---------------------------------------------------------------------


def test_emergency_contacts(client: TestClient, db_session: Session) -> None:
    school_admin(client, db_session)
    child = add_child(client)

    added = client.post(
        f"{API}/students/{child['id']}/emergency-contacts",
        json={"name": "Aunt Njeri", "phone": "020 123 4567", "relationship": "aunt"},
    )
    assert added.status_code == 201
    [contact] = added.json()["emergency_contacts"]
    assert contact["phone"] == "+254201234567"  # a landline is fine here

    edited = client.patch(
        f"{API}/emergency-contacts/{contact['id']}", json={"phone": "0711 111 111"}
    ).json()
    assert edited["emergency_contacts"][0]["phone"] == "+254711111111"

    removed = client.delete(f"{API}/emergency-contacts/{contact['id']}").json()
    assert removed["emergency_contacts"] == []


# --- Guardians ------------------------------------------------------------------------------


def test_the_school_corrects_a_guardian_until_they_confirm(
    client: TestClient, db_session: Session
) -> None:
    school_admin(client, db_session)
    add_child(client)
    add_child(client, "Baraka", guardians=[mother("0733 999 888", full_name="Mary Kamau")])
    achieng, mary = sorted(client.get(f"{API}/guardians").json(), key=lambda g: g["full_name"])

    fixed = client.patch(
        f"{API}/guardians/{achieng['id']}",
        json={"full_name": "Achieng Atieno", "whatsapp_number": "0799 000 000"},
    )
    assert fixed.json()["whatsapp_number"] == "+254799000000"

    taken = client.patch(
        f"{API}/guardians/{achieng['id']}", json={"whatsapp_number": "0733 999 888"}
    )
    assert taken.status_code == 409

    confirmed = db_session.get(Guardian, uuid.UUID(mary["id"]))
    assert confirmed is not None
    confirmed.status = GuardianStatus.CONFIRMED
    db_session.commit()
    locked = client.patch(f"{API}/guardians/{mary['id']}", json={"full_name": "M. Kamau"})
    assert locked.status_code == 409

    invited = client.get(f"{API}/guardians", params={"status": "invited"}).json()
    assert [g["full_name"] for g in invited] == ["Achieng Atieno"]


# --- Tenancy and roles ----------------------------------------------------------------------


def test_another_schools_children_and_guardians_are_out_of_reach(
    client: TestClient, db_session: Session
) -> None:
    hilltop = make_organization(db_session, "Hilltop School")
    their_child = make_student(db_session, hilltop, "Brian", "Otieno")
    their_guardian = make_guardian(db_session, hilltop, number="+254712345678")

    school_admin(client, db_session)
    ours = add_child(client)  # same number as their guardian: a separate person at our school

    assert [s["id"] for s in client.get(f"{API}/students").json()] == [ours["id"]]
    assert client.get(f"{API}/students/{their_child.id}").status_code == 404
    assert (
        client.patch(f"{API}/students/{their_child.id}", json={"first_name": "x"}).status_code
        == 404
    )
    assert (
        client.post(f"{API}/students/{their_child.id}/guardians", json=mother()).status_code == 404
    )
    assert client.get(f"{API}/guardians/{their_guardian.id}").status_code == 404
    assert (
        client.patch(f"{API}/guardians/{their_guardian.id}", json={"full_name": "x"}).status_code
        == 404
    )
    assert ours["guardians"][0]["guardian_id"] != str(their_guardian.id)


def test_crew_cannot_see_children(client: TestClient, db_session: Session) -> None:
    school = make_organization(db_session)
    make_membership(
        db_session, make_user(db_session, "peter@example.com"), school, MembershipRole.DRIVER
    )
    assert sign_in(client, "peter@example.com").status_code == 200
    assert client.get(f"{API}/students").status_code == 403
    assert client.get(f"{API}/guardians").status_code == 403
