"""Daily counts of the ID-document check: how many sessions reached it, and how those checks ended.

Revision ID: 0013
Revises: 0012
Created: 2026-11-09

The console's dashboard shows the design's step-up conversion: of the people who reached the ID-document check — sent
there by a face check that couldn't decide, or starting there in a live check while no age model is certified (D24) —
the share who finished it, and the share who passed. Each session that reaches the check adds one to a daily count of
"opened", and each check that ends adds one to a count of how it ended. Like `face_stage_stats`, the counts outlive the
sessions and say nothing about any one person.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0013"
down_revision: str | Sequence[str] | None = "0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

APP_ROLE = "dwarpal_app"


def upgrade() -> None:
    op.create_table(
        "document_stage_stats",
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("livemode", sa.Boolean(), primary_key=True),
        sa.Column("day", sa.Date(), primary_key=True),
        sa.Column("step", sa.String(16), primary_key=True),
        sa.Column("sessions", sa.Integer(), nullable=False),
    )
    op.execute(f"GRANT SELECT, INSERT, UPDATE ON document_stage_stats TO {APP_ROLE}")
    op.execute("ALTER TABLE document_stage_stats ENABLE ROW LEVEL SECURITY")
    op.execute("CREATE POLICY tenant ON document_stage_stats USING (project_id IN (SELECT id FROM projects))")


def downgrade() -> None:
    op.drop_table("document_stage_stats")
