"""Merge migration heads

Revision ID: b1cc7d8d2aa1
Revises: 8b9515dbf275, c85140124625, migrate_session_to_flow_id
Create Date: 2025-06-30 02:12:59.972221

"""


# revision identifiers, used by Alembic.
revision = 'b1cc7d8d2aa1'
down_revision = ('8b9515dbf275', 'c85140124625', 'migrate_session_to_flow_id')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass 