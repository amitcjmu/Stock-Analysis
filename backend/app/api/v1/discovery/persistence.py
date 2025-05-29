"""
Data persistence utilities for the discovery module.
Handles file-based storage until full client account design.
"""

import json
import logging
from pathlib import Path
from typing import Any, List, Dict, Optional

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
        with open(filepath, 'w') as f:
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
            with open(filepath, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load {filename}: {e}")
    return default_value or []

def backup_processed_assets() -> bool:
    """Backup processed assets to file."""
    return save_to_file("processed_assets_backup", processed_assets_store)

def initialize_persistence() -> None:
    """Initialize persistent stores and load existing data."""
    global processed_assets_store
    
    # Load processed assets from backup on startup
    saved_assets = load_from_file("processed_assets_backup", [])
    if saved_assets:
        processed_assets_store.extend(saved_assets)
        logger.info(f"Loaded {len(saved_assets)} assets from backup")

def get_processed_assets() -> List[Dict[str, Any]]:
    """Get the current processed assets store."""
    return processed_assets_store

def add_processed_asset(asset: Dict[str, Any]) -> None:
    """Add an asset to the processed assets store."""
    processed_assets_store.append(asset)

def clear_processed_assets() -> None:
    """Clear the processed assets store."""
    global processed_assets_store
    processed_assets_store = []

def update_asset_by_id(asset_id: str, updated_data: Dict[str, Any]) -> bool:
    """Update an asset in the store by ID."""
    for i, asset in enumerate(processed_assets_store):
        if asset.get('id') == asset_id:
            processed_assets_store[i].update(updated_data)
            backup_processed_assets()
            return True
    return False 