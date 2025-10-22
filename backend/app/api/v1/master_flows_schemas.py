"""
Master Flow Coordination API Schemas
Response models for master flow endpoints
"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict


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

    model_config = ConfigDict(from_attributes=True)


class MasterFlowResponse(BaseModel):
    """Master flow detail response model (Bug #676 fix)"""

    flow_id: str
    flow_type: str
    flow_name: Optional[str] = None
    flow_status: str
    client_account_id: str
    engagement_id: str
    user_id: str
    flow_configuration: Dict[str, Any]
    current_phase: Optional[str] = None
    progress_percentage: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    execution_metadata: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)
