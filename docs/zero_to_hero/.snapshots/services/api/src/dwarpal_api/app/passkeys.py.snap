"""Passkeys for the console (Phase 9): register one, list and remove them, and sign in with one instead of a password.

The checks themselves are in domain/webauthn.py. This module keeps each challenge in Valkey for a few minutes, to be
taken exactly once; stores and finds passkeys; and opens a console session on success. A passkey asks the device to
verify the person (a PIN, fingerprint or face), so signing in with one needs no one-time code as well.
"""

from __future__ import annotations

import json
import secrets
from typing import TYPE_CHECKING, Any
from urllib.parse import urlsplit

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from dwarpal_api.adapters.db import FIND_PASSKEY, tenant
from dwarpal_api.adapters.passwords import verify_password
from dwarpal_api.adapters.tables import Membership, Passkey, User
from dwarpal_api.app import audit, console
from dwarpal_api.domain import ids, totp, webauthn
from dwarpal_api.errors import ApiError

if TYPE_CHECKING:
    from dwarpal_api.app.console import ConsoleSession
    from dwarpal_api.app.verification import Services

CHALLENGE_TTL_S = 300  # five minutes to answer the device's prompt
MAX_PASSKEYS = 10
SIGN_IN_REFUSED = ApiError(401, "passkey_refused", "that passkey can't sign you in here")


def rp_id(svc: Services) -> str:
    """The site's name passkeys are bound to: the setting, or the host of the console's first origin."""
    return svc.settings.passkey_rp_id or urlsplit(svc.settings.console_origins[0]).hostname or "localhost"


def _decoded(text: str) -> bytes:
    try:
        return webauthn.b64url_decode(text)
    except webauthn.WebAuthnError:
        raise ApiError(422, "malformed_passkey_answer", "the browser's passkey answer is malformed") from None


async def _reauthenticate(svc: Services, user: User, password: str, code: str | None, address: str) -> None:
    """Adding a way in needs the password, and a current code if one-time codes are on: a borrowed signed-in browser
    isn't enough. Attempts count against the same limits as signing in."""
    await console._spend_sign_in(svc, user.email, address)
    good = await verify_password(user.password_hash, password)
    if user.totp_secret_sealed is not None:
        secret = console._master(svc).open(user.totp_secret_sealed, user.id.bytes).decode()
        step = totp.accepted_step(secret, code or "", svc.now().timestamp(), user.totp_last_step)
        good = good and step is not None
        if step is not None:
            user.totp_last_step = step
    if not good:
        raise ApiError(403, "reauthentication_failed", "that password or code is wrong")


async def registration_options(svc: Services, current: ConsoleSession) -> dict[str, Any]:
    """What the browser's `navigator.credentials.create` needs. The challenge is kept for one registration."""
    challenge = secrets.token_bytes(32)
    async with tenant(svc.sessions, user_id=current.user_id) as session:
        user = await session.get(User, current.user_id)
        if user is None:
            raise ApiError(401, "not_signed_in", "sign in again")
        existing = list(await session.scalars(select(Passkey.credential_id).where(Passkey.user_id == user.id)))
    await svc.store.put(f"passkey:new:{current.user_id}", challenge, CHALLENGE_TTL_S)
    return {
        "challenge": webauthn.b64url_encode(challenge),
        "rp": {"id": rp_id(svc), "name": "Dwarpal console"},
        # The person's handle is their account's random ID: it names no one.
        "user": {"id": webauthn.b64url_encode(user.id.bytes), "name": user.email, "displayName": user.email},
        "pubKeyCredParams": [
            {"type": "public-key", "alg": webauthn.EDDSA},
            {"type": "public-key", "alg": webauthn.ES256},
        ],
        "authenticatorSelection": {"residentKey": "required", "userVerification": "required"},
        "attestation": "none",
        "excludeCredentials": [{"type": "public-key", "id": webauthn.b64url_encode(c)} for c in existing],
        "timeout": CHALLENGE_TTL_S * 1000,
    }


async def register(
    svc: Services,
    current: ConsoleSession,
    name: str,
    client_data_json: str,
    attestation_object: str,
    password: str,
    code: str | None,
    address: str,
) -> dict[str, Any]:
    """Check the device's answer to the registration's challenge and keep the new passkey's public key."""
    now = svc.now()
    async with tenant(svc.sessions, user_id=current.user_id) as session:
        user = await session.get(User, current.user_id, with_for_update=True)
        if user is None:
            raise ApiError(401, "not_signed_in", "sign in again")
        await _reauthenticate(svc, user, password, code, address)
        challenge = await svc.store.take(f"passkey:new:{current.user_id}")
        if challenge is None:
            raise ApiError(409, "no_passkey_pending", "start adding a passkey again: the last request expired")
        try:
            made = webauthn.verify_registration(
                _decoded(client_data_json),
                _decoded(attestation_object),
                challenge,
                svc.settings.console_origins,
                rp_id(svc),
            )
        except webauthn.WebAuthnError as error:
            raise ApiError(422, f"passkey_{error.code}", str(error)) from None
        count = await session.scalar(select(func.count()).select_from(Passkey).where(Passkey.user_id == user.id))
        if (count or 0) >= MAX_PASSKEYS:
            raise ApiError(409, "too_many_passkeys", f"remove a passkey first: at most {MAX_PASSKEYS} are kept")
        passkey = Passkey(
            id=svc.new_id(),
            user_id=user.id,
            credential_id=made.credential_id,
            public_key=made.public_key,
            sign_count=made.sign_count,
            name=name,
            created_at=now,
        )
        session.add(passkey)
        try:
            await session.flush()
        except IntegrityError:  # this device's passkey is registered already
            raise ApiError(409, "passkey_exists", "this passkey is registered already") from None
        await console._record_for_all(session, user, "user.passkey_added", {"name": name}, now)
        await session.commit()
    return _shown(passkey)


def _shown(passkey: Passkey) -> dict[str, Any]:
    return {
        "id": ids.encode("pk", passkey.id),
        "name": passkey.name,
        "created_at": passkey.created_at.isoformat(),
        "last_used_at": passkey.last_used_at.isoformat() if passkey.last_used_at else None,
    }


async def list_passkeys(svc: Services, current: ConsoleSession) -> dict[str, Any]:
    async with tenant(svc.sessions, user_id=current.user_id) as session:
        rows = await session.scalars(
            select(Passkey).where(Passkey.user_id == current.user_id).order_by(Passkey.created_at)
        )
        return {"data": [_shown(row) for row in rows]}


async def remove(svc: Services, current: ConsoleSession, passkey_text: str) -> None:
    try:
        passkey_id = ids.decode("pk", passkey_text)
    except ids.InvalidIdError:
        raise ApiError(404, "passkey_not_found", "no such passkey") from None
    now = svc.now()
    async with tenant(svc.sessions, user_id=current.user_id) as session:
        passkey = await session.get(Passkey, passkey_id, with_for_update=True)
        user = await session.get(User, current.user_id)
        if passkey is None or user is None or passkey.user_id != user.id:
            raise ApiError(404, "passkey_not_found", "no such passkey")
        await session.delete(passkey)
        await console._record_for_all(session, user, "user.passkey_removed", {"name": passkey.name}, now)
        await session.commit()


async def sign_in_options(svc: Services, address: str) -> dict[str, Any]:
    """A challenge for `navigator.credentials.get`, with no account named: the device offers its passkeys for this
    site, and the person picks one. Counted against the address's sign-in limit, so challenges can't be farmed."""
    await _spend_address(svc, address)
    challenge = secrets.token_bytes(32)
    await svc.store.put(f"passkey:sign-in:{webauthn.b64url_encode(challenge)}", b"1", CHALLENGE_TTL_S)
    return {
        "challenge": webauthn.b64url_encode(challenge),
        "rpId": rp_id(svc),
        "userVerification": "required",
        "timeout": CHALLENGE_TTL_S * 1000,
    }


async def _spend_address(svc: Services, address: str) -> None:
    settings = svc.settings
    wait_ms = await svc.store.take_token(
        f"sign-in:address:{address}", settings.login_per_minute / 60, settings.login_burst
    )
    if wait_ms:
        retry = {"Retry-After": str(-(-wait_ms // 1000))}
        raise ApiError(429, "too_many_sign_ins", "too many sign-in attempts; wait and try again", retry)


def _challenge_in(client_data_json: bytes) -> str:
    """The challenge the browser says it signed: only a key to look up — the full check comes after."""
    try:
        client = json.loads(client_data_json)
    except ValueError:
        raise SIGN_IN_REFUSED from None
    challenge = client.get("challenge") if isinstance(client, dict) else None
    if not isinstance(challenge, str) or len(challenge) > 128:
        raise SIGN_IN_REFUSED
    return challenge


async def sign_in(
    svc: Services,
    credential_id: str,
    client_data_json: str,
    authenticator_data: str,
    signature: str,
    user_handle: str | None,
    address: str,
) -> tuple[str, ConsoleSession]:
    """Check a passkey's signature over a challenge this server gave out — once — and open a console session."""
    await _spend_address(svc, address)
    client_data = _decoded(client_data_json)
    challenge_text = _challenge_in(client_data)
    if await svc.store.take(f"passkey:sign-in:{challenge_text}") is None:
        raise ApiError(401, "passkey_challenge_expired", "the sign-in took too long or was used already; try again")
    async with svc.sessions() as session:
        found = (await session.execute(FIND_PASSKEY, {"credential_id": _decoded(credential_id)})).first()
    if found is None or (user_handle is not None and _decoded(user_handle) != found.user_id.bytes):
        raise SIGN_IN_REFUSED
    now = svc.now()
    async with tenant(svc.sessions, user_id=found.user_id) as session:
        passkey = await session.get(Passkey, found.id, with_for_update=True)
        user = await session.get(User, found.user_id)
        if passkey is None or user is None:
            raise SIGN_IN_REFUSED
        try:
            passkey.sign_count = webauthn.verify_assertion(
                passkey.public_key,
                passkey.sign_count,
                client_data,
                _decoded(authenticator_data),
                _decoded(signature),
                webauthn.b64url_decode(challenge_text),
                svc.settings.console_origins,
                rp_id(svc),
            )
        except webauthn.WebAuthnError as error:
            raise ApiError(401, f"passkey_{error.code}", str(error)) from None
        passkey.last_used_at = user.last_login_at = now
        target = ids.encode("usr", user.id)
        for org_id in await session.scalars(select(Membership.org_id).where(Membership.user_id == user.id)):
            facts = {"method": "passkey"}
            await audit.record(session, org_id, console.actor_of(user.id), "user.signed_in", target, facts, now)
        await session.commit()
    return await console.open_session(svc, found.user_id)
