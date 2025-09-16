"""
Core monitoring functionality for Cache Performance Monitor

Handles event collection, background monitoring, and performance threshold checking.
"""

import asyncio
import time
import uuid
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict

from app.core.logging import get_logger
from app.services.caching.auth_cache_service import get_auth_cache_service
from app.services.monitoring.performance_metrics_collector import get_metrics_collector

from .base import CacheLayer, CacheOperation, CachePerformanceEvent, CacheResult

logger = get_logger(__name__)


class CacheMonitoringService:
    """Core service for cache performance monitoring"""

    def __init__(self, max_events: int = 50000):
        self.max_events = max_events
        self.events: deque[CachePerformanceEvent] = deque(maxlen=max_events)

        # Background monitoring
        self.monitoring_enabled = True
        self.background_task: asyncio.Task = None
        self.executor = ThreadPoolExecutor(
            max_workers=2, thread_name_prefix="cache-monitor"
        )

        # Services
        self.auth_cache_service = get_auth_cache_service()
        self.metrics_collector = get_metrics_collector()

        logger.info(f"CacheMonitoringService initialized with {max_events} max events")

    def start_background_monitoring(self) -> None:
        """Start background monitoring tasks"""
        if self.background_task is None or self.background_task.done():
            self.background_task = asyncio.create_task(self._background_monitor_loop())
            logger.info("Background cache monitoring started")

    async def _background_monitor_loop(self) -> None:
        """Background monitoring loop"""
        while self.monitoring_enabled:
            try:
                await self._collect_cache_health_metrics()
                await asyncio.sleep(60)  # Check every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in background cache monitoring: {e}")
                await asyncio.sleep(120)  # Wait longer on error

    async def _collect_cache_health_metrics(self) -> None:
        """Collect cache health metrics from services"""
        try:
            # Get auth cache health data
            if hasattr(self.auth_cache_service, "get_health_data"):
                health_data = await self.auth_cache_service.get_health_data()
                self._process_health_check_results(health_data)

        except Exception as e:
            logger.error(f"Error collecting cache health metrics: {e}")

    def _process_health_check_results(self, health_data: Dict[str, Any]) -> None:
        """Process health check results and create performance events"""
        try:
            current_time = time.time()

            # Process Redis stats if available
            redis_stats = health_data.get("redis", {})
            if redis_stats:
                event = CachePerformanceEvent(
                    operation_id=str(uuid.uuid4()),
                    operation=CacheOperation.HEALTH_CHECK,
                    cache_layer=CacheLayer.REDIS,
                    key_pattern="health_check",
                    start_time=current_time,
                    end_time=current_time,
                    result=(
                        CacheResult.SUCCESS
                        if redis_stats.get("connected")
                        else CacheResult.ERROR
                    ),
                    metadata=redis_stats,
                )
                self.events.append(event)

            # Process memory cache stats if available
            memory_stats = health_data.get("memory", {})
            if memory_stats:
                event = CachePerformanceEvent(
                    operation_id=str(uuid.uuid4()),
                    operation=CacheOperation.HEALTH_CHECK,
                    cache_layer=CacheLayer.MEMORY,
                    key_pattern="health_check",
                    start_time=current_time,
                    end_time=current_time,
                    result=CacheResult.SUCCESS,
                    metadata=memory_stats,
                )
                self.events.append(event)

        except Exception as e:
            logger.error(f"Error processing health check results: {e}")

    def record_cache_operation(
        self,
        operation: CacheOperation,
        cache_layer: CacheLayer,
        key_pattern: str,
        start_time: float,
        end_time: float,
        result: CacheResult,
        data_size_bytes: int = 0,
        metadata: Dict[str, Any] = None,
    ) -> str:
        """Record a cache operation performance event"""
        operation_id = str(uuid.uuid4())

        event = CachePerformanceEvent(
            operation_id=operation_id,
            operation=operation,
            cache_layer=cache_layer,
            key_pattern=key_pattern,
            start_time=start_time,
            end_time=end_time,
            result=result,
            data_size_bytes=data_size_bytes,
            metadata=metadata or {},
        )

        self.events.append(event)

        # Check performance thresholds
        self._check_performance_thresholds(event)

        return operation_id

    def _check_performance_thresholds(self, event: CachePerformanceEvent) -> None:
        """Check if event exceeds performance thresholds and log warnings"""
        duration_ms = event.duration_ms

        # Response time thresholds
        if duration_ms > 1000:  # 1 second threshold
            logger.warning(
                f"Slow cache operation: {event.operation} on {event.cache_layer} "
                f"took {duration_ms:.2f}ms for key pattern '{event.key_pattern}'"
            )
        elif duration_ms > 500:  # 500ms warning
            logger.info(
                f"Cache operation warning: {event.operation} on {event.cache_layer} "
                f"took {duration_ms:.2f}ms for key pattern '{event.key_pattern}'"
            )

        # Error tracking
        if event.result in [CacheResult.ERROR, CacheResult.TIMEOUT]:
            logger.error(
                f"Cache operation failed: {event.operation} on {event.cache_layer} "
                f"resulted in {event.result} for key pattern '{event.key_pattern}'"
            )

    def cleanup_old_events(self, max_age_hours: int = 24) -> int:
        """Clean up old events to prevent memory bloat"""
        cutoff_time = time.time() - (max_age_hours * 3600)
        initial_count = len(self.events)

        # Filter out old events
        self.events = deque(
            (event for event in self.events if event.start_time >= cutoff_time),
            maxlen=self.max_events,
        )

        cleaned_count = initial_count - len(self.events)

        if cleaned_count > 0:
            logger.debug(f"Cleaned up {cleaned_count} old cache performance events")

        return cleaned_count

    async def shutdown(self) -> None:
        """Shutdown monitoring service"""
        logger.info("Shutting down cache monitoring service...")

        self.monitoring_enabled = False

        if self.background_task and not self.background_task.done():
            self.background_task.cancel()
            try:
                await self.background_task
            except asyncio.CancelledError:
                pass

        self.executor.shutdown(wait=True)

        logger.info("Cache monitoring service shutdown complete")

    def get_events(self) -> deque:
        """Get current events collection"""
        return self.events
