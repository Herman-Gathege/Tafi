"""Add trips, boarding events and trip locations.

Revision ID: 0004_crew_trips
Revises: 0003_school_operations
Create Date: 2026-10-16
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004_crew_trips"
down_revision: str | None = "0003_school_operations"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "trips",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("route_run_id", sa.Uuid(), nullable=False),
        sa.Column("service_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_by_membership_id", sa.Uuid(), nullable=True),
        sa.Column("ended_by_membership_id", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["route_run_id"], ["route_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["started_by_membership_id"], ["memberships.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["ended_by_membership_id"], ["memberships.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("route_run_id", "service_date", name="uq_trip_run_service_date"),
    )
    op.create_index(op.f("ix_trips_organization_id"), "trips", ["organization_id"])
    op.create_index(op.f("ix_trips_route_run_id"), "trips", ["route_run_id"])
    op.create_index(
        "ix_trips_organization_service_date", "trips", ["organization_id", "service_date"]
    )

    op.create_table(
        "boarding_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("trip_id", sa.Uuid(), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("recorded_by_membership_id", sa.Uuid(), nullable=False),
        sa.Column("method", sa.String(length=32), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("latitude", sa.Numeric(9, 6), nullable=True),
        sa.Column("longitude", sa.Numeric(9, 6), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["trip_id"], ["trips.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["recorded_by_membership_id"], ["memberships.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_boarding_events_organization_id"), "boarding_events", ["organization_id"]
    )
    op.create_index(op.f("ix_boarding_events_trip_id"), "boarding_events", ["trip_id"])
    op.create_index(op.f("ix_boarding_events_student_id"), "boarding_events", ["student_id"])
    op.create_index("ix_boarding_events_trip_student", "boarding_events", ["trip_id", "student_id"])

    op.create_table(
        "trip_locations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("trip_id", sa.Uuid(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("latitude", sa.Numeric(9, 6), nullable=False),
        sa.Column("longitude", sa.Numeric(9, 6), nullable=False),
        sa.Column("accuracy_m", sa.Numeric(7, 2), nullable=True),
        sa.Column("recorded_by_membership_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["trip_id"], ["trips.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["recorded_by_membership_id"], ["memberships.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_trip_locations_organization_id"), "trip_locations", ["organization_id"]
    )
    op.create_index(op.f("ix_trip_locations_trip_id"), "trip_locations", ["trip_id"])
    op.create_index("ix_trip_locations_trip_recorded", "trip_locations", ["trip_id", "recorded_at"])


def downgrade() -> None:
    op.drop_index("ix_trip_locations_trip_recorded", table_name="trip_locations")
    op.drop_index(op.f("ix_trip_locations_trip_id"), table_name="trip_locations")
    op.drop_index(op.f("ix_trip_locations_organization_id"), table_name="trip_locations")
    op.drop_table("trip_locations")

    op.drop_index("ix_boarding_events_trip_student", table_name="boarding_events")
    op.drop_index(op.f("ix_boarding_events_student_id"), table_name="boarding_events")
    op.drop_index(op.f("ix_boarding_events_trip_id"), table_name="boarding_events")
    op.drop_index(op.f("ix_boarding_events_organization_id"), table_name="boarding_events")
    op.drop_table("boarding_events")

    op.drop_index("ix_trips_organization_service_date", table_name="trips")
    op.drop_index(op.f("ix_trips_route_run_id"), table_name="trips")
    op.drop_index(op.f("ix_trips_organization_id"), table_name="trips")
    op.drop_table("trips")
