"""merge_all_heads_final

Revision ID: 4a69564e2679
Revises: 005_user_active_flows_simple, 4aac48ccc8ba
Create Date: 2025-07-11 05:14:52.738606

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4a69564e2679'
down_revision = ('005_user_active_flows_simple', '4aac48ccc8ba')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass 