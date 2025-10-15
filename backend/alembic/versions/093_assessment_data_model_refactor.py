"""assessment_data_model_refactor

Refactor assessment_flows table to support canonical application grouping
and enrichment tracking. This migration adds proper semantic fields to
distinguish between asset IDs and canonical application IDs, enabling
application-centric assessment views with rich metadata.

Key Changes:
- Add selected_asset_ids: Proper semantic field for asset UUIDs
- Add selected_canonical_application_ids: Resolved canonical applications
- Add application_asset_groups: Application-centric grouping structure
- Add enrichment_status: Track enrichment table population
- Add readiness_summary: Assessment readiness aggregates
- Migrate data from selected_application_ids to selected_asset_ids
- Mark selected_application_ids as deprecated (kept for backward compatibility)

Revision ID: 093_assessment_data_model_refactor
Revises: 092_add_supported_versions_requirement_details
Create Date: 2025-10-15 12:00:00.000000

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "093_assessment_data_model_refactor"
down_revision = "092_add_supported_versions_requirement_details"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add new semantic fields to assessment_flows table for canonical
    application grouping and enrichment tracking.

    IDEMPOTENT: Uses IF NOT EXISTS checks for all column additions and indexes.
    """

    # Add selected_asset_ids column (proper semantic field for asset UUIDs)
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'assessment_flows'
                AND column_name = 'selected_asset_ids'
            ) THEN
                ALTER TABLE migration.assessment_flows
                ADD COLUMN selected_asset_ids JSONB DEFAULT '[]'::jsonb;

                COMMENT ON COLUMN migration.assessment_flows.selected_asset_ids
                IS 'Array of asset UUIDs selected for assessment (proper semantic field)';
            END IF;
        END $$;
        """
    )

    # Add selected_canonical_application_ids column
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'assessment_flows'
                AND column_name = 'selected_canonical_application_ids'
            ) THEN
                ALTER TABLE migration.assessment_flows
                ADD COLUMN selected_canonical_application_ids JSONB DEFAULT '[]'::jsonb;

                COMMENT ON COLUMN migration.assessment_flows.selected_canonical_application_ids
                IS 'Array of canonical application UUIDs '
                   '(resolved from assets via collection_flow_applications junction table)';
            END IF;
        END $$;
        """
    )

    # Add application_asset_groups column (grouping structure)
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'assessment_flows'
                AND column_name = 'application_asset_groups'
            ) THEN
                ALTER TABLE migration.assessment_flows
                ADD COLUMN application_asset_groups JSONB DEFAULT '[]'::jsonb;

                COMMENT ON COLUMN migration.assessment_flows.application_asset_groups
                IS 'Array of application groups with their assets. '
                   'Structure: [{"canonical_application_id": "uuid", '
                   '"canonical_application_name": "CRM System", "asset_ids": ["uuid1"], '
                   '"asset_count": 2, "asset_types": ["server"], '
                   '"readiness_summary": {"ready": 1, "not_ready": 1}}]';
            END IF;
        END $$;
        """
    )

    # Add enrichment_status column (enrichment table population tracking)
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'assessment_flows'
                AND column_name = 'enrichment_status'
            ) THEN
                ALTER TABLE migration.assessment_flows
                ADD COLUMN enrichment_status JSONB DEFAULT '{}'::jsonb;

                COMMENT ON COLUMN migration.assessment_flows.enrichment_status
                IS 'Summary of enrichment table population. '
                   'Structure: {"compliance_flags": 2, "licenses": 0, "vulnerabilities": 3, '
                   '"resilience": 1, "dependencies": 4, "product_links": 0, "field_conflicts": 0}';
            END IF;
        END $$;
        """
    )

    # Add readiness_summary column (assessment readiness aggregates)
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'assessment_flows'
                AND column_name = 'readiness_summary'
            ) THEN
                ALTER TABLE migration.assessment_flows
                ADD COLUMN readiness_summary JSONB DEFAULT '{}'::jsonb;

                COMMENT ON COLUMN migration.assessment_flows.readiness_summary
                IS 'Assessment readiness summary. '
                   'Structure: {"total_assets": 5, "ready": 2, "not_ready": 3, '
                   '"in_progress": 0, "avg_completeness_score": 0.64}';
            END IF;
        END $$;
        """
    )

    # Create GIN indexes for JSONB fields (performance optimization)
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'assessment_flows'
                AND indexname = 'idx_assessment_flows_selected_asset_ids'
            ) THEN
                CREATE INDEX idx_assessment_flows_selected_asset_ids
                ON migration.assessment_flows USING GIN (selected_asset_ids);
            END IF;
        END $$;
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'assessment_flows'
                AND indexname = 'idx_assessment_flows_canonical_app_ids'
            ) THEN
                CREATE INDEX idx_assessment_flows_canonical_app_ids
                ON migration.assessment_flows USING GIN (selected_canonical_application_ids);
            END IF;
        END $$;
        """
    )

    # Migrate existing data: Copy selected_application_ids → selected_asset_ids
    # This is a semantic correction since selected_application_ids actually contains asset UUIDs
    op.execute(
        """
        UPDATE migration.assessment_flows
        SET selected_asset_ids = selected_application_ids
        WHERE selected_asset_ids = '[]'::jsonb
          AND selected_application_ids IS NOT NULL
          AND selected_application_ids != '[]'::jsonb;
        """
    )

    # Mark selected_application_ids as deprecated (keep for backward compatibility)
    op.execute(
        """
        COMMENT ON COLUMN migration.assessment_flows.selected_application_ids
        IS 'DEPRECATED: Use selected_asset_ids instead. Kept for backward compatibility. '
           'This column actually stores asset UUIDs, not application UUIDs '
           '(semantic mismatch from pre-October 2025). '
           'Will be removed in future migration after all code updated.';
        """
    )


def downgrade() -> None:
    """
    Remove new semantic fields from assessment_flows table.

    IDEMPOTENT: Uses IF EXISTS checks for all operations.
    """

    # Drop indexes
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'assessment_flows'
                AND indexname = 'idx_assessment_flows_canonical_app_ids'
            ) THEN
                DROP INDEX migration.idx_assessment_flows_canonical_app_ids;
            END IF;
        END $$;
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'assessment_flows'
                AND indexname = 'idx_assessment_flows_selected_asset_ids'
            ) THEN
                DROP INDEX migration.idx_assessment_flows_selected_asset_ids;
            END IF;
        END $$;
        """
    )

    # Drop columns in reverse order
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'assessment_flows'
                AND column_name = 'readiness_summary'
            ) THEN
                ALTER TABLE migration.assessment_flows
                DROP COLUMN readiness_summary;
            END IF;
        END $$;
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'assessment_flows'
                AND column_name = 'enrichment_status'
            ) THEN
                ALTER TABLE migration.assessment_flows
                DROP COLUMN enrichment_status;
            END IF;
        END $$;
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'assessment_flows'
                AND column_name = 'application_asset_groups'
            ) THEN
                ALTER TABLE migration.assessment_flows
                DROP COLUMN application_asset_groups;
            END IF;
        END $$;
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'assessment_flows'
                AND column_name = 'selected_canonical_application_ids'
            ) THEN
                ALTER TABLE migration.assessment_flows
                DROP COLUMN selected_canonical_application_ids;
            END IF;
        END $$;
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'assessment_flows'
                AND column_name = 'selected_asset_ids'
            ) THEN
                ALTER TABLE migration.assessment_flows
                DROP COLUMN selected_asset_ids;
            END IF;
        END $$;
        """
    )

    # Restore original comment on selected_application_ids
    op.execute(
        """
        COMMENT ON COLUMN migration.assessment_flows.selected_application_ids
        IS NULL;
        """
    )
