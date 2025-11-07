"""
Data Cleansing API - Base Module
Common imports, router, and schema models for data cleansing endpoints.
"""

import logging
from typing import Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Create router for data cleansing endpoints
router = APIRouter()


# Request Models
class TriggerDataCleansingRequest(BaseModel):
    """Request to trigger data cleansing analysis"""

    force_refresh: bool = False
    include_agent_analysis: bool = True


class ResolveQualityIssueRequest(BaseModel):
    """Request to resolve a quality issue"""

    status: str  # 'resolved', 'ignored'
    resolution_notes: Optional[str] = None


# Response Models
class DataQualityIssue(BaseModel):
    """Data quality issue identified during cleansing analysis"""

    id: str
    field_name: str
    issue_type: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    description: str
    affected_records: int
    recommendation: str
    auto_fixable: bool = False
    status: Optional[str] = None  # 'pending', 'resolved', 'ignored'


class DataCleansingRecommendation(BaseModel):
    """Data cleansing recommendation"""

    id: str
    category: str  # 'standardization', 'validation', 'enrichment', 'deduplication'
    title: str
    description: str
    priority: str  # 'low', 'medium', 'high'
    impact: str
    effort_estimate: str
    fields_affected: List[str]
    # Additional fields for frontend compatibility (Issue #875, #876)
    confidence: Optional[float] = 0.85  # 0.0 to 1.0 range, default 85% confidence
    status: str = "pending"  # 'pending' | 'applied' | 'rejected'
    agent_source: Optional[str] = "Data Quality Agent"
    implementation_steps: Optional[List[str]] = []


class DataCleansingAnalysis(BaseModel):
    """Complete data cleansing analysis results"""

    flow_id: str
    analysis_timestamp: str
    total_records: int
    total_fields: int
    quality_score: float  # 0-100
    issues_count: int
    recommendations_count: int
    quality_issues: List[DataQualityIssue]
    recommendations: List[DataCleansingRecommendation]
    field_quality_scores: Dict[str, float]
    processing_status: str
    source: Optional[str] = None  # "agent", "fallback", "mock" to indicate data source


class DataCleansingStats(BaseModel):
    """Data cleansing statistics"""

    total_records: int
    clean_records: int
    records_with_issues: int
    issues_by_severity: Dict[str, int]
    completion_percentage: float


class ResolveQualityIssueResponse(BaseModel):
    """Response after resolving a quality issue"""

    success: bool
    message: str
    issue_id: str
    resolution_status: str
    resolved_at: str
