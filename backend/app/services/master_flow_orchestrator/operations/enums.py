"""
Enums for Flow Operations

Common enumerations used across operation modules.
"""

from enum import Enum


class FlowOperationType(Enum):
    """Types of flow operations for audit logging"""
    CREATE = "create_flow"
    DELETE = "delete_flow"
    PAUSE = "pause_flow"
    RESUME = "resume_flow"
    EXECUTE_PHASE = "execute_phase"
    STATUS_CHECK = "status_check"
    LIST = "list_flows"