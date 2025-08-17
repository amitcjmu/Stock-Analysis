"""
Storage Manager Operation Executor

Handles execution of individual storage operations across different backends,
including direct operations for reads and health checks.
"""

from typing import Any, Dict, Optional, TYPE_CHECKING

from app.core.logging import get_logger

from .base import StorageType

if TYPE_CHECKING:
    from .storage_manager import StorageManager

logger = get_logger(__name__)


class OperationExecutor:
    """Handles execution of storage operations"""

    def __init__(self, storage_manager: "StorageManager"):
        self.storage_manager = storage_manager

    async def get_from_backend(
        self, key: str, storage_type: StorageType
    ) -> Optional[Any]:
        """Get value from the specified backend"""
        try:
            backend = self.storage_manager._backends.get(storage_type)
            if backend is None:
                logger.error(f"No backend available for storage type: {storage_type}")
                return None

            return await backend.get(key)

        except Exception as e:
            logger.error(f"Error getting {key} from {storage_type}: {e}")
            return None

    async def exists_in_backend(self, key: str, storage_type: StorageType) -> bool:
        """Check if key exists in the specified backend"""
        try:
            backend = self.storage_manager._backends.get(storage_type)
            if backend is None:
                return False

            return await backend.exists(key)

        except Exception as e:
            logger.error(f"Error checking existence of {key} in {storage_type}: {e}")
            return False

    async def health_check_backends(self) -> Dict[str, Any]:
        """Perform health check on all backends"""
        health_results = {}
        issues = []

        for storage_type, backend in self.storage_manager._backends.items():
            if backend is None:
                continue

            try:
                backend_health = await backend.health_check()
                health_results[storage_type.value] = backend_health

                if not backend_health.get("available", False):
                    issues.append(f"{storage_type.value} backend is not available")

            except Exception as e:
                health_results[storage_type.value] = {
                    "available": False,
                    "error": str(e),
                }
                issues.append(f"{storage_type.value} backend health check failed: {e}")

        return health_results, issues

    async def check_cache_health(self) -> tuple[Dict[str, Any], list[str]]:
        """Check cache health"""
        issues = []

        try:
            cache_health = await self.storage_manager.cache.health_check()

            if cache_health.get("overall_status") != "healthy":
                issues.extend(cache_health.get("issues", []))

            return cache_health, issues

        except Exception as e:
            issues.append(f"Cache health check error: {str(e)}")
            return {}, issues

    async def check_queue_health(self) -> tuple[Dict[str, Any], list[str]]:
        """Check queue health"""
        queue_health = {}
        issues = []

        try:
            from .base import Priority

            for priority in Priority:
                queue_size = len(self.storage_manager.operation_queues[priority])
                queue_health[priority.value] = {
                    "size": queue_size,
                    "has_timer": self.storage_manager.debounce_timers[priority]
                    is not None,
                }

                # Check for queue congestion
                if queue_size > self.storage_manager.max_queue_size * 0.8:
                    issues.append(
                        f"{priority.value} queue approaching capacity: {queue_size}"
                    )

        except Exception as e:
            issues.append(f"Queue health check error: {str(e)}")

        return queue_health, issues

    async def get_performance_metrics(self) -> tuple[Dict[str, Any], list[str]]:
        """Get performance metrics"""
        issues = []

        try:
            stats = await self.storage_manager.get_stats()
            performance = {
                "total_operations": stats.total_operations,
                "cache_hit_rate": stats.cache_hit_rate,
                "error_rate": stats.error_rate,
                "average_batch_size": stats.average_batch_size,
                "average_processing_time_ms": stats.average_processing_time_ms,
            }

            # Performance warnings
            if stats.error_rate > 5.0:
                issues.append(f"High error rate: {stats.error_rate:.2f}%")

            if stats.average_processing_time_ms > 1000:
                issues.append(
                    f"High processing time: {stats.average_processing_time_ms:.1f}ms"
                )

            return performance, issues

        except Exception as e:
            issues.append(f"Performance metrics error: {str(e)}")
            return {}, issues
