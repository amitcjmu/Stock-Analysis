"""
Master Flow Coordination API Schemas
Response models for master flow endpoints
"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel


class MasterFlowSummaryResponse(BaseModel):
    """Master flow summary response model"""

    master_flow_id: str
    total_assets: int
    phases: Dict[str, int]
    asset_types: Dict[str, int]
    strategies: Dict[str, int]
    status_distribution: Dict[str, int]


class CrossPhaseAnalyticsResponse(BaseModel):
    """Cross-phase analytics response model"""

    master_flows: Dict[str, Dict[str, Any]]
    phase_transitions: Dict[str, int]
    quality_by_phase: Dict[str, Dict[str, Any]]


class MasterFlowCoordinationResponse(BaseModel):
    """Master flow coordination summary response"""

    flow_type_distribution: Dict[str, int]
    master_flow_references: Dict[str, int]
    assessment_readiness: Dict[str, int]
    coordination_metrics: Dict[str, float]
    error: Optional[str] = None


class DiscoveryFlowResponse(BaseModel):
    """Simple discovery flow response for master flow API"""

    id: str
    flow_id: str
    client_account_id: str
    engagement_id: str
    flow_name: Optional[str] = None
    status: str
    progress_percentage: float
    master_flow_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
