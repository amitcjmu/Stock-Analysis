"""
Analysis endpoint handlers for 6R analysis creation and retrieval.
Contains handlers for: create analysis, get analysis, list analyses.
"""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.sixr_analysis_modular.services.analysis_service import (
    AnalysisService,
)
from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from app.services.persistent_agents import TenantScopedAgentPool
from app.models.sixr_analysis import SixRAnalysis
from app.models.sixr_analysis import SixRAnalysisParameters as SixRParametersModel
from app.models.sixr_analysis import SixRRecommendation as SixRRecommendationModel
from app.schemas.sixr_analysis import (
    AnalysisStatus,
    SixRAnalysisListResponse,
    SixRAnalysisRequest,
    SixRAnalysisResponse,
    SixRParameterBase,
    SixRParameters,
    SixRRecommendation,
)

logger = logging.getLogger(__name__)


async def create_sixr_analysis(
    request: SixRAnalysisRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Create a new 6R analysis for the specified applications.

    This endpoint initiates the 6R analysis workflow:
    1. Creates analysis record
    2. Runs discovery analysis on application data
    3. Performs initial 6R recommendation
    4. Generates qualifying questions for refinement

    Bug #666 - Phase 2: Now using AI-powered analysis via TenantScopedAgentPool
    """
    try:
        # Bug #666 - Phase 2: Use TenantScopedAgentPool for AI-powered analysis
        # Pass the pool CLASS (not instance) - it manages singleton agents per tenant
        service = AnalysisService(
            crewai_service=TenantScopedAgentPool, require_ai=False
        )

        # Create analysis record with tenant context
        analysis = SixRAnalysis(
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id,
            name=request.analysis_name
            or f"6R Analysis {datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            description=request.description,
            status=AnalysisStatus.PENDING,
            priority=request.priority,
            application_ids=request.application_ids,
            current_iteration=1,
            progress_percentage=0.0,
            created_by="system",
        )

        db.add(analysis)
        await db.commit()
        await db.refresh(analysis)

        # Create initial parameters
        initial_params = request.initial_parameters or SixRParameterBase()

        # Handle application types if provided
        if request.application_types and len(request.application_ids) == 1:
            app_id = request.application_ids[0]
            if app_id in request.application_types:
                initial_params.application_type = request.application_types[app_id]

        parameters = SixRParametersModel(
            analysis_id=analysis.id,
            iteration_number=1,
            **initial_params.dict(),
            created_by="system",
        )

        db.add(parameters)
        await db.commit()

        # SECURITY FIX: Pass tenant context to prevent cross-tenant data access (Qodo Bot)
        # Lines 128-136 from original file - CRITICAL: Do not remove
        background_tasks.add_task(
            service.run_initial_analysis,
            analysis.id,
            initial_params.dict(),
            "system",
            context.client_account_id,
            context.engagement_id,
        )

        # Return initial response
        return SixRAnalysisResponse(
            analysis_id=analysis.id,
            status=AnalysisStatus.PENDING,
            current_iteration=1,
            applications=[{"id": app_id} for app_id in request.application_ids],
            parameters=SixRParameters(
                business_value=initial_params.business_value,
                technical_complexity=initial_params.technical_complexity,
                migration_urgency=initial_params.migration_urgency,
                compliance_requirements=initial_params.compliance_requirements,
                cost_sensitivity=initial_params.cost_sensitivity,
                risk_tolerance=initial_params.risk_tolerance,
                innovation_priority=initial_params.innovation_priority,
                application_type=initial_params.application_type,
                parameter_source="user_input",
                confidence_level=0.8,
                last_updated=datetime.utcnow(),
                updated_by="system",
            ),
            qualifying_questions=[],
            recommendation=None,
            progress_percentage=5.0,
            estimated_completion=None,
            created_at=analysis.created_at,
            updated_at=analysis.updated_at or analysis.created_at,
        )

    except Exception as e:
        logger.error(f"Failed to create 6R analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create analysis: {str(e)}",
        )


async def get_analysis(analysis_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get analysis by ID with current recommendation."""
    # Get analysis
    result = await db.execute(
        select(SixRAnalysis).where(SixRAnalysis.id == analysis_id)
    )
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    # Get current parameters
    params_result = await db.execute(
        select(SixRParametersModel)
        .where(SixRParametersModel.analysis_id == analysis_id)
        .order_by(SixRParametersModel.iteration_number.desc())
    )
    current_params = params_result.scalar_one_or_none()
    if not current_params:
        raise HTTPException(status_code=404, detail="Analysis parameters not found")

    # Get latest recommendation for this analysis
    rec_result = await db.execute(
        select(SixRRecommendationModel)
        .where(SixRRecommendationModel.analysis_id == analysis_id)
        .order_by(SixRRecommendationModel.iteration_number.desc())
        .limit(1)  # Ensure we only get one row
    )
    latest_recommendation = rec_result.scalar_one_or_none()

    # Convert to response format
    response_data = {
        "analysis_id": analysis.id,
        "status": analysis.status,
        "current_iteration": analysis.current_iteration,
        "applications": [{"id": app_id} for app_id in analysis.application_ids],
        "parameters": SixRParameters(
            business_value=current_params.business_value,
            technical_complexity=current_params.technical_complexity,
            migration_urgency=current_params.migration_urgency,
            compliance_requirements=current_params.compliance_requirements,
            cost_sensitivity=current_params.cost_sensitivity,
            risk_tolerance=current_params.risk_tolerance,
            innovation_priority=current_params.innovation_priority,
            application_type=current_params.application_type,
            parameter_source=current_params.parameter_source,
            confidence_level=current_params.confidence_level,
            last_updated=current_params.updated_at or current_params.created_at,
            updated_by=current_params.updated_by,
        ),
        "qualifying_questions": [],
        "recommendation": None,
        "progress_percentage": analysis.progress_percentage,
        "estimated_completion": analysis.estimated_completion,
        "created_at": analysis.created_at,
        "updated_at": analysis.updated_at or analysis.created_at,
    }

    # Add current recommendation if available
    if latest_recommendation:
        response_data["recommendation"] = SixRRecommendation(
            recommended_strategy=latest_recommendation.recommended_strategy,
            confidence_score=latest_recommendation.confidence_score,
            strategy_scores=latest_recommendation.strategy_scores or [],
            key_factors=latest_recommendation.key_factors or [],
            assumptions=latest_recommendation.assumptions or [],
            next_steps=latest_recommendation.next_steps or [],
            estimated_effort=latest_recommendation.estimated_effort,
            estimated_timeline=latest_recommendation.estimated_timeline,
            estimated_cost_impact=latest_recommendation.estimated_cost_impact,
        )

    return SixRAnalysisResponse(**response_data)


async def list_sixr_analyses(
    page: int = 1,
    page_size: int = 20,
    status_filter: Optional[AnalysisStatus] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    List all 6R analyses with optional filtering and pagination.
    """
    try:
        # Build query
        query = select(SixRAnalysis)

        if status_filter:
            query = query.where(SixRAnalysis.status == status_filter)

        # Get total count
        count_result = await db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total_count = count_result.scalar()

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await db.execute(query)
        analyses = result.scalars().all()

        # Convert to response format
        analysis_responses = []
        for analysis in analyses:
            # Get parameters for this analysis
            params_result = await db.execute(
                select(SixRParametersModel)
                .where(SixRParametersModel.analysis_id == analysis.id)
                .order_by(SixRParametersModel.iteration_number.desc())
            )
            current_params = params_result.scalar_one_or_none()

            if current_params:
                params = SixRParameters(
                    business_value=current_params.business_value,
                    technical_complexity=current_params.technical_complexity,
                    migration_urgency=current_params.migration_urgency,
                    compliance_requirements=current_params.compliance_requirements,
                    cost_sensitivity=current_params.cost_sensitivity,
                    risk_tolerance=current_params.risk_tolerance,
                    innovation_priority=current_params.innovation_priority,
                    application_type=current_params.application_type,
                    parameter_source=current_params.parameter_source,
                    confidence_level=current_params.confidence_level,
                    last_updated=current_params.updated_at or current_params.created_at,
                    updated_by=current_params.updated_by,
                )
            else:
                params = SixRParameters()

            # Get latest recommendation for this analysis
            rec_result = await db.execute(
                select(SixRRecommendationModel)
                .where(SixRRecommendationModel.analysis_id == analysis.id)
                .order_by(SixRRecommendationModel.iteration_number.desc())
                .limit(1)  # Ensure we only get one row
            )
            latest_recommendation = rec_result.scalar_one_or_none()

            recommendation = None
            if latest_recommendation:
                recommendation = SixRRecommendation(
                    recommended_strategy=latest_recommendation.recommended_strategy,
                    confidence_score=latest_recommendation.confidence_score,
                    strategy_scores=latest_recommendation.strategy_scores or [],
                    key_factors=latest_recommendation.key_factors or [],
                    assumptions=latest_recommendation.assumptions or [],
                    next_steps=latest_recommendation.next_steps or [],
                    estimated_effort=latest_recommendation.estimated_effort,
                    estimated_timeline=latest_recommendation.estimated_timeline,
                    estimated_cost_impact=latest_recommendation.estimated_cost_impact,
                    risk_factors=latest_recommendation.risk_factors or [],
                    business_benefits=latest_recommendation.business_benefits or [],
                    technical_benefits=latest_recommendation.technical_benefits or [],
                )

            analysis_responses.append(
                SixRAnalysisResponse(
                    analysis_id=analysis.id,
                    status=analysis.status,
                    current_iteration=analysis.current_iteration,
                    applications=analysis.application_data
                    or [{"id": app_id} for app_id in analysis.application_ids],
                    parameters=params,
                    qualifying_questions=[],
                    recommendation=recommendation,  # Now includes actual recommendation data
                    progress_percentage=analysis.progress_percentage,
                    estimated_completion=analysis.estimated_completion,
                    created_at=analysis.created_at,
                    updated_at=analysis.updated_at or analysis.created_at,
                )
            )

        return SixRAnalysisListResponse(
            analyses=analysis_responses,
            total_count=total_count,
            page=page,
            page_size=page_size,
        )

    except Exception as e:
        logger.error(f"Failed to list analyses: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list analyses: {str(e)}",
        )
