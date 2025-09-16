"""
Core error recovery system implementation.

Main ErrorRecoverySystem class that orchestrates recovery operations,
background sync jobs, and health monitoring.
"""

import asyncio
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple

from app.core.config import settings
from app.core.logging import get_logger
from app.services.auth.fallback_orchestrator import (
    FallbackOrchestrator,
    OperationType,
    get_fallback_orchestrator,
)
from app.services.monitoring.service_health_manager import (
    ServiceHealthManager,
    ServiceType,
    get_service_health_manager,
)

from .dlq import DeadLetterQueue
from .models import (
    FailureCategory,
    RecoveryOperation,
    RecoveryPriority,
    RecoveryType,
)
from .sync import SyncJobManager
from .utils import (
    calculate_retry_delay,
    get_recovery_stats_summary,
    perform_consistency_check,
)
from .workers import RecoveryWorkerMixin

logger = get_logger(__name__)


class ErrorRecoverySystem(RecoveryWorkerMixin):
    """
    Comprehensive Error Recovery System

    Provides automatic error recovery, background synchronization, data consistency
    checks, and dead letter queue management for failed operations.
    """

    def __init__(
        self,
        health_manager: Optional[ServiceHealthManager] = None,
        fallback_orchestrator: Optional[FallbackOrchestrator] = None,
    ):
        self.health_manager = health_manager or get_service_health_manager()
        self.fallback_orchestrator = (
            fallback_orchestrator or get_fallback_orchestrator()
        )

        # Recovery queues by priority
        self.recovery_queues: Dict[RecoveryPriority, deque] = {
            priority: deque() for priority in RecoveryPriority
        }

        # Sync job manager
        self.sync_manager = SyncJobManager()

        # Dead letter queue
        self.dead_letter_queue = DeadLetterQueue()

        # Recovery statistics
        self.recovery_stats: Dict[RecoveryType, Dict[str, int]] = defaultdict(
            lambda: {"attempts": 0, "successes": 0, "failures": 0}
        )

        # Service recovery tracking
        self.service_recovery_callbacks: Dict[ServiceType, List[Callable]] = (
            defaultdict(list)
        )
        self.last_service_health: Dict[ServiceType, bool] = {}

        # Background task management
        self.enabled = True
        self.recovery_worker_task: Optional[asyncio.Task] = None
        self.sync_worker_task: Optional[asyncio.Task] = None
        self.health_monitor_task: Optional[asyncio.Task] = None

        # Configuration
        self.max_queue_size = getattr(settings, "RECOVERY_MAX_QUEUE_SIZE", 10000)
        self.worker_batch_size = getattr(settings, "RECOVERY_WORKER_BATCH_SIZE", 10)
        self.sync_batch_size = getattr(settings, "RECOVERY_SYNC_BATCH_SIZE", 100)

        # Consistency check configuration
        self.consistency_check_enabled = True
        self.consistency_check_sample_rate = 0.1  # Check 10% of operations

        logger.info(
            "ErrorRecoverySystem initialized with comprehensive recovery capabilities"
        )

        # Start background workers
        if self.enabled:
            self._start_background_workers()

    async def schedule_recovery_operation(
        self,
        operation_func: Callable,
        operation_args: Tuple = (),
        operation_kwargs: Optional[Dict[str, Any]] = None,
        recovery_type: RecoveryType = RecoveryType.IMMEDIATE_RETRY,
        failure_category: FailureCategory = FailureCategory.UNKNOWN,
        priority: RecoveryPriority = RecoveryPriority.NORMAL,
        operation_type: OperationType = OperationType.CACHE_READ,
        service_type: ServiceType = ServiceType.REDIS,
        context_data: Optional[Dict[str, Any]] = None,
        success_callback: Optional[Callable] = None,
        failure_callback: Optional[Callable] = None,
        **recovery_config,
    ) -> str:
        """
        Schedule a recovery operation

        Args:
            operation_func: Function to execute for recovery
            operation_args: Arguments for the operation function
            operation_kwargs: Keyword arguments for the operation function
            recovery_type: Type of recovery operation
            failure_category: Category of failure for strategy selection
            priority: Priority level for processing order
            operation_type: Type of operation being recovered
            service_type: Service type involved in the operation
            context_data: Additional context for the operation
            success_callback: Callback for successful recovery
            failure_callback: Callback for failed recovery
            **recovery_config: Additional recovery configuration

        Returns:
            str: Operation ID for tracking
        """
        operation_kwargs = operation_kwargs or {}
        context_data = context_data or {}

        # Create recovery operation
        recovery_op = RecoveryOperation(
            recovery_type=recovery_type,
            failure_category=failure_category,
            priority=priority,
            operation_type=operation_type,
            service_type=service_type,
            operation_func=operation_func,
            operation_args=operation_args,
            operation_kwargs=operation_kwargs,
            context_data=context_data,
            success_callback=success_callback,
            failure_callback=failure_callback,
            **recovery_config,
        )

        # Calculate initial delay for delayed retry
        if recovery_type == RecoveryType.DELAYED_RETRY:
            delay = calculate_retry_delay(recovery_op)
            recovery_op.next_retry_at = datetime.utcnow() + timedelta(seconds=delay)

        # Add to appropriate queue
        queue = self.recovery_queues[priority]

        if len(queue) >= self.max_queue_size:
            logger.error(
                f"Recovery queue full for priority {priority}, dropping operation"
            )
            return recovery_op.operation_id

        queue.append(recovery_op)

        logger.info(
            f"Scheduled {recovery_type} recovery operation {recovery_op.operation_id} "
            f"for {service_type} with priority {priority}"
        )

        return recovery_op.operation_id

    async def _record_recovery_success(
        self,
        operation: RecoveryOperation,
        total_time: float,
        result: Any,
        consistency_passed: bool,
    ):
        """Record successful recovery operation"""
        # Update statistics
        self.recovery_stats[operation.recovery_type]["attempts"] += 1
        self.recovery_stats[operation.recovery_type]["successes"] += 1

        logger.info(
            f"Recovery operation {operation.operation_id} succeeded "
            f"after {operation.retry_count} attempts in {total_time:.3f}s"
        )

    async def _record_recovery_failure(
        self, operation: RecoveryOperation, total_time: float, error_msg: str
    ):
        """Record failed recovery operation"""
        # Update statistics
        self.recovery_stats[operation.recovery_type]["attempts"] += 1
        self.recovery_stats[operation.recovery_type]["failures"] += 1

        logger.error(
            f"Recovery operation {operation.operation_id} failed permanently "
            f"after {operation.retry_count} attempts: {error_msg}"
        )

    async def _perform_consistency_check(
        self, operation: RecoveryOperation, result: Any
    ) -> bool:
        """Perform consistency check on recovered data"""
        return perform_consistency_check(
            operation, result, self.consistency_check_sample_rate
        )

    def _calculate_retry_delay(self, operation: RecoveryOperation) -> float:
        """Calculate retry delay with exponential backoff and jitter"""
        return calculate_retry_delay(operation)

    async def schedule_background_sync(
        self,
        service_type: ServiceType,
        sync_type: str = "incremental_sync",
        source_keys: Optional[List[str]] = None,
        target_keys: Optional[List[str]] = None,
        data_items: Optional[List[Dict[str, Any]]] = None,
        priority: RecoveryPriority = RecoveryPriority.NORMAL,
        scheduled_at: Optional[datetime] = None,
    ) -> str:
        """Schedule a background synchronization job"""
        return await self.sync_manager.schedule_background_sync(
            service_type=service_type,
            sync_type=sync_type,
            source_keys=source_keys,
            target_keys=target_keys,
            data_items=data_items,
            priority=priority,
            scheduled_at=scheduled_at,
        )

    async def _perform_full_sync(self, job):
        """Execute full synchronization"""
        await self.sync_manager.execute_full_sync(job)

    async def _perform_incremental_sync(self, job):
        """Execute incremental synchronization"""
        await self.sync_manager.execute_incremental_sync(job)

    async def _perform_repair_sync(self, job):
        """Execute data repair synchronization"""
        await self.sync_manager.execute_data_repair_sync(job)

    def register_service_recovery_callback(
        self, service_type: ServiceType, callback: Callable
    ):
        """Register a callback for service recovery events"""
        self.service_recovery_callbacks[service_type].append(callback)
        logger.debug(f"Registered recovery callback for {service_type}")

    async def get_recovery_status(self) -> Dict[str, Any]:
        """Get comprehensive recovery system status"""
        queue_stats = {}
        for priority in RecoveryPriority:
            queue = self.recovery_queues[priority]
            queue_stats[priority.value] = {
                "length": len(queue),
                "oldest_operation": (
                    queue[0].created_at.isoformat() if queue else None
                ),
            }

        return {
            "enabled": self.enabled,
            "recovery_queues": queue_stats,
            "recovery_statistics": get_recovery_stats_summary(self.recovery_stats),
            "sync_jobs": self.sync_manager.get_sync_stats(),
            "dead_letter_queue": self.dead_letter_queue.get_stats(),
            "service_health": {
                service_type.value: health
                for service_type, health in self.last_service_health.items()
            },
            "consistency_check_enabled": self.consistency_check_enabled,
            "consistency_check_sample_rate": self.consistency_check_sample_rate,
        }

    async def get_dead_letter_items(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get items from the dead letter queue"""
        return await self.dead_letter_queue.get_items(limit)

    async def retry_dead_letter_item(self, operation_id: str) -> bool:
        """Retry a dead letter queue item"""
        items = await self.dead_letter_queue.get_items()

        for item in items:
            if item["operation_id"] == operation_id:
                # Remove from dead letter queue
                if await self.dead_letter_queue.remove_item(operation_id):
                    # Reschedule as recovery operation
                    op_data = item["operation_data"]

                    # Reset retry count
                    op_data["retry_count"] = 0
                    op_data["next_retry_at"] = None

                    # Create new recovery operation (simplified)
                    await self.schedule_recovery_operation(
                        operation_func=None,  # Would need to reconstruct
                        recovery_type=RecoveryType(op_data["recovery_type"]),
                        failure_category=FailureCategory(op_data["failure_category"]),
                        priority=RecoveryPriority(op_data["priority"]),
                        operation_type=OperationType(op_data["operation_type"]),
                        service_type=ServiceType(op_data["service_type"]),
                    )

                    logger.info(
                        f"Rescheduled dead letter item {operation_id} for retry"
                    )
                    return True

        return False

    async def shutdown(self):
        """Gracefully shutdown the error recovery system"""
        logger.info("Shutting down ErrorRecoverySystem...")

        self.enabled = False

        # Cancel background tasks
        tasks = [
            self.recovery_worker_task,
            self.sync_worker_task,
            self.health_monitor_task,
        ]

        for task in tasks:
            if task and not task.done():
                task.cancel()

        # Wait for tasks to complete
        await asyncio.sleep(0.5)

        # Process remaining critical operations
        critical_queue = self.recovery_queues[RecoveryPriority.CRITICAL]
        remaining_ops = min(len(critical_queue), 10)  # Process up to 10 critical ops

        for _ in range(remaining_ops):
            if critical_queue:
                operation = critical_queue.popleft()
                try:
                    await self._execute_recovery_operation(operation)
                except Exception as e:
                    logger.error(
                        f"Error processing final operation {operation.operation_id}: {e}"
                    )

        logger.info("ErrorRecoverySystem shutdown complete")
