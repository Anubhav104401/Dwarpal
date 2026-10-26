"""The console's use cases, for people at Dwarpal's customers: signing up and in, one-time codes, members, keys and
the audit log. Every organisation action checks the person's role first (domain/roles.py)."""

from __future__ import annotations

import hashlib
import json
import re
import secrets
import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from dwarpal_api.adapters.db import FIND_USER, tenant
from dwarpal_api.adapters.passwords import hash_password, verify_password
from dwarpal_api.adapters.tables import ApiKey, AuditEntry, Membership, Organization, Project, User
from dwarpal_api.app import audit
from dwarpal_api.domain import ids, totp
from dwarpal_api.domain.keys import SCOPES, generate_api_key
from dwarpal_api.domain.roles import Action, Role, can
from dwarpal_api.errors import ApiError

if TYPE_CHECKING:
    from dwarpal_api.adapters.signing import MasterKey
    from dwarpal_api.app.verification import Services

EMAIL = re.compile(r"^[^@\s]{1,64}@[^@\s]{1,189}\.[^@\s.]{2,}$")
PASSWORD_LENGTHS = (12, 256)
SIGN_IN_REFUSED = ApiError(401, "invalid_credentials", "the e-mail address or the password is wrong")


@dataclass(frozen=True)
class ConsoleSession:
    user_id: uuid.UUID
    csrf: str  # the synchroniser token every change must repeat in its X-CSRF-Token header


def _slot(token: str) -> str:
    return "console:" + hashlib.sha256(token.encode()).hexdigest()  # Valkey never holds the cookie's value itself


def actor_of(user_id: uuid.UUID) -> tuple[str, str]:
    return ("user", ids.encode("usr", user_id))


def _master(svc: Services) -> MasterKey:
    if svc.master is None:
        raise RuntimeError("the toolbox has no master key")
    return svc.master


async def open_session(svc: Services, user_id: uuid.UUID) -> tuple[str, ConsoleSession]:
    """A new signed-in session: an unguessable token for the cookie, and a separate token against CSRF."""
    token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    record = json.dumps({"user": str(user_id), "csrf": csrf}).encode()
    await svc.store.put(_slot(token), record, svc.settings.console_session_ttl_s)
    return token, ConsoleSession(user_id, csrf)


async def session_of(svc: Services, token: str) -> ConsoleSession | None:
    stored = await svc.store.fetch(_slot(token), svc.settings.console_session_ttl_s) if token else None
    if stored is None:
        return None
    record = json.loads(stored)
    return ConsoleSession(uuid.UUID(record["user"]), record["csrf"])


async def close_session(svc: Services, token: str) -> None:
    await svc.store.drop(_slot(token))


def normalise_email(email: str) -> str:
    email = email.strip().lower()
    if not EMAIL.match(email):
        raise ApiError(422, "invalid_email", "that doesn't look like an e-mail address")
    return email


def check_password(password: str, email: str) -> None:
    shortest, longest = PASSWORD_LENGTHS
    if not shortest <= len(password) <= longest or password.lower() == email:
        raise ApiError(422, "weak_password", f"use a password of {shortest} to {longest} characters, not your e-mail")


async def sign_up(svc: Services, email: str, password: str, organisation: str) -> tuple[str, ConsoleSession]:
    """A new person, with a new organisation they own and a first project in it."""
    email = normalise_email(email)
    check_password(password, email)
    password_hash = await hash_password(password)
    now, user_id, org_id = svc.now(), svc.new_id(), svc.new_id()
    try:
        async with tenant(svc.sessions, org_id=org_id, user_id=user_id) as session:
            if (await session.execute(FIND_USER, {"email": email})).first() is not None:
                raise ApiError(409, "email_taken", "an account with this e-mail address already exists")
            session.add(User(id=user_id, email=email, password_hash=password_hash, created_at=now))
            session.add(Organization(id=org_id, name=organisation, slug=f"org-{org_id.hex}", created_at=now))
            await session.flush()
            session.add(Membership(org_id=org_id, user_id=user_id, role=Role.OWNER, created_at=now))
            project = Project(
                id=svc.new_id(), org_id=org_id, name="Default project", allowed_origins=[], created_at=now
            )
            session.add(project)
            facts = {"name": organisation, "project": ids.encode("prj", project.id)}
            await audit.record(
                session, org_id, actor_of(user_id), "organisation.created", ids.encode("org", org_id), facts, now
            )
            await session.commit()
    except IntegrityError:  # the same address signed up at the same moment
        raise ApiError(409, "email_taken", "an account with this e-mail address already exists") from None
    return await open_session(svc, user_id)


async def _spend_sign_in(svc: Services, email: str, address: str) -> None:
    """Sign-in attempts are limited per account and per network address, so guessing passwords is slow."""
    settings = svc.settings
    for key in (f"sign-in:account:{email}", f"sign-in:address:{address}"):
        wait_ms = await svc.store.take_token(key, settings.login_per_minute / 60, settings.login_burst)
        if wait_ms:
            retry = {"Retry-After": str(-(-wait_ms // 1000))}
            raise ApiError(429, "too_many_sign_ins", "too many sign-in attempts; wait and try again", retry)


async def sign_in(
    svc: Services, email: str, password: str, code: str | None, address: str
) -> tuple[str, ConsoleSession]:
    email = email.strip().lower()
    await _spend_sign_in(svc, email, address)
    async with svc.sessions() as session:
        found = (await session.execute(FIND_USER, {"email": email})).first()
    # The same answer, after the same amount of hashing, whether the account exists or the password is wrong.
    if not await verify_password(found.password_hash if found else None, password) or found is None:
        raise SIGN_IN_REFUSED
    now = svc.now()
    async with tenant(svc.sessions, user_id=found.id) as session:
        user = await session.get(User, found.id, with_for_update=True)
        if user is None:
            raise SIGN_IN_REFUSED
        if user.totp_secret_sealed is not None:
            if not code:
                raise ApiError(401, "totp_required", "enter the 6-digit code from your authenticator app")
            secret = _master(svc).open(user.totp_secret_sealed, user.id.bytes).decode()
            step = totp.accepted_step(secret, code, now.timestamp(), user.totp_last_step)
            if step is None:
                raise ApiError(401, "invalid_totp", "that code is wrong or already used")
            user.totp_last_step = step
        user.last_login_at = now
        for org_id in await session.scalars(select(Membership.org_id).where(Membership.user_id == user.id)):
            await audit.record(
                session, org_id, actor_of(user.id), "user.signed_in", ids.encode("usr", user.id), {}, now
            )
        await session.commit()
    return await open_session(svc, found.id)


async def me(svc: Services, current: ConsoleSession) -> dict[str, Any]:
    async with tenant(svc.sessions, user_id=current.user_id) as session:
        user = await session.get(User, current.user_id)
        rows = (
            await session.execute(
                select(Organization, Membership.role)
                .join(Membership, Membership.org_id == Organization.id)
                .where(Membership.user_id == current.user_id)
                .order_by(Organization.created_at)
            )
        ).all()
    if user is None:
        raise ApiError(401, "not_signed_in", "sign in again")
    return {
        "id": ids.encode("usr", user.id),
        "object": "user",
        "email": user.email,
        "totp_enabled": user.totp_secret_sealed is not None,
        "csrf_token": current.csrf,
        "organisations": [{"id": ids.encode("org", org.id), "name": org.name, "role": role} for org, role in rows],
    }


async def totp_enrol(svc: Services, current: ConsoleSession) -> dict[str, Any]:
    """Offer a new secret. It takes effect only once a code made from it is confirmed (totp_confirm)."""
    secret = totp.new_secret()
    async with tenant(svc.sessions, user_id=current.user_id) as session:
        user = await session.get(User, current.user_id, with_for_update=True)
        if user is None:
            raise ApiError(401, "not_signed_in", "sign in again")
        user.totp_pending_sealed = _master(svc).seal(secret.encode(), user.id.bytes)
        await session.commit()
    return {"secret": secret, "uri": totp.provisioning_uri(secret, user.email)}


async def totp_confirm(svc: Services, current: ConsoleSession, code: str) -> None:
    now = svc.now()
    async with tenant(svc.sessions, user_id=current.user_id) as session:
        user = await session.get(User, current.user_id, with_for_update=True)
        if user is None or user.totp_pending_sealed is None:
            raise ApiError(409, "no_totp_pending", "start setting up one-time codes first")
        secret = _master(svc).open(user.totp_pending_sealed, user.id.bytes).decode()
        step = totp.accepted_step(secret, code, now.timestamp(), None)
        if step is None:
            raise ApiError(422, "invalid_totp", "that code is wrong; check the time on your phone")
        user.totp_secret_sealed, user.totp_pending_sealed, user.totp_last_step = user.totp_pending_sealed, None, step
        for org_id in await session.scalars(select(Membership.org_id).where(Membership.user_id == user.id)):
            await audit.record(
                session, org_id, actor_of(user.id), "user.mfa_enabled", ids.encode("usr", user.id), {}, now
            )
        await session.commit()


async def authorise(svc: Services, current: ConsoleSession, org_text: str, action: Action) -> tuple[uuid.UUID, str]:
    """The organisation, if the person is a member whose role allows `action`; else 404 (not a member) or 403."""
    try:
        org_id = ids.decode("org", org_text)
    except ids.InvalidIdError:
        raise ApiError(404, "organisation_not_found", "no such organisation") from None
    async with tenant(svc.sessions, user_id=current.user_id) as session:
        role = await session.scalar(
            select(Membership.role).where(Membership.user_id == current.user_id, Membership.org_id == org_id)
        )
    if role is None:
        raise ApiError(404, "organisation_not_found", "no such organisation")
    if not can(role, action):
        raise ApiError(403, "forbidden_for_role", f"your role ({role}) can't do this")
    return org_id, role


async def list_members(svc: Services, current: ConsoleSession, org_text: str) -> dict[str, Any]:
    org_id, _ = await authorise(svc, current, org_text, Action.READ_SESSIONS)
    async with tenant(svc.sessions, org_id=org_id, user_id=current.user_id) as session:
        rows = (
            await session.execute(
                select(User.id, User.email, Membership.role)
                .join(Membership, Membership.user_id == User.id)
                .where(Membership.org_id == org_id)
                .order_by(Membership.created_at)
            )
        ).all()
    members = [{"user": ids.encode("usr", user_id), "email": email, "role": role} for user_id, email, role in rows]
    return {"object": "list", "data": members}


async def add_member(svc: Services, current: ConsoleSession, org_text: str, email: str, role: str) -> dict[str, Any]:
    """Give an existing account a role in the organisation. Only an owner may make another owner."""
    org_id, own_role = await authorise(svc, current, org_text, Action.MANAGE_MEMBERS)
    if role not in set(Role):
        raise ApiError(422, "unknown_role", f"choose a role from {', '.join(Role)}")
    if role == Role.OWNER and own_role != Role.OWNER:
        raise ApiError(403, "forbidden_for_role", "only an owner can make someone an owner")
    email, now = normalise_email(email), svc.now()
    try:
        async with tenant(svc.sessions, org_id=org_id, user_id=current.user_id) as session:
            found = (await session.execute(FIND_USER, {"email": email})).first()
            if found is None:
                raise ApiError(404, "user_not_found", "there is no account with that e-mail address yet")
            session.add(Membership(org_id=org_id, user_id=found.id, role=role, created_at=now))
            target = ids.encode("usr", found.id)
            await audit.record(session, org_id, actor_of(current.user_id), "member.added", target, {"role": role}, now)
            await session.commit()
    except IntegrityError:
        raise ApiError(409, "already_a_member", "that person is already a member") from None
    return {"user": ids.encode("usr", found.id), "email": email, "role": role}


async def create_key(
    svc: Services, current: ConsoleSession, org_text: str, project_text: str, scopes: list[str], livemode: bool
) -> dict[str, Any]:
    org_id, _ = await authorise(svc, current, org_text, Action.MANAGE_KEYS)
    if not scopes or not set(scopes) <= SCOPES:
        raise ApiError(422, "unknown_scope", f"choose scopes from {', '.join(sorted(SCOPES))}")
    try:
        project_id = ids.decode("prj", project_text)
    except ids.InvalidIdError:
        raise ApiError(404, "project_not_found", "no such project") from None
    key, now = generate_api_key(livemode=livemode), svc.now()
    async with tenant(svc.sessions, org_id=org_id, user_id=current.user_id) as session:
        project = await session.get(Project, project_id)
        if project is None or project.org_id != org_id:
            raise ApiError(404, "project_not_found", "no such project")
        row = ApiKey(
            id=svc.new_id(),
            project_id=project_id,
            livemode=livemode,
            lookup=key.lookup,
            secret_digest=key.digest,
            name="console",
            scopes=sorted(set(scopes)),
            created_at=now,
            expires_at=None,
            revoked_at=None,
        )
        session.add(row)
        facts = {"project": project_text, "scopes": row.scopes, "livemode": livemode}
        await audit.record(session, org_id, actor_of(current.user_id), "api_key.created", key.lookup, facts, now)
        await session.commit()
    # Shown once, now; Dwarpal keeps only its digest.
    return {"id": key.lookup, "object": "api_key", "key": key.plaintext, "scopes": row.scopes, "livemode": livemode}


async def audit_log(svc: Services, current: ConsoleSession, org_text: str, limit: int) -> dict[str, Any]:
    """The organisation's newest audit entries, and whether its whole chain is intact."""
    org_id, _ = await authorise(svc, current, org_text, Action.READ_AUDIT)
    async with tenant(svc.sessions, org_id=org_id, user_id=current.user_id) as session:
        query = select(AuditEntry).where(AuditEntry.org_id == org_id).order_by(AuditEntry.seq.desc()).limit(limit)
        entries = list(await session.scalars(query))
        report = await audit.verify(session, org_id)
    data = [
        {
            "seq": entry.seq,
            "actor": f"{entry.actor_type}:{entry.actor_id}",
            "action": entry.action,
            "target": entry.target,
            "data": entry.data,
            "created_at": entry.created_at.isoformat(),
        }
        for entry in entries
    ]
    chain = {"entries": report.entries, "intact": report.intact, "first_broken": report.first_broken}
    return {"object": "list", "data": data, "chain": chain}
