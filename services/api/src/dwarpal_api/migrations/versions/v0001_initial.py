"""Initial tables: projects, API keys, verification sessions and attempts, signing keys, issued tokens.

Revision ID: 0001
Revises:
Created: 2026-10-16
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TIMESTAMP = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("allowed_origins", postgresql.ARRAY(sa.Text()), nullable=False),
        sa.Column("created_at", TIMESTAMP, nullable=False),
    )
    op.create_table(
        "api_keys",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("livemode", sa.Boolean(), nullable=False),
        sa.Column("lookup", sa.String(16), nullable=False, unique=True),
        sa.Column("secret_digest", sa.LargeBinary(32), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("created_at", TIMESTAMP, nullable=False),
        sa.Column("revoked_at", TIMESTAMP, nullable=True),
    )
    op.create_index("ix_api_keys_project_id", "api_keys", ["project_id"])
    op.create_table(
        "verification_sessions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("livemode", sa.Boolean(), nullable=False),
        sa.Column("policy_id", sa.String(40), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("outcome", sa.String(16), nullable=True),
        sa.Column("client_secret_digest", sa.LargeBinary(32), nullable=False),
        sa.Column("return_url", sa.Text(), nullable=True),
        sa.Column("external_ref", sa.String(200), nullable=True),
        sa.Column("attempts_count", sa.Integer(), nullable=False),
        sa.Column("model_version", sa.String(80), nullable=True),
        sa.Column("created_at", TIMESTAMP, nullable=False),
        sa.Column("expires_at", TIMESTAMP, nullable=False),
        sa.Column("completed_at", TIMESTAMP, nullable=True),
    )
    op.create_index("ix_verification_sessions_project_id", "verification_sessions", ["project_id"])
    op.create_table(
        "verification_attempts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "session_id", sa.Uuid(), sa.ForeignKey("verification_sessions.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("outcome", sa.String(16), nullable=False),
        sa.Column("reasons", postgresql.ARRAY(sa.Text()), nullable=False),
        sa.Column("scores", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", TIMESTAMP, nullable=False),
    )
    op.create_index("ix_verification_attempts_session_id", "verification_attempts", ["session_id"])
    op.create_table(
        "signing_keys",
        sa.Column("kid", sa.String(40), primary_key=True),
        sa.Column("public_jwk", postgresql.JSONB(), nullable=False),
        sa.Column("private_key_sealed", sa.LargeBinary(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("created_at", TIMESTAMP, nullable=False),
    )
    op.create_table(
        "issued_tokens",
        sa.Column("jti", sa.Uuid(), primary_key=True),
        sa.Column(
            "session_id", sa.Uuid(), sa.ForeignKey("verification_sessions.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("audience", sa.String(40), nullable=False),
        sa.Column("issued_at", TIMESTAMP, nullable=False),
        sa.Column("expires_at", TIMESTAMP, nullable=False),
    )
    op.create_index("ix_issued_tokens_session_id", "issued_tokens", ["session_id"])


def downgrade() -> None:
    dependents_first = (
        "issued_tokens",
        "signing_keys",
        "verification_attempts",
        "verification_sessions",
        "api_keys",
        "projects",
    )
    for table in dependents_first:
        op.drop_table(table)
