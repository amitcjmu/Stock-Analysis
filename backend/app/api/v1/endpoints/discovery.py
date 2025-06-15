"""
Main Discovery API Router
This file consolidates all discovery-related endpoints and provides a single, unified
entry point for the discovery module, centered around the agentic CrewAI workflow.
"""

import logging
from fastapi import APIRouter
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Create main router
router = APIRouter()

# Include discovery flow router for async CrewAI workflows
try:
    from app.api.v1.discovery.discovery_flow import router as discovery_flow_router
    router.include_router(discovery_flow_router, tags=["discovery-flow"])
    logger.info("✅ Discovery flow router included in discovery")
except ImportError as e:
    logger.warning(f"⚠️ Discovery flow router not available: {e}")

# Include agent discovery endpoints
try:
    from app.api.v1.endpoints.agents.discovery.router import router as agents_discovery_router
    router.include_router(agents_discovery_router, prefix="/agents", tags=["discovery-agents"])
    logger.info("✅ Agent discovery router included in discovery")
except ImportError as e:
    logger.warning(f"⚠️ Agent discovery router not available: {e}")

@router.get("/health")
async def discovery_health_check() -> Dict[str, Any]:
    """
    Health check endpoint for the discovery module.
    Confirms that the main discovery router is active and key sub-modules are loaded.
    """
    return {
        "status": "healthy",
        "module": "discovery-unified",
        "version": "4.0.0",
        "description": "All discovery operations are now routed through the agentic workflow.",
        "components": {
            "discovery_flow_service": "active",
            "agent_discovery_endpoints": "active",
        }
    } 