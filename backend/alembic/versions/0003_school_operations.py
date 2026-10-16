"""Add the school's data: students, guardians, consent, routes, stops, vehicles, runs.

Membership roles are stored as text, so the new `conductor` role (D-21) needs no change here.

Revision ID: 0003_school_operations
Revises: 0002_auth_and_tenancy
Create Date: 2026-10-14
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003_school_operations"
down_revision: str | None = "0002_auth_and_tenancy"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _id() -> sa.Column:
    return sa.Column("id", sa.Uuid(), nullable=False)


def _organization_id() -> sa.Column:
    return sa.Column("organization_id", sa.Uuid(), nullable=False)


def _organization_fk() -> sa.ForeignKeyConstraint:
    return sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE")


def _created_at() -> sa.Column:
    return sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )


def _updated_at() -> sa.Column:
    return sa.Column(
        "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )


def _index(table: str, column: str, *, unique: bool = False) -> None:
    op.create_index(op.f(f"ix_{table}_{column}"), table, [column], unique=unique)


def upgrade() -> None:
    # --- Children -----------------------------------------------------------------------------
    op.create_table(
        "students",
        _id(),
        _organization_id(),
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("last_name", sa.String(length=100), nullable=False),
        sa.Column("grade", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        _created_at(),
        _updated_at(),
        _organization_fk(),
        sa.PrimaryKeyConstraint("id"),
    )
    _index("students", "organization_id")

    op.create_table(
        "emergency_contacts",
        _id(),
        _organization_id(),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=False),
        sa.Column("relationship", sa.String(length=64), nullable=True),
        _created_at(),
        _updated_at(),
        _organization_fk(),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    _index("emergency_contacts", "organization_id")
    _index("emergency_contacts", "student_id")

    op.create_table(
        "child_cards",
        _id(),
        _organization_id(),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column(
            "issued_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        _created_at(),
        _organization_fk(),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    _index("child_cards", "organization_id")
    _index("child_cards", "student_id")
    _index("child_cards", "code", unique=True)

    # --- Guardians and consent ----------------------------------------------------------------
    op.create_table(
        "guardians",
        _id(),
        _organization_id(),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("whatsapp_number", sa.String(length=20), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="invited"),
        _created_at(),
        _updated_at(),
        _organization_fk(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id", "whatsapp_number", name="uq_guardian_organization_whatsapp"
        ),
    )
    _index("guardians", "organization_id")

    op.create_table(
        "student_guardians",
        _id(),
        _organization_id(),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("guardian_id", sa.Uuid(), nullable=False),
        sa.Column("relationship", sa.String(length=32), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("receives_messages", sa.Boolean(), nullable=False, server_default=sa.true()),
        _created_at(),
        _organization_fk(),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["guardian_id"], ["guardians.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("student_id", "guardian_id", name="uq_student_guardian"),
    )
    _index("student_guardians", "organization_id")
    _index("student_guardians", "student_id")
    _index("student_guardians", "guardian_id")

    op.create_table(
        "guardian_consents",
        _id(),
        _organization_id(),
        sa.Column("guardian_id", sa.Uuid(), nullable=False),
        sa.Column("consent_version", sa.String(length=32), nullable=False),
        sa.Column("method", sa.String(length=32), nullable=False),
        sa.Column("given_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("withdrawn_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("recorded_by_user_id", sa.Uuid(), nullable=True),
        _created_at(),
        _organization_fk(),
        sa.ForeignKeyConstraint(["guardian_id"], ["guardians.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recorded_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    _index("guardian_consents", "organization_id")
    _index("guardian_consents", "guardian_id")

    op.create_table(
        "guardian_invites",
        _id(),
        _organization_id(),
        sa.Column("guardian_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("invited_by_user_id", sa.Uuid(), nullable=True),
        _created_at(),
        _organization_fk(),
        sa.ForeignKeyConstraint(["guardian_id"], ["guardians.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["invited_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    _index("guardian_invites", "organization_id")
    _index("guardian_invites", "guardian_id")
    _index("guardian_invites", "token_hash", unique=True)

    # --- Routes, stops and vehicles -----------------------------------------------------------
    op.create_table(
        "routes",
        _id(),
        _organization_id(),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        _created_at(),
        _updated_at(),
        _organization_fk(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "code", name="uq_route_organization_code"),
    )
    _index("routes", "organization_id")

    op.create_table(
        "stops",
        _id(),
        _organization_id(),
        sa.Column("route_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("landmark", sa.String(length=255), nullable=True),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("latitude", sa.Numeric(precision=9, scale=6), nullable=True),
        sa.Column("longitude", sa.Numeric(precision=9, scale=6), nullable=True),
        _created_at(),
        _updated_at(),
        _organization_fk(),
        sa.ForeignKeyConstraint(["route_id"], ["routes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    _index("stops", "organization_id")
    _index("stops", "route_id")

    op.create_table(
        "vehicles",
        _id(),
        _organization_id(),
        sa.Column("plate", sa.String(length=16), nullable=False),
        sa.Column("seats", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        _created_at(),
        _updated_at(),
        _organization_fk(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "plate", name="uq_vehicle_organization_plate"),
    )
    _index("vehicles", "organization_id")

    op.create_table(
        "route_runs",
        _id(),
        _organization_id(),
        sa.Column("route_id", sa.Uuid(), nullable=False),
        sa.Column("direction", sa.String(length=32), nullable=False),
        sa.Column("departure_time", sa.Time(), nullable=False),
        sa.Column("vehicle_id", sa.Uuid(), nullable=True),
        sa.Column("driver_membership_id", sa.Uuid(), nullable=False),
        sa.Column("conductor_membership_id", sa.Uuid(), nullable=True),
        _created_at(),
        _updated_at(),
        _organization_fk(),
        sa.ForeignKeyConstraint(["route_id"], ["routes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"], ondelete="SET NULL"),
        # No ON DELETE: a driver who still drives a run cannot be removed until reassigned.
        sa.ForeignKeyConstraint(["driver_membership_id"], ["memberships.id"]),
        sa.ForeignKeyConstraint(
            ["conductor_membership_id"], ["memberships.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("route_id", "direction", name="uq_route_run_route_direction"),
    )
    _index("route_runs", "organization_id")
    _index("route_runs", "route_id")
    _index("route_runs", "vehicle_id")
    _index("route_runs", "driver_membership_id")
    _index("route_runs", "conductor_membership_id")

    # --- Who rides where -----------------------------------------------------------------------
    op.create_table(
        "student_route_assignments",
        _id(),
        _organization_id(),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("route_id", sa.Uuid(), nullable=False),
        sa.Column("pickup_stop_id", sa.Uuid(), nullable=True),
        sa.Column("dropoff_stop_id", sa.Uuid(), nullable=True),
        sa.Column("active_from", sa.Date(), nullable=False),
        sa.Column("active_to", sa.Date(), nullable=True),
        _created_at(),
        _updated_at(),
        _organization_fk(),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["route_id"], ["routes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["pickup_stop_id"], ["stops.id"]),
        sa.ForeignKeyConstraint(["dropoff_stop_id"], ["stops.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    _index("student_route_assignments", "organization_id")
    _index("student_route_assignments", "student_id")
    _index("student_route_assignments", "route_id")
    _index("student_route_assignments", "pickup_stop_id")
    _index("student_route_assignments", "dropoff_stop_id")
    op.create_index(
        "uq_student_route_assignments_current",
        "student_route_assignments",
        ["student_id"],
        unique=True,
        postgresql_where=sa.text("active_to IS NULL"),
        sqlite_where=sa.text("active_to IS NULL"),
    )

    op.create_table(
        "stop_change_requests",
        _id(),
        _organization_id(),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("guardian_id", sa.Uuid(), nullable=False),
        sa.Column("requested_stop_id", sa.Uuid(), nullable=True),
        sa.Column("requested_location", sa.String(length=500), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("decided_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        _created_at(),
        _updated_at(),
        _organization_fk(),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["guardian_id"], ["guardians.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["requested_stop_id"], ["stops.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["decided_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    _index("stop_change_requests", "organization_id")
    _index("stop_change_requests", "student_id")
    _index("stop_change_requests", "guardian_id")


def downgrade() -> None:
    # Dropping a table drops its indexes with it.
    for table in (
        "stop_change_requests",
        "student_route_assignments",
        "route_runs",
        "vehicles",
        "stops",
        "routes",
        "guardian_invites",
        "guardian_consents",
        "student_guardians",
        "guardians",
        "child_cards",
        "emergency_contacts",
        "students",
    ):
        op.drop_table(table)
