"""
Pydantic schemas for discovery-related data structures.
"""
import uuid
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class CMDBData(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    data: List[Dict[str, Any]]

class FieldMapping(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_field: str
    target_field: str
    confidence: float

class FieldMappingUpdate(BaseModel):
    source_field: str
    target_field: str

class FieldMappingSuggestion(BaseModel):
    source_field: str
    suggested_target: str
    confidence: float

class FieldMappingAnalysis(BaseModel):
    unmapped_fields: List[str]
    suggestions: List[FieldMappingSuggestion]

class FieldMappingResponse(BaseModel):
    mappings: List[FieldMapping]
    analysis: FieldMappingAnalysis

class DiscoveredAsset(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    asset_name: str
    asset_type: str
    details: Dict[str, Any]

# Real-time Processing Schemas
class ProcessingUpdate(BaseModel):
    id: str
    timestamp: str
    phase: str
    agent_name: str
    update_type: str  # 'progress' | 'validation' | 'insight' | 'error' | 'warning' | 'success'
    message: str
    details: Optional[Dict[str, Any]] = None

class ValidationStatus(BaseModel):
    format_valid: bool
    security_scan_passed: bool
    data_quality_score: float
    issues_found: List[str]

class AgentStatus(BaseModel):
    status: str  # 'idle' | 'processing' | 'completed' | 'error'
    confidence: float
    insights_generated: int
    clarifications_pending: int

class ProcessingStatusResponse(BaseModel):
    flow_id: str
    phase: str
    status: str  # 'initializing' | 'processing' | 'validating' | 'completed' | 'failed'
    progress_percentage: float
    records_processed: int
    records_total: int
    records_failed: int
    validation_status: ValidationStatus
    agent_status: Dict[str, AgentStatus]
    recent_updates: List[ProcessingUpdate]
    estimated_completion: Optional[str] = None
    last_update: str

class SecurityScan(BaseModel):
    status: str
    issues: List[str]
    scan_time: str
    threat_level: str

class FormatValidation(BaseModel):
    status: str
    errors: List[str]
    warnings: List[str]
    validation_time: str

class DataQuality(BaseModel):
    score: float
    metrics: Dict[str, float]
    issues: List[str]
    assessment_time: str

class ValidationStatusResponse(BaseModel):
    flow_id: str
    overall_status: str  # 'passed' | 'failed' | 'pending'
    security_scan: SecurityScan
    format_validation: FormatValidation
    data_quality: DataQuality
    last_validation: str
    # Progress tracking fields
    validation_progress: float = Field(default=0.0, description="Validation progress percentage (0-100)")
    agents_completed: int = Field(default=0, description="Number of validation agents completed")
    total_agents: int = Field(default=4, description="Total number of validation agents")
    agent_status: Optional[Dict[str, Dict[str, Any]]] = Field(default=None, description="Individual agent status details") 