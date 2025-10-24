"""
Router registration utilities for the v1 API.
This module handles the registration of all routers to reduce complexity
in the main api.py file.
"""

import logging
from fastapi import APIRouter

from app.api.v1.api_tags import APITags

logger = logging.getLogger(__name__)


def register_core_routers(api_router: APIRouter):
    """Register core routers that are always available."""
    from app.api.v1.router_imports import (
        sixr_router,
        analysis_router,
        agents_router,
        agent_learning_router,
        assessment_events_router,
        # assessment_flow_router,  # Moved to conditional routers
        asset_workflow_router,
        asset_inventory_router,
        asset_conflicts_router,
        chat_router,
        context_router,
        data_import_router,
        execute_router,
        monitoring_router,
        context_establishment_router,
        flow_sync_debug_router,
        plan_router,
    )
    from app.api.v1.endpoints.flow_metadata import router as flow_metadata_router

    logger.info("--- Registering Core Routers ---")

    # Core Discovery and Analysis
    api_router.include_router(sixr_router, prefix="/6r")
    api_router.include_router(analysis_router, prefix="/analysis")
    logger.info("✅ Core analysis routers registered")

    # Agent Management
    api_router.include_router(agents_router, prefix="/agents")
    api_router.include_router(agent_learning_router, prefix="/agent-learning")
    logger.info("✅ Agent management routers registered")

    # Assessment and Workflow
    api_router.include_router(assessment_events_router, prefix="/assessment-events")
    # api_router.include_router(assessment_flow_router,
    #                           prefix="/assessment-flow")  # Disabled - circular import
    api_router.include_router(asset_workflow_router, prefix="/asset-workflow")
    api_router.include_router(execute_router, prefix="/execute")
    logger.info("✅ Assessment and workflow routers registered")

    # Asset Management
    api_router.include_router(asset_inventory_router, prefix="/asset-inventory")
    api_router.include_router(
        asset_conflicts_router
    )  # Uses prefix from router definition
    logger.info("✅ Asset management routers registered")

    # Communication and Context
    api_router.include_router(chat_router, prefix="/chat")
    api_router.include_router(context_router, prefix="/context")
    api_router.include_router(
        context_establishment_router, prefix="/context-establishment"
    )
    logger.info("✅ Communication and context routers registered")

    # Data and Monitoring
    api_router.include_router(data_import_router, prefix="/data-import")
    api_router.include_router(monitoring_router, prefix="/monitoring")
    api_router.include_router(flow_sync_debug_router, prefix="/flow-sync-debug")
    logger.info("✅ Data and monitoring routers registered")

    # Planning
    api_router.include_router(plan_router, prefix="/plan")
    logger.info("✅ Plan router registered")

    # Flow Metadata (for FlowTypeConfig pattern per ADR-027)
    api_router.include_router(flow_metadata_router)
    logger.info("✅ Flow metadata router registered")


def register_conditional_routers(api_router: APIRouter):
    """Register routers that are conditionally available based on imports."""
    from app.api.v1.router_imports import (
        ANALYSIS_QUEUES_AVAILABLE,
        analysis_queues_router,
        DISCOVERY_AVAILABLE,
        # discovery_router removed - legacy endpoints deprecated
        UNIFIED_DISCOVERY_AVAILABLE,
        unified_discovery_router,
        dependency_analysis_router,
        agent_insights_router,
        clarifications_router,
        # ASSESSMENT_FLOW_AVAILABLE,  # Currently disabled
        # assessment_flow_router,     # Currently disabled
        COLLECTION_AVAILABLE,
        collection_flows_router,
        collection_post_completion_router,
        collection_bulk_ops_router,
        COLLECTION_GAPS_AVAILABLE,
        collection_gaps_vendor_products_router,
        collection_gaps_maintenance_windows_router,
        collection_gaps_governance_router,
        collection_gaps_assets_router,
        collection_gaps_collection_flows_router,
        collection_gap_analysis_router,
        FLOW_PROCESSING_AVAILABLE,
        flow_processing_router,
        routers_with_flags,
    )

    logger.info("--- Registering Conditional Routers ---")

    # Analysis Queues
    if ANALYSIS_QUEUES_AVAILABLE:
        api_router.include_router(analysis_queues_router, prefix="/analysis")
        logger.info("✅ Analysis Queues router included at /analysis/queues")
    else:
        logger.warning("⚠️ Analysis Queues router not available")

    # Discovery API - REMOVED: Legacy endpoints have been removed
    # Use MFO or unified-discovery instead
    if DISCOVERY_AVAILABLE:
        logger.error(
            "❌ LEGACY DISCOVERY ROUTER DETECTED BUT NOT REGISTERED. "
            "Legacy endpoints are deprecated and must be removed from the codebase. "
            "Use MFO or unified-discovery instead."
        )
        # DO NOT register the legacy discovery router - it violates MFO-first architecture

    # Assessment Flow API - DISABLED: Must use MFO endpoints (/api/v1/master-flows/*)
    # Direct assessment-flow endpoints violate MFO architecture principles
    # All assessment operations should go through Master Flow Orchestrator
    # if ASSESSMENT_FLOW_AVAILABLE:
    #     api_router.include_router(assessment_flow_router, prefix="/assessment-flow")
    #     logger.info("✅ Assessment Flow API router included at /assessment-flow")
    # else:
    #     logger.warning("⚠️ Assessment Flow API router not available")
    logger.info("ℹ️ Assessment Flow endpoints accessed via MFO at /master-flows/*")

    # Collection Gaps API - MUST be registered BEFORE collection_router for correct routing
    # The gap analysis router has more specific routes (/collection/flows/{id}/gaps, /scan-gaps, etc.)
    # that would otherwise be shadowed by the legacy /collection/flows/{id}/gaps endpoint
    if COLLECTION_GAPS_AVAILABLE:
        api_router.include_router(
            collection_gap_analysis_router,  # Two-phase gap analysis endpoints (FIRST for precedence)
            tags=[APITags.COLLECTION_GAP_ANALYSIS],
        )
        api_router.include_router(
            collection_gaps_vendor_products_router, prefix="/collection"
        )
        api_router.include_router(
            collection_gaps_maintenance_windows_router, prefix="/collection"
        )
        api_router.include_router(
            collection_gaps_governance_router, prefix="/collection"
        )
        api_router.include_router(collection_gaps_assets_router, prefix="/collection")
        api_router.include_router(
            collection_gaps_collection_flows_router, prefix="/collection"
        )
        logger.info(
            (
                "✅ Collection Gaps API routers included at /collection/vendor-products, "
                "/collection/maintenance-windows, /collection/governance, "
                "/collection/assets, /collection/collection-flows, "
                "/collection/flows/{flow_id}/gaps|scan-gaps|analyze-gaps|update-gaps"
            )
        )
    else:
        logger.warning("⚠️ Collection Gaps API routers not available")

    # Collection Flow API - Registered AFTER gap analysis router to avoid shadowing
    if COLLECTION_AVAILABLE:
        # Legacy Collection Flow API (from collection_flows.py)
        api_router.include_router(collection_flows_router, prefix="/collection")
        logger.info("✅ Collection Flow API router included at /collection")

        # Collection Post-Completion API - Asset resolution after collection
        api_router.include_router(
            collection_post_completion_router, prefix="/collection"
        )
        logger.info("✅ Collection Post-Completion router included at /collection")

        # Collection Bulk Operations API - Adaptive Questionnaire Enhancements
        # Aggregated router from collection/__init__.py includes:
        # - bulk_answer (bulk-answer-preview, bulk-answer)
        # - dynamic_questions (questions/filtered, dependency-change)
        # - bulk_import (bulk-import/analyze, bulk-import/execute, bulk-import/status)
        # - gap_analysis (gap-analysis)
        api_router.include_router(
            collection_bulk_ops_router,
            prefix="/collection",
            tags=[APITags.COLLECTION_BULK_OPERATIONS],
        )
        logger.info(
            "✅ Collection Bulk Operations router included at /collection "
            "(bulk-answer, questions/filtered, bulk-import, gap-analysis)"
        )
    else:
        logger.warning(
            "⚠️ Collection Flow API and Bulk Operations routers not available"
        )

    # Flow Processing API
    if FLOW_PROCESSING_AVAILABLE:
        api_router.include_router(flow_processing_router, prefix="/flow-processing")
        logger.info("✅ Flow Processing API router included at /flow-processing")
    else:
        logger.warning("⚠️ Flow Processing API router not available")

    # Blocking flows check
    if routers_with_flags.get("BLOCKING_FLOWS", (False, None))[0]:
        blocking_flows_router = routers_with_flags["BLOCKING_FLOWS"][1]
        api_router.include_router(blocking_flows_router, prefix="/blocking-flows")
        logger.info("✅ Simple blocking flows check included at /blocking-flows")
    else:
        logger.warning("⚠️ Blocking flows router not available")

    # Unified Discovery Flow API
    if UNIFIED_DISCOVERY_AVAILABLE:
        api_router.include_router(unified_discovery_router, prefix="/unified-discovery")
        logger.info(
            "✅ Unified Discovery Flow API router included at /unified-discovery"
        )

        api_router.include_router(
            dependency_analysis_router, prefix="/unified-discovery/dependencies"
        )
        logger.info(
            "✅ Dependency Analysis router included at /unified-discovery/dependencies"
        )

        api_router.include_router(agent_insights_router, prefix="/unified-discovery")
        logger.info("✅ Agent Insights router included at /unified-discovery")

        api_router.include_router(clarifications_router, prefix="/unified-discovery")
        logger.info("✅ Clarifications router included at /unified-discovery")
    else:
        logger.warning("⚠️ Unified Discovery Flow API router not available")


def register_utility_routers(api_router: APIRouter):
    """Register utility and system routers."""
    from app.api.v1.router_imports import (
        routers_with_flags,
        API_HEALTH_AVAILABLE,
        api_health_router,
    )

    logger.info("--- Registering Utility Routers ---")

    # API Health endpoints
    if API_HEALTH_AVAILABLE:
        api_router.include_router(api_health_router, prefix="/api-health")
        logger.info("✅ API Health router included")

    # Test Diagnostics endpoints (for E2E testing only)
    import os

    if os.getenv("E2E_TEST_MODE", "false").lower() == "true":
        try:
            from app.api.v1.endpoints.test_diagnostics import (
                router as test_diagnostics_router,
            )

            api_router.include_router(test_diagnostics_router, prefix="/test")
            logger.info(
                "✅ Test Diagnostics router included at /test (E2E testing only)"
            )
        except ImportError as e:
            logger.warning(f"Test Diagnostics router import failed: {e}")
    else:
        logger.debug("Test Diagnostics router not enabled (E2E_TEST_MODE not set)")

    # Health endpoints
    if routers_with_flags.get("HEALTH", (False, None))[0]:
        health_router = routers_with_flags["HEALTH"][1]
        api_router.include_router(health_router, prefix="/health")
        logger.info("✅ Health router included")

    if routers_with_flags.get("LLM_HEALTH", (False, None))[0]:
        llm_health_router = routers_with_flags["LLM_HEALTH"][1]
        api_router.include_router(llm_health_router, prefix="/llm")
        logger.info("✅ LLM Health router included")

    # Data Cleansing endpoints
    if routers_with_flags.get("DATA_CLEANSING", (False, None))[0]:
        data_cleansing_router = routers_with_flags["DATA_CLEANSING"][1]
        api_router.include_router(data_cleansing_router)
        logger.info("✅ Data Cleansing router included (prefix removed)")

        # Backward compatibility
        api_router.include_router(data_cleansing_router, prefix="/data-cleansing")
        logger.info("✅ Data Cleansing legacy compatibility router included")
    else:
        logger.warning("⚠️ Data Cleansing router not available")

    # Observability
    if routers_with_flags.get("OBSERVABILITY", (False, None))[0]:
        observability_router = routers_with_flags["OBSERVABILITY"][1]
        api_router.include_router(observability_router, prefix="/observability")
        logger.info("✅ Observability router included")
    else:
        logger.warning("⚠️ Observability router not available")


def register_admin_routers(api_router: APIRouter):
    """Register admin and security routers."""
    from app.api.v1.router_imports import (
        ADMIN_ENDPOINTS_AVAILABLE,
        platform_admin_router,
        security_audit_router,
        llm_usage_router,
        memory_management_router,
        routers_with_flags,
    )
    from app.api.v1.endpoints.admin_flows import router as admin_flows_router

    logger.info("--- Registering Admin Routers ---")

    # Platform Admin
    if ADMIN_ENDPOINTS_AVAILABLE:
        api_router.include_router(platform_admin_router, prefix="/admin/platform")
        logger.info("✅ Platform Admin router included")

        api_router.include_router(security_audit_router, prefix="/admin/security/audit")
        logger.info("✅ Security Audit router included")

        api_router.include_router(
            llm_usage_router, prefix="/admin/llm-usage", tags=[APITags.ADMIN_LLM_USAGE]
        )
        logger.info("✅ LLM Usage router included")

        api_router.include_router(memory_management_router, tags=[APITags.ADMIN])
        logger.info("✅ Memory Management router included")
    else:
        logger.warning("⚠️ Platform Admin routers not available")

    # Admin Flow Management (Bug #651 fix - cleanup stale flows)
    api_router.include_router(admin_flows_router, prefix="/admin", tags=[APITags.ADMIN])
    logger.info("✅ Admin Flow Management router included")

    # RBAC Admin
    if routers_with_flags.get("RBAC_ADMIN", (False, None))[0]:
        rbac_admin_router = routers_with_flags["RBAC_ADMIN"][1]
        api_router.include_router(rbac_admin_router, prefix="/admin/rbac")
        logger.info("✅ RBAC Admin router included")
    else:
        logger.warning("⚠️ RBAC Admin router not available")

    # Client Management Admin
    if routers_with_flags.get("CLIENT_MANAGEMENT", (False, None))[0]:
        client_management_router = routers_with_flags["CLIENT_MANAGEMENT"][1]
        api_router.include_router(client_management_router, prefix="/admin/clients")
        logger.info("✅ Client Management router included")
    else:
        logger.warning("⚠️ Client Management router not available")

    # Engagement Management Admin
    if routers_with_flags.get("ENGAGEMENT_MANAGEMENT", (False, None))[0]:
        engagement_management_router = routers_with_flags["ENGAGEMENT_MANAGEMENT"][1]
        api_router.include_router(
            engagement_management_router, prefix="/admin/engagements"
        )
        logger.info("✅ Engagement Management router included")
    else:
        logger.warning("⚠️ Engagement Management router not available")

    # Flow Comparison Admin
    if routers_with_flags.get("FLOW_COMPARISON", (False, None))[0]:
        flow_comparison_router = routers_with_flags["FLOW_COMPARISON"][1]
        api_router.include_router(
            flow_comparison_router, prefix="/admin/flow-comparison"
        )
        logger.info("✅ Flow Comparison router included")
    else:
        logger.warning("⚠️ Flow Comparison router not available")

    # User Approvals
    if routers_with_flags.get("USER_APPROVALS", (False, None))[0]:
        user_approvals_router = routers_with_flags["USER_APPROVALS"][1]
        api_router.include_router(user_approvals_router, prefix="/admin/user-approvals")
        logger.info("✅ User Approvals router included")
    else:
        logger.warning("⚠️ User Approvals router not available")

    # Simple Admin
    if routers_with_flags.get("SIMPLE_ADMIN", (False, None))[0]:
        simple_admin_router = routers_with_flags["SIMPLE_ADMIN"][1]
        api_router.include_router(simple_admin_router)
        logger.info("✅ Simple Admin router included")
    else:
        logger.warning("⚠️ Simple Admin router not available")

    # Rate Limiting Admin
    if routers_with_flags.get("RATE_LIMITING", (False, None))[0]:
        rate_limiting_router = routers_with_flags["RATE_LIMITING"][1]
        api_router.include_router(rate_limiting_router, prefix="/admin/rate-limiting")
        logger.info("✅ Rate Limiting router included")
    else:
        logger.warning("⚠️ Rate Limiting router not available")

    # User Access Management Admin
    if routers_with_flags.get("ADMIN_USER_ACCESS", (False, None))[0]:
        admin_user_access_router = routers_with_flags["ADMIN_USER_ACCESS"][1]
        api_router.include_router(admin_user_access_router, prefix="/admin/user-access")
        logger.info("✅ Admin User Access router included")
    else:
        logger.warning("⚠️ Admin User Access router not available")


def register_auth_routers(api_router: APIRouter):
    """Register authentication routers."""
    from app.api.v1.router_imports import routers_with_flags

    logger.info("--- Registering Auth Routers ---")

    if routers_with_flags.get("AUTH_RBAC", (False, None))[0]:
        auth_router = routers_with_flags["AUTH_RBAC"][1]
        api_router.include_router(auth_router, prefix="/auth")
        logger.info("✅ Auth RBAC router included")
    else:
        logger.warning("⚠️ Auth RBAC router not available")


def register_special_routers(api_router: APIRouter):
    """Register special purpose routers (emergency, websocket, etc.)."""
    from app.api.v1.router_imports import routers_with_flags

    logger.info("--- Registering Special Routers ---")

    # Emergency System Control
    if routers_with_flags.get("EMERGENCY", (False, None))[0]:
        emergency_router = routers_with_flags["EMERGENCY"][1]
        api_router.include_router(emergency_router, prefix="/system")
        logger.info("✅ Emergency System Control router included")
    else:
        logger.warning("⚠️ Emergency System Control router not available")

    # Flow Health
    if routers_with_flags.get("FLOW_HEALTH", (False, None))[0]:
        flow_health_router = routers_with_flags["FLOW_HEALTH"][1]
        api_router.include_router(flow_health_router, prefix="/flows/health")
        logger.info("✅ Flow Health router included")
    else:
        logger.warning("⚠️ Flow Health router not available")

    # Agent Events for SSE
    if routers_with_flags.get("AGENT_EVENTS", (False, None))[0]:
        agent_events_router = routers_with_flags["AGENT_EVENTS"][1]
        api_router.include_router(agent_events_router, prefix="/agent-events")
        logger.info("✅ Agent Events router included")
    else:
        logger.warning("⚠️ Agent Events router not available")

    # Master Flows
    if routers_with_flags.get("MASTER_FLOWS", (False, None))[0]:
        master_flows_router = routers_with_flags["MASTER_FLOWS"][1]
        api_router.include_router(master_flows_router, prefix="/master-flows")
        logger.info("✅ Master Flows router included")
    else:
        logger.warning("⚠️ Master Flows router not available")

    # FinOps
    if routers_with_flags.get("FINOPS", (False, None))[0]:
        finops_router = routers_with_flags["FINOPS"][1]
        api_router.include_router(finops_router)
        logger.info("✅ FinOps router included")
    else:
        logger.warning("⚠️ FinOps router not available")

    # Canonical Applications
    if routers_with_flags.get("CANONICAL_APPLICATIONS", (False, None))[0]:
        canonical_applications_router = routers_with_flags["CANONICAL_APPLICATIONS"][1]
        api_router.include_router(
            canonical_applications_router, prefix="/canonical-applications"
        )
        logger.info(
            "✅ Canonical Applications router included at /canonical-applications"
        )
    else:
        logger.warning("⚠️ Canonical Applications router not available")


def register_all_routers(api_router: APIRouter):
    """Register all routers in organized groups."""
    # Validate endpoint migration mappings on startup
    try:
        from app.utils.endpoint_migration_logger import validate_endpoint_migration

        validate_endpoint_migration()
    except ImportError as e:
        logger.warning(f"Endpoint migration validation skipped: {e}")

    register_core_routers(api_router)
    register_conditional_routers(api_router)
    register_utility_routers(api_router)
    register_admin_routers(api_router)
    register_auth_routers(api_router)
    register_special_routers(api_router)
    logger.info("--- Router Registration Complete ---")
