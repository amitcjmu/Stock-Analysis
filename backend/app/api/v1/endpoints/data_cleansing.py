"""
Data Cleansing API Endpoints

Provides endpoints for data cleansing analysis and results.
Integrates with the DataCleansingCrew for processing field mappings and providing insights.
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.core.context import get_current_context, RequestContext
from app.models.user import User
from app.core.auth import get_current_user
from app.repositories.discovery_flow_repository import DiscoveryFlowRepository
from app.repositories.data_import_repository import DataImportRepository
from app.repositories.field_mapping_repository import FieldMappingRepository

logger = logging.getLogger(__name__)

router = APIRouter()

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

class DataCleansingStats(BaseModel):
    """Data cleansing statistics"""
    total_records: int
    clean_records: int
    records_with_issues: int
    issues_by_severity: Dict[str, int]
    completion_percentage: float

@router.get(
    "/flows/{flow_id}/data-cleansing",
    response_model=DataCleansingAnalysis,
    summary="Get data cleansing analysis for a flow"
)
async def get_data_cleansing_analysis(
    flow_id: str,
    include_details: bool = Query(True, description="Include detailed issues and recommendations"),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
    current_user: User = Depends(get_current_user)
) -> DataCleansingAnalysis:
    """
    Get comprehensive data cleansing analysis for a discovery flow.
    
    Returns quality issues, recommendations, and field-level analysis.
    """
    try:
        logger.info(f"Getting data cleansing analysis for flow {flow_id}")
        
        # Get flow repository with proper context
        flow_repo = DiscoveryFlowRepository(db, context.client_account_id)
        
        # Verify flow exists and user has access
        flow = await flow_repo.get_by_flow_id(flow_id)
        if not flow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Flow {flow_id} not found"
            )
        
        # Get data import for this flow
        data_import_repo = DataImportRepository(db, context.client_account_id)
        data_imports = await data_import_repo.get_by_discovery_flow_id(flow_id)
        
        if not data_imports:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No data imports found for flow {flow_id}"
            )
        
        # Get field mappings
        field_mapping_repo = FieldMappingRepository(db, context.client_account_id)
        field_mappings = await field_mapping_repo.get_by_data_import_id(data_imports[0].id)
        
        # Perform data cleansing analysis
        analysis_result = await _perform_data_cleansing_analysis(
            flow_id=flow_id,
            data_imports=data_imports,
            field_mappings=field_mappings,
            include_details=include_details
        )
        
        logger.info(f"✅ Data cleansing analysis completed for flow {flow_id}")
        return analysis_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get data cleansing analysis for flow {flow_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get data cleansing analysis: {str(e)}"
        )

@router.get(
    "/flows/{flow_id}/data-cleansing/stats",
    response_model=DataCleansingStats,
    summary="Get data cleansing statistics"
)
async def get_data_cleansing_stats(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
    current_user: User = Depends(get_current_user)
) -> DataCleansingStats:
    """Get basic data cleansing statistics for a flow."""
    try:
        logger.info(f"Getting data cleansing stats for flow {flow_id}")
        
        # Get flow repository with proper context
        flow_repo = DiscoveryFlowRepository(db, context.client_account_id)
        
        # Verify flow exists
        flow = await flow_repo.get_by_flow_id(flow_id)
        if not flow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Flow {flow_id} not found"
            )
        
        # Get basic stats from data import
        data_import_repo = DataImportRepository(db, context.client_account_id)
        data_imports = await data_import_repo.get_by_discovery_flow_id(flow_id)
        
        if not data_imports:
            # Return empty stats if no data
            return DataCleansingStats(
                total_records=0,
                clean_records=0,
                records_with_issues=0,
                issues_by_severity={"low": 0, "medium": 0, "high": 0, "critical": 0},
                completion_percentage=0.0
            )
        
        # Calculate stats from first data import
        data_import = data_imports[0]
        total_records = len(data_import.raw_data.get("data", [])) if data_import.raw_data else 0
        
        # For now, return basic calculated stats
        # TODO: Integrate with actual data cleansing crew results
        clean_records = int(total_records * 0.85)  # Estimate 85% clean
        records_with_issues = total_records - clean_records
        
        return DataCleansingStats(
            total_records=total_records,
            clean_records=clean_records,
            records_with_issues=records_with_issues,
            issues_by_severity={
                "low": int(records_with_issues * 0.4),
                "medium": int(records_with_issues * 0.3), 
                "high": int(records_with_issues * 0.2),
                "critical": int(records_with_issues * 0.1)
            },
            completion_percentage=85.0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get data cleansing stats for flow {flow_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get data cleansing stats: {str(e)}"
        )

async def _perform_data_cleansing_analysis(
    flow_id: str,
    data_imports: List[Any],
    field_mappings: List[Any],
    include_details: bool = True
) -> DataCleansingAnalysis:
    """
    Perform data cleansing analysis on the imported data and field mappings.
    
    This function analyzes the data quality and provides recommendations.
    In the future, this should integrate with the DataCleansingCrew.
    """
    from datetime import datetime
    import uuid
    
    # Get the first data import (primary)
    data_import = data_imports[0] if data_imports else None
    raw_data = data_import.raw_data.get("data", []) if data_import and data_import.raw_data else []
    
    total_records = len(raw_data)
    total_fields = len(field_mappings)
    
    # Mock quality issues for demo (replace with actual data cleansing crew analysis)
    quality_issues = []
    recommendations = []
    field_quality_scores = {}
    
    if include_details and field_mappings:
        # Generate sample quality issues based on field mappings
        for i, mapping in enumerate(field_mappings[:5]):  # Limit to first 5 for demo
            source_field = mapping.source_field
            
            # Mock quality issue
            quality_issues.append(DataQualityIssue(
                id=str(uuid.uuid4()),
                field_name=source_field,
                issue_type="missing_values",
                severity="medium",
                description=f"Field '{source_field}' has missing values in some records",
                affected_records=max(1, int(total_records * 0.1)),
                recommendation=f"Consider filling missing values for '{source_field}' with default values or remove incomplete records",
                auto_fixable=True
            ))
            
            # Mock field quality score
            field_quality_scores[source_field] = round(85.0 + (i * 2), 1)
        
        # Generate sample recommendations
        recommendations.extend([
            DataCleansingRecommendation(
                id=str(uuid.uuid4()),
                category="standardization",
                title="Standardize date formats",
                description="Multiple date formats detected. Standardize to ISO 8601 format",
                priority="high",
                impact="Improves data consistency and query performance",
                effort_estimate="2-4 hours",
                fields_affected=["created_date", "modified_date", "last_seen"]
            ),
            DataCleansingRecommendation(
                id=str(uuid.uuid4()),
                category="validation",
                title="Validate server names",
                description="Some server names contain invalid characters or inconsistent naming",
                priority="medium",
                impact="Ensures proper asset identification",
                effort_estimate="1-2 hours",
                fields_affected=["server_name", "hostname"]
            )
        ])
    
    # Calculate overall quality score
    quality_score = 85.0  # Mock score
    if field_quality_scores:
        quality_score = sum(field_quality_scores.values()) / len(field_quality_scores)
    
    return DataCleansingAnalysis(
        flow_id=flow_id,
        analysis_timestamp=datetime.utcnow().isoformat(),
        total_records=total_records,
        total_fields=total_fields,
        quality_score=round(quality_score, 1),
        issues_count=len(quality_issues),
        recommendations_count=len(recommendations),
        quality_issues=quality_issues,
        recommendations=recommendations,
        field_quality_scores=field_quality_scores,
        processing_status="completed"
    )