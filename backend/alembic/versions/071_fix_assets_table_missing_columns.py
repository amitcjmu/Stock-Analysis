"""Fix assets table missing columns and import_field_mappings engagement_id

Revision ID: 071
Revises: 070
Create Date: 2025-01-21 17:30:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID

# revision identifiers, used by Alembic.
revision = "071_fix_assets_table_missing_columns"
down_revision = "070_add_missing_cfse_fields_if_needed"
branch_labels = None
depends_on = None


def _column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            """
        SELECT COUNT(*)
        FROM information_schema.columns
        WHERE table_schema = 'migration'
          AND table_name = :table_name
          AND column_name = :column_name
        """
        ),
        {"table_name": table_name, "column_name": column_name},
    )
    return result.scalar() > 0


def upgrade():
    """Add missing columns to assets and import_field_mappings tables."""

    # Add discovered_at column to assets table if it doesn't exist
    # This column is defined in AssessmentFieldsMixin but apparently wasn't migrated
    if not _column_exists("assets", "discovered_at"):
        op.add_column(
            "assets",
            sa.Column(
                "discovered_at",
                sa.DateTime(timezone=True),
                server_default=func.now(),
                nullable=True,
                comment="Timestamp when the asset was first discovered.",
            ),
            schema="migration",
        )
        print("✓ Added discovered_at column to assets table")
    else:
        print("✓ discovered_at column already exists in assets table")

    # Add engagement_id column to import_field_mappings table if it doesn't exist
    # This is needed for proper multi-tenant isolation
    if not _column_exists("import_field_mappings", "engagement_id"):
        op.add_column(
            "import_field_mappings",
            sa.Column(
                "engagement_id",
                PostgresUUID(as_uuid=True),
                sa.ForeignKey("engagements.id", ondelete="CASCADE"),
                nullable=True,  # Nullable to avoid breaking existing data
                comment="FK to engagement for multi-tenant isolation.",
            ),
            schema="migration",
        )

        # Create index for performance
        op.create_index(
            "ix_import_field_mappings_engagement_id",
            "import_field_mappings",
            ["engagement_id"],
            schema="migration",
        )

        print("✓ Added engagement_id column to import_field_mappings table")
    else:
        print("✓ engagement_id column already exists in import_field_mappings table")


def downgrade():
    """Remove the added columns."""

    # Remove discovered_at column from assets table if it exists
    if _column_exists("assets", "discovered_at"):
        op.drop_column("assets", "discovered_at", schema="migration")
        print("✓ Removed discovered_at column from assets table")
    else:
        print("✓ discovered_at column does not exist in assets table")

    # Remove engagement_id column from import_field_mappings table if it exists
    if _column_exists("import_field_mappings", "engagement_id"):
        # Drop index first
        try:
            op.drop_index(
                "ix_import_field_mappings_engagement_id",
                table_name="import_field_mappings",
                schema="migration",
            )
        except Exception:
            pass  # Index might not exist

        op.drop_column("import_field_mappings", "engagement_id", schema="migration")
        print("✓ Removed engagement_id column from import_field_mappings table")
    else:
        print("✓ engagement_id column does not exist in import_field_mappings table")
