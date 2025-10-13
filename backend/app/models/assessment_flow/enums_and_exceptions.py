"""
Assessment Flow Enums and Exceptions
Shared constants and exceptions for the assessment flow system.
"""

from enum import Enum

# Import canonical AssessmentPhase from assessment_flow_state to avoid circular imports
# This is safe because assessment_flow_state doesn't import from this file
from app.models.assessment_flow_state import AssessmentPhase

__all__ = [
    "AssessmentPhase",
    "AssessmentFlowStatus",
    "AssessmentStatus",
    "ArchitectureRequirementType",
    "ComponentType",
    "TechDebtSeverity",
    "AssessmentFlowError",
    "CrewExecutionError",
]


class AssessmentFlowStatus(str, Enum):
    """Assessment flow status states."""

    INITIALIZED = "initialized"
    PROCESSING = "processing"
    PAUSED_FOR_USER_INPUT = "paused_for_user_input"
    COMPLETED = "completed"
    ERROR = "error"


class AssessmentStatus(str, Enum):
    """Detailed status for individual assessment components."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    REQUIRES_INPUT = "requires_input"
    COMPLETED = "completed"
    FAILED = "failed"


class ArchitectureRequirementType(str, Enum):
    """Types of architecture requirements."""

    SECURITY = "security"
    PERFORMANCE = "performance"
    SCALABILITY = "scalability"
    RELIABILITY = "reliability"
    MAINTAINABILITY = "maintainability"
    OBSERVABILITY = "observability"


class ComponentType(str, Enum):
    """Types of application components."""

    DATABASE = "database"
    CACHE = "cache"
    MESSAGE_QUEUE = "message_queue"
    LOAD_BALANCER = "load_balancer"
    CDN = "cdn"
    STORAGE = "storage"
    COMPUTE = "compute"
    NETWORK = "network"
    SECURITY = "security"
    MONITORING = "monitoring"
    LOGGING = "logging"


class TechDebtSeverity(str, Enum):
    """Severity levels for technical debt."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AssessmentFlowError(Exception):
    """Base exception for assessment flow operations."""

    pass


class CrewExecutionError(Exception):
    """Exception for crew execution failures."""

    pass
