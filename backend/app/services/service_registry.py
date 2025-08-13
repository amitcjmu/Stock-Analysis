"""
Service Registry for Service Registry Architecture

This module provides the ServiceRegistry class that manages service lifecycle per execution,
providing dependency injection for tools while ensuring the orchestrator maintains session ownership.

Key Features:
- Per-execution service registry that caches service instances
- Receives AsyncSession, RequestContext, and optional ToolAuditLogger from orchestrator
- NEVER owns or closes the database session - only clears service cache on cleanup
- Provides get_service() for lazy service instantiation
- Provides get_audit_logger() for tools to access injected logger
- Includes bounded metrics buffer (max 100 items) with automatic flushing
- Implements async context manager for proper cleanup

Security & Performance:
- Bounded metrics buffer prevents memory exhaustion
- Non-blocking metrics flushing prevents I/O bottlenecks
- Proper cleanup ensures no resource leaks
- Session ownership remains with orchestrator for transaction control
"""

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Type, TypeVar, cast
from collections import deque
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.logging import get_logger

# Type variable for service classes
T = TypeVar("T")


# Import the real ToolAuditLogger
from app.services.flow_orchestration.tool_audit_logger import ToolAuditLogger


@dataclass
class MetricRecord:
    """Represents a single metric record"""

    timestamp: datetime
    service_name: str
    metric_name: str
    metric_value: Any
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert metric record to dictionary for serialization"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "service_name": self.service_name,
            "metric_name": self.metric_name,
            "metric_value": self.metric_value,
            "metadata": self.metadata,
        }


class ServiceRegistry:
    """
    Per-execution service registry that manages service lifecycle and provides dependency injection.

    The ServiceRegistry provides:
    - Lazy service instantiation and caching per execution
    - Database session propagation without ownership
    - Request context propagation to all services
    - Optional audit logger injection for tools
    - Bounded metrics collection with automatic flushing
    - Proper cleanup without closing orchestrator-owned resources

    Key Principles:
    1. ServiceRegistry receives resources (session, context, audit_logger) from orchestrator
    2. ServiceRegistry NEVER closes or commits the database session
    3. ServiceRegistry only clears its service cache on cleanup
    4. Services are instantiated lazily and cached for the execution lifetime
    5. Metrics are buffered and flushed non-blocking to prevent I/O bottlenecks
    """

    # Maximum number of metrics to buffer before auto-flush
    MAX_METRICS_BUFFER_SIZE = 100

    def __init__(
        self,
        db: AsyncSession,
        context: RequestContext,
        audit_logger: Optional[ToolAuditLogger] = None,
    ):
        """
        Initialize the service registry with orchestrator-provided resources.

        Args:
            db: Active AsyncSession from orchestrator (DO NOT close/commit)
            context: Request context with client, engagement, user info
            audit_logger: Optional audit logger for tool operations

        Raises:
            ValueError: If db or context is None
        """
        if db is None:
            raise ValueError("Database session is required")
        if context is None:
            raise ValueError("Request context is required")

        self._db = db
        self._context = context
        self._audit_logger = audit_logger
        self._logger = get_logger(self.__class__.__module__)

        # Service instance cache - cleared on cleanup, never persisted
        self._service_cache: Dict[Type, Any] = {}

        # Bounded metrics buffer with automatic flushing
        self._metrics_buffer: deque = deque(maxlen=self.MAX_METRICS_BUFFER_SIZE)
        self._metrics_flush_task: Optional[asyncio.Task] = None
        self._periodic_flush_task: Optional[asyncio.Task] = None

        # Track registry lifecycle for debugging
        self._registry_id = f"registry_{id(self)}"
        self._is_closed = False
        
        # Don't start periodic flush immediately - defer until first use or context entry
        # This avoids issues with event loop not being available during init
        self._periodic_flush_started = False

        self._logger.debug(
            f"Initialized ServiceRegistry {self._registry_id}",
            extra={
                "registry_id": self._registry_id,
                "context_client_id": self._context.client_account_id,
                "context_engagement_id": self._context.engagement_id,
                "has_audit_logger": self._audit_logger is not None,
            },
        )

    def get_service(self, service_class: Type[T]) -> T:
        """
        Get or create a service instance with lazy instantiation and caching.

        This method provides dependency injection by:
        1. Checking if service is already cached
        2. If not cached, instantiating with db and context
        3. Caching the instance for subsequent requests
        4. Returning the service instance

        Args:
            service_class: The service class to instantiate

        Returns:
            Service instance of the requested type

        Raises:
            ValueError: If registry is closed or service_class is invalid
            TypeError: If service_class cannot be instantiated with expected signature
        """
        if self._is_closed:
            raise ValueError(
                f"Cannot get service from closed registry {self._registry_id}"
            )

        if service_class is None:
            raise ValueError("Service class cannot be None")

        # Check cache first
        if service_class in self._service_cache:
            self._logger.debug(
                f"Returning cached service {service_class.__name__}",
                extra={
                    "registry_id": self._registry_id,
                    "service_class": service_class.__name__,
                    "cache_hit": True,
                },
            )
            return cast(T, self._service_cache[service_class])

        # Instantiate new service
        try:
            # All services in the Service Registry pattern should accept (session, context)
            service_instance = service_class(self._db, self._context)

            # Cache the instance
            self._service_cache[service_class] = service_instance

            self._logger.debug(
                f"Created and cached service {service_class.__name__}",
                extra={
                    "registry_id": self._registry_id,
                    "service_class": service_class.__name__,
                    "cache_hit": False,
                    "cache_size": len(self._service_cache),
                },
            )

            return cast(T, service_instance)

        except Exception as e:
            self._logger.error(
                f"Failed to instantiate service {service_class.__name__}: {e}",
                extra={
                    "registry_id": self._registry_id,
                    "service_class": service_class.__name__,
                    "error": str(e),
                },
            )
            raise TypeError(
                f"Cannot instantiate {service_class.__name__}. "
                f"Ensure it accepts (AsyncSession, RequestContext) constructor parameters."
            ) from e

    def get_audit_logger(self) -> Optional[ToolAuditLogger]:
        """
        Get the injected audit logger for tools to use.

        This method provides access to the audit logger that was injected
        by the orchestrator. Tools can use this to log their operations
        and maintain audit trails.

        Returns:
            The injected ToolAuditLogger instance, or None if not provided
        """
        if self._is_closed:
            self._logger.warning(
                f"Attempted to get audit logger from closed registry {self._registry_id}",
                extra={"registry_id": self._registry_id},
            )
            return None

        self._logger.debug(
            f"Providing audit logger (available: {self._audit_logger is not None})",
            extra={
                "registry_id": self._registry_id,
                "has_audit_logger": self._audit_logger is not None,
            },
        )

        return self._audit_logger

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
        if self._is_closed:
            self._logger.warning(
                f"Attempted to record metric on closed registry {self._registry_id}",
                extra={"registry_id": self._registry_id, "metric_name": metric_name},
            )
            return

        metric_record = MetricRecord(
            timestamp=datetime.now(timezone.utc),
            service_name=service_name,
            metric_name=metric_name,
            metric_value=metric_value,
            metadata=metadata or {},
        )

        # Add to bounded buffer (automatically evicts oldest if at max size)
        self._metrics_buffer.append(metric_record)

        self._logger.debug(
            f"Recorded metric {metric_name} for {service_name}",
            extra={
                "registry_id": self._registry_id,
                "service_name": service_name,
                "metric_name": metric_name,
                "buffer_size": len(self._metrics_buffer),
                "metric_value": metric_value,
            },
        )

        # Auto-flush if buffer is full
        if len(self._metrics_buffer) >= self.MAX_METRICS_BUFFER_SIZE:
            self._logger.debug(
                f"Metrics buffer full ({len(self._metrics_buffer)}), triggering auto-flush",
                extra={"registry_id": self._registry_id},
            )
            asyncio.create_task(
                self._flush_metrics(), name=f"metrics_flush_{self._registry_id}"
            )

    async def _flush_metrics(self) -> None:
        """
        Flush metrics buffer non-blocking.

        This method:
        1. Copies current metrics buffer
        2. Clears the buffer for new metrics
        3. Writes metrics asynchronously without blocking
        4. Handles flush failures gracefully
        """
        # Start periodic flush if not started (first async operation)
        if not self._periodic_flush_started:
            self._start_periodic_flush()
            
        if not self._metrics_buffer:
            return

        # Copy metrics and clear buffer atomically
        metrics_to_flush = list(self._metrics_buffer)
        self._metrics_buffer.clear()

        self._logger.debug(
            f"Flushing {len(metrics_to_flush)} metrics",
            extra={
                "registry_id": self._registry_id,
                "metrics_count": len(metrics_to_flush),
            },
        )

        try:
            # Write metrics asynchronously
            await self._write_metrics_async(metrics_to_flush)

            self._logger.debug(
                f"Successfully flushed {len(metrics_to_flush)} metrics",
                extra={
                    "registry_id": self._registry_id,
                    "metrics_count": len(metrics_to_flush),
                },
            )

        except Exception as e:
            self._logger.error(
                f"Failed to flush metrics: {e}",
                extra={
                    "registry_id": self._registry_id,
                    "metrics_count": len(metrics_to_flush),
                    "error": str(e),
                },
            )
            # Note: We don't re-queue failed metrics to prevent memory accumulation
            # In production, consider dead letter queue for critical metrics

    def _start_periodic_flush(self) -> None:
        """Start periodic metrics flush task."""
        # Only start if we have an event loop and haven't started yet
        if self._periodic_flush_started:
            return
            
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # No event loop available, skip periodic flush
            self._logger.debug(
                "No event loop available for periodic flush, will start on first async operation"
            )
            return
            
        if not self._periodic_flush_task or self._periodic_flush_task.done():
            self._periodic_flush_task = asyncio.create_task(
                self._periodic_flush_loop(),
                name=f"periodic_flush_{self._registry_id}"
            )
            self._periodic_flush_started = True
    
    async def _periodic_flush_loop(self) -> None:
        """Periodically flush metrics to prevent long-lived buffers."""
        try:
            while not self._is_closed:
                # Wait 30 seconds between flushes
                await asyncio.sleep(30)
                
                # Flush if we have any metrics
                if self._metrics_buffer and not self._is_closed:
                    self._logger.debug(
                        f"Periodic flush triggered for {len(self._metrics_buffer)} metrics",
                        extra={"registry_id": self._registry_id}
                    )
                    await self._flush_metrics()
        except asyncio.CancelledError:
            # Task was cancelled, this is expected during cleanup
            pass
        except Exception as e:
            self._logger.error(
                f"Periodic flush task failed: {e}",
                extra={"registry_id": self._registry_id, "error": str(e)}
            )
    
    async def _write_metrics_async(self, metrics: List[MetricRecord]) -> None:
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
                    "registry_id": self._registry_id,
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
                    "registry_id": self._registry_id,
                    "metrics_count": len(metrics),
                    "error": str(e),
                },
            )
            raise

    async def __aenter__(self):
        """
        Async context manager entry.

        Returns:
            Self for use in 'async with' statements
        """
        self._logger.debug(
            f"Entering ServiceRegistry context {self._registry_id}",
            extra={"registry_id": self._registry_id},
        )
        
        # Start periodic flush when entering context (event loop available)
        if not self._periodic_flush_started:
            self._start_periodic_flush()
        
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Async context manager exit with proper cleanup.

        This method ensures proper cleanup without affecting orchestrator resources:
        1. Flushes any remaining metrics
        2. Clears service cache (services are garbage collected)
        3. Cancels any pending flush tasks
        4. Marks registry as closed
        5. NEVER closes the database session (orchestrator owns it)

        Args:
            exc_type: Exception type (if any)
            exc_val: Exception value (if any)
            exc_tb: Exception traceback (if any)
        """
        self._logger.debug(
            f"Exiting ServiceRegistry context {self._registry_id}",
            extra={
                "registry_id": self._registry_id,
                "had_exception": exc_type is not None,
                "services_cached": len(self._service_cache),
                "metrics_buffered": len(self._metrics_buffer),
            },
        )

        try:
            # Flush any remaining metrics
            if self._metrics_buffer:
                await self._flush_metrics()

            # Cancel any pending flush tasks
            if self._metrics_flush_task and not self._metrics_flush_task.done():
                self._metrics_flush_task.cancel()
                try:
                    await self._metrics_flush_task
                except asyncio.CancelledError:
                    pass
            
            # Cancel periodic flush task
            if self._periodic_flush_task and not self._periodic_flush_task.done():
                self._periodic_flush_task.cancel()
                try:
                    await self._periodic_flush_task
                except asyncio.CancelledError:
                    pass

            # Clear service cache (services will be garbage collected)
            self._service_cache.clear()

            # Mark as closed
            self._is_closed = True

            self._logger.debug(
                f"ServiceRegistry cleanup completed {self._registry_id}",
                extra={"registry_id": self._registry_id},
            )

        except Exception as cleanup_error:
            self._logger.error(
                f"Error during ServiceRegistry cleanup: {cleanup_error}",
                extra={
                    "registry_id": self._registry_id,
                    "cleanup_error": str(cleanup_error),
                },
            )
            # Don't re-raise cleanup errors - log and continue

    def get_registry_stats(self) -> Dict[str, Any]:
        """
        Get current registry statistics for monitoring and debugging.

        Returns:
            Dictionary containing registry statistics
        """
        return {
            "registry_id": self._registry_id,
            "is_closed": self._is_closed,
            "services_cached": len(self._service_cache),
            "cached_service_types": [
                cls.__name__ for cls in self._service_cache.keys()
            ],
            "metrics_buffered": len(self._metrics_buffer),
            "has_audit_logger": self._audit_logger is not None,
            "context_client_id": self._context.client_account_id,
            "context_engagement_id": self._context.engagement_id,
            "context_flow_id": self._context.flow_id,
        }
