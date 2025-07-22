"""
CMDB Discovery Data Models
Pydantic models for request/response validation.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class CMDBAnalysisRequest(BaseModel):
    """Request model for CMDB analysis."""
    filename: str
    content: str
    fileType: str


class CMDBProcessingRequest(BaseModel):
    """Request model for CMDB data processing."""
    filename: str
    data: List[Dict[str, Any]]
    projectInfo: Optional[Dict[str, Any]] = None


class CMDBFeedbackRequest(BaseModel):
    """Request model for user feedback submission."""
    filename: str
    originalAnalysis: Dict[str, Any]
    userCorrections: Dict[str, Any]
    assetTypeOverride: Optional[str] = None


class PageFeedbackRequest(BaseModel):
    """Request model for general page feedback."""
    page: str
    rating: int
    comment: str
    category: str = 'general'
    breadcrumb: str = ''
    timestamp: str


class DataQualityResult(BaseModel):
    """Data quality assessment result."""
    score: int
    issues: List[str]
    recommendations: List[str]


class AssetCoverage(BaseModel):
    """Asset type coverage statistics."""
    applications: int
    servers: int
    databases: int
    dependencies: int


class CMDBAnalysisResponse(BaseModel):
    """Response model for CMDB analysis."""
    status: str
    dataQuality: DataQualityResult
    coverage: AssetCoverage
    missingFields: List[str]
    requiredProcessing: List[str]
    readyForImport: bool
    preview: Optional[List[Dict[str, Any]]] = None 