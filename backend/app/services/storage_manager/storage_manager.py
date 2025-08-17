"""
StorageManager - Main Export Module

This module exports the main StorageManager class and utilities from the core module.
It serves as the primary interface for the storage manager system while keeping
backward compatibility.
"""

# Import the main implementation from core
from .core import (
    StorageManager,
    get_storage_manager,
    shutdown_storage_manager,
)

# Re-export for backward compatibility
__all__ = [
    "StorageManager",
    "get_storage_manager",
    "shutdown_storage_manager",
]

# Legacy compatibility - ensure these are available for any old imports
StorageManager = StorageManager
get_storage_manager = get_storage_manager
shutdown_storage_manager = shutdown_storage_manager
