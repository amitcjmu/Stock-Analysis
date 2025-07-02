"""Add it_guidelines and decision_criteria to client_accounts

Revision ID: d29421e93333
Revises: fefc24e0d15b
Create Date: 2025-07-02 03:09:19.921450

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd29421e93333'
down_revision = 'fefc24e0d15b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add it_guidelines column
    op.add_column('client_accounts', sa.Column('it_guidelines', sa.JSON(), nullable=True))
    # Add decision_criteria column
    op.add_column('client_accounts', sa.Column('decision_criteria', sa.JSON(), nullable=True))
    
    # Set default values for existing rows
    op.execute("UPDATE client_accounts SET it_guidelines = '{}' WHERE it_guidelines IS NULL")
    op.execute("UPDATE client_accounts SET decision_criteria = '{}' WHERE decision_criteria IS NULL")


def downgrade() -> None:
    # Remove the columns
    op.drop_column('client_accounts', 'decision_criteria')
    op.drop_column('client_accounts', 'it_guidelines') 