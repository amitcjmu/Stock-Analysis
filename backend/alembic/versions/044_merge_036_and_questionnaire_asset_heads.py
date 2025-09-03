"""merge_036_and_cef530e2_heads

Revision ID: 044_merge_036_and_questionnaire_asset_heads
Revises: 043_merge_migration_heads
Create Date: 2025-08-28 18:48:56.868134
CC: Fixed reference to renamed 036b
"""

# noqa: F401 - Unused imports are required by Alembic
from alembic import op  # noqa: F401
import sqlalchemy as sa  # noqa: F401


# revision identifiers, used by Alembic.
revision = "044_merge_036_and_questionnaire_asset_heads"
down_revision = "043_merge_migration_heads"
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
