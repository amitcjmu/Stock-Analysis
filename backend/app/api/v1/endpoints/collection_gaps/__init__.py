"""
Collection gaps API endpoints.

This module provides REST API endpoints for collection gaps Phase 1 functionality.
"""

from .collection_flows import router as collection_flows_router
from .vendor_products import router as vendor_products_router
from .maintenance_windows import router as maintenance_windows_router
from .governance import router as governance_router

__all__ = [
    "collection_flows_router",
    "vendor_products_router",
    "maintenance_windows_router",
    "governance_router",
]
