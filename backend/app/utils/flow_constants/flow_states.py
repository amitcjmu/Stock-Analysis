"""
Flow state definitions and management utilities.
Provides standardized flow status, phases, and state transitions.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Set


class FlowStatus(str, Enum):
    """Standard flow status values."""

    PENDING = "pending"
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    RETRY = "retry"
    ROLLBACK = "rollback"
    ARCHIVED = "archived"


class FlowPhase(str, Enum):
    """Standard flow phases."""

    INITIALIZATION = "initialization"
    DATA_IMPORT = "data_import"
    DATA_VALIDATION = "data_validation"
    FIELD_MAPPING = "field_mapping"
    DATA_CLEANSING = "data_cleansing"
    ASSET_INVENTORY = "asset_inventory"
    DEPENDENCY_ANALYSIS = "dependency_analysis"
    TECH_DEBT_ANALYSIS = "tech_debt_analysis"
    ASSESSMENT = "assessment"
    PLANNING = "planning"
    EXECUTION = "execution"
    MODERNIZATION = "modernization"
    FINALIZATION = "finalization"
    CLEANUP = "cleanup"


class FlowType(str, Enum):
    """Types of flows in the system."""

    DISCOVERY = "discovery"
    ASSESSMENT = "assessment"
    PLANNING = "planning"
    EXECUTION = "execution"
    MODERNIZATION = "modernization"
    FINOPS = "finops"
    OBSERVABILITY = "observability"
    DECOMMISSION = "decommission"


class FlowPriority(str, Enum):
    """Flow priority levels."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"
    URGENT = "urgent"


class PhaseStatus(str, Enum):
    """Phase-specific status values."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"
    WAITING_FOR_INPUT = "waiting_for_input"
    WAITING_FOR_APPROVAL = "waiting_for_approval"


@dataclass
class FlowState:
    """Complete flow state information."""

    flow_id: str
    flow_type: FlowType
    status: FlowStatus
    current_phase: Optional[FlowPhase] = None
    phase_status: Optional[PhaseStatus] = None
    priority: FlowPriority = FlowPriority.NORMAL
    progress_percentage: float = 0.0
    error_count: int = 0
    retry_count: int = 0

    def is_active(self) -> bool:
        """Check if flow is currently active."""
        return self.status in {
            FlowStatus.INITIALIZING,
            FlowStatus.RUNNING,
            FlowStatus.WAITING,
            FlowStatus.RETRY,
        }

    def is_terminal(self) -> bool:
        """Check if flow is in a terminal state."""
        return self.status in {
            FlowStatus.COMPLETED,
            FlowStatus.FAILED,
            FlowStatus.CANCELLED,
            FlowStatus.ARCHIVED,
        }

    def is_error(self) -> bool:
        """Check if flow is in an error state."""
        return self.status in {
            FlowStatus.FAILED,
            FlowStatus.TIMEOUT,
            FlowStatus.ROLLBACK,
        }

    def can_retry(self) -> bool:
        """Check if flow can be retried."""
        return (
            self.status in {FlowStatus.FAILED, FlowStatus.TIMEOUT}
            and self.retry_count < 3
        )


# Flow status messages
FLOW_STATUS_MESSAGES: Dict[FlowStatus, str] = {
    FlowStatus.PENDING: "Flow is pending execution",
    FlowStatus.INITIALIZING: "Flow is being initialized",
    FlowStatus.RUNNING: "Flow is running",
    FlowStatus.PAUSED: "Flow is paused",
    FlowStatus.WAITING: "Flow is waiting for external input",
    FlowStatus.COMPLETED: "Flow completed successfully",
    FlowStatus.FAILED: "Flow failed to complete",
    FlowStatus.CANCELLED: "Flow was cancelled",
    FlowStatus.TIMEOUT: "Flow timed out",
    FlowStatus.RETRY: "Flow is being retried",
    FlowStatus.ROLLBACK: "Flow is being rolled back",
    FlowStatus.ARCHIVED: "Flow has been archived",
}

# Phase sequences for different flow types
PHASE_SEQUENCES: Dict[FlowType, List[FlowPhase]] = {
    FlowType.DISCOVERY: [
        FlowPhase.INITIALIZATION,
        FlowPhase.DATA_IMPORT,
        FlowPhase.DATA_VALIDATION,
        FlowPhase.FIELD_MAPPING,
        FlowPhase.DATA_CLEANSING,
        FlowPhase.ASSET_INVENTORY,
        FlowPhase.DEPENDENCY_ANALYSIS,
        FlowPhase.TECH_DEBT_ANALYSIS,
        FlowPhase.FINALIZATION,
    ],
    FlowType.ASSESSMENT: [
        FlowPhase.INITIALIZATION,
        FlowPhase.ASSET_INVENTORY,
        FlowPhase.ASSESSMENT,
        FlowPhase.TECH_DEBT_ANALYSIS,
        FlowPhase.FINALIZATION,
    ],
    FlowType.PLANNING: [
        FlowPhase.INITIALIZATION,
        FlowPhase.PLANNING,
        FlowPhase.FINALIZATION,
    ],
    FlowType.EXECUTION: [
        FlowPhase.INITIALIZATION,
        FlowPhase.EXECUTION,
        FlowPhase.FINALIZATION,
    ],
    FlowType.MODERNIZATION: [
        FlowPhase.INITIALIZATION,
        FlowPhase.MODERNIZATION,
        FlowPhase.FINALIZATION,
    ],
    FlowType.FINOPS: [
        FlowPhase.INITIALIZATION,
        FlowPhase.ASSESSMENT,
        FlowPhase.FINALIZATION,
    ],
    FlowType.OBSERVABILITY: [
        FlowPhase.INITIALIZATION,
        FlowPhase.ASSESSMENT,
        FlowPhase.FINALIZATION,
    ],
    FlowType.DECOMMISSION: [
        FlowPhase.INITIALIZATION,
        FlowPhase.PLANNING,
        FlowPhase.EXECUTION,
        FlowPhase.CLEANUP,
        FlowPhase.FINALIZATION,
    ],
}

# Valid state transitions
VALID_TRANSITIONS: Dict[FlowStatus, Set[FlowStatus]] = {
    FlowStatus.PENDING: {FlowStatus.INITIALIZING, FlowStatus.CANCELLED},
    FlowStatus.INITIALIZING: {
        FlowStatus.RUNNING,
        FlowStatus.FAILED,
        FlowStatus.CANCELLED,
    },
    FlowStatus.RUNNING: {
        FlowStatus.PAUSED,
        FlowStatus.WAITING,
        FlowStatus.COMPLETED,
        FlowStatus.FAILED,
        FlowStatus.TIMEOUT,
        FlowStatus.CANCELLED,
    },
    FlowStatus.PAUSED: {FlowStatus.RUNNING, FlowStatus.CANCELLED},
    FlowStatus.WAITING: {FlowStatus.RUNNING, FlowStatus.TIMEOUT, FlowStatus.CANCELLED},
    FlowStatus.COMPLETED: {FlowStatus.ARCHIVED},
    FlowStatus.FAILED: {FlowStatus.RETRY, FlowStatus.ROLLBACK, FlowStatus.ARCHIVED},
    FlowStatus.CANCELLED: {FlowStatus.ARCHIVED},
    FlowStatus.TIMEOUT: {FlowStatus.RETRY, FlowStatus.FAILED, FlowStatus.ARCHIVED},
    FlowStatus.RETRY: {FlowStatus.RUNNING, FlowStatus.FAILED},
    FlowStatus.ROLLBACK: {FlowStatus.FAILED, FlowStatus.ARCHIVED},
    FlowStatus.ARCHIVED: set(),  # Terminal state
}


# Helper functions
def get_flow_status_message(status: FlowStatus) -> str:
    """Get descriptive message for flow status."""
    return FLOW_STATUS_MESSAGES.get(status, "Unknown status")


def get_next_phase(
    flow_type: FlowType, current_phase: FlowPhase
) -> Optional[FlowPhase]:
    """Get the next phase in the flow sequence."""
    phases = PHASE_SEQUENCES.get(flow_type, [])

    try:
        current_index = phases.index(current_phase)
        if current_index < len(phases) - 1:
            return phases[current_index + 1]
    except ValueError:
        pass

    return None


def get_previous_phase(
    flow_type: FlowType, current_phase: FlowPhase
) -> Optional[FlowPhase]:
    """Get the previous phase in the flow sequence."""
    phases = PHASE_SEQUENCES.get(flow_type, [])

    try:
        current_index = phases.index(current_phase)
        if current_index > 0:
            return phases[current_index - 1]
    except ValueError:
        pass

    return None


def is_terminal_status(status: FlowStatus) -> bool:
    """Check if status is terminal (no further transitions)."""
    return status in {
        FlowStatus.COMPLETED,
        FlowStatus.FAILED,
        FlowStatus.CANCELLED,
        FlowStatus.ARCHIVED,
    }


def is_error_status(status: FlowStatus) -> bool:
    """Check if status indicates an error state."""
    return status in {FlowStatus.FAILED, FlowStatus.TIMEOUT, FlowStatus.ROLLBACK}


def is_active_status(status: FlowStatus) -> bool:
    """Check if status indicates an active flow."""
    return status in {
        FlowStatus.INITIALIZING,
        FlowStatus.RUNNING,
        FlowStatus.WAITING,
        FlowStatus.RETRY,
    }


def can_transition_to(current_status: FlowStatus, target_status: FlowStatus) -> bool:
    """Check if transition from current to target status is allowed."""
    allowed_transitions = VALID_TRANSITIONS.get(current_status, set())
    return target_status in allowed_transitions


def get_allowed_transitions(current_status: FlowStatus) -> Set[FlowStatus]:
    """Get all allowed transitions from current status."""
    return VALID_TRANSITIONS.get(current_status, set())


def get_phase_sequence(flow_type: FlowType) -> List[FlowPhase]:
    """Get the complete phase sequence for a flow type."""
    return PHASE_SEQUENCES.get(flow_type, [])


def calculate_progress_percentage(
    flow_type: FlowType, current_phase: FlowPhase, phase_progress: float = 0.0
) -> float:
    """Calculate overall progress percentage for a flow."""
    phases = PHASE_SEQUENCES.get(flow_type, [])

    if not phases:
        return 0.0

    try:
        current_index = phases.index(current_phase)

        # Calculate progress based on completed phases plus current phase progress
        completed_phases = current_index
        total_phases = len(phases)

        # Each phase represents an equal portion of the total progress
        phase_weight = 100.0 / total_phases

        # Progress = (completed phases * phase weight) + (current phase progress * phase weight)
        progress = (completed_phases * phase_weight) + (phase_progress * phase_weight)

        return min(100.0, max(0.0, progress))
    except ValueError:
        return 0.0


def get_flow_type_display_name(flow_type: FlowType) -> str:
    """Get display name for flow type."""
    display_names = {
        FlowType.DISCOVERY: "Discovery",
        FlowType.ASSESSMENT: "Assessment",
        FlowType.PLANNING: "Planning",
        FlowType.EXECUTION: "Execution",
        FlowType.MODERNIZATION: "Modernization",
        FlowType.FINOPS: "FinOps",
        FlowType.OBSERVABILITY: "Observability",
        FlowType.DECOMMISSION: "Decommission",
    }
    return display_names.get(flow_type, flow_type.value.title())


def get_phase_display_name(phase: FlowPhase) -> str:
    """Get display name for flow phase."""
    display_names = {
        FlowPhase.INITIALIZATION: "Initialization",
        FlowPhase.DATA_IMPORT: "Data Import",
        FlowPhase.DATA_VALIDATION: "Data Validation",
        FlowPhase.FIELD_MAPPING: "Field Mapping",
        FlowPhase.DATA_CLEANSING: "Data Cleansing",
        FlowPhase.ASSET_INVENTORY: "Asset Inventory",
        FlowPhase.DEPENDENCY_ANALYSIS: "Dependency Analysis",
        FlowPhase.TECH_DEBT_ANALYSIS: "Tech Debt Analysis",
        FlowPhase.ASSESSMENT: "Assessment",
        FlowPhase.PLANNING: "Planning",
        FlowPhase.EXECUTION: "Execution",
        FlowPhase.MODERNIZATION: "Modernization",
        FlowPhase.FINALIZATION: "Finalization",
        FlowPhase.CLEANUP: "Cleanup",
    }
    return display_names.get(phase, phase.value.title().replace("_", " "))
