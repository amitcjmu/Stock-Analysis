"""
Assessment Flow Enums and Exceptions
Shared constants and exceptions for the assessment flow system.
"""

from enum import Enum


class AssessmentFlowStatus(str, Enum):
    """Assessment flow status states."""

    INITIALIZED = "initialized"
    PROCESSING = "processing"
    PAUSED_FOR_USER_INPUT = "paused_for_user_input"
    COMPLETED = "completed"
    ERROR = "error"


class AssessmentPhase(str, Enum):
    """Assessment flow phases."""

    INITIALIZATION = "initialization"
    ARCHITECTURE_MINIMUMS = "architecture_minimums"
    TECH_DEBT_ANALYSIS = "tech_debt_analysis"
    COMPONENT_SIXR_STRATEGIES = "component_sixr_strategies"
    APP_ON_PAGE_GENERATION = "app_on_page_generation"
    FINAL_REPORT_GENERATION = "final_report_generation"
    COMPLETED = "completed"


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
