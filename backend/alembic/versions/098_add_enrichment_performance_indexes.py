"""Add indexes for enrichment and canonical mapping performance

Revision ID: 098_add_enrichment_performance_indexes
Revises: 097_add_enrichment_pattern_types
Create Date: 2025-10-16

This migration adds database indexes to optimize:
1. AssessmentApplicationResolver queries (tenant + canonical_application_id)
2. Bulk asset mapping lookups (asset_id)
3. Unmapped asset queries (tenant + asset_type)

Per GPT-5 recommendations in ASSESSMENT_CANONICAL_GROUPING_REMEDIATION_PLAN.md,
these indexes improve performance for enrichment pipeline and canonical application grouping.
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "098_add_enrichment_performance_indexes"
down_revision = "097_add_enrichment_pattern_types"
branch_labels = None
depends_on = None


def upgrade():
    """Add performance indexes for enrichment and canonical mapping."""

    # Index for AssessmentApplicationResolver queries
    # Used when resolving canonical applications by tenant and canonical_application_id
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'collection_flow_applications'
                AND indexname = 'idx_cfa_tenant_canonical'
            ) THEN
                CREATE INDEX idx_cfa_tenant_canonical
                ON migration.collection_flow_applications (
                    client_account_id,
                    engagement_id,
                    canonical_application_id
                );
            END IF;
        END $$;
    """
    )

    # Index for bulk asset mapping lookups
    # Used when checking if an asset is already mapped to a canonical application
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'collection_flow_applications'
                AND indexname = 'idx_cfa_asset_lookup'
            ) THEN
                CREATE INDEX idx_cfa_asset_lookup
                ON migration.collection_flow_applications (asset_id);
            END IF;
        END $$;
    """
    )

    # Index for unmapped asset queries
    # Used when finding assets without canonical mappings for a tenant
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'assets'
                AND indexname = 'idx_assets_tenant_type'
            ) THEN
                CREATE INDEX idx_assets_tenant_type
                ON migration.assets (
                    client_account_id,
                    engagement_id,
                    asset_type
                );
            END IF;
        END $$;
    """
    )


def downgrade():
    """Remove performance indexes."""
    op.execute("DROP INDEX IF EXISTS migration.idx_cfa_tenant_canonical;")
    op.execute("DROP INDEX IF EXISTS migration.idx_cfa_asset_lookup;")
    op.execute("DROP INDEX IF EXISTS migration.idx_assets_tenant_type;")
