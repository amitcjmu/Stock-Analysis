"""
Utility functions for engagement CRUD operations
"""

import logging

from sqlalchemy import text

from app.core.security.cache_encryption import secure_setattr

logger = logging.getLogger(__name__)


def _update_basic_fields(engagement, field, value):
    """Update basic engagement fields. Returns True if field was handled."""
    if field == "engagement_name" and value:
        engagement.name = value
        return True
    elif field == "engagement_description" and value:
        engagement.description = value
        return True
    elif field == "target_cloud_provider" and value:
        engagement.engagement_type = value
        return True
    elif field in ["migration_phase", "current_phase"] and value:
        engagement.status = value
        return True
    elif field == "engagement_manager" and value:
        engagement.client_contact_name = value
        return True
    elif field == "client_account_id" and value:
        engagement.client_account_id = value
        return True
    return False


def _ensure_settings_dict(engagement):
    """Ensure settings is a valid dictionary."""
    current_settings = engagement.settings or {}
    if not isinstance(current_settings, dict):
        current_settings = {}
    return current_settings


def _update_settings_fields(engagement, field, value):
    """Update fields stored in engagement settings."""
    if field == "technical_lead" and value:
        current_settings = _ensure_settings_dict(engagement)
        current_settings["technical_lead"] = value
        engagement.settings = current_settings
        return True
    elif field == "budget" and value is not None:
        current_settings = _ensure_settings_dict(engagement)
        current_settings["estimated_budget"] = float(value)
        engagement.settings = current_settings
        return True
    elif field == "budget_currency" and value:
        current_settings = _ensure_settings_dict(engagement)
        current_settings["budget_currency"] = value
        engagement.settings = current_settings
        return True
    return False


def _update_date_fields(engagement, field, value, parse_date_string):
    """Update date fields with proper parsing."""
    if field in ["start_date", "planned_start_date"] and value:
        parsed_date = parse_date_string(value)
        if parsed_date:
            engagement.start_date = parsed_date
            return True
    elif field in ["end_date", "planned_end_date"] and value:
        parsed_date = parse_date_string(value)
        if parsed_date:
            engagement.target_completion_date = parsed_date
            return True
    return False


def _update_migration_scope(engagement, field, value):
    """Update migration scope field."""
    if field == "migration_scope" and value:
        current_scope = engagement.migration_scope or {}
        if not isinstance(current_scope, dict):
            current_scope = {}
        current_scope["scope_type"] = value
        engagement.migration_scope = current_scope
        return True
    return False


def _process_field_updates(engagement, update_dict, parse_date_string):
    """Process all field updates for the engagement."""
    for field, value in update_dict.items():
        # Try updating basic fields
        if _update_basic_fields(engagement, field, value):
            continue

        # Try updating settings fields
        if _update_settings_fields(engagement, field, value):
            continue

        # Try updating date fields
        if _update_date_fields(engagement, field, value, parse_date_string):
            continue

        # Try updating migration scope
        if _update_migration_scope(engagement, field, value):
            continue

        # Fall back to direct field update if field exists
        if hasattr(engagement, field):
            secure_setattr(engagement, field, value)


async def _delete_dependent_records(db, engagement_id):
    """Delete records that depend on data_imports."""
    # Delete raw import records
    await db.execute(
        text(
            """
            DELETE FROM raw_import_records
            WHERE data_import_id IN (
                SELECT id FROM data_imports
                WHERE engagement_id = :engagement_id
            )
        """
        ),
        {"engagement_id": engagement_id},
    )

    # Delete import field mappings
    await db.execute(
        text(
            """
            DELETE FROM import_field_mappings
            WHERE data_import_id IN (
                SELECT id FROM data_imports
                WHERE engagement_id = :engagement_id
            )
        """
        ),
        {"engagement_id": engagement_id},
    )


async def _delete_engagement_tables(db, engagement_id):
    """Delete records from engagement-related tables.

    This handles the complete FK dependency chain for all 64+ tables that
    reference engagement_id. Tables are deleted in order of dependency
    (children first, then parents).
    """
    # Tables that reference other child tables (deepest dependencies first)
    child_tables_of_child_tables = [
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

    for table in child_tables_of_child_tables:
        try:
            await db.execute(
                text(
                    f"DELETE FROM {table} WHERE engagement_id = :engagement_id"
                ),  # noqa: S608
                {"engagement_id": engagement_id},
            )
        except Exception as e:
            logger.debug(f"Table {table} cleanup (may not exist or no data): {e}")

    # All tables with direct engagement_id FK reference (comprehensive list)
    direct_reference_tables = [
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
        "cache_metadata",
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
        # Field mapping and rules
        "field_dependency_rules",
        # Background tasks
        "collection_background_tasks",
        # User associations and access
        "engagement_access",
    ]

    for table in direct_reference_tables:
        try:
            await db.execute(
                text(
                    f"DELETE FROM {table} WHERE engagement_id = :engagement_id"
                ),  # noqa: S608
                {"engagement_id": engagement_id},
            )
        except Exception as table_error:
            logger.debug(
                f"Table {table} cleanup (may not exist or no data): {table_error}"
            )
            # Continue with other tables


async def _update_user_references(db, engagement_id):
    """Update user references to set engagement fields to NULL."""
    # Update users table
    await db.execute(
        text(
            """
            UPDATE users
            SET default_engagement_id = NULL
            WHERE default_engagement_id = :engagement_id
        """
        ),
        {"engagement_id": engagement_id},
    )

    # Update user roles
    await db.execute(
        text(
            """
            UPDATE user_roles
            SET scope_engagement_id = NULL
            WHERE scope_engagement_id = :engagement_id
        """
        ),
        {"engagement_id": engagement_id},
    )


async def _perform_cascade_deletion(db, engagement_id, engagement):
    """Perform cascade deletion of engagement and all related records atomically."""
    # Use a transaction to ensure atomicity - if any step fails, all changes rollback
    async with db.begin():
        # Delete dependent records first
        await _delete_dependent_records(db, engagement_id)

        # Delete from engagement-related tables
        await _delete_engagement_tables(db, engagement_id)

        # Update user references
        await _update_user_references(db, engagement_id)

        # Finally delete the engagement itself
        await db.delete(engagement)
        # Note: No explicit commit needed - the context manager handles it


async def _perform_soft_delete(db, engagement):
    """Perform soft delete when cascade deletion fails."""
    engagement.is_active = False
    engagement.status = "deleted"
    await db.commit()
