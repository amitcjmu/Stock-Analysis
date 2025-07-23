"""
Pydantic schemas for assessment flow service operations.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AssessmentRequest(BaseModel):
    """Request model for assessment operations."""

    flow_id: str = Field(..., description="Discovery flow identifier")
    assessment_type: str = Field(
        "full", description="Type of assessment (full, partial, validation)"
    )
    selected_asset_ids: Optional[List[str]] = Field(
        None, description="Specific asset IDs for partial assessment"
    )
    include_recommendations: bool = Field(
        True, description="Include AI-generated recommendations"
    )
    assessment_options: Optional[Dict[str, Any]] = Field(
        None, description="Additional assessment configuration"
    )


class FlowCompletionRequest(BaseModel):
    """Request model for flow completion operations."""

    flow_id: str = Field(..., description="Discovery flow identifier")
    user_id: Optional[str] = Field(None, description="User initiating completion")
    completion_options: Optional[Dict[str, Any]] = Field(
        None, description="Completion configuration options"
    )
    generate_assessment_package: bool = Field(
        True, description="Generate assessment package during completion"
    )


class AssetReadinessResponse(BaseModel):
    """Response model for asset readiness assessment."""

    asset_id: str = Field(..., description="Asset identifier")
    asset_name: str = Field(..., description="Asset name")
    is_ready: bool = Field(..., description="Whether asset is ready for migration")
    readiness_score: float = Field(..., description="Numeric readiness score (0-1)")
    readiness_level: str = Field(..., description="Categorical readiness level")
    readiness_factors: Dict[str, Any] = Field(
        ..., description="Detailed readiness factor scores"
    )
    blocking_issues: List[str] = Field(..., description="Issues preventing readiness")
    recommendations: List[str] = Field(
        ..., description="Recommendations for improving readiness"
    )


class RiskAssessmentResponse(BaseModel):
    """Response model for migration risk assessment."""

    overall_risk_score: float = Field(..., description="Overall risk score (0-1)")
    overall_risk_level: str = Field(..., description="Categorical risk level")
    total_assets: int = Field(..., description="Total number of assets assessed")
    risk_distribution: Dict[str, Dict[str, Any]] = Field(
        ..., description="Risk level distribution"
    )
    risk_factors: List[Dict[str, Any]] = Field(
        ..., description="Identified risk factors"
    )
    mitigation_strategies: List[Dict[str, Any]] = Field(
        ..., description="Risk mitigation strategies"
    )
    recommendations: List[str] = Field(
        ..., description="Risk management recommendations"
    )


class ComplexityAssessmentResponse(BaseModel):
    """Response model for migration complexity assessment."""

    overall_complexity_score: float = Field(
        ..., description="Overall complexity score (0-1)"
    )
    overall_complexity_level: str = Field(
        ..., description="Categorical complexity level"
    )
    total_assets: int = Field(..., description="Total number of assets assessed")
    complexity_distribution: Dict[str, Dict[str, Any]] = Field(
        ..., description="Complexity level distribution"
    )
    effort_estimates: Dict[str, Any] = Field(
        ..., description="Effort estimation details"
    )
    complexity_factors: List[Dict[str, Any]] = Field(
        ..., description="Identified complexity factors"
    )
    recommendations: List[str] = Field(
        ..., description="Complexity management recommendations"
    )
    estimated_effort: str = Field(..., description="Human-readable effort estimate")


class ValidationResult(BaseModel):
    """Response model for validation operations."""

    is_valid: bool = Field(..., description="Whether validation passed")
    validation_score: float = Field(..., description="Numeric validation score (0-1)")
    validation_level: str = Field(..., description="Categorical validation level")
    validation_checks: Dict[str, Any] = Field(
        ..., description="Detailed validation check results"
    )
    validation_errors: List[str] = Field(..., description="Validation errors found")
    validation_warnings: List[str] = Field(..., description="Validation warnings")
    recommendations: List[str] = Field(
        ..., description="Recommendations for passing validation"
    )


class AssessmentPackage(BaseModel):
    """Response model for assessment package generation."""

    package_id: str = Field(..., description="Unique assessment package identifier")
    flow_id: str = Field(..., description="Discovery flow identifier")
    generated_at: datetime = Field(..., description="Package generation timestamp")
    package_version: str = Field(..., description="Package format version")
    metadata: Dict[str, Any] = Field(..., description="Package metadata")
    asset_inventory: Dict[str, Any] = Field(..., description="Complete asset inventory")
    risk_assessment: RiskAssessmentResponse = Field(
        ..., description="Migration risk assessment"
    )
    complexity_assessment: ComplexityAssessmentResponse = Field(
        ..., description="Migration complexity assessment"
    )
    migration_waves: List[Dict[str, Any]] = Field(
        ..., description="Recommended migration waves"
    )
    recommendations: Dict[str, Any] = Field(
        ..., description="Migration recommendations"
    )
    summary: Dict[str, Any] = Field(..., description="Executive summary")


class FlowCompletionResponse(BaseModel):
    """Response model for flow completion operations."""

    flow_id: str = Field(..., description="Discovery flow identifier")
    status: str = Field(..., description="Completion status")
    completed_at: datetime = Field(..., description="Completion timestamp")
    assessment_ready: bool = Field(
        ..., description="Whether flow is ready for assessment"
    )
    assessment_package: Optional[AssessmentPackage] = Field(
        None, description="Generated assessment package"
    )
    next_steps: Dict[str, Any] = Field(..., description="Recommended next steps")
    completion_summary: Dict[str, Any] = Field(
        ..., description="Completion summary and metrics"
    )


class AssessmentResponse(BaseModel):
    """Generic response model for assessment operations."""

    operation_type: str = Field(
        ..., description="Type of assessment operation performed"
    )
    flow_id: str = Field(..., description="Discovery flow identifier")
    status: str = Field(..., description="Operation status")
    timestamp: datetime = Field(..., description="Operation timestamp")
    results: Dict[str, Any] = Field(..., description="Operation results")
    recommendations: List[str] = Field(..., description="Operation recommendations")
    next_steps: List[Dict[str, Any]] = Field(..., description="Recommended next steps")


class PartialAssessmentRequest(BaseModel):
    """Request model for partial assessment operations."""

    flow_id: str = Field(..., description="Discovery flow identifier")
    selected_asset_ids: List[str] = Field(
        ..., description="Asset IDs to include in assessment"
    )
    assessment_scope: str = Field(
        "selected_assets", description="Scope of partial assessment"
    )
    assessment_options: Optional[Dict[str, Any]] = Field(
        None, description="Assessment configuration"
    )


class ValidationRequest(BaseModel):
    """Request model for validation operations."""

    flow_id: str = Field(..., description="Discovery flow identifier")
    validation_type: str = Field(
        "comprehensive", description="Type of validation to perform"
    )
    validation_options: Optional[Dict[str, Any]] = Field(
        None, description="Validation configuration"
    )


class CoordinationResponse(BaseModel):
    """Response model for flow coordination operations."""

    operation: str = Field(..., description="Coordination operation performed")
    flow_id: str = Field(..., description="Discovery flow identifier")
    status: str = Field(..., description="Coordination status")
    timestamp: datetime = Field(..., description="Operation timestamp")
    coordination_results: Dict[str, Any] = Field(
        ..., description="Coordination operation results"
    )
    orchestration_summary: Dict[str, Any] = Field(
        ..., description="High-level orchestration summary"
    )
    next_phase: Optional[Dict[str, Any]] = Field(
        None, description="Next phase information"
    )


class AssetCriteriaRequest(BaseModel):
    """Request model for asset selection by criteria."""

    flow_id: str = Field(..., description="Discovery flow identifier")
    criteria: Dict[str, Any] = Field(..., description="Asset selection criteria")
    limit: Optional[int] = Field(None, description="Maximum number of assets to return")
    sort_by: Optional[str] = Field(None, description="Field to sort results by")


class BulkAssetUpdateRequest(BaseModel):
    """Request model for bulk asset updates."""

    asset_ids: List[str] = Field(..., description="Asset IDs to update")
    update_data: Dict[str, Any] = Field(
        ..., description="Data to update for all assets"
    )
    update_type: str = Field("assessment_data", description="Type of bulk update")


class FlowStatisticsResponse(BaseModel):
    """Response model for flow statistics."""

    flow_id: str = Field(..., description="Discovery flow identifier")
    total_assets: int = Field(..., description="Total number of assets in flow")
    migration_ready: int = Field(..., description="Number of migration-ready assets")
    migration_ready_percentage: float = Field(
        ..., description="Percentage of migration-ready assets"
    )
    validated_assets: int = Field(..., description="Number of validated assets")
    validated_percentage: float = Field(
        ..., description="Percentage of validated assets"
    )
    asset_types: Dict[str, int] = Field(..., description="Asset count by type")
    complexity_distribution: Dict[str, int] = Field(
        ..., description="Asset count by complexity"
    )
    flow_status: str = Field(..., description="Current flow status")
    progress_percentage: Optional[float] = Field(
        None, description="Flow progress percentage"
    )
    assessment_ready: bool = Field(..., description="Whether flow is assessment ready")


class SearchAssetsRequest(BaseModel):
    """Request model for asset search operations."""

    flow_id: str = Field(..., description="Discovery flow identifier")
    search_term: str = Field(..., description="Search term for asset name or type")
    limit: int = Field(50, description="Maximum number of search results")
    filters: Optional[Dict[str, Any]] = Field(
        None, description="Additional search filters"
    )


class ResetFlowRequest(BaseModel):
    """Request model for flow reset operations."""

    flow_id: str = Field(..., description="Discovery flow identifier")
    reset_scope: str = Field("assessment_data", description="Scope of reset operation")
    reset_options: Optional[Dict[str, Any]] = Field(
        None, description="Reset configuration options"
    )
    confirmation: bool = Field(False, description="Confirmation of reset operation")
