"""
Discovery Flow Management Schemas
Enhanced Pydantic models for CrewAI Flow state management and flow lifecycle operations
Provides comprehensive validation and type safety for flow management APIs
Phase 4: Advanced Features & Production Readiness
"""

from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum

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

class RecoveryOptions(BaseModel):
    """Advanced recovery options"""
    repair_corrupted_state: bool = True
    reconstruct_agent_memory: bool = True
    validate_data_consistency: bool = True
    optimize_for_resumption: bool = True

class AdvancedRecoveryRequest(BaseModel):
    """Request for advanced flow recovery"""
    recovery_options: RecoveryOptions = Field(default_factory=RecoveryOptions)

class RecoveryAction(BaseModel):
    """Individual recovery action"""
    action_type: str
    description: str
    success: bool
    details: Optional[Dict[str, Any]] = None

class PerformanceMetrics(BaseModel):
    """Performance metrics"""
    recovery_time_ms: float = 0
    data_integrity_score: float = Field(ge=0, le=100, default=100)
    agent_memory_completeness: float = Field(ge=0, le=100, default=100)

class AdvancedRecoveryResponse(BaseModel):
    """Response for advanced flow recovery"""
    success: bool
    flow_id: str
    recovery_actions: List[str]
    flow_state: Dict[str, Any]
    performance_metrics: PerformanceMetrics
    recovered_at: str

class ExpiredFlow(BaseModel):
    """Expired flow information"""
    flow_id: str
    current_phase: FlowPhase
    status: FlowStatus
    last_activity: str
    days_since_activity: int
    auto_cleanup_eligible: bool = True
    deletion_impact: Dict[str, Any] = Field(default_factory=dict)

class ExpiredFlowsResponse(BaseModel):
    """Response for expired flows query"""
    expired_flows: List[ExpiredFlow]
    total_expired: int
    expiration_hours: int
    context: FlowContext

class AutoCleanupRequest(BaseModel):
    """Request for auto-cleanup of expired flows"""
    dry_run: bool = True
    expiration_hours: Optional[int] = None
    force_cleanup: bool = False

class CleanupMetrics(BaseModel):
    """Cleanup performance metrics"""
    total_duration_ms: float
    flows_per_second: float

class DataCleanedSummary(BaseModel):
    """Summary of data cleaned during auto-cleanup"""
    flows_deleted: int = 0
    assets_cleaned: int = 0
    memory_freed_mb: float = 0

class AutoCleanupResponse(BaseModel):
    """Response for auto-cleanup operation"""
    dry_run: bool
    expired_flows_found: int
    cleanup_successful: List[str] = Field(default_factory=list)
    cleanup_failed: List[str] = Field(default_factory=list)
    total_data_cleaned: DataCleanedSummary
    performance_metrics: CleanupMetrics
    cleanup_completed_at: str

class QueryOptimization(BaseModel):
    """Query optimization recommendation"""
    type: str
    description: str
    recommendation: str
    priority: Optional[str] = "medium"

class IndexRecommendation(BaseModel):
    """Database index recommendation"""
    type: str
    table: str
    columns: List[str]
    reason: str
    priority: str = "medium"

class PerformanceImprovement(BaseModel):
    """Performance improvement metrics"""
    incomplete_flow_query_ms: float = 0
    flows_found: int = 0
    state_update_ms: Optional[float] = None

class PerformanceOptimizationResponse(BaseModel):
    """Response for performance optimization analysis"""
    query_optimizations: List[QueryOptimization] = Field(default_factory=list)
    index_recommendations: List[IndexRecommendation] = Field(default_factory=list)
    performance_improvements: Dict[str, Any] = Field(default_factory=dict)
    analysis_completed_at: str

# === PHASE 4: MONITORING SCHEMAS ===

class SystemCapabilities(BaseModel):
    """System capabilities status"""
    crewai_available: bool
    advanced_recovery: bool = True
    bulk_operations: bool = True
    auto_cleanup: bool = True
    performance_optimization: bool = True

class HealthRecommendation(BaseModel):
    """Health check recommendation"""
    type: str
    message: str
    priority: str = "medium"

class FlowStatistics(BaseModel):
    """Flow management statistics"""
    incomplete_flows: int = 0
    expired_flows: int = 0
    total_managed_flows: int = 0

class AdvancedHealthResponse(BaseModel):
    """Advanced health check response"""
    status: str
    timestamp: str
    flow_statistics: FlowStatistics
    system_capabilities: SystemCapabilities
    recommendations: List[HealthRecommendation] = Field(default_factory=list)

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