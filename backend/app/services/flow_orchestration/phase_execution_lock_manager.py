"""
Phase Execution Lock Manager

Prevents duplicate concurrent execution of assessment phases using AsyncIO locks.
Implements 5-minute timeout protection and thread-safe lock management.

CRITICAL: This addresses Issue #999 where rapid resume calls trigger duplicate
agent executions, causing wasted resources and potential state corruption.

Architecture:
- Singleton pattern for centralized lock management
- AsyncIO locks for async/await compatibility
- Per-(flow_id, phase) lock granularity
- Automatic timeout cleanup (5 minutes)
- Thread-safe operations

Usage:
    from app.services.flow_orchestration.phase_execution_lock_manager import (
        phase_lock_manager
    )

    # In API endpoint (before queueing background task):
    if not await phase_lock_manager.try_acquire_lock(flow_id, phase):
        logger.info(f"Phase {phase} already executing, skipping")
        return existing_status

    # In background task (wrap execution):
    try:
        result = await execute_phase()
    finally:
        phase_lock_manager.release_lock(flow_id, phase)
"""

import logging
from asyncio import Lock
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Awaitable, Callable, Dict, Tuple

logger = logging.getLogger(__name__)


class PhaseExecutionLockManager:
    """
    Singleton manager for preventing duplicate concurrent phase executions.

    Provides thread-safe lock management with timeout protection to prevent
    resource waste from rapid duplicate API calls triggering multiple agent
    executions for the same (flow_id, phase) combination.

    Features:
    - Per-(flow_id, phase) lock granularity
    - 5-minute timeout automatic cleanup
    - Thread-safe singleton pattern
    - Structured logging for observability

    Thread Safety:
    - Uses defaultdict with Lock values (thread-safe)
    - AsyncIO Lock objects are inherently async-safe
    - Singleton pattern ensures single instance per process
    """

    _instance: "PhaseExecutionLockManager | None" = None
    _locks: Dict[Tuple[str, str], Lock] = defaultdict(Lock)
    _lock_timestamps: Dict[Tuple[str, str], datetime] = {}
    _TIMEOUT_MINUTES = 5

    def __new__(cls) -> "PhaseExecutionLockManager":
        """Enforce singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            logger.info("✅ PhaseExecutionLockManager singleton initialized")
        return cls._instance

    async def try_acquire_lock(self, flow_id: str, phase: str) -> bool:
        """
        Try to acquire execution lock for (flow_id, phase).

        Returns True if lock was successfully acquired (caller can proceed).
        Returns False if lock is already held (duplicate execution attempt).

        Automatically handles timeout cleanup if previous execution exceeded
        5 minutes without releasing the lock (safeguard against crashes).

        Args:
            flow_id: Assessment flow identifier
            phase: Assessment phase name (e.g., "readiness", "architecture")

        Returns:
            True if lock acquired successfully, False if already locked

        Thread Safety:
            AsyncIO locks are async-safe. This method is safe for concurrent
            calls from multiple background tasks.
        """
        lock_key = (flow_id, phase)
        lock = self._locks[lock_key]

        # Check for timeout and force cleanup if needed
        if lock_key in self._lock_timestamps:
            elapsed = datetime.utcnow() - self._lock_timestamps[lock_key]
            if elapsed > timedelta(minutes=self._TIMEOUT_MINUTES):
                logger.warning(
                    f"⏱️ Lock timeout for {flow_id}:{phase} "
                    f"(held for {elapsed.total_seconds():.1f}s > "
                    f"{self._TIMEOUT_MINUTES * 60}s), forcing release"
                )
                if lock.locked():
                    lock.release()
                del self._lock_timestamps[lock_key]

        # Try to acquire lock (non-blocking check)
        if lock.locked():
            logger.warning(
                f"🔒 Phase {phase} already executing for flow {flow_id}, "
                "skipping duplicate execution attempt"
            )
            return False

        # Acquire lock and record timestamp
        await lock.acquire()
        self._lock_timestamps[lock_key] = datetime.utcnow()
        logger.info(f"✅ Acquired execution lock for {flow_id}:{phase}")
        return True

    def release_lock(self, flow_id: str, phase: str) -> None:
        """
        Release execution lock for (flow_id, phase).

        Should be called in a finally block to ensure lock is always released
        even if execution raises an exception.

        Args:
            flow_id: Assessment flow identifier
            phase: Assessment phase name

        Thread Safety:
            Safe to call even if lock was never acquired (no-op).
        """
        lock_key = (flow_id, phase)

        # Remove timestamp tracking
        if lock_key in self._lock_timestamps:
            elapsed = datetime.utcnow() - self._lock_timestamps[lock_key]
            del self._lock_timestamps[lock_key]
            logger.info(
                f"🔓 Released execution lock for {flow_id}:{phase} "
                f"(held for {elapsed.total_seconds():.1f}s)"
            )
        else:
            logger.debug(
                f"Release called for {flow_id}:{phase} without timestamp "
                "(lock may not have been acquired)"
            )

        # Release the actual lock
        lock = self._locks[lock_key]
        if lock.locked():
            lock.release()
        else:
            logger.debug(
                f"Lock for {flow_id}:{phase} was not locked during release attempt"
            )

    async def execute_with_lock(
        self,
        flow_id: str,
        phase: str,
        executor_func: Callable[[], Awaitable[Any]],
    ) -> Dict[str, Any]:
        """
        Execute a function with automatic lock acquisition and release.

        Convenience method that combines try_acquire_lock, execution, and
        release_lock into a single operation with proper exception handling.

        Args:
            flow_id: Assessment flow identifier
            phase: Assessment phase name
            executor_func: Async function to execute with lock protection

        Returns:
            Result from executor_func, or error dict if lock already held

        Example:
            result = await phase_lock_manager.execute_with_lock(
                flow_id,
                "readiness",
                lambda: execute_readiness_phase(flow_id)
            )
        """
        if not await self.try_acquire_lock(flow_id, phase):
            return {
                "status": "already_running",
                "message": f"Phase {phase} already executing for flow {flow_id}",
                "flow_id": flow_id,
                "phase": phase,
            }

        try:
            logger.info(f"🚀 Executing {phase} for {flow_id} with lock protection")
            result = await executor_func()
            logger.info(f"✅ Completed {phase} for {flow_id}")
            return result
        except Exception as e:
            logger.error(
                f"❌ Error executing {phase} for {flow_id}: {e}", exc_info=True
            )
            raise
        finally:
            self.release_lock(flow_id, phase)


# Singleton instance for global use
phase_lock_manager = PhaseExecutionLockManager()
