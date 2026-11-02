"""Command-line helpers for the API: apply database migrations, create a demo project with a test key, and summarise
recent liveness results.

uv run --package dwarpal-api python -m dwarpal_api.cli migrate
uv run --package dwarpal-api python -m dwarpal_api.cli seed-dev
uv run --package dwarpal-api python -m dwarpal_api.cli liveness-report --since 2026-10-17T12:00
uv run --package dwarpal-api python -m dwarpal_api.cli rotate-key --lookup <key id> [--grace-hours 24]
uv run --package dwarpal-api python -m dwarpal_api.cli revoke-key --lookup <key id>
uv run --package dwarpal-api python -m dwarpal_api.cli deliver-webhooks [--once]
uv run --package dwarpal-api python -m dwarpal_api.cli maintain
uv run --package dwarpal-api python -m dwarpal_api.cli verify-audit
uv run --package dwarpal-api python -m dwarpal_api.cli openapi
"""

from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import sys
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx
from alembic import command
from alembic.config import Config
from sqlalchemy import select

from dwarpal_api.adapters.db import make_engine, make_sessions
from dwarpal_api.adapters.signing import MasterKey
from dwarpal_api.adapters.tables import ApiKey, Organization, Project, VerificationAttempt
from dwarpal_api.app import audit, maintenance
from dwarpal_api.app.delivery import Deliverer
from dwarpal_api.domain import ids
from dwarpal_api.domain.keys import SCOPES, generate_api_key
from dwarpal_api.settings import Settings

MIGRATIONS = Path(__file__).resolve().parent / "migrations"
# The published API document: written by `openapi`, and checked against the code by the tests.
API_DOCUMENT = Path(__file__).resolve().parents[4] / "docs" / "api" / "openapi.json"
OPERATOR = ("operator", "cli")  # how the audit log names a change made with these tools
DEMO_ORIGINS = ["http://localhost:3000", "http://localhost:3100"]


def migration_config(database_url: str | None = None) -> Config:
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS))
    if database_url:
        config.set_main_option("sqlalchemy.url", database_url)
    return config


def migrate(database_url: str | None = None) -> None:
    command.upgrade(migration_config(database_url), "head")


async def seed_dev(
    settings: Settings, origins: list[str] | None = None, livemode: bool = False, scopes: list[str] | None = None
) -> tuple[str, str]:
    now = datetime.now(UTC)
    millis = int(now.timestamp() * 1000)
    engine = make_engine(settings.database_url)
    key = generate_api_key(livemode=livemode)
    org_id = ids.uuid7(millis)
    org = Organization(id=org_id, name="Amber Cellars Ltd (demo)", slug=f"demo-{org_id.hex}", created_at=now)
    project = Project(
        id=ids.uuid7(millis),
        org_id=org.id,
        name="Amber Cellars (demo)",
        allowed_origins=origins or DEMO_ORIGINS,
        created_at=now,
    )
    api_key = ApiKey(
        id=ids.uuid7(millis),
        project_id=project.id,
        livemode=livemode,
        lookup=key.lookup,
        secret_digest=key.digest,
        name="demo shop",
        scopes=scopes if scopes is not None else sorted(SCOPES),
        created_at=now,
        expires_at=None,
        revoked_at=None,
    )
    async with make_sessions(engine)() as session:
        session.add(org)
        await session.flush()
        session.add(project)
        await session.flush()
        session.add(api_key)
        facts = {"scopes": api_key.scopes, "livemode": livemode}
        await audit.record(session, org.id, OPERATOR, "api_key.created", key.lookup, facts, now)
        await session.commit()
    await engine.dispose()
    return ids.encode("prj", project.id), key.plaintext


async def rotate_key(settings: Settings, lookup: str, grace: timedelta) -> str:
    """Make a replacement for a key, with the same project, mode, name and scopes; the old key keeps working for
    `grace`, so a website can switch over without a moment in which neither key works. Returns the new key."""
    now = datetime.now(UTC)
    engine = make_engine(settings.database_url)
    try:
        async with make_sessions(engine)() as session:
            old = await session.scalar(select(ApiKey).where(ApiKey.lookup == lookup).with_for_update())
            if old is None or old.revoked_at is not None or (old.expires_at is not None and old.expires_at <= now):
                raise SystemExit(f"no working key with the id {lookup!r}")
            key = generate_api_key(livemode=old.livemode)
            session.add(
                ApiKey(
                    id=ids.uuid7(int(now.timestamp() * 1000)),
                    project_id=old.project_id,
                    livemode=old.livemode,
                    lookup=key.lookup,
                    secret_digest=key.digest,
                    name=old.name,
                    scopes=list(old.scopes),
                    created_at=now,
                    expires_at=None,
                    revoked_at=None,
                )
            )
            ends = now + grace
            old.expires_at = ends if old.expires_at is None else min(old.expires_at, ends)
            project = await session.get(Project, old.project_id)
            if project is not None:
                facts = {"replaced_by": key.lookup, "old_key_expires_at": old.expires_at.isoformat()}
                await audit.record(session, project.org_id, OPERATOR, "api_key.rotated", lookup, facts, now)
            await session.commit()
    finally:
        await engine.dispose()
    return key.plaintext


async def revoke_key(settings: Settings, lookup: str) -> bool:
    """Stop a key at once (for a key that leaked). Returns whether there was such a key still working."""
    engine = make_engine(settings.database_url)
    try:
        async with make_sessions(engine)() as session:
            key = await session.scalar(select(ApiKey).where(ApiKey.lookup == lookup, ApiKey.revoked_at.is_(None)))
            if key is not None:
                key.revoked_at = datetime.now(UTC)
                project = await session.get(Project, key.project_id)
                if project is not None:
                    await audit.record(session, project.org_id, OPERATOR, "api_key.revoked", lookup, {}, key.revoked_at)
                await session.commit()
    finally:
        await engine.dispose()
    return key is not None


async def deliver_webhooks(settings: Settings, once: bool = False) -> None:
    """Run the webhook delivery worker (app/delivery.py) as the tables' owner, until stopped (or once)."""
    engine = make_engine(settings.database_url)
    async with httpx.AsyncClient(timeout=settings.webhook_timeout_s) as http:
        deliverer = Deliverer(
            make_sessions(engine),
            MasterKey(settings.master_key.get_secret_value()),
            http,
            lambda: datetime.now(UTC),
            allow_private=settings.webhook_allow_private,
        )
        try:
            await deliverer.run(settings.webhook_poll_s, once=once)
        finally:
            await engine.dispose()


def api_document() -> str:
    """The API's OpenAPI document as stable text: sorted keys, two-space indents, one final newline."""
    from dwarpal_api.main import create_app  # here, not at the top: the app imports this module's neighbours

    return json.dumps(create_app().openapi(), indent=2, sort_keys=True, ensure_ascii=False) + "\n"


async def maintain(settings: Settings, now: datetime | None = None) -> str:
    """The scheduled jobs, once: expire abandoned sessions (announcing each), then purge what is past retention."""
    now = now or datetime.now(UTC)
    engine = make_engine(settings.database_url)
    try:
        sessions = make_sessions(engine)
        expired = await maintenance.sweep_expired(sessions, lambda: ids.uuid7(int(now.timestamp() * 1000)), now)
        purged = await maintenance.purge(sessions, now)
    finally:
        await engine.dispose()
    return f"expired {expired} sessions; purged {purged.sessions} sessions and {purged.events} events"


async def verify_audit(settings: Settings) -> tuple[str, bool]:
    """Check every organisation's audit chain; the text names each broken one and its first bad entry."""
    engine = make_engine(settings.database_url)
    try:
        reports = await maintenance.verify_all_chains(make_sessions(engine))
    finally:
        await engine.dispose()
    broken = {org: r for org, r in reports.items() if not r.intact}
    lines = [f"{len(reports)} organisations, {sum(r.entries for r in reports.values())} audit entries checked"]
    lines += [f"BROKEN: {ids.encode('org', org)} at entry {r.first_broken}" for org, r in broken.items()]
    return "\n".join(lines + ([] if broken else ["every chain is intact"])), not broken


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
    rendered = [live["rendered"] for live in lives if live.get("rendered") is not None]
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
        + (
            f"; rendered chance median {statistics.median(rendered):.2f}, highest {max(rendered):.2f}"
            if rendered
            else ""
        )
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
    commands = [
        "migrate",
        "seed-dev",
        "liveness-report",
        "rotate-key",
        "revoke-key",
        "deliver-webhooks",
        "maintain",
        "verify-audit",
        "openapi",
    ]
    parser.add_argument("command", choices=commands)
    parser.add_argument("--since", type=datetime.fromisoformat, help="liveness-report: attempts from this time on")
    parser.add_argument("--lookup", help="rotate-key, revoke-key: the key's id (the 12 characters after dk_test_)")
    parser.add_argument("--grace-hours", type=float, default=24.0, help="rotate-key: how long the old key still works")
    parser.add_argument("--once", action="store_true", help="deliver-webhooks: send what is due now, then stop")
    args = parser.parse_args(argv)
    if args.command == "migrate":
        migrate()
        print("database is at the latest migration")
        return 0
    if args.command == "liveness-report":
        since = args.since or datetime.now(UTC) - timedelta(days=1)
        print(asyncio.run(liveness_report(Settings(), since if since.tzinfo else since.replace(tzinfo=UTC))))
        return 0
    if args.command == "deliver-webhooks":
        asyncio.run(deliver_webhooks(Settings(), once=args.once))
        return 0
    if args.command == "openapi":
        API_DOCUMENT.parent.mkdir(parents=True, exist_ok=True)
        API_DOCUMENT.write_text(api_document(), encoding="utf-8", newline="\n")
        print(f"wrote {API_DOCUMENT}")
        return 0
    if args.command == "maintain":
        print(asyncio.run(maintain(Settings())))
        return 0
    if args.command == "verify-audit":
        report, intact = asyncio.run(verify_audit(Settings()))
        print(report)
        return 0 if intact else 1
    if args.command in ("rotate-key", "revoke-key") and not args.lookup:
        parser.error(f"{args.command} needs --lookup")
    if args.command == "rotate-key":
        plaintext = asyncio.run(rotate_key(Settings(), args.lookup, timedelta(hours=args.grace_hours)))
        print(f"new key: {plaintext}\n(store it now; it is shown only once. The old key stops in {args.grace_hours} h)")
        return 0
    if args.command == "revoke-key":
        revoked = asyncio.run(revoke_key(Settings(), args.lookup))
        print("revoked" if revoked else f"no working key with the id {args.lookup!r}")
        return 0 if revoked else 1
    project_id, plaintext = asyncio.run(seed_dev(Settings()))
    print(f"project:  {project_id}\ntest key: {plaintext}\nkey id:   {plaintext[8:20]}")
    print("(store the key now; it is shown only once)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
