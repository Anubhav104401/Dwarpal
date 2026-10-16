"""Command-line helpers for the API: apply database migrations, and create a demo project with a test key.

uv run --package dwarpal-api python -m dwarpal_api.cli migrate
uv run --package dwarpal-api python -m dwarpal_api.cli seed-dev
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import UTC, datetime
from pathlib import Path

from alembic import command
from alembic.config import Config

from dwarpal_api.adapters.db import make_engine, make_sessions
from dwarpal_api.adapters.tables import ApiKey, Project
from dwarpal_api.domain import ids
from dwarpal_api.domain.keys import generate_api_key
from dwarpal_api.settings import Settings

MIGRATIONS = Path(__file__).resolve().parent / "migrations"
DEMO_ORIGINS = ["http://localhost:3000", "http://localhost:3100"]


def migration_config(database_url: str | None = None) -> Config:
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS))
    if database_url:
        config.set_main_option("sqlalchemy.url", database_url)
    return config


def migrate(database_url: str | None = None) -> None:
    command.upgrade(migration_config(database_url), "head")


async def seed_dev(settings: Settings, origins: list[str] | None = None, livemode: bool = False) -> tuple[str, str]:
    now = datetime.now(UTC)
    millis = int(now.timestamp() * 1000)
    engine = make_engine(settings.database_url)
    key = generate_api_key(livemode=livemode)
    project = Project(
        id=ids.uuid7(millis), name="Amber Cellars (demo)", allowed_origins=origins or DEMO_ORIGINS, created_at=now
    )
    api_key = ApiKey(
        id=ids.uuid7(millis),
        project_id=project.id,
        livemode=livemode,
        lookup=key.lookup,
        secret_digest=key.digest,
        name="demo shop",
        created_at=now,
        revoked_at=None,
    )
    async with make_sessions(engine)() as session:
        session.add(project)
        await session.flush()
        session.add(api_key)
        await session.commit()
    await engine.dispose()
    return ids.encode("prj", project.id), key.plaintext


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="dwarpal-api", description="Dwarpal API helpers")
    parser.add_argument("command", choices=["migrate", "seed-dev"])
    args = parser.parse_args(argv)
    if args.command == "migrate":
        migrate()
        print("database is at the latest migration")
        return 0
    project_id, plaintext = asyncio.run(seed_dev(Settings()))
    print(f"project:  {project_id}\ntest key: {plaintext}\n(store the key now; it is shown only once)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
