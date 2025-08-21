"""
Pydantic schemas for Collection Flow API
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


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
    client_account_id: str
    engagement_id: str
    status: str
    automation_tier: str
    current_phase: str
    progress: float
    collection_config: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    gaps_identified: Optional[int] = None
    collection_metrics: Optional[Dict[str, Any]] = None
    discovery_flow_id: Optional[str] = None

    class Config:
        from_attributes = True


class CollectionGapAnalysisResponse(BaseModel):
    """Schema for gap analysis response"""

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

    class Config:
        from_attributes = True


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
    responses_collected: Optional[Dict[str, Any]] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


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
