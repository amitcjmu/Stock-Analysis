"""
Discovery Flow Management Schemas
Pydantic schemas for flow management API endpoints
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

# ========================================
# REQUEST SCHEMAS
# ========================================

class FlowResumptionRequest(BaseModel):
    """Request schema for flow resumption"""
    resume_context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional context for flow resumption"
    )
    validate_state: bool = Field(
        default=True,
        description="Whether to validate flow state before resumption"
    )
    restore_agent_memory: bool = Field(
        default=True,
        description="Whether to restore agent memory during resumption"
    )

class FlowDeletionRequest(BaseModel):
    """Request schema for flow deletion"""
    force_delete: bool = Field(
        default=False,
        description="Force deletion even if flow is running"
    )
    cleanup_options: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Options for cleanup process"
    )
    reason: Optional[str] = Field(
        default="user_requested",
        description="Reason for deletion"
    )

class BulkFlowOperationRequest(BaseModel):
    """Request schema for bulk flow operations"""
    operation: str = Field(
        description="Operation to perform: 'delete', 'pause', or 'resume'"
    )
    session_ids: List[str] = Field(
        description="List of session IDs to operate on"
    )
    options: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Options for bulk operation"
    )

# ========================================
# RESPONSE SCHEMAS
# ========================================

class FlowInfo(BaseModel):
    """Basic flow information"""
    session_id: str
    flow_id: str
    current_phase: str
    status: str
    progress_percentage: float
    phase_completion: Dict[str, bool]
    crew_status: Dict[str, Any]
    created_at: str
    updated_at: str
    started_at: Optional[str] = None
    
    # CrewAI Flow specific data
    agent_insights: List[Dict[str, Any]]
    success_criteria: Dict[str, Any]
    errors: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    
    # Flow management capabilities
    can_resume: bool
    deletion_impact: Dict[str, Any]
    
    # Database integration status
    database_assets_created: List[str]
    database_integration_status: str

class IncompleteFlowResponse(BaseModel):
    """Response schema for incomplete flows endpoint"""
    success: bool
    flows: List[FlowInfo]
    count: int
    has_incomplete_flows: bool
    context: Dict[str, Any]

class FlowDetailsResponse(BaseModel):
    """Response schema for flow details endpoint"""
    success: bool
    flow: Dict[str, Any]  # Extended FlowInfo with additional details
    session_id: str

class FlowResumptionResponse(BaseModel):
    """Response schema for flow resumption"""
    success: bool
    message: str
    session_id: str
    current_phase: str
    progress_percentage: float
    estimated_completion: str
    resume_context: Dict[str, Any]

class FlowDeletionResponse(BaseModel):
    """Response schema for flow deletion"""
    success: bool
    message: str
    session_id: str
    cleanup_summary: Dict[str, Any]
    deletion_timestamp: str
    data_recovery_possible: bool

class BulkOperationResult(BaseModel):
    """Result for individual bulk operation"""
    session_id: str
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None

class BulkFlowOperationResponse(BaseModel):
    """Response schema for bulk flow operations"""
    success: bool
    operation: str
    total_requested: int
    successful_operations: int
    failed_operations: int
    results: List[BulkOperationResult]
    summary: str

# ========================================
# VALIDATION SCHEMAS
# ========================================

class FlowValidationResult(BaseModel):
    """Flow validation result"""
    can_resume: bool
    reason: str
    validation_errors: List[str]
    current_phase: Optional[str] = None
    progress_percentage: Optional[float] = None
    last_activity: Optional[str] = None

class NewFlowValidationResponse(BaseModel):
    """Response for new flow validation"""
    can_start_new_flow: bool
    blocking_flows_count: int
    message: str
    blocking_flows: Optional[List[Dict[str, Any]]] = None
    suggested_actions: Optional[List[str]] = None

# ========================================
# MANAGEMENT SCHEMAS
# ========================================

class FlowManagementInfo(BaseModel):
    """Comprehensive flow management information"""
    session_id: str
    flow_id: str
    current_phase: str
    status: str
    progress_percentage: float
    phase_completion: Dict[str, bool]
    can_resume: bool
    deletion_impact: Dict[str, Any]
    agent_insights: List[Dict[str, Any]]
    recent_errors: List[Dict[str, Any]]
    recent_warnings: List[Dict[str, Any]]
    created_at: str
    updated_at: str
    estimated_remaining_time: str
    crew_status: Dict[str, Any]
    database_integration_status: str

class CleanupImpactAnalysis(BaseModel):
    """Analysis of cleanup impact for flow deletion"""
    session_id: str
    flow_phase: str
    progress_percentage: float
    status: str
    data_to_delete: Dict[str, int]
    estimated_cleanup_time: str
    data_recovery_possible: bool
    warnings: List[str]
    recommendations: List[str]

# ========================================
# AUDIT SCHEMAS
# ========================================

class FlowDeletionAuditRecord(BaseModel):
    """Audit record for flow deletion"""
    session_id: str
    client_account_id: str
    engagement_id: str
    flow_id: str
    deleted_at: datetime
    deletion_reason: str
    force_delete: bool
    flow_state_snapshot: Dict[str, Any]
    cleanup_options: Dict[str, Any]
    user_id: Optional[str] = None
    admin_action: bool = False

# ========================================
# ERROR SCHEMAS
# ========================================

class FlowManagementError(BaseModel):
    """Error response for flow management operations"""
    success: bool = False
    error: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

# ========================================
# CONTEXT SCHEMAS
# ========================================

class FlowContext(BaseModel):
    """Flow context information"""
    client_account_id: str
    engagement_id: str
    user_id: Optional[str] = None
    session_id: str
    flow_id: str

class FlowStateSnapshot(BaseModel):
    """Snapshot of flow state for audit/backup purposes"""
    session_id: str
    flow_id: str
    current_phase: str
    status: str
    progress_percentage: float
    phase_completion: Dict[str, bool]
    crew_status: Dict[str, Any]
    field_mappings: Dict[str, Any]
    cleaned_data: List[Dict[str, Any]]
    asset_inventory: Dict[str, Any]
    dependencies: Dict[str, Any]
    technical_debt: Dict[str, Any]
    agent_insights: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    workflow_log: List[Dict[str, Any]]
    database_assets_created: List[str]
    shared_memory_id: str
    created_at: str
    updated_at: str 