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

The service is modularized into:
- models: Core data structures and enums
- dlq: Dead letter queue management
- sync: Background synchronization jobs
- workers: Background worker tasks
- core: Main ErrorRecoverySystem orchestration
- utils: Utility functions and helpers

Architecture:
The ErrorRecoverySystem coordinates with the ServiceHealthManager and
FallbackOrchestrator to provide comprehensive error recovery capabilities
that maintain data consistency and service availability during failures.
"""

from typing import Optional

from .core import ErrorRecoverySystem
from .models import (
    FailureCategory,
    RecoveryOperation,
    RecoveryPriority,
    RecoveryResult,
    RecoveryType,
    SyncJob,
)

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


# Public API - maintain backward compatibility
__all__ = [
    "ErrorRecoverySystem",
    "RecoveryOperation",
    "RecoveryResult",
    "RecoveryType",
    "FailureCategory",
    "RecoveryPriority",
    "SyncJob",
    "get_error_recovery_system",
    "shutdown_error_recovery_system",
]
