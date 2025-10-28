"""
Analysis retrieval endpoint handler for 6R analysis.
Contains handler for: get analysis by ID with current recommendation.
"""

import logging
from uuid import UUID

from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.sixr_analysis import SixRAnalysis
from app.models.sixr_analysis import SixRAnalysisParameters as SixRParametersModel
from app.models.sixr_analysis import SixRRecommendation as SixRRecommendationModel
from app.schemas.sixr_analysis import (
    SixRAnalysisResponse,
    SixRParameters,
    SixRRecommendation,
)

logger = logging.getLogger(__name__)


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
