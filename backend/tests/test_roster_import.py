"""A school imports its roster from a spreadsheet saved as CSV (S3-11)."""

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.guardian import Guardian
from app.models.organization import Organization
from app.models.student import Student
from app.models.user import MembershipRole
from tests.helpers import (
    PASSWORD,
    make_membership,
    make_organization,
    make_route,
    make_stop,
    make_user,
)

IMPORT = "/api/v1/school/students/import"
HEADER = (
    "first_name,last_name,class,guardian_name,guardian_whatsapp,guardian_relationship,"
    "second_guardian_name,second_guardian_whatsapp,second_guardian_relationship,"
    "route_code,pickup_stop,dropoff_stop"
)


def sign_in(client: TestClient, email: str, password: str = PASSWORD):
    return client.post("/api/v1/auth/sign-in", json={"email": email, "password": password})


def school_admin(client: TestClient, db: Session) -> Organization:
    school = make_organization(db)
    make_membership(db, make_user(db, "grace@example.com"), school)
    assert sign_in(client, "grace@example.com").status_code == 200
    route = make_route(db, school, "R1")
    make_stop(db, route, "Main gate", 1)
    make_stop(db, route, "Shops", 2)
    return school


def csv(*rows: str, header: str = HEADER) -> dict[str, str]:
    return {"csv": "\n".join([header, *rows]) + "\n"}


def count(db: Session, model: type) -> int:
    return db.scalar(select(func.count()).select_from(model)) or 0


GOOD = [
    "Wanjiru,Otieno,Grade 4,Achieng Otieno,0712 345 678,mother,Otieno Senior,0722 000 111,father,"
    "R1,Main gate,Shops",
    "Baraka,Otieno,Grade 2,Achieng Otieno,+254712345678,Mother,,,,r1,main gate,",
    "",
    "Juma,Kamau,PP2,Mary Kamau,0733 999 888,,,,,,,",
]


def test_preview_says_what_would_happen_and_saves_nothing(
    client: TestClient, db_session: Session
) -> None:
    school_admin(client, db_session)

    preview = client.post(f"{IMPORT}/preview", json=csv(*GOOD))

    assert preview.status_code == 200, preview.text
    assert preview.json() == {
        "rows": 3,
        "children_to_add": 3,
        "children_skipped": 0,
        "guardians_new": 3,  # Achieng (shared by siblings), Otieno Senior, Mary
        "guardians_existing": 0,
        "assigned_to_routes": 2,
        "problems": [],
        "imported": False,
    }
    assert count(db_session, Student) == 0


def test_import_creates_children_guardians_and_routes(
    client: TestClient, db_session: Session
) -> None:
    school_admin(client, db_session)

    done = client.post(IMPORT, json=csv(*GOOD))

    assert done.status_code == 200, done.text
    assert done.json()["imported"] is True
    assert count(db_session, Student) == 3
    assert count(db_session, Guardian) == 3

    children = {s["first_name"]: s for s in client.get("/api/v1/school/students").json()}
    wanjiru = children["Wanjiru"]
    assert [(g["full_name"], g["is_primary"]) for g in wanjiru["guardians"]] == [
        ("Achieng Otieno", True),
        ("Otieno Senior", False),
    ]
    assert wanjiru["route"]["pickup_stop"]["name"] == "Main gate"
    assert wanjiru["route"]["dropoff_stop"]["name"] == "Shops"
    assert children["Baraka"]["guardians"][0]["whatsapp_number"] == "+254712345678"
    assert children["Baraka"]["route"]["dropoff_stop"] is None
    assert children["Juma"]["route"] is None
    assert children["Juma"]["guardians"][0]["relationship"] == "guardian"  # blank → guardian


def test_every_problem_is_listed_by_row_and_nothing_is_imported(
    client: TestClient, db_session: Session
) -> None:
    school_admin(client, db_session)
    rows = csv(
        GOOD[0],
        ",Kamau,,Mary Kamau,0733 999 888,,,,,,,",
        "Juma,Kamau,,Mary Kamau,0733 99,,,,,,,",
        "Amani,Njeri,,Ann Njeri,0711 111 111,aunt,,,,,,",
        "Brian,Ouma,,Lucy Ouma,0744 444 444,,,,,R9,Main gate,",
        "Faith,Mwangi,,Grace Mwangi,0755 555 555,,,,,R1,Shell,",
        "Tom,Kip,,Rose Kip,0766 666 666,,,,,,Main gate,",
        "Ann,Wairimu,,Jane Wairimu,0777 777 777,,Paul Wairimu,0777 777 777,father,,,",
    )

    preview = client.post(f"{IMPORT}/preview", json=rows).json()

    assert [(p["row"], p["message"]) for p in preview["problems"]] == [
        (3, "first name is empty"),
        (4, "guardian WhatsApp number '0733 99' is not a mobile number"),
        (5, "guardian relationship must be mother, father, guardian or other"),
        (6, "there is no route R9"),
        (7, "no stop called 'Shell' on route R1"),
        (8, "a stop needs a route_code"),
        (9, "the two guardians have the same WhatsApp number"),
    ]
    refused = client.post(IMPORT, json=rows)
    assert refused.status_code == 422
    assert "Nothing was imported: 7 rows need fixing" in refused.json()["detail"]
    assert count(db_session, Student) == 0


def test_the_header_must_match_the_template(client: TestClient, db_session: Session) -> None:
    school_admin(client, db_session)

    missing = client.post(
        f"{IMPORT}/preview", json=csv("Wanjiru,Otieno", header="first_name,last_name")
    ).json()
    assert missing["problems"] == [
        {"row": 1, "message": "Missing columns: guardian_name, guardian_whatsapp"}
    ]

    unknown = client.post(
        f"{IMPORT}/preview",
        json=csv("a,b,c,d,e", header="first_name,last_name,guardian_name,guardian_whatsapp,shoe"),
    ).json()
    assert unknown["problems"][0]["message"].startswith("Unknown column: shoe")


def test_excel_style_files_are_understood(client: TestClient, db_session: Session) -> None:
    """Excel adds an invisible byte-order mark, and some set-ups separate with ';'."""
    school_admin(client, db_session)
    text = (
        "\ufeffFirst Name;Last Name;Grade;Guardian Name;Guardian WhatsApp;"
        "Route Code;Pickup Stop\r\n"
        "Wanjiru;Otieno;Grade 4;Achieng Otieno;0712 345 678;R1;Shops\r\n"
    )

    preview = client.post(f"{IMPORT}/preview", json={"csv": text}).json()

    assert preview["problems"] == []
    assert (preview["children_to_add"], preview["assigned_to_routes"]) == (1, 1)


def test_importing_the_same_file_again_skips_children_already_there(
    client: TestClient, db_session: Session
) -> None:
    school_admin(client, db_session)
    client.post(IMPORT, json=csv(*GOOD))

    again = client.post(
        IMPORT, json=csv(*GOOD, "Neema,Otieno,Grade 1,Achieng Otieno,0712345678,,,,,,,")
    )

    assert again.json()["children_skipped"] == 3
    assert again.json()["children_to_add"] == 1
    assert again.json()["guardians_existing"] == 1  # Neema's mother is already known
    assert count(db_session, Student) == 4
    assert count(db_session, Guardian) == 3


def test_a_child_listed_twice_is_a_problem(client: TestClient, db_session: Session) -> None:
    school_admin(client, db_session)
    preview = client.post(f"{IMPORT}/preview", json=csv(GOOD[3], GOOD[3])).json()
    assert preview["problems"] == [{"row": 3, "message": "Juma Kamau is in the file twice"}]


def test_another_schools_routes_are_not_found(client: TestClient, db_session: Session) -> None:
    hilltop = make_organization(db_session, "Hilltop School")
    make_stop(db_session, make_route(db_session, hilltop, "R7"), "Gate")
    school_admin(client, db_session)

    preview = client.post(
        f"{IMPORT}/preview", json=csv("Juma,Kamau,,Mary Kamau,0733999888,,,,,R7,Gate,")
    ).json()

    assert preview["problems"] == [{"row": 2, "message": "there is no route R7"}]


def test_crew_cannot_import(client: TestClient, db_session: Session) -> None:
    school = make_organization(db_session)
    make_membership(
        db_session, make_user(db_session, "peter@example.com"), school, MembershipRole.DRIVER
    )
    assert sign_in(client, "peter@example.com").status_code == 200
    assert client.post(f"{IMPORT}/preview", json=csv(*GOOD)).status_code == 403
    assert client.post(IMPORT, json=csv(*GOOD)).status_code == 403
