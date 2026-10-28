"""Recovery codes for console users who use one-time codes.

Revision ID: 0008
Revises: 0007
Created: 2026-10-29

Ten single-use codes, given when one-time codes are switched on, each sign a person in once in place of a code from
their phone — for when the phone is lost. Only an HMAC of each is kept, keyed from the master key, so a copy of the
table alone can't reveal them.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0008"
down_revision: str | Sequence[str] | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("recovery_digests", postgresql.ARRAY(sa.Text()), nullable=False, server_default="{}"),
    )


def downgrade() -> None:
    op.drop_column("users", "recovery_digests")
