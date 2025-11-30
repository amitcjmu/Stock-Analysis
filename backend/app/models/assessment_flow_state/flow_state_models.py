"""
Assessment Flow State Models
Main flow state models for assessment flow management and API responses.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

from app.models.asset.enums import SixRStrategy

from .architecture_models import (
    ApplicationArchitectureOverride,
    ArchitectureRequirement,
)
from .component_models import ApplicationComponent, TechDebtItem
from .decision_models import SixRDecision
from .enums import AssessmentFlowStatus, AssessmentPhase, TechDebtSeverity


class AssessmentFlowState(BaseModel):
    """Complete assessment flow state with all components"""

    model_config = ConfigDict(use_enum_values=True, validate_assignment=True)

    # Flow identification
    flow_id: UUID = Field(..., description="Unique flow identifier")
    client_account_id: UUID = Field(..., description="Client account UUID")
    engagement_id: UUID = Field(..., description="Engagement UUID")
    selected_application_ids: List[UUID] = Field(
        ..., description="Selected application UUIDs (legacy - may contain asset UUIDs)"
    )
    selected_canonical_application_ids: List[UUID] = Field(
        default_factory=list,
        description="Selected canonical application UUIDs (preferred over selected_application_ids)",
    )

    # Architecture requirements
    engagement_architecture_standards: List[ArchitectureRequirement] = Field(
        default_factory=list, description="Engagement-level architecture standards"
    )
    application_architecture_overrides: Dict[
        str, List[ApplicationArchitectureOverride]
    ] = Field(default_factory=dict, description="App-specific architecture overrides")
    architecture_captured: bool = Field(
        default=False, description="Whether architecture has been captured"
    )

    # Component identification
    application_components: Dict[str, List[ApplicationComponent]] = Field(
        default_factory=dict, description="Components by application ID"
    )

    # Tech debt analysis
    tech_debt_analysis: Dict[str, List[TechDebtItem]] = Field(
        default_factory=dict, description="Tech debt items by application ID"
    )
    component_tech_debt: Dict[str, Dict[str, float]] = Field(
        default_factory=dict, description="Tech debt scores by app->component"
    )

    # 6R decisions
    sixr_decisions: Dict[str, SixRDecision] = Field(
        default_factory=dict, description="6R decisions by application ID"
    )

    # User interaction tracking
    pause_points: List[str] = Field(
        default_factory=list, description="Pause point identifiers"
    )
    user_inputs: Dict[str, Any] = Field(
        default_factory=dict, description="Phase-specific user inputs"
    )

    # Flow metadata
    status: AssessmentFlowStatus = Field(
        default=AssessmentFlowStatus.INITIALIZED, description="Flow status"
    )
    progress: int = Field(default=0, ge=0, le=100, description="Progress percentage")
    current_phase: AssessmentPhase = Field(
        default=AssessmentPhase.INITIALIZATION, description="Current phase"
    )
    next_phase: Optional[AssessmentPhase] = Field(
        default=None, description="Next phase to execute"
    )
    phase_results: Dict[str, Any] = Field(
        default_factory=dict, description="Phase completion results"
    )
    agent_insights: List[Dict[str, Any]] = Field(
        default_factory=list, description="Agent-generated insights"
    )

    # Readiness tracking
    apps_ready_for_planning: List[UUID] = Field(
        default_factory=list, description="Apps ready for planning"
    )

    # Timestamps
    created_at: datetime = Field(..., description="When flow was created")
    updated_at: datetime = Field(..., description="When flow was last updated")
    last_user_interaction: Optional[datetime] = Field(
        default=None, description="Last user interaction time"
    )
    completed_at: Optional[datetime] = Field(
        default=None, description="When flow was completed"
    )

    @field_validator("progress")
    @classmethod
    def validate_progress(cls, v):
        if not 0 <= v <= 100:
            raise ValueError("Progress must be between 0 and 100")
        return v

    @computed_field
    @property
    def is_complete(self) -> bool:
        """Check if flow is complete"""
        return self.status == AssessmentFlowStatus.COMPLETED

    @computed_field
    @property
    def apps_needing_review(self) -> List[UUID]:
        """Get applications that need user review"""
        return [
            UUID(app_id)
            for app_id, decision in self.sixr_decisions.items()
            if decision.confidence_score < 0.8
        ]

    @computed_field
    @property
    def high_risk_applications(self) -> List[UUID]:
        """Get applications with high risk factors"""
        return [
            UUID(app_id)
            for app_id, decision in self.sixr_decisions.items()
            if decision.has_high_risk_factors
        ]

    @computed_field
    @property
    def critical_tech_debt_count(self) -> int:
        """Count critical tech debt items across all applications"""
        count = 0
        for app_debt in self.tech_debt_analysis.values():
            count += sum(
                1 for item in app_debt if item.severity == TechDebtSeverity.CRITICAL
            )
        return count

    def get_applications_by_strategy(self, strategy: SixRStrategy) -> List[UUID]:
        """Get applications using a specific strategy"""
        return [
            UUID(app_id)
            for app_id, decision in self.sixr_decisions.items()
            if decision.overall_strategy == strategy
        ]

    def get_phase_progress(self) -> Dict[str, bool]:
        """Get completion status of all phases"""
        phases = list(AssessmentPhase)
        current_index = (
            phases.index(self.current_phase) if self.current_phase in phases else 0
        )

        return {phase.value: i <= current_index for i, phase in enumerate(phases)}

    def calculate_overall_readiness_score(self) -> float:
        """Calculate overall migration readiness score"""
        if not self.sixr_decisions:
            return 0.0

        total_score = 0.0
        app_count = len(self.sixr_decisions)

        for decision in self.sixr_decisions.values():
            # Base score from confidence
            score = decision.confidence_score * 100

            # Reduce score for high tech debt
            if decision.tech_debt_score and decision.tech_debt_score > 70:
                score -= 20

            # Reduce score for high risk factors
            if decision.has_high_risk_factors:
                score -= 15

            # Reduce score for compatibility issues
            if decision.get_compatibility_issues():
                score -= 10

            total_score += max(0, score)  # Ensure non-negative

        return round(total_score / app_count, 1)

    def get_strategy_distribution(self) -> Dict[str, int]:
        """Get distribution of strategies across applications"""
        distribution = {}
        for decision in self.sixr_decisions.values():
            strategy = decision.overall_strategy.value
            distribution[strategy] = distribution.get(strategy, 0) + 1
        return distribution

    def get_migration_complexity_summary(self) -> Dict[str, Any]:
        """Get summary of migration complexity factors"""
        return {
            "total_applications": len(self.selected_application_ids),
            "decisions_completed": len(self.sixr_decisions),
            "apps_ready_for_planning": len(self.apps_ready_for_planning),
            "high_risk_apps": len(self.high_risk_applications),
            "critical_tech_debt": self.critical_tech_debt_count,
            "overall_readiness": self.calculate_overall_readiness_score(),
            "strategy_distribution": self.get_strategy_distribution(),
        }


class AssessmentFlowSummary(BaseModel):
    """Simplified assessment flow summary for list views"""

    model_config = ConfigDict(use_enum_values=True)

    flow_id: UUID
    client_account_id: UUID
    engagement_id: UUID
    status: AssessmentFlowStatus
    progress: int
    current_phase: AssessmentPhase
    total_applications: int
    decisions_completed: int
    overall_readiness: float
    created_at: datetime
    updated_at: datetime


class AssessmentPhaseResult(BaseModel):
    """Result of completing an assessment phase"""

    model_config = ConfigDict(use_enum_values=True)

    phase: AssessmentPhase
    completed: bool
    result_data: Dict[str, Any]
    agent_insights: List[Dict[str, Any]]
    next_phase: Optional[AssessmentPhase] = None
    pause_required: bool = False
    user_input_needed: bool = False


class AssessmentValidationResult(BaseModel):
    """Result of validating assessment data"""

    model_config = ConfigDict(use_enum_values=True)

    valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
