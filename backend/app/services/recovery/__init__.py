"""
Recovery Services

This package provides comprehensive error recovery capabilities including automatic
service recovery, background synchronization, data consistency checks, and dead
letter queue management for failed operations.
"""

from .error_recovery_system import ErrorRecoverySystem, get_error_recovery_system

__all__ = [
    "ErrorRecoverySystem",
    "get_error_recovery_system",
]
