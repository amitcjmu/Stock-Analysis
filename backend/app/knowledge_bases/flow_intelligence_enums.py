"""
Flow Intelligence Knowledge Base - Enums
Enumeration types for flow processing
"""

from enum import Enum


class FlowType(Enum):
    DISCOVERY = "discovery"
    ASSESSMENT = "assessment"
    PLANNING = "planning"
    EXECUTION = "execution"
    DECOMMISSION = "decommission"
    FINOPS = "finops"
    MODERNIZE = "modernize"


class PhaseStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class ActionType(Enum):
    USER_ACTION = "user_action"  # User needs to do something
    SYSTEM_ACTION = "system_action"  # System needs to process something
    NAVIGATION = "navigation"  # Simple navigation to view results
