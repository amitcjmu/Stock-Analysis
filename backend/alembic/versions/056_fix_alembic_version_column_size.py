"""Fix alembic_version column size to handle longer migration names

Revision ID: 056_fix_alembic_version_column_size
Revises: 055_add_execution_metadata
Create Date: 2025-09-11

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = "056_fix_alembic_version_column_size"
down_revision = "055_add_execution_metadata"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Increase alembic_version.version_num column size from VARCHAR(50) to VARCHAR(100)
    to handle longer migration names.
    """
    # First check current column size
    conn = op.get_bind()
    result = conn.execute(
        text(
            """
            SELECT character_maximum_length
            FROM information_schema.columns
            WHERE table_schema = 'migration'
            AND table_name = 'alembic_version'
            AND column_name = 'version_num'
            """
        )
    )
    current_size = result.scalar()

    if current_size and current_size < 100:
        # Increase column size
        op.alter_column(
            "alembic_version",
            "version_num",
            type_=sa.String(100),
            existing_type=sa.String(50),
            schema="migration",
        )
        print(
            f"✅ Increased alembic_version.version_num from VARCHAR({current_size}) to VARCHAR(100)"
        )
    else:
        print(
            f"ℹ️ alembic_version.version_num already has sufficient size: VARCHAR({current_size})"
        )


def downgrade() -> None:
    """
    Revert column size back to VARCHAR(50)
    Note: This will fail if any existing migration names are longer than 50 characters
    """
    op.alter_column(
        "alembic_version",
        "version_num",
        type_=sa.String(50),
        existing_type=sa.String(100),
        schema="migration",
    )
