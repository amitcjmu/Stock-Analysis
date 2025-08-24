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
- Integrated performance monitoring via ServiceRegistryMonitor

Security & Performance:
- Bounded metrics buffer prevents memory exhaustion
- Non-blocking metrics flushing prevents I/O bottlenecks
- Proper cleanup ensures no resource leaks
- Session ownership remains with orchestrator for transaction control
- Real-time performance tracking and cache hit rate monitoring
"""

import asyncio
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Type, TypeVar, cast, TYPE_CHECKING
from collections import deque
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.logging import get_logger
from app.services.service_registry_metrics import get_monitor
from app.services.service_registry_metrics_ops import ServiceRegistryMetricsOps
from app.services.service_registry_operations import ServiceRegistryOperations

# Use TYPE_CHECKING to avoid circular imports while maintaining type hints
if TYPE_CHECKING:
    from app.services.flow_orchestration.tool_audit_logger import ToolAuditLogger

# Type variable for service classes
T = TypeVar("T")


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
        audit_logger: Optional["ToolAuditLogger"] = None,
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

        # Get the global monitor instance for performance tracking
        self._monitor = get_monitor()

        # Initialize metrics and operations modules
        self._metrics_ops = ServiceRegistryMetricsOps(self)
        self._operations = ServiceRegistryOperations(self)

        # Track registry creation in monitor
        self._monitor.track_registry_creation(self._registry_id)

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

        # Track start time for instantiation measurement
        start_time = time.perf_counter()

        # Check cache first
        if service_class in self._service_cache:
            execution_time_ms = (time.perf_counter() - start_time) * 1000

            # Track cache hit in monitor
            self._monitor.track_service_instantiation(
                self._registry_id,
                service_class.__name__,
                execution_time_ms,
                cache_hit=True,
            )

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

            # Calculate instantiation time
            execution_time_ms = (time.perf_counter() - start_time) * 1000

            # Track cache miss and instantiation in monitor
            self._monitor.track_service_instantiation(
                self._registry_id,
                service_class.__name__,
                execution_time_ms,
                cache_hit=False,
            )

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

    def get_audit_logger(self) -> Optional["ToolAuditLogger"]:
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

        This method delegates to the metrics operations module for non-blocking
        metrics collection and automatic flushing.

        Args:
            service_name: Name of the service recording the metric
            metric_name: Name/type of the metric
            metric_value: The metric value (number, string, etc.)
            metadata: Optional additional metadata
        """
        self._metrics_ops.record_metric(
            service_name, metric_name, metric_value, metadata
        )

    async def _flush_metrics(self) -> None:
        """
        Flush metrics buffer non-blocking.

        Delegates to metrics operations module for backward compatibility.
        """
        await self._metrics_ops.flush_metrics()

    def _start_periodic_flush(self) -> None:
        """Start periodic metrics flush task - delegates to metrics operations."""
        self._metrics_ops._start_periodic_flush()

    async def _periodic_flush_loop(self) -> None:
        """Periodic flush loop - delegates to metrics operations."""
        await self._metrics_ops._periodic_flush_loop()

    async def _write_metrics_async(self, metrics: List[MetricRecord]) -> None:
        """Write metrics async - delegates to metrics operations."""
        await self._metrics_ops._write_metrics_async(metrics)

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
            self._metrics_ops._start_periodic_flush()

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

        # Delegate cleanup to operations module
        await self._operations.cleanup_registry()

    def get_registry_stats(self) -> Dict[str, Any]:
        """
        Get current registry statistics for monitoring and debugging.

        Delegates to operations module for backward compatibility.

        Returns:
            Dictionary containing registry statistics
        """
        return self._operations.get_registry_stats()
