"""add_data_validation_completed_column

Add data_validation_completed column to discovery_flows table
to align with ADR-027 Discovery v3.0.0 flow configuration.

Revision ID: 093_add_data_validation_completed
Revises: 092_add_supported_versions_requirement_details
Create Date: 2025-10-15 18:30:00.000000
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "093_add_data_validation_completed"
down_revision = "092_add_supported_versions_requirement_details"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add data_validation_completed column to discovery_flows table.

    Per ADR-027: Discovery v3.0.0 has 5 phases including data_validation.
    This column was missing from the original schema and needs to be added
    to properly track the data validation phase completion status.

    IDEMPOTENT: Uses IF NOT EXISTS pattern via raw SQL for safety.
    """

    # Add column using raw SQL for better idempotency control
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'discovery_flows'
                AND column_name = 'data_validation_completed'
            ) THEN
                ALTER TABLE migration.discovery_flows
                ADD COLUMN data_validation_completed BOOLEAN NOT NULL DEFAULT false;
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    """
    Remove data_validation_completed column.

    IDEMPOTENT: Uses IF EXISTS pattern for safety.
    """
    op.execute(
        """
        ALTER TABLE migration.discovery_flows
        DROP COLUMN IF EXISTS data_validation_completed;
        """
    )
