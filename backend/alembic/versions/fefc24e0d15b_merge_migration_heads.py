"""merge_migration_heads

Revision ID: fefc24e0d15b
Revises: ensure_user_profiles, remove_session_id_cleanup
Create Date: 2025-07-02 02:30:57.570514

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fefc24e0d15b'
down_revision = ('ensure_user_profiles', 'remove_session_id_cleanup')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass 