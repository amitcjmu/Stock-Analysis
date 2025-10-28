"""
Analysis listing endpoint handler for 6R analysis.
Contains handler for: list analyses with filtering and pagination.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from app.models.asset import Asset
from app.models.sixr_analysis import SixRAnalysis
from app.models.sixr_analysis import SixRAnalysisParameters as SixRParametersModel
from app.models.sixr_analysis import SixRRecommendation as SixRRecommendationModel
from app.schemas.sixr_analysis import (
    AnalysisStatus,
    SixRAnalysisListResponse,
    SixRAnalysisResponse,
    SixRParameters,
    SixRRecommendation,
)

logger = logging.getLogger(__name__)


async def list_sixr_analyses(
    page: int = 1,
    page_size: int = 20,
    status_filter: Optional[AnalysisStatus] = None,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    List all 6R analyses with optional filtering and pagination.
    SECURITY: Scoped to current tenant (client_account_id, engagement_id)
    """
    try:
        # Build query with tenant scoping (SECURITY FIX)
        query = select(SixRAnalysis).where(
            SixRAnalysis.client_account_id == context.client_account_id,
            SixRAnalysis.engagement_id == context.engagement_id,
        )

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

            # Bug #814 fix: Always fetch complete asset data from database
            # to prevent frontend crashes on undefined fields
            applications = []
            for app_id in analysis.application_ids:
                try:
                    # Handle both UUID and integer application IDs
                    # Legacy analyses may have integer IDs, newer ones use UUIDs
                    if isinstance(app_id, int):
                        # Skip integer IDs - Asset table uses UUID primary keys
                        # Fall back to cached data or defaults
                        logger.debug(
                            f"Skipping integer app_id {app_id} - Asset table uses UUIDs"
                        )
                        asset = None
                    else:
                        # Try to get asset from database with UUID
                        asset_uuid = UUID(app_id) if isinstance(app_id, str) else app_id
                        asset_result = await db.execute(
                            select(Asset).where(Asset.id == asset_uuid)
                        )
                        asset = asset_result.scalar_one_or_none()

                    if asset:
                        # Use complete data from database
                        app_data = {
                            "id": str(asset.id),
                            "name": asset.name or f"Application {app_id}",
                            "criticality": asset.criticality or "medium",
                            "business_criticality": asset.business_criticality
                            or "medium",
                            "asset_type": asset.asset_type or "application",
                            "technology_stack": asset.technology_stack or "",
                            "migration_complexity": asset.migration_complexity
                            or "medium",
                            "six_r_strategy": asset.six_r_strategy,
                        }
                    else:
                        # Fallback to cached data or defaults
                        # Bug #814: Check if application_data exists and is not empty
                        app_id_str = str(app_id)
                        cached_data = (
                            analysis.application_data
                            if analysis.application_data
                            and len(analysis.application_data) > 0
                            else None
                        )

                        cached = None
                        if cached_data:
                            # Search for matching app in cached data
                            cached = next(
                                (
                                    a
                                    for a in cached_data
                                    if str(a.get("id")) == app_id_str
                                ),
                                None,
                            )

                        if cached:
                            # Use cached data with defensive defaults
                            app_data = {
                                "id": app_id_str,
                                "name": cached.get("name", f"Application {app_id}"),
                                "criticality": cached.get("criticality", "medium"),
                                "business_criticality": cached.get(
                                    "business_criticality", "medium"
                                ),
                                "asset_type": cached.get("asset_type", "application"),
                                "technology_stack": cached.get("technology_stack", ""),
                                "migration_complexity": cached.get(
                                    "migration_complexity", "medium"
                                ),
                                "six_r_strategy": cached.get("six_r_strategy"),
                            }
                        else:
                            # Ultimate fallback with all required fields
                            app_data = {
                                "id": app_id_str,
                                "name": f"Application {app_id}",
                                "criticality": "medium",
                                "business_criticality": "medium",
                                "asset_type": "application",
                                "technology_stack": "",
                                "migration_complexity": "medium",
                                "six_r_strategy": None,
                            }

                    applications.append(app_data)
                except Exception as e:
                    logger.warning(f"Failed to fetch asset {app_id}: {e}")
                    # Use minimal fallback with required fields
                    applications.append(
                        {
                            "id": str(app_id),
                            "name": f"Application {app_id}",
                            "criticality": "medium",
                            "business_criticality": "medium",
                            "asset_type": "application",
                            "technology_stack": "",
                            "migration_complexity": "medium",
                            "six_r_strategy": None,
                        }
                    )

            analysis_responses.append(
                SixRAnalysisResponse(
                    analysis_id=analysis.id,
                    status=analysis.status,
                    current_iteration=analysis.current_iteration,
                    applications=applications,
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
