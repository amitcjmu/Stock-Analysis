"""
Advanced Flow Management Schemas
Phase 4: Advanced Features & Production Readiness
Extracted from discovery_flow_schemas.py for better modularity
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# Re-define enums to avoid circular imports
from enum import Enum


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


class FlowContext(BaseModel):
    """Flow context information"""

    client_account_id: str
    engagement_id: str


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
