"""
Recommendation endpoint handlers for 6R analysis recommendations.
Contains handlers for: get recommendation.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.sixr_analysis import SixRAnalysis
from app.models.sixr_analysis import SixRRecommendation as SixRRecommendationModel
from app.schemas.sixr_analysis import SixRRecommendationResponse

logger = logging.getLogger(__name__)


async def get_sixr_recommendation(
    analysis_id: UUID,
    iteration_number: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Get the 6R recommendation for a specific analysis and iteration.

    If no iteration is specified, returns the latest recommendation.
    """
    try:
        # Get analysis
        result = await db.execute(
            select(SixRAnalysis).where(SixRAnalysis.id == analysis_id)
        )
        analysis = result.scalar_one_or_none()

        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found"
            )

        # Get recommendation for specific iteration or latest
        if iteration_number:
            rec_result = await db.execute(
                select(SixRRecommendationModel).where(
                    SixRRecommendationModel.analysis_id == analysis_id,
                    SixRRecommendationModel.iteration_number == iteration_number,
                )
            )
            recommendation = rec_result.scalar_one_or_none()
        else:
            # Get latest recommendation
            rec_result = await db.execute(
                select(SixRRecommendationModel)
                .where(SixRRecommendationModel.analysis_id == analysis_id)
                .order_by(SixRRecommendationModel.iteration_number.desc())
            )
            recommendation = rec_result.scalar_one_or_none()
            iteration_number = analysis.current_iteration

        if not recommendation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found"
            )

        # Build response
        return SixRRecommendationResponse(
            analysis_id=analysis_id,
            iteration_number=iteration_number,
            recommendation=recommendation,
            comparison_with_previous=None,  # TODO: Implement comparison logic
            confidence_evolution=[],  # TODO: Implement confidence tracking
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get recommendation for analysis {analysis_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recommendation: {str(e)}",
        )
