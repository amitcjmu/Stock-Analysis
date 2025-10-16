"""add_supported_versions_requirement_details

Add supported_versions and requirement_details columns to
engagement_architecture_standards table to support architecture
standards workflow.

Revision ID: 092_add_supported_versions_requirement_details
Revises: 091_add_phase_deprecation_comments_adr027
Create Date: 2025-10-15 01:18:03.651744

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "092_add_supported_versions_requirement_details"
down_revision = "091_add_phase_deprecation_comments_adr027"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add supported_versions and requirement_details columns to
    engagement_architecture_standards table.

    IDEMPOTENT: Uses IF NOT EXISTS checks for column additions.
    """
    # Check and add supported_versions column
    # Idempotent: Only adds if column doesn't exist
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'engagement_architecture_standards'
                AND column_name = 'supported_versions'
            ) THEN
                ALTER TABLE migration.engagement_architecture_standards
                ADD COLUMN supported_versions JSONB DEFAULT '{}'::jsonb;
            END IF;
        END $$;
        """
    )

    # Check and add requirement_details column
    # Idempotent: Only adds if column doesn't exist
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'engagement_architecture_standards'
                AND column_name = 'requirement_details'
            ) THEN
                ALTER TABLE migration.engagement_architecture_standards
                ADD COLUMN requirement_details JSONB DEFAULT '{}'::jsonb;
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    """
    Remove supported_versions and requirement_details columns.

    IDEMPOTENT: Uses IF EXISTS checks for column removal.
    """
    # Idempotent: Only drops if column exists
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'engagement_architecture_standards'
                AND column_name = 'requirement_details'
            ) THEN
                ALTER TABLE migration.engagement_architecture_standards
                DROP COLUMN requirement_details;
            END IF;
        END $$;
        """
    )

    # Idempotent: Only drops if column exists
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'engagement_architecture_standards'
                AND column_name = 'supported_versions'
            ) THEN
                ALTER TABLE migration.engagement_architecture_standards
                DROP COLUMN supported_versions;
            END IF;
        END $$;
        """
    )
