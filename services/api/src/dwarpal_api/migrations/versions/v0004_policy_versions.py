"""Custom policies, as versions that never change: editing a policy adds its next version.

Revision ID: 0004
Revises: 0003
Created: 2026-10-25

A session pins the version it was created with (`policy_version`; 0 means one of the built-in presets), so changing a
policy never changes the rules for a check already under way, and every result says exactly which rules it followed.
The API's role may read and add versions but never change or delete one: the database itself keeps them immutable.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | Sequence[str] | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

APP_ROLE = "dwarpal_app"


def upgrade() -> None:
    op.create_table(
        "policies",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(40), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("min_age", sa.Integer(), nullable=False),
        sa.Column("risk_budget", sa.Float(), nullable=False),
        sa.Column("max_face_attempts", sa.Integer(), nullable=False),
        sa.Column("token_ttl_s", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("project_id", "name", "version", name="uq_policies_project_id_name_version"),
    )
    op.execute(f"GRANT SELECT, INSERT ON policies TO {APP_ROLE}")
    op.execute("ALTER TABLE policies ENABLE ROW LEVEL SECURITY")
    op.execute("CREATE POLICY tenant ON policies USING (project_id IN (SELECT id FROM projects))")
    # Sessions made before this migration all used presets.
    op.add_column(
        "verification_sessions", sa.Column("policy_version", sa.Integer(), nullable=False, server_default="0")
    )
    op.alter_column("verification_sessions", "policy_version", server_default=None)


def downgrade() -> None:
    op.drop_column("verification_sessions", "policy_version")
    op.drop_table("policies")
