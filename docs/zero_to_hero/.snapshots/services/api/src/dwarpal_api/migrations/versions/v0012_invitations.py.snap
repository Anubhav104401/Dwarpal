"""Invitations: someone without an account yet is invited by e-mail address, and joins on signing up (decision D44).

Revision ID: 0012
Revises: 0011
Created: 2026-11-08

No e-mail is sent (decision D25): the invitation waits, and the person joins the organisation, with the role it names,
when they sign up with that address. Signing up happens before any organisation is named, so the invitations are taken
through a function the policies don't bind — as signing in finds an account.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0012"
down_revision: str | Sequence[str] | None = "0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

APP_ROLE = "dwarpal_app"
TIMESTAMP = sa.DateTime(timezone=True)

FUNCTIONS = (
    # Signing up: every invitation for this address is taken (deleted and returned) at once, so none is used twice.
    """CREATE FUNCTION dwarpal_take_invitations(p_email text)
    RETURNS TABLE (org_id uuid, role text, invited_by uuid)
    LANGUAGE sql VOLATILE SECURITY DEFINER SET search_path = public
    AS $$ DELETE FROM invitations WHERE email = p_email RETURNING org_id, role, invited_by $$""",
    "REVOKE ALL ON FUNCTION dwarpal_take_invitations(text) FROM PUBLIC",
    f"GRANT EXECUTE ON FUNCTION dwarpal_take_invitations(text) TO {APP_ROLE}",
)


def upgrade() -> None:
    op.create_table(
        "invitations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("invited_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", TIMESTAMP, nullable=False),
        sa.CheckConstraint("role IN ('owner', 'admin', 'developer', 'analyst')", name="ck_invitations_role"),
        sa.UniqueConstraint("org_id", "email", name="uq_invitations_org_id_email"),
    )
    op.create_index("ix_invitations_email", "invitations", ["email"])
    for statement in FUNCTIONS:
        op.execute(statement)
    op.execute(f"GRANT SELECT, INSERT, DELETE ON invitations TO {APP_ROLE}")
    op.execute("ALTER TABLE invitations ENABLE ROW LEVEL SECURITY")
    # An organisation's own invitations, only.
    op.execute("CREATE POLICY tenant ON invitations USING (org_id = app_org())")


def downgrade() -> None:
    op.drop_table("invitations")
    op.execute("DROP FUNCTION dwarpal_take_invitations(text)")
