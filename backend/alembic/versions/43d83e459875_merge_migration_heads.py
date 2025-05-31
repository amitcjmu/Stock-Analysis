"""merge_migration_heads

Revision ID: 43d83e459875
Revises: add_feedback_tables_001, learning_system_001
Create Date: 2025-05-31 17:41:57.482298

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '43d83e459875'
down_revision = ('add_feedback_tables_001', 'learning_system_001')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass 