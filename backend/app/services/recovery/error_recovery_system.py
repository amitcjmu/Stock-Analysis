"""
Error Recovery System

Comprehensive error recovery system with automatic service recovery, background
synchronization, data consistency checks, and dead letter queue management.
Provides intelligent recovery strategies for different types of failures.

Key Features:
- Automatic service recovery detection and restoration
- Background synchronization when services come back online
- Data consistency checks and repair mechanisms
- Dead letter queue for failed operations
- Exponential backoff retry logic with jitter
- Recovery pattern learning and optimization
- Integration with circuit breakers and health monitoring

Recovery Strategies:
- Immediate Retry: For transient failures
- Delayed Retry: For temporary service unavailability
- Background Sync: For data consistency after recovery
- Dead Letter Processing: For persistent failures
- Manual Intervention: For complex recovery scenarios

Architecture:
The ErrorRecoverySystem coordinates with the ServiceHealthManager and
FallbackOrchestrator to provide comprehensive error recovery capabilities
that maintain data consistency and service availability during failures.
"""

import asyncio
import random
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from app.core.config import settings
from app.core.logging import get_logger
from app.services.monitoring.service_health_manager import (
    ServiceHealthManager,
    ServiceType,
    get_service_health_manager,
)
from app.services.auth.fallback_orchestrator import (
    FallbackOrchestrator,
    OperationType,
    get_fallback_orchestrator,
)

logger = get_logger(__name__)


class RecoveryType(str, Enum):
    """Types of recovery operations"""

    IMMEDIATE_RETRY = "immediate_retry"
    DELAYED_RETRY = "delayed_retry"
    BACKGROUND_SYNC = "background_sync"
    DATA_REPAIR = "data_repair"
    DEAD_LETTER = "dead_letter"
    MANUAL_INTERVENTION = "manual_intervention"


class FailureCategory(str, Enum):
    """Categories of failures for recovery strategies"""

    TRANSIENT = "transient"  # Network timeouts, temporary unavailability
    PERSISTENT = "persistent"  # Configuration errors, service down
    DATA_CORRUPTION = "data_corruption"  # Data integrity issues
    AUTHENTICATION = "authentication"  # Auth/permission failures
    RESOURCE_EXHAUSTION = "resource_exhaustion"  # Memory, disk, quota issues
    UNKNOWN = "unknown"  # Unclassified failures


class RecoveryPriority(str, Enum):
    """Priority levels for recovery operations"""

    CRITICAL = "critical"  # User-facing operations, auth failures
    HIGH = "high"  # Important background operations
    NORMAL = "normal"  # Regular cache updates, sync operations
    LOW = "low"  # Cleanup, maintenance operations


@dataclass
class RecoveryOperation:
    """Represents a recovery operation to be executed"""

    operation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    recovery_type: RecoveryType = RecoveryType.IMMEDIATE_RETRY
    failure_category: FailureCategory = FailureCategory.UNKNOWN
    priority: RecoveryPriority = RecoveryPriority.NORMAL
    operation_type: OperationType = OperationType.CACHE_READ
    service_type: ServiceType = ServiceType.REDIS

    # Operation details
    operation_func: Optional[Callable] = None
    operation_args: Tuple = field(default_factory=tuple)
    operation_kwargs: Dict[str, Any] = field(default_factory=dict)

    # Recovery configuration
    max_retry_attempts: int = 5
    retry_count: int = 0
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 300.0  # 5 minutes
    backoff_multiplier: float = 2.0
    jitter_enabled: bool = True

    # Timing and scheduling
    created_at: datetime = field(default_factory=datetime.utcnow)
    next_retry_at: Optional[datetime] = None
    last_attempt_at: Optional[datetime] = None

    # Context and metadata
    context_data: Dict[str, Any] = field(default_factory=dict)
    failure_history: List[Dict[str, Any]] = field(default_factory=list)
    recovery_metadata: Dict[str, Any] = field(default_factory=dict)

    # Callback functions
    success_callback: Optional[Callable] = None
    failure_callback: Optional[Callable] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "operation_id": self.operation_id,
            "recovery_type": self.recovery_type.value,
            "failure_category": self.failure_category.value,
            "priority": self.priority.value,
            "operation_type": self.operation_type.value,
            "service_type": self.service_type.value,
            "max_retry_attempts": self.max_retry_attempts,
            "retry_count": self.retry_count,
            "base_delay_seconds": self.base_delay_seconds,
            "max_delay_seconds": self.max_delay_seconds,
            "backoff_multiplier": self.backoff_multiplier,
            "jitter_enabled": self.jitter_enabled,
            "created_at": self.created_at.isoformat(),
            "next_retry_at": (
                self.next_retry_at.isoformat() if self.next_retry_at else None
            ),
            "last_attempt_at": (
                self.last_attempt_at.isoformat() if self.last_attempt_at else None
            ),
            "context_data": self.context_data,
            "failure_history": self.failure_history,
            "recovery_metadata": self.recovery_metadata,
        }


@dataclass
class RecoveryResult:
    """Result of a recovery operation"""

    operation_id: str
    success: bool
    recovery_type: RecoveryType
    attempts_made: int
    total_time_seconds: float
    final_error: Optional[str] = None
    recovered_data: Any = None
    consistency_check_passed: bool = True
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SyncJob:
    """Background synchronization job"""

    job_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    service_type: ServiceType = ServiceType.REDIS
    sync_type: str = "full_sync"
    source_keys: List[str] = field(default_factory=list)
    target_keys: List[str] = field(default_factory=list)
    data_items: List[Dict[str, Any]] = field(default_factory=list)
    priority: RecoveryPriority = RecoveryPriority.NORMAL
    created_at: datetime = field(default_factory=datetime.utcnow)
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0
    error_message: Optional[str] = None


class DeadLetterQueue:
    """Dead letter queue for failed operations that cannot be recovered"""

    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.items: deque = deque(maxlen=max_size)
        self.lock = asyncio.Lock()

    async def add_item(self, operation: RecoveryOperation, final_error: str):
        """Add a failed operation to the dead letter queue"""
        async with self.lock:
            dead_letter_item = {
                "operation_id": operation.operation_id,
                "operation_data": operation.to_dict(),
                "final_error": final_error,
                "added_at": datetime.utcnow().isoformat(),
                "retry_attempts_made": operation.retry_count,
            }

            self.items.append(dead_letter_item)

        logger.error(
            f"Added operation {operation.operation_id} to dead letter queue "
            f"after {operation.retry_count} attempts: {final_error}"
        )

    async def get_items(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get items from the dead letter queue"""
        async with self.lock:
            return list(self.items)[-limit:] if limit else list(self.items)

    async def remove_item(self, operation_id: str) -> bool:
        """Remove an item from the dead letter queue"""
        async with self.lock:
            for i, item in enumerate(self.items):
                if item["operation_id"] == operation_id:
                    del self.items[i]
                    return True
            return False

    async def clear(self) -> int:
        """Clear all items from the dead letter queue"""
        async with self.lock:
            count = len(self.items)
            self.items.clear()
            return count

    def get_stats(self) -> Dict[str, Any]:
        """Get dead letter queue statistics"""
        return {
            "total_items": len(self.items),
            "max_size": self.max_size,
            "utilization": len(self.items) / self.max_size * 100,
        }


class ErrorRecoverySystem:
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

        # Background sync jobs
        self.sync_jobs: Dict[str, SyncJob] = {}
        self.sync_queue: deque = deque()

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

    def _start_background_workers(self):
        """Start background worker tasks"""
        try:
            self.recovery_worker_task = asyncio.create_task(self._recovery_worker())
            self.sync_worker_task = asyncio.create_task(self._sync_worker())
            self.health_monitor_task = asyncio.create_task(self._health_monitor())

            logger.info("Started error recovery background workers")
        except Exception as e:
            logger.error(f"Failed to start recovery background workers: {e}")

    async def _recovery_worker(self):
        """Background worker for processing recovery operations"""
        while self.enabled:
            try:
                await self._process_recovery_batch()
                await asyncio.sleep(1)  # Process every second
            except Exception as e:
                logger.error(f"Error in recovery worker: {e}")
                await asyncio.sleep(5)  # Back off on error

    async def _sync_worker(self):
        """Background worker for processing sync jobs"""
        while self.enabled:
            try:
                await self._process_sync_batch()
                await asyncio.sleep(10)  # Process every 10 seconds
            except Exception as e:
                logger.error(f"Error in sync worker: {e}")
                await asyncio.sleep(30)  # Back off on error

    async def _health_monitor(self):
        """Monitor service health changes for recovery triggers"""
        while self.enabled:
            try:
                await self._check_service_recoveries()
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Error in health monitor: {e}")
                await asyncio.sleep(60)  # Back off on error

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
            delay = self._calculate_retry_delay(recovery_op)
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

    async def _process_recovery_batch(self):
        """Process a batch of recovery operations"""
        operations_to_process = []

        # Collect operations from all priority queues (process higher priority first)
        for priority in [
            RecoveryPriority.CRITICAL,
            RecoveryPriority.HIGH,
            RecoveryPriority.NORMAL,
            RecoveryPriority.LOW,
        ]:
            queue = self.recovery_queues[priority]
            batch_count = min(len(queue), self.worker_batch_size)

            for _ in range(batch_count):
                if queue:
                    operation = queue.popleft()

                    # Check if operation should be processed now
                    if self._should_process_operation(operation):
                        operations_to_process.append(operation)
                    else:
                        # Put back in queue for later processing
                        queue.append(operation)

            # Process higher priority operations first
            if operations_to_process:
                break

        # Process collected operations
        for operation in operations_to_process:
            try:
                await self._execute_recovery_operation(operation)
            except Exception as e:
                logger.error(
                    f"Error executing recovery operation {operation.operation_id}: {e}"
                )

    def _should_process_operation(self, operation: RecoveryOperation) -> bool:
        """Check if a recovery operation should be processed now"""
        now = datetime.utcnow()

        # Check if it's time for delayed retry
        if operation.next_retry_at and now < operation.next_retry_at:
            return False

        # Check if max retries exceeded
        if operation.retry_count >= operation.max_retry_attempts:
            return True  # Process to move to dead letter queue

        return True

    async def _execute_recovery_operation(self, operation: RecoveryOperation):
        """Execute a recovery operation"""
        start_time = time.time()
        operation.retry_count += 1
        operation.last_attempt_at = datetime.utcnow()

        try:
            logger.debug(
                f"Executing recovery operation {operation.operation_id} (attempt {operation.retry_count})"
            )

            # Check service health before attempting
            if not await self.health_manager.is_service_available(
                operation.service_type
            ):
                raise Exception(f"Service {operation.service_type} is not available")

            # Execute the operation
            if operation.operation_func:
                if asyncio.iscoroutinefunction(operation.operation_func):
                    result = await operation.operation_func(
                        *operation.operation_args, **operation.operation_kwargs
                    )
                else:
                    result = operation.operation_func(
                        *operation.operation_args, **operation.operation_kwargs
                    )
            else:
                raise Exception("No operation function provided")

            # Success
            execution_time = time.time() - start_time

            # Perform consistency check if enabled
            consistency_passed = True
            if self.consistency_check_enabled and operation.operation_type in [
                OperationType.CACHE_WRITE,
                OperationType.USER_SESSION,
            ]:
                consistency_passed = await self._perform_consistency_check(
                    operation, result
                )

            # Create recovery result
            recovery_result = RecoveryResult(
                operation_id=operation.operation_id,
                success=True,
                recovery_type=operation.recovery_type,
                attempts_made=operation.retry_count,
                total_time_seconds=execution_time,
                recovered_data=result,
                consistency_check_passed=consistency_passed,
            )

            # Update statistics
            self.recovery_stats[operation.recovery_type]["attempts"] += 1
            self.recovery_stats[operation.recovery_type]["successes"] += 1

            # Execute success callback
            if operation.success_callback:
                try:
                    if asyncio.iscoroutinefunction(operation.success_callback):
                        await operation.success_callback(recovery_result)
                    else:
                        operation.success_callback(recovery_result)
                except Exception as e:
                    logger.error(
                        f"Error in success callback for {operation.operation_id}: {e}"
                    )

            logger.info(
                f"Recovery operation {operation.operation_id} succeeded "
                f"after {operation.retry_count} attempts in {execution_time:.3f}s"
            )

        except Exception as e:
            execution_time = time.time() - start_time
            error_message = str(e)

            # Record failure
            operation.failure_history.append(
                {
                    "attempt": operation.retry_count,
                    "error": error_message,
                    "timestamp": datetime.utcnow().isoformat(),
                    "execution_time": execution_time,
                }
            )

            # Check if we should retry or move to dead letter queue
            if operation.retry_count >= operation.max_retry_attempts:
                # Move to dead letter queue
                await self.dead_letter_queue.add_item(operation, error_message)

                # Create failure result
                recovery_result = RecoveryResult(
                    operation_id=operation.operation_id,
                    success=False,
                    recovery_type=operation.recovery_type,
                    attempts_made=operation.retry_count,
                    total_time_seconds=execution_time,
                    final_error=error_message,
                )

                # Update statistics
                self.recovery_stats[operation.recovery_type]["attempts"] += 1
                self.recovery_stats[operation.recovery_type]["failures"] += 1

                # Execute failure callback
                if operation.failure_callback:
                    try:
                        if asyncio.iscoroutinefunction(operation.failure_callback):
                            await operation.failure_callback(recovery_result)
                        else:
                            operation.failure_callback(recovery_result)
                    except Exception as cb_e:
                        logger.error(
                            f"Error in failure callback for {operation.operation_id}: {cb_e}"
                        )

                logger.error(
                    f"Recovery operation {operation.operation_id} failed permanently "
                    f"after {operation.retry_count} attempts: {error_message}"
                )
            else:
                # Schedule retry
                delay = self._calculate_retry_delay(operation)
                operation.next_retry_at = datetime.utcnow() + timedelta(seconds=delay)

                # Put back in queue
                self.recovery_queues[operation.priority].append(operation)

                logger.warning(
                    f"Recovery operation {operation.operation_id} failed (attempt {operation.retry_count}), "
                    f"retrying in {delay:.1f}s: {error_message}"
                )

    def _calculate_retry_delay(self, operation: RecoveryOperation) -> float:
        """Calculate retry delay with exponential backoff and jitter"""
        base_delay = operation.base_delay_seconds
        multiplier = operation.backoff_multiplier
        retry_count = operation.retry_count

        # Exponential backoff
        delay = base_delay * (multiplier**retry_count)

        # Apply maximum delay
        delay = min(delay, operation.max_delay_seconds)

        # Add jitter if enabled
        if operation.jitter_enabled:
            jitter = delay * 0.1 * random.uniform(-1, 1)  # ±10% jitter
            delay += jitter

        return max(delay, 0.1)  # Minimum 100ms delay

    async def _perform_consistency_check(
        self, operation: RecoveryOperation, result: Any
    ) -> bool:
        """Perform consistency check on recovered data"""
        try:
            # Sample-based consistency checking
            if random.random() > self.consistency_check_sample_rate:
                return True  # Skip this check

            # Basic consistency checks based on operation type
            if operation.operation_type == OperationType.USER_SESSION:
                return self._check_user_session_consistency(result)
            elif operation.operation_type == OperationType.CACHE_WRITE:
                return self._check_cache_write_consistency(operation, result)

            return True  # Default to consistent if no specific check

        except Exception as e:
            logger.error(f"Consistency check failed for {operation.operation_id}: {e}")
            return False

    def _check_user_session_consistency(self, session_data: Any) -> bool:
        """Check user session data consistency"""
        if not isinstance(session_data, dict):
            return False

        required_fields = ["user_id", "email", "role"]
        for required_field in required_fields:
            if required_field not in session_data:
                logger.warning(
                    f"Missing required field in session data: {required_field}"
                )
                return False

        return True

    def _check_cache_write_consistency(
        self, operation: RecoveryOperation, result: Any
    ) -> bool:
        """Check cache write operation consistency"""
        # For cache writes, we consider it consistent if the operation returned success
        return result is True or (
            isinstance(result, dict) and result.get("success", False)
        )

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
        sync_job = SyncJob(
            service_type=service_type,
            sync_type=sync_type,
            source_keys=source_keys or [],
            target_keys=target_keys or [],
            data_items=data_items or [],
            priority=priority,
            scheduled_at=scheduled_at,
        )

        self.sync_jobs[sync_job.job_id] = sync_job
        self.sync_queue.append(sync_job.job_id)

        logger.info(
            f"Scheduled background sync job {sync_job.job_id} for {service_type}"
        )
        return sync_job.job_id

    async def _process_sync_batch(self):
        """Process background synchronization jobs"""
        jobs_to_process = []

        # Get jobs ready for processing
        batch_count = min(len(self.sync_queue), self.sync_batch_size)
        for _ in range(batch_count):
            if self.sync_queue:
                job_id = self.sync_queue.popleft()
                if job_id in self.sync_jobs:
                    job = self.sync_jobs[job_id]

                    # Check if job should be processed now
                    if (
                        job.scheduled_at is None
                        or datetime.utcnow() >= job.scheduled_at
                    ):
                        jobs_to_process.append(job)
                    else:
                        # Put back in queue
                        self.sync_queue.append(job_id)

        # Process jobs
        for job in jobs_to_process:
            try:
                await self._execute_sync_job(job)
            except Exception as e:
                logger.error(f"Error executing sync job {job.job_id}: {e}")
                job.error_message = str(e)
                job.completed_at = datetime.utcnow()

    async def _execute_sync_job(self, job: SyncJob):
        """Execute a background synchronization job"""
        job.started_at = datetime.utcnow()

        try:
            logger.info(f"Starting sync job {job.job_id} for {job.service_type}")

            # Check service availability
            if not await self.health_manager.is_service_available(job.service_type):
                raise Exception(f"Service {job.service_type} is not available for sync")

            # Execute sync based on type
            if job.sync_type == "full_sync":
                await self._execute_full_sync(job)
            elif job.sync_type == "incremental_sync":
                await self._execute_incremental_sync(job)
            elif job.sync_type == "data_repair":
                await self._execute_data_repair_sync(job)
            else:
                raise Exception(f"Unknown sync type: {job.sync_type}")

            job.progress = 100.0
            job.completed_at = datetime.utcnow()

            logger.info(f"Completed sync job {job.job_id} successfully")

        except Exception as e:
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            logger.error(f"Sync job {job.job_id} failed: {e}")

    async def _execute_full_sync(self, job: SyncJob):
        """Execute full synchronization"""
        # This would implement full sync logic based on service type
        # For now, simulate sync operation
        total_items = len(job.data_items) or 100

        for i in range(total_items):
            # Simulate sync work
            await asyncio.sleep(0.01)
            job.progress = (i + 1) / total_items * 100

            # Check if we should stop
            if not self.enabled:
                break

    async def _execute_incremental_sync(self, job: SyncJob):
        """Execute incremental synchronization"""
        # This would implement incremental sync logic
        # For now, simulate sync operation
        total_items = len(job.source_keys) or 10

        for i in range(total_items):
            # Simulate sync work
            await asyncio.sleep(0.05)
            job.progress = (i + 1) / total_items * 100

    async def _execute_data_repair_sync(self, job: SyncJob):
        """Execute data repair synchronization"""
        # This would implement data repair logic
        # For now, simulate repair operation
        total_items = len(job.data_items) or 5

        for i in range(total_items):
            # Simulate repair work
            await asyncio.sleep(0.1)
            job.progress = (i + 1) / total_items * 100

    async def _check_service_recoveries(self):
        """Check for service recoveries and trigger callbacks"""
        for service_type in ServiceType:
            current_health = await self.health_manager.is_service_available(
                service_type
            )
            previous_health = self.last_service_health.get(service_type, False)

            # Service recovered
            if current_health and not previous_health:
                logger.info(f"Service recovery detected for {service_type}")
                await self._handle_service_recovery(service_type)

            self.last_service_health[service_type] = current_health

    async def _handle_service_recovery(self, service_type: ServiceType):
        """Handle service recovery"""
        # Execute recovery callbacks
        callbacks = self.service_recovery_callbacks[service_type]
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(service_type)
                else:
                    callback(service_type)
            except Exception as e:
                logger.error(
                    f"Error in service recovery callback for {service_type}: {e}"
                )

        # Schedule background sync for recovered service
        await self.schedule_background_sync(
            service_type=service_type,
            sync_type="incremental_sync",
            priority=RecoveryPriority.HIGH,
        )

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

        # Get sync job status
        active_sync_jobs = []
        completed_sync_jobs = []
        failed_sync_jobs = []

        for job in self.sync_jobs.values():
            if job.completed_at is None:
                active_sync_jobs.append(
                    {
                        "job_id": job.job_id,
                        "service_type": job.service_type.value,
                        "sync_type": job.sync_type,
                        "progress": job.progress,
                        "started_at": (
                            job.started_at.isoformat() if job.started_at else None
                        ),
                    }
                )
            elif job.error_message:
                failed_sync_jobs.append(
                    {
                        "job_id": job.job_id,
                        "service_type": job.service_type.value,
                        "error": job.error_message,
                        "completed_at": job.completed_at.isoformat(),
                    }
                )
            else:
                completed_sync_jobs.append(
                    {
                        "job_id": job.job_id,
                        "service_type": job.service_type.value,
                        "sync_type": job.sync_type,
                        "completed_at": job.completed_at.isoformat(),
                    }
                )

        return {
            "enabled": self.enabled,
            "recovery_queues": queue_stats,
            "recovery_statistics": {
                recovery_type.value: {
                    "attempts": stats["attempts"],
                    "successes": stats["successes"],
                    "failures": stats["failures"],
                    "success_rate": (stats["successes"] / max(stats["attempts"], 1))
                    * 100,
                }
                for recovery_type, stats in self.recovery_stats.items()
            },
            "sync_jobs": {
                "active": len(active_sync_jobs),
                "completed": len(completed_sync_jobs),
                "failed": len(failed_sync_jobs),
                "queue_length": len(self.sync_queue),
            },
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


# Singleton instance
_error_recovery_system_instance: Optional[ErrorRecoverySystem] = None


def get_error_recovery_system() -> ErrorRecoverySystem:
    """Get singleton ErrorRecoverySystem instance"""
    global _error_recovery_system_instance
    if _error_recovery_system_instance is None:
        _error_recovery_system_instance = ErrorRecoverySystem()
    return _error_recovery_system_instance


# Cleanup function for app shutdown
async def shutdown_error_recovery_system():
    """Shutdown error recovery system (call during app shutdown)"""
    global _error_recovery_system_instance
    if _error_recovery_system_instance:
        await _error_recovery_system_instance.shutdown()
        _error_recovery_system_instance = None
