"""Optimize indexes for canonical application identity system

Revision ID: 052_optimize_application_indexes
Revises: 051_migrate_existing_collection_applications
Create Date: 2025-09-03 03:41:00.000000

This migration creates comprehensive indexes for optimal performance:
- Multi-tenant isolation enforcement indexes
- Fast lookup indexes for deduplication
- Vector similarity search indexes (if pgvector available)
- Usage pattern optimization indexes
- Composite indexes for complex queries
"""

from alembic import op
from sqlalchemy import text
import logging

# revision identifiers, used by Alembic.
revision = "052_optimize_application_indexes"
down_revision = "051_migrate_existing_collection_applications"
branch_labels = None
depends_on = None

logger = logging.getLogger(__name__)


def check_pgvector_availability(conn) -> bool:
    """Check if pgvector extension is available for vector indexes"""
    try:
        result = conn.execute(
            text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
        )
        row = result.fetchone()
        if row:
            logger.info("✅ pgvector extension detected - will create vector indexes")
            return True
        logger.info("ℹ️ pgvector extension not available - skipping vector indexes")
        return False
    except Exception as e:
        logger.info(
            f"ℹ️ pgvector extension not available (error: {e}) - skipping vector indexes"
        )
        return False


def upgrade() -> None:
    """Create optimized indexes for canonical application system"""
    conn = op.get_bind()
    logger.info("🚀 Creating optimized indexes for canonical application system")

    try:
        # Check if pgvector extension is available
        pgvector_available = check_pgvector_availability(conn)

        # 1. Multi-tenant isolation enforcement indexes (CRITICAL for security)
        logger.info("🔒 Creating multi-tenant isolation indexes...")

        op.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_canonical_apps_tenant_security
            ON migration.canonical_applications (client_account_id, engagement_id)
        """
        )

        op.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_app_variants_tenant_security
            ON migration.application_name_variants (client_account_id, engagement_id)
        """
        )

        # 2. Performance indexes for lookups and searches
        logger.info("⚡ Creating performance indexes...")

        # Hash-based lookups for exact matches
        op.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_canonical_apps_name_hash_perf
            ON migration.canonical_applications (name_hash, client_account_id, engagement_id)
        """
        )

        op.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_app_variants_hash_perf
            ON migration.application_name_variants (variant_hash, client_account_id, engagement_id)
        """
        )

        # Text search indexes for partial matching
        op.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_canonical_apps_normalized_search
            ON migration.canonical_applications (normalized_name, client_account_id, engagement_id)
        """
        )

        op.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_app_variants_normalized_search
            ON migration.application_name_variants (normalized_variant, client_account_id, engagement_id)
        """
        )

        # 3. Usage pattern optimization indexes
        logger.info("📊 Creating usage pattern indexes...")

        op.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_canonical_apps_usage_stats
            ON migration.canonical_applications (usage_count DESC, last_used_at DESC)
        """
        )

        op.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_app_variants_usage_stats
            ON migration.application_name_variants (usage_count DESC, last_used_at DESC)
        """
        )

        # Confidence and verification indexes
        op.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_canonical_apps_confidence
            ON migration.canonical_applications (confidence_score DESC, is_verified)
        """
        )

        op.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_app_variants_confidence
            ON migration.application_name_variants (match_confidence DESC, similarity_score DESC)
        """
        )

        # 4. Relationship indexes for foreign key performance
        logger.info("🔗 Creating relationship indexes...")

        op.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_app_variants_canonical_lookup
            ON migration.application_name_variants (canonical_application_id)
        """
        )

        op.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_collection_flow_apps_canonical_lookup
            ON migration.collection_flow_applications (canonical_application_id)
            WHERE canonical_application_id IS NOT NULL
        """
        )

        op.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_collection_flow_apps_variant_lookup
            ON migration.collection_flow_applications (name_variant_id)
            WHERE name_variant_id IS NOT NULL
        """
        )

        # 5. Vector similarity indexes (if pgvector available)
        if pgvector_available:
            logger.info("🔍 Creating vector similarity indexes...")

            op.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_canonical_apps_vector_similarity
                ON migration.canonical_applications
                USING ivfflat (name_embedding vector_cosine_ops)
                WITH (lists = 100)
                WHERE name_embedding IS NOT NULL
            """
            )

            op.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_app_variants_vector_similarity
                ON migration.application_name_variants
                USING ivfflat (variant_embedding vector_cosine_ops)
                WITH (lists = 100)
                WHERE variant_embedding IS NOT NULL
            """
            )

        # 6. Composite indexes for complex queries
        logger.info("🔧 Creating composite indexes...")

        # Deduplication workflow composite index
        op.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_canonical_apps_dedup_workflow
            ON migration.canonical_applications
            (client_account_id, engagement_id, normalized_name, confidence_score DESC, is_verified DESC)
        """
        )

        # Application selection composite index
        op.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_app_variants_selection_workflow
            ON migration.application_name_variants
            (client_account_id, engagement_id, canonical_application_id, match_confidence DESC)
        """
        )

        # Collection flow optimization composite index
        op.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_collection_flow_apps_optimization
            ON migration.collection_flow_applications
            (collection_flow_id, canonical_application_id, collection_status, created_at DESC)
        """
        )

        # 7. Partial indexes for specific scenarios
        logger.info("🎯 Creating partial indexes...")

        # Unverified applications needing review
        op.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_canonical_apps_unverified
            ON migration.canonical_applications (client_account_id, engagement_id, created_at DESC)
            WHERE is_verified = false
        """
        )

        # High-usage applications for performance priority
        op.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_canonical_apps_high_usage
            ON migration.canonical_applications (last_used_at DESC, confidence_score DESC)
            WHERE usage_count >= 5
        """
        )

        # Low-confidence variants needing attention
        op.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_app_variants_low_confidence
            ON migration.application_name_variants (client_account_id, engagement_id, match_confidence ASC)
            WHERE match_confidence < 0.8
        """
        )

        # 8. Update table statistics for query planner optimization
        logger.info("📈 Updating table statistics...")

        op.execute("ANALYZE migration.canonical_applications")
        op.execute("ANALYZE migration.application_name_variants")
        op.execute("ANALYZE migration.collection_flow_applications")

        logger.info("🎉 Index optimization completed successfully!")

    except Exception as e:
        logger.error(f"❌ Index optimization failed: {str(e)}")
        raise


def downgrade() -> None:
    """Remove performance indexes (keep only essential ones)"""
    logger.info("🔄 Starting index optimization downgrade")

    try:
        # List of performance indexes to remove
        performance_indexes = [
            "idx_canonical_apps_tenant_security",
            "idx_app_variants_tenant_security",
            "idx_canonical_apps_name_hash_perf",
            "idx_app_variants_hash_perf",
            "idx_canonical_apps_normalized_search",
            "idx_app_variants_normalized_search",
            "idx_canonical_apps_usage_stats",
            "idx_app_variants_usage_stats",
            "idx_canonical_apps_confidence",
            "idx_app_variants_confidence",
            "idx_app_variants_canonical_lookup",
            "idx_collection_flow_apps_canonical_lookup",
            "idx_collection_flow_apps_variant_lookup",
            "idx_canonical_apps_vector_similarity",
            "idx_app_variants_vector_similarity",
            "idx_canonical_apps_dedup_workflow",
            "idx_app_variants_selection_workflow",
            "idx_collection_flow_apps_optimization",
            "idx_canonical_apps_unverified",
            "idx_canonical_apps_high_usage",
            "idx_app_variants_low_confidence",
        ]

        for index_name in performance_indexes:
            try:
                op.execute(f"DROP INDEX IF EXISTS migration.{index_name}")
                logger.info(f"🗑️ Removed index: {index_name}")
            except Exception as drop_error:
                logger.warning(
                    f"⚠️ Failed to remove index {index_name}: {str(drop_error)}"
                )

        logger.info("✅ Index optimization downgrade completed")

    except Exception as e:
        logger.error(f"❌ Index downgrade failed: {str(e)}")
        raise
