"""
6R Analysis API endpoints for migration strategy analysis workflow.
Provides REST API for 6R analysis, parameter updates, question handling, and recommendations.

MODULARIZED STRUCTURE (October 2025):
- Main router defined here with route registrations
- Handler logic in sixr_analysis_modular/handlers/
- Service logic in sixr_analysis_modular/services/
- Maintains backward compatibility - all routes work the same

Per CLAUDE.md modularization pattern:
- This file < 300 lines (router definitions only)
- Handler files < 300 lines each (endpoint logic)
- Service files contain business logic
"""

import logging
from typing import Optional

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from app.schemas.sixr_analysis import (
    AnalysisStatus,
    BulkAnalysisRequest,
    BulkAnalysisResponse,
    InlineAnswersRequest,
    InlineAnswersResponse,
    IterationRequest,
    QualifyingQuestionsRequest,
    SixRAnalysisListResponse,
    SixRAnalysisRequest,
    SixRAnalysisResponse,
    SixRParameterUpdateRequest,
    SixRRecommendationResponse,
)

# Import handlers from modular structure
from app.api.v1.endpoints.sixr_analysis_modular.handlers import (
    create_sixr_analysis,
    get_analysis,
    list_sixr_analyses,
    update_sixr_parameters,
    submit_qualifying_responses,
    submit_inline_answers,
    create_analysis_iteration,
    get_sixr_recommendation,
    create_bulk_analysis,
)

# Conditional import for CrewAI technical debt crew
try:
    from app.services.crewai_flows.crews.technical_debt_crew import (
        create_technical_debt_crew,
    )

    TECHNICAL_DEBT_CREW_AVAILABLE = True
except ImportError:
    TECHNICAL_DEBT_CREW_AVAILABLE = False

    def create_technical_debt_crew(*args, **kwargs):
        return None


logger = logging.getLogger(__name__)

router = APIRouter()

# Bug #666 - Phase 2 COMPLETE: All endpoints now use TenantScopedAgentPool per request
# No module-level service instantiation - services created per-request with tenant context
logger.info("6R Analysis router initialized - using AI-powered analysis per request")


# ============================================================================
# ANALYSIS ENDPOINTS
# ============================================================================


@router.post("/analyze", response_model=SixRAnalysisResponse)
async def create_analysis_endpoint(
    request: SixRAnalysisRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Create a new 6R analysis for the specified applications.

    Delegates to: handlers.analysis_handlers.create_sixr_analysis
    """
    return await create_sixr_analysis(request, background_tasks, db, context)


@router.get("/{analysis_id}", response_model=SixRAnalysisResponse)
async def get_analysis_endpoint(analysis_id: UUID, db: AsyncSession = Depends(get_db)):
    """
    Get analysis by ID with current recommendation.

    Delegates to: handlers.analysis_handlers.get_analysis
    """
    return await get_analysis(analysis_id, db)


@router.get("/", response_model=SixRAnalysisListResponse)
async def list_analyses_endpoint(
    page: int = 1,
    page_size: int = 20,
    status_filter: Optional[AnalysisStatus] = None,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    List all 6R analyses with optional filtering and pagination.

    Delegates to: handlers.analysis_handlers.list_sixr_analyses
    """
    return await list_sixr_analyses(page, page_size, status_filter, db, context)


# ============================================================================
# PARAMETER ENDPOINTS
# ============================================================================


@router.put("/{analysis_id}/parameters", response_model=SixRAnalysisResponse)
async def update_parameters_endpoint(
    analysis_id: UUID,
    request: SixRParameterUpdateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Update 6R analysis parameters and trigger re-analysis.

    Delegates to: handlers.parameter_handlers.update_sixr_parameters
    """
    return await update_sixr_parameters(
        analysis_id, request, background_tasks, db, context
    )


@router.post("/{analysis_id}/questions", response_model=SixRAnalysisResponse)
async def submit_questions_endpoint(
    analysis_id: UUID,
    request: QualifyingQuestionsRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Submit responses to qualifying questions and trigger analysis refinement.

    Delegates to: handlers.parameter_handlers.submit_qualifying_responses
    """
    return await submit_qualifying_responses(
        analysis_id, request, background_tasks, db, context
    )


@router.post("/{analysis_id}/inline-answers", response_model=InlineAnswersResponse)
async def submit_inline_answers_endpoint(
    analysis_id: UUID,
    request: InlineAnswersRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Submit inline answers for Tier 1 gaps and resume analysis.

    Per Two-Tier Inline Gap-Filling Design (October 2025), this endpoint:
    1. Updates asset fields with user-provided values
    2. Resumes AI agent execution with complete data

    Delegates to: handlers.parameter_handlers.submit_inline_answers
    """
    return await submit_inline_answers(
        analysis_id, request, background_tasks, db, context
    )


@router.post("/{analysis_id}/iterate", response_model=SixRAnalysisResponse)
async def create_iteration_endpoint(
    analysis_id: UUID,
    request: IterationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Create a new iteration of the 6R analysis based on feedback.

    Delegates to: handlers.parameter_handlers.create_analysis_iteration
    """
    return await create_analysis_iteration(
        analysis_id, request, background_tasks, db, context
    )


# ============================================================================
# RECOMMENDATION ENDPOINTS
# ============================================================================


@router.get("/{analysis_id}/recommendation", response_model=SixRRecommendationResponse)
async def get_recommendation_endpoint(
    analysis_id: UUID,
    iteration_number: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Get the 6R recommendation for a specific analysis and iteration.

    Delegates to: handlers.recommendation_handlers.get_sixr_recommendation
    """
    return await get_sixr_recommendation(analysis_id, iteration_number, db)


# ============================================================================
# BULK ANALYSIS ENDPOINTS
# ============================================================================


@router.post("/bulk", response_model=BulkAnalysisResponse)
async def create_bulk_endpoint(
    request: BulkAnalysisRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Create bulk 6R analysis for multiple applications.

    Delegates to: handlers.bulk_handlers.create_bulk_analysis
    """
    return await create_bulk_analysis(request, background_tasks, db, context)


# ============================================================================
# MODULARIZATION NOTES
# ============================================================================
# All handler logic moved to sixr_analysis_modular/handlers/
# - analysis_handlers.py: create, get, list analyses
# - parameter_handlers.py: update params, questions, iterations
# - recommendation_handlers.py: get recommendations
# - bulk_handlers.py: bulk operations
#
# SECURITY FIX PRESERVED: Lines 128-136 in analysis_handlers.py
# - Tenant context (client_account_id, engagement_id) passed to background tasks
# - Prevents cross-tenant data access (Qodo Bot security concern)
#
# BACKWARD COMPATIBILITY: All routes maintain same:
# - Route paths
# - Request/response schemas
# - Behavior and functionality
# ============================================================================
