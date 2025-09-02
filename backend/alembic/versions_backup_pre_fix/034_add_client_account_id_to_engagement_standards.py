"""Add client_account_id to engagement_architecture_standards table

Revision ID: 034_add_client_account_id_to_engagement_standards
Revises: 033_merge_metadata_rename_heads
Create Date: 2025-08-23 16:32:00.000000

This migration adds the missing client_account_id column to the
engagement_architecture_standards table for multi-tenant isolation.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "034_add_client_account_id_to_engagement_standards"
down_revision = "033_merge_all_heads"
branch_labels = None
depends_on = None


def column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table within the 'migration' schema."""
    bind = op.get_bind()
    try:
        stmt = sa.text(
            """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                  AND table_name = :table_name
                  AND column_name = :column_name
            )
            """
        )
        result = bind.execute(
            stmt, {"table_name": table_name, "column_name": column_name}
        ).scalar()
        return bool(result)
    except Exception as e:
        print(f"Error checking if column {column_name} exists in {table_name}: {e}")
        return False


def upgrade() -> None:
    """Add client_account_id column to engagement_architecture_standards table"""

    print("🔄 Adding client_account_id to engagement_architecture_standards table...")

    # Check if column already exists
    if not column_exists("engagement_architecture_standards", "client_account_id"):
        # Add the column
        op.add_column(
            "engagement_architecture_standards",
            sa.Column(
                "client_account_id",
                postgresql.UUID(as_uuid=True),
                nullable=True,  # Initially nullable to allow migration
                comment="Client account for multi-tenant isolation",
            ),
            schema="migration",
        )
        print("  ✅ Added client_account_id column")

        # Update existing rows to set client_account_id from the engagement
        op.execute(
            """
            UPDATE migration.engagement_architecture_standards eas
            SET client_account_id = e.client_account_id
            FROM migration.engagements e
            WHERE eas.engagement_id = e.id
            """
        )
        print("  ✅ Populated client_account_id from engagement relationships")

        # Now make the column non-nullable
        op.alter_column(
            "engagement_architecture_standards",
            "client_account_id",
            nullable=False,
            schema="migration",
        )
        print("  ✅ Made client_account_id non-nullable")

        # Add foreign key constraint
        op.create_foreign_key(
            "fk_engagement_architecture_standards_client_account",
            "engagement_architecture_standards",
            "client_accounts",
            ["client_account_id"],
            ["id"],
            source_schema="migration",
            referent_schema="migration",
            ondelete="CASCADE",
        )
        print("  ✅ Added foreign key constraint to client_accounts")

        # Add index for performance
        op.create_index(
            "ix_engagement_architecture_standards_client_account",
            "engagement_architecture_standards",
            ["client_account_id"],
            schema="migration",
        )
        print("  ✅ Added index on client_account_id")

    else:
        print("  ℹ️  Column client_account_id already exists, skipping")

    print("✅ Migration completed successfully")


def downgrade() -> None:
    """Remove client_account_id column from engagement_architecture_standards table"""

    print(
        "🔄 Removing client_account_id from engagement_architecture_standards table..."
    )

    if column_exists("engagement_architecture_standards", "client_account_id"):
        # Drop index
        try:
            op.drop_index(
                "ix_engagement_architecture_standards_client_account",
                schema="migration",
            )
            print("  ✅ Dropped index")
        except Exception:
            pass

        # Drop foreign key
        try:
            op.drop_constraint(
                "fk_engagement_architecture_standards_client_account",
                "engagement_architecture_standards",
                type_="foreignkey",
                schema="migration",
            )
            print("  ✅ Dropped foreign key constraint")
        except Exception:
            pass

        # Drop column
        op.drop_column(
            "engagement_architecture_standards", "client_account_id", schema="migration"
        )
        print("  ✅ Dropped client_account_id column")
    else:
        print("  ℹ️  Column client_account_id does not exist, skipping")

    print("✅ Downgrade completed")
