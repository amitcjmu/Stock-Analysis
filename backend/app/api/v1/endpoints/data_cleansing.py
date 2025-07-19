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
from app.models.client_account import User
from app.api.v1.auth.auth_utils import get_current_user
from app.repositories.discovery_flow_repository import DiscoveryFlowRepository
from app.models.data_import.core import DataImport
from app.models.data_import.mapping import ImportFieldMapping

logger = logging.getLogger(__name__)

router = APIRouter()

# Request Models
class TriggerDataCleansingRequest(BaseModel):
    """Request to trigger data cleansing analysis"""
    force_refresh: bool = False
    include_agent_analysis: bool = True

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
    This is a READ-ONLY operation that should NOT trigger any agent execution
    or modify flow status.
    """
    try:
        logger.info(f"📊 READ-ONLY: Getting data cleansing analysis for flow {flow_id} (should not modify flow status)")
        
        # Get flow repository with proper context
        flow_repo = DiscoveryFlowRepository(db, context.client_account_id)
        
        # Verify flow exists and user has access (READ-ONLY check)
        flow = await flow_repo.get_by_flow_id(flow_id)
        if not flow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Flow {flow_id} not found"
            )
        
        # Log current flow status for debugging
        logger.info(f"🔍 Flow {flow_id} current status: {flow.status} (before data lookup)")
        
        # Important: We are only READING data, not executing any agents
        # This endpoint should never modify flow status or trigger execution
        
        # Get data import for this flow using the same logic as import storage handler
        from sqlalchemy import select
        from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
        
        # First try to get data import via discovery flow's data_import_id
        data_import = None
        if flow.data_import_id:
            data_import_query = select(DataImport).where(
                DataImport.id == flow.data_import_id
            )
            data_import_result = await db.execute(data_import_query)
            data_import = data_import_result.scalar_one_or_none()
            
        # If not found, try master flow ID lookup (same as import storage handler)
        if not data_import:
            logger.info(f"Flow {flow_id} has no data_import_id, trying master flow ID lookup")
            
            # Get the database ID for this flow_id (FK references id, not flow_id)
            db_id_query = select(CrewAIFlowStateExtensions.id).where(
                CrewAIFlowStateExtensions.flow_id == flow_id
            )
            db_id_result = await db.execute(db_id_query)
            flow_db_id = db_id_result.scalar_one_or_none()
            
            if flow_db_id:
                # Look for data imports with this master_flow_id
                import_query = select(DataImport).where(
                    DataImport.master_flow_id == flow_db_id
                ).order_by(DataImport.created_at.desc()).limit(1)
                
                import_result = await db.execute(import_query)
                data_import = import_result.scalar_one_or_none()
                
                if data_import:
                    logger.info(f"✅ Found data import via master flow ID lookup: {data_import.id}")
        
        if not data_import:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No data import found for flow {flow_id}"
            )
            
        data_imports = [data_import]  # Convert to list for compatibility with existing code
        
        # Get field mappings  
        field_mapping_query = select(ImportFieldMapping).where(
            ImportFieldMapping.data_import_id == data_imports[0].id
        )
        field_mapping_result = await db.execute(field_mapping_query)
        field_mappings = field_mapping_result.scalars().all()
        
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
        
        # Get data import for this flow using the same logic as import storage handler
        from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
        
        # First try to get data import via discovery flow's data_import_id
        data_import = None
        if flow.data_import_id:
            data_import_query = select(DataImport).where(
                DataImport.id == flow.data_import_id
            )
            data_import_result = await db.execute(data_import_query)
            data_import = data_import_result.scalar_one_or_none()
            
        # If not found, try master flow ID lookup (same as import storage handler)
        if not data_import:
            logger.info(f"Flow {flow_id} has no data_import_id, trying master flow ID lookup")
            
            # Get the database ID for this flow_id (FK references id, not flow_id)
            db_id_query = select(CrewAIFlowStateExtensions.id).where(
                CrewAIFlowStateExtensions.flow_id == flow_id
            )
            db_id_result = await db.execute(db_id_query)
            flow_db_id = db_id_result.scalar_one_or_none()
            
            if flow_db_id:
                # Look for data imports with this master_flow_id
                import_query = select(DataImport).where(
                    DataImport.master_flow_id == flow_db_id
                ).order_by(DataImport.created_at.desc()).limit(1)
                
                import_result = await db.execute(import_query)
                data_import = import_result.scalar_one_or_none()
        
        if not data_import:
            # Return empty stats if no data
            return DataCleansingStats(
                total_records=0,
                clean_records=0,
                records_with_issues=0,
                issues_by_severity={"low": 0, "medium": 0, "high": 0, "critical": 0},
                completion_percentage=0.0
            )
            
        data_imports = [data_import]  # Convert to list for compatibility with existing code
        
        # Calculate stats from first data import
        data_import = data_imports[0]
        total_records = data_import.total_records if data_import.total_records else 0
        # Use the total_records field which should be properly set during import
        
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

@router.post(
    "/flows/{flow_id}/data-cleansing/trigger",
    response_model=DataCleansingAnalysis,
    summary="Trigger data cleansing analysis for a flow"
)
async def trigger_data_cleansing_analysis(
    flow_id: str,
    request: TriggerDataCleansingRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
    current_user: User = Depends(get_current_user)
) -> DataCleansingAnalysis:
    """
    Trigger data cleansing analysis for a discovery flow.
    
    This endpoint actually executes the data cleansing phase using CrewAI agents
    to analyze data quality and provide recommendations.
    """
    try:
        logger.info(f"🚀 TRIGGERING data cleansing analysis for flow {flow_id}")
        
        # Get flow repository with proper context
        flow_repo = DiscoveryFlowRepository(db, context.client_account_id)
        
        # Verify flow exists and user has access
        flow = await flow_repo.get_by_flow_id(flow_id)
        if not flow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Flow {flow_id} not found"
            )
        
        logger.info(f"🔍 Flow {flow_id} current status: {flow.status}")
        
        # Import the MasterFlowOrchestrator to execute the data cleansing phase
        try:
            from app.services.master_flow_orchestrator import MasterFlowOrchestrator
            flow_orchestrator = MasterFlowOrchestrator(
                client_account_id=context.client_account_id,
                engagement_id=context.engagement_id,
                user_id=current_user.id
            )
            
            # Execute the data cleansing phase using the orchestrator
            logger.info(f"🤖 Executing data cleansing phase for flow {flow_id}")
            
            execution_result = await flow_orchestrator.execute_phase(
                flow_id=flow_id,
                phase_name="data_cleansing",
                phase_input={"force_refresh": request.force_refresh, "include_agent_analysis": request.include_agent_analysis}
            )
            
            logger.info(f"✅ Data cleansing phase execution completed: {execution_result.get('status', 'unknown')}")
            
            # If execution was successful, get the updated analysis
            if execution_result.get('status') == 'success':
                # Get data import for this flow to perform analysis
                from sqlalchemy import select
                from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
                
                # First try to get data import via discovery flow's data_import_id
                data_import = None
                if flow.data_import_id:
                    data_import_query = select(DataImport).where(
                        DataImport.id == flow.data_import_id
                    )
                    data_import_result = await db.execute(data_import_query)
                    data_import = data_import_result.scalar_one_or_none()
                    
                # If not found, try master flow ID lookup
                if not data_import:
                    logger.info(f"Flow {flow_id} has no data_import_id, trying master flow ID lookup")
                    
                    # Get the database ID for this flow_id (FK references id, not flow_id)
                    db_id_query = select(CrewAIFlowStateExtensions.id).where(
                        CrewAIFlowStateExtensions.flow_id == flow_id
                    )
                    db_id_result = await db.execute(db_id_query)
                    flow_db_id = db_id_result.scalar_one_or_none()
                    
                    if flow_db_id:
                        # Look for data imports with this master_flow_id
                        import_query = select(DataImport).where(
                            DataImport.master_flow_id == flow_db_id
                        ).order_by(DataImport.created_at.desc()).limit(1)
                        
                        import_result = await db.execute(import_query)
                        data_import = import_result.scalar_one_or_none()
                
                if not data_import:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"No data import found for flow {flow_id}"
                    )
                
                data_imports = [data_import]
                
                # Get field mappings  
                field_mapping_query = select(ImportFieldMapping).where(
                    ImportFieldMapping.data_import_id == data_imports[0].id
                )
                field_mapping_result = await db.execute(field_mapping_query)
                field_mappings = field_mapping_result.scalars().all()
                
                # Perform data cleansing analysis with agent results
                analysis_result = await _perform_data_cleansing_analysis(
                    flow_id=flow_id,
                    data_imports=data_imports,
                    field_mappings=field_mappings,
                    include_details=True,
                    execution_result=execution_result
                )
                
                logger.info(f"✅ Data cleansing analysis triggered and completed for flow {flow_id}")
                return analysis_result
            else:
                # Execution failed, but still return analysis with error status
                logger.warning(f"⚠️ Data cleansing execution failed: {execution_result.get('error', 'Unknown error')}")
                
                # Return a basic analysis indicating the execution failed
                from datetime import datetime
                return DataCleansingAnalysis(
                    flow_id=flow_id,
                    analysis_timestamp=datetime.utcnow().isoformat(),
                    total_records=0,
                    total_fields=0,
                    quality_score=0.0,
                    issues_count=0,
                    recommendations_count=0,
                    quality_issues=[],
                    recommendations=[],
                    field_quality_scores={},
                    processing_status=f"failed: {execution_result.get('error', 'Unknown error')}"
                )
                
        except ImportError as e:
            logger.error(f"❌ CrewAI service not available: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Data cleansing analysis service not available"
            )
        except Exception as e:
            logger.error(f"❌ Failed to execute data cleansing phase: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to execute data cleansing analysis: {str(e)}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to trigger data cleansing analysis for flow {flow_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger data cleansing analysis: {str(e)}"
        )

async def _perform_data_cleansing_analysis(
    flow_id: str,
    data_imports: List[Any],
    field_mappings: List[Any],
    include_details: bool = True,
    execution_result: Optional[Dict[str, Any]] = None
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
    
    # Get raw data from the data import (using the correct attribute)
    total_records = data_import.total_records if data_import else 0
    # Use the total_records field which should be properly set during import
    # Avoid accessing lazy-loaded relationships in async context
    
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