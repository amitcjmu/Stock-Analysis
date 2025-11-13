"""
6R Decision Models
Models for migration strategy decisions and learning feedback.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field

from .component_models import ComponentTreatment
from app.models.asset.enums import SixRStrategy  # Canonical enum location


class SixRDecision(BaseModel):
    """Application-level 6R decision with component rollup"""

    model_config = ConfigDict(use_enum_values=True, validate_assignment=True)

    application_id: UUID = Field(..., description="UUID of the application")
    application_name: str = Field(
        ..., min_length=1, description="Name of the application"
    )
    component_treatments: List[ComponentTreatment] = Field(
        default_factory=list, description="Component-level treatments"
    )
    overall_strategy: SixRStrategy = Field(
        ..., description="Overall application strategy"
    )
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence in the decision"
    )
    rationale: str = Field(..., description="Rationale for the overall strategy")
    architecture_exceptions: List[str] = Field(
        default_factory=list, description="Architecture standard exceptions"
    )
    tech_debt_score: Optional[float] = Field(
        default=None, ge=0.0, description="Overall tech debt score"
    )
    risk_factors: List[str] = Field(
        default_factory=list, description="Risk factors identified"
    )
    estimated_effort_hours: Optional[int] = Field(
        default=None, ge=0, description="Estimated migration effort"
    )
    estimated_cost: Optional[Decimal] = Field(
        default=None, ge=0, description="Estimated migration cost"
    )
    move_group_hints: List[str] = Field(
        default_factory=list, description="Migration grouping hints"
    )
    user_modifications: Optional[Dict[str, Any]] = Field(
        default=None, description="User-made modifications"
    )
    modified_by: Optional[str] = Field(
        default=None, description="Who made modifications"
    )
    modified_at: Optional[datetime] = Field(
        default=None, description="When modifications were made"
    )
    app_on_page_data: Optional[Dict[str, Any]] = Field(
        default=None, description="Complete app-on-page view"
    )
    decision_factors: Optional[Dict[str, Any]] = Field(
        default=None, description="Factors that influenced decision"
    )
    ready_for_planning: bool = Field(
        default=False, description="Ready for planning flow"
    )

    @computed_field
    @property
    def has_high_risk_factors(self) -> bool:
        """Check if application has high-risk factors"""
        high_risk_keywords = [
            "legacy",
            "deprecated",
            "unsupported",
            "critical",
            "security",
        ]
        return any(
            keyword in " ".join(self.risk_factors).lower()
            for keyword in high_risk_keywords
        )

    @computed_field
    @property
    def component_strategy_summary(self) -> Dict[str, int]:
        """Summary of component strategies"""
        summary = {}
        for treatment in self.component_treatments:
            strategy = treatment.recommended_strategy.value
            summary[strategy] = summary.get(strategy, 0) + 1
        return summary

    def calculate_overall_strategy(self) -> SixRStrategy:
        """Calculate app-level strategy from component treatments"""
        if not self.component_treatments:
            return (
                SixRStrategy.REHOST
            )  # Default fallback (retain → rehost per 6R standardization)

        strategies = [ct.recommended_strategy for ct in self.component_treatments]

        # Return highest modernization strategy (6R framework - standardized Oct 2025)
        strategy_order = [
            SixRStrategy.REPLACE,  # Consolidates rewrite + repurchase
            SixRStrategy.REARCHITECT,
            SixRStrategy.REFACTOR,
            SixRStrategy.REPLATFORM,
            SixRStrategy.REHOST,
            SixRStrategy.RETIRE,
        ]

        for strategy in strategy_order:
            if strategy in strategies:
                return strategy

        return (
            SixRStrategy.REHOST
        )  # Default fallback (retain → rehost per 6R standardization)

    def get_compatibility_issues(self) -> List[str]:
        """Get all compatibility issues across components"""
        issues = []
        for treatment in self.component_treatments:
            if treatment.compatibility_issues:
                issues.extend(treatment.compatibility_issues)
        return list(set(issues))  # Remove duplicates

    def validate_component_compatibility(self) -> List[str]:
        """Validate compatibility between component treatments"""
        issues = []
        treatments = {
            ct.component_name: ct.recommended_strategy
            for ct in self.component_treatments
        }

        # Check for incompatible combinations
        if (
            treatments.get("frontend") == SixRStrategy.REPLACE
            and treatments.get("backend") == SixRStrategy.REHOST
        ):
            issues.append(
                "Frontend replacement with backend rehost may cause integration issues"
            )

        if treatments.get("database") == SixRStrategy.RETIRE and any(
            s == SixRStrategy.REHOST for s in treatments.values()
        ):
            issues.append("Database retirement conflicts with rehosted components")

        return issues


class AssessmentLearningFeedback(BaseModel):
    """Learning feedback for agent improvement"""

    model_config = ConfigDict(use_enum_values=True, validate_assignment=True)

    original_strategy: SixRStrategy = Field(
        ..., description="Agent's original recommendation"
    )
    override_strategy: SixRStrategy = Field(..., description="User's override decision")
    feedback_reason: str = Field(..., description="User's rationale for change")
    agent_id: str = Field(..., description="Which agent made the original decision")
    learned_pattern: Optional[Dict[str, Any]] = Field(
        default=None, description="Pattern extracted for learning"
    )
