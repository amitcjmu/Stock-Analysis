"""
Tenant Scoped Agent Pool - Pool Management Module

This module handles pool statistics, cleanup operations, and lifecycle management
for the tenant scoped agent pool system.
"""

import asyncio
import logging
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List

# Make psutil optional - not critical for core functionality
try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logging.getLogger(__name__).warning(
        "psutil not available - memory monitoring disabled. Install with: pip install psutil"
    )

logger = logging.getLogger(__name__)


@dataclass
class TenantPoolStats:
    """Statistics for a tenant's agent pool."""

    client_account_id: str
    engagement_id: str
    agent_count: int
    last_activity: datetime
    memory_usage: float
    total_requests: int
    error_count: int


class PoolManager:
    """Manages pool statistics, cleanup, and lifecycle operations."""

    # Class-level storage for pool statistics and cleanup
    _cleanup_thread = None
    _cleanup_interval = 3600  # 1 hour in seconds
    _should_stop_cleanup = False
    _pool_stats = {}  # Store statistics per tenant
    _memory_monitor = None

    @classmethod
    async def get_pool_statistics(cls) -> List[TenantPoolStats]:
        """Get statistics for all tenant pools."""
        stats = []

        try:
            for key, pool_data in cls._pool_stats.items():
                if isinstance(key, tuple) and len(key) == 2:
                    client_account_id, engagement_id = key

                    stats.append(
                        TenantPoolStats(
                            client_account_id=client_account_id,
                            engagement_id=engagement_id,
                            agent_count=pool_data.get("agent_count", 0),
                            last_activity=pool_data.get(
                                "last_activity", datetime.now()
                            ),
                            memory_usage=pool_data.get("memory_usage", 0.0),
                            total_requests=pool_data.get("total_requests", 0),
                            error_count=pool_data.get("error_count", 0),
                        )
                    )

            logger.info(f"Retrieved statistics for {len(stats)} tenant pools")

        except Exception as e:
            logger.error(f"Error retrieving pool statistics: {e}")

        return stats

    @classmethod
    async def cleanup_idle_pools(cls, max_idle_hours: int = 24):
        """Clean up idle tenant pools that haven't been used recently."""
        try:
            cutoff_time = datetime.now() - timedelta(hours=max_idle_hours)
            cleaned_count = 0

            # Get list of pools to clean (create copy to avoid modification during iteration)
            pools_to_clean = []

            for key, pool_data in list(cls._pool_stats.items()):
                last_activity = pool_data.get("last_activity", datetime.now())
                if last_activity < cutoff_time:
                    pools_to_clean.append(key)

            # Clean up the idle pools
            for pool_key in pools_to_clean:
                try:
                    # Remove from statistics
                    if pool_key in cls._pool_stats:
                        del cls._pool_stats[pool_key]
                        cleaned_count += 1

                    if isinstance(pool_key, tuple) and len(pool_key) == 2:
                        client_id, engagement_id = pool_key
                        logger.info(
                            f"Cleaned up idle pool for client {client_id}, engagement {engagement_id}"
                        )

                except Exception as e:
                    logger.warning(f"Error cleaning up pool {pool_key}: {e}")

            logger.info(
                f"Cleaned up {cleaned_count} idle pools (idle > {max_idle_hours} hours)"
            )

        except Exception as e:
            logger.error(f"Error during pool cleanup: {e}")

    @classmethod
    def update_pool_stats(
        cls,
        client_account_id: str,
        engagement_id: str,
        agent_count: int = None,
        increment_requests: bool = False,
        increment_errors: bool = False,
    ):
        """Update statistics for a tenant pool."""
        key = (client_account_id, engagement_id)

        if key not in cls._pool_stats:
            cls._pool_stats[key] = {
                "agent_count": 0,
                "last_activity": datetime.now(),
                "memory_usage": 0.0,
                "total_requests": 0,
                "error_count": 0,
            }

        pool_data = cls._pool_stats[key]
        pool_data["last_activity"] = datetime.now()

        if agent_count is not None:
            pool_data["agent_count"] = agent_count

        if increment_requests:
            pool_data["total_requests"] += 1

        if increment_errors:
            pool_data["error_count"] += 1

        # Update memory usage if psutil is available
        if PSUTIL_AVAILABLE:
            pool_data["memory_usage"] = cls._get_current_memory_usage()

    @classmethod
    def _get_current_memory_usage(cls) -> float:
        """Get current memory usage percentage."""
        if not PSUTIL_AVAILABLE:
            return 0.0

        try:
            memory_info = psutil.virtual_memory()
            return memory_info.percent
        except Exception as e:
            logger.warning(f"Failed to get memory usage: {e}")
            return 0.0

    @classmethod
    def schedule_automatic_cleanup(cls):
        """Schedule automatic cleanup of idle pools."""
        if cls._cleanup_thread and cls._cleanup_thread.is_alive():
            return  # Already running

        def run_cleanup():
            while not cls._should_stop_cleanup:
                try:
                    # Run cleanup in async context
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(cls.cleanup_idle_pools())
                    loop.close()

                    logger.debug("Automatic pool cleanup completed")

                except Exception as e:
                    logger.error(f"Error during automatic cleanup: {e}")

                # Wait for next cleanup cycle
                for _ in range(cls._cleanup_interval):
                    if cls._should_stop_cleanup:
                        break
                    threading.Event().wait(1)

        cls._should_stop_cleanup = False
        cls._cleanup_thread = threading.Thread(target=run_cleanup, daemon=True)
        cls._cleanup_thread.start()

        logger.info(
            f"Scheduled automatic pool cleanup every {cls._cleanup_interval} seconds"
        )

    @classmethod
    def stop_automatic_cleanup(cls):
        """Stop automatic cleanup of idle pools."""
        cls._should_stop_cleanup = True

        if cls._cleanup_thread and cls._cleanup_thread.is_alive():
            cls._cleanup_thread.join(timeout=5)

        logger.info("Stopped automatic pool cleanup")

    @classmethod
    def start_memory_monitoring(cls):
        """Start memory monitoring for the agent pool."""
        if not PSUTIL_AVAILABLE:
            logger.warning("Memory monitoring not available - psutil not installed")
            return

        try:
            # Initialize memory monitoring
            cls._memory_monitor = True
            logger.info("Memory monitoring started")

        except Exception as e:
            logger.error(f"Failed to start memory monitoring: {e}")

    @classmethod
    def stop_memory_monitoring(cls):
        """Stop memory monitoring for the agent pool."""
        try:
            cls._memory_monitor = None
            logger.info("Memory monitoring stopped")

        except Exception as e:
            logger.error(f"Failed to stop memory monitoring: {e}")

    @classmethod
    def get_memory_stats(cls) -> Dict[str, float]:
        """Get current memory statistics."""
        stats = {"memory_percent": 0.0, "memory_available": 0.0, "memory_used": 0.0}

        if not PSUTIL_AVAILABLE:
            return stats

        try:
            memory = psutil.virtual_memory()
            stats.update(
                {
                    "memory_percent": memory.percent,
                    "memory_available": memory.available / (1024**3),  # GB
                    "memory_used": memory.used / (1024**3),  # GB
                }
            )
        except Exception as e:
            logger.warning(f"Failed to get memory stats: {e}")

        return stats
