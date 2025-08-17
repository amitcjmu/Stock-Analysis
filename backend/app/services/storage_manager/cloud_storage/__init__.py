"""
Cloud Storage Backends for Storage Manager

Modularized cloud storage backends including:
- redis_backend: Redis-based caching storage
- database_backend: Database-backed storage
- session_backend: Session-based storage
- local_backend: Local file system storage
"""

# Import all backend classes for backward compatibility
from .redis_backend import RedisStorageBackend, create_redis_backend
from .database_backend import DatabaseStorageBackend, create_database_backend
from .session_backend import SessionStorageBackend, create_session_storage_backend
from .local_backend import LocalStorageBackend, create_local_storage_backend


def get_storage_backend():
    """Get storage backend - placeholder implementation"""
    return RedisStorageBackend()


__all__ = [
    "RedisStorageBackend",
    "DatabaseStorageBackend",
    "SessionStorageBackend",
    "LocalStorageBackend",
    "create_redis_backend",
    "create_database_backend",
    "create_session_storage_backend",
    "create_local_storage_backend",
    "get_storage_backend",
]
