"""How a database error becomes an answer: the request's fault, the dependency's absence, or a real fault."""

from __future__ import annotations

import pytest
from sqlalchemy.exc import DBAPIError
from starlette.requests import Request

from dwarpal_api.http import problems


class DriverError(Exception):
    """What the database driver raises, carrying PostgreSQL's five-character error code."""

    def __init__(self, sqlstate: str) -> None:
        super().__init__(sqlstate)
        self.sqlstate = sqlstate


def a_request() -> Request:
    request = Request({"type": "http", "method": "GET", "path": "/", "headers": [], "query_string": b""})
    request.state.request_id = "req_test"
    return request


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("sqlstate", "status"),
    [
        ("22021", 422),  # text the database can't store: the request's fault
        ("57P01", 503),  # the server is shutting down (found by stopping PostgreSQL under load)
        ("08003", 503),  # the connection is gone
        ("42P01", 500),  # anything else is a fault of ours, and is said to be one
    ],
)
async def test_a_database_error_is_answered_by_what_caused_it(sqlstate: str, status: int) -> None:
    error = DBAPIError("SELECT 1", {}, DriverError(sqlstate))
    answer = await problems.on_database_error(a_request(), error)
    assert answer.status_code == status
    assert (answer.headers.get("retry-after") == problems.RETRY_AFTER_S) is (status == 503)
