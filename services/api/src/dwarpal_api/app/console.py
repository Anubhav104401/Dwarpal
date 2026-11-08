"""The console's use cases, for people at Dwarpal's customers: signing up and in, one-time codes, members, keys and
the audit log. Every organisation action checks the person's role first (domain/roles.py)."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import re
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from dwarpal_api.adapters.db import FIND_USER, TAKE_INVITATIONS, name_tenant, tenant
from dwarpal_api.adapters.passwords import hash_password, verify_password
from dwarpal_api.adapters.tables import (
    ApiKey,
    AuditEntry,
    Invitation,
    Membership,
    Organization,
    Passkey,
    Project,
    User,
    VerificationAttempt,
    VerificationSession,
)
from dwarpal_api.app import analytics, audit, policies, verification, webhooks
from dwarpal_api.domain import ids, origins, totp
from dwarpal_api.domain.keys import SCOPES, generate_api_key
from dwarpal_api.domain.policy import Policy
from dwarpal_api.domain.roles import Action, Role, can
from dwarpal_api.errors import ApiError

if TYPE_CHECKING:
    from dwarpal_api.adapters.signing import MasterKey
    from dwarpal_api.app.verification import Services

EMAIL = re.compile(r"^[^@\s]{1,64}@[^@\s]{1,189}\.[^@\s.]{2,}$")
PASSWORD_LENGTHS = (12, 256)
MAX_PROJECTS = 20
PROJECT_NAME_LENGTHS = (1, 80)
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


def _generation(user_id: uuid.UUID) -> str:
    """The key of a person's session generation: every session remembers the one it began in, and changing the
    password or deleting the account moves it on, which ends all the sessions begun before (decisions D31, D32)."""
    return f"console:generation:{user_id}"


async def open_session(svc: Services, user_id: uuid.UUID) -> tuple[str, ConsoleSession]:
    """A new signed-in session: an unguessable token for the cookie, and a separate token against CSRF."""
    token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    generation = await svc.store.counter(_generation(user_id))
    record = json.dumps({"user": str(user_id), "csrf": csrf, "generation": generation}).encode()
    await svc.store.put(_slot(token), record, svc.settings.console_session_ttl_s)
    return token, ConsoleSession(user_id, csrf)


async def session_of(svc: Services, token: str) -> ConsoleSession | None:
    stored = await svc.store.fetch(_slot(token), svc.settings.console_session_ttl_s) if token else None
    if stored is None:
        return None
    record = json.loads(stored)
    user_id = uuid.UUID(record["user"])
    if record.get("generation", 0) != await svc.store.counter(_generation(user_id)):
        await svc.store.drop(_slot(token))  # begun before a password change or the account's deletion
        return None
    return ConsoleSession(user_id, record["csrf"])


async def end_sessions(svc: Services, user_id: uuid.UUID) -> None:
    """End every console session of this person, everywhere."""
    await svc.store.bump(_generation(user_id))


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
            await _join_invited(session, user_id, email, now)
            await session.commit()
    except IntegrityError:  # the same address signed up at the same moment
        raise ApiError(409, "email_taken", "an account with this e-mail address already exists") from None
    return await open_session(svc, user_id)


async def _join_invited(session: AsyncSession, user_id: uuid.UUID, email: str, now: datetime) -> None:
    """A new account joins every organisation that invited its address (decision D44), with the role each named. The
    invitations are taken — deleted — in the same transaction, so none is used twice."""
    for org_id, role, invited_by in (await session.execute(TAKE_INVITATIONS, {"email": email})).all():
        await name_tenant(session, org_id=org_id, user_id=user_id)
        session.add(Membership(org_id=org_id, user_id=user_id, role=role, created_at=now))
        facts = {"role": role, "invited_by": ids.encode("usr", invited_by)}
        await audit.record(session, org_id, actor_of(user_id), "member.joined", ids.encode("usr", user_id), facts, now)


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
            if step is not None:
                user.totp_last_step = step
            elif _use_recovery_code(svc, user, code):
                left = {"recovery_codes_left": len(user.recovery_digests)}
                await _record_for_all(session, user, "user.recovery_code_used", left, now)
            else:
                raise ApiError(401, "invalid_totp", "that code is wrong or already used")
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
        "recovery_codes_left": len(user.recovery_digests),
        "csrf_token": current.csrf,
        "organisations": [{"id": ids.encode("org", org.id), "name": org.name, "role": role} for org, role in rows],
    }


def _recovery_key(svc: Services) -> bytes:
    """The key for recovery codes' HMACs, derived from the master key for this purpose alone."""
    master = base64.b64decode(svc.settings.master_key.get_secret_value())
    return hmac.new(master, b"dwarpal recovery codes", hashlib.sha256).digest()


def _new_recovery_codes(svc: Services, user: User) -> list[str]:
    """Replace the user's recovery codes with a fresh set, and return them: the only time they exist in plain text."""
    codes = totp.new_recovery_codes()
    key = _recovery_key(svc)
    user.recovery_digests = [totp.recovery_digest(key, user.id.bytes, code) for code in codes]
    return codes


def _use_recovery_code(svc: Services, user: User, code: str) -> bool:
    """Whether `code` is one of the user's unused recovery codes; if so, it is used up."""
    digest = totp.recovery_digest(_recovery_key(svc), user.id.bytes, code)
    if not any(hmac.compare_digest(digest, kept) for kept in user.recovery_digests):
        return False
    user.recovery_digests = [kept for kept in user.recovery_digests if kept != digest]
    return True


async def _record_for_all(session: AsyncSession, user: User, action: str, facts: dict[str, Any], now: Any) -> None:
    """Record something a person did to their own account in every organisation they belong to."""
    target = ids.encode("usr", user.id)
    for org_id in await session.scalars(select(Membership.org_id).where(Membership.user_id == user.id)):
        await audit.record(session, org_id, actor_of(user.id), action, target, facts, now)


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


async def totp_confirm(svc: Services, current: ConsoleSession, code: str) -> dict[str, Any]:
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
        codes = _new_recovery_codes(svc, user)
        await _record_for_all(session, user, "user.mfa_enabled", {}, now)
        await session.commit()
    return {"recovery_codes": codes}


async def replace_recovery_codes(svc: Services, current: ConsoleSession) -> dict[str, Any]:
    """A fresh set of recovery codes, replacing all the old ones (used or not): for when they were lost or used up."""
    now = svc.now()
    async with tenant(svc.sessions, user_id=current.user_id) as session:
        user = await session.get(User, current.user_id, with_for_update=True)
        if user is None or user.totp_secret_sealed is None:
            raise ApiError(409, "totp_not_enabled", "switch on one-time codes first")
        codes = _new_recovery_codes(svc, user)
        await _record_for_all(session, user, "user.recovery_codes_replaced", {}, now)
        await session.commit()
    return {"recovery_codes": codes}


async def totp_disable(svc: Services, current: ConsoleSession, password: str, code: str, address: str) -> None:
    """Switch one-time codes off — only with the password and a current code, so a borrowed signed-in browser isn't
    enough to remove the protection. Attempts count against the same limits as signing in."""
    now = svc.now()
    async with tenant(svc.sessions, user_id=current.user_id) as session:
        user = await session.get(User, current.user_id, with_for_update=True)
        if user is None or user.totp_secret_sealed is None:
            raise ApiError(409, "totp_not_enabled", "one-time codes are already off")
        await _spend_sign_in(svc, user.email, address)
        secret = _master(svc).open(user.totp_secret_sealed, user.id.bytes).decode()
        step = totp.accepted_step(secret, code, now.timestamp(), user.totp_last_step)
        if not await verify_password(user.password_hash, password) or step is None:
            raise ApiError(403, "reauthentication_failed", "that password or code is wrong")
        user.totp_secret_sealed, user.totp_pending_sealed, user.totp_last_step = None, None, None
        user.recovery_digests = []
        await _record_for_all(session, user, "user.mfa_disabled", {}, now)
        await session.commit()


async def _reauthenticate(svc: Services, user: User, password: str, code: str | None, now: datetime) -> None:
    """The person, not just their signed-in browser: the password, and a current code if one-time codes are on."""
    password_ok = await verify_password(user.password_hash, password)
    if user.totp_secret_sealed is not None:
        secret = _master(svc).open(user.totp_secret_sealed, user.id.bytes).decode()
        step = totp.accepted_step(secret, code or "", now.timestamp(), user.totp_last_step)
        if not password_ok or step is None:
            raise ApiError(403, "reauthentication_failed", "that password or code is wrong")
        user.totp_last_step = step
    elif not password_ok:
        raise ApiError(403, "reauthentication_failed", "that password is wrong")


async def change_password(
    svc: Services, current: ConsoleSession, password: str, new_password: str, code: str | None, address: str
) -> tuple[str, ConsoleSession]:
    """A new password (decision D31), with the old one (and a current code, if one-time codes are on). Every console
    session of the person ends, everywhere; this browser gets a fresh one."""
    now = svc.now()
    async with tenant(svc.sessions, user_id=current.user_id) as session:
        user = await session.get(User, current.user_id, with_for_update=True)
        if user is None:
            raise ApiError(401, "not_signed_in", "sign in again")
        await _spend_sign_in(svc, user.email, address)
        await _reauthenticate(svc, user, password, code, now)
        check_password(new_password, user.email)
        user.password_hash = await hash_password(new_password)
        await _record_for_all(session, user, "user.password_changed", {}, now)
        await session.commit()
    await end_sessions(svc, current.user_id)
    return await open_session(svc, current.user_id)


async def delete_account(svc: Services, current: ConsoleSession, password: str, code: str | None, address: str) -> None:
    """Erase the person's account (decision D32), with their password (and a current code, if one-time codes are on).

    Refused while they are the only owner of an organisation that has other members: ownership must be handed over
    first. An organisation where they are the only member is closed with them: its keys stop at once, and its records
    are purged by the usual retention. Their e-mail address, password, one-time-code secret, recovery codes and passkeys
    are erased, and every session ends; their ID stays in the audit chains, which therefore still verify."""
    now = svc.now()
    async with tenant(svc.sessions, user_id=current.user_id) as session:
        user = await session.get(User, current.user_id, with_for_update=True)
        if user is None:
            raise ApiError(401, "not_signed_in", "sign in again")
        await _spend_sign_in(svc, user.email, address)
        await _reauthenticate(svc, user, password, code, now)
        memberships = list(await session.scalars(select(Membership).where(Membership.user_id == user.id)))
        closing: dict[uuid.UUID, bool] = {}
        for membership in memberships:
            # Each organisation in turn is named as the tenant, within this one transaction: all or nothing.
            await name_tenant(session, org_id=membership.org_id, user_id=user.id)
            others_query = select(Membership).where(
                Membership.org_id == membership.org_id, Membership.user_id != user.id
            )
            others = list(await session.scalars(others_query.with_for_update()))
            if others and membership.role == Role.OWNER and all(o.role != Role.OWNER for o in others):
                name = await session.scalar(select(Organization.name).where(Organization.id == membership.org_id))
                raise ApiError(409, "hand_over_ownership", f"make someone else an owner of {name} first")
            closing[membership.org_id] = not others
        target = ids.encode("usr", user.id)
        for membership in memberships:
            org_id = membership.org_id
            await name_tenant(session, org_id=org_id, user_id=user.id)
            if closing[org_id]:
                projects = select(Project.id).where(Project.org_id == org_id)
                stop = update(ApiKey).where(ApiKey.project_id.in_(projects), ApiKey.revoked_at.is_(None))
                await session.execute(stop.values(revoked_at=now))
                org_text = ids.encode("org", org_id)
                await audit.record(session, org_id, actor_of(user.id), "organisation.closed", org_text, {}, now)
            await audit.record(session, org_id, actor_of(user.id), "user.deleted", target, {}, now)
            await session.delete(membership)
        await name_tenant(session, user_id=user.id)
        user.email = f"deleted-{user.id.hex}@deleted.invalid"  # unique, and no one's address
        user.password_hash = "!"  # not an Argon2 hash: no password can ever match it  # noqa: S105
        user.totp_secret_sealed, user.totp_pending_sealed, user.totp_last_step = None, None, None
        user.recovery_digests, user.last_login_at = [], None
        await session.execute(delete(Passkey).where(Passkey.user_id == user.id))
        await session.commit()
    await end_sessions(svc, current.user_id)


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


def project_view(project: Project) -> dict[str, Any]:
    return {
        "id": ids.encode("prj", project.id),
        "name": project.name,
        "allowed_origins": project.allowed_origins,
        "retention_days": project.retention_days,
    }


async def list_projects(svc: Services, current: ConsoleSession, org_text: str) -> dict[str, Any]:
    """The organisation's projects, oldest first, for any member."""
    org_id, _ = await authorise(svc, current, org_text, Action.READ_SESSIONS)
    async with tenant(svc.sessions, org_id=org_id, user_id=current.user_id) as session:
        query = select(Project).where(Project.org_id == org_id).order_by(Project.created_at)
        projects = list(await session.scalars(query))
    return {"object": "list", "data": [project_view(p) for p in projects]}


def _project_name(name: str) -> str:
    name, (shortest, longest) = name.strip(), PROJECT_NAME_LENGTHS
    if not shortest <= len(name) <= longest:
        raise ApiError(422, "invalid_project_name", f"a project's name is {shortest} to {longest} characters")
    return name


def _allowed_origins(svc: Services, texts: list[str]) -> list[str]:
    try:
        return origins.allowed_origins(texts, production=svc.settings.environment == "production")
    except origins.InvalidOriginError as error:
        raise ApiError(422, "invalid_origin", str(error)) from None


async def create_project(
    svc: Services, current: ConsoleSession, org_text: str, name: str, allowed_origins: list[str]
) -> dict[str, Any]:
    """A new project in the organisation, with the origins its websites run on (decisions D28, D29)."""
    org_id, _ = await authorise(svc, current, org_text, Action.MANAGE_PROJECTS)
    name, chosen, now = _project_name(name), _allowed_origins(svc, allowed_origins), svc.now()
    async with tenant(svc.sessions, org_id=org_id, user_id=current.user_id) as session:
        # The organisation's row is locked, so two new projects at once can't both slip under the limit.
        await session.get(Organization, org_id, with_for_update=True)
        count = await session.scalar(select(func.count()).select_from(Project).where(Project.org_id == org_id))
        if (count or 0) >= MAX_PROJECTS:
            raise ApiError(409, "too_many_projects", f"an organisation may have at most {MAX_PROJECTS} projects")
        project = Project(
            id=svc.new_id(), org_id=org_id, name=name, allowed_origins=chosen, retention_days=90, created_at=now
        )
        session.add(project)
        target, facts = ids.encode("prj", project.id), {"name": name, "allowed_origins": chosen}
        await audit.record(session, org_id, actor_of(current.user_id), "project.created", target, facts, now)
        await session.commit()
    return project_view(project)


async def update_project(
    svc: Services,
    current: ConsoleSession,
    org_text: str,
    project_text: str,
    name: str | None,
    allowed_origins: list[str] | None,
) -> dict[str, Any]:
    """Rename a project, or replace the list of origins it allows; what changed is recorded, from and to."""
    if name is None and allowed_origins is None:
        raise ApiError(422, "nothing_to_change", "send a new name, new allowed origins, or both")
    org_id, project_id = await project_in(svc, current, org_text, project_text, Action.MANAGE_PROJECTS)
    new_name = None if name is None else _project_name(name)
    chosen = None if allowed_origins is None else _allowed_origins(svc, allowed_origins)
    now = svc.now()
    async with tenant(svc.sessions, org_id=org_id, user_id=current.user_id) as session:
        project = await session.get(Project, project_id, with_for_update=True)
        if project is None:
            raise ApiError(404, "project_not_found", "no such project")
        changes: dict[str, Any] = {}
        if new_name is not None and new_name != project.name:
            changes["name"] = {"from": project.name, "to": new_name}
            project.name = new_name
        if chosen is not None and chosen != project.allowed_origins:
            changes["allowed_origins"] = {"from": project.allowed_origins, "to": chosen}
            project.allowed_origins = chosen
        if changes:
            target = ids.encode("prj", project_id)
            await audit.record(session, org_id, actor_of(current.user_id), "project.updated", target, changes, now)
        await session.commit()
    return project_view(project)


async def add_member(svc: Services, current: ConsoleSession, org_text: str, email: str, role: str) -> dict[str, Any]:
    """Give an account a role in the organisation; an address without an account yet is invited instead, and joins on
    signing up (decision D44). Only an owner may make — or invite — another owner."""
    org_id, own_role = await authorise(svc, current, org_text, Action.MANAGE_MEMBERS)
    if role not in set(Role):
        raise ApiError(422, "unknown_role", f"choose a role from {', '.join(Role)}")
    if role == Role.OWNER and own_role != Role.OWNER:
        raise ApiError(403, "forbidden_for_role", "only an owner can make someone an owner")
    email, now = normalise_email(email), svc.now()
    actor = actor_of(current.user_id)
    try:
        async with tenant(svc.sessions, org_id=org_id, user_id=current.user_id) as session:
            found = (await session.execute(FIND_USER, {"email": email})).first()
            if found is None:
                invitation = Invitation(
                    id=svc.new_id(), org_id=org_id, email=email, role=role, invited_by=current.user_id, created_at=now
                )
                session.add(invitation)
                # The audit names the invitation, not the address: the chain can't be edited later.
                target = ids.encode("inv", invitation.id)
                await audit.record(session, org_id, actor, "member.invited", target, {"role": role}, now)
                await session.commit()
                return {"invitation": target, "email": email, "role": role, "pending": True}
            session.add(Membership(org_id=org_id, user_id=found.id, role=role, created_at=now))
            target = ids.encode("usr", found.id)
            await audit.record(session, org_id, actor, "member.added", target, {"role": role}, now)
            await session.commit()
    except IntegrityError:
        raise ApiError(409, "already_a_member", "that person is already a member, or already invited") from None
    return {"user": ids.encode("usr", found.id), "email": email, "role": role, "pending": False}


async def list_invitations(svc: Services, current: ConsoleSession, org_text: str) -> dict[str, Any]:
    """The organisation's invitations still waiting for someone to sign up, oldest first."""
    org_id, _ = await authorise(svc, current, org_text, Action.MANAGE_MEMBERS)
    async with tenant(svc.sessions, org_id=org_id, user_id=current.user_id) as session:
        query = select(Invitation).where(Invitation.org_id == org_id).order_by(Invitation.created_at)
        waiting = list(await session.scalars(query))
    data = [
        {
            "id": ids.encode("inv", i.id),
            "email": i.email,
            "role": i.role,
            "created_at": i.created_at.isoformat(),
        }
        for i in waiting
    ]
    return {"object": "list", "data": data}


async def cancel_invitation(svc: Services, current: ConsoleSession, org_text: str, invitation_text: str) -> None:
    org_id, _ = await authorise(svc, current, org_text, Action.MANAGE_MEMBERS)
    try:
        invitation_id = ids.decode("inv", invitation_text)
    except ids.InvalidIdError:
        raise ApiError(404, "invitation_not_found", "no such invitation") from None
    async with tenant(svc.sessions, org_id=org_id, user_id=current.user_id) as session:
        # No lock: an invitation is never changed, only made and deleted (the app may not update one).
        invitation = await session.get(Invitation, invitation_id)
        if invitation is None or invitation.org_id != org_id:
            raise ApiError(404, "invitation_not_found", "no such invitation")
        facts = {"role": invitation.role}
        await audit.record(
            session, org_id, actor_of(current.user_id), "member.invitation_cancelled", invitation_text, facts, svc.now()
        )
        await session.delete(invitation)
        await session.commit()


def _member_id(user_text: str) -> uuid.UUID:
    try:
        return ids.decode("usr", user_text)
    except ids.InvalidIdError:
        raise ApiError(404, "member_not_found", "no such member") from None


async def _lock_member(
    session: AsyncSession, org_id: uuid.UUID, own_role: str, user_id: uuid.UUID, new_role: str | None
) -> Membership:
    """The membership to change (to `new_role`) or remove (`None`), locked, if the rules allow it: only an owner may
    make, change or remove an owner, and the last owner stays one."""
    # Lock the owners first, in one order for everyone: two owners demoting each other at once can't both succeed.
    owners_query = select(Membership).where(Membership.org_id == org_id, Membership.role == Role.OWNER)
    owners = list(await session.scalars(owners_query.with_for_update()))
    member = await session.get(Membership, (org_id, user_id), with_for_update=True)
    if member is None:
        raise ApiError(404, "member_not_found", "no such member")
    if Role.OWNER in (member.role, new_role) and own_role != Role.OWNER:
        raise ApiError(403, "forbidden_for_role", "only an owner can make, change or remove an owner")
    if member.role == Role.OWNER and new_role != Role.OWNER and len(owners) == 1:
        raise ApiError(409, "last_owner", "an organisation needs an owner: make someone else an owner first")
    return member


async def change_role(
    svc: Services, current: ConsoleSession, org_text: str, user_text: str, role: str
) -> dict[str, Any]:
    """Give a member another role, recorded with the old and new roles."""
    org_id, own_role = await authorise(svc, current, org_text, Action.MANAGE_MEMBERS)
    if role not in set(Role):
        raise ApiError(422, "unknown_role", f"choose a role from {', '.join(Role)}")
    user_id, now = _member_id(user_text), svc.now()
    async with tenant(svc.sessions, org_id=org_id, user_id=current.user_id) as session:
        member = await _lock_member(session, org_id, own_role, user_id, role)
        before, member.role = member.role, role
        target, facts = ids.encode("usr", user_id), {"from": before, "to": role}
        await audit.record(session, org_id, actor_of(current.user_id), "member.role_changed", target, facts, now)
        await session.commit()
    return {"user": target, "role": role}


async def remove_member(svc: Services, current: ConsoleSession, org_text: str, user_text: str) -> None:
    """Take someone out of the organisation (their account stays). People may remove themselves, unless last owner."""
    org_id, own_role = await authorise(svc, current, org_text, Action.MANAGE_MEMBERS)
    user_id, now = _member_id(user_text), svc.now()
    async with tenant(svc.sessions, org_id=org_id, user_id=current.user_id) as session:
        member = await _lock_member(session, org_id, own_role, user_id, None)
        target, facts = ids.encode("usr", user_id), {"role": member.role}
        await audit.record(session, org_id, actor_of(current.user_id), "member.removed", target, facts, now)
        await session.delete(member)
        await session.commit()


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


def key_view(key: ApiKey, now: datetime) -> dict[str, Any]:
    """What the console shows of a key (decision D30): never its secret, which Dwarpal doesn't have."""
    expired = key.expires_at is not None and key.expires_at <= now
    return {
        "id": key.lookup,
        "object": "api_key",
        "livemode": key.livemode,
        "scopes": key.scopes,
        "created_at": key.created_at.isoformat(),
        "expires_at": key.expires_at.isoformat() if key.expires_at else None,
        "revoked_at": key.revoked_at.isoformat() if key.revoked_at else None,
        "state": "revoked" if key.revoked_at else "expired" if expired else "active",
    }


async def project_keys(svc: Services, current: ConsoleSession, org_text: str, project_text: str) -> dict[str, Any]:
    """A project's keys, newest first, for the roles that may create and revoke them."""
    org_id, project_id = await project_in(svc, current, org_text, project_text, Action.MANAGE_KEYS)
    async with tenant(svc.sessions, org_id=org_id, user_id=current.user_id) as session:
        query = select(ApiKey).where(ApiKey.project_id == project_id).order_by(ApiKey.created_at.desc())
        keys = list(await session.scalars(query))
    now = svc.now()
    return {"object": "list", "data": [key_view(key, now) for key in keys]}


async def revoke_key(svc: Services, current: ConsoleSession, org_text: str, project_text: str, key_text: str) -> None:
    """Stop a key at once — every request looks its key up afresh, so the next one with it is refused. Revoking a key
    twice changes nothing."""
    org_id, project_id = await project_in(svc, current, org_text, project_text, Action.MANAGE_KEYS)
    now = svc.now()
    async with tenant(svc.sessions, org_id=org_id, user_id=current.user_id) as session:
        query = select(ApiKey).where(ApiKey.project_id == project_id, ApiKey.lookup == key_text)
        key = await session.scalar(query.with_for_update())
        if key is None:
            raise ApiError(404, "key_not_found", "no such key in this project")
        if key.revoked_at is None:
            key.revoked_at = now
            facts = {"project": ids.encode("prj", project_id)}
            await audit.record(session, org_id, actor_of(current.user_id), "api_key.revoked", key.lookup, facts, now)
        await session.commit()


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


async def project_in(
    svc: Services, current: ConsoleSession, org_text: str, project_text: str, action: Action
) -> tuple[uuid.UUID, uuid.UUID]:
    """The organisation and one of its projects, if the person's role there allows `action`; else 404 or 403."""
    org_id, _ = await authorise(svc, current, org_text, action)
    try:
        project_id = ids.decode("prj", project_text)
    except ids.InvalidIdError:
        raise ApiError(404, "project_not_found", "no such project") from None
    async with tenant(svc.sessions, org_id=org_id, user_id=current.user_id) as session:
        project = await session.get(Project, project_id)
    if project is None or project.org_id != org_id:
        raise ApiError(404, "project_not_found", "no such project")
    return org_id, project_id


async def project_sessions(
    svc: Services,
    current: ConsoleSession,
    org_text: str,
    project_text: str,
    livemode: bool,
    limit: int,
    starting_after: str | None,
    only: verification.SessionFilter,
) -> dict[str, Any]:
    """A project's sessions, newest first, a page at a time — the same list a website reads with its key."""
    _, project_id = await project_in(svc, current, org_text, project_text, Action.READ_SESSIONS)
    return await verification.list_sessions(svc, project_id, livemode, limit, starting_after, only)


async def session_trace(
    svc: Services, current: ConsoleSession, org_text: str, project_text: str, session_text: str
) -> dict[str, Any]:
    """One session with its **decision trace**: every attempt's outcome, reasons and scores — the numbers the
    decision rested on, never an image."""
    _, project_id = await project_in(svc, current, org_text, project_text, Action.READ_SESSIONS)
    session_id = verification.parse_session_id(session_text)
    async with tenant(svc.sessions, project_id=project_id) as session:
        row = await session.get(VerificationSession, session_id)
        if row is None:
            raise ApiError(404, "session_not_found", "no such verification session")
        query = (
            select(VerificationAttempt)
            .where(VerificationAttempt.session_id == session_id)
            .order_by(VerificationAttempt.created_at)
        )
        attempts = list(await session.scalars(query))
    trace = [
        {
            "kind": attempt.kind,
            "outcome": attempt.outcome,
            "reasons": attempt.reasons,
            "scores": attempt.scores,
            "created_at": attempt.created_at.isoformat(),
        }
        for attempt in attempts
    ]
    return {**verification.summary_view(row, svc.now()), "attempts": trace}


async def project_analytics(
    svc: Services, current: ConsoleSession, org_text: str, project_text: str, livemode: bool, days: int
) -> dict[str, Any]:
    _, project_id = await project_in(svc, current, org_text, project_text, Action.READ_ANALYTICS)
    return await analytics.session_counts(svc, project_id, livemode, days)


def model_information(svc: Services) -> dict[str, Any]:
    """The age model now deciding, for anyone signed in: what it is, what it learnt from and was calibrated on, whether
    it may decide live sessions, and its lines for each age. Not its file, checksums or the build that made it."""
    details = svc.manifest.details
    training = details.get("training", {})
    calibration = details.get("calibration")
    return {
        "version": svc.manifest.version,
        "calibrated": svc.manifest.calibrated,
        "note": details.get("note"),
        "permitted_use": details.get("permitted_use"),
        "training": {"backbone": training["backbone"], "dataset": training["dataset"]} if training else None,
        "calibration": calibration,
        "thresholds": [
            {
                "min_age": row["min_age"],
                "risk_budget": row["risk_budget"],
                "tau_pass": row["tau_pass"],
                "tau_fail": row["tau_fail"],
                "minor_bound": row.get("minor_bound"),  # worst plausible share of those under the age who pass
                "adult_bound": row.get("adult_bound"),  # and of those comfortably over it who fail
                # How adults in each band above the age fared on the test split: the policy editor's projection.
                "adults": [
                    {key: band[key] for key in ("ages", "faces", "pass", "step_up", "fail")}
                    for band in row.get("adults", [])
                ],
            }
            for row in details.get("thresholds", [])
        ],
    }


def published_model(svc: Services) -> dict[str, Any]:
    """The age model now deciding, for anyone, signed in or not: all that `model_information` says except the scores
    where each line passes and fails. Its bounds and the adults' outcomes say how well a line works; the exact scores
    would only help someone tuning an attack against it."""
    information = model_information(svc)
    lines = [
        {key: value for key, value in line.items() if key not in ("tau_pass", "tau_fail")}
        for line in information["thresholds"]
    ]
    return {**information, "thresholds": lines}


async def project_policies(svc: Services, current: ConsoleSession, org_text: str, project_text: str) -> dict[str, Any]:
    _, project_id = await project_in(svc, current, org_text, project_text, Action.READ_SESSIONS)
    return await policies.list_all(svc.sessions, project_id)


async def add_policy_version(
    svc: Services, current: ConsoleSession, org_text: str, project_text: str, draft: Policy
) -> dict[str, Any]:
    """The next version of one of the project's policies, recorded in the audit log under the person's name."""
    org_id, project_id = await project_in(svc, current, org_text, project_text, Action.MANAGE_POLICIES)
    actor = actor_of(current.user_id)
    return await policies.add_version(
        svc.sessions, svc.manifest, project_id, draft, svc.now(), svc.new_id(), org_id, actor
    )


async def project_webhooks(
    svc: Services, current: ConsoleSession, org_text: str, project_text: str, livemode: bool
) -> dict[str, Any]:
    """A project's webhook endpoints. Only for roles that manage them: they say where the project's events go."""
    _, project_id = await project_in(svc, current, org_text, project_text, Action.MANAGE_WEBHOOKS)
    return await webhooks.list_endpoints(svc, project_id, livemode)


async def add_webhook(
    svc: Services,
    current: ConsoleSession,
    org_text: str,
    project_text: str,
    livemode: bool,
    url: str,
    events: list[str],
) -> dict[str, Any]:
    """A new endpoint, with its signing secret shown once — the same checks as the website API's, the person named."""
    org_id, project_id = await project_in(svc, current, org_text, project_text, Action.MANAGE_WEBHOOKS)
    actor = actor_of(current.user_id)
    return await webhooks.create_endpoint(svc, project_id, org_id, livemode, actor, url, events)


async def remove_webhook(
    svc: Services, current: ConsoleSession, org_text: str, project_text: str, livemode: bool, endpoint_text: str
) -> None:
    org_id, project_id = await project_in(svc, current, org_text, project_text, Action.MANAGE_WEBHOOKS)
    actor = actor_of(current.user_id)
    await webhooks.delete_endpoint(svc, project_id, org_id, livemode, actor, endpoint_text)


async def switch_webhook(
    svc: Services,
    current: ConsoleSession,
    org_text: str,
    project_text: str,
    livemode: bool,
    endpoint_text: str,
    enabled: bool,
) -> dict[str, Any]:
    org_id, project_id = await project_in(svc, current, org_text, project_text, Action.MANAGE_WEBHOOKS)
    actor = actor_of(current.user_id)
    return await webhooks.set_enabled(svc, project_id, org_id, livemode, actor, endpoint_text, enabled)


async def send_test_event(
    svc: Services, current: ConsoleSession, org_text: str, project_text: str, livemode: bool, endpoint_text: str
) -> dict[str, Any]:
    _, project_id = await project_in(svc, current, org_text, project_text, Action.MANAGE_WEBHOOKS)
    return await webhooks.send_test(svc, project_id, livemode, endpoint_text)


async def webhook_deliveries(
    svc: Services, current: ConsoleSession, org_text: str, project_text: str, livemode: bool, endpoint_text: str
) -> dict[str, Any]:
    _, project_id = await project_in(svc, current, org_text, project_text, Action.MANAGE_WEBHOOKS)
    return await webhooks.list_deliveries(svc, project_id, livemode, endpoint_text)


async def replay_delivery(
    svc: Services, current: ConsoleSession, org_text: str, project_text: str, livemode: bool, delivery_text: str
) -> dict[str, Any]:
    _, project_id = await project_in(svc, current, org_text, project_text, Action.MANAGE_WEBHOOKS)
    return await webhooks.replay(svc, project_id, livemode, delivery_text)
