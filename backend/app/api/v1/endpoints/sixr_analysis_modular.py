"""
6R Analysis API Endpoints - Modular & Robust
Combines robust error handling with clean modular architecture.

Bug #666 - Phase 2: This file is DEPRECATED in favor of sixr_analysis.py
which uses AI-powered analysis via TenantScopedAgentPool per request.
"""

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from app.services.persistent_agents import TenantScopedAgentPool

from .sixr_handlers import (
    AnalysisEndpointsHandler,
    BackgroundTasksHandler,
    IterationHandler,
    ParameterManagementHandler,
    RecommendationHandler,
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Bug #666 - Phase 2: Handlers now created per-request with TenantScopedAgentPool
# No module-level handler instantiation
logger.info("SixR Analysis Modular router initialized - handlers created per request")


@router.get("/health")
async def sixr_analysis_health_check(
    context: RequestContext = Depends(get_current_context),
):
    """Health check endpoint for 6R analysis module."""
    # Bug #666 - Phase 2: Create handlers per-request with AI pool
    analysis_handler = AnalysisEndpointsHandler(crewai_service=TenantScopedAgentPool)
    parameter_handler = ParameterManagementHandler(crewai_service=TenantScopedAgentPool)
    iteration_handler = IterationHandler(crewai_service=TenantScopedAgentPool)
    recommendation_handler = RecommendationHandler()
    background_handler = BackgroundTasksHandler(crewai_service=TenantScopedAgentPool)

    return {
        "status": "healthy",
        "module": "sixr-analysis",
        "version": "3.0.0",  # Bug #666 - Phase 2: Updated version
        "ai_powered": True,  # AI analysis enabled
        "components": {
            "analysis_endpoints": analysis_handler.is_available(),
            "parameter_management": parameter_handler.is_available(),
            "iteration_handler": iteration_handler.is_available(),
            "recommendation_handler": recommendation_handler.is_available(),
            "background_tasks": background_handler.is_available(),
        },
    }


@router.post("/analyze")
async def create_sixr_analysis(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Create a new 6R analysis for the specified applications.

    Bug #666 - Phase 2: Now using AI-powered analysis via TenantScopedAgentPool
    """
    try:
        # Bug #666 - Phase 2: Create handler per-request with AI pool
        analysis_handler = AnalysisEndpointsHandler(
            crewai_service=TenantScopedAgentPool
        )

        request_body = await request.json()
        result = await analysis_handler.create_analysis(
            request_body, background_tasks, db
        )
        return result

    except Exception as e:
        logger.error(f"Error in create_sixr_analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create analysis: {str(e)}",
        )


@router.get("/{analysis_id}")
async def get_sixr_analysis(
    analysis_id: int,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """Get a specific 6R analysis by ID."""
    try:
        # Bug #666 - Phase 2: Create handler per-request with AI pool
        analysis_handler = AnalysisEndpointsHandler(
            crewai_service=TenantScopedAgentPool
        )

        result = await analysis_handler.get_analysis(analysis_id, db)
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_sixr_analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analysis: {str(e)}",
        )


@router.put("/{analysis_id}/parameters")
async def update_sixr_parameters(
    analysis_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """Update analysis parameters and optionally re-run analysis."""
    try:
        # Bug #666 - Phase 2: Create handler per-request with AI pool
        parameter_handler = ParameterManagementHandler(
            crewai_service=TenantScopedAgentPool
        )

        request_body = await request.json()
        result = await parameter_handler.update_parameters(
            analysis_id, request_body, db
        )
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in update_sixr_parameters: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update parameters: {str(e)}",
        )


@router.post("/{analysis_id}/questions")
async def submit_qualifying_questions(
    analysis_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """Submit answers to qualifying questions and update parameters."""
    try:
        # Bug #666 - Phase 2: Create handler per-request with AI pool
        parameter_handler = ParameterManagementHandler(
            crewai_service=TenantScopedAgentPool
        )

        request_body = await request.json()
        result = await parameter_handler.submit_qualifying_questions(
            analysis_id, request_body, db
        )
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in submit_qualifying_questions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit questions: {str(e)}",
        )


@router.post("/{analysis_id}/iterate")
async def create_sixr_iteration(
    analysis_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """Create a new analysis iteration with updated parameters."""
    try:
        # Bug #666 - Phase 2: Create handler per-request with AI pool
        iteration_handler = IterationHandler(crewai_service=TenantScopedAgentPool)

        request_body = await request.json()
        result = await iteration_handler.create_iteration(analysis_id, request_body, db)
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in create_sixr_iteration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create iteration: {str(e)}",
        )


@router.get("/{analysis_id}/recommendation")
async def get_sixr_recommendation(
    analysis_id: int,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """Get the recommendation for a specific analysis."""
    try:
        # Bug #666 - Phase 2: Create handler per-request (doesn't use AI pool)
        recommendation_handler = RecommendationHandler()

        result = await recommendation_handler.get_recommendation(analysis_id, db)
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_sixr_recommendation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recommendation: {str(e)}",
        )


@router.get("/")
async def list_sixr_analyses(
    skip: int = 0,
    limit: int = 100,
    status_filter: str = None,
    priority_filter: str = None,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """List all 6R analyses with optional filtering."""
    try:
        # Bug #666 - Phase 2: Create handler per-request with AI pool
        analysis_handler = AnalysisEndpointsHandler(
            crewai_service=TenantScopedAgentPool
        )

        result = await analysis_handler.list_analyses(
            db, skip, limit, status_filter, priority_filter
        )
        return result

    except Exception as e:
        logger.error(f"Error in list_sixr_analyses: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list analyses: {str(e)}",
        )


@router.post("/bulk")
async def create_bulk_sixr_analysis(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """Create bulk 6R analysis for multiple applications."""
    try:
        # Bug #666 - Phase 2: Create handler per-request with AI pool
        analysis_handler = AnalysisEndpointsHandler(
            crewai_service=TenantScopedAgentPool
        )

        request_body = await request.json()
        result = await analysis_handler.create_bulk_analysis(
            request_body, background_tasks, db
        )
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in create_bulk_sixr_analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create bulk analysis: {str(e)}",
        )
