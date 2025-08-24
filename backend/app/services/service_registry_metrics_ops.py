"""
Service Registry Metrics Operations Module

This module contains metrics buffer management and flushing operations for the ServiceRegistry.
Extracted from main service_registry.py to keep the main file under 400 lines.
"""

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from app.core.logging import get_logger

# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from app.services.service_registry import ServiceRegistry, MetricRecord

logger = get_logger(__name__)


class ServiceRegistryMetricsOps:
    """
    Metrics operations for ServiceRegistry that handles buffer management and flushing.

    This class provides:
    - Bounded metrics buffer management
    - Non-blocking metrics flushing
    - Periodic flush scheduling
    - Async metrics writing
    """

    def __init__(self, registry: "ServiceRegistry"):
        """Initialize metrics operations with reference to parent registry"""
        self._registry = registry
        self._logger = logger

    def record_metric(
        self,
        service_name: str,
        metric_name: str,
        metric_value: Any,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Record a metric in the bounded buffer with automatic flushing.

        This method provides non-blocking metrics collection:
        1. Creates a metric record with timestamp
        2. Adds to bounded buffer (auto-evicts old metrics if full)
        3. Triggers automatic flush if buffer reaches max size
        4. Ensures metrics don't block main execution flow

        Args:
            service_name: Name of the service recording the metric
            metric_name: Name/type of the metric
            metric_value: The metric value (number, string, etc.)
            metadata: Optional additional metadata
        """
        if self._registry._is_closed:
            self._logger.warning(
                f"Attempted to record metric on closed registry {self._registry._registry_id}",
                extra={
                    "registry_id": self._registry._registry_id,
                    "metric_name": metric_name,
                },
            )
            return

        # Import here to avoid circular imports
        from app.services.service_registry import MetricRecord

        metric_record = MetricRecord(
            timestamp=datetime.now(timezone.utc),
            service_name=service_name,
            metric_name=metric_name,
            metric_value=metric_value,
            metadata=metadata or {},
        )

        # Add to bounded buffer (automatically evicts oldest if at max size)
        self._registry._metrics_buffer.append(metric_record)

        self._logger.debug(
            f"Recorded metric {metric_name} for {service_name}",
            extra={
                "registry_id": self._registry._registry_id,
                "service_name": service_name,
                "metric_name": metric_name,
                "buffer_size": len(self._registry._metrics_buffer),
                "metric_value": metric_value,
            },
        )

        # Auto-flush if buffer is full
        if (
            len(self._registry._metrics_buffer)
            >= self._registry.MAX_METRICS_BUFFER_SIZE
        ):
            self._logger.debug(
                f"Metrics buffer full ({len(self._registry._metrics_buffer)}), triggering auto-flush",
                extra={"registry_id": self._registry._registry_id},
            )
            # Trigger flush only if no flush task is currently running
            # This prevents concurrent flushes and potential race conditions
            if (
                not self._registry._metrics_flush_task
                or self._registry._metrics_flush_task.done()
            ):
                try:
                    asyncio.get_running_loop()
                except RuntimeError:
                    # No running loop; skip scheduling and allow periodic/next async op to flush
                    self._logger.debug(
                        "No event loop running, skipping auto-flush scheduling",
                        extra={"registry_id": self._registry._registry_id},
                    )
                    return
                self._registry._metrics_flush_task = asyncio.create_task(
                    self.flush_metrics(),
                    name=f"metrics_flush_{self._registry._registry_id}",
                )

    async def flush_metrics(self) -> None:
        """
        Flush metrics buffer non-blocking.

        This method:
        1. Copies current metrics buffer
        2. Clears the buffer for new metrics
        3. Writes metrics asynchronously without blocking
        4. Handles flush failures gracefully
        """
        # Start periodic flush if not started (first async operation)
        if not self._registry._periodic_flush_started:
            self._start_periodic_flush()

        if not self._registry._metrics_buffer:
            return

        # Copy metrics and clear buffer atomically
        metrics_to_flush = list(self._registry._metrics_buffer)
        self._registry._metrics_buffer.clear()

        self._logger.debug(
            f"Flushing {len(metrics_to_flush)} metrics",
            extra={
                "registry_id": self._registry._registry_id,
                "metrics_count": len(metrics_to_flush),
            },
        )

        try:
            # Write metrics asynchronously (use registry method for backward compatibility)
            await self._registry._write_metrics_async(metrics_to_flush)

            # Track metrics flush in monitor
            self._registry._monitor.track_metrics_flush(
                self._registry._registry_id, len(metrics_to_flush)
            )

            self._logger.debug(
                f"Successfully flushed {len(metrics_to_flush)} metrics",
                extra={
                    "registry_id": self._registry._registry_id,
                    "metrics_count": len(metrics_to_flush),
                },
            )

        except Exception as e:
            self._logger.error(
                f"Failed to flush metrics: {e}",
                extra={
                    "registry_id": self._registry._registry_id,
                    "metrics_count": len(metrics_to_flush),
                    "error": str(e),
                },
            )
            # Note: We don't re-queue failed metrics to prevent memory accumulation
            # In production, consider dead letter queue for critical metrics

    def _start_periodic_flush(self) -> None:
        """Start periodic metrics flush task."""
        # Only start if we have an event loop and haven't started yet
        if self._registry._periodic_flush_started:
            return

        try:
            asyncio.get_running_loop()
        except RuntimeError:
            # No event loop available, skip periodic flush
            self._logger.debug(
                "No event loop available for periodic flush, will start on first async operation"
            )
            return

        if (
            not self._registry._periodic_flush_task
            or self._registry._periodic_flush_task.done()
        ):
            self._registry._periodic_flush_task = asyncio.create_task(
                self._periodic_flush_loop(),
                name=f"periodic_flush_{self._registry._registry_id}",
            )
            self._registry._periodic_flush_started = True

    async def _periodic_flush_loop(self) -> None:
        """Periodically flush metrics to prevent long-lived buffers."""
        try:
            while not self._registry._is_closed:
                # Wait 30 seconds between flushes
                await asyncio.sleep(30)

                # Flush if we have any metrics
                if self._registry._metrics_buffer and not self._registry._is_closed:
                    self._logger.debug(
                        f"Periodic flush triggered for {len(self._registry._metrics_buffer)} metrics",
                        extra={"registry_id": self._registry._registry_id},
                    )
                    await self.flush_metrics()
        except asyncio.CancelledError:
            # Task was cancelled, this is expected during cleanup
            pass
        except Exception as e:
            self._logger.error(
                f"Periodic flush task failed: {e}",
                extra={"registry_id": self._registry._registry_id, "error": str(e)},
            )

    async def _write_metrics_async(self, metrics: List["MetricRecord"]) -> None:
        """
        Write metrics asynchronously without blocking main execution.

        This method handles the actual I/O for metrics writing:
        1. Serializes metrics to appropriate format
        2. Writes to configured metrics store (database, time-series DB, etc.)
        3. Handles write failures gracefully
        4. Provides minimal latency impact on main execution

        Args:
            metrics: List of metric records to write

        Note:
            This is a placeholder implementation. In production, this would
            write to your actual metrics storage (InfluxDB, Prometheus, etc.)
        """
        try:
            # Serialize metrics for storage
            serialized_metrics = [metric.to_dict() for metric in metrics]

            # TODO: Replace with actual metrics storage implementation
            # Examples:
            # - Write to InfluxDB for time-series data
            # - Write to Prometheus pushgateway
            # - Write to database metrics table
            # - Send to external monitoring service

            # For now, log the metrics at debug level
            self._logger.debug(
                f"Writing {len(serialized_metrics)} metrics to storage",
                extra={
                    "registry_id": self._registry._registry_id,
                    "metrics_data": serialized_metrics,
                    "storage_type": "placeholder_logging",
                },
            )

            # Simulate async I/O operation
            await asyncio.sleep(0.01)

        except Exception as e:
            # Re-raise for caller to handle
            self._logger.error(
                f"Metrics write operation failed: {e}",
                extra={
                    "registry_id": self._registry._registry_id,
                    "metrics_count": len(metrics),
                    "error": str(e),
                },
            )
            raise
