"""
Main API router for AI Force Migration Platform v2.
Clean, modern API design with proper versioning.
"""

from fastapi import APIRouter
import logging

# V2 Discovery Flow Management
try:
    from app.api.v1.discovery_flow_v2 import router as discovery_flow_router
    DISCOVERY_FLOW_AVAILABLE = True
except ImportError:
    DISCOVERY_FLOW_AVAILABLE = False

# Setup logger
logger = logging.getLogger(__name__)

# --- API v2 Router Setup ---
api_v2_router = APIRouter()

# Include V2 Discovery Flow Management
if DISCOVERY_FLOW_AVAILABLE:
    api_v2_router.include_router(discovery_flow_router, prefix="/discovery-flows", tags=["Discovery Flow v2"])
    logger.info("✅ V2 Discovery Flow router included at /api/v2/discovery-flows")
else:
    logger.warning("⚠️ V2 Discovery Flow router not available")

# Health check for V2 API
@api_v2_router.get("/health")
async def v2_health_check():
    """Health check endpoint for API v2"""
    return {
        "status": "healthy",
        "version": "2.0",
        "service": "ai-force-migration-platform-v2",
        "available_endpoints": {
            "discovery_flows": DISCOVERY_FLOW_AVAILABLE
        }
    }

# Debug endpoint to list all V2 routes
@api_v2_router.get("/debug/routes", include_in_schema=False)
async def debug_v2_routes():
    """Debug endpoint to list all registered V2 routes."""
    routes = []
    for route in api_v2_router.routes:
        routes.append({
            "path": route.path,
            "name": getattr(route, "name", ""),
            "methods": getattr(route, "methods", [])
        })
    return {"v2_routes": routes} 