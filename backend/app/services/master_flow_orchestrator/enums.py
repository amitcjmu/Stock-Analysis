"""
Enumerations for Master Flow Orchestrator
"""

from enum import Enum


class FlowOperationType(Enum):
    """Flow operation types for audit logging"""

    CREATE = "create"
    EXECUTE = "execute"
    PAUSE = "pause"
    RESUME = "resume"
    DELETE = "delete"
    STATUS_CHECK = "status_check"
    LIST = "list"
