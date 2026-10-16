"""The database tables, described as Python classes. No table has a column that could hold an image."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, LargeBinary, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from dwarpal_api.adapters.db import Base

Timestamp = DateTime(timezone=True)


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    allowed_origins: Mapped[list[str]] = mapped_column(ARRAY(Text))
    created_at: Mapped[datetime] = mapped_column(Timestamp)


class ApiKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    livemode: Mapped[bool]
    lookup: Mapped[str] = mapped_column(String(16), unique=True)
    secret_digest: Mapped[bytes] = mapped_column(LargeBinary(32))
    name: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(Timestamp)
    revoked_at: Mapped[datetime | None] = mapped_column(Timestamp)


class VerificationSession(Base):
    __tablename__ = "verification_sessions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    livemode: Mapped[bool]
    policy_id: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(24))
    outcome: Mapped[str | None] = mapped_column(String(16))
    client_secret_digest: Mapped[bytes] = mapped_column(LargeBinary(32))
    return_url: Mapped[str | None] = mapped_column(Text)
    external_ref: Mapped[str | None] = mapped_column(String(200))
    attempts_count: Mapped[int]
    model_version: Mapped[str | None] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(Timestamp)
    expires_at: Mapped[datetime] = mapped_column(Timestamp)
    completed_at: Mapped[datetime | None] = mapped_column(Timestamp)


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


METADATA = Base.metadata
