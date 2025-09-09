"""
Asset Inventory Executor (Backward Compatibility Wrapper)
Handles asset inventory phase execution for the Unified Discovery Flow.

NOTE: This file has been modularized. The actual implementation is now in the
asset_inventory submodule for better maintainability and code organization.
"""

import warnings

# Import the actual implementation from the modularized structure
from .asset_inventory import AssetInventoryExecutor

# Warn about deprecated import path
warnings.warn(
    "Importing AssetInventoryExecutor from asset_inventory_executor is deprecated. "
    "Please import from .asset_inventory instead.",
    FutureWarning,
    stacklevel=2,
)

# Re-export for backward compatibility
__all__ = ["AssetInventoryExecutor"]
