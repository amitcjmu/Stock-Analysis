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


class AssessmentApplicationsListResponse(BaseModel):
    """
    Response for GET /master-flows/{flow_id}/assessment-applications.

    Returns application-centric view with canonical grouping.
    Enhanced in October 2025 to use AssessmentApplicationResolver.
    """

    flow_id: str
    applications: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of application groups with their assets",
    )
    total_applications: int = Field(
        0, ge=0, description="Total number of application groups"
    )
    total_assets: int = Field(0, ge=0, description="Total number of assets")
    unmapped_assets: int = Field(
        0, ge=0, description="Number of assets without canonical mapping"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "flow_id": "ced44ce1-effc-403f-89cc-aeeb05ceba84",
                "applications": [
                    {
                        "canonical_application_id": "05459507-86cb-41f9-9c2d-2a9f4a50445a",
                        "canonical_application_name": "CRM System",
                        "asset_count": 3,
                        "asset_types": ["server", "database", "network_device"],
                        "readiness_summary": {
                            "ready": 2,
                            "not_ready": 1,
                            "in_progress": 0,
                        },
                    }
                ],
                "total_applications": 1,
                "total_assets": 3,
                "unmapped_assets": 0,
            }
        }
    )


class AssetReadinessDetail(BaseModel):
    """Detailed readiness information for a single asset."""

    asset_id: str
    asset_name: str
    asset_type: str
    assessment_readiness: str
    completeness_score: float = Field(ge=0.0, le=1.0)
    assessment_blockers: List[str] = Field(default_factory=list)
    missing_critical_attributes: List[str] = Field(default_factory=list)


class AssessmentReadinessResponse(BaseModel):
    """
    Response for GET /master-flows/{flow_id}/assessment-readiness.

    Provides detailed readiness information with blockers and guidance.
    """

    flow_id: str
    readiness_summary: Dict[str, Any] = Field(
        default_factory=dict,
        description="Overall readiness summary",
    )
    enrichment_status: Dict[str, Any] = Field(
        default_factory=dict,
        description="Enrichment table population status",
    )
    blockers: List[AssetReadinessDetail] = Field(
        default_factory=list,
        description="Assets with blockers (not ready)",
    )
    actionable_guidance: List[str] = Field(
        default_factory=list,
        description="Actionable guidance for addressing blockers",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "flow_id": "ced44ce1-effc-403f-89cc-aeeb05ceba84",
                "readiness_summary": {
                    "total_assets": 5,
                    "ready": 2,
                    "not_ready": 3,
                    "in_progress": 0,
                    "avg_completeness_score": 0.64,
                },
                "enrichment_status": {
                    "compliance_flags": 2,
                    "licenses": 0,
                    "vulnerabilities": 3,
                },
                "blockers": [
                    {
                        "asset_id": "c4ed088f-6658-405b-b011-8ce50c065ddf",
                        "asset_name": "DevTestVM01",
                        "asset_type": "server",
                        "assessment_readiness": "not_ready",
                        "completeness_score": 0.42,
                        "assessment_blockers": [
                            "missing_business_owner",
                            "missing_dependencies",
                        ],
                        "missing_critical_attributes": [
                            "business_owner",
                            "annual_operating_cost",
                        ],
                    }
                ],
                "actionable_guidance": ["3 asset(s) missing business owner"],
            }
        }
    )


class AssessmentProgressCategory(BaseModel):
    """Progress for a single attribute category."""

    name: str = Field(..., description="Category name")
    attributes: List[str] = Field(
        default_factory=list, description="Attribute names in category"
    )
    completed: int = Field(0, ge=0, description="Number of completed attributes")
    total: int = Field(0, ge=0, description="Total attributes in category")
    progress_percent: float = Field(
        0.0, ge=0.0, le=100.0, description="Progress percentage"
    )


class AssessmentProgressResponse(BaseModel):
    """
    Response for GET /master-flows/{flow_id}/assessment-progress.

    Returns attribute-level progress tracking by category.
    """

    flow_id: str
    categories: List[AssessmentProgressCategory] = Field(
        default_factory=list,
        description="Progress by category",
    )
    overall_progress: float = Field(
        0.0, ge=0.0, le=100.0, description="Overall progress percentage"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "flow_id": "ced44ce1-effc-403f-89cc-aeeb05ceba84",
                "categories": [
                    {
                        "name": "Infrastructure",
                        "attributes": [
                            "asset_name",
                            "technology_stack",
                            "operating_system",
                        ],
                        "completed": 15,
                        "total": 18,
                        "progress_percent": 83.3,
                    }
                ],
                "overall_progress": 65.5,
            }
        }
    )
