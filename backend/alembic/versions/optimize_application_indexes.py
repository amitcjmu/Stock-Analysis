"""Optimize indexes for canonical application identity system

Revision ID: optimize_app_indexes_001
Revises: migrate_collection_apps_001
Create Date: 2025-08-26 12:00:00.000000

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
revision = "optimize_app_indexes_001"
down_revision = "migrate_collection_apps_001"
branch_labels = None
depends_on = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def upgrade() -> None:
    """Create optimized indexes for canonical application system"""

    conn = op.get_bind()

    logger.info("🚀 Creating optimized indexes for canonical application system")

    try:
        # Check if pgvector extension is available for vector indexes
        try:
            conn.execute(text("SELECT 1 FROM pg_extension WHERE extname = 'vector'"))
            pgvector_available = True
            logger.info("✅ pgvector extension detected - will create vector indexes")
        except Exception:
            pgvector_available = False
            logger.info("ℹ️ pgvector extension not available - skipping vector indexes")

        # CRITICAL SECURITY INDEXES - Multi-tenant isolation enforcement
        logger.info("🔒 Creating multi-tenant isolation indexes...")

        # Canonical applications tenant isolation (already exists but ensure it's optimal)
        op.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_canonical_apps_tenant_security
            ON migration.canonical_applications (client_account_id, engagement_id)
        """
        )

        # Application name variants tenant isolation
        op.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_app_variants_tenant_security
            ON migration.application_name_variants (client_account_id, engagement_id)
        """
        )

        # Collection flow applications tenant isolation
        op.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_collection_flow_apps_tenant_security
            ON migration.collection_flow_applications (client_account_id, engagement_id)
        """
        )

        # PERFORMANCE INDEXES - Fast lookups for deduplication
        logger.info("⚡ Creating fast lookup indexes...")

        # Hash-based exact matching (fastest path for deduplication)
        op.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_canonical_apps_hash_exact_match
            ON migration.canonical_applications
            USING BTREE (name_hash, client_account_id, engagement_id)
        """
        )

        op.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_app_variants_hash_exact_match
            ON migration.application_name_variants
            USING BTREE (variant_hash, client_account_id, engagement_id)
        """
        )

        # Normalized name pattern matching for fuzzy search
        op.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_canonical_apps_normalized_pattern
            ON migration.canonical_applications
            USING BTREE (normalized_name text_pattern_ops, client_account_id, engagement_id)
        """
        )

        op.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_app_variants_normalized_pattern
            ON migration.application_name_variants
            USING BTREE (normalized_variant text_pattern_ops, client_account_id, engagement_id)
        """
        )

        # Full-text search indexes for advanced search
        op.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_canonical_apps_fulltext_search
            ON migration.canonical_applications
            USING GIN (to_tsvector('english', canonical_name))
        """
        )

        # VECTOR SIMILARITY INDEXES - For semantic matching
        if pgvector_available:
            logger.info("🧠 Creating vector similarity search indexes...")

            try:
                # Vector similarity index for canonical applications
                # Using HNSW for better query performance with good recall
                op.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_canonical_apps_vector_similarity
                    ON migration.canonical_applications
                    USING hnsw (name_embedding vector_cosine_ops)
                    WITH (m = 16, ef_construction = 64)
                """
                )

                # Vector similarity index for application variants
                op.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_app_variants_vector_similarity
                    ON migration.application_name_variants
                    USING hnsw (variant_embedding vector_cosine_ops)
                    WITH (m = 16, ef_construction = 64)
                """
                )

                logger.info("✅ Vector similarity indexes created successfully")

            except Exception as vector_error:
                logger.warning(f"⚠️ Vector index creation failed: {str(vector_error)}")
                logger.info(
                    "   This is normal if pgvector version doesn't support HNSW"
                )

                # Fallback to IVFFlat index for older pgvector versions
                try:
                    op.execute(
                        """
                        CREATE INDEX IF NOT EXISTS idx_canonical_apps_vector_ivfflat
                        ON migration.canonical_applications
                        USING ivfflat (name_embedding vector_cosine_ops)
                        WITH (lists = 100)
                    """
                    )

                    op.execute(
                        """
                        CREATE INDEX IF NOT EXISTS idx_app_variants_vector_ivfflat
                        ON migration.application_name_variants
                        USING ivfflat (variant_embedding vector_cosine_ops)
                        WITH (lists = 100)
                    """
                    )

                    logger.info("✅ IVFFlat vector indexes created as fallback")

                except Exception as ivf_error:
                    logger.warning(
                        f"⚠️ IVFFlat index creation also failed: {str(ivf_error)}"
                    )
                    logger.info("   Vector similarity search will use sequential scans")

        # USAGE PATTERN INDEXES - For analytics and optimization
        logger.info("📊 Creating usage pattern indexes...")

        # Usage statistics for popular applications
        op.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_canonical_apps_usage_stats
            ON migration.canonical_applications
            (usage_count DESC, last_used_at DESC, client_account_id, engagement_id)
        """
        )

        # Variant usage patterns
        op.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_app_variants_usage_stats
            ON migration.application_name_variants
            (usage_count DESC, last_used_at DESC, canonical_application_id)
        """
        )

        # Verification status for data quality tracking
        op.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_canonical_apps_verification
            ON migration.canonical_applications
            (is_verified, verification_source, confidence_score, client_account_id, engagement_id)
        """
        )

        # RELATIONSHIP INDEXES - For efficient joins and foreign key lookups
        logger.info("🔗 Creating relationship indexes...")

        # Collection flow to canonical application relationships
        op.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_collection_flow_apps_canonical_rel
            ON migration.collection_flow_applications
            (canonical_application_id, collection_flow_id, collection_status)
        """
        )

        # Collection flow to variant relationships
        op.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_collection_flow_apps_variant_rel
            ON migration.collection_flow_applications
            (name_variant_id, collection_flow_id)
            WHERE name_variant_id IS NOT NULL
        """
        )

        # Canonical application to variants relationship
        op.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_app_variants_canonical_rel
            ON migration.application_name_variants
            (canonical_application_id, match_confidence DESC, similarity_score DESC)
        """
        )

        # COMPOSITE INDEXES - For complex queries common in the application
        logger.info("🔧 Creating composite indexes for complex queries...")

        # Tenant-scoped search with usage ranking
        op.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_canonical_apps_tenant_search_ranked
            ON migration.canonical_applications
            (client_account_id, engagement_id, usage_count DESC, canonical_name)
        """
        )

        # Deduplication workflow optimization
        op.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_canonical_apps_dedup_workflow
            ON migration.canonical_applications
            (client_account_id, engagement_id, normalized_name, confidence_score DESC)
        """
        )

        # Variant lookup optimization
        op.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_app_variants_lookup_optimization
            ON migration.application_name_variants
            (client_account_id, engagement_id, normalized_variant, canonical_application_id)
        """
        )

        # Quality assessment index
        op.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_canonical_apps_quality_assessment
            ON migration.canonical_applications
            (client_account_id, engagement_id, is_verified, confidence_score DESC, usage_count DESC)
        """
        )

        # PARTIAL INDEXES - For specific use cases to save space and improve performance
        logger.info("🎯 Creating partial indexes for specific use cases...")

        # Index only unverified applications for quality review workflows
        op.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_canonical_apps_unverified_only
            ON migration.canonical_applications
            (client_account_id, engagement_id, confidence_score DESC, usage_count DESC)
            WHERE is_verified = false
        """
        )

        # Index only high-usage applications for optimization
        op.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_canonical_apps_high_usage_only
            ON migration.canonical_applications
            (client_account_id, engagement_id, last_used_at DESC)
            WHERE usage_count >= 5
        """
        )

        # Index only recent variants for cleanup workflows
        op.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_app_variants_recent_only
            ON migration.application_name_variants
            (canonical_application_id, first_seen_at DESC)
            WHERE first_seen_at >= CURRENT_DATE - INTERVAL '30 days'
        """
        )

        # STATISTICS OPTIMIZATION - Update table statistics for query planner
        logger.info("📈 Updating table statistics for query optimization...")

        op.execute("ANALYZE migration.canonical_applications")
        op.execute("ANALYZE migration.application_name_variants")
        op.execute("ANALYZE migration.collection_flow_applications")

        # CONSTRAINT VALIDATION - Ensure data integrity
        logger.info("🔍 Validating constraint integrity...")

        # Verify tenant isolation constraints
        validation_query = text(
            """
            SELECT
                'canonical_applications' as table_name,
                COUNT(*) as total_rows,
                COUNT(DISTINCT client_account_id) as distinct_clients,
                COUNT(DISTINCT engagement_id) as distinct_engagements,
                COUNT(*) FILTER (WHERE client_account_id IS NULL OR engagement_id IS NULL) as missing_tenant_info
            FROM migration.canonical_applications

            UNION ALL

            SELECT
                'application_name_variants' as table_name,
                COUNT(*) as total_rows,
                COUNT(DISTINCT client_account_id) as distinct_clients,
                COUNT(DISTINCT engagement_id) as distinct_engagements,
                COUNT(*) FILTER (WHERE client_account_id IS NULL OR engagement_id IS NULL) as missing_tenant_info
            FROM migration.application_name_variants

            UNION ALL

            SELECT
                'collection_flow_applications' as table_name,
                COUNT(*) as total_rows,
                COUNT(DISTINCT client_account_id) as distinct_clients,
                COUNT(DISTINCT engagement_id) as distinct_engagements,
                COUNT(*) FILTER (WHERE client_account_id IS NULL OR engagement_id IS NULL) as missing_tenant_info
            FROM migration.collection_flow_applications
        """
        )

        validation_result = conn.execute(validation_query)
        validation_rows = validation_result.fetchall()

        for row in validation_rows:
            logger.info(
                f"📊 {row.table_name}: {row.total_rows} rows, "
                f"{row.distinct_clients} clients, {row.distinct_engagements} engagements"
            )
            if row.missing_tenant_info > 0:
                logger.warning(
                    f"⚠️ {row.missing_tenant_info} rows missing tenant information in {row.table_name}"
                )

        # Final performance recommendation
        logger.info("💡 Performance recommendations:")
        logger.info("   • Consider running VACUUM ANALYZE periodically on these tables")
        logger.info("   • Monitor index usage with pg_stat_user_indexes")
        logger.info(
            "   • Adjust vector index parameters based on data size and query patterns"
        )
        logger.info(
            "   • Consider partitioning by client_account_id for very large datasets"
        )

        conn.commit()
        logger.info("🎉 Index optimization completed successfully!")

    except Exception as e:
        logger.error(f"❌ Index optimization failed: {str(e)}")
        conn.rollback()
        raise


def downgrade() -> None:
    """Remove performance indexes (keep only essential ones)"""

    conn = op.get_bind()

    logger.info("🔄 Starting index optimization downgrade")

    try:
        # Remove performance optimization indexes (keep security/constraint indexes)
        performance_indexes = [
            # Vector similarity indexes
            "idx_canonical_apps_vector_similarity",
            "idx_app_variants_vector_similarity",
            "idx_canonical_apps_vector_ivfflat",
            "idx_app_variants_vector_ivfflat",
            # Usage pattern indexes
            "idx_canonical_apps_usage_stats",
            "idx_app_variants_usage_stats",
            "idx_canonical_apps_verification",
            # Composite optimization indexes
            "idx_canonical_apps_tenant_search_ranked",
            "idx_canonical_apps_dedup_workflow",
            "idx_app_variants_lookup_optimization",
            "idx_canonical_apps_quality_assessment",
            # Partial indexes
            "idx_canonical_apps_unverified_only",
            "idx_canonical_apps_high_usage_only",
            "idx_app_variants_recent_only",
            # Pattern matching indexes
            "idx_canonical_apps_normalized_pattern",
            "idx_app_variants_normalized_pattern",
            "idx_canonical_apps_fulltext_search",
        ]

        for index_name in performance_indexes:
            try:
                op.execute(f"DROP INDEX IF EXISTS migration.{index_name}")
                logger.info(f"🗑️ Removed index: {index_name}")
            except Exception as drop_error:
                logger.warning(
                    f"⚠️ Failed to remove index {index_name}: {str(drop_error)}"
                )

        conn.commit()
        logger.info("✅ Index optimization downgrade completed")

    except Exception as e:
        logger.error(f"❌ Index downgrade failed: {str(e)}")
        conn.rollback()
        raise
