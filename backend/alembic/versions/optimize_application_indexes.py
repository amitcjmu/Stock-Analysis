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
import logging
import sys
import os

# Add alembic directory to path to import migration utilities
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from migration_utilities import (
    check_pgvector_availability,
    create_tenant_isolation_indexes,
    create_performance_indexes,
    create_vector_indexes,
    create_usage_pattern_indexes,
    create_relationship_indexes,
    create_composite_indexes,
    create_partial_indexes,
    update_table_statistics,
    validate_constraints,
    log_performance_recommendations,
    get_performance_index_names,
)

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
        # Check if pgvector extension is available
        pgvector_available = check_pgvector_availability(conn)

        # Create all index types using utility functions
        create_tenant_isolation_indexes()
        create_performance_indexes()

        # Create vector indexes if available
        if pgvector_available:
            create_vector_indexes(conn)

        create_usage_pattern_indexes()
        create_relationship_indexes()
        create_composite_indexes()
        create_partial_indexes()
        update_table_statistics()
        validate_constraints(conn)
        log_performance_recommendations()

        logger.info("🎉 Index optimization completed successfully!")

    except Exception as e:
        logger.error(f"❌ Index optimization failed: {str(e)}")
        # Don't call rollback in alembic migrations - it handles transactions
        raise


def downgrade() -> None:
    """Remove performance indexes (keep only essential ones)"""
    logger.info("🔄 Starting index optimization downgrade")

    try:
        # Get performance index names from utilities
        performance_indexes = get_performance_index_names()

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
        # Don't call rollback in alembic migrations - it handles transactions
        raise
