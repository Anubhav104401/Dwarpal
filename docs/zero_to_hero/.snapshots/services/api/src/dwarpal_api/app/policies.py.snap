"""Policies a website can choose: the built-in presets, and its own policies, kept as versions that never change."""

from __future__ import annotations

import re
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from dwarpal_api.adapters.db import tenant
from dwarpal_api.adapters.tables import PolicyVersion, VerificationSession
from dwarpal_api.app import audit
from dwarpal_api.domain.policy import PRESETS, ModelManifest, Policy, UncalibratedPolicyError, get_policy
from dwarpal_api.errors import ApiError

NAME = re.compile(r"^[a-z][a-z0-9_]{2,39}$")


def from_row(row: PolicyVersion) -> Policy:
    return Policy(row.name, row.min_age, row.risk_budget, row.max_face_attempts, row.token_ttl_s, row.version)


async def latest(session: AsyncSession, project_id: uuid.UUID, name: str) -> Policy:
    """The policy a new session gets for `name`: the preset of that name, or the project's newest version of it."""
    if name in PRESETS:
        return get_policy(name)
    query = (
        select(PolicyVersion)
        .where(PolicyVersion.project_id == project_id, PolicyVersion.name == name)
        .order_by(PolicyVersion.version.desc())
        .limit(1)
    )
    row = await session.scalar(query)
    if row is None:
        raise ApiError(422, "unknown_policy", f"there is no policy called {name!r}")
    return from_row(row)


async def pinned(session: AsyncSession, row: VerificationSession) -> Policy:
    """The exact policy version a session was created with, whatever has been added since."""
    if row.policy_version == 0:
        return get_policy(row.policy_id)
    version = await session.scalar(
        select(PolicyVersion).where(
            PolicyVersion.project_id == row.project_id,
            PolicyVersion.name == row.policy_id,
            PolicyVersion.version == row.policy_version,
        )
    )
    if version is None:  # can't happen while versions are never deleted; refuse rather than guess
        raise ApiError(409, "policy_missing", f"the policy {row.policy_id}@{row.policy_version} no longer exists")
    return from_row(version)


def view(policy: Policy) -> dict[str, Any]:
    return {
        "object": "policy",
        "id": policy.label,
        "name": policy.id,
        "version": policy.version,
        "preset": policy.version == 0,
        "min_age": policy.min_age,
        "risk_budget": policy.risk_budget,
        "max_face_attempts": policy.max_face_attempts,
        "token_ttl_s": policy.token_ttl_s,
    }


async def add_version(
    sessions: async_sessionmaker[AsyncSession],
    manifest: ModelManifest,
    project_id: uuid.UUID,
    draft: Policy,
    now: datetime,
    new_id: uuid.UUID,
    org_id: uuid.UUID,
    actor: tuple[str, str],
) -> dict[str, Any]:
    """Add the next version of a project's policy `draft.id`. Its version number is one more than the newest."""
    if not NAME.match(draft.id) or draft.id in PRESETS:
        raise ApiError(422, "invalid_policy_name", "use 3-40 lower-case letters, digits or _, and not a preset's name")
    try:
        manifest.thresholds_for(draft)
    except UncalibratedPolicyError as error:
        raise ApiError(422, "policy_not_supported", str(error)) from None
    try:
        async with tenant(sessions, project_id) as session:
            newest = await session.scalar(
                select(func.max(PolicyVersion.version)).where(
                    PolicyVersion.project_id == project_id, PolicyVersion.name == draft.id
                )
            )
            version = (newest or 0) + 1
            session.add(
                PolicyVersion(
                    id=new_id,
                    project_id=project_id,
                    name=draft.id,
                    version=version,
                    min_age=draft.min_age,
                    risk_budget=draft.risk_budget,
                    max_face_attempts=draft.max_face_attempts,
                    token_ttl_s=draft.token_ttl_s,
                    created_at=now,
                )
            )
            facts = {"min_age": draft.min_age, "risk_budget": draft.risk_budget, "attempts": draft.max_face_attempts}
            await audit.record(session, org_id, actor, "policy.version_added", f"{draft.id}@{version}", facts, now)
            await session.commit()
    except IntegrityError:  # another request added the same version at the same moment
        raise ApiError(
            409, "policy_version_conflict", "another version was added at the same time; try again"
        ) from None
    return view(Policy(draft.id, draft.min_age, draft.risk_budget, draft.max_face_attempts, draft.token_ttl_s, version))


async def list_all(sessions: async_sessionmaker[AsyncSession], project_id: uuid.UUID) -> dict[str, Any]:
    """Every preset, then every version of the project's own policies, oldest version first."""
    async with tenant(sessions, project_id) as session:
        rows = list(
            await session.scalars(
                select(PolicyVersion)
                .where(PolicyVersion.project_id == project_id)
                .order_by(PolicyVersion.name, PolicyVersion.version)
            )
        )
    presets = [view(PRESETS[name]) for name in sorted(PRESETS)]
    return {"object": "list", "data": presets + [view(from_row(row)) for row in rows]}
