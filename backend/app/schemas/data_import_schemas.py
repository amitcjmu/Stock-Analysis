"""
Data Import Validation Schemas
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional, Literal
from datetime import datetime
from .flow import FlowType, FlowStatus

class ValidationAgentResult(BaseModel):
    """Result from a single validation agent"""
    agent_id: str
    agent_name: str
    validation: Literal['passed', 'failed', 'warning']
    confidence: float = Field(ge=0.0, le=1.0)
    message: str
    details: List[str] = []
    processing_time_seconds: Optional[float] = None

class SecurityAnalysisResult(BaseModel):
    """Security analysis specific results"""
    threat_level: Literal['low', 'medium', 'high', 'critical']
    detected_threats: List[str] = []
    security_score: float = Field(ge=0.0, le=1.0)
    recommendations: List[str] = []

class DataImportValidationRequest(BaseModel):
    """Request for data import validation"""
    category: Literal['cmdb', 'app-discovery', 'infrastructure', 'sensitive']
    filename: str
    file_size_mb: float
    content_type: str
    client_account_id: Optional[int] = None
    engagement_id: Optional[int] = None

class DataImportValidationResponse(BaseModel):
    """Response from data import validation"""
    success: bool
    file_status: Literal['approved', 'rejected', 'approved_with_warnings']
    validation_flow_id: str
    agent_results: List[ValidationAgentResult]
    security_clearances: Dict[str, bool]
    next_step: str
    message: str
    processing_time_seconds: Optional[float] = None

class FileMetadata(BaseModel):
    """File metadata for import requests"""
    filename: str
    size: int
    type: str

class UploadContext(BaseModel):
    """Context information for data upload"""
    intended_type: str
    validation_flow_id: Optional[str] = None  # Flow-based field name
    validation_upload_id: Optional[str] = None  # Alternative field name
    validation_id: Optional[str] = None  # Direct field name
    upload_timestamp: str
    
    def get_validation_id(self) -> str:
        """Get validation ID from any of the field names"""
        return (self.validation_id or 
                self.validation_upload_id or 
                self.validation_flow_id or 
                "")

class StoreImportRequest(BaseModel):
    """Request schema for storing import data"""
    file_data: List[Dict[str, Any]]
    metadata: FileMetadata
    upload_context: UploadContext
    client_id: Optional[str] = None
    engagement_id: Optional[str] = None

class ValidationFlow(BaseModel):
    """Complete validation flow data"""
    flow_id: str
    filename: str
    size_mb: float
    content_type: str
    category: str
    uploaded_by: int
    uploaded_at: datetime
    flow_type: FlowType = FlowType.DISCOVERY
    status: FlowStatus
    agent_results: List[ValidationAgentResult] = []
    security_analysis: Optional[SecurityAnalysisResult] = None
    completion_time: Optional[datetime] = None

class AgentConfiguration(BaseModel):
    """Configuration for a validation agent"""
    name: str
    role: str
    analysis_time_seconds: int
    categories: Optional[List[str]] = None
    max_file_size_mb: Optional[int] = None
    supported_types: Optional[List[str]] = None
    threat_patterns: Optional[List[str]] = None
    pii_patterns: Optional[List[str]] = None
    quality_thresholds: Optional[Dict[str, float]] = None
    regulations: Optional[List[str]] = None 