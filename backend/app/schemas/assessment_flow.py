"""
Assessment Flow Pydantic schemas for API request/response validation.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, ConfigDict

from app.models.assessment_flow import AssessmentFlowStatus, AssessmentPhase


class AssessmentApplicationInfo(BaseModel):
    """Schema for basic application information in assessment flows."""

    id: str
    name: str
    type: Optional[str] = None
    environment: Optional[str] = None
    business_criticality: Optional[str] = None
    technology_stack: List[str] = Field(default_factory=list)
    complexity_score: Optional[float] = None
    readiness_score: Optional[float] = None
    discovery_completed_at: Optional[datetime] = None


class AssessmentFlowCreateRequest(BaseModel):
    """Request schema for creating a new assessment flow."""

    selected_application_ids: List[str] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Application IDs to include in assessment",
    )

    @field_validator("selected_application_ids")
    @classmethod
    def validate_application_ids(cls, v):
        """Validate application IDs format."""
        for app_id in v:
            if not app_id or not isinstance(app_id, str):
                raise ValueError("Application IDs must be non-empty strings")
        return v


class AssessmentFlowResponse(BaseModel):
    """Response schema for assessment flow operations."""

    flow_id: str
    status: AssessmentFlowStatus
    current_phase: AssessmentPhase
    next_phase: Optional[AssessmentPhase] = None
    selected_applications: Optional[int] = None
    message: str

    model_config = ConfigDict(use_enum_values=True)


class AssessmentFlowStatusResponse(BaseModel):
    """Detailed status response for assessment flow."""

    flow_id: str
    status: AssessmentFlowStatus
    progress_percentage: int = Field(ge=0, le=100, description="Progress percentage")
    current_phase: AssessmentPhase
    next_phase: Optional[AssessmentPhase] = None
    pause_points: List[str] = []
    user_inputs_captured: bool = False
    phase_results: Dict[str, Any] = {}
    apps_ready_for_planning: List[str] = []
    last_user_interaction: Optional[datetime] = None
    phase_data: Optional[Dict[str, Any]] = None
    selected_applications: int = Field(description="Number of selected applications")
    assessment_complete: bool = Field(description="Whether assessment is complete")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(use_enum_values=True)


class ResumeFlowRequest(BaseModel):
    """Request schema for resuming assessment flow."""

    user_input: Dict[str, Any] = Field(..., description="User input for current phase")
    save_progress: bool = Field(default=True, description="Whether to save progress")


class NavigateToPhaseRequest(BaseModel):
    """Request schema for navigating to specific phase."""

    target_phase: AssessmentPhase = Field(
        ..., description="Target phase to navigate to"
    )
    force_navigation: bool = Field(
        default=False, description="Force navigation even if prerequisites not met"
    )


# Architecture Standards Schemas


class ArchitectureStandardCreate(BaseModel):
    """Schema for creating architecture standards."""

    standard_type: str = Field(
        ..., description="Type of standard (e.g., cloud_provider, framework)"
    )
    domain: Optional[str] = Field(
        None, description="Domain area (e.g., infrastructure, application)"
    )
    standard_definition: Dict[str, Any] = Field(
        ..., description="The actual standard definition"
    )
    enforcement_level: str = Field(
        default="recommended", description="Enforcement level"
    )
    is_template: bool = Field(
        default=False, description="Whether this is a reusable template"
    )
    customizable_fields: List[str] = Field(
        default=[], description="Fields that can be customized"
    )


class ArchitectureStandardResponse(BaseModel):
    """Response schema for architecture standards."""

    id: str
    standard_type: str
    domain: Optional[str]
    standard_definition: Dict[str, Any]
    enforcement_level: str
    is_template: bool
    customizable_fields: List[str]
    created_by: str
    created_at: datetime
    updated_at: datetime


class ArchitectureStandardUpdate(BaseModel):
    """Schema for updating architecture standards."""

    standard_definition: Optional[Dict[str, Any]] = None
    enforcement_level: Optional[str] = None
    customizable_fields: Optional[List[str]] = None


class ApplicationOverrideCreate(BaseModel):
    """Schema for creating application overrides."""

    application_id: str = Field(..., description="Application ID for override")
    standard_id: str = Field(..., description="Standard ID being overridden")
    override_data: Dict[str, Any] = Field(..., description="Override values")
    override_reason: Optional[str] = Field(
        None, description="Justification for override"
    )
    requires_approval: bool = Field(
        default=False, description="Whether override requires approval"
    )


class ApplicationOverrideResponse(BaseModel):
    """Response schema for application overrides."""

    id: str
    application_id: str
    standard_id: str
    override_data: Dict[str, Any]
    override_reason: Optional[str]
    requires_approval: bool
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    approval_comments: Optional[str]
    created_by: str
    created_at: datetime
    updated_at: datetime


class ArchitectureStandardsUpdateRequest(BaseModel):
    """Request schema for updating architecture standards and overrides."""

    engagement_standards: Optional[List[ArchitectureStandardCreate]] = Field(
        None, description="Engagement-level standards"
    )
    application_overrides: Optional[List[ApplicationOverrideCreate]] = Field(
        None, description="Application-specific overrides"
    )


# Component Analysis Schemas


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


# 6R Decision Schemas


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


class AppOnPageData(BaseModel):
    """Schema for app-on-page generation."""

    application_summary: Dict[str, Any] = Field(..., description="Application summary")
    component_breakdown: List[ComponentStructure] = Field(
        ..., description="Component breakdown"
    )
    tech_debt_summary: TechDebtAnalysis = Field(..., description="Tech debt summary")
    migration_recommendations: List[SixRDecision] = Field(
        ..., description="Migration recommendations"
    )
    estimated_timeline: Dict[str, Any] = Field(
        ..., description="Estimated migration timeline"
    )
    cost_analysis: Dict[str, Any] = Field(..., description="Cost analysis")
    risk_assessment: Dict[str, Any] = Field(..., description="Risk assessment")
    next_steps: List[str] = Field(..., description="Recommended next steps")


class AppOnPageResponse(BaseModel):
    """Response schema for app-on-page data."""

    flow_id: str
    application_id: str
    app_on_page_data: AppOnPageData
    generated_at: datetime
    last_updated: datetime


# Finalization Schemas


class AssessmentFinalization(BaseModel):
    """Schema for finalizing assessment."""

    apps_to_finalize: List[str] = Field(
        ..., description="Application IDs to mark as ready for planning"
    )
    finalization_notes: Optional[str] = Field(
        None, description="Notes about finalization"
    )
    export_to_planning: bool = Field(
        default=True, description="Whether to export to Planning Flow"
    )


class AssessmentReport(BaseModel):
    """Schema for comprehensive assessment report."""

    flow_id: str
    assessment_summary: Dict[str, Any]
    applications_assessed: List[str]
    architecture_standards_applied: Dict[str, Any]
    component_analysis_results: Dict[str, Any]
    tech_debt_analysis_results: Dict[str, Any]
    sixr_decisions_summary: Dict[str, Any]
    apps_ready_for_planning: List[str]
    overall_readiness_score: float
    report_generated_at: datetime


# Event Streaming Schemas


class AssessmentFlowEvent(BaseModel):
    """Schema for assessment flow events."""

    flow_id: str
    event_type: str = Field(..., description="Type of event")
    phase: AssessmentPhase
    timestamp: datetime
    data: Dict[str, Any] = Field(default={}, description="Event data")
    message: Optional[str] = Field(None, description="Human-readable message")

    model_config = ConfigDict(use_enum_values=True)


class AgentProgressEvent(BaseModel):
    """Schema for agent progress events."""

    flow_id: str
    agent_name: str
    task_name: str
    progress_percentage: float = Field(ge=0, le=100)
    status: str = Field(..., description="Agent status")
    timestamp: datetime
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details")
