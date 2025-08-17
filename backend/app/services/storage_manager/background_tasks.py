"""
Storage Manager Background Tasks

Contains background task implementations for cleanup, metrics collection,
and other maintenance operations for the StorageManager.
"""

import asyncio
from collections import deque
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from app.core.logging import get_logger

if TYPE_CHECKING:
    from .storage_manager import StorageManager

logger = get_logger(__name__)


class BackgroundTaskManager:
    """Manages background tasks for the StorageManager"""

    def __init__(self, storage_manager: "StorageManager"):
        self.storage_manager = storage_manager
        self._cleanup_task = None
        self._metrics_task = None

    def start_background_tasks(self):
        """Start background tasks for cleanup and metrics collection"""
        try:
            # Start cleanup task (runs every 5 minutes)
            self._cleanup_task = asyncio.create_task(self._cleanup_expired_operations())

            # Start metrics collection task (runs every minute)
            if self.storage_manager.enable_metrics:
                self._metrics_task = asyncio.create_task(self._collect_metrics())

            logger.debug("Background tasks started successfully")
        except RuntimeError as e:
            if "no running event loop" in str(e):
                logger.debug(
                    "No event loop running, background tasks will start when needed"
                )
            else:
                logger.error(f"Failed to start background tasks: {e}")
        except Exception as e:
            logger.error(f"Failed to start background tasks: {e}")

    async def _cleanup_expired_operations(self):
        """Background task to clean up expired operations and statistics"""
        while self.storage_manager.enabled:
            try:
                await asyncio.sleep(self.storage_manager.config.cleanup_interval)

                current_time = datetime.utcnow()
                cleaned_count = 0

                # Clean up old operations from queues
                for priority in self.storage_manager.operation_queues:
                    async with self.storage_manager._queue_locks[priority]:
                        queue = self.storage_manager.operation_queues[priority]

                        # Remove operations older than 1 hour
                        cutoff_time = current_time - timedelta(hours=1)

                        # Create new queue with non-expired operations
                        new_queue = deque()
                        while queue:
                            operation = queue.popleft()
                            if operation.created_at > cutoff_time:
                                new_queue.append(operation)
                            else:
                                cleaned_count += 1

                        self.storage_manager.operation_queues[priority] = new_queue

                # Clean up processing times older than 1 hour
                cutoff_timestamp = current_time.timestamp() - 3600
                while (
                    self.storage_manager.processing_times
                    and len(self.storage_manager.processing_times) > 0
                    and self.storage_manager.processing_times[0][0] < cutoff_timestamp
                ):
                    self.storage_manager.processing_times.popleft()

                if cleaned_count > 0:
                    logger.info(f"Cleaned up {cleaned_count} expired operations")

            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")

    async def _collect_metrics(self):
        """Background task to collect and log performance metrics"""
        while self.storage_manager.enabled:
            try:
                await asyncio.sleep(
                    self.storage_manager.config.metrics_collection_interval
                )

                if self.storage_manager.enable_metrics:
                    stats = await self.storage_manager.get_stats()

                    # Log key performance metrics
                    logger.info(
                        f"Storage metrics - Queue length: {stats.queue_length}, "
                        f"Cache hit rate: {stats.cache_hit_rate:.1f}%, "
                        f"Avg batch size: {stats.average_batch_size:.1f}, "
                        f"Error rate: {stats.error_rate:.2f}%"
                    )

                    # Log warnings for concerning metrics
                    if stats.queue_length > self.storage_manager.max_queue_size * 0.8:
                        logger.warning(
                            f"Storage queue approaching capacity: "
                            f"{stats.queue_length}/{self.storage_manager.max_queue_size}"
                        )

                    if stats.error_rate > 5.0:
                        logger.warning(
                            f"High storage error rate: {stats.error_rate:.2f}%"
                        )

                    if (
                        stats.cache_hit_rate < 50.0
                        and stats.cache_hits + stats.cache_misses > 100
                    ):
                        logger.warning(
                            f"Low cache hit rate: {stats.cache_hit_rate:.1f}%"
                        )

            except Exception as e:
                logger.error(f"Error in metrics collection task: {e}")

    async def shutdown(self):
        """Shutdown background tasks"""
        # Cancel all tasks
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()

        if self._metrics_task and not self._metrics_task.done():
            self._metrics_task.cancel()

        # Wait for tasks to complete
        for task in [self._cleanup_task, self._metrics_task]:
            if task and not task.done():
                try:
                    await task
                except asyncio.CancelledError:
                    pass
