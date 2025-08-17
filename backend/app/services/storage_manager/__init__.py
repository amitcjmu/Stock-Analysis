"""
Storage Manager - High-Performance Batched Storage Operations

This modular storage system provides:
- Batched operations with debouncing
- Multi-backend support (Redis, localStorage, sessionStorage, database, memory)
- Priority-based operation queuing
- Thread-safe concurrent operations
- Automatic retry with exponential backoff
- Performance metrics and monitoring
- Multi-level caching
- Compression and encryption support

Key Components:
- StorageManager: Main orchestrator for storage operations
- Multiple storage backends with different performance characteristics
- Multi-level cache hierarchy for optimal performance
- Comprehensive metrics collection and monitoring
- Flexible compression and encryption options

Usage:
    ```python
    from app.services.storage_manager import get_storage_manager, Priority, StorageType

    storage = get_storage_manager()

    await storage.set(
        key="user:123:session",
        value=session_data,
        storage_type=StorageType.REDIS,
        priority=Priority.HIGH,
        ttl=3600
    )
    ```
"""

# Core storage manager and utilities
from .storage_manager import (
    StorageManager,
    get_storage_manager,
    shutdown_storage_manager,
)

# Base classes and enums
from .base import (
    BatchResult,
    BaseOperationProcessor,
    BaseStorageBackend,
    OperationType,
    Priority,
    StorageConfiguration,
    StorageOperation,
    StorageStats,
    StorageType,
    create_operation,
    validate_key,
    validate_value,
)

# Storage backends
from .local_storage import (
    InMemoryStorage,
    FileStorage,
    TemporaryStorage,
    create_memory_storage,
    create_file_storage,
    create_temporary_storage,
)

from .cloud_storage import (
    RedisStorageBackend,
    DatabaseStorageBackend,
    SessionStorageBackend,
    LocalStorageBackend,
    create_redis_backend,
    create_database_backend,
    create_session_storage_backend,
    create_local_storage_backend,
    get_storage_backend,
)

# Cache management
from .cache_manager import (
    CacheStrategy,
    CacheLevel,
    CacheEntry,
    CachePerformanceMetrics,
    CacheEvictionPolicy,
    MultiLevelCache,
    create_multi_level_cache,
)

# Compression and encryption
from .compression import (
    CompressionType,
    SerializationFormat,
    CompressionManager,
    compress_value,
    decompress_value,
)

from .encryption import (
    EncryptionType,
    KeyDerivationMethod,
    EncryptionManager,
    encrypt_value,
    decrypt_value,
)

# Metrics and monitoring
from .metadata_manager import (
    MetricType,
    AggregationPeriod,
    OperationMetadata,
    MetricDataPoint,
    AggregatedMetrics,
    MetricsCollector,
    get_metrics_collector,
    shutdown_metrics_collector,
)

# Exceptions
from .exceptions import (
    StorageError,
    StorageBackendError,
    StorageConnectionError,
    StorageTimeoutError,
    StorageCapacityError,
    StorageValidationError,
    StorageSerializationError,
    StoragePermissionError,
    StorageConfigurationError,
    StorageRetryExhaustedError,
    StorageIntegrityError,
    StorageQueueFullError,
    wrap_storage_exception,
)

# Main exports for backward compatibility
__all__ = [
    # Core storage manager
    "StorageManager",
    "get_storage_manager",
    "shutdown_storage_manager",
    # Base classes and enums (primary exports for backward compatibility)
    "StorageType",
    "Priority",
    "OperationType",
    "StorageOperation",
    "BatchResult",
    "StorageStats",
    "StorageConfiguration",
    "BaseStorageBackend",
    "BaseOperationProcessor",
    "create_operation",
    "validate_key",
    "validate_value",
    # Storage backends
    "InMemoryStorage",
    "FileStorage",
    "TemporaryStorage",
    "RedisStorageBackend",
    "DatabaseStorageBackend",
    "SessionStorageBackend",
    "LocalStorageBackend",
    "create_memory_storage",
    "create_file_storage",
    "create_temporary_storage",
    "create_redis_backend",
    "create_database_backend",
    "create_session_storage_backend",
    "create_local_storage_backend",
    "get_storage_backend",
    # Cache management
    "CacheStrategy",
    "CacheLevel",
    "CacheEntry",
    "CachePerformanceMetrics",
    "CacheEvictionPolicy",
    "MultiLevelCache",
    "create_multi_level_cache",
    # Compression and encryption
    "CompressionType",
    "SerializationFormat",
    "CompressionManager",
    "compress_value",
    "decompress_value",
    "EncryptionType",
    "KeyDerivationMethod",
    "EncryptionManager",
    "encrypt_value",
    "decrypt_value",
    # Metrics and monitoring
    "MetricType",
    "AggregationPeriod",
    "OperationMetadata",
    "MetricDataPoint",
    "AggregatedMetrics",
    "MetricsCollector",
    "get_metrics_collector",
    "shutdown_metrics_collector",
    # Exceptions
    "StorageError",
    "StorageBackendError",
    "StorageConnectionError",
    "StorageTimeoutError",
    "StorageCapacityError",
    "StorageValidationError",
    "StorageSerializationError",
    "StoragePermissionError",
    "StorageConfigurationError",
    "StorageRetryExhaustedError",
    "StorageIntegrityError",
    "StorageQueueFullError",
    "wrap_storage_exception",
]

# Version information
__version__ = "2.0.0"
__author__ = "Storage Manager Team"
__description__ = (
    "High-performance modular storage system with batching, caching, and monitoring"
)

# Backward compatibility aliases
# These ensure that existing code continues to work without modification
StorageManager = StorageManager
StorageOperation = StorageOperation
StorageType = StorageType
Priority = Priority
get_storage_manager = get_storage_manager

# Legacy imports that may be used by existing code
# Note: InMemoryStorage is now imported from local_storage module

# Module-level configuration
DEFAULT_STORAGE_TYPE = StorageType.REDIS
DEFAULT_PRIORITY = Priority.NORMAL
DEFAULT_TTL = 3600  # 1 hour


# Utility functions for common operations
def create_default_storage_manager(**kwargs) -> StorageManager:
    """
    Create a StorageManager with default configuration.

    Args:
        **kwargs: Additional configuration options

    Returns:
        Configured StorageManager instance
    """
    config = StorageConfiguration(**kwargs)
    return StorageManager(config=config)


def get_storage_stats() -> StorageStats:
    """
    Get current storage statistics from the default manager.

    Returns:
        Current storage statistics
    """
    import asyncio

    manager = get_storage_manager()
    return asyncio.run(manager.get_stats())


def reset_storage_stats() -> bool:
    """
    Reset storage statistics for the default manager.

    Returns:
        True if successful
    """
    import asyncio

    manager = get_storage_manager()
    return asyncio.run(manager.reset_stats())


# Module initialization
def _initialize_module():
    """Initialize the storage manager module"""
    import logging

    logger = logging.getLogger(__name__)
    logger.info(f"Storage Manager module initialized (version {__version__})")


# Initialize module on import
_initialize_module()
