"""Add created_by to client_accounts

Revision ID: 3b36f179e1ef
Revises: d29421e93333
Create Date: 2025-07-02 03:11:43.375824

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3b36f179e1ef'
down_revision = 'd29421e93333'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add created_by column
    op.add_column('client_accounts', sa.Column('created_by', sa.UUID(), nullable=True))


def downgrade() -> None:
    # Remove the column
    op.drop_column('client_accounts', 'created_by') 