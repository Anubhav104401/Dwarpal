"""The Age Pass's use cases (Phase 9, D21): give a batch of passes to a person who has just passed, and accept one
instead of a face check — both only where the website's policy says so.

The rules are in domain/agepass.py. Nothing here records a pass, its key or its salts: a session notes only *when* it
gave out its one batch, and a pass shown later is remembered only as a hash, until it expires, so it can't be used
twice.
"""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from dwarpal_api.adapters.db import session_tenant
from dwarpal_api.adapters.tables import VerificationAttempt
from dwarpal_api.app.policies import pinned
from dwarpal_api.app.verification import announce, load_session, methods_of, public_id, spend_device_budgets
from dwarpal_api.domain import agepass
from dwarpal_api.domain.decision import Outcome
from dwarpal_api.domain.sessions import Status, move
from dwarpal_api.errors import ApiError

if TYPE_CHECKING:
    from dwarpal_api.app.verification import Services

ISSUE_WINDOW = timedelta(minutes=10)  # passes are given out only just after the check that earned them
NONCE_TTL_S = 300


def _refused(error: agepass.AgePassError) -> ApiError:
    return ApiError(422, f"age_pass_{error.code}", str(error))


async def issue(svc: Services, session_id: uuid.UUID, keys: list[dict[str, Any]]) -> dict[str, Any]:
    """A batch of passes, one bound to each public key the browser made, for a session that has just passed under a
    policy that accepts passes. One batch per session, and never from a session that was itself decided by a pass:
    a pass can't renew itself."""
    if not 1 <= len(keys) <= agepass.BATCH:
        raise ApiError(422, "invalid_request", f"send between 1 and {agepass.BATCH} public keys")
    try:
        holders = [agepass.holder_key(key) for key in keys]
    except agepass.AgePassError as error:
        raise _refused(error) from None
    if len({(key["x"], key["y"]) for key in holders}) != len(holders):
        raise ApiError(422, "age_pass_invalid_holder_key", "each pass needs its own key")
    now = svc.now()
    async with session_tenant(svc.sessions, session_id) as session:
        row = await load_session(session, session_id, lock=True)
        policy = await pinned(session, row)
        if not policy.accept_age_pass:
            raise ApiError(409, "age_pass_not_accepted", "this website's policy doesn't use Age Passes")
        if row.status != Status.COMPLETED or row.outcome != Outcome.PASS:
            raise ApiError(409, "age_pass_not_earned", "Age Passes are given only after a passed check")
        if row.age_pass_issued_at is not None:
            raise ApiError(409, "age_pass_already_issued", "this check has already given out its passes")
        if "age_pass" in await methods_of(session, row):
            raise ApiError(409, "age_pass_not_earned", "a check decided by an Age Pass can't give out new ones")
        if row.completed_at is None or now - row.completed_at > ISSUE_WINDOW:
            raise ApiError(409, "age_pass_too_late", "passes are given out only just after the check")
        passes = []
        for holder in holders:
            made = agepass.new_pass(svc.settings.issuer, policy.min_age, row.livemode, holder, now.date())
            passes.append(agepass.joined(svc.keyring.sign(made.claims, typ=agepass.TYP), made.disclosures))
        row.age_pass_issued_at = now
        await session.commit()
    expires = datetime.fromtimestamp(made.claims["exp"], now.tzinfo)
    return {"passes": passes, "lines": agepass.lines_for(policy.min_age), "expires_at": expires.isoformat()}


async def nonce(svc: Services, session_id: uuid.UUID, device: str | None, address: str | None) -> dict[str, Any]:
    """A one-time number for the browser's key-binding JWT, so a presentation can't be recorded and played again.
    Asking for one spends from the same hourly budgets as a face challenge."""
    async with session_tenant(svc.sessions, session_id) as session:
        row = await load_session(session, session_id)
        policy = await pinned(session, row)
    if not policy.accept_age_pass:
        raise ApiError(409, "age_pass_not_accepted", "this website's policy doesn't use Age Passes")
    if row.status != Status.IN_PROGRESS:
        raise ApiError(409, "session_not_in_progress", f"this session is {row.status}")
    await spend_device_budgets(svc, row.project_id, device, address)
    value = secrets.token_urlsafe(32)
    await svc.store.put(f"agepass:nonce:{session_id}", value.encode(), NONCE_TTL_S)
    return {"nonce": value, "audience": public_id(row)}


async def present(svc: Services, session_id: uuid.UUID, text: str) -> dict[str, Any]:
    """Accept a pass in place of a face check: Dwarpal's signature, an unexpired pass of the session's mode, a
    disclosed line at or above the policy's age, and the holder's key-binding JWT over this session's nonce. A pass
    passes once; the session completes as it would after a face check, and the website's token says how."""
    try:
        shown = agepass.split(text)
    except agepass.AgePassError as error:
        raise _refused(error) from None
    expected = await svc.store.take(f"agepass:nonce:{session_id}")
    if expected is None:
        raise ApiError(409, "age_pass_nonce_expired", "ask for a new nonce: the last one expired or was used")
    claims = svc.keyring.verify(shown.signed, typ=agepass.TYP)
    if claims is None:
        raise ApiError(422, "age_pass_not_an_age_pass", "this isn't an Age Pass signed by Dwarpal")
    now = svc.now()
    async with session_tenant(svc.sessions, session_id) as session:
        row = await load_session(session, session_id, lock=True)
        policy = await pinned(session, row)
        if not policy.accept_age_pass:
            raise ApiError(409, "age_pass_not_accepted", "this website's policy doesn't use Age Passes")
        if row.status != Status.IN_PROGRESS:
            raise ApiError(409, "session_not_in_progress", f"this session is {row.status}")
        try:
            agepass.check_pass(claims, issuer=svc.settings.issuer, livemode=row.livemode, now=now)
            values = agepass.disclosed(claims, shown.disclosures)
            confirmation = claims.get("cnf")
            holder = agepass.holder_key(confirmation.get("jwk") if isinstance(confirmation, dict) else None)
            agepass.check_key_binding(
                shown.key_binding,
                holder,
                nonce=expected.decode(),
                audience=public_id(row),
                now=now,
                signed_part=shown.signed_part,
            )
        except agepass.AgePassError as error:
            raise _refused(error) from None
        line = agepass.line_proved(values, policy.min_age)
        if line is None:
            raise ApiError(422, "age_pass_line_too_low", f"the pass doesn't show an age of {policy.min_age} or over")
        # Each pass passes once: remember its hash (never the pass) until it expires anyway.
        fingerprint = hashlib.sha256(shown.signed.encode()).hexdigest()
        remaining = max(int(claims["exp"] - now.timestamp()), 1)
        if await svc.store.claim(f"agepass:used:{fingerprint}", b"1", remaining) is not None:
            raise ApiError(409, "age_pass_used", "this pass has been used already")
        session.add(
            VerificationAttempt(
                id=svc.new_id(),
                session_id=row.id,
                kind="age_pass",
                outcome=Outcome.PASS,
                reasons=[],
                scores={"line": line},
                created_at=now,
            )
        )
        row.status = move(Status.IN_PROGRESS, Status.COMPLETED)
        row.outcome = Outcome.PASS
        row.completed_at = now
        await announce(svc, session, row, now)
        await session.commit()
    return {"outcome": Outcome.PASS}
