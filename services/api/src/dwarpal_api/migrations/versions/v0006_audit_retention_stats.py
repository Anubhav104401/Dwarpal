"""A tamper-evident audit log per organisation, a retention period per project, and daily session counts.

Revision ID: 0006
Revises: 0005
Created: 2026-10-25

Each audit entry carries the hash of the one before it, so changing or removing any entry breaks every hash after it.
The API's role may only add entries; `audit_heads` holds each organisation's latest link and serialises appends.
Session metadata is purged after the project's retention period; the daily counts in `session_stats` are kept.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0006"
down_revision: str | Sequence[str] | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

APP_ROLE = "dwarpal_app"
TIMESTAMP = sa.DateTime(timezone=True)
BY_ORGANISATION = "org_id IN (SELECT id FROM organizations)"
RIGHTS = {
    "audit_log": ("SELECT, INSERT", BY_ORGANISATION),  # an audit entry, once written, is never changed
    "audit_heads": ("SELECT, INSERT, UPDATE", BY_ORGANISATION),
    "session_stats": ("SELECT, INSERT, UPDATE", "project_id IN (SELECT id FROM projects)"),
}


def upgrade() -> None:
    op.create_table(
        "audit_heads",
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("last_seq", sa.BigInteger(), nullable=False),
        sa.Column("last_hash", sa.LargeBinary(32), nullable=False),
    )
    op.create_table(
        "audit_log",
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("seq", sa.BigInteger(), primary_key=True),
        sa.Column("actor_type", sa.String(16), nullable=False),
        sa.Column("actor_id", sa.String(64), nullable=False),
        sa.Column("action", sa.String(60), nullable=False),
        sa.Column("target", sa.String(80), nullable=False),
        sa.Column("data", JSONB(), nullable=False),
        sa.Column("prev_hash", sa.LargeBinary(32), nullable=False),
        sa.Column("hash", sa.LargeBinary(32), nullable=False),
        sa.Column("created_at", TIMESTAMP, nullable=False),
    )
    op.create_table(
        "session_stats",
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("livemode", sa.Boolean(), primary_key=True),
        sa.Column("day", sa.Date(), primary_key=True),
        sa.Column("policy", sa.String(60), primary_key=True),
        sa.Column("outcome", sa.String(16), primary_key=True),
        sa.Column("sessions", sa.Integer(), nullable=False),
    )
    for table, (rights, rule) in RIGHTS.items():
        op.execute(f"GRANT {rights} ON {table} TO {APP_ROLE}")
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"CREATE POLICY tenant ON {table} USING ({rule})")
    op.add_column("projects", sa.Column("retention_days", sa.Integer(), nullable=False, server_default="90"))
    op.alter_column("projects", "retention_days", server_default=None)
    op.create_check_constraint("ck_projects_retention_days", "projects", "retention_days BETWEEN 1 AND 365")
    # The purge looks for old sessions across every project.
    op.create_index("ix_verification_sessions_created_at", "verification_sessions", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_verification_sessions_created_at", table_name="verification_sessions")
    op.drop_constraint("ck_projects_retention_days", "projects", type_="check")
    op.drop_column("projects", "retention_days")
    op.drop_table("session_stats")
    op.drop_table("audit_log")
    op.drop_table("audit_heads")
