"""Merge migration heads

Revision ID: 515dd09499ad
Revises: b5231e9a3171, 006_llm_usage_tracking
Create Date: 2025-06-04 23:48:50.781056

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '515dd09499ad'
down_revision = ('b5231e9a3171', '006_llm_usage_tracking')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass 