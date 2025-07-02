"""merge_all_heads

Revision ID: 13b95eacf168
Revises: 002_add_assessment_flow_tables, 3b36f179e1ef
Create Date: 2025-07-02 21:58:07.635633

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '13b95eacf168'
down_revision = ('002_add_assessment_flow_tables', '3b36f179e1ef')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass 