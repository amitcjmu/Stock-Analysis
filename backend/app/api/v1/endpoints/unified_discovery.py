"""
Unified Discovery Flow API - Master Flow Orchestrator Integration

This endpoint provides the proper architectural flow as shown in the DFD:
File upload → /api/v1/unified-discovery/flow/initialize → MasterFlowOrchestrator → UnifiedDiscoveryFlow

ARCHITECTURAL FIX: This ensures all discovery flows go through the Master Flow Orchestrator
instead of bypassing it with direct CrewAI flow creation.

This file has been modularized. Related endpoints can be found in:
- app.api.v1.endpoints.dependency_analysis - Dependency analysis endpoints
- app.api.v1.endpoints.agent_insights - Agent insights and questions endpoints
- app.api.v1.endpoints.clarifications - Clarification submission endpoints
- app.api.v1.endpoints.flow_management - Flow lifecycle management endpoints
- app.services.discovery.flow_execution_service - Flow execution logic
- app.services.discovery.flow_status_service - Flow status operations
- app.services.discovery.data_extraction_service - Data extraction utilities

MODULARIZED STRUCTURE:
- unified_discovery/flow_handlers.py - Flow initialization, status, and execution endpoints
- unified_discovery/asset_handlers.py - Asset listing and summary endpoints
- unified_discovery/field_mapping_handlers.py - Field mapping endpoints
- unified_discovery/health_handlers.py - Health check endpoints
"""

from fastapi import APIRouter

# Import all modularized routers
from .unified_discovery.flow_handlers import router as flow_router
from .unified_discovery.asset_handlers import router as asset_router
from .unified_discovery.field_mapping_handlers import router as field_mapping_router
from .unified_discovery.health_handlers import router as health_router

# Create main router and include all modular routers
router = APIRouter()

# Include all the modularized routers
router.include_router(flow_router, tags=["Unified Discovery"])
router.include_router(asset_router, tags=["Unified Discovery"])
router.include_router(field_mapping_router, tags=["Field Mapping"])
router.include_router(health_router, tags=["System Health"])

# For backward compatibility, we can also expose the individual routers
# This maintains the existing API structure while allowing modular organization
__all__ = [
    "router",
    "flow_router",
    "asset_router",
    "field_mapping_router",
    "health_router",
]
