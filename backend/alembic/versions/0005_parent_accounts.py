"""Give a guardian an optional login.

Revision ID: 0005_parent_accounts
Revises: 0004_crew_trips
Create Date: 2026-10-19
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0005_parent_accounts"
down_revision: str | None = "0004_crew_trips"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
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


def downgrade() -> None:
    op.drop_index("uq_guardian_user", table_name="guardians")
    op.drop_index(op.f("ix_guardians_user_id"), table_name="guardians")
    op.drop_constraint("fk_guardians_user_id_users", "guardians", type_="foreignkey")
    op.drop_column("guardians", "user_id")
