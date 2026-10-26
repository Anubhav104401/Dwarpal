"""The console API: what Dwarpal's own web console calls on behalf of a signed-in person. A session lives in a cookie;
every change must also carry the session's CSRF token, and come from one of the console's own origins."""

from __future__ import annotations

import hmac
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, Query, Request, Response
from pydantic import BaseModel, ConfigDict, Field

from dwarpal_api.app import console
from dwarpal_api.app.console import ConsoleSession
from dwarpal_api.app.verification import Services
from dwarpal_api.errors import ApiError
from dwarpal_api.http.deps import services

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
    code: Annotated[str | None, Field(pattern=r"^[0-9]{6}$")] = None


class Code(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: Annotated[str, Field(pattern=r"^[0-9]{6}$")]


class NewMember(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: Annotated[str, Field(max_length=254)]
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


@router.post("/totp")
async def totp_enrol(current: Changer, svc: Toolbox) -> dict[str, Any]:
    return await console.totp_enrol(svc, current)


@router.post("/totp/confirm", status_code=204)
async def totp_confirm(body: Code, current: Changer, svc: Toolbox) -> Response:
    await console.totp_confirm(svc, current, body.code)
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


@router.post("/orgs/{org_text}/projects/{project_text}/keys", status_code=201)
async def create_key(org_text: str, project_text: str, body: NewKey, current: Changer, svc: Toolbox) -> dict[str, Any]:
    return await console.create_key(svc, current, org_text, project_text, body.scopes, body.livemode)


@router.get("/orgs/{org_text}/audit")
async def audit_log(
    org_text: str, current: Reader, svc: Toolbox, limit: Annotated[int, Query(ge=1, le=500)] = 100
) -> dict[str, Any]:
    return await console.audit_log(svc, current, org_text, limit)
