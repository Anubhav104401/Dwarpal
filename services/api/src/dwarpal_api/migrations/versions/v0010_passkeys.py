"""Passkeys: console sign-in with a key pair kept on the person's device (WebAuthn).

Revision ID: 0010
Revises: 0009
Created: 2026-11-01

A user may register a few passkeys. Only each one's public key is kept, with its ID and its signature counter; the
private key never leaves the device. Signing in with a passkey happens before anyone is named, so the passkey is
found by its ID through a function the policies don't bind.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0010"
down_revision: str | Sequence[str] | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

APP_ROLE = "dwarpal_app"
TIMESTAMP = sa.DateTime(timezone=True)

FUNCTIONS = (
    """CREATE FUNCTION dwarpal_find_passkey(p_credential_id bytea)
    RETURNS TABLE (id uuid, user_id uuid, public_key bytea, sign_count bigint)
    LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public
    AS $$ SELECT id, user_id, public_key, sign_count FROM passkeys WHERE credential_id = p_credential_id $$""",
    "REVOKE ALL ON FUNCTION dwarpal_find_passkey(bytea) FROM PUBLIC",
    f"GRANT EXECUTE ON FUNCTION dwarpal_find_passkey(bytea) TO {APP_ROLE}",
)


def upgrade() -> None:
    op.create_table(
        "passkeys",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("credential_id", sa.LargeBinary(), nullable=False, unique=True),
        sa.Column("public_key", sa.LargeBinary(), nullable=False),
        sa.Column("sign_count", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(60), nullable=False),
        sa.Column("created_at", TIMESTAMP, nullable=False),
        sa.Column("last_used_at", TIMESTAMP, nullable=True),
    )
    for statement in FUNCTIONS:
        op.execute(statement)
    op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON passkeys TO {APP_ROLE}")
    op.execute("ALTER TABLE passkeys ENABLE ROW LEVEL SECURITY")
    op.execute("CREATE POLICY tenant ON passkeys USING (user_id = app_user())")


def downgrade() -> None:
    op.drop_table("passkeys")
    op.execute("DROP FUNCTION dwarpal_find_passkey(bytea)")
