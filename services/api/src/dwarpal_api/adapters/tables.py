"""The database tables, described as Python classes. No table has a column that could hold an image."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    LargeBinary,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from dwarpal_api.adapters.db import Base

Timestamp = DateTime(timezone=True)


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    slug: Mapped[str] = mapped_column(String(60), unique=True)
    created_at: Mapped[datetime] = mapped_column(Timestamp)


class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (CheckConstraint("retention_days BETWEEN 1 AND 365", name="ck_projects_retention_days"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    allowed_origins: Mapped[list[str]] = mapped_column(ARRAY(Text))
    # How many days a session's metadata is kept before the purge removes it (1 to 365; 90 by default).
    retention_days: Mapped[int] = mapped_column(default=90)
    created_at: Mapped[datetime] = mapped_column(Timestamp)


class ApiKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    livemode: Mapped[bool]
    lookup: Mapped[str] = mapped_column(String(16), unique=True)
    secret_digest: Mapped[bytes] = mapped_column(LargeBinary(32))
    name: Mapped[str] = mapped_column(String(120))
    # The operations the key may perform (domain/keys.py, SCOPES).
    scopes: Mapped[list[str]] = mapped_column(ARRAY(Text))
    created_at: Mapped[datetime] = mapped_column(Timestamp)
    # When a rotated key stops working; None for a key that hasn't been rotated.
    expires_at: Mapped[datetime | None] = mapped_column(Timestamp)
    revoked_at: Mapped[datetime | None] = mapped_column(Timestamp)


class VerificationSession(Base):
    __tablename__ = "verification_sessions"
    # A project's sessions, newest first, for the paginated list (UUIDv7s sort by the time they were made); and every
    # project's sessions by age, for the retention purge.
    __table_args__ = (
        Index("ix_verification_sessions_project_id_id", "project_id", "id"),
        Index("ix_verification_sessions_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    livemode: Mapped[bool]
    policy_id: Mapped[str] = mapped_column(String(40))
    # Which version of the policy the session follows: 0 for a preset, else a row of `policies`.
    policy_version: Mapped[int]
    status: Mapped[str] = mapped_column(String(24))
    outcome: Mapped[str | None] = mapped_column(String(16))
    client_secret_digest: Mapped[bytes] = mapped_column(LargeBinary(32))
    return_url: Mapped[str | None] = mapped_column(Text)
    external_ref: Mapped[str | None] = mapped_column(String(200))
    attempts_count: Mapped[int]
    model_version: Mapped[str | None] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(Timestamp)
    started_at: Mapped[datetime | None] = mapped_column(Timestamp)  # when the person first opened the verify page
    expires_at: Mapped[datetime] = mapped_column(Timestamp)
    completed_at: Mapped[datetime | None] = mapped_column(Timestamp)


class PolicyVersion(Base):
    """One version of a project's custom policy. Never changed once made: a new version is a new row."""

    __tablename__ = "policies"
    __table_args__ = (UniqueConstraint("project_id", "name", "version", name="uq_policies_project_id_name_version"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(40))
    version: Mapped[int]
    min_age: Mapped[int]
    risk_budget: Mapped[float] = mapped_column(Float)
    max_face_attempts: Mapped[int]
    token_ttl_s: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(Timestamp)


class VerificationAttempt(Base):
    __tablename__ = "verification_attempts"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("verification_sessions.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[str] = mapped_column(String(16))
    outcome: Mapped[str] = mapped_column(String(16))
    reasons: Mapped[list[str]] = mapped_column(ARRAY(Text))
    scores: Mapped[dict[str, Any]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(Timestamp)


class SigningKey(Base):
    __tablename__ = "signing_keys"

    kid: Mapped[str] = mapped_column(String(40), primary_key=True)
    public_jwk: Mapped[dict[str, Any]] = mapped_column(JSONB)
    private_key_sealed: Mapped[bytes] = mapped_column(LargeBinary)
    status: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(Timestamp)


class IssuedToken(Base):
    __tablename__ = "issued_tokens"

    jti: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("verification_sessions.id", ondelete="CASCADE"), index=True
    )
    audience: Mapped[str] = mapped_column(String(40))
    issued_at: Mapped[datetime] = mapped_column(Timestamp)
    expires_at: Mapped[datetime] = mapped_column(Timestamp)
    # When a website asked Dwarpal to check this token (/v1/tokens/introspect); a token can be introspected once.
    introspected_at: Mapped[datetime | None] = mapped_column(Timestamp)


class WebhookEndpoint(Base):
    """A website's address for notifications, with the secret that signs them (sealed under the master key)."""

    __tablename__ = "webhook_endpoints"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    livemode: Mapped[bool]
    url: Mapped[str] = mapped_column(Text)
    secret_sealed: Mapped[bytes] = mapped_column(LargeBinary)
    events: Mapped[list[str]] = mapped_column(ARRAY(Text))
    enabled: Mapped[bool]
    created_at: Mapped[datetime] = mapped_column(Timestamp)


class Event(Base):
    """Something that happened to a project's sessions, as it was at that moment. Never changed once written."""

    __tablename__ = "events"
    __table_args__ = (Index("ix_events_project_id_id", "project_id", "id"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    livemode: Mapped[bool]
    type: Mapped[str] = mapped_column(String(60))
    data: Mapped[dict[str, Any]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(Timestamp)


class WebhookDelivery(Base):
    """One event on its way to one endpoint: the transactional outbox the delivery worker empties."""

    __tablename__ = "webhook_deliveries"
    __table_args__ = (
        Index("ix_webhook_deliveries_due", "next_attempt_at", postgresql_where=text("status = 'pending'")),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    endpoint_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("webhook_endpoints.id", ondelete="CASCADE"), index=True)
    event_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String(16))  # pending, delivered or dead
    attempt: Mapped[int]  # how many times it has been sent so far
    next_attempt_at: Mapped[datetime] = mapped_column(Timestamp)
    last_status: Mapped[int | None]  # the receiver's last HTTP status, if it answered
    last_error: Mapped[str | None] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(Timestamp)
    delivered_at: Mapped[datetime | None] = mapped_column(Timestamp)


class AuditHead(Base):
    """The newest link of one organisation's audit chain. Locking it serialises that organisation's appends."""

    __tablename__ = "audit_heads"

    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), primary_key=True)
    last_seq: Mapped[int] = mapped_column(BigInteger)
    last_hash: Mapped[bytes] = mapped_column(LargeBinary(32))


class AuditEntry(Base):
    """One thing someone did, chained to the entry before it by `prev_hash`. Never changed once written."""

    __tablename__ = "audit_log"

    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), primary_key=True)
    seq: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    actor_type: Mapped[str] = mapped_column(String(16))  # api_key or operator
    actor_id: Mapped[str] = mapped_column(String(64))
    action: Mapped[str] = mapped_column(String(60))
    target: Mapped[str] = mapped_column(String(80))
    data: Mapped[dict[str, Any]] = mapped_column(JSONB)
    prev_hash: Mapped[bytes] = mapped_column(LargeBinary(32))
    hash: Mapped[bytes] = mapped_column(LargeBinary(32))
    created_at: Mapped[datetime] = mapped_column(Timestamp)


class SessionStat(Base):
    """How many sessions of one project ended one way, on one day, under one policy. Kept after the purge."""

    __tablename__ = "session_stats"

    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True)
    livemode: Mapped[bool] = mapped_column(primary_key=True)
    day: Mapped[date] = mapped_column(primary_key=True)
    policy: Mapped[str] = mapped_column(String(60), primary_key=True)
    outcome: Mapped[str] = mapped_column(String(16), primary_key=True)
    sessions: Mapped[int]


class FaceStageStat(Base):
    """How many of one project's face checks reached one decision on one day, within one band of time (`from_s`
    seconds or more, up to the next band). Kept after the purge."""

    __tablename__ = "face_stage_stats"

    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True)
    livemode: Mapped[bool] = mapped_column(primary_key=True)
    day: Mapped[date] = mapped_column(primary_key=True)
    outcome: Mapped[str] = mapped_column(String(16), primary_key=True)
    from_s: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    sessions: Mapped[int]


class User(Base):
    """A person at one of Dwarpal's customers, who signs in to the console. Never someone whose age is checked."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)  # stored in lower case
    password_hash: Mapped[str] = mapped_column(Text)  # Argon2id, with its salt and settings inside
    totp_secret_sealed: Mapped[bytes | None] = mapped_column(LargeBinary)  # one-time codes, once switched on
    totp_pending_sealed: Mapped[bytes | None] = mapped_column(LargeBinary)  # a secret offered but not yet confirmed
    totp_last_step: Mapped[int | None] = mapped_column(BigInteger)  # the last code used, so it can't be used again
    recovery_digests: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)  # HMACs of unused recovery codes
    created_at: Mapped[datetime] = mapped_column(Timestamp)
    last_login_at: Mapped[datetime | None] = mapped_column(Timestamp)


class Membership(Base):
    """A user's role in an organisation: owner, admin, developer or analyst (domain/roles.py)."""

    __tablename__ = "memberships"
    __table_args__ = (
        CheckConstraint("role IN ('owner', 'admin', 'developer', 'analyst')", name="ck_memberships_role"),
    )

    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, index=True)
    role: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(Timestamp)


METADATA = Base.metadata
