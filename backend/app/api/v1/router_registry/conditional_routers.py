"""
Conditional router registration for the v1 API.
Contains routers that are conditionally available based on feature flags or imports.
"""

import logging
from fastapi import APIRouter


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
