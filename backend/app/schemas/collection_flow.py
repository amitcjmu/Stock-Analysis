"""
Pydantic schemas for Collection Flow API
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict


class CollectionFlowCreate(BaseModel):
    """Schema for creating a collection flow"""

    automation_tier: Optional[str] = Field(
        default="tier_2", description="Automation tier (tier_1 to tier_4)"
    )
    collection_config: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Collection configuration"
    )
    target_platforms: Optional[List[str]] = Field(
        default_factory=list, description="Target platforms to scan"
    )
    allow_multiple: Optional[bool] = Field(
        default=False,
        description="Allow multiple concurrent flows (overrides 409 conflict checking)",
    )
    missing_attributes: Optional[Dict[str, List[str]]] = Field(
        default=None,
        description="Missing attributes by asset_id - triggers gap creation and questionnaire generation",
    )


class CollectionFlowUpdate(BaseModel):
    """Schema for updating a collection flow"""

    action: Optional[str] = Field(
        None,
        description="Action to perform: continue, pause, cancel, update_applications",
    )
    user_input: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="User input for flow continuation"
    )
    collection_config: Optional[Dict[str, Any]] = Field(
        None, description="Updated collection configuration"
    )
    flow_name: Optional[str] = Field(None, description="Updated flow name")
    automation_tier: Optional[str] = Field(None, description="Updated automation tier")


class CollectionFlowResponse(BaseModel):
    """Schema for collection flow response"""

    id: str
    flow_id: Optional[str] = (
        None  # CRITICAL: Master flow ID - required for delete operations
    )
    client_account_id: str
    engagement_id: str
    status: str
    automation_tier: str
    current_phase: Optional[str] = Field(
        default="initialized", description="Current phase of the flow"
    )
    progress: float
    collection_config: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    gaps_identified: Optional[int] = None
    collection_metrics: Optional[Dict[str, Any]] = None
    discovery_flow_id: Optional[str] = None

    # Assessment transition tracking (Phase 4)
    assessment_ready: Optional[bool] = None
    apps_ready_for_assessment: Optional[int] = None
    assessment_flow_id: Optional[str] = None
    assessment_transition_date: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class CollectionGapAnalysisResponse(BaseModel):
    """Schema for gap analysis response (DEPRECATED - for backwards compatibility)"""

    id: str
    collection_flow_id: str
    attribute_name: str
    attribute_category: str
    business_impact: str
    priority: int
    collection_difficulty: str
    affects_strategies: List[str]
    blocks_decision: bool
    recommended_collection_method: Optional[str] = None
    resolution_status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CollectionGapAnalysisSummaryResponse(BaseModel):
    """Schema for gap analysis summary response - matches actual database schema"""

    id: str
    client_account_id: str
    engagement_id: str
    collection_flow_id: str
    total_fields_required: int
    fields_collected: int
    fields_missing: int
    completeness_percentage: float
    data_quality_score: Optional[float] = None
    confidence_level: Optional[float] = None
    automation_coverage: Optional[float] = None
    critical_gaps: List[Dict[str, Any]] = Field(default_factory=list)  # JSONB list
    optional_gaps: List[Dict[str, Any]] = Field(default_factory=list)  # JSONB list
    gap_categories: Dict[str, List[str]] = Field(default_factory=dict)  # JSONB dict
    recommended_actions: List[str] = Field(default_factory=list)
    questionnaire_requirements: Dict[str, Any] = Field(default_factory=dict)
    analyzed_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QuestionnaireSubmissionRequest(BaseModel):
    """Schema for submitting questionnaire responses"""

    responses: Dict[str, Any] = Field(
        ..., description="Form responses with field_id -> value mapping"
    )
    form_metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Form metadata including application_id, completion_percentage, etc.",
    )
    validation_results: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Validation results including isValid flag and field-level errors",
    )


class AdaptiveQuestionnaireResponse(BaseModel):
    """Schema for adaptive questionnaire response"""

    id: str
    collection_flow_id: str
    title: str
    description: Optional[str] = None
    target_gaps: List[str]
    questions: List[Dict[str, Any]]
    validation_rules: Optional[Dict[str, Any]] = None
    completion_status: str
    status_line: Optional[str] = None
    responses_collected: Optional[Dict[str, Any]] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ManageFlowRequest(BaseModel):
    """Schema for managing existing flows via /flows/manage endpoint"""

    action: str = Field(
        ...,
        description=(
            "Action to perform on flows. Valid actions: "
            "'cancel_flow', 'cancel_multiple', 'complete_flow', "
            "'cancel_stale', 'auto_complete'"
        ),
    )
    flow_id: Optional[str] = Field(
        None,
        description=(
            "Specific flow ID for single-flow actions " "(required for 'cancel_flow')"
        ),
    )
    flow_ids: Optional[List[str]] = Field(
        None,
        description=(
            "Multiple flow IDs for batch actions " "(required for 'cancel_multiple')"
        ),
    )


class CollectionApplicationSelectionRequest(BaseModel):
    """Schema for collection flow application selection request"""

    selected_application_ids: List[str] = Field(
        ...,
        description="List of application IDs to include in the collection flow",
        min_length=1,
    )
    action: Optional[str] = Field(
        default="update_applications",
        description="Action to perform (default: update_applications)",
    )


class QuestionnaireGenerationRequest(BaseModel):
    """Request to generate questionnaire using agents"""

    selected_asset_ids: Optional[List[str]] = Field(
        None,
        description="List of asset IDs to focus questionnaire on",
    )
    scope: Optional[str] = Field(
        default="engagement",
        description="Scope of questionnaire: engagement, tenant, or asset",
    )
    questionnaire_type: Optional[str] = Field(
        default="adaptive",
        description="Type of questionnaire to generate",
    )


class QuestionnaireGenerationResponse(BaseModel):
    """Response from questionnaire generation request"""

    status: str = Field(
        ...,
        description="Generation status: pending, ready, fallback, or error",
    )
    questionnaire_id: Optional[str] = Field(
        None,
        description="ID of generated questionnaire when ready",
    )
    error_code: Optional[str] = Field(
        None,
        description="Error code if generation failed or pending",
    )
    retry_after: Optional[int] = Field(
        None,
        description="Seconds to wait before retrying if pending",
    )
    message: Optional[str] = Field(
        None,
        description="Human-readable status message",
    )
