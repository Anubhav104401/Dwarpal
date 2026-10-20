"""Command-line helpers for the API: apply database migrations, create a demo project with a test key, and summarise
recent liveness results.

uv run --package dwarpal-api python -m dwarpal_api.cli migrate
uv run --package dwarpal-api python -m dwarpal_api.cli seed-dev
uv run --package dwarpal-api python -m dwarpal_api.cli liveness-report --since 2026-10-17T12:00
"""

from __future__ import annotations

import argparse
import asyncio
import statistics
import sys
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from alembic import command
from alembic.config import Config
from sqlalchemy import select

from dwarpal_api.adapters.db import make_engine, make_sessions
from dwarpal_api.adapters.tables import ApiKey, Project, VerificationAttempt
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


def liveness_summary(attempts: list[tuple[str, dict[str, Any]]]) -> str:
    """What happened to a batch of face attempts: outcomes, which liveness checks fired, and the light evidence."""
    outcomes = Counter(outcome for outcome, _ in attempts)
    lives = [scores["liveness"] for _, scores in attempts if scores.get("liveness")]
    evidence = Counter(live["evidence"] for live in lives)
    poses = [live["pose"] for live in lives if live["pose"] is not None]
    problems = Counter(problem for pose in poses for problem in pose["problems"])
    signs = Counter(sign for live in lives for sign in live["injection"])
    shown = sum(1 for live in lives if live["light"] is not None and live["light"].get("shown", True))
    lights = [live["light"] for live in lives if live["light"] is not None and live["light"]["usable"]]
    skin = [light["r_skin"] for light in lights if light["r_skin"] is not None]
    passed = sum(pose["passed"] for pose in poses)
    reach: dict[str, list[float]] = {}
    for pose in poses:
        for name, value in pose.get("reached", []):
            if value is not None:
                reach.setdefault(name, []).append(value)
    reaches = [f"{name} {statistics.median(v):+.2f} / {min(v):+.2f}" for name, v in sorted(reach.items())]
    measured = Counter(pose.get("measured_by", "five_points") for pose in poses)
    real = [live["presentation"] for live in lives if live.get("presentation") is not None]
    patterns = [live["screen_pattern"] for live in lives if live.get("screen_pattern") is not None]
    gradual = [moved for pose in poses for _, moved in pose.get("gradual", [])]
    lines = [
        f"{len(attempts)} face attempts: " + ", ".join(f"{name} {count}" for name, count in outcomes.most_common()),
        "evidence: " + (", ".join(f"{name} {count}" for name, count in evidence.most_common()) or "none"),
        f"pose challenge passed: {passed} of {len(poses)}"
        + (
            f" ({passed / len(poses):.0%}); false-reject rate if all were genuine: {1 - passed / len(poses):.0%}"
            if poses
            else ""
        ),
        "pose problems: " + (", ".join(f"{name} {count}" for name, count in problems.most_common()) or "none"),
        "pose measured by: " + (", ".join(f"{name} {count}" for name, count in measured.most_common()) or "none"),
        "pose reach from frontal, median / lowest: " + (", ".join(reaches) or "none"),
        "injection signs: " + (", ".join(f"{name} {count}" for name, count in signs.most_common()) or "none"),
        "presentation: "
        + (f"real-face chance median {statistics.median(real):.2f}, lowest {min(real):.2f}" if real else "not measured")
        + (f"; screen pattern median {statistics.median(patterns):.2f}" if patterns else "")
        + f"; poses caught mid-turn {sum(gradual)} of {len(gradual)}",
        f"light shown: {shown} of {len(lives)}; usable: {len(lights)} of {len(lives)}"
        + (
            f"; skin correlation median {statistics.median(skin):+.2f}, range {min(skin):+.2f} to {max(skin):+.2f}"
            if skin
            else ""
        ),
    ]
    return "\n".join(lines)


async def liveness_report(settings: Settings, since: datetime) -> str:
    engine = make_engine(settings.database_url)
    async with make_sessions(engine)() as session:
        rows = (
            await session.execute(
                select(VerificationAttempt.outcome, VerificationAttempt.scores).where(
                    VerificationAttempt.kind == "face", VerificationAttempt.created_at >= since
                )
            )
        ).all()
    await engine.dispose()
    return liveness_summary([(outcome, scores) for outcome, scores in rows])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="dwarpal-api", description="Dwarpal API helpers")
    parser.add_argument("command", choices=["migrate", "seed-dev", "liveness-report"])
    parser.add_argument("--since", type=datetime.fromisoformat, help="liveness-report: attempts from this time on")
    args = parser.parse_args(argv)
    if args.command == "migrate":
        migrate()
        print("database is at the latest migration")
        return 0
    if args.command == "liveness-report":
        since = args.since or datetime.now(UTC) - timedelta(days=1)
        print(asyncio.run(liveness_report(Settings(), since if since.tzinfo else since.replace(tzinfo=UTC))))
        return 0
    project_id, plaintext = asyncio.run(seed_dev(Settings()))
    print(f"project:  {project_id}\ntest key: {plaintext}\n(store the key now; it is shown only once)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
