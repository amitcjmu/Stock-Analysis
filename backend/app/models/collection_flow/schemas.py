"""
Collection Flow Schemas and State Management
Contains enums, Pydantic-like state classes, and in-memory data structures.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional


class AutomationTier(str, Enum):
    """Automation tier levels"""

    TIER_1 = "tier_1"  # Manual/Template-based
    TIER_2 = "tier_2"  # Script-Assisted
    TIER_3 = "tier_3"  # API-Integrated
    TIER_4 = "tier_4"  # Fully Automated


class CollectionFlowStatus(str, Enum):
    """Collection Flow status values - lifecycle states only per ADR-012"""

    INITIALIZED = "initialized"
    RUNNING = "running"  # Active execution
    PAUSED = "paused"  # Waiting for user input
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CollectionPhase(str, Enum):
    """Collection flow phases"""

    INITIALIZATION = "initialization"
    ASSET_SELECTION = (
        "asset_selection"  # Replaces platform_detection and automated_collection
    )
    GAP_ANALYSIS = "gap_analysis"
    QUESTIONNAIRE_GENERATION = "questionnaire_generation"
    MANUAL_COLLECTION = "manual_collection"
    DATA_VALIDATION = "data_validation"
    FINALIZATION = "finalization"


class CollectionStatus(str, Enum):
    """Collection flow status for in-memory state management"""

    INITIALIZING = "initializing"
    SELECTING_ASSETS = (
        "selecting_assets"  # Replaces detecting_platforms and collecting_data
    )
    ANALYZING_GAPS = "analyzing_gaps"
    GENERATING_QUESTIONNAIRES = "generating_questionnaires"
    MANUAL_COLLECTION = "manual_collection"
    VALIDATING_DATA = "validating_data"
    COMPLETED = "completed"
    FAILED = "failed"
    ERROR = "error"


class PlatformType(str, Enum):
    """Supported platform types for collection"""

    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    ON_PREMISE = "on_premise"
    KUBERNETES = "kubernetes"
    VMWARE = "vmware"
    OPENSHIFT = "openshift"
    CUSTOM = "custom"


class DataDomain(str, Enum):
    """Data domains for collection"""

    INFRASTRUCTURE = "infrastructure"
    APPLICATION = "application"
    DATABASE = "database"
    NETWORK = "network"
    SECURITY = "security"
    COMPLIANCE = "compliance"
    PERFORMANCE = "performance"
    COST = "cost"


class CollectionFlowState:
    """In-memory state model for collection flow execution"""

    def __init__(
        self,
        flow_id: str,
        client_account_id: str,
        engagement_id: str,
        user_id: Optional[str] = None,
        discovery_flow_id: Optional[str] = None,
        automation_tier: AutomationTier = AutomationTier.TIER_1,
        current_phase: CollectionPhase = CollectionPhase.INITIALIZATION,
        next_phase: CollectionPhase = None,
        status: CollectionStatus = CollectionStatus.INITIALIZING,
        progress: float = 0.0,
        created_at: datetime = None,
        updated_at: datetime = None,
    ):
        self.flow_id = flow_id
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
        self.user_id = user_id
        self.discovery_flow_id = discovery_flow_id
        self.automation_tier = automation_tier
        self.current_phase = current_phase
        self.next_phase = next_phase
        self.status = status
        self.progress = progress
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)

        # Configuration
        self.collection_config = {}
        self.metadata = {}
        self.phase_state = {}

        # Results and insights
        self.collected_platforms = []
        self.collection_results = {}
        self.gap_analysis_results = {}
        self.agent_insights = []

        # Quality metrics
        self.collection_quality_score = None
        self.confidence_score = None

        # Assessment readiness
        self.assessment_ready = False
        self.apps_ready_for_assessment = 0

        # Error handling
        self.error_message = None
        self.error_details = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary representation."""
        return {
            "flow_id": self.flow_id,
            "client_account_id": self.client_account_id,
            "engagement_id": self.engagement_id,
            "user_id": self.user_id,
            "discovery_flow_id": self.discovery_flow_id,
            "automation_tier": (
                self.automation_tier.value
                if isinstance(self.automation_tier, Enum)
                else self.automation_tier
            ),
            "current_phase": (
                self.current_phase.value
                if isinstance(self.current_phase, Enum)
                else self.current_phase
            ),
            "next_phase": (
                self.next_phase.value
                if isinstance(self.next_phase, Enum) and self.next_phase
                else self.next_phase
            ),
            "status": (
                self.status.value if isinstance(self.status, Enum) else self.status
            ),
            "progress": self.progress,
            "collection_config": self.collection_config,
            "metadata": self.metadata,
            "phase_state": self.phase_state,
            "collected_platforms": self.collected_platforms,
            "collection_results": self.collection_results,
            "gap_analysis_results": self.gap_analysis_results,
            "agent_insights": self.agent_insights,
            "collection_quality_score": self.collection_quality_score,
            "confidence_score": self.confidence_score,
            "assessment_ready": self.assessment_ready,
            "apps_ready_for_assessment": self.apps_ready_for_assessment,
            "error_message": self.error_message,
            "error_details": self.error_details,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def update_progress(self, progress: float):
        """Update progress and timestamp."""
        self.progress = max(0.0, min(100.0, progress))
        self.updated_at = datetime.now(timezone.utc)

    def advance_phase(self, next_phase: CollectionPhase):
        """Advance to next phase."""
        self.current_phase = self.next_phase or next_phase
        self.next_phase = next_phase
        self.updated_at = datetime.now(timezone.utc)

    def set_error(self, error_message: str, error_details: Dict[str, Any] = None):
        """Set error state."""
        self.status = CollectionStatus.ERROR
        self.error_message = error_message
        self.error_details = error_details or {}
        self.updated_at = datetime.now(timezone.utc)

    def clear_error(self):
        """Clear error state."""
        if self.status == CollectionStatus.ERROR:
            self.status = CollectionStatus.INITIALIZING
        self.error_message = None
        self.error_details = {}
        self.updated_at = datetime.now(timezone.utc)

    def is_complete(self) -> bool:
        """Check if flow is complete."""
        return self.status == CollectionStatus.COMPLETED

    def is_failed(self) -> bool:
        """Check if flow failed."""
        return self.status in [CollectionStatus.FAILED, CollectionStatus.ERROR]
