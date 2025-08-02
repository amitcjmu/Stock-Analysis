"""
Storage Services

High-performance storage abstraction layer with:
- Batched operations with debouncing
- Multi-backend support (Redis, localStorage, sessionStorage, database, memory)
- Priority-based operation queuing
- Thread-safe concurrent operations
- Automatic retry with exponential backoff
- Performance monitoring and metrics
"""

from .storage_manager import (
    Priority,
    StorageManager,
    StorageOperation,
    StorageType,
    get_storage_manager,
)

__all__ = [
    "StorageManager",
    "StorageOperation",
    "StorageType",
    "Priority",
    "get_storage_manager",
]
