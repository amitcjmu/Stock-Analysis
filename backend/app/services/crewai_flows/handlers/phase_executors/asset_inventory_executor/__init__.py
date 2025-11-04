"""
Asset Inventory Executor Package
Modularized asset inventory phase executor.

This package provides the AssetInventoryExecutor class for creating assets
from raw import records during the discovery flow's asset inventory phase.

Maintains backward compatibility - existing imports will continue to work:
    from app.services.crewai_flows.handlers.phase_executors.asset_inventory_executor import AssetInventoryExecutor

Module structure:
- base.py: Main AssetInventoryExecutor class
- queries.py: Database query operations
- commands.py: Database write operations
- transforms.py: Data transformation logic
- utils.py: Utility functions (JSONB serialization)
- preview_handler.py: Asset preview and approval workflow
- conflict_handler.py: Conflict detection and resolution
"""

from .base import AssetInventoryExecutor
from .queries import get_raw_records, get_field_mappings
from .commands import mark_records_processed, persist_asset_inventory_completion
from .transforms import transform_raw_record_to_asset
from .utils import serialize_uuids_for_jsonb
from .preview_handler import (
    check_preview_and_approval,
    store_preview_data,
    filter_approved_assets,
    mark_assets_created,
)
from .conflict_handler import create_conflict_free_assets, handle_conflicts

# Export all public symbols for backward compatibility
__all__ = [
    # Main class
    "AssetInventoryExecutor",
    # Query operations
    "get_raw_records",
    "get_field_mappings",
    # Command operations
    "mark_records_processed",
    "persist_asset_inventory_completion",
    # Transform operations
    "transform_raw_record_to_asset",
    # Utility functions
    "serialize_uuids_for_jsonb",
    # Preview handling
    "check_preview_and_approval",
    "store_preview_data",
    "filter_approved_assets",
    "mark_assets_created",
    # Conflict handling
    "create_conflict_free_assets",
    "handle_conflicts",
]
