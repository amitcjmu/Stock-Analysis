"""
Unified Discovery Modular Endpoints

This package contains the modularized unified discovery endpoints,
extracted from the main unified_discovery.py file for better maintainability.

Modules:
- flow_handlers: Flow initialization, status, and execution endpoints
- asset_handlers: Asset listing and summary endpoints
- field_mapping_handlers: Field mapping endpoints
- health_handlers: Health check endpoints
"""

from fastapi import APIRouter

# Import all routers for easy access
from .flow_handlers import router as flow_router
from .asset_handlers import router as asset_router
from .field_mapping_handlers import router as field_mapping_router
from .health_handlers import router as health_router

# Create main router and include all modular routers (same as unified_discovery.py)
router = APIRouter()

# Include all the modularized routers
router.include_router(flow_router, tags=["Unified Discovery"])
router.include_router(asset_router, tags=["Unified Discovery"])
router.include_router(field_mapping_router, tags=["Field Mapping"])
router.include_router(health_router, tags=["System Health"])

__all__ = [
    "router",  # Main combined router for import compatibility
    "flow_router",
    "asset_router",
    "field_mapping_router",
    "health_router",
]
