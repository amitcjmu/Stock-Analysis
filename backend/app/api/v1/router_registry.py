"""
Router registration utilities for the v1 API.
This module handles the registration of all routers to reduce complexity
in the main api.py file.
"""

import logging
from fastapi import APIRouter

# from app.api.v1.api_tags import APITags  # Will be used when updating tag assignments

logger = logging.getLogger(__name__)


def register_core_routers(api_router: APIRouter):
    """Register core routers that are always available."""
    from app.api.v1.router_imports import (
        sixr_router,
        analysis_router,
        agents_router,
        agent_learning_router,
        assessment_events_router,
        # assessment_flow_router,  # CC: Disabled due to circular import
        asset_workflow_router,
        asset_inventory_router,
        chat_router,
        context_router,
        data_import_router,
        execute_router,
        monitoring_router,
        context_establishment_router,
        flow_sync_debug_router,
        plan_router,
    )

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


def register_conditional_routers(api_router: APIRouter):
    """Register routers that are conditionally available based on imports."""
    from app.api.v1.router_imports import (
        ANALYSIS_QUEUES_AVAILABLE,
        analysis_queues_router,
        DISCOVERY_AVAILABLE,
        discovery_router,
        UNIFIED_DISCOVERY_AVAILABLE,
        unified_discovery_router,
        dependency_analysis_router,
        agent_insights_router,
        clarifications_router,
        COLLECTION_AVAILABLE,
        collection_router,
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

    # Discovery API (LEGACY - Prefer unified-discovery)
    if DISCOVERY_AVAILABLE:
        api_router.include_router(discovery_router, prefix="/discovery")
        logger.info("✅ Discovery API router included at /discovery (LEGACY)")
        logger.warning(
            "🔄 MIGRATION NOTICE: /discovery endpoints are legacy. Use /unified-discovery instead"
        )
    else:
        logger.warning("⚠️ Discovery API router not available")

    # Collection Flow API
    if COLLECTION_AVAILABLE:
        api_router.include_router(collection_router, prefix="/collection")
        logger.info("✅ Collection Flow API router included at /collection")
    else:
        logger.warning("⚠️ Collection Flow API router not available")

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
        routers_with_flags,
    )

    logger.info("--- Registering Admin Routers ---")

    # Platform Admin
    if ADMIN_ENDPOINTS_AVAILABLE:
        api_router.include_router(platform_admin_router, prefix="/admin/platform")
        logger.info("✅ Platform Admin router included")

        api_router.include_router(security_audit_router, prefix="/admin/security/audit")
        logger.info("✅ Security Audit router included")
    else:
        logger.warning("⚠️ Platform Admin routers not available")

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
