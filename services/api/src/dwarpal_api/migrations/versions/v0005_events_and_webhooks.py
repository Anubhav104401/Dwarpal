"""Events, webhook endpoints and the delivery outbox; tokens remember when they were introspected.

Revision ID: 0005
Revises: 0004
Created: 2026-10-25

An event is written in the same transaction as the change it reports, together with one delivery row per webhook
endpoint that wants it (the transactional outbox), so an outcome can't be saved without its notification, or the
other way round. Events never change once written. The delivery worker, an operator process, sends the rows.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ARRAY, JSONB

revision: str = "0005"
down_revision: str | Sequence[str] | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

APP_ROLE = "dwarpal_app"
TIMESTAMP = sa.DateTime(timezone=True)
BY_PROJECT = "project_id IN (SELECT id FROM projects)"
RIGHTS = {
    "webhook_endpoints": ("SELECT, INSERT, UPDATE, DELETE", BY_PROJECT),
    "events": ("SELECT, INSERT", BY_PROJECT),  # an event, once written, is history
    "webhook_deliveries": ("SELECT, INSERT, UPDATE", "endpoint_id IN (SELECT id FROM webhook_endpoints)"),
}


def upgrade() -> None:
    op.create_table(
        "webhook_endpoints",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("livemode", sa.Boolean(), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("secret_sealed", sa.LargeBinary(), nullable=False),
        sa.Column("events", ARRAY(sa.Text()), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("created_at", TIMESTAMP, nullable=False),
    )
    op.create_index("ix_webhook_endpoints_project_id", "webhook_endpoints", ["project_id"])
    op.create_table(
        "events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("livemode", sa.Boolean(), nullable=False),
        sa.Column("type", sa.String(60), nullable=False),
        sa.Column("data", JSONB(), nullable=False),
        sa.Column("created_at", TIMESTAMP, nullable=False),
    )
    op.create_index("ix_events_project_id_id", "events", ["project_id", "id"])
    op.create_table(
        "webhook_deliveries",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("endpoint_id", sa.Uuid(), sa.ForeignKey("webhook_endpoints.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_id", sa.Uuid(), sa.ForeignKey("events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("attempt", sa.Integer(), nullable=False),
        sa.Column("next_attempt_at", TIMESTAMP, nullable=False),
        sa.Column("last_status", sa.Integer(), nullable=True),
        sa.Column("last_error", sa.String(200), nullable=True),
        sa.Column("created_at", TIMESTAMP, nullable=False),
        sa.Column("delivered_at", TIMESTAMP, nullable=True),
    )
    op.create_index("ix_webhook_deliveries_endpoint_id", "webhook_deliveries", ["endpoint_id"])
    # The worker's question, "what is due now?", reads only pending rows in time order.
    op.create_index(
        "ix_webhook_deliveries_due",
        "webhook_deliveries",
        ["next_attempt_at"],
        postgresql_where=sa.text("status = 'pending'"),
    )
    for table, (rights, rule) in RIGHTS.items():
        op.execute(f"GRANT {rights} ON {table} TO {APP_ROLE}")
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"CREATE POLICY tenant ON {table} USING ({rule})")
    op.add_column("issued_tokens", sa.Column("introspected_at", TIMESTAMP, nullable=True))


def downgrade() -> None:
    op.drop_column("issued_tokens", "introspected_at")
    op.drop_table("webhook_deliveries")
    op.drop_table("events")
    op.drop_table("webhook_endpoints")
