"""
Component Analysis and Tech Debt Pydantic schemas.

This module contains schemas for component identification,
technical debt analysis, and 6R migration decisions.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ComponentStructure(BaseModel):
    """Schema for component structure."""

    component_type: str = Field(..., description="Type of component")
    component_name: str = Field(..., description="Name of component")
    description: Optional[str] = None
    technologies: List[str] = Field(default=[], description="Technologies used")
    dependencies: List[str] = Field(default=[], description="Component dependencies")
    complexity_score: Optional[float] = Field(
        None, ge=0, le=100, description="Complexity score 0-100"
    )
    confidence_score: Optional[float] = Field(
        None, ge=0, le=1, description="AI confidence 0-1"
    )


class ComponentUpdate(BaseModel):
    """Schema for updating component identification."""

    components: List[ComponentStructure] = Field(
        ..., description="Updated component list"
    )
    user_verified: bool = Field(
        default=False, description="Whether user has verified components"
    )
    verification_comments: Optional[str] = Field(
        None, description="User verification comments"
    )


class TechDebtItem(BaseModel):
    """Schema for technical debt item."""

    debt_type: str = Field(..., description="Type of technical debt")
    severity: str = Field(..., description="Severity level")
    description: str = Field(..., description="Description of debt")
    estimated_effort_hours: Optional[int] = Field(
        None, description="Estimated effort to resolve"
    )
    impact_score: Optional[float] = Field(
        None, ge=0, le=100, description="Impact score"
    )
    remediation_suggestions: List[str] = Field(
        default=[], description="Remediation suggestions"
    )


class TechDebtAnalysis(BaseModel):
    """Schema for technical debt analysis."""

    overall_debt_score: float = Field(
        ..., ge=0, le=100, description="Overall debt score"
    )
    debt_items: List[TechDebtItem] = Field(..., description="Individual debt items")
    analysis_confidence: float = Field(
        ..., ge=0, le=1, description="Analysis confidence"
    )
    recommendations: List[str] = Field(
        default=[], description="High-level recommendations"
    )


class TechDebtUpdates(BaseModel):
    """Schema for updating tech debt analysis."""

    debt_analysis: TechDebtAnalysis = Field(..., description="Updated debt analysis")
    user_feedback: Optional[str] = Field(None, description="User feedback on analysis")
    accepted_recommendations: List[str] = Field(
        default=[], description="User-accepted recommendations"
    )


class SixRDecision(BaseModel):
    """Schema for 6R migration decision."""

    component_id: Optional[str] = Field(
        None, description="Component ID (if component-level decision)"
    )
    recommended_strategy: str = Field(..., description="Primary 6R recommendation")
    alternative_strategies: List[Dict[str, Any]] = Field(
        default=[], description="Alternative strategies with scores"
    )
    strategy_rationale: str = Field(..., description="Explanation for recommendation")
    confidence_score: float = Field(
        ..., ge=0, le=1, description="Confidence in recommendation"
    )
    estimated_effort: Optional[int] = Field(
        None, description="Estimated effort in hours"
    )
    estimated_cost: Optional[float] = Field(None, description="Estimated cost")
    risk_level: str = Field(..., description="Risk level assessment")
    dependencies: List[str] = Field(
        default=[], description="Dependencies affecting decision"
    )


class SixRDecisionUpdate(BaseModel):
    """Schema for updating 6R decisions."""

    decisions: List[SixRDecision] = Field(..., description="Updated 6R decisions")
    user_overrides: Dict[str, Any] = Field(
        default={}, description="User overrides to AI recommendations"
    )
    approval_status: str = Field(default="pending", description="Approval status")
