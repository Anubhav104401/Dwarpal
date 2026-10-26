"""Passwords, hashed with Argon2id: slow and memory-hungry on purpose, so stolen hashes are costly to crack."""

from __future__ import annotations

import asyncio

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

# argon2-cffi's defaults follow RFC 9106's second recommendation: 3 passes over 64 MiB, 4 lanes; about 50 ms here.
HASHER = PasswordHasher()
# Checked when an e-mail address is unknown, so that answering takes as long as for a real account.
DECOY = HASHER.hash("a password nobody has; checked so that unknown accounts take as long as real ones")


async def hash_password(password: str) -> str:
    # In a worker thread: 50 ms of hashing would otherwise stop every other request on the server.
    return await asyncio.to_thread(HASHER.hash, password)


async def verify_password(stored: str | None, password: str) -> bool:
    """Whether `password` matches the stored hash. With no account (None), check the decoy and answer False."""

    def check() -> bool:
        try:
            return HASHER.verify(stored or DECOY, password) and stored is not None
        except (VerificationError, InvalidHashError):
            return False

    return await asyncio.to_thread(check)
