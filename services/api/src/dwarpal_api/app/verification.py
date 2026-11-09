"""The use cases of a verification: create, start, challenge, attempt, finish — and the result a website reads."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlencode, urlsplit

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from dwarpal_api.adapters.db import session_tenant, tenant
from dwarpal_api.adapters.inference import InferenceClient
from dwarpal_api.adapters.signing import KeyRing, MasterKey
from dwarpal_api.adapters.store import FlowStore
from dwarpal_api.adapters.tables import (
    DocumentStageStat,
    FaceStageStat,
    IssuedToken,
    Project,
    SessionStat,
    VerificationAttempt,
    VerificationSession,
)
from dwarpal_api.app import webhooks
from dwarpal_api.app.policies import latest, pinned
from dwarpal_api.domain import ids, origins
from dwarpal_api.domain.challenges import new_challenge
from dwarpal_api.domain.decision import Decision, Outcome, decide
from dwarpal_api.domain.keys import generate_client_secret, matches
from dwarpal_api.domain.policy import ModelManifest, Policy, UncalibratedPolicyError
from dwarpal_api.domain.sessions import STATUS_AFTER, Status, is_expired, move
from dwarpal_api.domain.stepup import MAX_DOCUMENT_ATTEMPTS, DocumentDecision, decide_document
from dwarpal_api.domain.timing import band_of
from dwarpal_api.errors import ApiError
from dwarpal_api.settings import Settings
from dwarpal_contracts import DocumentAnalysis, FaceAnalysis, FaceRequestMeta

FLOW_STATUSES = frozenset({Status.IN_PROGRESS, Status.AWAITING_STEP_UP, Status.COMPLETED})
# The sessions whose verify page may still be shown — inside a website's frame too (`frame_ancestor`).
SHOWN_STATUSES = FLOW_STATUSES | {Status.CREATED}
MAX_PAGE = 100
CHALLENGES_PER_ATTEMPT = 2
HOUR_S = 3600
# Where a challenge may be issued: a face attempt's, or the selfie of a step-up's document check.
CHALLENGE_STATUSES = frozenset({Status.IN_PROGRESS, Status.AWAITING_STEP_UP})


@dataclass
class Services:
    settings: Settings
    sessions: async_sessionmaker[AsyncSession]
    store: FlowStore
    inference: InferenceClient
    keyring: KeyRing
    manifest: ModelManifest
    # Seals idempotent replies kept in Valkey (app/idempotency.py); derived from the master key.
    idempotency_secret: bytes = b""
    # Seals webhook endpoints' signing secrets (app/webhooks.py).
    master: MasterKey | None = None

    def now(self) -> datetime:
        return datetime.now(UTC)

    def new_id(self) -> uuid.UUID:
        return ids.uuid7(int(self.now().timestamp() * 1000))


def origin_of(url: str) -> str:
    """The origin of a return address, written the standard way (domain/origins.py), so it compares with a project's
    allowed origins as plain text; empty — matching none of them — for an address without a proper origin."""
    try:
        return origins.origin_of(url)
    except origins.InvalidOriginError:
        return ""


def public_id(row: VerificationSession) -> str:
    return ids.encode("vs", row.id)


def policy_label(row: VerificationSession) -> str:
    return row.policy_id if row.policy_version == 0 else f"{row.policy_id}@{row.policy_version}"


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


async def expire_if_due(svc: Services, session: AsyncSession, row: VerificationSession, now: datetime) -> None:
    if is_expired(Status(row.status), row.expires_at, now):
        row.status = move(Status(row.status), Status.EXPIRED)
        await announce(svc, session, row, now)


async def announce(svc: Services, session: AsyncSession, row: VerificationSession, now: datetime) -> None:
    await record_final(session, svc.new_id, row, now)


async def record_final(
    session: AsyncSession, new_id: Callable[[], uuid.UUID], row: VerificationSession, now: datetime
) -> None:
    """For a session that has just completed or expired, in the transaction that saves the change: write its event
    (the website's webhook can never miss an outcome, nor hear of one that wasn't saved), and count it in the day's
    statistics, which outlive the session itself."""
    expired = row.status == Status.EXPIRED
    event_type = "verification_session.expired" if expired else "verification_session.completed"
    await webhooks.emit(session, new_id, now, row.project_id, row.livemode, event_type, summary_view(row, now))
    key = {
        "project_id": row.project_id,
        "livemode": row.livemode,
        "day": now.date(),
        "policy": policy_label(row),
        "outcome": "expired" if expired else (row.outcome or "unknown"),
    }
    count = insert(SessionStat).values(**key, sessions=1)
    count = count.on_conflict_do_update(index_elements=list(key), set_={"sessions": SessionStat.sessions + 1})
    await session.execute(count)


async def record_face_stage(session: AsyncSession, row: VerificationSession, outcome: Outcome, now: datetime) -> None:
    """Count a face check that has reached a decision, in the day's counts for the dashboard: its outcome, and the band
    of time from opening the verify page to the decision. (A session from before `started_at` was kept counts from its
    creation.)"""
    began = row.started_at or row.created_at
    key = {
        "project_id": row.project_id,
        "livemode": row.livemode,
        "day": now.date(),
        "outcome": outcome.value,
        "from_s": band_of((now - began).total_seconds()),
    }
    count = insert(FaceStageStat).values(**key, sessions=1)
    count = count.on_conflict_do_update(index_elements=list(key), set_={"sessions": FaceStageStat.sessions + 1})
    await session.execute(count)


async def record_document_stage(session: AsyncSession, row: VerificationSession, step: str, now: datetime) -> None:
    """Count a session reaching the ID-document check ("opened"), or that check ending ("pass", "fail", "reject", or
    "age_pass"), in the day's counts for the dashboard: together, the design's step-up conversion."""
    key = {"project_id": row.project_id, "livemode": row.livemode, "day": now.date(), "step": step}
    count = insert(DocumentStageStat).values(**key, sessions=1)
    count = count.on_conflict_do_update(index_elements=list(key), set_={"sessions": DocumentStageStat.sessions + 1})
    await session.execute(count)


def document_only(svc: Services, livemode: bool) -> bool:
    """Decision D24: until an age model is certified for live use, a live check is decided by an ID document alone. The
    age estimate is never used for it, so the face check is skipped: the document check's own selfie, with the same
    challenge, still proves a live person is there and that the document is theirs."""
    return livemode and not svc.manifest.calibrated


def document_open(svc: Services, row: VerificationSession) -> bool:
    """Whether the document check may be used now: after a face check sent the person there, or from the start in a
    document-only session."""
    return row.status == Status.AWAITING_STEP_UP or (
        row.status == Status.IN_PROGRESS and document_only(svc, row.livemode)
    )


async def create_session(
    svc: Services, project: Project, livemode: bool, policy_id: str, return_url: str | None, external_ref: str | None
) -> tuple[VerificationSession, str]:
    async with tenant(svc.sessions, project.id) as session:
        # A preset, or the newest version of the project's own policy of that name, pinned for the session's life.
        policy = await latest(session, project.id, policy_id)
        if not document_only(svc, livemode):
            # The age model will decide: it must have thresholds for this policy's age and budget.
            try:
                svc.manifest.thresholds_for(policy)
            except UncalibratedPolicyError as error:
                raise ApiError(422, "policy_not_supported", str(error)) from None
        if return_url is not None and origin_of(return_url) not in project.allowed_origins:
            raise ApiError(422, "return_url_not_allowed", "return_url must be on one of the project's allowed origins")
        now, session_id = svc.now(), svc.new_id()
        secret = generate_client_secret(ids.encode("vs", session_id))
        row = VerificationSession(
            id=session_id,
            project_id=project.id,
            livemode=livemode,
            policy_id=policy.id,
            policy_version=policy.version,
            status=Status.CREATED,
            outcome=None,
            client_secret_digest=secret.digest,
            return_url=return_url,
            external_ref=external_ref,
            attempts_count=0,
            model_version=None,
            created_at=now,
            started_at=None,
            expires_at=now + timedelta(seconds=svc.settings.session_ttl_s),
            completed_at=None,
        )
        session.add(row)
        await session.commit()
    return row, secret.plaintext


async def start_flow(svc: Services, session_text: str, client_secret: str) -> dict[str, Any]:
    session_id = parse_session_id(session_text)
    async with session_tenant(svc.sessions, session_id) as session:
        row = await load_session(session, session_id, lock=True)
        if not matches(client_secret, row.client_secret_digest):
            raise ApiError(401, "invalid_client_secret", "the client secret does not match this session")
        await expire_if_due(svc, session, row, svc.now())
        if row.status == Status.CREATED:
            row.status = move(Status.CREATED, Status.IN_PROGRESS)
            row.started_at = svc.now()
            if document_only(svc, row.livemode):  # D24: this check starts at the ID document
                await record_document_stage(session, row, "opened", row.started_at)
        project = await session.get(Project, row.project_id)
        policy = await pinned(session, row)
        await session.commit()
    if row.status not in FLOW_STATUSES or project is None:
        raise ApiError(409, "session_not_open", f"this session is {row.status}")
    token = await svc.store.open_flow(row.id, svc.settings.flow_ttl_s)
    view = {
        "id": public_id(row),
        "status": row.status,
        "outcome": row.outcome,
        "project_name": project.name,
        "min_age": policy.min_age,
        "attempts_remaining": max(policy.max_face_attempts - row.attempts_count, 0),
        "return_origin": origin_of(row.return_url) if row.return_url else None,
        # For the Age Pass (Phase 9): whether the website accepts one, and the mode a pass must match.
        "accept_age_pass": policy.accept_age_pass,
        "livemode": row.livemode,
        # D24: this check is decided by an ID document (or an Age Pass), never by the face check.
        "document_only": document_only(svc, row.livemode),
    }
    return {"flow_token": token, "session": view}


async def frame_ancestor(svc: Services, session_text: str) -> str | None:
    """The one website allowed to show this session's verify page inside a frame (decision D16): the origin of its
    return address, which the website registered with its secret key and which must be one of the project's allowed
    origins. None — no website at all — for a session without a return address, an unknown one, or one that is over."""
    try:
        session_id = parse_session_id(session_text)
    except ApiError:
        return None
    async with session_tenant(svc.sessions, session_id) as session:
        row = await session.get(VerificationSession, session_id)
    if row is None or row.return_url is None or row.status not in SHOWN_STATUSES:
        return None
    if is_expired(Status(row.status), row.expires_at, svc.now()):
        return None
    return origin_of(row.return_url)


async def issue_challenge(
    svc: Services, session_id: uuid.UUID, device: str | None = None, address: str | None = None
) -> dict[str, Any]:
    async with session_tenant(svc.sessions, session_id) as session:
        row = await load_session(session, session_id)
        policy = await pinned(session, row)
    if row.status not in CHALLENGE_STATUSES:
        raise ApiError(409, "session_not_in_progress", f"this session is {row.status}")
    await spend_device_budgets(svc, row.project_id, device, address)
    budget = (policy.max_face_attempts + MAX_DOCUMENT_ATTEMPTS) * CHALLENGES_PER_ATTEMPT
    settings = svc.settings
    challenge = await svc.store.issue_challenge(
        row.id, new_challenge(), settings.challenge_ttl_s, budget, settings.session_ttl_s
    )
    if challenge is None:
        raise ApiError(429, "too_many_challenges", "this session has used all of its challenges")
    return challenge


async def spend_device_budgets(svc: Services, project_id: uuid.UUID, device: str | None, address: str | None) -> None:
    """Stop endless trial and error across sessions: each device, and each network address, may take only so many
    challenges an hour. Starting a new session doesn't reset these, unlike the per-session budget."""
    settings = svc.settings
    budgets = [
        (f"device:{project_id}:{device}", settings.device_challenges_per_hour) if device else None,
        (f"address:{project_id}:{address}", settings.address_challenges_per_hour) if address else None,
    ]
    for key, limit in filter(None, budgets):
        if not await svc.store.spend_budget(key, limit, HOUR_S):
            raise ApiError(429, "too_many_attempts", "too many age checks from this device; try again later")


def attempt_scores(analysis: FaceAnalysis | None, decision: Decision | None = None) -> dict[str, Any]:
    if analysis is None:
        return {"analysis": "unavailable"}
    problems = sorted({flag for frame in analysis.frames for flag in frame.flags})
    return {
        "model": analysis.model_version,
        "frames": len(analysis.frames),
        "usable_frames": analysis.usable_frames,
        "problems": problems,
        "p_over": decision.p_over if decision else None,
        "tau": decision.tau_effective if decision else None,
        "analysis_ms": round(analysis.duration_ms, 1),
        # Which liveness check fired is kept here, for the people who run Dwarpal, and never shown to the user.
        "liveness": analysis.liveness.model_dump() if analysis.liveness else None,
    }


async def submit_face_attempt(
    svc: Services, session_id: uuid.UUID, challenge_id: str, meta: FaceRequestMeta, frames: list[bytes]
) -> tuple[Decision, int]:
    async with session_tenant(svc.sessions, session_id) as session:
        before = await load_session(session, session_id)
    if before.status != Status.IN_PROGRESS:
        raise ApiError(409, "session_not_in_progress", "this session is not accepting attempts")
    if document_only(svc, before.livemode):
        raise ApiError(409, "document_required", "this check is decided by an ID document: use the document check")
    challenge = await svc.store.take_challenge(challenge_id, session_id)
    if challenge is None:
        raise ApiError(409, "challenge_invalid", "the challenge is unknown, expired or already used")
    # The frames are judged against what the server asked for, never against what the browser says it was asked.
    analysis = await svc.inference.analyze_face(meta.model_copy(update={"challenge": challenge}), frames)
    async with session_tenant(svc.sessions, session_id) as session:
        row = await load_session(session, session_id, lock=True)
        now = svc.now()
        await expire_if_due(svc, session, row, now)
        if row.status != Status.IN_PROGRESS:
            await session.commit()
            raise ApiError(409, "session_not_in_progress", f"this session is {row.status}")
        policy = await pinned(session, row)
        model_ok = analysis is not None and svc.manifest.serves_model(analysis.model_version)
        failures = await session.scalar(
            select(func.count())
            .select_from(VerificationAttempt)
            .where(
                VerificationAttempt.session_id == row.id,
                VerificationAttempt.reasons.contains(["liveness_check_failed"]),
            )
        )
        decision = decide(
            policy,
            svc.manifest.thresholds_for(policy),
            analysis,
            row.attempts_count,
            model_ok,
            liveness_failures=failures or 0,
            livemode=row.livemode,
        )
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
        if decision.outcome != Outcome.RETRY:
            await record_face_stage(session, row, decision.outcome, now)
        if decision.outcome == Outcome.STEP_UP:  # sent on to the ID-document check
            await record_document_stage(session, row, "opened", now)
        if row.status == Status.COMPLETED:
            row.completed_at = now
            await announce(svc, session, row, now)
        remaining = policy.max_face_attempts - row.attempts_count
        await session.commit()
    return decision, remaining


def document_scores(analysis: DocumentAnalysis | None, decision: DocumentDecision) -> dict[str, Any]:
    """What is kept of a document check: its results, and of the document only its kind, issuer, the year and month of
    birth and the expiry — never a name, a document number or a picture (§9.1)."""
    if analysis is None:
        return {"analysis": "unavailable"}
    document = decision.document
    return {
        "zone_problem": analysis.zone_problem,
        "document": None
        if document is None
        else {
            "format": document.format,
            "type": document.document_type,
            "issuer": document.issuer,
            "birth_year_month": f"{document.birth.year:04d}-{document.birth.month:02d}",
            "expiry": document.expiry.isoformat(),
            "repaired": list(document.repaired),
        },
        "document_faces": analysis.document_faces,
        "similarity": None if analysis.similarity is None else round(analysis.similarity, 3),
        "selfie": attempt_scores(analysis.face),
        "analysis_ms": round(analysis.duration_ms, 1),
    }


async def submit_document_attempt(
    svc: Services,
    session_id: uuid.UUID,
    challenge_id: str,
    meta: FaceRequestMeta,
    frames: list[bytes],
    document: bytes,
) -> tuple[DocumentDecision, int]:
    """The step-up with an ID document (Phase 6): open to a session the face check sent there, and to a document-only
    session from the start (D24)."""
    async with session_tenant(svc.sessions, session_id) as session:
        if not document_open(svc, await load_session(session, session_id)):
            raise ApiError(409, "session_not_awaiting_step_up", "this session is not waiting for a step-up")
    challenge = await svc.store.take_challenge(challenge_id, session_id)
    if challenge is None:
        raise ApiError(409, "challenge_invalid", "the challenge is unknown, expired or already used")
    meta = meta.model_copy(update={"challenge": challenge})
    analysis = await svc.inference.analyze_document(meta, frames, document)
    async with session_tenant(svc.sessions, session_id) as session:
        row = await load_session(session, session_id, lock=True)
        now = svc.now()
        await expire_if_due(svc, session, row, now)
        if not document_open(svc, row):
            await session.commit()
            raise ApiError(409, "session_not_awaiting_step_up", f"this session is {row.status}")
        policy = await pinned(session, row)
        earlier = list(
            await session.scalars(
                select(VerificationAttempt.reasons).where(
                    VerificationAttempt.session_id == row.id, VerificationAttempt.kind == "document"
                )
            )
        )
        failures = sum(1 for reasons in earlier if "liveness_check_failed" in reasons)
        decision = decide_document(policy, analysis, len(earlier), now.date(), failures, row.livemode)
        session.add(
            VerificationAttempt(
                id=svc.new_id(),
                session_id=row.id,
                kind="document",
                outcome=decision.outcome,
                reasons=list(decision.reasons),
                scores=document_scores(analysis, decision),
                created_at=now,
            )
        )
        if decision.outcome != Outcome.RETRY:
            row.status = move(Status(row.status), Status.COMPLETED)
            row.outcome = decision.outcome
            row.completed_at = now
            await record_document_stage(session, row, decision.outcome.value, now)
            await announce(svc, session, row, now)
        remaining = MAX_DOCUMENT_ATTEMPTS - len(earlier) - 1
        await session.commit()
    return decision, remaining


async def methods_of(session: AsyncSession, row: VerificationSession) -> list[str]:
    """How a completed session was decided, for its token: by the face alone, by a document check after it, or by an
    Age Pass (Phase 9)."""
    decided_by_pass = await session.scalar(
        select(func.count())
        .select_from(VerificationAttempt)
        .where(VerificationAttempt.session_id == row.id, VerificationAttempt.kind == "age_pass")
    )
    if decided_by_pass:
        return ["age_pass"]
    decided_by_document = await session.scalar(
        select(func.count())
        .select_from(VerificationAttempt)
        .where(
            VerificationAttempt.session_id == row.id,
            VerificationAttempt.kind == "document",
            VerificationAttempt.outcome != Outcome.RETRY,
        )
    )
    if decided_by_document:
        # A document-only session (D24) never had its age estimated.
        faced = await session.scalar(
            select(func.count())
            .select_from(VerificationAttempt)
            .where(VerificationAttempt.session_id == row.id, VerificationAttempt.kind == "face")
        )
        return ["face_estimation", "document_mrz", "face_match"] if faced else ["document_mrz", "face_match"]
    return ["face_estimation"]


async def finish(svc: Services, session_id: uuid.UUID) -> str | None:
    async with session_tenant(svc.sessions, session_id) as session:
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
        "policy": policy_label(row),
        "client_secret": client_secret,
        "url": f"{svc.settings.verify_url}/v/{public_id(row)}#cs={client_secret}",
        "expires_at": row.expires_at.isoformat(),
    }


async def result_view(svc: Services, session_text: str, project_id: uuid.UUID, livemode: bool) -> dict[str, Any]:
    async with tenant(svc.sessions, project_id) as session:
        row = await load_session(session, parse_session_id(session_text))
        if row.project_id != project_id or row.livemode != livemode:
            raise ApiError(404, "session_not_found", "no such verification session")
        now = svc.now()
        await expire_if_due(svc, session, row, now)
        policy = await pinned(session, row)
        token = None
        if row.status == Status.COMPLETED:
            token = mint_token(svc, session, row, policy, now, await methods_of(session, row))
        await session.commit()
    return {**summary_view(row, now), "min_age": policy.min_age, "age_token": token}


def summary_view(row: VerificationSession, now: datetime) -> dict[str, Any]:
    """What a website may see of a session without a token being made: no age token, ever."""
    expired = row.status != Status.EXPIRED and is_expired(Status(row.status), row.expires_at, now)
    return {
        "id": public_id(row),
        "object": "verification_session",
        "status": Status.EXPIRED if expired else row.status,
        "outcome": row.outcome,
        "livemode": row.livemode,
        "policy": policy_label(row),
        "attempts": row.attempts_count,
        "external_ref": row.external_ref,
        "created_at": row.created_at.isoformat(),
        "expires_at": row.expires_at.isoformat(),
        "completed_at": row.completed_at.isoformat() if row.completed_at else None,
    }


@dataclass(frozen=True)
class SessionFilter:
    """Which sessions to list: those with this outcome, and with this reference of the website's own; None means any.
    (No status: "expired" is worked out when a session is read, so a stored status would mislead a filter.)"""

    outcome: Outcome | None = None
    external_ref: str | None = None


async def list_sessions(
    svc: Services,
    project_id: uuid.UUID,
    livemode: bool,
    limit: int,
    starting_after: str | None,
    only: SessionFilter = SessionFilter(),  # noqa: B008 - frozen, so one shared default is safe
) -> dict[str, Any]:
    """One page of a project's sessions, newest first. The cursor is the last session of the previous page: UUIDv7s
    sort by creation time, so "older than the cursor" is a plain comparison, which stays right as sessions are added.
    """
    query = select(VerificationSession).where(
        VerificationSession.project_id == project_id, VerificationSession.livemode == livemode
    )
    if starting_after is not None:
        query = query.where(VerificationSession.id < parse_session_id(starting_after))
    if only.outcome is not None:
        query = query.where(VerificationSession.outcome == only.outcome)
    if only.external_ref is not None:
        query = query.where(VerificationSession.external_ref == only.external_ref)
    query = query.order_by(VerificationSession.id.desc()).limit(min(limit, MAX_PAGE) + 1)
    async with tenant(svc.sessions, project_id) as session:
        rows = list(await session.scalars(query))
    page, now = rows[:limit], svc.now()
    has_more = len(rows) > limit
    return {
        "object": "list",
        "data": [summary_view(row, now) for row in page],
        "has_more": has_more,
        "next_cursor": public_id(page[-1]) if has_more else None,
    }


def mint_token(
    svc: Services,
    session: AsyncSession,
    row: VerificationSession,
    policy: Policy,
    now: datetime,
    methods: list[str] | None = None,
) -> str:
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
        "methods": methods or ["face_estimation"],
        "policy": policy_label(row),
        "model": row.model_version,
        "livemode": row.livemode,
    }
    return svc.keyring.sign(claims)


async def introspect(svc: Services, project_id: uuid.UUID, token: str) -> dict[str, Any]:
    """Check an age token for a website that would rather ask than verify signatures itself (RFC 7662's idea). A token
    is answered as active once: the second time, or if it is forged, expired, or another project's, `active` is false,
    with no reason given, so the answer teaches a forger nothing."""
    now, inactive = svc.now(), {"active": False}
    claims = svc.keyring.verify(token)
    if claims is None or claims.get("iss") != svc.settings.issuer or claims.get("aud") != ids.encode("prj", project_id):
        return inactive
    if not isinstance(claims.get("exp"), int) or claims["exp"] <= now.timestamp():
        return inactive
    try:
        jti = uuid.UUID(str(claims.get("jti")))
    except ValueError:
        return inactive
    async with tenant(svc.sessions, project_id) as session:
        issued = await session.get(IssuedToken, jti, with_for_update=True)
        if issued is None or issued.introspected_at is not None:
            return inactive
        issued.introspected_at = now
        await session.commit()
    return {"active": True, **claims}
