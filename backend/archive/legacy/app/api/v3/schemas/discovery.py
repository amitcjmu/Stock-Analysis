"""
API v3 Discovery Schemas
Comprehensive Pydantic schemas for all discovery flow operations.
"""

from pydantic import BaseModel, Field, field_validator
from uuid import UUID
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum
import uuid


class FlowPhase(str, Enum):
    """Discovery flow phases"""
    INITIALIZATION = "initialization"
    DATA_VALIDATION = "data_validation"
    FIELD_MAPPING = "field_mapping"
    DATA_CLEANSING = "data_cleansing"
    INVENTORY_BUILDING = "inventory_building"
    APP_SERVER_DEPENDENCIES = "app_server_dependencies"
    APP_APP_DEPENDENCIES = "app_app_dependencies"
    TECHNICAL_DEBT = "technical_debt"
    COMPLETED = "completed"


class FlowStatus(str, Enum):
    """Flow execution status"""
    INITIALIZING = "initializing"
    INITIALIZED = "initialized"
    IN_PROGRESS = "in_progress"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExecutionMode(str, Enum):
    """Flow execution mode"""
    CREWAI = "crewai"
    DATABASE = "database"
    HYBRID = "hybrid"


class AssetType(str, Enum):
    """Asset type classification"""
    SERVER = "server"
    APPLICATION = "application"
    DATABASE = "database"
    NETWORK = "network"
    STORAGE = "storage"
    CONTAINER = "container"
    VIRTUAL_MACHINE = "virtual_machine"
    SERVICE = "service"
    UNKNOWN = "unknown"


class MigrationComplexity(str, Enum):
    """Migration complexity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FlowCreate(BaseModel):
    """Request schema for creating a flow"""
    name: str = Field(..., description="Flow name", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Flow description", max_length=1000)
    raw_data: Optional[List[Dict[str, Any]]] = Field(None, description="Raw CMDB data")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    execution_mode: ExecutionMode = Field(default=ExecutionMode.HYBRID, description="Execution mode")
    data_import_id: Optional[str] = Field(None, description="Data import ID for linking")


class FlowUpdate(BaseModel):
    """Request schema for updating a flow"""
    name: Optional[str] = Field(None, description="Flow name", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Flow description", max_length=1000)
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    status: Optional[FlowStatus] = Field(None, description="Flow status")
    current_phase: Optional[FlowPhase] = Field(None, description="Current phase")


class PhaseExecution(BaseModel):
    """Request schema for executing a specific phase"""
    phase: FlowPhase = Field(..., description="Phase to execute")
    data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Phase-specific data")
    execution_mode: ExecutionMode = Field(default=ExecutionMode.HYBRID, description="Execution mode")
    human_input: Optional[Dict[str, Any]] = Field(None, description="Human input for the phase")


class PhaseStatus(BaseModel):
    """Phase execution status"""
    phase: FlowPhase
    status: FlowStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress_percentage: float = Field(ge=0, le=100, default=0.0)
    agent_insights: List[Dict[str, Any]] = Field(default_factory=list)
    results: Optional[Dict[str, Any]] = None
    errors: List[str] = Field(default_factory=list)


class AssetInfo(BaseModel):
    """Asset information schema"""
    asset_name: str = Field(..., description="Asset name")
    asset_type: AssetType = Field(..., description="Asset type")
    ip_address: Optional[str] = Field(None, description="IP address")
    operating_system: Optional[str] = Field(None, description="Operating system")
    environment: Optional[str] = Field(None, description="Environment/tier")
    location: Optional[str] = Field(None, description="Physical location")
    business_owner: Optional[str] = Field(None, description="Business owner")
    migration_complexity: Optional[MigrationComplexity] = Field(None, description="Migration complexity")
    migration_priority: Optional[int] = Field(None, description="Migration priority", ge=1, le=5)
    confidence_score: Optional[float] = Field(None, description="Classification confidence", ge=0.0, le=1.0)


class FlowResponse(BaseModel):
    """Response schema for flow operations"""
    flow_id: UUID
    name: str
    description: Optional[str] = None
    status: FlowStatus
    current_phase: FlowPhase
    progress_percentage: float = Field(ge=0, le=100)
    created_at: datetime
    updated_at: datetime
    
    # Multi-tenant context
    client_account_id: UUID
    engagement_id: UUID
    user_id: Optional[UUID] = None
    
    # Phase tracking
    phases_completed: List[FlowPhase] = Field(default_factory=list)
    phases_status: Dict[str, PhaseStatus] = Field(default_factory=dict)
    
    # Execution tracking
    execution_mode: ExecutionMode
    crewai_status: Optional[str] = None
    database_status: Optional[str] = None
    
    # Data and results
    metadata: Dict[str, Any] = Field(default_factory=dict)
    field_mapping: Optional[Dict[str, Any]] = None
    data_cleansing_results: Optional[Dict[str, Any]] = None
    agent_insights: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Statistics
    records_processed: int = 0
    records_total: int = 0
    records_valid: int = 0
    records_failed: int = 0
    assets_discovered: int = 0
    dependencies_mapped: int = 0
    
    # Asset inventory
    assets: List[AssetInfo] = Field(default_factory=list)


class FlowListResponse(BaseModel):
    """Response schema for flow list operations"""
    flows: List[FlowResponse]
    total: int
    page: int = 1
    page_size: int = 20
    has_next: bool = False
    has_previous: bool = False


class FlowStatusResponse(BaseModel):
    """Response schema for flow status operations"""
    flow_id: UUID
    status: FlowStatus
    current_phase: FlowPhase
    progress_percentage: float = Field(ge=0, le=100)
    updated_at: datetime
    
    # Real-time status
    is_running: bool = False
    is_paused: bool = False
    can_resume: bool = False
    can_cancel: bool = False
    
    # Phase details
    current_phase_status: Optional[PhaseStatus] = None
    next_phase: Optional[FlowPhase] = None
    
    # Execution details
    execution_mode: ExecutionMode
    crewai_status: Optional[str] = None
    database_status: Optional[str] = None
    
    # Latest insights
    latest_insights: List[Dict[str, Any]] = Field(default_factory=list)


class FlowExecutionResponse(BaseModel):
    """Response schema for flow execution operations"""
    success: bool
    flow_id: UUID
    action: str
    status: FlowStatus
    message: str
    timestamp: datetime
    
    # Phase execution details
    phase: Optional[FlowPhase] = None
    phase_status: Optional[PhaseStatus] = None
    next_phase: Optional[FlowPhase] = None
    
    # Execution tracking
    crewai_execution: Optional[str] = None
    database_execution: Optional[str] = None
    
    # Results
    results: Optional[Dict[str, Any]] = None
    agent_insights: List[Dict[str, Any]] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


class FlowDeletionResponse(BaseModel):
    """Response schema for flow deletion operations"""
    success: bool
    flow_id: UUID
    action: str = "deleted"
    force_delete: bool = False
    message: str
    timestamp: datetime
    
    # Cleanup details
    cleanup_summary: Dict[str, Any] = Field(default_factory=dict)
    crewai_cleanup: Optional[Dict[str, Any]] = None
    database_cleanup: Optional[Dict[str, Any]] = None


class FlowHealthResponse(BaseModel):
    """Response schema for flow health check"""
    status: str = "healthy"
    service: str = "discovery-flow-v3"
    version: str = "3.0.0"
    timestamp: datetime
    
    # Component health
    components: Dict[str, bool] = Field(default_factory=dict)
    architecture: str = "hybrid_crewai_postgresql"
    
    # Performance metrics
    active_flows: int = 0
    total_flows: int = 0
    avg_response_time_ms: Optional[float] = None


# Pagination and filtering schemas
class FlowFilterParams(BaseModel):
    """Parameters for filtering flows"""
    status: Optional[FlowStatus] = None
    current_phase: Optional[FlowPhase] = None
    execution_mode: Optional[ExecutionMode] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    updated_after: Optional[datetime] = None
    updated_before: Optional[datetime] = None


class PaginationParams(BaseModel):
    """Parameters for pagination"""
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    sort_by: str = Field(default="created_at", description="Sort field")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$", description="Sort order")


# Resume and control schemas
class FlowResumeRequest(BaseModel):
    """Request schema for resuming flows"""
    resume_context: Optional[Dict[str, Any]] = None
    target_phase: Optional[FlowPhase] = None
    human_input: Optional[Dict[str, Any]] = None


class FlowPauseRequest(BaseModel):
    """Request schema for pausing flows"""
    reason: str = Field(default="user_requested", description="Reason for pausing")
    save_state: bool = Field(default=True, description="Save current state")


# Asset promotion schemas
class AssetPromotionResponse(BaseModel):
    """Response schema for asset promotion operations"""
    success: bool
    flow_id: UUID
    action: str = "asset_promotion"
    message: str
    timestamp: datetime
    
    # Promotion statistics
    assets_promoted: int = 0
    assets_skipped: int = 0
    errors: int = 0
    statistics: Dict[str, Any] = Field(default_factory=dict)


# Note: UUID validation is handled by Pydantic automatically with UUID field type


# === New Schemas for Missing Functionality ===

class FlowValidationRequest(BaseModel):
    """Request for flow validation"""
    comprehensive: bool = Field(default=True, description="Perform comprehensive validation")
    check_persistence: bool = Field(default=True, description="Check persistence layer")
    check_crewai_state: bool = Field(default=True, description="Check CrewAI state")


class FlowValidationResponse(BaseModel):
    """Response for flow validation"""
    flow_id: UUID
    is_valid: bool
    validation_timestamp: datetime
    issues: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    persistence_status: Dict[str, Any] = Field(default_factory=dict)
    crewai_state_status: Dict[str, Any] = Field(default_factory=dict)
    recommendations: List[str] = Field(default_factory=list)


class FlowRecoveryRequest(BaseModel):
    """Request for flow recovery"""
    recovery_strategy: str = Field(default="latest_checkpoint", description="Recovery strategy")
    force_recovery: bool = Field(default=False, description="Force recovery even if current state exists")


class FlowRecoveryResponse(BaseModel):
    """Response for flow recovery"""
    flow_id: UUID
    recovery_successful: bool
    recovery_strategy_used: str
    recovered_from_checkpoint: Optional[datetime] = None
    recovery_timestamp: datetime
    state_before_recovery: Optional[Dict[str, Any]] = None
    state_after_recovery: Optional[Dict[str, Any]] = None
    message: str


class UserApprovalRequest(BaseModel):
    """Request for user approval"""
    approved: bool = Field(..., description="Whether user approves proceeding")
    phase_to_approve: str = Field(..., description="Phase that needs approval")
    user_feedback: Optional[str] = Field(default=None, description="User feedback or comments")
    modifications: Optional[Dict[str, Any]] = Field(default=None, description="User modifications to flow data")


class UserApprovalResponse(BaseModel):
    """Response for user approval"""
    flow_id: UUID
    approval_recorded: bool
    approved_phase: str
    next_phase: Optional[str] = None
    flow_resumed: bool
    approval_timestamp: datetime
    message: str


class ValidationReportRequest(BaseModel):
    """Request for validation report"""
    include_details: bool = Field(default=True, description="Include detailed validation results")
    phase: Optional[str] = Field(default=None, description="Specific phase to validate")


class ValidationReportResponse(BaseModel):
    """Response for validation report"""
    flow_id: UUID
    validation_status: str
    phase_validations: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    data_quality_score: float
    security_assessment: Dict[str, Any] = Field(default_factory=dict)
    recommendations: List[str] = Field(default_factory=list)
    awaiting_approval: bool
    report_timestamp: datetime


class FlowCleanupRequest(BaseModel):
    """Request for flow cleanup"""
    older_than_days: int = Field(default=30, description="Clean flows older than N days")
    status_filter: Optional[List[FlowStatus]] = Field(default=None, description="Only clean flows with these statuses")
    dry_run: bool = Field(default=False, description="Preview what would be cleaned without deleting")


class FlowCleanupResponse(BaseModel):
    """Response for flow cleanup"""
    flows_cleaned: int
    flows_identified: int
    cleanup_timestamp: datetime
    dry_run: bool
    cleaned_flow_ids: List[UUID] = Field(default_factory=list)
    space_reclaimed_mb: Optional[float] = None
    message: str


class BulkValidationRequest(BaseModel):
    """Request for bulk validation"""
    flow_ids: List[UUID] = Field(..., description="List of flow IDs to validate")
    validation_type: str = Field(default="basic", description="Type of validation: basic, comprehensive")


class BulkValidationResponse(BaseModel):
    """Response for bulk validation"""
    total_flows: int
    valid_flows: int
    invalid_flows: int
    validation_results: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    validation_timestamp: datetime
    duration_seconds: float