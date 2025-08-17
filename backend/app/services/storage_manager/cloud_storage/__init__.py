"""
Cloud Storage Backends for Storage Manager

Modularized cloud storage backends including:
- redis_backend: Redis-based caching storage
- database_backend: Database-backed storage
- session_backend: Session-based storage
- local_backend: Local file system storage
"""

# Import all backend classes for backward compatibility
from .redis_backend import RedisStorageBackend
from .database_backend import DatabaseStorageBackend
from .session_backend import SessionStorageBackend
from .local_backend import LocalStorageBackend

__all__ = [
    "RedisStorageBackend",
    "DatabaseStorageBackend",
    "SessionStorageBackend",
    "LocalStorageBackend",
]
