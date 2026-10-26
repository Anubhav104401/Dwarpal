"""Every error leaves the API in one shape, RFC 9457 "problem details", tagged with the request's ID."""

from __future__ import annotations

import logging
import re
import secrets
import time
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from redis.exceptions import ConnectionError as ValkeyDown
from redis.exceptions import TimeoutError as ValkeySlow
from sqlalchemy.exc import DBAPIError, InterfaceError, OperationalError
from starlette.datastructures import Headers, MutableHeaders
from starlette.exceptions import HTTPException
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from dwarpal_api.errors import ApiError

SAFE_REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{8,64}$")
logger = logging.getLogger("dwarpal.api")


class Problem(BaseModel):
    """The shape of every refusal (RFC 9457), described once so the published API document can show it."""

    type: str
    title: str
    status: int
    detail: str
    code: str
    request_id: str


# The refusals any operation may answer with, each as application/problem+json; the API document lists them all.
REFUSALS = {
    400: "the request is malformed",
    401: "missing or wrong credentials",
    403: "the credentials don't allow this",
    404: "no such thing",
    405: "the method isn't allowed here",
    409: "it conflicts with the current state",
    413: "the body is too large",
    422: "the request makes no sense",
    429: "too many requests; see Retry-After",
    503: "a dependency is unavailable; try again",
}
PROBLEM_RESPONSES: dict[int | str, dict[str, Any]] = {
    status: {
        "description": description,
        "content": {"application/problem+json": {"schema": {"$ref": "#/components/schemas/Problem"}}},
    }
    for status, description in REFUSALS.items()
}


def problem(
    request: Request, status: int, code: str, detail: str, headers: dict[str, str] | None = None
) -> JSONResponse:
    body = {
        "type": f"/errors/{code}",
        "title": code.replace("_", " "),
        "status": status,
        "detail": detail,
        "code": code,
        "request_id": request.state.request_id,
    }
    return JSONResponse(body, status_code=status, media_type="application/problem+json", headers=headers)


async def on_unexpected(request: Request, error: Exception) -> Response:
    logger.error("unexpected %s", type(error).__name__, exc_info=error, extra={"request_id": request.state.request_id})
    return problem(request, 500, "internal_error", "something went wrong on our side; please try again")


# A database or Valkey that can't be reached. Nothing can be decided without them, so nothing is: the caller is told
# to try again shortly (503), and no check can pass by accident.
DEPENDENCY_FAILURES = (ValkeyDown, ValkeySlow, OperationalError, InterfaceError, ConnectionError, TimeoutError)
RETRY_AFTER_S = "5"


async def on_dependency_down(request: Request, error: Exception) -> Response:
    logger.warning("dependency unavailable: %s", type(error).__name__, extra={"request_id": request.state.request_id})
    detail = "a service Dwarpal depends on is unavailable; try again shortly"
    return problem(request, 503, "service_unavailable", detail, {"Retry-After": RETRY_AFTER_S})


# PostgreSQL can't store some characters in text — above all NUL (U+0000), which JSON and addresses can carry. When
# it refuses one, the request was at fault, not the server: one answer for every route, instead of a 500.
UNSTORABLE_TEXT = {"22021", "22P05"}  # character_not_in_repertoire, untranslatable_character


async def on_database_error(request: Request, error: Exception) -> Response:
    if isinstance(error, DBAPIError) and getattr(error.orig, "sqlstate", None) in UNSTORABLE_TEXT:
        return problem(request, 422, "invalid_text", "text may not contain the NUL character (or other control bytes)")
    return await on_unexpected(request, error)


async def on_api_error(request: Request, error: Exception) -> Response:
    if not isinstance(error, ApiError):
        return await on_unexpected(request, error)
    return problem(request, error.status, error.code, error.detail, error.headers)


async def on_invalid_request(request: Request, error: Exception) -> Response:
    if not isinstance(error, RequestValidationError):
        return await on_unexpected(request, error)
    fields = sorted({".".join(str(part) for part in item["loc"][1:]) or "body" for item in error.errors()})
    return problem(request, 422, "invalid_request", "invalid or missing: " + ", ".join(fields))


async def on_http_error(request: Request, error: Exception) -> Response:
    if not isinstance(error, HTTPException):
        return await on_unexpected(request, error)
    headers = dict(error.headers or {})
    if error.status_code == 405:
        # HTTP requires a 405 to list every method the address accepts. Starlette names only those of the first route
        # it tried, so when GET and POST are two routes on one path, the list is gathered from all of them.
        headers["Allow"] = ", ".join(allowed_methods(request))
    return problem(request, error.status_code, "http_error", str(error.detail), headers)


def allowed_methods(request: Request) -> list[str]:
    methods: set[str] = set()
    for route in request.app.routes:
        pattern, route_methods = getattr(route, "path_regex", None), getattr(route, "methods", None)
        if pattern is not None and route_methods and pattern.match(request.url.path):
            methods |= set(route_methods)
    return sorted(methods)


class RequestIds:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        offered = Headers(scope=scope).get("x-request-id", "")
        request_id = offered if SAFE_REQUEST_ID.match(offered) else f"req_{secrets.token_hex(8)}"
        scope.setdefault("state", {})["request_id"] = request_id
        started, status = time.perf_counter(), 500

        async def send_tagged(message: Message) -> None:
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
                MutableHeaders(scope=message).append("X-Request-Id", request_id)
            await send(message)

        try:
            await self.app(scope, receive, send_tagged)
        finally:
            elapsed = round((time.perf_counter() - started) * 1000, 1)
            fields = {"request_id": request_id, "method": scope["method"], "path": scope["path"], "status": status}
            logger.info("request", extra={**fields, "duration_ms": elapsed})


def describe_problems(app: FastAPI) -> None:
    """Add the Problem shape to the API document FastAPI builds, so that every refusal listed there has a schema."""
    build = app.openapi

    def openapi() -> dict[str, Any]:
        document = build()  # FastAPI builds the document once, then hands back the same one
        document.setdefault("components", {}).setdefault("schemas", {}).setdefault(
            "Problem", Problem.model_json_schema()
        )
        return document

    app.openapi = openapi  # type: ignore[method-assign]


def install(app: FastAPI) -> None:
    describe_problems(app)
    app.add_middleware(RequestIds)
    app.add_exception_handler(ApiError, on_api_error)
    app.add_exception_handler(RequestValidationError, on_invalid_request)
    app.add_exception_handler(HTTPException, on_http_error)
    app.add_exception_handler(DBAPIError, on_database_error)  # the dependency failures below are more specific
    for failure in DEPENDENCY_FAILURES:
        app.add_exception_handler(failure, on_dependency_down)
    app.add_exception_handler(Exception, on_unexpected)
