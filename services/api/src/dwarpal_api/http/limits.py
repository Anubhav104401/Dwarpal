"""Size limits on request bodies, enforced from the headers before a single byte of the body is read."""

from __future__ import annotations

from starlette.requests import Request
from starlette.types import ASGIApp, Receive, Scope, Send

from dwarpal_api.http.problems import problem
from dwarpal_contracts import MAX_DOCUMENT_BYTES, MAX_FRAME_BYTES, MAX_FRAMES

JSON_LIMIT = 64 * 1024
UPLOAD_LIMIT = MAX_FRAMES * MAX_FRAME_BYTES + 64 * 1024
# The uploads, by the end of their path: a face attempt's frames, and a document check's frames and photo (Phase 6).
UPLOAD_LIMITS = {"/face-attempts": UPLOAD_LIMIT, "/stepup/mrz": UPLOAD_LIMIT + MAX_DOCUMENT_BYTES}


class BodyLimit:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            headers = dict(scope["headers"])
            path: str = scope["path"]
            limit = next((size for end, size in UPLOAD_LIMITS.items() if path.endswith(end)), JSON_LIMIT)
            declared = headers.get(b"content-length", b"0")
            refusal = None
            if b"transfer-encoding" in headers:
                refusal = problem(Request(scope), 411, "length_required", "send the body with a Content-Length header")
            elif not declared.isdigit() or int(declared) > limit:
                refusal = problem(Request(scope), 413, "request_too_large", f"the body must be at most {limit} bytes")
            if refusal is not None:
                await refusal(scope, receive, send)
                return
        await self.app(scope, receive, send)
