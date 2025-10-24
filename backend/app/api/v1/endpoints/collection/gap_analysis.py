"""
Collection Gap Analysis Endpoint

Provides endpoint for weight-based gap analysis with fast/thorough modes.
Part of Collection Flow Adaptive Questionnaire Enhancements.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.context import RequestContext, get_current_context_dependency
from app.schemas.collection import GapAnalysisResponse
from app.services.collection.incremental_gap_analyzer import IncrementalGapAnalyzer

logger = logging.getLogger(__name__)

router = APIRouter()


class GapAnalysisRequest(BaseModel):
    """Request model for gap analysis."""

    child_flow_id: UUID = Field(..., description="Collection child flow UUID")
    asset_id: UUID = Field(..., description="Asset UUID to analyze")
    analysis_mode: str = Field(
        default="fast", description="Analysis mode: fast or thorough"
    )
    critical_only: bool = Field(default=False, description="Only return critical gaps")


@router.post("/gap-analysis", response_model=GapAnalysisResponse)
async def analyze_gaps(
    request: GapAnalysisRequest,
    context: RequestContext = Depends(get_current_context_dependency),
    db: AsyncSession = Depends(get_db),
):
    """
    Analyze gaps for a single asset with weight-based progress tracking.

    **Modes:**
    - `fast`: Analyze only this asset (quick)
    - `thorough`: Analyze with dependency graph traversal (slower, more complete)

    **Returns:**
    - List of gaps with criticality and weight information
    - Progress metrics with completion percentage
    - Weight-based calculations for accurate progress tracking
    """
    try:
        if request.analysis_mode not in ["fast", "thorough"]:
            raise ValueError("analysis_mode must be 'fast' or 'thorough'")

        service = IncrementalGapAnalyzer(db=db, context=context)

        # Service returns Pydantic model directly
        result = await service.analyze_gaps(
            child_flow_id=request.child_flow_id,
            asset_id=request.asset_id,
            mode=request.analysis_mode,
            critical_only=request.critical_only,
        )

        return result

    except ValueError as e:
        logger.error(f"❌ Gap analysis validation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Gap analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
