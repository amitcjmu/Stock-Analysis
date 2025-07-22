"""
Pydantic schemas for discovery flow service operations.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class FlowCreationRequest(BaseModel):
    """Request model for creating discovery flows."""
    
    flow_id: str = Field(..., description="CrewAI flow identifier")
    raw_data: List[Dict[str, Any]] = Field(..., description="Raw discovery data")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Flow metadata")
    data_import_id: Optional[str] = Field(None, description="Data import identifier for linking")
    user_id: Optional[str] = Field(None, description="User creating the flow")


class PhaseCompletionRequest(BaseModel):
    """Request model for updating phase completion."""
    
    flow_id: str = Field(..., description="Discovery flow identifier")
    phase: str = Field(..., description="Phase name to update")
    phase_data: Dict[str, Any] = Field(..., description="Phase completion data")
    crew_status: Optional[Dict[str, Any]] = Field(None, description="CrewAI crew status")
    agent_insights: Optional[List[Dict[str, Any]]] = Field(None, description="Agent insights from phase")


class AssetValidationRequest(BaseModel):
    """Request model for asset validation operations."""
    
    asset_id: str = Field(..., description="Asset identifier")
    validation_status: str = Field(..., description="Validation status")
    validation_results: Optional[Dict[str, Any]] = Field(None, description="Validation results data")


class BulkAssetValidationRequest(BaseModel):
    """Request model for bulk asset validation."""
    
    asset_ids: List[str] = Field(..., description="List of asset identifiers")
    validation_status: str = Field(..., description="Validation status to apply")
    validation_results: Optional[Dict[str, Any]] = Field(None, description="Common validation results")


class FlowSummaryResponse(BaseModel):
    """Response model for flow summary information."""
    
    flow_info: Dict[str, Any] = Field(..., description="Basic flow information")
    phase_completion: Dict[str, Any] = Field(..., description="Phase completion status")
    assets: Dict[str, Any] = Field(..., description="Asset statistics")
    progress_analysis: Dict[str, Any] = Field(..., description="Progress analysis")
    quality_assessment: Dict[str, Any] = Field(..., description="Quality assessment")
    timestamps: Dict[str, Optional[str]] = Field(..., description="Flow timestamps")
    crewai_integration: Dict[str, Any] = Field(..., description="CrewAI integration status")


class MultiFlowSummaryResponse(BaseModel):
    """Response model for multi-flow summary statistics."""
    
    overview: Dict[str, Any] = Field(..., description="High-level overview")
    flow_status_distribution: Dict[str, int] = Field(..., description="Flow status counts")
    phase_completion: Dict[str, Any] = Field(..., description="Phase completion statistics")
    quality_metrics: Dict[str, Any] = Field(..., description="Quality metrics across flows")
    performance_indicators: Dict[str, Any] = Field(..., description="Performance indicators")


class FlowHealthReportResponse(BaseModel):
    """Response model for flow health reports."""
    
    flow_id: str = Field(..., description="Discovery flow identifier")
    overall_health: str = Field(..., description="Overall health status")
    health_score: float = Field(..., description="Numeric health score")
    health_indicators: List[Dict[str, Any]] = Field(..., description="Health indicators found")
    recommendations: List[str] = Field(..., description="Health improvement recommendations")
    metrics: Dict[str, float] = Field(..., description="Health metrics")
    generated_at: str = Field(..., description="Report generation timestamp")


class AssetFilterCriteria(BaseModel):
    """Model for asset filtering criteria."""
    
    asset_type: Optional[str] = Field(None, description="Filter by asset type")
    validation_status: Optional[str] = Field(None, description="Filter by validation status")
    min_quality_score: Optional[float] = Field(None, description="Minimum quality score")
    max_quality_score: Optional[float] = Field(None, description="Maximum quality score")
    min_confidence_score: Optional[float] = Field(None, description="Minimum confidence score")
    max_confidence_score: Optional[float] = Field(None, description="Maximum confidence score")
    created_after: Optional[datetime] = Field(None, description="Created after date")
    created_before: Optional[datetime] = Field(None, description="Created before date")


class CrewAIStateSync(BaseModel):
    """Model for CrewAI state synchronization."""
    
    flow_id: str = Field(..., description="Discovery flow identifier")
    crewai_state: Dict[str, Any] = Field(..., description="CrewAI flow state")
    phase: Optional[str] = Field(None, description="Current phase")
    force_sync: bool = Field(False, description="Force synchronization even if conflicts exist")


class CrewAIExport(BaseModel):
    """Model for CrewAI flow export data."""
    
    flow_id: str = Field(..., description="Discovery flow identifier")
    current_phase: str = Field(..., description="Current flow phase")
    flow_status: str = Field(..., description="Flow status")
    progress_percentage: Optional[float] = Field(None, description="Progress percentage")
    phase_completion: Dict[str, bool] = Field(..., description="Phase completion status")
    raw_data: List[Dict[str, Any]] = Field(..., description="Raw flow data")
    metadata: Dict[str, Any] = Field(..., description="Flow metadata")
    phase_data: Dict[str, Any] = Field(..., description="Phase-specific data")
    crew_status: Dict[str, Any] = Field(..., description="Crew status information")
    agent_insights: List[Dict[str, Any]] = Field(..., description="Agent insights")
    timestamps: Dict[str, Optional[str]] = Field(..., description="Flow timestamps")


class ValidationReport(BaseModel):
    """Model for CrewAI state validation reports."""
    
    is_synced: bool = Field(..., description="Whether state is properly synced")
    discrepancies: List[Dict[str, Any]] = Field(..., description="Found discrepancies")
    sync_quality: str = Field(..., description="Overall sync quality rating")
    last_database_update: Optional[str] = Field(None, description="Last database update timestamp")
    validation_timestamp: str = Field(..., description="Validation execution timestamp")




class AssetQualityUpdate(BaseModel):
    """Model for updating asset quality scores."""
    
    asset_id: str = Field(..., description="Asset identifier")
    quality_score: float = Field(..., ge=0.0, le=1.0, description="Quality score (0.0-1.0)")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0.0-1.0)")


class FlowResponse(BaseModel):
    """Generic response model for discovery flow operations."""
    
    flow_id: str = Field(..., description="Discovery flow identifier")
    status: str = Field(..., description="Flow status")
    current_phase: str = Field(..., description="Current flow phase")
    progress_percentage: Optional[float] = Field(None, description="Progress percentage")
    asset_count: int = Field(..., description="Number of assets in flow")
    phase_completion: Dict[str, bool] = Field(..., description="Phase completion status")
    timestamps: Dict[str, Optional[str]] = Field(..., description="Flow timestamps")


class AssetStatistics(BaseModel):
    """Model for asset statistics and metrics."""
    
    total_count: int = Field(..., description="Total number of assets")
    type_distribution: Dict[str, int] = Field(..., description="Asset count by type")
    validation_status_distribution: Dict[str, int] = Field(..., description="Asset count by validation status")
    avg_quality_score: float = Field(..., description="Average quality score")
    avg_confidence_score: float = Field(..., description="Average confidence score")
    quality_metrics: Dict[str, int] = Field(..., description="Quality-related metrics")


class FlowListResponse(BaseModel):
    """Response model for flow list operations."""
    
    flows: List[FlowResponse] = Field(..., description="List of discovery flows")
    total_count: int = Field(..., description="Total number of flows")
    active_count: int = Field(..., description="Number of active flows")
    completed_count: int = Field(..., description="Number of completed flows")
    summary_statistics: Dict[str, Any] = Field(..., description="Summary statistics across flows")


class AssetResponse(BaseModel):
    """Response model for asset operations."""
    
    asset_id: str = Field(..., description="Asset identifier")
    asset_name: str = Field(..., description="Asset name")
    asset_type: str = Field(..., description="Asset type")
    validation_status: str = Field(..., description="Validation status")
    quality_score: Optional[float] = Field(None, description="Quality score")
    confidence_score: Optional[float] = Field(None, description="Confidence score")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")


class OperationResult(BaseModel):
    """Generic operation result model."""
    
    success: bool = Field(..., description="Whether operation succeeded")
    operation: str = Field(..., description="Operation performed")
    flow_id: Optional[str] = Field(None, description="Affected flow ID")
    asset_id: Optional[str] = Field(None, description="Affected asset ID")
    message: str = Field(..., description="Operation result message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional operation details")
    timestamp: str = Field(..., description="Operation timestamp")


class FlowPhaseData(BaseModel):
    """Model for flow phase-specific data."""
    
    phase_name: str = Field(..., description="Phase name")
    is_completed: bool = Field(..., description="Whether phase is completed")
    completion_timestamp: Optional[str] = Field(None, description="Phase completion timestamp")
    phase_data: Dict[str, Any] = Field(..., description="Phase-specific data")
    crew_status: Optional[Dict[str, Any]] = Field(None, description="Crew status for phase")
    agent_insights: Optional[List[Dict[str, Any]]] = Field(None, description="Agent insights from phase")


class ProgressAnalysis(BaseModel):
    """Model for flow progress analysis."""
    
    completion_rate: float = Field(..., description="Overall completion rate percentage")
    current_phase: str = Field(..., description="Current active phase")
    next_steps: List[str] = Field(..., description="Recommended next steps")
    potential_blockers: List[str] = Field(..., description="Potential blocking issues")
    estimated_completion: str = Field(..., description="Estimated completion timeframe")