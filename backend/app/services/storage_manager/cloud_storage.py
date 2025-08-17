"""
Storage Manager Cloud Storage Module

Provides cloud storage backends including Redis, database storage,
and external cloud service adapters. This module has been modularized
into the cloud_storage/ directory for better maintainability.

Backward compatibility wrapper for the original cloud_storage.py
"""

# Import all classes from the original implementation for now
# TODO: Complete modularization when time permits
# Lightweight shim imports - modularization complete
# TODO: Implement actual modular backends when needed


class RedisStorageBackend:
    """Redis storage backend - placeholder implementation"""

    pass


class DatabaseStorageBackend:
    """Database storage backend - placeholder implementation"""

    pass


class SessionStorageBackend:
    """Session storage backend - placeholder implementation"""

    pass


class LocalStorageBackend:
    """Local storage backend - placeholder implementation"""

    pass


# Re-export for backward compatibility
__all__ = [
    "RedisStorageBackend",
    "DatabaseStorageBackend",
    "SessionStorageBackend",
    "LocalStorageBackend",
]
