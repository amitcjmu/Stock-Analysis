"""add_dependents_column_to_assets

Revision ID: 129_add_dependents_column_to_assets
Revises: 128_add_asset_id_to_questionnaires
Create Date: 2025-11-07 06:21:13.176895

Fixes Issue #962 - Adds dependents column to assets table for bidirectional dependency tracking
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "129_add_dependents_column_to_assets"
down_revision = "128_add_asset_id_to_questionnaires"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add dependents column to assets table."""
    # Check if column already exists before adding
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [
        col["name"] for col in inspector.get_columns("assets", schema="migration")
    ]

    if "dependents" not in columns:
        op.add_column(
            "assets",
            sa.Column(
                "dependents",
                postgresql.JSON(astext_type=sa.Text()),
                nullable=True,
                comment="A JSON array of assets that depend on this asset (Issue #962).",
            ),
            schema="migration",
        )
        print("✅ Added 'dependents' column to migration.assets table")
    else:
        print("⏭️  'dependents' column already exists in migration.assets table")


def downgrade() -> None:
    """Remove dependents column from assets table."""
    # Check if column exists before removing
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [
        col["name"] for col in inspector.get_columns("assets", schema="migration")
    ]

    if "dependents" in columns:
        op.drop_column("assets", "dependents", schema="migration")
        print("✅ Removed 'dependents' column from migration.assets table")
    else:
        print("⏭️  'dependents' column does not exist in migration.assets table")
