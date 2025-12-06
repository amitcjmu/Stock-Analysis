"""Add JSONB GIN indexes for metadata queries (Issue #987)

Adds GIN indexes on frequently queried JSONB columns to improve query performance
from O(n) full table scans to O(log n) index scans.

Expected Performance Improvement: 10-100x for JSONB queries

Revision ID: 148_add_jsonb_gin_indexes
Revises: 146_add_additional_cmdb_fields_to_assets
Create Date: 2025-12-05
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "148_add_jsonb_gin_indexes"
down_revision = "146_add_additional_cmdb_fields_to_assets"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add GIN indexes on high-priority JSONB columns.

    Priority Order (based on query frequency):
    1. agent_discovered_patterns.pattern_data - Agent pattern matching
    2. discovery_flows.phase_state - Flow phase queries
    3. assets.custom_attributes - Critical attribute queries (Issue #798)
    4. assets.technical_details - Technical metadata queries
    5. collection_flows.collection_config - Flow configuration queries
    6. assessment_flows.flow_metadata - Assessment metadata queries

    Note: Cannot use CREATE INDEX CONCURRENTLY inside transaction block.
    For production deployment on large tables, consider running indexes
    separately outside of Alembic with CONCURRENTLY option.
    """
    # HIGH PRIORITY: agent_discovered_patterns.pattern_data
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_agent_patterns_pattern_data_gin
        ON migration.agent_discovered_patterns
        USING gin (pattern_data);
        """
    )

    # HIGH PRIORITY: discovery_flows.phase_state
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_discovery_flows_phase_state_gin
        ON migration.discovery_flows
        USING gin (phase_state);
        """
    )

    # HIGH PRIORITY: assets.custom_attributes (for Issue #798 queries)
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_assets_custom_attributes_gin
        ON migration.assets
        USING gin (custom_attributes);
        """
    )

    # MEDIUM PRIORITY: assets.technical_details
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_assets_technical_details_gin
        ON migration.assets
        USING gin (technical_details);
        """
    )

    # MEDIUM PRIORITY: collection_flows.collection_config
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_collection_flows_config_gin
        ON migration.collection_flows
        USING gin (collection_config);
        """
    )

    # MEDIUM PRIORITY: assessment_flows.flow_metadata
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_assessment_flows_metadata_gin
        ON migration.assessment_flows
        USING gin (flow_metadata);
        """
    )

    # LOWER PRIORITY: gap_analysis.critical_gaps
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_gap_analysis_critical_gaps_gin
        ON migration.gap_analysis
        USING gin (critical_gaps);
        """
    )


def downgrade() -> None:
    """Remove all GIN indexes (separate statements for reliability)."""
    op.execute("DROP INDEX IF EXISTS migration.ix_gap_analysis_critical_gaps_gin;")
    op.execute("DROP INDEX IF EXISTS migration.ix_assessment_flows_metadata_gin;")
    op.execute("DROP INDEX IF EXISTS migration.ix_collection_flows_config_gin;")
    op.execute("DROP INDEX IF EXISTS migration.ix_assets_technical_details_gin;")
    op.execute("DROP INDEX IF EXISTS migration.ix_assets_custom_attributes_gin;")
    op.execute("DROP INDEX IF EXISTS migration.ix_discovery_flows_phase_state_gin;")
    op.execute("DROP INDEX IF EXISTS migration.ix_agent_patterns_pattern_data_gin;")
