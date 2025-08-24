"""
Service Registry Operations Module

This module contains cleanup, statistics, and utility operations for the ServiceRegistry.
Extracted from main service_registry.py to keep the main file under 400 lines.
"""

import asyncio
from typing import Any, Dict, TYPE_CHECKING

from app.core.logging import get_logger

# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from app.services.service_registry import ServiceRegistry

logger = get_logger(__name__)


class ServiceRegistryOperations:
    """
    Operations mixin for ServiceRegistry that handles cleanup and statistics.

    This class provides:
    - Registry cleanup operations
    - Performance statistics collection
    - Task cancellation utilities
    - Registry state management
    """

    def __init__(self, registry: "ServiceRegistry"):
        """Initialize operations with reference to parent registry"""
        self._registry = registry
        self._logger = logger

    async def cleanup_registry(self) -> None:
        """
        Perform complete registry cleanup.

        This method ensures proper cleanup without affecting orchestrator resources:
        1. Flushes any remaining metrics
        2. Clears service cache (services are garbage collected)
        3. Cancels any pending flush tasks
        4. Marks registry as closed
        5. NEVER closes the database session (orchestrator owns it)
        """
        try:
            # Mark as closed first to prevent new metrics from being recorded during shutdown
            self._registry._is_closed = True

            # Flush any remaining metrics (use the public method for backward compatibility)
            if self._registry._metrics_buffer:
                await self._registry._flush_metrics()

            # Cancel any pending flush tasks
            await self._cancel_flush_tasks()

            # Clear service cache (services will be garbage collected)
            self._registry._service_cache.clear()

            # Track registry cleanup in monitor
            self._registry._monitor.track_registry_cleanup(self._registry._registry_id)

            self._logger.debug(
                f"ServiceRegistry cleanup completed {self._registry._registry_id}",
                extra={"registry_id": self._registry._registry_id},
            )

        except Exception as cleanup_error:
            self._logger.error(
                f"Error during ServiceRegistry cleanup: {cleanup_error}",
                extra={
                    "registry_id": self._registry._registry_id,
                    "cleanup_error": str(cleanup_error),
                },
            )
            # Don't re-raise cleanup errors - log and continue

    async def _cancel_flush_tasks(self) -> None:
        """Cancel all pending flush tasks gracefully"""
        # Cancel metrics flush task
        if (
            self._registry._metrics_flush_task
            and not self._registry._metrics_flush_task.done()
        ):
            self._registry._metrics_flush_task.cancel()
            try:
                await self._registry._metrics_flush_task
            except asyncio.CancelledError:
                pass

        # Cancel periodic flush task
        if (
            self._registry._periodic_flush_task
            and not self._registry._periodic_flush_task.done()
        ):
            self._registry._periodic_flush_task.cancel()
            try:
                await self._registry._periodic_flush_task
            except asyncio.CancelledError:
                pass

    def get_registry_stats(self) -> Dict[str, Any]:
        """
        Get current registry statistics for monitoring and debugging.

        Returns:
            Dictionary containing registry statistics
        """
        return {
            "registry_id": self._registry._registry_id,
            "is_closed": self._registry._is_closed,
            "services_cached": len(self._registry._service_cache),
            "cached_service_types": [
                cls.__name__ for cls in self._registry._service_cache.keys()
            ],
            "metrics_buffered": len(self._registry._metrics_buffer),
            "has_audit_logger": self._registry._audit_logger is not None,
            "context_client_id": self._registry._context.client_account_id,
            "context_engagement_id": self._registry._context.engagement_id,
            "context_flow_id": self._registry._context.flow_id,
        }

    def validate_registry_state(self) -> bool:
        """
        Validate that registry is in a valid state for operations.

        Returns:
            True if registry is ready for operations, False if closed/invalid
        """
        if self._registry._is_closed:
            self._logger.warning(
                f"Registry {self._registry._registry_id} is closed",
                extra={"registry_id": self._registry._registry_id},
            )
            return False

        return True
