"""The use cases of a verification: create, start, challenge, attempt, finish — and the result a website reads."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlencode, urlsplit

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from dwarpal_api.adapters.inference import InferenceClient
from dwarpal_api.adapters.signing import KeyRing
from dwarpal_api.adapters.store import FlowStore
from dwarpal_api.adapters.tables import IssuedToken, Project, VerificationAttempt, VerificationSession
from dwarpal_api.domain import ids
from dwarpal_api.domain.decision import Decision, Outcome, decide
from dwarpal_api.domain.keys import generate_client_secret, matches
from dwarpal_api.domain.policy import ModelManifest, UncalibratedPolicyError, UnknownPolicyError, get_policy
from dwarpal_api.domain.sessions import STATUS_AFTER, Status, is_expired, move
from dwarpal_api.errors import ApiError
from dwarpal_api.settings import Settings
from dwarpal_contracts import FaceAnalysis, FaceRequestMeta

FLOW_STATUSES = frozenset({Status.IN_PROGRESS, Status.AWAITING_STEP_UP, Status.COMPLETED})
CHALLENGES_PER_ATTEMPT = 2


@dataclass
class Services:
    settings: Settings
    sessions: async_sessionmaker[AsyncSession]
    store: FlowStore
    inference: InferenceClient
    keyring: KeyRing
    manifest: ModelManifest

    def now(self) -> datetime:
        return datetime.now(UTC)

    def new_id(self) -> uuid.UUID:
        return ids.uuid7(int(self.now().timestamp() * 1000))


def origin_of(url: str) -> str:
    parts = urlsplit(url)
    return f"{parts.scheme}://{parts.netloc}"


def public_id(row: VerificationSession) -> str:
    return ids.encode("vs", row.id)


async def load_session(session: AsyncSession, session_id: uuid.UUID, *, lock: bool = False) -> VerificationSession:
    query = select(VerificationSession).where(VerificationSession.id == session_id)
    row = await session.scalar(query.with_for_update() if lock else query)
    if row is None:
        raise ApiError(404, "session_not_found", "no such verification session")
    return row


def parse_session_id(text: str) -> uuid.UUID:
    try:
        return ids.decode("vs", text)
    except ids.InvalidIdError:
        raise ApiError(404, "session_not_found", "no such verification session") from None


def expire_if_due(row: VerificationSession, now: datetime) -> None:
    if is_expired(Status(row.status), row.expires_at, now):
        row.status = move(Status(row.status), Status.EXPIRED)


async def create_session(
    svc: Services, project: Project, livemode: bool, policy_id: str, return_url: str | None, external_ref: str | None
) -> tuple[VerificationSession, str]:
    try:
        policy = get_policy(policy_id)
        svc.manifest.thresholds_for(policy)
    except UnknownPolicyError:
        raise ApiError(422, "unknown_policy", f"there is no policy called {policy_id!r}") from None
    except UncalibratedPolicyError as error:
        raise ApiError(422, "policy_not_supported", str(error)) from None
    if livemode and not svc.manifest.calibrated:
        raise ApiError(409, "model_not_calibrated", "live sessions need a calibrated age model; use a test key")
    if return_url is not None and origin_of(return_url) not in project.allowed_origins:
        raise ApiError(422, "return_url_not_allowed", "return_url must be on one of the project's allowed origins")
    now, session_id = svc.now(), svc.new_id()
    secret = generate_client_secret(ids.encode("vs", session_id))
    row = VerificationSession(
        id=session_id,
        project_id=project.id,
        livemode=livemode,
        policy_id=policy.id,
        status=Status.CREATED,
        outcome=None,
        client_secret_digest=secret.digest,
        return_url=return_url,
        external_ref=external_ref,
        attempts_count=0,
        model_version=None,
        created_at=now,
        expires_at=now + timedelta(seconds=svc.settings.session_ttl_s),
        completed_at=None,
    )
    async with svc.sessions() as session:
        session.add(row)
        await session.commit()
    return row, secret.plaintext


async def start_flow(svc: Services, session_text: str, client_secret: str) -> dict[str, Any]:
    async with svc.sessions() as session:
        row = await load_session(session, parse_session_id(session_text), lock=True)
        if not matches(client_secret, row.client_secret_digest):
            raise ApiError(401, "invalid_client_secret", "the client secret does not match this session")
        expire_if_due(row, svc.now())
        if row.status == Status.CREATED:
            row.status = move(Status.CREATED, Status.IN_PROGRESS)
        project = await session.get(Project, row.project_id)
        await session.commit()
    if row.status not in FLOW_STATUSES or project is None:
        raise ApiError(409, "session_not_open", f"this session is {row.status}")
    policy = get_policy(row.policy_id)
    token = await svc.store.open_flow(row.id, svc.settings.flow_ttl_s)
    view = {
        "id": public_id(row),
        "status": row.status,
        "outcome": row.outcome,
        "project_name": project.name,
        "min_age": policy.min_age,
        "attempts_remaining": max(policy.max_face_attempts - row.attempts_count, 0),
    }
    return {"flow_token": token, "session": view}


async def issue_challenge(svc: Services, session_id: uuid.UUID) -> dict[str, Any]:
    async with svc.sessions() as session:
        row = await load_session(session, session_id)
    if row.status != Status.IN_PROGRESS:
        raise ApiError(409, "session_not_in_progress", f"this session is {row.status}")
    budget = get_policy(row.policy_id).max_face_attempts * CHALLENGES_PER_ATTEMPT
    settings = svc.settings
    challenge = await svc.store.issue_challenge(row.id, settings.challenge_ttl_s, budget, settings.session_ttl_s)
    if challenge is None:
        raise ApiError(429, "too_many_challenges", "this session has used all of its challenges")
    return challenge


def attempt_scores(analysis: FaceAnalysis | None, decision: Decision) -> dict[str, Any]:
    if analysis is None:
        return {"analysis": "unavailable"}
    problems = sorted({flag for frame in analysis.frames for flag in frame.flags})
    return {
        "model": analysis.model_version,
        "frames": len(analysis.frames),
        "usable_frames": analysis.usable_frames,
        "problems": problems,
        "p_over": decision.p_over,
        "tau": decision.tau_effective,
        "analysis_ms": round(analysis.duration_ms, 1),
    }


async def submit_face_attempt(
    svc: Services, session_id: uuid.UUID, challenge_id: str, meta: FaceRequestMeta, frames: list[bytes]
) -> tuple[Decision, int]:
    async with svc.sessions() as session:
        if (await load_session(session, session_id)).status != Status.IN_PROGRESS:
            raise ApiError(409, "session_not_in_progress", "this session is not accepting attempts")
    if not await svc.store.take_challenge(challenge_id, session_id):
        raise ApiError(409, "challenge_invalid", "the challenge is unknown, expired or already used")
    analysis = await svc.inference.analyze_face(meta, frames)
    async with svc.sessions() as session:
        row = await load_session(session, session_id, lock=True)
        now = svc.now()
        expire_if_due(row, now)
        if row.status != Status.IN_PROGRESS:
            await session.commit()
            raise ApiError(409, "session_not_in_progress", f"this session is {row.status}")
        policy = get_policy(row.policy_id)
        model_ok = analysis is not None and svc.manifest.serves_model(analysis.model_version)
        decision = decide(policy, svc.manifest.thresholds_for(policy), analysis, row.attempts_count, model_ok)
        session.add(
            VerificationAttempt(
                id=svc.new_id(),
                session_id=row.id,
                kind="face",
                outcome=decision.outcome,
                reasons=list(decision.reasons),
                scores=attempt_scores(analysis, decision),
                created_at=now,
            )
        )
        row.attempts_count += 1
        row.status = move(Status(row.status), STATUS_AFTER[decision.outcome])
        if decision.outcome != Outcome.RETRY:
            row.outcome = decision.outcome
        if analysis is not None:
            row.model_version = analysis.model_version
        if row.status == Status.COMPLETED:
            row.completed_at = now
        remaining = policy.max_face_attempts - row.attempts_count
        await session.commit()
    return decision, remaining


async def finish(svc: Services, session_id: uuid.UUID) -> str | None:
    async with svc.sessions() as session:
        row = await load_session(session, session_id)
    if row.status not in (Status.COMPLETED, Status.AWAITING_STEP_UP):
        raise ApiError(409, "session_not_finished", f"this session is {row.status}")
    if row.return_url is None:
        return None
    separator = "&" if urlsplit(row.return_url).query else "?"
    return f"{row.return_url}{separator}{urlencode({'session_id': public_id(row)})}"


def created_view(svc: Services, row: VerificationSession, client_secret: str) -> dict[str, Any]:
    return {
        "id": public_id(row),
        "object": "verification_session",
        "status": row.status,
        "livemode": row.livemode,
        "policy": row.policy_id,
        "client_secret": client_secret,
        "url": f"{svc.settings.verify_url}/v/{public_id(row)}#cs={client_secret}",
        "expires_at": row.expires_at.isoformat(),
    }


async def result_view(svc: Services, session_text: str, project_id: uuid.UUID, livemode: bool) -> dict[str, Any]:
    async with svc.sessions() as session:
        row = await load_session(session, parse_session_id(session_text))
        if row.project_id != project_id or row.livemode != livemode:
            raise ApiError(404, "session_not_found", "no such verification session")
        now = svc.now()
        expire_if_due(row, now)
        token = mint_token(svc, session, row, now) if row.status == Status.COMPLETED else None
        await session.commit()
    return {
        "id": public_id(row),
        "object": "verification_session",
        "status": row.status,
        "outcome": row.outcome,
        "livemode": row.livemode,
        "policy": row.policy_id,
        "min_age": get_policy(row.policy_id).min_age,
        "attempts": row.attempts_count,
        "external_ref": row.external_ref,
        "created_at": row.created_at.isoformat(),
        "expires_at": row.expires_at.isoformat(),
        "completed_at": row.completed_at.isoformat() if row.completed_at else None,
        "age_token": token,
    }


def mint_token(svc: Services, session: AsyncSession, row: VerificationSession, now: datetime) -> str:
    policy = get_policy(row.policy_id)
    jti, audience = svc.new_id(), ids.encode("prj", row.project_id)
    expires = now + timedelta(seconds=policy.token_ttl_s)
    session.add(IssuedToken(jti=jti, session_id=row.id, audience=audience, issued_at=now, expires_at=expires))
    claims = {
        "iss": svc.settings.issuer,
        "aud": audience,
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "exp": int(expires.timestamp()),
        "jti": str(jti),
        "sid": public_id(row),
        "outcome": row.outcome,
        f"age_over_{policy.min_age}": row.outcome == Outcome.PASS,
        "assurance": "basic",
        "methods": ["face_estimation"],
        "policy": row.policy_id,
        "model": row.model_version,
        "livemode": row.livemode,
    }
    return svc.keyring.sign(claims)
