"""
Collection Flow Query Operations
Read-only database operations for collection flows including status, flow details,
gaps, questionnaires, and readiness assessments.
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.security.secure_logging import safe_log_format
from app.models import User
from app.models.asset import Asset
from app.models.collection_flow import (
    AdaptiveQuestionnaire,
    CollectionFlow,
    CollectionFlowStatus,
    CollectionGapAnalysis,
)
from app.schemas.collection_flow import (
    CollectionFlowResponse,
    CollectionGapAnalysisResponse,
    AdaptiveQuestionnaireResponse,
)

# Import modular functions
from app.api.v1.endpoints import collection_serializers

logger = logging.getLogger(__name__)


async def get_adaptive_questionnaires(
    flow_id: str,
    db: AsyncSession,
    current_user: User,
    context: RequestContext,
) -> List[AdaptiveQuestionnaireResponse]:
    """Get adaptive questionnaires for a collection flow.

    Args:
        flow_id: Collection flow ID
        db: Database session
        current_user: Current authenticated user
        context: Request context

    Returns:
        List of adaptive questionnaires

    Raises:
        HTTPException: If flow not found or unauthorized
    """
    try:
        # First verify the flow exists and user has access
        flow_result = await db.execute(
            select(CollectionFlow).where(
                CollectionFlow.flow_id == UUID(flow_id),
                CollectionFlow.engagement_id == context.engagement_id,
            )
        )
        flow = flow_result.scalar_one_or_none()

        if not flow:
            raise HTTPException(status_code=404, detail="Collection flow not found")

        # Get questionnaires for this flow
        result = await db.execute(
            select(AdaptiveQuestionnaire)
            .where(AdaptiveQuestionnaire.collection_flow_id == flow.id)
            .order_by(AdaptiveQuestionnaire.created_at.desc())
        )
        questionnaires = result.scalars().all()

        # If no questionnaires exist yet, return empty list
        # The frontend will retry until CrewAI generates them
        if not questionnaires:
            logger.info(f"No questionnaires found yet for flow {flow_id}")
            return []

        # Convert to response schema
        return [
            AdaptiveQuestionnaireResponse(
                id=str(q.id),
                collection_flow_id=str(q.collection_flow_id),
                application_id=str(q.application_id) if q.application_id else None,
                questionnaire_type=q.questionnaire_type,
                questions=q.questions or {},
                responses=q.responses or {},
                metadata=q.metadata or {},
                status=q.status,
                created_at=q.created_at,
                updated_at=q.updated_at,
            )
            for q in questionnaires
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting adaptive questionnaires for flow {flow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def get_collection_status(
    db: AsyncSession,
    current_user: User,
    context: RequestContext,
) -> Dict[str, Any]:
    """Get collection flow status for current engagement.

    Args:
        db: Database session
        current_user: Current authenticated user
        context: Request context

    Returns:
        Dictionary with collection status information
    """
    try:
        # Get active collection flow - use first() to handle multiple rows
        result = await db.execute(
            select(CollectionFlow)
            .where(
                CollectionFlow.engagement_id == context.engagement_id,
                CollectionFlow.status.notin_(
                    [
                        CollectionFlowStatus.COMPLETED.value,
                        CollectionFlowStatus.CANCELLED.value,
                        CollectionFlowStatus.FAILED.value,
                    ]
                ),
            )
            .order_by(CollectionFlow.created_at.desc())
            .limit(1)  # Ensure we only get one row
        )
        collection_flow = result.scalar_one_or_none()

        if not collection_flow:
            return collection_serializers.build_no_active_flow_response()

        return collection_serializers.build_collection_status_response(collection_flow)

    except Exception as e:
        logger.error(safe_log_format("Error getting collection status: {e}", e=e))
        raise HTTPException(status_code=500, detail=str(e))


async def get_collection_flow(
    flow_id: str,
    db: AsyncSession,
    current_user: User,
    context: RequestContext,
) -> CollectionFlowResponse:
    """Get collection flow by ID with authorization.

    Args:
        flow_id: Collection flow ID
        db: Database session
        current_user: Current authenticated user
        context: Request context

    Returns:
        Collection flow details

    Raises:
        HTTPException: If flow not found or unauthorized
    """
    try:
        result = await db.execute(
            select(CollectionFlow).where(
                CollectionFlow.flow_id == UUID(flow_id),
                CollectionFlow.engagement_id == context.engagement_id,
            )
        )
        collection_flow = result.scalar_one_or_none()

        if not collection_flow:
            logger.warning(
                safe_log_format(
                    "Collection flow not found: flow_id={flow_id}, "
                    "engagement_id={engagement_id}",
                    flow_id=flow_id,
                    engagement_id=context.engagement_id,
                )
            )
            raise HTTPException(status_code=404, detail="Collection flow not found")

        return collection_serializers.serialize_collection_flow(collection_flow)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "Error getting collection flow: flow_id={flow_id}, error={e}",
                flow_id=flow_id,
                e=e,
            )
        )
        raise HTTPException(status_code=500, detail=str(e))


async def get_collection_gaps(
    flow_id: str,
    db: AsyncSession,
    current_user: User,
    context: RequestContext,
) -> List[CollectionGapAnalysisResponse]:
    """Get collection gap analysis for a flow.

    Args:
        flow_id: Collection flow ID
        db: Database session
        current_user: Current authenticated user
        context: Request context

    Returns:
        List of collection gap analyses

    Raises:
        HTTPException: If flow not found or unauthorized
    """
    try:
        # Verify flow ownership
        flow_result = await db.execute(
            select(CollectionFlow).where(
                CollectionFlow.flow_id == UUID(flow_id),
                CollectionFlow.engagement_id == context.engagement_id,
            )
        )
        collection_flow = flow_result.scalar_one_or_none()

        if not collection_flow:
            raise HTTPException(status_code=404, detail="Collection flow not found")

        # Get gap analyses
        gaps_result = await db.execute(
            select(CollectionGapAnalysis).where(
                CollectionGapAnalysis.collection_flow_id == collection_flow.id
            )
        )
        gaps = gaps_result.scalars().all()

        return [
            CollectionGapAnalysisResponse(
                id=str(gap.id),
                collection_flow_id=str(gap.collection_flow_id),
                asset_type=gap.asset_type,
                gap_category=gap.gap_category,
                gap_description=gap.gap_description,
                priority=gap.priority,
                recommended_actions=gap.recommended_actions,
                estimated_effort=gap.estimated_effort,
                created_at=gap.created_at,
                updated_at=gap.updated_at,
            )
            for gap in gaps
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "Error getting collection gaps: flow_id={flow_id}, error={e}",
                flow_id=flow_id,
                e=e,
            )
        )
        raise HTTPException(status_code=500, detail=str(e))


async def get_collection_readiness(
    flow_id: str,
    db: AsyncSession,
    current_user: User,
    context: RequestContext,
) -> Dict[str, Any]:
    """Assess collection readiness for a specific flow or current engagement.

    Args:
        flow_id: Collection flow ID to assess
        db: Database session
        current_user: Current authenticated user
        context: Request context

    Returns:
        Dictionary with readiness assessment
    """
    try:
        from uuid import UUID

        # Get asset count for engagement
        asset_result = await db.execute(
            select(func.count(Asset.id)).where(
                Asset.engagement_id == context.engagement_id
            )
        )
        asset_count = asset_result.scalar() or 0

        # Get the specific collection flow by ID
        flow_result = await db.execute(
            select(CollectionFlow).where(
                CollectionFlow.flow_id == UUID(flow_id),
                CollectionFlow.engagement_id == context.engagement_id,
            )
        )
        active_flow = flow_result.scalar_one_or_none()

        if not active_flow:
            # If specific flow not found, try to get any active flow as fallback
            flow_result = await db.execute(
                select(CollectionFlow)
                .where(
                    CollectionFlow.engagement_id == context.engagement_id,
                    CollectionFlow.status != CollectionFlowStatus.COMPLETED.value,
                )
                .order_by(CollectionFlow.created_at.desc())
            )
            active_flow = flow_result.scalar_one_or_none()

        # Calculate readiness score
        readiness_score = 0.0
        factors = []

        if asset_count > 0:
            readiness_score += 0.4
            factors.append(f"Assets available: {asset_count}")
        else:
            factors.append("No assets found - discovery may be needed")

        if active_flow:
            readiness_score += 0.3
            factors.append(f"Collection flow in progress: {active_flow.status}")
        else:
            factors.append("No active collection flow")

        # Check for completed discovery
        if asset_count >= 10:  # Arbitrary threshold for sufficient discovery
            readiness_score += 0.3
            factors.append("Sufficient asset coverage for collection")

        return {
            "readiness_score": round(readiness_score, 2),
            "asset_count": asset_count,
            "active_flow": {
                "id": str(active_flow.id) if active_flow else None,
                "status": active_flow.status if active_flow else None,
                "phase": active_flow.current_phase if active_flow else None,
            },
            "readiness_factors": factors,
            "recommendations": _get_readiness_recommendations(
                readiness_score, asset_count, active_flow
            ),
        }

    except Exception as e:
        logger.error(safe_log_format("Error assessing collection readiness: {e}", e=e))
        raise HTTPException(status_code=500, detail=str(e))


async def get_incomplete_flows(
    db: AsyncSession,
    current_user: User,
    context: RequestContext,
    limit: int = 50,
) -> List[CollectionFlowResponse]:
    """Get incomplete collection flows for current engagement.

    Args:
        db: Database session
        current_user: Current authenticated user
        context: Request context
        limit: Maximum number of flows to return

    Returns:
        List of incomplete collection flows
    """
    try:
        result = await db.execute(
            select(CollectionFlow)
            .where(
                CollectionFlow.engagement_id == context.engagement_id,
                CollectionFlow.status.in_(
                    [
                        CollectionFlowStatus.INITIALIZED.value,
                        CollectionFlowStatus.PLATFORM_DETECTION.value,
                        CollectionFlowStatus.AUTOMATED_COLLECTION.value,
                        CollectionFlowStatus.GAP_ANALYSIS.value,
                        CollectionFlowStatus.MANUAL_COLLECTION.value,
                        CollectionFlowStatus.FAILED.value,
                    ]
                ),
            )
            .order_by(CollectionFlow.created_at.desc())
            .limit(limit)
        )
        flows = result.scalars().all()

        return [
            collection_serializers.serialize_collection_flow(flow) for flow in flows
        ]

    except Exception as e:
        logger.error(safe_log_format("Error getting incomplete flows: {e}", e=e))
        raise HTTPException(status_code=500, detail=str(e))


def _get_readiness_recommendations(
    readiness_score: float, asset_count: int, active_flow: Optional[CollectionFlow]
) -> List[str]:
    """Generate readiness recommendations based on current state.

    Args:
        readiness_score: Calculated readiness score
        asset_count: Number of discovered assets
        active_flow: Active collection flow if any

    Returns:
        List of recommendation strings
    """
    recommendations = []

    if readiness_score < 0.3:
        recommendations.append("Run discovery flow first to identify assets")

    if asset_count < 5:
        recommendations.append("Increase asset coverage before starting collection")

    if active_flow and active_flow.status == CollectionFlowStatus.FAILED.value:
        recommendations.append("Review and resolve failed collection flow issues")

    if not active_flow and asset_count > 10:
        recommendations.append("Ready to start collection flow")

    if readiness_score >= 0.7:
        recommendations.append("All prerequisites met - proceed with collection")

    return recommendations
