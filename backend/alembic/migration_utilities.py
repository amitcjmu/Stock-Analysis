"""
Migration utilities for Alembic migrations

Common helper functions and utilities for database migrations,
particularly for index creation and optimization tasks.
"""

import logging
from alembic import op
from sqlalchemy import text

logger = logging.getLogger(__name__)


def check_pgvector_availability(conn) -> bool:
    """Check if pgvector extension is available for vector indexes"""
    try:
        conn.execute(text("SELECT 1 FROM pg_extension WHERE extname = 'vector'"))
        logger.info("✅ pgvector extension detected - will create vector indexes")
        return True
    except Exception:
        logger.info("ℹ️ pgvector extension not available - skipping vector indexes")
        return False


def create_tenant_isolation_indexes() -> None:
    """Create multi-tenant isolation enforcement indexes"""
    logger.info("🔒 Creating multi-tenant isolation indexes...")

    # Canonical applications tenant isolation
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


def create_performance_indexes() -> None:
    """Create fast lookup indexes for deduplication and search"""
    logger.info("⚡ Creating fast lookup indexes...")

    # Hash-based exact matching
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

    # Normalized name pattern matching
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

    # Full-text search indexes
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_canonical_apps_fulltext_search
        ON migration.canonical_applications
        USING GIN (to_tsvector('english', canonical_name))
    """
    )


def create_vector_index_for_canonical(conn) -> None:
    """Create vector similarity index for canonical applications"""
    try:
        op.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_canonical_apps_vector_similarity
            ON migration.canonical_applications
            USING hnsw (name_embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 64)
        """
        )
        logger.info(
            "✓ Created HNSW vector index for canonical_applications.name_embedding"
        )
    except Exception as idx_error:
        logger.warning(
            f"⚠️ Failed to create HNSW vector index for canonical applications: {str(idx_error)}"
        )
        # Try IVFFlat as fallback
        try:
            op.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_canonical_apps_vector_similarity
                ON migration.canonical_applications
                USING ivfflat (name_embedding vector_cosine_ops)
                WITH (lists = 100)
            """
            )
            logger.info(
                "✓ Created IVFFlat vector index for canonical_applications.name_embedding"
            )
        except Exception as fallback_error:
            logger.warning(
                f"⚠️ Failed to create vector index (fallback): {str(fallback_error)}"
            )


def create_vector_index_for_variants(conn) -> None:
    """Create vector similarity index for application variants"""
    # First check if variant_embedding column exists
    variant_check = text(
        """
        SELECT column_name, data_type, udt_name
        FROM information_schema.columns
        WHERE table_schema = 'migration'
        AND table_name = 'application_name_variants'
        AND column_name = 'variant_embedding'
    """
    )
    variant_result = conn.execute(variant_check)
    variant_info = variant_result.fetchone()

    if (
        variant_info
        and variant_info.data_type == "USER-DEFINED"
        and variant_info.udt_name == "vector"
    ):
        try:
            op.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_app_variants_vector_similarity
                ON migration.application_name_variants
                USING hnsw (variant_embedding vector_cosine_ops)
                WITH (m = 16, ef_construction = 64)
            """
            )
            logger.info(
                "✓ Created HNSW vector index for application_name_variants.variant_embedding"
            )
        except Exception as variant_idx_error:
            logger.warning(
                f"⚠️ Failed to create HNSW vector index for variants: {str(variant_idx_error)}"
            )
            # Try IVFFlat as fallback
            try:
                op.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_app_variants_vector_similarity
                    ON migration.application_name_variants
                    USING ivfflat (variant_embedding vector_cosine_ops)
                    WITH (lists = 100)
                """
                )
                logger.info(
                    "✓ Created IVFFlat vector index for application_name_variants.variant_embedding"
                )
            except Exception as variant_fallback_error:
                # Fix line length issue here
                error_msg = f"⚠️ Failed to create vector index for variants (fallback): {str(variant_fallback_error)}"
                logger.warning(error_msg)
    else:
        logger.info(
            "ℹ️ variant_embedding column not found or wrong type - skipping variant vector index"
        )


def create_vector_indexes(conn) -> None:
    """Create vector similarity indexes for semantic matching"""
    logger.info("🧠 Creating vector similarity search indexes...")

    try:
        # Check if the column exists and determine its type
        vector_columns_check = text(
            """
            SELECT column_name, data_type, udt_name
            FROM information_schema.columns
            WHERE table_schema = 'migration'
            AND table_name = 'canonical_applications'
            AND column_name = 'name_embedding'
        """
        )

        result = conn.execute(vector_columns_check)
        column_info = result.fetchone()
        has_vector_column = column_info is not None
        is_vector_type = (
            column_info
            and (
                column_info.data_type == "USER-DEFINED"
                and column_info.udt_name == "vector"
            )
            if column_info
            else False
        )

        if has_vector_column and is_vector_type:
            create_vector_index_for_canonical(conn)
            create_vector_index_for_variants(conn)
            logger.info("✅ Vector similarity indexes created successfully")
        else:
            if has_vector_column:
                logger.info(
                    "ℹ️ Vector columns found but are ARRAY(Float) type - skipping vector indexes"
                )
                logger.info(
                    "   Vector indexes require proper vector type from pgvector extension"
                )
            else:
                logger.warning("⚠️ Vector columns not found - skipping vector indexes")

    except Exception as vector_error:
        logger.warning(f"⚠️ Vector index creation failed: {str(vector_error)}")
        logger.info("   Vector similarity search will use sequential scans")


def create_usage_pattern_indexes() -> None:
    """Create indexes for analytics and optimization"""
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


def create_relationship_indexes() -> None:
    """Create indexes for efficient joins and foreign key lookups"""
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


def create_composite_indexes() -> None:
    """Create composite indexes for complex queries"""
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


def create_partial_indexes() -> None:
    """Create partial indexes for specific use cases"""
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

    # Skip time-based partial indexes due to PostgreSQL immutability requirements
    logger.info(
        "ℹ️ Skipping time-based partial indexes (PostgreSQL immutability constraints)"
    )


def update_table_statistics() -> None:
    """Update table statistics for query optimization"""
    logger.info("📈 Updating table statistics for query optimization...")

    op.execute("ANALYZE migration.canonical_applications")
    op.execute("ANALYZE migration.application_name_variants")
    op.execute("ANALYZE migration.collection_flow_applications")


def validate_constraints(conn) -> None:
    """Validate constraint integrity"""
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


def log_performance_recommendations() -> None:
    """Log final performance recommendations"""
    logger.info("💡 Performance recommendations:")
    logger.info("   • Consider running VACUUM ANALYZE periodically on these tables")
    logger.info("   • Monitor index usage with pg_stat_user_indexes")
    logger.info(
        "   • Adjust vector index parameters based on data size and query patterns"
    )
    logger.info(
        "   • Consider partitioning by client_account_id for very large datasets"
    )


def get_performance_index_names() -> list:
    """Get list of performance index names for cleanup operations"""
    return [
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
        # Pattern matching indexes
        "idx_canonical_apps_normalized_pattern",
        "idx_app_variants_normalized_pattern",
        "idx_canonical_apps_fulltext_search",
    ]
