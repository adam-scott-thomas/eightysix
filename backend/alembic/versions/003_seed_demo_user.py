"""Seed demo user account.

Revision ID: 003
Revises: 002
Create Date: 2026-04-16
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEMO_USER_ID = "00000000-0000-4000-a000-000000000001"


def upgrade() -> None:
    # Insert demo user if not exists.
    # Password hash placeholder — real hash set on app startup.
    op.execute(sa.text(
        """
        INSERT INTO users (id, email, hashed_password, full_name, role, is_active)
        VALUES (:id, :email, :pw, :name, 'admin', true)
        ON CONFLICT (email) DO UPDATE SET role = 'admin'
        """
    ).bindparams(
        id=DEMO_USER_ID,
        email="demo@quantumatiq.com",
        pw="$PLACEHOLDER$",
        name="Demo User",
    ))


def downgrade() -> None:
    op.execute(sa.text(
        "DELETE FROM users WHERE email = 'demo@quantumatiq.com'"
    ))
