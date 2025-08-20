"""
Discovery Flow Management Schemas
Enhanced Pydantic models for CrewAI Flow state management and flow lifecycle operations
Provides comprehensive validation and type safety for flow management APIs
Phase 4: Advanced Features & Production Readiness
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# === FIELD MAPPING IMPORTS ===
# Field mapping schemas have been extracted to app.schemas.field_mapping_schemas

# === ENUMS ===


class FlowStatus(str, Enum):
    """Flow status enumeration"""

    RUNNING = "running"
    PAUSED = "paused"
    FAILED = "failed"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class FlowPhase(str, Enum):
    """Flow phase enumeration"""

    FIELD_MAPPING = "field_mapping"
    DATA_CLEANSING = "data_cleansing"
    ASSET_INVENTORY = "asset_inventory"
    DEPENDENCY_ANALYSIS = "dependency_analysis"
    TECH_DEBT = "tech_debt"


class BulkOperation(str, Enum):
    """Bulk operation types"""

    DELETE = "delete"
    PAUSE = "pause"
    RESUME = "resume"
    ARCHIVE = "archive"


# === BASE MODELS ===


class FlowContext(BaseModel):
    """Flow context information"""

    client_account_id: str
    engagement_id: str


class FlowInfo(BaseModel):
    """Basic flow information"""

    flow_id: str
    current_phase: FlowPhase
    status: FlowStatus
    progress_percentage: float = Field(ge=0, le=100)
    created_at: str
    updated_at: str
    started_at: Optional[str] = None


class FlowManagementInfo(BaseModel):
    """Flow management capabilities"""

    can_resume: bool
    deletion_impact: Dict[str, Any] = Field(default_factory=dict)
    last_activity: Optional[str] = None
    days_since_activity: Optional[int] = None


# === EXISTING SCHEMAS (Phase 1-3) ===


class IncompleteFlowsResponse(BaseModel):
    """Response for incomplete flows query"""

    flows: List[Dict[str, Any]]
    total_count: int
    context: FlowContext


class FlowDetailsResponse(BaseModel):
    """Response for flow details query"""

    flow_id: str
    flow_state: Dict[str, Any]
    can_resume: bool
    validation_errors: List[str] = Field(default_factory=list)
    management_info: Dict[str, Any]


class FlowResumeRequest(BaseModel):
    """Request to resume a flow"""

    resume_context: Optional[Dict[str, Any]] = Field(default_factory=dict)
    force_resume: bool = False


class FlowResumeResponse(BaseModel):
    """Response for flow resumption"""

    success: bool
    flow_id: str
    message: str
    resumed_at: str
    current_phase: Optional[str] = None
    next_phase: Optional[str] = None
    progress_percentage: Optional[float] = None
    status: Optional[str] = None


class FlowDeleteResponse(BaseModel):
    """Response for flow deletion"""

    success: bool
    flow_id: str
    cleanup_summary: Dict[str, Any]
    deleted_at: str


class BulkOperationsRequest(BaseModel):
    """Request for bulk operations"""

    operation: BulkOperation
    flow_ids: List[str] = Field(min_items=1)
    options: Optional[Dict[str, Any]] = Field(default_factory=dict)


class BulkOperationResult(BaseModel):
    """Result for individual bulk operation"""

    flow_id: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class BulkOperationsResponse(BaseModel):
    """Response for bulk operations"""

    operation: BulkOperation
    total_flows: int
    successful: List[BulkOperationResult]
    failed: List[BulkOperationResult]
    summary: Dict[str, Any]
    performance_metrics: Dict[str, Any]


class FlowValidationResponse(BaseModel):
    """Response for flow validation"""

    can_start_new_flow: bool
    blocking_flows: List[Dict[str, Any]] = Field(default_factory=list)
    total_incomplete_flows: int
    validation_message: str


# === PHASE 4: ADVANCED SCHEMAS ===
# Advanced flow schemas have been extracted to app.schemas.advanced_flow_schemas
# Import them from there if needed for backward compatibility


# === VALIDATION HELPERS ===


class FlowValidationError(BaseModel):
    """Flow validation error"""

    field: str
    message: str
    code: str


class FlowContextValidation(BaseModel):
    """Flow context validation"""

    valid: bool
    errors: List[FlowValidationError] = Field(default_factory=list)


# === AUDIT SCHEMAS ===


class FlowAuditEntry(BaseModel):
    """Flow audit entry"""

    flow_id: str
    action: str
    user_id: str
    timestamp: str
    details: Dict[str, Any] = Field(default_factory=dict)


class FlowAuditResponse(BaseModel):
    """Flow audit response"""

    entries: List[FlowAuditEntry]
    total_entries: int
    page: int = 1
    page_size: int = 50


# === ERROR SCHEMAS ===


class FlowManagementError(BaseModel):
    """Flow management error"""

    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: str
    flow_id: Optional[str] = None


class FlowContinuationResult(BaseModel):
    """Result of flow continuation analysis from CrewAI agents"""

    flow_id: str
    current_phase: str
    target_page: str
    user_guidance: str
    confidence_score: float
    processing_time: float
    agent_insights: Dict[str, Any]


class ErrorResponse(BaseModel):
    """Generic error response"""

    success: bool = False
    error: FlowManagementError
