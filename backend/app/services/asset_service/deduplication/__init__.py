"""
Asset Deduplication Package

Modularized deduplication logic for asset creation/updates with conflict detection.
Maintains backward compatibility with monolithic deduplication.py.

CC: Package exports for backward compatibility
"""

# Core constants
from .constants import (
    DEFAULT_ALLOWED_MERGE_FIELDS,
    NEVER_MERGE_FIELDS,
)

# Main orchestration
from .orchestration import (
    create_or_update_asset,
    create_new_asset,
)

# Hierarchical lookup
from .hierarchical_lookup import (
    find_existing_asset_hierarchical,
)

# Merge strategies
from .merge_strategies import (
    enrich_asset,
    overwrite_asset,
)

# Conflict detection
from .conflict_detection import (
    bulk_prepare_conflicts,
    serialize_asset_for_comparison,
    _check_single_asset_conflict,
)

# Batch operations
from .batch_operations import (
    bulk_create_or_update_assets,
    _build_prefetch_criteria,
    _build_lookup_indexes,
    _find_existing_in_indexes,
)

__all__ = [
    # Constants
    "DEFAULT_ALLOWED_MERGE_FIELDS",
    "NEVER_MERGE_FIELDS",
    # Main orchestration
    "create_or_update_asset",
    "create_new_asset",
    # Hierarchical lookup
    "find_existing_asset_hierarchical",
    # Merge strategies
    "enrich_asset",
    "overwrite_asset",
    # Conflict detection
    "bulk_prepare_conflicts",
    "serialize_asset_for_comparison",
    "_check_single_asset_conflict",
    # Batch operations
    "bulk_create_or_update_assets",
    "_build_prefetch_criteria",
    "_build_lookup_indexes",
    "_find_existing_in_indexes",
]
