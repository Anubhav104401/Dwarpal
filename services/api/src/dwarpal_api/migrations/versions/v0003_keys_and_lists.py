"""Scoped, expiring API keys, and an index for listing a project's sessions newest first.

Revision ID: 0003
Revises: 0002
Created: 2026-10-25

A key now carries the operations it may perform (its scopes) and, once it has been rotated, the moment it stops
working. The key look-up function returns both, so it is replaced.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ARRAY

revision: str = "0003"
down_revision: str | Sequence[str] | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

APP_ROLE = "dwarpal_app"
EVERY_SCOPE = "{sessions:read,sessions:write}"
FIND_KEY = """CREATE FUNCTION dwarpal_find_api_key(p_lookup text)
    RETURNS TABLE (id uuid, project_id uuid, livemode boolean, secret_digest bytea, revoked_at timestamptz{extra})
    LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public
    AS $$ SELECT id, project_id, livemode, secret_digest, revoked_at{columns}
          FROM api_keys WHERE lookup = p_lookup $$"""


def replace_find_key(extra: str, columns: str) -> None:
    op.execute("DROP FUNCTION dwarpal_find_api_key(text)")
    op.execute(FIND_KEY.format(extra=extra, columns=columns))
    op.execute("REVOKE ALL ON FUNCTION dwarpal_find_api_key(text) FROM PUBLIC")
    op.execute(f"GRANT EXECUTE ON FUNCTION dwarpal_find_api_key(text) TO {APP_ROLE}")


def upgrade() -> None:
    # Existing keys keep doing everything they did; the default is removed again, so new keys must say their scopes.
    op.add_column("api_keys", sa.Column("scopes", ARRAY(sa.Text()), nullable=False, server_default=EVERY_SCOPE))
    op.alter_column("api_keys", "scopes", server_default=None)
    op.add_column("api_keys", sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_verification_sessions_project_id_id", "verification_sessions", ["project_id", "id"])
    replace_find_key(", scopes text[], expires_at timestamptz", ", scopes, expires_at")


def downgrade() -> None:
    replace_find_key("", "")
    op.drop_index("ix_verification_sessions_project_id_id", table_name="verification_sessions")
    op.drop_column("api_keys", "expires_at")
    op.drop_column("api_keys", "scopes")
