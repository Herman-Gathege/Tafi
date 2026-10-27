"""Sprint 4 review fixes: no parent logins, crew deactivated not deleted, stopped on record.

- Removes `guardians.user_id` (added in 0005): parents sign in with a one-time WhatsApp code
  in Sprint 5 (D-20), not with a password. Any `parent` memberships the demo seed created
  go too.
- Adds `memberships.is_active`: crew are deactivated, never deleted, so their trips and
  boarding events stay attributed to them (D-34).
- Adds the server's record of "I am stopped" to `trips`, and the confirmation each mark
  relied on to `boarding_events` (D-32).

Revision ID: 0006_sprint4_fixes
Revises: 0005_parent_accounts
Create Date: 2026-10-26
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0006_sprint4_fixes"
down_revision: str | None = "0005_parent_accounts"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Parent logins (0005) are withdrawn.
    op.drop_index("uq_guardian_user", table_name="guardians")
    op.drop_index(op.f("ix_guardians_user_id"), table_name="guardians")
    op.drop_constraint("fk_guardians_user_id_users", "guardians", type_="foreignkey")
    op.drop_column("guardians", "user_id")
    op.execute(sa.text("DELETE FROM memberships WHERE role = 'parent'"))

    # Crew are deactivated, never deleted.
    op.add_column(
        "memberships",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )

    # "I am stopped", recorded by the server.
    op.add_column(
        "trips", sa.Column("stopped_confirmed_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "trips", sa.Column("stopped_confirmed_by_membership_id", sa.Uuid(), nullable=True)
    )
    op.create_foreign_key(
        "fk_trips_stopped_confirmed_by_membership_id_memberships",
        "trips",
        "memberships",
        ["stopped_confirmed_by_membership_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.add_column(
        "boarding_events",
        sa.Column("stopped_confirmed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("boarding_events", "stopped_confirmed_at")
    op.drop_constraint(
        "fk_trips_stopped_confirmed_by_membership_id_memberships", "trips", type_="foreignkey"
    )
    op.drop_column("trips", "stopped_confirmed_by_membership_id")
    op.drop_column("trips", "stopped_confirmed_at")
    op.drop_column("memberships", "is_active")

    op.add_column("guardians", sa.Column("user_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_guardians_user_id_users",
        "guardians",
        "users",
        ["user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(op.f("ix_guardians_user_id"), "guardians", ["user_id"])
    op.create_index("uq_guardian_user", "guardians", ["user_id"], unique=True)
