"""People: console users with passwords and optional one-time codes, and their roles in organisations.

Revision ID: 0007
Revises: 0006
Created: 2026-10-25

Users are people at Dwarpal's customers, never the people who verify their age. A unit of work may now also name a
user (`app.user_id`): a user sees their own row, their memberships, and the organisations they belong to. Signing in
happens before anyone is named, so the account is found through a function the policies don't bind.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: str | Sequence[str] | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

APP_ROLE = "dwarpal_app"
TIMESTAMP = sa.DateTime(timezone=True)
ORGANISATIONS_BEFORE = "id = app_org() OR id = (SELECT org_id FROM projects WHERE id = app_project())"
# A user also sees the organisations they belong to (memberships shows them only their own rows).
ORGANISATIONS_AFTER = f"{ORGANISATIONS_BEFORE} OR id IN (SELECT org_id FROM memberships)"  # noqa: S608 - fixed text

FUNCTIONS = (
    """CREATE FUNCTION app_user() RETURNS uuid LANGUAGE sql STABLE
    AS $$ SELECT nullif(current_setting('app.user_id', true), '')::uuid $$""",
    # Signing in: what checking a password and a one-time code needs, found by e-mail address before anyone is named.
    """CREATE FUNCTION dwarpal_find_user(p_email text)
    RETURNS TABLE (id uuid, password_hash text, totp_secret_sealed bytea)
    LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public
    AS $$ SELECT id, password_hash, totp_secret_sealed FROM users WHERE email = p_email $$""",
    "REVOKE ALL ON FUNCTION dwarpal_find_user(text) FROM PUBLIC",
    f"GRANT EXECUTE ON FUNCTION dwarpal_find_user(text) TO {APP_ROLE}",
)


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("email", sa.String(254), nullable=False, unique=True),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("totp_secret_sealed", sa.LargeBinary(), nullable=True),
        sa.Column("totp_pending_sealed", sa.LargeBinary(), nullable=True),
        sa.Column("totp_last_step", sa.BigInteger(), nullable=True),
        sa.Column("created_at", TIMESTAMP, nullable=False),
        sa.Column("last_login_at", TIMESTAMP, nullable=True),
    )
    op.create_table(
        "memberships",
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("created_at", TIMESTAMP, nullable=False),
        sa.CheckConstraint("role IN ('owner', 'admin', 'developer', 'analyst')", name="ck_memberships_role"),
    )
    op.create_index("ix_memberships_user_id", "memberships", ["user_id"])
    for statement in FUNCTIONS:
        op.execute(statement)
    op.execute(f"GRANT SELECT, INSERT, UPDATE ON users TO {APP_ROLE}")
    op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON memberships TO {APP_ROLE}")
    op.execute("ALTER TABLE users ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE memberships ENABLE ROW LEVEL SECURITY")
    # Your own memberships, and every membership of the organisation the transaction named.
    op.execute("CREATE POLICY tenant ON memberships USING (user_id = app_user() OR org_id = app_org())")
    # Yourself, and the people who share the named organisation with you.
    op.execute("CREATE POLICY tenant ON users USING (id = app_user() OR id IN (SELECT user_id FROM memberships))")
    op.execute("DROP POLICY tenant ON organizations")
    op.execute(f"CREATE POLICY tenant ON organizations USING ({ORGANISATIONS_AFTER})")


def downgrade() -> None:
    op.execute("DROP POLICY tenant ON organizations")
    op.execute(f"CREATE POLICY tenant ON organizations USING ({ORGANISATIONS_BEFORE})")
    # The users policy reads memberships, and memberships points at users: the policy goes first, then the tables
    # (with their remaining policy), and only then the functions those policies used.
    op.execute("DROP POLICY tenant ON users")
    op.drop_table("memberships")
    op.drop_table("users")
    op.execute("DROP FUNCTION dwarpal_find_user(text), app_user()")
