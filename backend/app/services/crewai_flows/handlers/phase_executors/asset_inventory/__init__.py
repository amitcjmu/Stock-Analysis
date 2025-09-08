"""
Asset Inventory Executor Module
Modularized asset inventory processing for the Unified Discovery Flow.
"""

# Maintain backward compatibility - expose the main executor class
from .executor import AssetInventoryExecutor

__all__ = ["AssetInventoryExecutor"]
