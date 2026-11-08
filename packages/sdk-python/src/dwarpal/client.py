"""The client for Dwarpal's API, for a website's server: create a verification session, and read its result.

Two forms with the same methods: `Client` waits for each answer; `AsyncClient` is for `async` code (FastAPI, aiohttp).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal

import httpx

from dwarpal.errors import DwarpalApiError

SessionStatus = Literal["created", "in_progress", "awaiting_step_up", "completed", "expired", "canceled"]
SessionOutcome = Literal["pass", "fail", "reject", "step_up"]
STATUSES = frozenset({"created", "in_progress", "awaiting_step_up", "completed", "expired", "canceled"})
OUTCOMES = frozenset({"pass", "fail", "reject", "step_up"})
API_KEY = re.compile(r"^dk_(test|live)_[A-Za-z0-9_-]{20,}$")
SESSION_ID = re.compile(r"^vs_[0-9A-Za-z]{26}$")
IDEMPOTENCY_KEY = re.compile(r"^[\x21-\x7e]{8,255}$")  # 8 to 255 printable characters, no spaces


@dataclass(frozen=True)
class CreatedSession:
    id: str
    status: SessionStatus
    livemode: bool
    policy: str
    url: str  # send the person here; the link carries a one-time secret: never log it or store it
    expires_at: datetime


@dataclass(frozen=True)
class SessionResult:
    id: str
    status: SessionStatus
    outcome: SessionOutcome | None
    livemode: bool
    policy: str
    min_age: int
    attempts: int
    external_ref: str | None
    completed_at: datetime | None
    age_token: str | None  # signed, once completed: check it with `verify_age_token` before trusting it


def _field(data: dict[str, Any], key: str, kind: type | tuple[type, ...]) -> Any:
    """One field of the API's answer, of the expected kind; anything else is the API misbehaving, not the caller."""
    value = data.get(key)
    if not isinstance(value, kind) or (kind is int and isinstance(value, bool)):
        raise TypeError(f'the API\'s answer has an unexpected "{key}"')
    return value


def _choice(data: dict[str, Any], key: str, allowed: frozenset[str], optional: bool = False) -> Any:
    value = data.get(key)
    if value is None and optional:
        return None
    if value not in allowed:
        raise TypeError(f'the API\'s answer has an unexpected "{key}"')
    return value


def _when(text: str | None) -> datetime | None:
    return None if text is None else datetime.fromisoformat(text)


def _created(data: dict[str, Any]) -> CreatedSession:
    return CreatedSession(
        id=_field(data, "id", str),
        status=_choice(data, "status", STATUSES),
        livemode=_field(data, "livemode", bool),
        policy=_field(data, "policy", str),
        url=_field(data, "url", str),
        expires_at=datetime.fromisoformat(_field(data, "expires_at", str)),
    )


def _result(data: dict[str, Any]) -> SessionResult:
    return SessionResult(
        id=_field(data, "id", str),
        status=_choice(data, "status", STATUSES),
        outcome=_choice(data, "outcome", OUTCOMES, optional=True),
        livemode=_field(data, "livemode", bool),
        policy=_field(data, "policy", str),
        min_age=_field(data, "min_age", int),
        attempts=_field(data, "attempts", int),
        external_ref=_field(data, "external_ref", (str, type(None))),
        completed_at=_when(_field(data, "completed_at", (str, type(None)))),
        age_token=_field(data, "age_token", (str, type(None))),
    )


def _session_body(policy: str | None, return_url: str | None, external_ref: str | None) -> dict[str, str]:
    body = {"policy": policy, "return_url": return_url, "external_ref": external_ref}
    return {name: value for name, value in body.items() if value is not None}


def _idempotency(key: str | None) -> dict[str, str]:
    """The `Idempotency-Key` header, when a key is given. It makes a retry safe: the same request sent again with the
    same key, after its answer was lost, gets the first session back instead of a second one. Use a fresh random key
    for each new session (`secrets.token_urlsafe(16)`), never an order number or anything another request could
    share."""
    if key is None:
        return {}
    if not IDEMPOTENCY_KEY.fullmatch(key):  # not `match`: `$` would let a final line break through
        raise ValueError("idempotency_key must be 8 to 255 printable characters, without spaces")
    return {"Idempotency-Key": key}


def _session_path(session_id: str) -> str:
    if not SESSION_ID.match(session_id):
        raise ValueError("session_id must be a Dwarpal session ID: vs_ followed by 26 characters")
    return f"/v1/verification-sessions/{session_id}"


def _answer(response: httpx.Response) -> dict[str, Any]:
    """The answer's JSON, or the API's refusal as a `DwarpalApiError` (with its stable code and request ID)."""
    try:
        parsed = response.json()
    except ValueError:
        parsed = None
    data: dict[str, Any] = parsed if isinstance(parsed, dict) else {}
    if response.is_error:
        code = data.get("code") if isinstance(data.get("code"), str) else "http_error"
        detail = (
            data.get("detail") if isinstance(data.get("detail"), str) else f"the API answered {response.status_code}"
        )
        raise DwarpalApiError(response.status_code, str(code), str(detail), response.headers.get("x-request-id"))
    return data


def _headers(api_key: str) -> dict[str, str]:
    if not API_KEY.match(api_key):
        raise ValueError("api_key must be a Dwarpal secret key: dk_test_… or dk_live_…")
    return {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}


class Client:
    """Dwarpal's API, waiting for each answer. Use it on your server only: the key is secret.

    with Client(api_key, base_url="https://api.dwarpal.example") as dwarpal:
        session = dwarpal.create_session(policy="uk_osa_18", return_url="https://shop.example/done")
    """

    def __init__(self, api_key: str, base_url: str, timeout_s: float = 10.0, http: httpx.Client | None = None) -> None:
        self._http = http or httpx.Client(base_url=base_url.rstrip("/"), timeout=timeout_s)
        self._http.headers.update(_headers(api_key))

    def create_session(
        self,
        policy: str | None = None,
        return_url: str | None = None,
        external_ref: str | None = None,
        idempotency_key: str | None = None,
    ) -> CreatedSession:
        """Create a verification session, and get the link to send the person to."""
        body, headers = _session_body(policy, return_url, external_ref), _idempotency(idempotency_key)
        return _created(_answer(self._http.post("/v1/verification-sessions", json=body, headers=headers)))

    def retrieve_session(self, session_id: str) -> SessionResult:
        """Read a session's result. A completed session comes with a freshly signed age token."""
        return _result(_answer(self._http.get(_session_path(session_id))))

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> Client:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


class AsyncClient:
    """Dwarpal's API for `async` code: the same methods as `Client`, awaited."""

    def __init__(
        self, api_key: str, base_url: str, timeout_s: float = 10.0, http: httpx.AsyncClient | None = None
    ) -> None:
        self._http = http or httpx.AsyncClient(base_url=base_url.rstrip("/"), timeout=timeout_s)
        self._http.headers.update(_headers(api_key))

    async def create_session(
        self,
        policy: str | None = None,
        return_url: str | None = None,
        external_ref: str | None = None,
        idempotency_key: str | None = None,
    ) -> CreatedSession:
        body, headers = _session_body(policy, return_url, external_ref), _idempotency(idempotency_key)
        return _created(_answer(await self._http.post("/v1/verification-sessions", json=body, headers=headers)))

    async def retrieve_session(self, session_id: str) -> SessionResult:
        return _result(_answer(await self._http.get(_session_path(session_id))))

    async def aclose(self) -> None:
        await self._http.aclose()

    async def __aenter__(self) -> AsyncClient:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.aclose()
