"""
Modular unified discovery router that combines all functionality.
This replaces the monolithic unified_discovery_api.py file.
"""

from fastapi import APIRouter

# Import all modular routers
from .unified_discovery.routes.flow_routes import router as flow_router
from .unified_discovery.routes.import_routes import router as import_router
from .unified_discovery.routes.status_routes import router as status_router
from .unified_discovery.routes.websocket_routes import router as websocket_router

# Create main router
router = APIRouter(prefix="/unified-discovery", tags=["unified-discovery"])

# Include all sub-routers
router.include_router(flow_router)
router.include_router(import_router)
router.include_router(status_router)
router.include_router(websocket_router)

# Legacy compatibility routes
from .unified_discovery.routes.flow_routes import (
    initialize_discovery_flow as legacy_initialize,
    get_discovery_flow_status as legacy_get_status,
    execute_discovery_flow as legacy_execute,
    get_active_discovery_flows as legacy_get_active
)

from .unified_discovery.routes.status_routes import (
    discovery_health_check as legacy_health,
    get_flow_assets as legacy_get_assets
)

# Add legacy routes for backward compatibility
@router.post("/flow/initialize")
async def initialize_discovery_flow_legacy(**kwargs):
    """Legacy compatibility route."""
    return await legacy_initialize(**kwargs)

@router.get("/flow/status/{flow_id}")
async def get_discovery_flow_status_legacy(flow_id: str, **kwargs):
    """Legacy compatibility route."""
    return await legacy_get_status(flow_id, **kwargs)

@router.post("/flow/execute")
async def execute_discovery_flow_legacy(**kwargs):
    """Legacy compatibility route."""
    return await legacy_execute(**kwargs)

@router.get("/flows/active")
async def get_active_discovery_flows_legacy(**kwargs):
    """Legacy compatibility route."""
    return await legacy_get_active(**kwargs)

@router.get("/health")
async def discovery_health_check_legacy(**kwargs):
    """Legacy compatibility route."""
    return await legacy_health(**kwargs)

@router.get("/assets/{flow_id}")
async def get_flow_assets_legacy(flow_id: str, **kwargs):
    """Legacy compatibility route."""
    return await legacy_get_assets(flow_id, **kwargs)

# Health check
@router.get("/modular-health")
async def modular_health_check():
    """Health check for modular unified discovery system."""
    return {
        "status": "healthy",
        "service": "unified_discovery_modular",
        "modules": ["flow", "import", "status", "websocket"],
        "layers": ["crewai", "database", "compatibility"],
        "legacy_compatibility": True
    }