"""
Client Cascade Delete Operations

Handles the complex FK dependency chain for deleting client accounts.
Tables are deleted in order of dependency (children first, then parents).
"""

import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Tables that reference other child tables (deepest dependencies first)
CHILD_TABLES_OF_CHILD_TABLES = [
    # These reference data_imports
    "raw_import_records",
    "import_field_mappings",
    # These reference flows
    "collection_answer_history",
    "collection_flow_applications",
    "collection_gap_analysis",
    "collection_question_rules",
    "adaptive_questionnaires",
    # These reference assets
    "asset_contacts",
    "asset_custom_attributes",
    "asset_dependencies",
    "asset_eol_assessments",
    "asset_field_conflicts",
    "asset_conflict_resolutions",
    # These reference canonical_applications
    "application_name_variants",
    "application_components",
    # These reference timelines
    "timeline_milestones",
    "timeline_phases",
    # These reference decommission plans
    "decommission_validation_checks",
    "decommission_execution_logs",
    # These reference resource pools
    "resource_allocations",
    "resource_skills",
    # These reference archive policies
    "archive_jobs",
]

# Main tables with direct client_account_id reference
DIRECT_REFERENCE_TABLES = [
    # Flow tables (must delete before crewai_flow_state_extensions)
    "discovery_flows",
    "collection_flows",
    "assessment_flows",
    "decommission_flows",
    "planning_flows",
    # The master flow table
    "crewai_flow_state_extensions",
    # Asset and related
    "assets",
    # Data management
    "data_imports",
    "data_retention_policies",
    "data_cleansing_recommendations",
    # Application tracking
    "canonical_applications",
    # Assessment related
    "assessments",
    "sixr_analyses_archive",
    "tech_debt_analysis",
    "sixr_decisions",
    "assessment_learning_feedback",
    "engagement_architecture_standards",
    # Wave and migration planning
    "migration_waves",
    "migration_exceptions",
    "project_timelines",
    "resource_pools",
    # Agent and performance tracking
    "agent_task_history",
    "agent_execution_history",
    "agent_performance_daily",
    "agent_discovered_patterns",
    # Decommission
    "decommission_plans",
    # Caching and audit
    "cache_configurations",
    "cache_invalidation_logs",
    "cache_metadata",
    "cache_performance_logs",
    "access_audit_log",
    "enhanced_access_audit_log",
    "flow_deletion_audit",
    "failure_journal",
    # Feedback and usage
    "feedback",
    "feedback_summaries",
    "llm_usage_logs",
    "llm_usage_summary",
    # Maintenance and scheduling
    "maintenance_windows",
    "blackout_periods",
    # Approval workflows
    "approval_requests",
    # Vendor and credentials
    "tenant_vendor_products",
    "platform_credentials",
    # Field mapping and rules
    "field_dependency_rules",
    "custom_attribute_schemas",
    # Background tasks
    "collection_background_tasks",
    # User associations and access
    "user_account_associations",
    "engagement_access",
    "client_access",
    # Finally, engagements
    "engagements",
]


async def cascade_delete_client_data(db: AsyncSession, client_id: str) -> None:
    """Delete all data from tables that reference client_account_id.

    This handles the complete FK dependency chain to avoid constraint violations.
    Tables are deleted in order of dependency (children first, then parents).
    """
    # First, get all engagement IDs for this client (needed for engagement-scoped tables)
    engagement_ids_result = await db.execute(
        text("SELECT id FROM engagements WHERE client_account_id = :client_id"),
        {"client_id": client_id},
    )
    engagement_ids = [str(row[0]) for row in engagement_ids_result.fetchall()]

    # Delete from child tables first
    for table in CHILD_TABLES_OF_CHILD_TABLES:
        try:
            # First try with engagement_id for engagement-scoped tables
            if engagement_ids:
                await db.execute(
                    text(
                        f"DELETE FROM {table} WHERE engagement_id IN :engagement_ids"
                    ),  # noqa: S608
                    {"engagement_ids": tuple(engagement_ids)},
                )
            # Then try with client_account_id
            await db.execute(
                text(
                    f"DELETE FROM {table} WHERE client_account_id = :client_id"
                ),  # noqa: S608
                {"client_id": client_id},
            )
        except Exception as e:
            logger.debug(f"Table {table} cleanup (may not exist or no data): {e}")

    # Delete from main tables with direct client_account_id reference
    for table in DIRECT_REFERENCE_TABLES:
        try:
            await db.execute(
                text(
                    f"DELETE FROM {table} WHERE client_account_id = :client_id"
                ),  # noqa: S608
                {"client_id": client_id},
            )
        except Exception as e:
            logger.debug(f"Table {table} cleanup (may not exist or no data): {e}")

    # Update user references to NULL (don't delete users)
    try:
        await db.execute(
            text(
                "UPDATE users SET default_client_id = NULL WHERE default_client_id = :client_id"
            ),
            {"client_id": client_id},
        )
        await db.execute(
            text(
                "UPDATE user_roles SET scope_client_id = NULL WHERE scope_client_id = :client_id"
            ),
            {"client_id": client_id},
        )
    except Exception as e:
        logger.debug(f"User reference cleanup: {e}")
