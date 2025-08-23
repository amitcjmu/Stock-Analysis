"""
Assessment Flow In-Memory Models
In-memory state models for CrewAI compatibility.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from .enums_and_exceptions import AssessmentFlowStatus, AssessmentPhase


class InMemorySixRDecision:
    """In-memory representation of a 6R decision for CrewAI processing."""

    def __init__(
        self,
        component_id: str,
        component_name: str,
        sixr_strategy: str,
        confidence: float,
        reasoning: str,
        dependencies: List[str] = None,
        estimated_effort: Optional[str] = None,
        risk_level: str = "medium",
        created_at: datetime = None,
    ):
        self.component_id = component_id
        self.component_name = component_name
        self.sixr_strategy = sixr_strategy
        self.confidence = confidence
        self.reasoning = reasoning
        self.dependencies = dependencies or []
        self.estimated_effort = estimated_effort
        self.risk_level = risk_level
        self.created_at = created_at or datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "component_id": self.component_id,
            "component_name": self.component_name,
            "sixr_strategy": self.sixr_strategy,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "dependencies": self.dependencies,
            "estimated_effort": self.estimated_effort,
            "risk_level": self.risk_level,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AssessmentFlowState:
    """
    In-memory assessment flow state for CrewAI integration.

    This class provides a simplified interface for CrewAI crews to work with
    assessment flow data without direct database dependencies.
    """

    def __init__(
        self,
        flow_id: str,
        engagement_id: str,
        client_account_id: str,
        status: AssessmentFlowStatus = AssessmentFlowStatus.INITIALIZED,
        current_phase: AssessmentPhase = AssessmentPhase.INITIALIZATION,
        master_flow_id: Optional[str] = None,
    ):
        self.flow_id = flow_id
        self.engagement_id = engagement_id
        self.client_account_id = client_account_id
        self.status = status
        self.current_phase = current_phase
        self.master_flow_id = master_flow_id
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

        # Phase-specific data
        self.architecture_standards: Dict[str, Any] = {}
        self.application_components: List[Dict[str, Any]] = []
        self.tech_debt_analysis: Dict[str, Any] = {}
        self.sixr_decisions: List[InMemorySixRDecision] = []
        self.learning_feedback: List[Dict[str, Any]] = []

        # Progress tracking
        self.phase_progress: Dict[str, float] = {}
        self.overall_progress = 0.0

        # Configuration and metadata
        self.configuration: Dict[str, Any] = {}
        self.metadata: Dict[str, Any] = {}

    def add_sixr_decision(
        self,
        component_id: str,
        component_name: str,
        sixr_strategy: str,
        confidence: float,
        reasoning: str,
        **kwargs
    ) -> InMemorySixRDecision:
        """Add a 6R decision to the flow state."""
        decision = InMemorySixRDecision(
            component_id=component_id,
            component_name=component_name,
            sixr_strategy=sixr_strategy,
            confidence=confidence,
            reasoning=reasoning,
            **kwargs
        )
        self.sixr_decisions.append(decision)
        self.updated_at = datetime.utcnow()
        return decision

    def update_phase_progress(self, phase: str, progress: float):
        """Update progress for a specific phase."""
        self.phase_progress[phase] = max(0.0, min(100.0, progress))
        self._recalculate_overall_progress()
        self.updated_at = datetime.utcnow()

    def _recalculate_overall_progress(self):
        """Recalculate overall progress based on phase progress."""
        if not self.phase_progress:
            self.overall_progress = 0.0
            return

        # Weight phases equally for simplicity
        total_progress = sum(self.phase_progress.values())
        self.overall_progress = total_progress / len(self.phase_progress)

    def transition_to_phase(self, new_phase: AssessmentPhase):
        """Transition to a new assessment phase."""
        self.current_phase = new_phase
        self.updated_at = datetime.utcnow()

    def update_status(self, new_status: AssessmentFlowStatus):
        """Update the flow status."""
        self.status = new_status
        self.updated_at = datetime.utcnow()

    def add_learning_feedback(self, feedback: Dict[str, Any]):
        """Add learning feedback from the assessment process."""
        feedback_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "flow_id": self.flow_id,
            **feedback,
        }
        self.learning_feedback.append(feedback_entry)
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert flow state to dictionary for serialization."""
        return {
            "flow_id": self.flow_id,
            "engagement_id": self.engagement_id,
            "client_account_id": self.client_account_id,
            "master_flow_id": self.master_flow_id,
            "status": (
                self.status.value
                if isinstance(self.status, AssessmentFlowStatus)
                else self.status
            ),
            "current_phase": (
                self.current_phase.value
                if isinstance(self.current_phase, AssessmentPhase)
                else self.current_phase
            ),
            "overall_progress": self.overall_progress,
            "phase_progress": self.phase_progress,
            "architecture_standards": self.architecture_standards,
            "application_components": self.application_components,
            "tech_debt_analysis": self.tech_debt_analysis,
            "sixr_decisions": [decision.to_dict() for decision in self.sixr_decisions],
            "learning_feedback": self.learning_feedback,
            "configuration": self.configuration,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AssessmentFlowState":
        """Create flow state from dictionary."""
        instance = cls(
            flow_id=data["flow_id"],
            engagement_id=data["engagement_id"],
            client_account_id=data["client_account_id"],
            status=AssessmentFlowStatus(
                data.get("status", AssessmentFlowStatus.INITIALIZED)
            ),
            current_phase=AssessmentPhase(
                data.get("current_phase", AssessmentPhase.INITIALIZATION)
            ),
            master_flow_id=data.get("master_flow_id"),
        )

        # Restore state data
        instance.overall_progress = data.get("overall_progress", 0.0)
        instance.phase_progress = data.get("phase_progress", {})
        instance.architecture_standards = data.get("architecture_standards", {})
        instance.application_components = data.get("application_components", [])
        instance.tech_debt_analysis = data.get("tech_debt_analysis", {})
        instance.configuration = data.get("configuration", {})
        instance.metadata = data.get("metadata", {})
        instance.learning_feedback = data.get("learning_feedback", [])

        # Restore 6R decisions
        instance.sixr_decisions = []
        for decision_data in data.get("sixr_decisions", []):
            decision = InMemorySixRDecision(
                component_id=decision_data["component_id"],
                component_name=decision_data["component_name"],
                sixr_strategy=decision_data["sixr_strategy"],
                confidence=decision_data["confidence"],
                reasoning=decision_data["reasoning"],
                dependencies=decision_data.get("dependencies", []),
                estimated_effort=decision_data.get("estimated_effort"),
                risk_level=decision_data.get("risk_level", "medium"),
                created_at=(
                    datetime.fromisoformat(decision_data["created_at"])
                    if decision_data.get("created_at")
                    else None
                ),
            )
            instance.sixr_decisions.append(decision)

        # Restore timestamps
        if data.get("created_at"):
            instance.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            instance.updated_at = datetime.fromisoformat(data["updated_at"])

        return instance
