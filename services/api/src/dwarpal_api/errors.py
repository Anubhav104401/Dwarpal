"""The one kind of error the API's own code raises on purpose: a refusal with a status, a stable code and a reason."""

from __future__ import annotations


class ApiError(Exception):
    def __init__(self, status: int, code: str, detail: str) -> None:
        super().__init__(detail)
        self.status = status
        self.code = code
        self.detail = detail
