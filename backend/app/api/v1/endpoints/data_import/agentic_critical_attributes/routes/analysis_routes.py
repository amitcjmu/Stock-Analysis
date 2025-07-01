"""
Agentic critical attributes analysis route handlers.
Thin controllers that delegate to service layer.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.context import get_current_context, RequestContext, extract_context_from_request
from ..models.attribute_schemas import (
    AttributeAnalysisRequest, AttributeAnalysisResponse,
    CrewExecutionRequest, CrewExecutionResponse
)
from ..services.attribute_analyzer import AttributeAnalyzer
from ..services.agent_coordinator import AgentCoordinator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analysis", tags=["agentic-analysis"])


def get_attribute_analyzer(
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
) -> AttributeAnalyzer:
    """Dependency injection for attribute analyzer."""
    return AttributeAnalyzer(db, context)


def get_agent_coordinator(
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
) -> AgentCoordinator:
    """Dependency injection for agent coordinator."""
    return AgentCoordinator(db, context)


@router.get("/agentic-critical-attributes", response_model=AttributeAnalysisResponse)
async def get_agentic_critical_attributes(
    request: Request,
    import_id: Optional[str] = None,
    force_reanalysis: bool = False,
    include_crew_analysis: bool = True,
    analysis_depth: str = "comprehensive",
    analyzer: AttributeAnalyzer = Depends(get_attribute_analyzer)
):
    """
    🤖 AGENTIC Critical Attributes Analysis
    
    Uses AI agents to analyze imported data and determine critical migration attributes.
    Falls back to enhanced pattern analysis when CrewAI is not available.
    """
    try:
        # Create analysis request
        analysis_request = AttributeAnalysisRequest(
            import_id=import_id,
            use_latest_import=import_id is None,
            force_reanalysis=force_reanalysis,
            include_crew_analysis=include_crew_analysis,
            analysis_depth=analysis_depth
        )
        
        # Execute analysis
        result = await analyzer.analyze_critical_attributes(analysis_request)
        
        logger.info(f"Analysis completed: {result.analysis_id}, success: {result.success}")
        return result
        
    except Exception as e:
        logger.error(f"Error in agentic critical attributes analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze critical attributes")


@router.post("/trigger-field-mapping-crew", response_model=CrewExecutionResponse)
async def trigger_field_mapping_crew_analysis(
    request: CrewExecutionRequest,
    coordinator: AgentCoordinator = Depends(get_agent_coordinator)
):
    """
    Trigger CrewAI field mapping crew analysis for specific import.
    
    This endpoint specifically executes CrewAI agents for field mapping analysis.
    """
    try:
        # Get the import data
        from app.models.data_import import DataImport
        from sqlalchemy import select, and_
        
        import_query = select(DataImport).where(
            and_(
                DataImport.id == request.import_id,
                DataImport.client_account_id == coordinator.context.client_account_id
            )
        )
        import_result = await coordinator.db.execute(import_query)
        data_import = import_result.scalar_one_or_none()
        
        if not data_import:
            raise HTTPException(status_code=404, detail="Data import not found")
        
        # Get sample data
        from app.models.data_import import RawImportRecord
        sample_query = select(RawImportRecord).where(
            RawImportRecord.data_import_id == data_import.id
        ).limit(10)
        sample_result = await coordinator.db.execute(sample_query)
        sample_records = sample_result.scalars().all()
        
        sample_data = []
        for record in sample_records:
            if record.raw_data:
                sample_data.append(record.raw_data)
        
        if not sample_data:
            return CrewExecutionResponse(
                success=False,
                execution_id="no_data",
                status="failed",
                message="No sample data available for analysis"
            )
        
        # Execute CrewAI analysis
        if request.background_execution:
            # TODO: Implement background task execution
            execution_id = f"crew_{request.import_id}_{int(datetime.utcnow().timestamp())}"
            
            return CrewExecutionResponse(
                success=True,
                execution_id=execution_id,
                status="queued",
                message="CrewAI analysis queued for background execution"
            )
        else:
            # Execute immediately
            from datetime import datetime
            start_time = datetime.utcnow()
            
            crew_result = await coordinator.execute_crew_analysis(
                data_import, sample_data, request.parameters.get("analysis_depth", "standard")
            )
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            execution_id = f"crew_{request.import_id}_{int(start_time.timestamp())}"
            
            return CrewExecutionResponse(
                success=crew_result.get("crew_execution") == "completed",
                execution_id=execution_id,
                status="completed" if crew_result.get("crew_execution") == "completed" else "failed",
                message=crew_result.get("analysis_result", "CrewAI analysis completed"),
                results=crew_result,
                execution_time=execution_time
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in CrewAI execution: {e}")
        raise HTTPException(status_code=500, detail="Failed to execute CrewAI analysis")


@router.get("/analysis-status/{analysis_id}")
async def get_analysis_status(
    analysis_id: str,
    analyzer: AttributeAnalyzer = Depends(get_attribute_analyzer)
):
    """Get status of a running analysis."""
    try:
        # TODO: Implement analysis status tracking
        # For now, return a simple status
        return {
            "analysis_id": analysis_id,
            "status": "completed",  # Placeholder
            "progress": 1.0,
            "message": "Analysis status tracking not yet implemented"
        }
    except Exception as e:
        logger.error(f"Error getting analysis status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analysis status")


@router.post("/reanalyze/{import_id}", response_model=AttributeAnalysisResponse)
async def reanalyze_import(
    import_id: str,
    analysis_depth: str = "comprehensive",
    analyzer: AttributeAnalyzer = Depends(get_attribute_analyzer)
):
    """Force reanalysis of a specific import."""
    try:
        analysis_request = AttributeAnalysisRequest(
            import_id=import_id,
            use_latest_import=False,
            force_reanalysis=True,
            include_crew_analysis=True,
            analysis_depth=analysis_depth
        )
        
        result = await analyzer.analyze_critical_attributes(analysis_request)
        return result
        
    except Exception as e:
        logger.error(f"Error in reanalysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to reanalyze import")


@router.get("/health")
async def health_check():
    """Health check endpoint for analysis routes."""
    return {"status": "healthy", "service": "agentic_critical_attributes_analysis"}