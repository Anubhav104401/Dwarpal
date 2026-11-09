"""The console's rules without a database: the role matrix, one-time codes (against RFC 6238's own test values), and
password hashing."""

from __future__ import annotations

import base64

import pytest

from dwarpal_api.adapters.passwords import hash_password, verify_password
from dwarpal_api.app.console import lock_s
from dwarpal_api.domain import totp
from dwarpal_api.domain.roles import Action, Role, can

# The design's matrix (§3.4), written out in full: one row per action, one column per role.
MATRIX = {
    Action.DELETE_ORGANISATION: (True, False, False, False),
    Action.MANAGE_MEMBERS: (True, True, False, False),
    Action.MANAGE_PROJECTS: (True, True, False, False),
    Action.READ_AUDIT: (True, True, False, False),
    Action.MANAGE_KEYS: (True, True, True, False),
    Action.MANAGE_WEBHOOKS: (True, True, True, False),
    Action.MANAGE_POLICIES: (True, True, True, False),
    Action.READ_SESSIONS: (True, True, True, True),
    Action.READ_ANALYTICS: (True, True, True, True),
}
ROLES = (Role.OWNER, Role.ADMIN, Role.DEVELOPER, Role.ANALYST)


def test_every_role_may_do_exactly_what_the_matrix_says() -> None:
    assert set(MATRIX) == set(Action)  # no action left out of the table
    for action, allowed in MATRIX.items():
        assert tuple(can(role, action) for role in ROLES) == allowed, action


def test_an_unknown_role_may_do_nothing() -> None:
    assert not any(can("superuser", action) for action in Action)


def test_locks_start_after_the_free_tries_then_double_up_to_the_longest() -> None:
    locks = [lock_s(failures, free=5, first_s=60, longest_s=3600) for failures in range(1, 15)]
    assert locks == [0, 0, 0, 0, 0, 60, 120, 240, 480, 960, 1920, 3600, 3600, 3600], locks
    assert lock_s(10**9, free=5, first_s=60, longest_s=3600) == 3600  # however many, at once and at most the longest


# RFC 6238, appendix B: the SHA-1 key "12345678901234567890" and its 8-digit codes; ours are the last six digits.
RFC_SECRET = base64.b32encode(b"12345678901234567890").decode()
RFC_CODES = {59: "94287082", 1111111109: "07081804", 1111111111: "14050471", 1234567890: "89005924"}


@pytest.mark.parametrize(("unix_s", "code"), RFC_CODES.items())
def test_codes_match_the_standards_own_examples(unix_s: int, code: str) -> None:
    assert totp.code_at(RFC_SECRET, unix_s // totp.STEP_S) == code[-totp.DIGITS :]


def test_a_code_is_accepted_once_near_its_time_and_never_again() -> None:
    secret, now = totp.new_secret(), 1_800_000_000.0
    step = int(now // totp.STEP_S)
    code = totp.code_at(secret, step)
    assert totp.accepted_step(secret, code, now, None) == step
    assert totp.accepted_step(secret, code, now + totp.STEP_S, None) == step  # a phone a little behind
    assert totp.accepted_step(secret, code, now + 3 * totp.STEP_S, None) is None  # too old
    assert totp.accepted_step(secret, code, now, last_step=step) is None  # already used
    assert totp.accepted_step(secret, "12345a", now, None) is None


def test_the_provisioning_address_carries_the_secret_and_the_settings() -> None:
    uri = totp.provisioning_uri("JBSWY3DPEHPK3PXP", "ana@shop.example")
    assert uri.startswith("otpauth://totp/Dwarpal%3Aana%40shop.example?secret=JBSWY3DPEHPK3PXP&")
    assert "digits=6" in uri and "period=30" in uri


@pytest.mark.anyio
async def test_passwords_are_salted_argon2id_and_unknown_accounts_never_match() -> None:
    first, second = await hash_password("correct horse battery"), await hash_password("correct horse battery")
    assert first.startswith("$argon2id$") and first != second  # a fresh salt every time
    assert await verify_password(first, "correct horse battery")
    assert not await verify_password(first, "correct horse battery!")
    assert not await verify_password(None, "anything at all")  # no account: the decoy is checked, and fails
