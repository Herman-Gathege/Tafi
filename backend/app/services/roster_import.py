"""Import a school's roster from a spreadsheet saved as CSV (S3-11).

Two passes over the same rules: `plan_import` checks every row and says what would happen;
`apply_import` does it, and only when no row has a problem — a school never ends up with half
an import. Children already in the school (same name, same guardian number) are skipped, so a
corrected file can be imported again.
"""

import csv
import io
import uuid
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.guardian import Guardian, GuardianRelationship, StudentGuardian
from app.models.student import Student
from app.models.transport import Route, Stop
from app.schemas.common import normalise_mobile

MAX_ROWS = 2000

# Header names as they appear in the template, in order. "grade" is accepted for "class".
COLUMNS = [
    "first_name",
    "last_name",
    "class",
    "guardian_name",
    "guardian_whatsapp",
    "guardian_relationship",
    "second_guardian_name",
    "second_guardian_whatsapp",
    "second_guardian_relationship",
    "route_code",
    "pickup_stop",
    "dropoff_stop",
]
REQUIRED = ["first_name", "last_name", "guardian_name", "guardian_whatsapp"]
ALIASES = {"grade": "class"}


@dataclass
class GuardianRow:
    full_name: str
    whatsapp_number: str
    relationship: GuardianRelationship


@dataclass
class ChildRow:
    row: int
    first_name: str
    last_name: str
    grade: str | None
    guardians: list[GuardianRow]
    route: Route | None = None
    pickup: Stop | None = None
    dropoff: Stop | None = None


@dataclass
class ImportPlan:
    rows: int = 0
    to_add: list[ChildRow] = field(default_factory=list)
    skipped: int = 0
    guardians_new: int = 0
    guardians_existing: int = 0
    problems: list[tuple[int, str]] = field(default_factory=list)

    @property
    def assigned_to_routes(self) -> int:
        return sum(1 for child in self.to_add if child.route is not None)


def _header_key(name: str) -> str:
    key = name.strip().lower().replace(" ", "_").replace("-", "_")
    return ALIASES.get(key, key)


def _read(text: str) -> tuple[list[dict[str, str]], list[tuple[int, str]]]:
    """Rows keyed by column name. Handles Excel's byte-order mark and ';' separators."""
    text = text.lstrip("\ufeff")
    first_line = text.split("\n", 1)[0]
    delimiter = ";" if first_line.count(";") > first_line.count(",") else ","
    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    try:
        header = next(reader)
    except StopIteration:
        return [], [(1, "The file is empty")]
    keys = [_header_key(name) for name in header]
    missing = [column for column in REQUIRED if column not in keys]
    if missing:
        return [], [(1, f"Missing column{'s' if len(missing) > 1 else ''}: {', '.join(missing)}")]
    unknown = [header[i] for i, key in enumerate(keys) if key and key not in COLUMNS]
    if unknown:
        return [], [(1, f"Unknown column: {', '.join(unknown)}. Use the template's headings.")]

    rows: list[dict[str, str]] = []
    for values in reader:
        if not any(value.strip() for value in values):
            rows.append({})  # keep row numbers aligned with the spreadsheet
            continue
        rows.append(
            {key: (values[i].strip() if i < len(values) else "") for i, key in enumerate(keys)}
        )
    return rows, []


def _required(record: dict[str, str], column: str, limit: int, problems: list[str]) -> str:
    """A required cell: note it when empty or too long."""
    value = record.get(column, "")
    if not value:
        problems.append(f"{column.replace('_', ' ')} is empty")
    elif len(value) > limit:
        problems.append(f"{column.replace('_', ' ')} is too long")
    return value


def _relationship(value: str, default: GuardianRelationship) -> GuardianRelationship | None:
    if not value:
        return default
    try:
        return GuardianRelationship(value.strip().lower())
    except ValueError:
        return None


def plan_import(db: Session, organization_id: uuid.UUID, text: str) -> ImportPlan:
    plan = ImportPlan()
    records, problems = _read(text)
    if problems:
        plan.problems = problems
        return plan

    routes = {
        route.code.upper(): route
        for route in db.scalars(select(Route).where(Route.organization_id == organization_id))
    }
    stops_by_route: dict[uuid.UUID, dict[str, Stop]] = {}
    for stop in db.scalars(select(Stop).where(Stop.organization_id == organization_id)):
        stops_by_route.setdefault(stop.route_id, {})[stop.name.strip().lower()] = stop
    existing_numbers = set(
        db.scalars(
            select(Guardian.whatsapp_number).where(Guardian.organization_id == organization_id)
        )
    )
    # (first, last, number) for every child already linked to a guardian at this school.
    existing_children = {
        (first.lower(), last.lower(), number)
        for first, last, number in db.execute(
            select(Student.first_name, Student.last_name, Guardian.whatsapp_number)
            .join(StudentGuardian, StudentGuardian.student_id == Student.id)
            .join(Guardian, Guardian.id == StudentGuardian.guardian_id)
            .where(Student.organization_id == organization_id)
        )
    }

    seen_in_file: set[tuple[str, str, str]] = set()
    new_numbers: set[str] = set()
    reused_numbers: set[str] = set()

    for index, record in enumerate(records, start=2):
        if not record:
            continue
        plan.rows += 1
        if plan.rows > MAX_ROWS:
            plan.problems.append((index, f"Too many rows: import at most {MAX_ROWS} at a time"))
            break
        row_problems: list[str] = []

        first = _required(record, "first_name", 100, row_problems)
        last = _required(record, "last_name", 100, row_problems)
        grade = record.get("class", "")
        if len(grade) > 50:
            row_problems.append("class is too long")

        guardians: list[GuardianRow] = []
        for prefix, required, default in (
            ("guardian", True, GuardianRelationship.GUARDIAN),
            ("second_guardian", False, GuardianRelationship.GUARDIAN),
        ):
            name = record.get(f"{prefix}_name", "")
            number = record.get(f"{prefix}_whatsapp", "")
            if not required and not name and not number:
                continue
            label = prefix.replace("_", " ")
            if not name:
                row_problems.append(f"{label} name is empty")
            elif len(name) > 255:
                row_problems.append(f"{label} name is too long")
            normalised = ""
            if not number:
                row_problems.append(f"{label} WhatsApp number is empty")
            else:
                try:
                    normalised = normalise_mobile(number)
                except ValueError:
                    row_problems.append(
                        f"{label} WhatsApp number '{number}' is not a mobile number"
                    )
            relationship = _relationship(record.get(f"{prefix}_relationship", ""), default)
            if relationship is None:
                row_problems.append(
                    f"{label} relationship must be mother, father, guardian or other"
                )
            if name and normalised and relationship is not None:
                guardians.append(GuardianRow(name, normalised, relationship))
        if len(guardians) == 2 and guardians[0].whatsapp_number == guardians[1].whatsapp_number:
            row_problems.append("the two guardians have the same WhatsApp number")

        child = ChildRow(index, first, last, grade or None, guardians)
        code = record.get("route_code", "").upper()
        pickup_name = record.get("pickup_stop", "")
        dropoff_name = record.get("dropoff_stop", "")
        if code:
            route = routes.get(code)
            if route is None:
                row_problems.append(f"there is no route {code}")
            elif not route.is_active:
                row_problems.append(f"route {code} is not running")
            else:
                child.route = route
                stops = stops_by_route.get(route.id, {})
                for which, name in (("pickup", pickup_name), ("dropoff", dropoff_name)):
                    if name:
                        found = stops.get(name.strip().lower())
                        if found is None:
                            row_problems.append(f"no stop called '{name}' on route {code}")
                        else:
                            setattr(child, which, found)
                if not pickup_name and not dropoff_name:
                    row_problems.append(f"give a pickup stop, a drop-off stop or both for {code}")
        elif pickup_name or dropoff_name:
            row_problems.append("a stop needs a route_code")

        if row_problems:
            plan.problems.append((index, "; ".join(row_problems)))
            continue

        primary_number = guardians[0].whatsapp_number
        key = (first.lower(), last.lower(), primary_number)
        if key in seen_in_file:
            plan.problems.append((index, f"{first} {last} is in the file twice"))
            continue
        seen_in_file.add(key)
        if key in existing_children:
            plan.skipped += 1
            continue

        plan.to_add.append(child)
        for guardian in guardians:
            if guardian.whatsapp_number in existing_numbers:
                reused_numbers.add(guardian.whatsapp_number)
            else:
                new_numbers.add(guardian.whatsapp_number)

    plan.guardians_new = len(new_numbers)
    plan.guardians_existing = len(reused_numbers)
    return plan
