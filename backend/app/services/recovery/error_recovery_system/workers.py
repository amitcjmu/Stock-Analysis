"""
Background worker tasks for error recovery system.

Manages recovery processing, sync jobs, and health monitoring workers.
"""

import asyncio
import time
from datetime import datetime, timedelta

# Remove unused List import - not used in this module

from app.core.logging import get_logger

from .models import RecoveryOperation, RecoveryPriority, RecoveryType
from .utils import calculate_retry_delay

logger = get_logger(__name__)


class RecoveryWorkerMixin:
    """Mixin for recovery worker functionality"""

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

    async def _execute_recovery_operation(
        self, operation: RecoveryOperation
    ):  # noqa: C901
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

                # Perform consistency check if enabled
                consistency_passed = True
                if self.consistency_check_enabled:
                    consistency_passed = await self._perform_consistency_check(
                        operation, result
                    )

                # Record success
                total_time = time.time() - start_time
                await self._record_recovery_success(
                    operation, total_time, result, consistency_passed
                )

                # Call success callback
                if operation.success_callback:
                    try:
                        if asyncio.iscoroutinefunction(operation.success_callback):
                            await operation.success_callback(result)
                        else:
                            operation.success_callback(result)
                    except Exception as e:
                        logger.warning(f"Error in success callback: {e}")

                logger.info(
                    f"Recovery operation {operation.operation_id} succeeded after {operation.retry_count} attempts"
                )

            else:
                raise Exception("No operation function provided")

        except Exception as e:
            error_msg = str(e)
            operation.failure_history.append(
                {
                    "attempt": operation.retry_count,
                    "timestamp": datetime.utcnow().isoformat(),
                    "error": error_msg,
                }
            )

            logger.warning(
                f"Recovery operation {operation.operation_id} failed (attempt {operation.retry_count}): {error_msg}"
            )

            # Check if we should retry or give up
            if operation.retry_count >= operation.max_retry_attempts:
                # Max retries exceeded, send to dead letter queue
                await self.dead_letter_queue.add_item(operation, error_msg)

                total_time = time.time() - start_time
                await self._record_recovery_failure(operation, total_time, error_msg)

                # Call failure callback
                if operation.failure_callback:
                    try:
                        if asyncio.iscoroutinefunction(operation.failure_callback):
                            await operation.failure_callback(error_msg)
                        else:
                            operation.failure_callback(error_msg)
                    except Exception as callback_error:
                        logger.warning(f"Error in failure callback: {callback_error}")

            else:
                # Schedule for retry
                if operation.recovery_type == RecoveryType.DELAYED_RETRY:
                    delay = calculate_retry_delay(operation)
                    operation.next_retry_at = datetime.utcnow() + timedelta(
                        seconds=delay
                    )

                # Put back in queue
                self.recovery_queues[operation.priority].append(operation)

    async def _process_sync_batch(self):
        """Process a batch of sync jobs"""
        jobs_to_process = []
        # Get sync jobs from sync manager
        sync_jobs = self.sync_manager.get_pending_jobs()
        sync_queue_size = min(len(sync_jobs), self.sync_batch_size)

        for i in range(sync_queue_size):
            if i < len(sync_jobs):
                job = sync_jobs[i]
                if self._should_process_sync_job(job):
                    jobs_to_process.append(job)
                    # Remove from sync manager pending jobs
                    self.sync_manager.mark_job_processing(job.job_id)
                # Note: Jobs that shouldn't be processed yet remain in pending state

        # Process sync jobs
        for job in jobs_to_process:
            try:
                await self._execute_sync_job(job)
            except Exception as e:
                logger.error(f"Error executing sync job {job.job_id}: {e}")

    def _should_process_sync_job(self, job) -> bool:
        """Check if a sync job should be processed now"""
        if job.scheduled_at and datetime.utcnow() < job.scheduled_at:
            return False
        return True

    async def _execute_sync_job(self, job):
        """Execute a background sync job"""
        job.started_at = datetime.utcnow()
        logger.info(f"Starting sync job {job.job_id} for {job.service_type}")

        try:
            # Check if target service is available
            if not await self.health_manager.is_service_available(job.service_type):
                raise Exception(f"Target service {job.service_type} not available")

            # Perform the synchronization based on job type
            if job.sync_type == "full_sync":
                await self._perform_full_sync(job)
            elif job.sync_type == "incremental_sync":
                await self._perform_incremental_sync(job)
            elif job.sync_type == "repair_sync":
                await self._perform_repair_sync(job)
            else:
                logger.warning(f"Unknown sync type: {job.sync_type}")

            job.completed_at = datetime.utcnow()
            job.progress = 100.0
            logger.info(f"Sync job {job.job_id} completed successfully")

        except Exception as e:
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            logger.error(f"Sync job {job.job_id} failed: {e}")

        # Remove from active jobs in sync manager
        self.sync_manager.complete_job(job.job_id)

    async def _check_service_recoveries(self):
        """Check for service recoveries and trigger sync operations"""
        for service_type, callbacks in self.service_recovery_callbacks.items():
            current_health = await self.health_manager.is_service_available(
                service_type
            )
            previous_health = self.last_service_health.get(service_type, False)

            # Service has recovered (was down, now up)
            if current_health and not previous_health:
                logger.info(
                    f"Service {service_type} has recovered, triggering callbacks"
                )

                # Execute recovery callbacks
                for callback in callbacks:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback()
                        else:
                            callback()
                    except Exception as e:
                        logger.error(f"Error in service recovery callback: {e}")

            self.last_service_health[service_type] = current_health
