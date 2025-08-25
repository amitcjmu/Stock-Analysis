"""
Flow API Schemas
Request and response models for flow operations.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class CreateFlowRequest(BaseModel):
    """Request model for creating a flow"""

    flow_type: str = Field(
        ..., description="Type of flow (discovery, assessment, planning, etc.)"
    )
    flow_name: Optional[str] = Field(
        None, description="Optional human-readable name for the flow"
    )
    configuration: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Flow-specific configuration"
    )
    initial_state: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Initial state data"
    )

    @validator("flow_type")
    def validate_flow_type(cls, v):
        """Validate flow type is not empty"""
        if not v or not v.strip():
            raise ValueError("Flow type cannot be empty")
        return v.strip().lower()


class FlowResponse(BaseModel):
    """Response model for flow operations"""

    flow_id: str
    flow_type: str
    flow_name: Optional[str]
    status: str
    phase: Optional[str]
    progress_percentage: float
    created_at: datetime
    updated_at: datetime
    created_by: str
    configuration: Dict[str, Any]
    metadata: Dict[str, Any]

    class Config:
        from_attributes = True


class ExecutePhaseRequest(BaseModel):
    """Request model for executing a flow phase"""

    phase_input: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Input data for the phase"
    )
    force_execution: bool = Field(
        False, description="Force execution even if preconditions fail"
    )


class FlowStatusResponse(BaseModel):
    """Detailed flow status response"""

    flow_id: str
    flow_type: str
    flow_name: Optional[str]
    status: str
    phase: Optional[str]
    progress_percentage: float
    created_at: datetime
    updated_at: datetime
    execution_history: List[Dict[str, Any]]
    current_state: Dict[str, Any]
    error_details: Optional[Dict[str, Any]]
    performance_metrics: Dict[str, Any]

    class Config:
        from_attributes = True


class FlowListResponse(BaseModel):
    """Response model for listing flows"""

    flows: List[FlowResponse]
    total: int
    page: int
    page_size: int


class FlowStateUpdate(BaseModel):
    """Request model for updating flow state"""

    state_updates: Dict[str, Any] = Field(..., description="State fields to update")
    merge_strategy: str = Field(
        "merge", description="How to merge updates (merge, replace, deep_merge)"
    )


class FlowTransitionRequest(BaseModel):
    """Request model for transitioning flow state"""

    target_phase: str = Field(..., description="Target phase to transition to")
    transition_data: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Data for the transition"
    )
    validate_preconditions: bool = Field(
        True, description="Whether to validate preconditions"
    )


class FlowAnalyticsResponse(BaseModel):
    """Response model for flow analytics"""

    flow_id: str
    flow_type: str
    phase_durations: Dict[str, float]
    success_rate: float
    error_count: int
    retry_count: int
    data_processed: Dict[str, Any]
    resource_usage: Dict[str, Any]


class FlowBulkOperationRequest(BaseModel):
    """Request model for bulk flow operations"""

    flow_ids: List[str] = Field(..., description="List of flow IDs to operate on")
    operation: str = Field(
        ..., description="Operation to perform (pause, resume, cancel, retry)"
    )
    operation_params: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Parameters for the operation"
    )


class FlowBulkOperationResponse(BaseModel):
    """Response model for bulk flow operations"""

    successful: List[str]
    failed: List[Dict[str, str]]  # {flow_id: error_message}
    total_processed: int
