"""
Asset Inventory Executor Package
Modularized asset inventory phase executor.

This package provides the AssetInventoryExecutor class for creating assets
from raw import records during the discovery flow's asset inventory phase.

Maintains backward compatibility - existing imports will continue to work:
    from app.services.crewai_flows.handlers.phase_executors.asset_inventory_executor import AssetInventoryExecutor
"""

from .base import AssetInventoryExecutor

# Export all public symbols for backward compatibility
__all__ = ["AssetInventoryExecutor"]
