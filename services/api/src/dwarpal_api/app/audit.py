"""The audit log: who changed what, chained so that no entry can be altered or removed without it showing."""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from dwarpal_api.adapters.tables import AuditEntry, AuditHead

GENESIS = bytes(32)  # the "previous hash" of each organisation's first entry


def canonical(entry: AuditEntry) -> bytes:
    """An entry's facts as one exact byte string: the same entry always gives the same bytes, so the same hash."""
    facts = {
        "org": str(entry.org_id),
        "seq": entry.seq,
        "actor": [entry.actor_type, entry.actor_id],
        "action": entry.action,
        "target": entry.target,
        "data": entry.data,
        "at": entry.created_at.isoformat(),
    }
    return json.dumps(facts, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def link(prev_hash: bytes, entry: AuditEntry) -> bytes:
    """hash_n = SHA-256(hash_n-1 ‖ canonical(entry_n)): each hash depends on every entry before it."""
    return hashlib.sha256(prev_hash + canonical(entry)).digest()


async def record(
    session: AsyncSession,
    org_id: uuid.UUID,
    actor: tuple[str, str],
    action: str,
    target: str,
    data: dict[str, Any],
    now: datetime,
) -> AuditEntry:
    """Append one entry to an organisation's chain, inside the caller's transaction: the change and its record are
    saved together. Locking the organisation's head row makes concurrent appends wait their turn, without one lock
    for everybody."""
    start = insert(AuditHead).values(org_id=org_id, last_seq=0, last_hash=GENESIS).on_conflict_do_nothing()
    await session.execute(start)  # the organisation's first entry: create its head, unless someone just did
    head = await session.scalar(select(AuditHead).where(AuditHead.org_id == org_id).with_for_update())
    if head is None:
        raise RuntimeError("the audit head should exist by now")
    entry = AuditEntry(
        org_id=org_id,
        seq=head.last_seq + 1,
        actor_type=actor[0],
        actor_id=actor[1],
        action=action,
        target=target,
        data=data,
        prev_hash=head.last_hash,
        hash=b"",
        created_at=now,
    )
    entry.hash = link(head.last_hash, entry)
    session.add(entry)
    head.last_seq, head.last_hash = entry.seq, entry.hash
    return entry


@dataclass(frozen=True)
class ChainReport:
    entries: int
    intact: bool
    first_broken: int | None  # the sequence number of the first entry that doesn't check out


async def verify(session: AsyncSession, org_id: uuid.UUID) -> ChainReport:
    """Recompute an organisation's chain from the start. An entry altered, removed or inserted shows as the first
    entry whose numbering or hash no longer follows from the one before; so does a head that doesn't match the end."""
    rows = await session.scalars(select(AuditEntry).where(AuditEntry.org_id == org_id).order_by(AuditEntry.seq))
    prev, expected_seq, count = GENESIS, 1, 0
    for entry in rows:
        count += 1
        if entry.seq != expected_seq or entry.prev_hash != prev or entry.hash != link(prev, entry):
            return ChainReport(count, False, entry.seq)
        prev, expected_seq = entry.hash, entry.seq + 1
    head = await session.get(AuditHead, org_id)
    if head is not None and (head.last_seq != expected_seq - 1 or head.last_hash != prev):
        return ChainReport(count, False, expected_seq)  # entries were removed from the end
    return ChainReport(count, True, None)
