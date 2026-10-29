"""When a person began, and daily counts of how the face check ended and how long it took.

Revision ID: 0009
Revises: 0008
Created: 2026-10-29

The console's dashboard shows the median time to a decision, the share of checks rejected as a likely attack and the
share sent to a stronger check. A session now records when the person opened the verify page, and each face check
that reaches a decision adds one to a daily count of its outcome and of its time, rounded down to a band such as
"10 to 15 seconds". Like `session_stats`, the counts outlive the sessions and say nothing about any one person.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009"
down_revision: str | Sequence[str] | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

APP_ROLE = "dwarpal_app"


def upgrade() -> None:
    op.add_column("verification_sessions", sa.Column("started_at", sa.DateTime(timezone=True), nullable=True))
    op.create_table(
        "face_stage_stats",
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("livemode", sa.Boolean(), primary_key=True),
        sa.Column("day", sa.Date(), primary_key=True),
        sa.Column("outcome", sa.String(16), primary_key=True),
        sa.Column("from_s", sa.SmallInteger(), primary_key=True),
        sa.Column("sessions", sa.Integer(), nullable=False),
    )
    op.execute(f"GRANT SELECT, INSERT, UPDATE ON face_stage_stats TO {APP_ROLE}")
    op.execute("ALTER TABLE face_stage_stats ENABLE ROW LEVEL SECURITY")
    op.execute("CREATE POLICY tenant ON face_stage_stats USING (project_id IN (SELECT id FROM projects))")


def downgrade() -> None:
    op.drop_table("face_stage_stats")
    op.drop_column("verification_sessions", "started_at")
