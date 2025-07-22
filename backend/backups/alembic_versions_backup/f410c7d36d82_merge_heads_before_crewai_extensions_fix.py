"""Merge heads before crewai extensions fix

Revision ID: f410c7d36d82
Revises: b1cc7d8d2aa1, add_v3_persistence_001
Create Date: 2025-06-30 03:56:10.989001

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = 'f410c7d36d82'
down_revision = ('b1cc7d8d2aa1', 'add_v3_persistence_001')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass 