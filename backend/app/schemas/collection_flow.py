"""
Pydantic schemas for Collection Flow API
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class CollectionFlowCreate(BaseModel):
    """Schema for creating a collection flow"""
    automation_tier: Optional[str] = Field(default="tier_2", description="Automation tier (tier_1 to tier_4)")
    collection_config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Collection configuration")
    target_platforms: Optional[List[str]] = Field(default_factory=list, description="Target platforms to scan")


class CollectionFlowUpdate(BaseModel):
    """Schema for updating a collection flow"""
    action: Optional[str] = Field(None, description="Action to perform: continue, pause, cancel")
    user_input: Optional[Dict[str, Any]] = Field(default_factory=dict, description="User input for flow continuation")
    collection_config: Optional[Dict[str, Any]] = Field(None, description="Updated collection configuration")


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