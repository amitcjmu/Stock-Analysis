"""
Bulk analysis endpoint handlers for 6R analysis bulk operations.
Contains handlers for: create bulk analysis.
"""

import logging
from fastapi import BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.sixr_analysis_modular.services.analysis_service import (
    AnalysisService,
)
from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from app.services.persistent_agents import TenantScopedAgentPool
from app.models.sixr_analysis import SixRAnalysis
from app.schemas.sixr_analysis import (
    AnalysisStatus,
    BulkAnalysisRequest,
    BulkAnalysisResponse,
    SixRAnalysisRequest,
    SixRAnalysisResponse,
    SixRParameterBase,
)

logger = logging.getLogger(__name__)


async def create_bulk_analysis(
    request: BulkAnalysisRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Create bulk 6R analysis for multiple applications.

    This endpoint creates individual analyses for each application
    and processes them in batches.

    Bug #666 - Phase 2: Now using AI-powered analysis via TenantScopedAgentPool
    """
    try:
        # Bug #666 - Phase 2: Create AI-powered service per request
        service = AnalysisService(
            crewai_service=TenantScopedAgentPool, require_ai=False
        )
        individual_analyses = []

        # Create individual analyses
        for app_id in request.application_ids:
            analysis_request = SixRAnalysisRequest(
                application_ids=[app_id],
                initial_parameters=request.default_parameters,
                analysis_name=f"{request.analysis_name} - App {app_id}",
                priority=request.priority,
            )

            # Create analysis with tenant context
            analysis = SixRAnalysis(
                client_account_id=context.client_account_id,
                engagement_id=context.engagement_id,
                name=analysis_request.analysis_name,
                status=AnalysisStatus.PENDING,
                priority=analysis_request.priority,
                application_ids=[app_id],
                current_iteration=1,
                progress_percentage=0.0,
                created_by="system",
            )

            db.add(analysis)
            individual_analyses.append(analysis)

        db.commit()

        # Start background bulk processing with AI-powered service
        background_tasks.add_task(
            service.run_bulk_analysis,
            [a.id for a in individual_analyses],
            request.batch_size,
            "system",
        )

        # Build response
        analysis_responses = []
        for analysis in individual_analyses:
            params = request.default_parameters or SixRParameterBase()
            analysis_responses.append(
                SixRAnalysisResponse(
                    analysis_id=analysis.id,
                    status=analysis.status,
                    current_iteration=1,
                    applications=[{"id": analysis.application_ids[0]}],
                    parameters=params,
                    qualifying_questions=[],
                    recommendation=None,
                    progress_percentage=0.0,
                    estimated_completion=None,
                    created_at=analysis.created_at,
                    updated_at=analysis.updated_at or analysis.created_at,
                )
            )

        return BulkAnalysisResponse(
            bulk_analysis_id=individual_analyses[
                0
            ].id,  # Use first analysis ID as bulk ID
            total_applications=len(request.application_ids),
            completed_applications=0,
            failed_applications=0,
            progress_percentage=0.0,
            individual_analyses=analysis_responses,
            estimated_completion=None,
            status=AnalysisStatus.PENDING,
        )

    except Exception as e:
        logger.error(f"Failed to create bulk analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create bulk analysis: {str(e)}",
        )
