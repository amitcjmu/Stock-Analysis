"""
Data persistence utilities for the discovery module.
Handles file-based storage until full client account design.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# Data directory for persistence
DATA_DIR = Path("data/persistence")
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Global storage for processed assets
processed_assets_store: List[Dict[str, Any]] = []


def save_to_file(filename: str, data: Any) -> bool:
    """Save data to a JSON file for persistence."""
    try:
        filepath = DATA_DIR / f"{filename}.json"
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2, default=str)
        return True
    except Exception as e:
        logger.warning(f"Failed to save {filename}: {e}")
        return False


def load_from_file(filename: str, default_value: Any = None) -> Any:
    """Load data from a JSON file."""
    try:
        filepath = DATA_DIR / f"{filename}.json"
        if filepath.exists():
            with open(filepath, "r") as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load {filename}: {e}")
    return default_value or []


def backup_processed_assets() -> bool:
    """Backup processed assets to file."""
    return save_to_file("processed_assets_backup", processed_assets_store)


def initialize_persistence() -> None:
    """Initialize persistent stores and load existing data."""

    # Load processed assets from backup on startup
    saved_assets = load_from_file("processed_assets_backup", [])
    if saved_assets:
        processed_assets_store.extend(saved_assets)
        logger.info(f"Loaded {len(saved_assets)} assets from backup")


def get_processed_assets() -> List[Dict[str, Any]]:
    """Get the current processed assets store."""
    return processed_assets_store


def add_processed_asset(asset: Dict[str, Any]) -> None:
    """Add an asset to the processed assets store with deduplication."""

    # Generate a unique identifier based on hostname and name
    asset_hostname = asset.get("hostname", "").strip().lower()
    asset_name = asset.get("asset_name", "").strip().lower()
    asset_type = asset.get("asset_type", "").strip().lower()

    # Check for duplicates - match on hostname or name if they exist
    for existing_asset in processed_assets_store:
        existing_hostname = existing_asset.get("hostname", "").strip().lower()
        existing_name = existing_asset.get("asset_name", "").strip().lower()
        existing_type = existing_asset.get("asset_type", "").strip().lower()

        # Consider it a duplicate if hostname matches (primary) or name+type matches
        is_duplicate = False
        if asset_hostname and existing_hostname and asset_hostname == existing_hostname:
            is_duplicate = True
        elif (
            asset_name
            and existing_name
            and asset_name == existing_name
            and asset_type == existing_type
        ):
            is_duplicate = True

        if is_duplicate:
            # Update existing asset with new data instead of adding duplicate
            existing_asset.update(asset)
            logger.info(f"Updated existing asset: {asset_hostname or asset_name}")
            return

    # No duplicate found, add new asset
    processed_assets_store.append(asset)
    logger.debug(f"Added new asset: {asset_hostname or asset_name}")


def bulk_update_assets(asset_ids: List[str], updates: Dict[str, Any]) -> int:
    """Bulk update multiple assets by their IDs."""
    updated_count = 0

    # Map frontend field names to backend storage field names
    field_mapping = {
        "type": "asset_type",  # Frontend 'type' -> Backend 'asset_type'
        "asset_type": "asset_type",  # Direct mapping
        "environment": "environment",  # Direct mapping
        "department": "business_owner",  # Frontend 'department' -> Backend 'business_owner'
        "criticality": "status",  # Frontend 'criticality' -> Backend 'status'
        "name": "asset_name",  # Frontend 'name' -> Backend 'asset_name'
        "hostname": "hostname",  # Direct mapping
        "ip_address": "ip_address",  # Direct mapping
        "operating_system": "operating_system",  # Direct mapping
    }

    # Translate frontend updates to backend field names
    backend_updates = {}
    for frontend_field, value in updates.items():
        backend_field = field_mapping.get(frontend_field, frontend_field)
        backend_updates[backend_field] = value
        logger.debug(f"Mapped field: {frontend_field} -> {backend_field} = {value}")

    logger.info(f"Bulk update: Looking for assets with IDs {asset_ids}")
    logger.info(f"Updates to apply: {backend_updates}")

    # Track which assets we find
    found_asset_ids = []

    for asset in processed_assets_store:
        # Check multiple possible ID fields
        asset_id = asset.get("id") or asset.get("ci_id") or asset.get("asset_id")
        if asset_id and str(asset_id) in asset_ids:
            found_asset_ids.append(asset_id)
            asset.update(backend_updates)
            updated_count += 1
            logger.info(
                f"Updated asset {asset_id}: {asset.get('hostname', 'Unknown')} with {backend_updates}"
            )

    logger.info(
        f"Found {len(found_asset_ids)} assets out of {len(asset_ids)} requested"
    )
    logger.info(f"Found asset IDs: {found_asset_ids}")

    if updated_count > 0:
        backup_processed_assets()
        logger.info(f"Bulk updated {updated_count} assets")
    else:
        # Debug: Show sample asset IDs in store
        sample_assets = processed_assets_store[:3]
        logger.warning("No assets were updated. Sample asset IDs in store:")
        for asset in sample_assets:
            sample_id = asset.get("id") or asset.get("ci_id") or asset.get("asset_id")
            logger.warning(
                f"  Sample ID: {sample_id}, hostname: {asset.get('hostname', 'Unknown')}"
            )

    return updated_count


def bulk_delete_assets(asset_ids: List[str]) -> int:
    """Bulk delete multiple assets by their IDs."""
    global processed_assets_store

    initial_count = len(processed_assets_store)

    # Filter out assets that match any of the provided IDs
    def should_keep_asset(asset):
        # Check multiple possible ID fields
        asset_id = asset.get("id") or asset.get("ci_id") or asset.get("asset_id")
        if asset_id and str(asset_id) in asset_ids:
            logger.debug(
                f"Marking for deletion: {asset_id} - {asset.get('hostname', 'Unknown')}"
            )
            return False
        return True

    processed_assets_store = [
        asset for asset in processed_assets_store if should_keep_asset(asset)
    ]
    deleted_count = initial_count - len(processed_assets_store)

    if deleted_count > 0:
        backup_processed_assets()
        logger.info(f"Bulk deleted {deleted_count} assets out of {initial_count} total")
    else:
        logger.warning(
            f"No assets were deleted. Checked {len(asset_ids)} IDs against {initial_count} assets"
        )
        # Log some sample IDs for debugging
        sample_assets = processed_assets_store[:3]
        for asset in sample_assets:
            asset_id = asset.get("id") or asset.get("ci_id") or asset.get("asset_id")
            logger.debug(
                f"Sample asset ID: {asset_id}, hostname: {asset.get('hostname', 'Unknown')}"
            )

    return deleted_count


def find_duplicate_assets() -> List[Dict[str, Any]]:
    """Find potential duplicate assets in the store."""
    duplicates = []
    hostname_groups = {}
    name_type_groups = {}

    # Group assets by potential duplicate criteria
    for i, asset in enumerate(processed_assets_store):
        hostname = asset.get("hostname", "").strip().lower()
        name = asset.get("asset_name", "").strip().lower()
        asset_type = asset.get("asset_type", "").strip().lower()

        # Group by hostname (primary key for duplicates)
        if hostname and hostname != "unknown":
            if hostname not in hostname_groups:
                hostname_groups[hostname] = []
            hostname_groups[hostname].append((i, asset))

        # Group by name+type combination (secondary key)
        if name and name != "unknown":
            name_type_key = f"{name}:{asset_type}"
            if name_type_key not in name_type_groups:
                name_type_groups[name_type_key] = []
            name_type_groups[name_type_key].append((i, asset))

    # Find hostname duplicates
    for hostname, asset_list in hostname_groups.items():
        if len(asset_list) > 1:
            indices = [item[0] for item in asset_list]
            assets = [item[1] for item in asset_list]
            duplicates.append(
                {
                    "type": "hostname",
                    "value": hostname,
                    "indices": indices,
                    "assets": assets,
                    "count": len(asset_list),
                }
            )

    # Find name+type duplicates (only if not already caught by hostname)
    hostname_indices = set()
    for dup in duplicates:
        hostname_indices.update(dup["indices"])

    for name_type_key, asset_list in name_type_groups.items():
        if len(asset_list) > 1:
            # Filter out assets already caught by hostname duplicates
            filtered_list = [
                (i, asset) for i, asset in asset_list if i not in hostname_indices
            ]
            if len(filtered_list) > 1:
                indices = [item[0] for item in filtered_list]
                assets = [item[1] for item in filtered_list]
                duplicates.append(
                    {
                        "type": "name_type",
                        "value": name_type_key,
                        "indices": indices,
                        "assets": assets,
                        "count": len(filtered_list),
                    }
                )

    return duplicates


def cleanup_duplicates() -> int:
    """Remove duplicate assets and return count of removed duplicates."""
    global processed_assets_store

    logger.info("Starting comprehensive duplicate cleanup...")

    duplicates = find_duplicate_assets()
    if not duplicates:
        logger.info("No duplicates found")
        return 0

    # Collect all indices to remove (keep the first occurrence of each duplicate group)
    indices_to_remove = set()

    for duplicate_info in duplicates:
        indices = duplicate_info["indices"]
        # Keep the first occurrence, mark the rest for removal
        for idx in indices[1:]:  # Skip first index (keep it)
            indices_to_remove.add(idx)

    # Sort indices in descending order to avoid index shifting issues
    sorted_indices = sorted(indices_to_remove, reverse=True)

    # Remove duplicates
    initial_count = len(processed_assets_store)
    for idx in sorted_indices:
        if idx < len(processed_assets_store):
            removed_asset = processed_assets_store.pop(idx)
            logger.debug(
                f"Removed duplicate asset at index {idx}: {removed_asset.get('hostname', 'Unknown')}"
            )

    removed_count = initial_count - len(processed_assets_store)

    if removed_count > 0:
        backup_processed_assets()
        logger.info(
            f"Cleaned up {removed_count} duplicate assets out of {initial_count} total assets"
        )
        logger.info(f"Duplicate groups processed: {len(duplicates)}")

    return removed_count


def clear_processed_assets() -> None:
    """Clear the processed assets store."""


def update_asset_by_id(asset_id: str, updated_data: Dict[str, Any]) -> bool:
    """Update an asset in the store by ID."""
    for i, asset in enumerate(processed_assets_store):
        if asset.get("id") == asset_id:
            processed_assets_store[i].update(updated_data)
            backup_processed_assets()
            return True
    return False
