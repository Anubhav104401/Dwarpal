"""Alembic's entry point: connect to the database and apply migrations, using the API's own settings."""

from __future__ import annotations

import asyncio

from alembic import context
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from dwarpal_api.adapters.tables import METADATA
from dwarpal_api.settings import Settings


def run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=METADATA, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


async def run_online() -> None:
    url = context.config.get_main_option("sqlalchemy.url") or Settings().database_url
    engine = create_async_engine(url)
    async with engine.connect() as connection:
        await connection.run_sync(run_migrations)
    await engine.dispose()


if context.is_offline_mode():
    raise SystemExit("offline (SQL-script) migrations are not supported; run them against a database")
asyncio.run(run_online())
