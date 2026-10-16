"""Every error leaves the API in one shape, RFC 9457 "problem details", tagged with the request's ID."""

from __future__ import annotations

import logging
import re
import secrets
import time

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.datastructures import Headers, MutableHeaders
from starlette.exceptions import HTTPException
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from dwarpal_api.errors import ApiError

SAFE_REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{8,64}$")
logger = logging.getLogger("dwarpal.api")


def problem(request: Request, status: int, code: str, detail: str) -> JSONResponse:
    body = {
        "type": f"/errors/{code}",
        "title": code.replace("_", " "),
        "status": status,
        "detail": detail,
        "code": code,
        "request_id": request.state.request_id,
    }
    return JSONResponse(body, status_code=status, media_type="application/problem+json")


async def on_unexpected(request: Request, error: Exception) -> Response:
    logger.error("unexpected %s", type(error).__name__, exc_info=error, extra={"request_id": request.state.request_id})
    return problem(request, 500, "internal_error", "something went wrong on our side; please try again")


async def on_api_error(request: Request, error: Exception) -> Response:
    if not isinstance(error, ApiError):
        return await on_unexpected(request, error)
    return problem(request, error.status, error.code, error.detail)


async def on_invalid_request(request: Request, error: Exception) -> Response:
    if not isinstance(error, RequestValidationError):
        return await on_unexpected(request, error)
    fields = sorted({".".join(str(part) for part in item["loc"][1:]) or "body" for item in error.errors()})
    return problem(request, 422, "invalid_request", "invalid or missing: " + ", ".join(fields))


async def on_http_error(request: Request, error: Exception) -> Response:
    if not isinstance(error, HTTPException):
        return await on_unexpected(request, error)
    return problem(request, error.status_code, "http_error", str(error.detail))


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


def install(app: FastAPI) -> None:
    app.add_middleware(RequestIds)
    app.add_exception_handler(ApiError, on_api_error)
    app.add_exception_handler(RequestValidationError, on_invalid_request)
    app.add_exception_handler(HTTPException, on_http_error)
    app.add_exception_handler(Exception, on_unexpected)
