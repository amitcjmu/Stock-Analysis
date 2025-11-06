"""
Core router registration for the v1 API.
Contains routers that are always available (not feature-flagged).
"""

import logging
from fastapi import APIRouter

from app.api.v1.api_tags import APITags

logger = logging.getLogger(__name__)


def register_core_routers(api_router: APIRouter):
    """Register core routers that are always available."""
    from app.api.v1.router_imports import (
        # sixr_router removed - replaced by Assessment Flow with MFO
        # integration (Phase 4, Issue #840)
        analysis_router,
        agents_router,
        agent_learning_router,
        assessment_events_router,
        # assessment_flow_router,  # Moved to conditional routers
        asset_workflow_router,
        asset_inventory_router,
        asset_conflicts_router,
        asset_preview_router,
        asset_editing_router,
        chat_router,
        context_router,
        data_import_router,
        execute_router,
        field_mapping_router,
        monitoring_router,
        context_establishment_router,
        flow_sync_debug_router,
        plan_router,
    )
    from app.api.v1.endpoints.flow_metadata import router as flow_metadata_router

    logger.info("--- Registering Core Routers ---")

    # Core Discovery and Analysis
    # /6r/* endpoints removed - replaced by Assessment Flow with MFO
    # integration (Phase 4, Issue #840)
    # All 6R analysis functionality now available at /assessment-flow/* endpoints
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
    api_router.include_router(asset_conflicts_router)  # Uses prefix from router
    api_router.include_router(asset_preview_router)  # Uses prefix from router
    api_router.include_router(
        asset_editing_router, prefix="/unified-discovery/assets", tags=[APITags.ASSETS]
    )  # Issues #911, #912 - Align with frontend routing
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
    api_router.include_router(
        field_mapping_router
    )  # Uses /field-mapping prefix from router
    api_router.include_router(monitoring_router, prefix="/monitoring")
    api_router.include_router(flow_sync_debug_router, prefix="/flow-sync-debug")
    logger.info("✅ Data and monitoring routers registered")

    # Planning
    api_router.include_router(plan_router, prefix="/plan")
    logger.info("✅ Plan router registered")

    # Flow Metadata (for FlowTypeConfig pattern per ADR-027)
    api_router.include_router(flow_metadata_router)
    logger.info("✅ Flow metadata router registered")
