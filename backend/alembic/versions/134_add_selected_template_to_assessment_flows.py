"""Add selected_template to assessment_flows

Revision ID: 134
Revises: 133
Create Date: 2025-01-16

This migration adds the selected_template column to assessment_flows table
to persist which architecture template was selected (enterprise-standard,
cloud-native, security-first, performance-optimized, or custom).
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "134_add_selected_template"
down_revision = "133_add_missing_enrichment_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add selected_template column to assessment_flows table"""
    # Use PostgreSQL DO block for idempotent migration
    op.execute(
        """
        DO $$
        BEGIN
            -- Add selected_template column if it doesn't exist
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                  AND table_name = 'assessment_flows'
                  AND column_name = 'selected_template'
            ) THEN
                ALTER TABLE migration.assessment_flows
                ADD COLUMN selected_template VARCHAR(100);

                COMMENT ON COLUMN migration.assessment_flows.selected_template IS
                'Architecture template ID selected by user (enterprise-standard, '
                'cloud-native, security-first, performance-optimized, custom, or NULL)';
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    """Remove selected_template column from assessment_flows table"""
    op.execute(
        """
        DO $$
        BEGIN
            -- Drop selected_template column if it exists
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                  AND table_name = 'assessment_flows'
                  AND column_name = 'selected_template'
            ) THEN
                ALTER TABLE migration.assessment_flows
                DROP COLUMN selected_template;
            END IF;
        END $$;
        """
    )
