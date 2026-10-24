"""Tenancy: organisations own projects, and row-level security confines every query to one tenant.

Revision ID: 0002
Revises: 0001
Created: 2026-10-24

The API connects as `dwarpal_app`, a role that owns no tables, so PostgreSQL applies the policies below to every query
it makes. Each unit of work names its tenant first (`app.project_id`, or `app.org_id` for the console); with none
named, the policies match nothing. Migrations and operator tools run as the tables' owner, whom the policies don't bind.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | Sequence[str] | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TIMESTAMP = sa.DateTime(timezone=True)
APP_ROLE = "dwarpal_app"
TENANT_TABLES = (
    "organizations",
    "projects",
    "api_keys",
    "verification_sessions",
    "verification_attempts",
    "issued_tokens",
)

# Which rows each table shows: those of the tenant the transaction named. A project's own rows, or every project's
# rows in the organisation; attempts and tokens follow their session, which the session policy already confines.
POLICIES = {
    "organizations": "id = app_org() OR id = (SELECT org_id FROM projects WHERE id = app_project())",
    "projects": "id = app_project() OR org_id = app_org()",
    "api_keys": "project_id IN (SELECT id FROM projects)",
    "verification_sessions": "project_id IN (SELECT id FROM projects)",
    "verification_attempts": "session_id IN (SELECT id FROM verification_sessions)",
    "issued_tokens": "session_id IN (SELECT id FROM verification_sessions)",
}

# Each statement is sent on its own: the database driver runs one statement per call.
FUNCTIONS = (
    """CREATE FUNCTION app_project() RETURNS uuid LANGUAGE sql STABLE
    AS $$ SELECT nullif(current_setting('app.project_id', true), '')::uuid $$""",
    """CREATE FUNCTION app_org() RETURNS uuid LANGUAGE sql STABLE
    AS $$ SELECT nullif(current_setting('app.org_id', true), '')::uuid $$""",
    # Two lookups made before the tenant is known. They run as the tables' owner (SECURITY DEFINER), so the policies
    # don't hide the row, and they return only what authentication needs.
    """CREATE FUNCTION dwarpal_find_api_key(p_lookup text)
    RETURNS TABLE (id uuid, project_id uuid, livemode boolean, secret_digest bytea, revoked_at timestamptz)
    LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public
    AS $$ SELECT id, project_id, livemode, secret_digest, revoked_at FROM api_keys WHERE lookup = p_lookup $$""",
    """CREATE FUNCTION dwarpal_session_project(p_session uuid) RETURNS uuid
    LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public
    AS $$ SELECT project_id FROM verification_sessions WHERE id = p_session $$""",
    "REVOKE ALL ON FUNCTION dwarpal_find_api_key(text), dwarpal_session_project(uuid) FROM PUBLIC",
)


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("slug", sa.String(60), nullable=False, unique=True),
        sa.Column("created_at", TIMESTAMP, nullable=False),
    )
    op.add_column("projects", sa.Column("org_id", sa.Uuid(), nullable=True))
    # Projects made before organisations existed each get one of their own.
    op.execute(
        "INSERT INTO organizations (id, name, slug, created_at) "
        "SELECT id, name || ' (organisation)', 'org-' || replace(id::text, '-', ''), created_at FROM projects"
    )
    op.execute("UPDATE projects SET org_id = id")
    op.alter_column("projects", "org_id", nullable=False)
    op.create_foreign_key("fk_projects_org_id", "projects", "organizations", ["org_id"], ["id"], ondelete="CASCADE")
    op.create_index("ix_projects_org_id", "projects", ["org_id"])

    op.execute(
        f"DO $$ BEGIN IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '{APP_ROLE}') "
        f"THEN CREATE ROLE {APP_ROLE} NOLOGIN; END IF; END $$"
    )
    # The login that runs the migrations may become the role (SET ROLE); PostgreSQL 16+ doesn't grant that by itself.
    op.execute(f"GRANT {APP_ROLE} TO CURRENT_USER")
    for statement in FUNCTIONS:
        op.execute(statement)
    op.execute(f"GRANT USAGE ON SCHEMA public TO {APP_ROLE}")
    op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {APP_ROLE}")
    op.execute(f"REVOKE ALL ON alembic_version FROM {APP_ROLE}")  # the migration history is the migrations' alone
    op.execute(f"GRANT EXECUTE ON FUNCTION dwarpal_find_api_key(text), dwarpal_session_project(uuid) TO {APP_ROLE}")
    for table, rule in POLICIES.items():
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"CREATE POLICY tenant ON {table} USING ({rule})")


def downgrade() -> None:
    for table in TENANT_TABLES:
        op.execute(f"DROP POLICY IF EXISTS tenant ON {table}")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
    op.execute("DROP FUNCTION dwarpal_session_project(uuid), dwarpal_find_api_key(text), app_org(), app_project()")
    op.execute(f"REVOKE ALL ON ALL TABLES IN SCHEMA public FROM {APP_ROLE}")
    op.execute(f"REVOKE USAGE ON SCHEMA public FROM {APP_ROLE}")
    op.drop_index("ix_projects_org_id", table_name="projects")
    op.drop_constraint("fk_projects_org_id", "projects", type_="foreignkey")
    op.drop_column("projects", "org_id")
    op.drop_table("organizations")
