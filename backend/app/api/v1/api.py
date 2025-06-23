"""
Main API router for the AI Force Migration Platform.
Includes all endpoint routers and API versioning.
"""

from fastapi import APIRouter
import logging

from app.api.v1.endpoints import (
    sixr_router,
    discovery_router,
    asset_inventory_router,
    monitoring_router,
    chat_router,
    agent_learning_router,
    data_import_router,
    sessions_router,
    context_router,
    test_discovery_router,
    agents_router,
)

from app.api.v1.endpoints.discovery_flow_management import router as discovery_flow_management_router

from app.api.v1.endpoints.context_establishment import router as context_establishment_router

from app.api.v1.unified_discovery import router as unified_discovery_router
from app.api.v1.routes.llm_health import router as llm_health_router

from app.api.v1.admin.client_management import router as client_management_router
from app.api.v1.admin.engagement_management import export_router as engagement_management_router
from app.api.v1.admin.platform_admin_handlers import router as platform_admin_router
from app.api.v1.auth.handlers.user_management_handlers import user_management_router as user_approvals_router
from app.api.v1.auth.rbac import router as auth_router


# Setup logger
logger = logging.getLogger(__name__)

# --- API Router Setup ---
api_router = APIRouter()

# --- Include All Routers ---
logger.info("--- Starting API Router Inclusion Process ---")

api_router.include_router(sixr_router, prefix="/sixr", tags=["6R Analysis"])
api_router.include_router(discovery_router, prefix="/discovery", tags=["Discovery"])
api_router.include_router(unified_discovery_router, prefix="", tags=["Unified Discovery Flow"])
api_router.include_router(discovery_flow_management_router, prefix="/discovery", tags=["Discovery Flow Management"])
api_router.include_router(asset_inventory_router, prefix="/assets", tags=["Asset Inventory"])
api_router.include_router(llm_health_router, prefix="/llm", tags=["LLM Health"])
api_router.include_router(data_import_router, prefix="/data-import", tags=["Data Import"])
api_router.include_router(monitoring_router, prefix="/monitoring", tags=["Monitoring"])
api_router.include_router(chat_router, prefix="/chat", tags=["Chat"])
# WebSocket router removed - using HTTP polling for Vercel+Railway compatibility
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(agent_learning_router, prefix="/agent-learning", tags=["Agent Learning"])
api_router.include_router(sessions_router, prefix="/sessions", tags=["Sessions"])


# Admin Routers
api_router.include_router(client_management_router, prefix="/admin/clients", tags=["Admin - Client Management"])
api_router.include_router(engagement_management_router, prefix="/admin/engagements", tags=["Admin - Engagement Management"])
api_router.include_router(platform_admin_router, prefix="/admin/platform", tags=["Admin - Platform Management"])
api_router.include_router(user_approvals_router, prefix="/admin/approvals", tags=["Admin - User Approvals"])

# Include context router
api_router.include_router(context_router, prefix="", tags=["Context"])

# Include context establishment router (exempt from engagement requirements)
api_router.include_router(context_establishment_router, prefix="/context", tags=["Context Establishment"])

# Include agents router
api_router.include_router(agents_router, prefix="/agents", tags=["Agents"])

# Include test discovery router for debugging
api_router.include_router(test_discovery_router, prefix="/test-discovery", tags=["Test Discovery"])

# Debug endpoint to list all routes
@api_router.get("/debug/routes", include_in_schema=False)
async def debug_routes():
    """Debug endpoint to list all registered routes."""
    routes = []
    for route in api_router.routes:
        routes.append({
            "path": route.path,
            "name": getattr(route, "name", ""),
            "methods": getattr(route, "methods", [])
        })
    return {"routes": routes}

logger.info("--- Finished API Router Inclusion Process ---")