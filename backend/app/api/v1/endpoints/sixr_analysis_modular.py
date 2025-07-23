"""
6R Analysis API Endpoints - Modular & Robust
Combines robust error handling with clean modular architecture.
"""

import logging

from fastapi import (APIRouter, BackgroundTasks, Depends, HTTPException,
                     Request, status)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

from .sixr_handlers import (AnalysisEndpointsHandler, BackgroundTasksHandler,
                            IterationHandler, ParameterManagementHandler,
                            RecommendationHandler)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Initialize handlers
analysis_handler = AnalysisEndpointsHandler()
parameter_handler = ParameterManagementHandler()
iteration_handler = IterationHandler()
recommendation_handler = RecommendationHandler()
background_handler = BackgroundTasksHandler()


@router.get("/health")
async def sixr_analysis_health_check():
    """Health check endpoint for 6R analysis module."""
    return {
        "status": "healthy",
        "module": "sixr-analysis",
        "version": "2.0.0",
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
):
    """Create a new 6R analysis for the specified applications."""
    try:
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
async def get_sixr_analysis(analysis_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific 6R analysis by ID."""
    try:
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
    analysis_id: int, request: Request, db: AsyncSession = Depends(get_db)
):
    """Update analysis parameters and optionally re-run analysis."""
    try:
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
    analysis_id: int, request: Request, db: AsyncSession = Depends(get_db)
):
    """Submit answers to qualifying questions and update parameters."""
    try:
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
    analysis_id: int, request: Request, db: AsyncSession = Depends(get_db)
):
    """Create a new analysis iteration with updated parameters."""
    try:
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
async def get_sixr_recommendation(analysis_id: int, db: AsyncSession = Depends(get_db)):
    """Get the recommendation for a specific analysis."""
    try:
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
):
    """List all 6R analyses with optional filtering."""
    try:
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
):
    """Create bulk 6R analysis for multiple applications."""
    try:
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
