"""
Storage Services

High-performance storage abstraction layer with:
- Batched operations with debouncing
- Multi-backend support (Redis, localStorage, sessionStorage, database, memory)
- Priority-based operation queuing
- Thread-safe concurrent operations
- Automatic retry with exponential backoff
- Performance monitoring and metrics

Note: This module now imports from the modular storage_manager package.
For advanced features, import directly from app.services.storage_manager.
"""

# Import from the new modular storage_manager package
from ..storage_manager import (
    Priority,
    StorageManager,
    StorageOperation,
    StorageType,
    get_storage_manager,
    # Also re-export additional classes for convenience
    BatchResult,
    StorageStats,
    InMemoryStorage,
)

__all__ = [
    "StorageManager",
    "StorageOperation",
    "StorageType",
    "Priority",
    "get_storage_manager",
    "BatchResult",
    "StorageStats",
    "InMemoryStorage",
]
