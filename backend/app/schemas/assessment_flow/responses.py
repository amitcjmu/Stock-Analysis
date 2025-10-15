"""
Assessment Flow Response Pydantic schemas.

This module contains all response schemas for assessment flow API endpoints.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict

from app.models.assessment_flow import AssessmentFlowStatus, AssessmentPhase
from .components import ComponentStructure, TechDebtAnalysis, SixRDecision


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
