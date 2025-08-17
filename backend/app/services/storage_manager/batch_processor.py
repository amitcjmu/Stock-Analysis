"""
Storage Manager Batch Processor

Handles batch processing of storage operations with debouncing,
priority queuing, and efficient execution strategies.
"""

import asyncio
import time
from collections import defaultdict
from typing import List, TYPE_CHECKING

from app.core.logging import get_logger

from .base import BatchResult, OperationType, Priority, StorageOperation, StorageType
from .exceptions import StorageQueueFullError

if TYPE_CHECKING:
    from .storage_manager import StorageManager

logger = get_logger(__name__)


class BatchProcessor:
    """Handles batch processing of storage operations"""

    def __init__(self, storage_manager: "StorageManager"):
        self.storage_manager = storage_manager

    async def queue_operation(self, operation: StorageOperation):
        """Queue an operation for batched processing"""
        if not self.storage_manager.enabled:
            logger.warning("StorageManager is disabled, skipping operation")
            return

        priority = operation.priority

        async with self.storage_manager._queue_locks[priority]:
            # Check queue size limits
            current_queue_size = sum(
                len(queue) for queue in self.storage_manager.operation_queues.values()
            )
            if current_queue_size >= self.storage_manager.max_queue_size:
                raise StorageQueueFullError(
                    queue_type=f"{priority.value}_queue",
                    current_size=current_queue_size,
                    max_size=self.storage_manager.max_queue_size,
                    operation_id=operation.operation_id,
                )

            # Add to appropriate priority queue
            self.storage_manager.operation_queues[priority].append(operation)

            # Start or restart debounce timer for this priority
            await self._schedule_batch_processing(priority)

    async def _schedule_batch_processing(self, priority: Priority):
        """Schedule batch processing for a priority queue with debouncing"""
        # Cancel existing timer if running
        if (
            self.storage_manager.debounce_timers[priority]
            and not self.storage_manager.debounce_timers[priority].done()
        ):
            self.storage_manager.debounce_timers[priority].cancel()

        # Get debounce interval for this priority
        delay = (
            self.storage_manager.config.debounce_intervals[priority] / 1000.0
        )  # Convert to seconds

        # Schedule new batch processing
        if delay == 0:
            # Critical priority - process immediately
            self.storage_manager.debounce_timers[priority] = asyncio.create_task(
                self._process_batch(priority)
            )
        else:
            # Other priorities - debounce
            self.storage_manager.debounce_timers[priority] = asyncio.create_task(
                self._debounced_batch_processing(priority, delay)
            )

    async def _debounced_batch_processing(self, priority: Priority, delay: float):
        """Wait for debounce delay then process batch"""
        try:
            await asyncio.sleep(delay)
            await self._process_batch(priority)
        except asyncio.CancelledError:
            # Timer was cancelled, no processing needed
            pass
        except Exception as e:
            logger.error(f"Error in debounced batch processing for {priority}: {e}")

    async def _process_batch(self, priority: Priority):
        """Process a batch of operations for a given priority"""
        start_time = time.time()

        async with self.storage_manager._queue_locks[priority]:
            queue = self.storage_manager.operation_queues[priority]
            if not queue:
                return

            # Extract operations for this batch (up to MAX_BATCH_SIZE)
            batch_operations = []
            for _ in range(min(len(queue), self.storage_manager.config.max_batch_size)):
                if queue:
                    batch_operations.append(queue.popleft())

        if not batch_operations:
            return

        logger.debug(
            f"Processing batch of {len(batch_operations)} operations (priority: {priority})"
        )

        # Group operations by storage type for efficient processing
        operations_by_type = defaultdict(list)
        for operation in batch_operations:
            operations_by_type[operation.storage_type].append(operation)

        # Process each storage type
        batch_result = BatchResult(total_operations=len(batch_operations))

        for storage_type, ops in operations_by_type.items():
            try:
                type_result = await self._process_storage_type_batch(storage_type, ops)
                batch_result.successful_operations += type_result.successful_operations
                batch_result.failed_operations += type_result.failed_operations
                batch_result.errors.extend(type_result.errors)

            except Exception as e:
                logger.error(f"Error processing {storage_type} batch: {e}")
                batch_result.failed_operations += len(ops)
                for op in ops:
                    batch_result.add_error(
                        op.operation_id, str(e), "batch_processing_error"
                    )

        # Update statistics
        duration_ms = (time.time() - start_time) * 1000
        batch_result.duration_ms = duration_ms

        await self.storage_manager._update_batch_stats(
            batch_result, len(batch_operations)
        )

        # Execute callbacks for completed operations
        await self._execute_callbacks(batch_operations, batch_result)

        logger.debug(
            f"Batch completed - {len(batch_operations)} ops, "
            f"{batch_result.success_rate:.1f}% success, {duration_ms:.2f}ms"
        )

    async def _process_storage_type_batch(
        self, storage_type: StorageType, operations: List[StorageOperation]
    ) -> BatchResult:
        """Process a batch of operations for a specific storage type"""
        result = BatchResult(total_operations=len(operations))

        for operation in operations:
            try:
                success = await self._execute_operation(operation)
                if success:
                    result.successful_operations += 1
                else:
                    result.failed_operations += 1
                    result.add_error(
                        operation.operation_id, "Operation failed", "execution_failed"
                    )

            except Exception as e:
                result.failed_operations += 1
                result.add_error(operation.operation_id, str(e), type(e).__name__)

                # Implement retry logic for failed operations
                if operation.retry_count < operation.max_retries:
                    await self._schedule_retry(operation)

        return result

    async def _execute_operation(self, operation: StorageOperation) -> bool:
        """Execute a single storage operation"""
        try:
            backend = self.storage_manager._backends.get(operation.storage_type)
            if backend is None:
                logger.error(
                    f"No backend available for storage type: {operation.storage_type}"
                )
                return False

            if operation.operation_type == OperationType.SET:
                return await backend.set(operation.key, operation.value, operation.ttl)
            elif operation.operation_type == OperationType.DELETE:
                return await backend.delete(operation.key)
            elif operation.operation_type == OperationType.CLEAR:
                return await backend.clear()
            else:
                logger.error(f"Unsupported operation type: {operation.operation_type}")
                return False

        except Exception as e:
            logger.error(f"Error executing operation {operation.operation_id}: {e}")
            return False

    async def _schedule_retry(self, operation: StorageOperation):
        """Schedule a retry for a failed operation"""
        operation.retry_count += 1

        # Calculate exponential backoff delay
        delay = min(
            self.storage_manager.config.base_retry_delay
            * (self.storage_manager.config.retry_backoff_factor**operation.retry_count),
            self.storage_manager.config.max_retry_delay,
        )

        logger.info(
            f"Scheduling retry {operation.retry_count}/{operation.max_retries} "
            f"for operation {operation.operation_id} in {delay:.2f}s"
        )

        # Schedule retry
        asyncio.create_task(self._retry_operation(operation, delay))

    async def _retry_operation(self, operation: StorageOperation, delay: float):
        """Retry a failed operation after delay"""
        try:
            await asyncio.sleep(delay)
            await self.queue_operation(operation)
        except Exception as e:
            logger.error(f"Error retrying operation {operation.operation_id}: {e}")

    async def _execute_callbacks(
        self, operations: List[StorageOperation], result: BatchResult
    ):
        """Execute callbacks for completed operations"""
        for operation in operations:
            if operation.callback:
                try:
                    # Determine if this specific operation succeeded
                    operation_succeeded = not any(
                        error["operation_id"] == operation.operation_id
                        for error in result.errors
                    )

                    # Execute callback
                    if asyncio.iscoroutinefunction(operation.callback):
                        await operation.callback(
                            operation.operation_id, operation_succeeded
                        )
                    else:
                        operation.callback(operation.operation_id, operation_succeeded)

                except Exception as e:
                    logger.error(
                        f"Error executing callback for operation {operation.operation_id}: {e}"
                    )

    async def process_remaining_operations(self):
        """Process remaining operations during shutdown"""
        try:
            remaining_operations = sum(
                len(queue) for queue in self.storage_manager.operation_queues.values()
            )
            if remaining_operations > 0:
                logger.info(
                    f"Processing {remaining_operations} remaining operations..."
                )

                # Process each priority queue
                for priority in [
                    Priority.CRITICAL,
                    Priority.HIGH,
                    Priority.NORMAL,
                    Priority.LOW,
                ]:
                    if self.storage_manager.operation_queues[priority]:
                        await self._process_batch(priority)

                # Wait a bit for processing to complete
                await asyncio.sleep(0.5)

        except Exception as e:
            logger.error(f"Error during shutdown processing: {e}")

    async def cancel_all_timers(self):
        """Cancel all debounce timers"""
        for priority in Priority:
            if (
                self.storage_manager.debounce_timers[priority]
                and not self.storage_manager.debounce_timers[priority].done()
            ):
                self.storage_manager.debounce_timers[priority].cancel()
