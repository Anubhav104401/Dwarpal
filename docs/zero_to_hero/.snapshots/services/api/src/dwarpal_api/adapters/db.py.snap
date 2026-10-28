"""The database connection: an async engine (a pool of connections), a factory for units of work, and the tenant every
unit of work is confined to."""

from __future__ import annotations

import re
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

ROLE_NAME = re.compile(r"^[a-z_][a-z0-9_]{0,62}$")
# set_config(..., true) lasts until the transaction ends: a later transaction starts with no tenant, and sees nothing.
NAME_TENANT = text(
    "SELECT set_config('app.project_id', :project, true), set_config('app.org_id', :org, true),"
    " set_config('app.user_id', :user, true)"
)
# The verify page's flow token names only a verification session: its project is looked up and named in one statement.
NAME_SESSION_TENANT = text(
    "SELECT set_config('app.project_id', coalesce(dwarpal_session_project(:session)::text, ''), true)"
)
# A console user signs in by e-mail address, before anyone is named: the same kind of function finds the account.
FIND_USER = text("SELECT id, password_hash, totp_secret_sealed FROM dwarpal_find_user(:email)")
# An API key is checked before its tenant is known, so it is read through a function that the policies don't bind.
FIND_API_KEY = text(
    "SELECT id, project_id, livemode, secret_digest, revoked_at, scopes, expires_at FROM dwarpal_find_api_key(:lookup)"
)


class Base(DeclarativeBase):
    """Every table class inherits from this, so all tables share one catalogue: Base.metadata."""


def make_engine(url: str, role: str | None = None) -> AsyncEngine:
    engine = create_async_engine(url, pool_pre_ping=True, pool_size=10, max_overflow=10)
    if role is not None:
        if not ROLE_NAME.match(role):
            raise ValueError(f"not a valid database role name: {role!r}")

        # Every new connection becomes the restricted role, which row-level security binds (owners aren't bound).
        @event.listens_for(engine.sync_engine, "connect")
        def become_role(connection: Any, _record: Any) -> None:
            # Outside any transaction (autocommit), or the pool's first rollback would undo it.
            connection.autocommit = True
            cursor = connection.cursor()
            # A role's name can't be sent as a query parameter, so it is written into the text — and checked first.
            cursor.execute(f"SET ROLE {role}")  # nosemgrep
            cursor.close()
            connection.autocommit = False

    return engine


def make_sessions(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


async def name_tenant(
    session: AsyncSession,
    project_id: uuid.UUID | None = None,
    org_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
) -> None:
    """Name the tenant for the rest of this transaction: one project, or one organisation; and, for the console, the
    signed-in user."""
    names = {
        name: str(value) if value else ""
        for name, value in (("project", project_id), ("org", org_id), ("user", user_id))
    }
    await session.execute(NAME_TENANT, names)


@asynccontextmanager
async def tenant(
    sessions: async_sessionmaker[AsyncSession],
    project_id: uuid.UUID | None = None,
    org_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
) -> AsyncIterator[AsyncSession]:
    """A unit of work confined to one project, or one organisation (and user): its first statement names the tenant,
    and the database's row-level security shows only that tenant's rows until the transaction ends."""
    async with sessions() as session:
        await name_tenant(session, project_id, org_id, user_id)
        yield session


@asynccontextmanager
async def session_tenant(
    sessions: async_sessionmaker[AsyncSession], session_id: uuid.UUID
) -> AsyncIterator[AsyncSession]:
    """A unit of work confined to the project that owns verification session `session_id` (to nothing, if there is
    no such session)."""
    async with sessions() as session:
        await session.execute(NAME_SESSION_TENANT, {"session": session_id})
        yield session
