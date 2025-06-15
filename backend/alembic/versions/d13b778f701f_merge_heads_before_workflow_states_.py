"""merge heads before workflow_states migration

Revision ID: d13b778f701f
Revises: a4c212b400af, 305c091bd5bf
Create Date: 2025-06-15 07:24:07.233960

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd13b778f701f'
down_revision = ('a4c212b400af', '305c091bd5bf')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass 