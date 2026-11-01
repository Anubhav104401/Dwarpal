"""The console API: what Dwarpal's own web console calls on behalf of a signed-in person. A session lives in a cookie;
every change must also carry the session's CSRF token, and come from one of the console's own origins."""

from __future__ import annotations

import hmac
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, Query, Request, Response
from pydantic import BaseModel, ConfigDict, Field

from dwarpal_api.app import console, passkeys
from dwarpal_api.app.console import ConsoleSession
from dwarpal_api.app.verification import Services, SessionFilter
from dwarpal_api.domain.decision import Outcome
from dwarpal_api.domain.policy import Policy
from dwarpal_api.errors import ApiError
from dwarpal_api.http.deps import services
from dwarpal_api.http.policies import NewVersion
from dwarpal_api.http.webhooks import NewEndpoint, Switch

router = APIRouter(prefix="/console/v1", tags=["console"])
Toolbox = Annotated[Services, Depends(services)]


def cookie_name(svc: Services) -> str:
    # The __Host- prefix makes browsers insist on Secure, path / and no Domain: no other site can set or read it.
    return "__Host-dwarpal_session" if svc.settings.console_cookie_secure else "dwarpal_session"


def check_origin(request: Request, svc: Services) -> None:
    origin = request.headers.get("origin")
    if origin is not None and origin not in svc.settings.console_origins:
        raise ApiError(403, "bad_origin", "this request didn't come from the console")


async def signed_in(request: Request, svc: Toolbox) -> tuple[str, ConsoleSession]:
    token = request.cookies.get(cookie_name(svc), "")
    current = await console.session_of(svc, token)
    if current is None:
        raise ApiError(401, "not_signed_in", "sign in to the console")
    return token, current


async def changing(
    request: Request,
    svc: Toolbox,
    session: Annotated[tuple[str, ConsoleSession], Depends(signed_in)],
    csrf: Annotated[str, Header(alias="X-CSRF-Token")] = "",
) -> ConsoleSession:
    """A signed-in request that changes something: it must repeat the session's CSRF token, which another site's page
    can't read, so it can't forge the request even though the browser would send the cookie."""
    check_origin(request, svc)
    current = session[1]
    if not hmac.compare_digest(csrf.encode(), current.csrf.encode()):
        raise ApiError(403, "csrf_failed", "missing or wrong X-CSRF-Token")
    return current


async def reading(session: Annotated[tuple[str, ConsoleSession], Depends(signed_in)]) -> ConsoleSession:
    return session[1]


Reader = Annotated[ConsoleSession, Depends(reading)]
Changer = Annotated[ConsoleSession, Depends(changing)]


def give_cookie(response: Response, svc: Services, token: str) -> None:
    secure = svc.settings.console_cookie_secure
    max_age = svc.settings.console_session_ttl_s
    response.set_cookie(
        cookie_name(svc), token, max_age=max_age, httponly=True, secure=secure, samesite="lax", path="/"
    )


class SignUp(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: Annotated[str, Field(max_length=254)]
    password: Annotated[str, Field(max_length=256)]
    organisation: Annotated[str, Field(min_length=1, max_length=120)]


class SignIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: Annotated[str, Field(max_length=254)]
    password: Annotated[str, Field(max_length=256)]
    # A 6-digit code from the phone, or one of the recovery codes (abcde-fghij, capitals and spaces allowed).
    code: Annotated[str | None, Field(pattern=r"^([0-9]{6}|[A-Za-z2-7]{5}[- ]?[A-Za-z2-7]{5})$")] = None


class Code(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: Annotated[str, Field(pattern=r"^[0-9]{6}$")]


class Reauthentication(BaseModel):
    """The password and a current code: proof that the person, not just their browser, is asking."""

    model_config = ConfigDict(extra="forbid")

    password: Annotated[str, Field(max_length=256)]
    code: Annotated[str, Field(pattern=r"^[0-9]{6}$")]


Base64Url = Annotated[str, Field(min_length=1, max_length=4096, pattern=r"^[A-Za-z0-9_-]+$")]


class NewPasskey(BaseModel):
    """A device's answer to `navigator.credentials.create`, with the password (and a current code, if one-time codes
    are on): adding a way in needs more than a signed-in browser."""

    model_config = ConfigDict(extra="forbid")

    name: Annotated[str, Field(min_length=1, max_length=60)]
    client_data_json: Base64Url
    attestation_object: Base64Url
    password: Annotated[str, Field(max_length=256)]
    code: Annotated[str | None, Field(pattern=r"^[0-9]{6}$")] = None


class PasskeySignIn(BaseModel):
    """A device's answer to `navigator.credentials.get`."""

    model_config = ConfigDict(extra="forbid")

    id: Base64Url
    client_data_json: Base64Url
    authenticator_data: Base64Url
    signature: Base64Url
    user_handle: Base64Url | None = None


class NewMember(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: Annotated[str, Field(max_length=254)]
    role: Annotated[str, Field(max_length=16)]


class RoleChange(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Annotated[str, Field(max_length=16)]


class NewKey(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scopes: Annotated[list[str], Field(min_length=1, max_length=8)]
    livemode: bool = False


@router.post("/signup", status_code=201)
async def sign_up(body: SignUp, request: Request, response: Response, svc: Toolbox) -> dict[str, Any]:
    check_origin(request, svc)
    token, current = await console.sign_up(svc, body.email, body.password, body.organisation)
    give_cookie(response, svc, token)
    return await console.me(svc, current)


@router.post("/login")
async def sign_in(body: SignIn, request: Request, response: Response, svc: Toolbox) -> dict[str, Any]:
    check_origin(request, svc)
    address = request.client.host if request.client else "unknown"
    token, current = await console.sign_in(svc, body.email, body.password, body.code, address)
    give_cookie(response, svc, token)
    return await console.me(svc, current)


@router.post("/passkey-login/options")
async def passkey_sign_in_options(request: Request, svc: Toolbox) -> dict[str, Any]:
    check_origin(request, svc)
    return await passkeys.sign_in_options(svc, request.client.host if request.client else "unknown")


@router.post("/passkey-login")
async def passkey_sign_in(body: PasskeySignIn, request: Request, response: Response, svc: Toolbox) -> dict[str, Any]:
    check_origin(request, svc)
    address = request.client.host if request.client else "unknown"
    token, current = await passkeys.sign_in(
        svc, body.id, body.client_data_json, body.authenticator_data, body.signature, body.user_handle, address
    )
    give_cookie(response, svc, token)
    return await console.me(svc, current)


@router.post("/logout", status_code=204)
async def sign_out(
    svc: Toolbox,
    _: Changer,
    session: Annotated[tuple[str, ConsoleSession], Depends(signed_in)],
) -> Response:
    await console.close_session(svc, session[0])
    response = Response(status_code=204)
    response.delete_cookie(cookie_name(svc), path="/", secure=svc.settings.console_cookie_secure, httponly=True)
    return response


@router.get("/me")
async def me(current: Reader, svc: Toolbox) -> dict[str, Any]:
    return await console.me(svc, current)


@router.get("/model")
async def model(current: Reader, svc: Toolbox) -> dict[str, Any]:
    """The age model now deciding — for anyone signed in, whatever their organisation."""
    return console.model_information(svc)


@router.post("/totp")
async def totp_enrol(current: Changer, svc: Toolbox) -> dict[str, Any]:
    return await console.totp_enrol(svc, current)


@router.post("/totp/confirm")
async def totp_confirm(body: Code, current: Changer, svc: Toolbox) -> dict[str, Any]:
    return await console.totp_confirm(svc, current, body.code)


@router.post("/totp/recovery-codes")
async def replace_recovery_codes(current: Changer, svc: Toolbox) -> dict[str, Any]:
    return await console.replace_recovery_codes(svc, current)


@router.post("/totp/disable", status_code=204)
async def totp_disable(body: Reauthentication, request: Request, current: Changer, svc: Toolbox) -> Response:
    address = request.client.host if request.client else "unknown"
    await console.totp_disable(svc, current, body.password, body.code, address)
    return Response(status_code=204)


@router.get("/passkeys")
async def list_passkeys(current: Reader, svc: Toolbox) -> dict[str, Any]:
    return await passkeys.list_passkeys(svc, current)


@router.post("/passkeys/options")
async def passkey_options(current: Changer, svc: Toolbox) -> dict[str, Any]:
    return await passkeys.registration_options(svc, current)


@router.post("/passkeys", status_code=201)
async def add_passkey(body: NewPasskey, request: Request, current: Changer, svc: Toolbox) -> dict[str, Any]:
    address = request.client.host if request.client else "unknown"
    return await passkeys.register(
        svc, current, body.name, body.client_data_json, body.attestation_object, body.password, body.code, address
    )


@router.delete("/passkeys/{passkey_text}", status_code=204)
async def remove_passkey(passkey_text: str, current: Changer, svc: Toolbox) -> Response:
    await passkeys.remove(svc, current, passkey_text)
    return Response(status_code=204)


@router.get("/orgs/{org_text}/members")
async def list_members(org_text: str, current: Reader, svc: Toolbox) -> dict[str, Any]:
    return await console.list_members(svc, current, org_text)


@router.get("/orgs/{org_text}/projects")
async def list_projects(org_text: str, current: Reader, svc: Toolbox) -> dict[str, Any]:
    return await console.list_projects(svc, current, org_text)


@router.post("/orgs/{org_text}/members", status_code=201)
async def add_member(org_text: str, body: NewMember, current: Changer, svc: Toolbox) -> dict[str, Any]:
    return await console.add_member(svc, current, org_text, body.email, body.role)


@router.patch("/orgs/{org_text}/members/{user_text}")
async def change_role(
    org_text: str, user_text: str, body: RoleChange, current: Changer, svc: Toolbox
) -> dict[str, Any]:
    return await console.change_role(svc, current, org_text, user_text, body.role)


@router.delete("/orgs/{org_text}/members/{user_text}", status_code=204)
async def remove_member(org_text: str, user_text: str, current: Changer, svc: Toolbox) -> Response:
    await console.remove_member(svc, current, org_text, user_text)
    return Response(status_code=204)


@router.post("/orgs/{org_text}/projects/{project_text}/keys", status_code=201)
async def create_key(org_text: str, project_text: str, body: NewKey, current: Changer, svc: Toolbox) -> dict[str, Any]:
    return await console.create_key(svc, current, org_text, project_text, body.scopes, body.livemode)


@router.get("/orgs/{org_text}/audit")
async def audit_log(
    org_text: str, current: Reader, svc: Toolbox, limit: Annotated[int, Query(ge=1, le=500)] = 100
) -> dict[str, Any]:
    return await console.audit_log(svc, current, org_text, limit)


PROJECT = "/orgs/{org_text}/projects/{project_text}"
Live = Annotated[bool, Query()]


@router.get(PROJECT + "/sessions")
async def project_sessions(
    org_text: str,
    project_text: str,
    current: Reader,
    svc: Toolbox,
    livemode: Live = False,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    starting_after: Annotated[str | None, Query(max_length=64)] = None,
    outcome: Annotated[Outcome | None, Query()] = None,
    external_ref: Annotated[str | None, Query(max_length=200)] = None,
) -> dict[str, Any]:
    only = SessionFilter(outcome, external_ref)
    return await console.project_sessions(svc, current, org_text, project_text, livemode, limit, starting_after, only)


@router.get(PROJECT + "/sessions/{session_text}")
async def session_trace(
    org_text: str, project_text: str, session_text: str, current: Reader, svc: Toolbox
) -> dict[str, Any]:
    return await console.session_trace(svc, current, org_text, project_text, session_text)


@router.get(PROJECT + "/analytics")
async def project_analytics(
    org_text: str,
    project_text: str,
    current: Reader,
    svc: Toolbox,
    livemode: Live = False,
    days: Annotated[int, Query(ge=1, le=365)] = 30,
) -> dict[str, Any]:
    return await console.project_analytics(svc, current, org_text, project_text, livemode, days)


@router.get(PROJECT + "/policies")
async def project_policies(org_text: str, project_text: str, current: Reader, svc: Toolbox) -> dict[str, Any]:
    return await console.project_policies(svc, current, org_text, project_text)


@router.post(PROJECT + "/policies", status_code=201)
async def add_policy_version(
    org_text: str, project_text: str, body: NewVersion, current: Changer, svc: Toolbox
) -> dict[str, Any]:
    draft = Policy(body.name, body.min_age, body.risk_budget, body.max_face_attempts, body.token_ttl_s)
    return await console.add_policy_version(svc, current, org_text, project_text, draft)


class ConsoleEndpoint(NewEndpoint):
    """A new endpoint as the website API takes it, plus the mode: a website's key carries it, a person chooses it."""

    livemode: bool = False


@router.get(PROJECT + "/webhooks")
async def project_webhooks(
    org_text: str, project_text: str, current: Reader, svc: Toolbox, livemode: Live = False
) -> dict[str, Any]:
    return await console.project_webhooks(svc, current, org_text, project_text, livemode)


@router.post(PROJECT + "/webhooks", status_code=201)
async def add_webhook(
    org_text: str, project_text: str, body: ConsoleEndpoint, current: Changer, svc: Toolbox
) -> dict[str, Any]:
    return await console.add_webhook(svc, current, org_text, project_text, body.livemode, body.url, body.events)


@router.delete(PROJECT + "/webhooks/{endpoint_text}", status_code=204)
async def remove_webhook(
    org_text: str, project_text: str, endpoint_text: str, current: Changer, svc: Toolbox, livemode: Live = False
) -> Response:
    await console.remove_webhook(svc, current, org_text, project_text, livemode, endpoint_text)
    return Response(status_code=204)


@router.patch(PROJECT + "/webhooks/{endpoint_text}")
async def switch_webhook(
    org_text: str,
    project_text: str,
    endpoint_text: str,
    body: Switch,
    current: Changer,
    svc: Toolbox,
    livemode: Live = False,
) -> dict[str, Any]:
    return await console.switch_webhook(svc, current, org_text, project_text, livemode, endpoint_text, body.enabled)


@router.post(PROJECT + "/webhooks/{endpoint_text}/test", status_code=202)
async def send_test_event(
    org_text: str, project_text: str, endpoint_text: str, current: Changer, svc: Toolbox, livemode: Live = False
) -> dict[str, Any]:
    return await console.send_test_event(svc, current, org_text, project_text, livemode, endpoint_text)


@router.get(PROJECT + "/webhooks/{endpoint_text}/deliveries")
async def webhook_deliveries(
    org_text: str, project_text: str, endpoint_text: str, current: Reader, svc: Toolbox, livemode: Live = False
) -> dict[str, Any]:
    return await console.webhook_deliveries(svc, current, org_text, project_text, livemode, endpoint_text)


@router.post(PROJECT + "/webhook-deliveries/{delivery_text}/replay", status_code=202)
async def replay_delivery(
    org_text: str, project_text: str, delivery_text: str, current: Changer, svc: Toolbox, livemode: Live = False
) -> dict[str, Any]:
    return await console.replay_delivery(svc, current, org_text, project_text, livemode, delivery_text)
