"""
Conditional router registration for the v1 API.
Contains routers that are conditionally available based on feature flags or imports.
"""

import logging
from fastapi import APIRouter

from app.api.v1.api_tags import APITags

logger = logging.getLogger(__name__)


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
        DECOMMISSION_FLOW_AVAILABLE,
        decommission_flow_router,
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

    # Assessment Flow API - ENABLED: Phase 2 of Assessment Flow MFO Migration (Issue #838)
    # Re-enabled with MFO integration layer per ADR-006 two-table pattern
    # Endpoints now route through MFO integration layer in assessment_flow/mfo_integration.py
    try:
        from app.api.v1.router_imports import (
            ASSESSMENT_FLOW_AVAILABLE,
            assessment_flow_router,
        )

        if ASSESSMENT_FLOW_AVAILABLE:
            api_router.include_router(assessment_flow_router, prefix="/assessment-flow")
            logger.info("✅ Assessment Flow API router included at /assessment-flow")
        else:
            logger.warning("⚠️ Assessment Flow API router not available")
    except ImportError as e:
        logger.error(f"❌ Failed to import Assessment Flow router: {e}")
        logger.info("ℹ️ Assessment Flow endpoints accessed via MFO at /master-flows/*")

    # Collection Gaps API - MUST be registered BEFORE collection_router for correct
    # routing. The gap analysis router has more specific routes
    # (/collection/flows/{id}/gaps, /scan-gaps, etc.) that would otherwise be
    # shadowed by the legacy /collection/flows/{id}/gaps endpoint
    if COLLECTION_GAPS_AVAILABLE:
        api_router.include_router(
            # Two-phase gap analysis endpoints (FIRST for precedence)
            collection_gap_analysis_router,
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

    # Decommission Flow API - MFO-integrated (Issue #935)
    if DECOMMISSION_FLOW_AVAILABLE:
        api_router.include_router(decommission_flow_router, prefix="/decommission-flow")
        logger.info("✅ Decommission Flow API router included at /decommission-flow")
    else:
        logger.warning("⚠️ Decommission Flow API router not available")
