"""The Age Pass: a policy may accept passes, and a session gives out at most one batch of them.

Revision ID: 0011
Revises: 0010
Created: 2026-11-02

A website opts in through its own policy (decision D21: off by default, and off for every preset). A session that
passed may give the person one batch of passes; the session records only *when* it did, never the passes, their keys
or their salts — so nothing Dwarpal keeps can connect a pass shown later to the check it came from.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0011"
down_revision: str | Sequence[str] | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("policies", sa.Column("accept_age_pass", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("verification_sessions", sa.Column("age_pass_issued_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("verification_sessions", "age_pass_issued_at")
    op.drop_column("policies", "accept_age_pass")
