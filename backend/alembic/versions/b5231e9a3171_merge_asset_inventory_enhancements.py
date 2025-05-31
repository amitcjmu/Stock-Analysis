"""merge asset inventory enhancements

Revision ID: b5231e9a3171
Revises: 00fc146d4abe, 5992adf19317
Create Date: 2025-05-31 18:23:01.965178

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b5231e9a3171'
down_revision = ('00fc146d4abe', '5992adf19317')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass 