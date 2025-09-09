"""
Collection Flow Query Operations
Read-only database operations for collection flows including status, flow details,
gaps, and readiness assessments.
"""

import logging
from datetime import datetime
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
    CollectionFlow,
    CollectionFlowStatus,
)
from app.schemas.collection_flow import (
    CollectionFlowResponse,
    CollectionGapAnalysisSummaryResponse,
)

# Import modular functions
from app.api.v1.endpoints import collection_serializers

# Re-export questionnaire functions for backward compatibility
from app.api.v1.endpoints.collection_crud_questionnaires import (
    get_adaptive_questionnaires,
)

__all__ = [
    "get_adaptive_questionnaires",
    "get_collection_status",
    "get_collection_flow",
    "get_collection_gaps",
    "get_collection_readiness",
    "get_incomplete_flows",
    "get_all_flows",
]

logger = logging.getLogger(__name__)


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
) -> CollectionGapAnalysisSummaryResponse:
    """Get collection gap analysis summary for a flow.

    Args:
        flow_id: Collection flow ID
        db: Database session
        current_user: Current authenticated user
        context: Request context

    Returns:
        Gap analysis summary with completeness metrics and structured gaps

    Raises:
        HTTPException: If flow not found or unauthorized
    """
    try:
        # Verify flow ownership and get collection flow
        flow_result = await db.execute(
            select(CollectionFlow).where(
                CollectionFlow.flow_id == UUID(flow_id),
                CollectionFlow.engagement_id == context.engagement_id,
                CollectionFlow.client_account_id == context.client_account_id,
            )
        )
        collection_flow = flow_result.scalar_one_or_none()

        if not collection_flow:
            raise HTTPException(status_code=404, detail="Collection flow not found")

        # Use gap analysis summary service to get or create summary
        from app.services.gap_analysis_summary_service import GapAnalysisSummaryService

        summary_service = GapAnalysisSummaryService(db)

        # First try to get existing summary
        gap_summary = await summary_service.get_gap_analysis_summary(
            collection_flow_id=str(collection_flow.id), context=context
        )

        # If no summary exists, try to ensure one from flow state (backwards compatibility)
        if not gap_summary:
            gap_summary = await summary_service.ensure_gap_summary_from_state(
                collection_flow_id=str(collection_flow.id), context=context
            )

        # If still no summary, return empty structure indicating analysis not yet performed
        if not gap_summary:
            return CollectionGapAnalysisSummaryResponse(
                id="",
                client_account_id=str(context.client_account_id),
                engagement_id=str(context.engagement_id),
                collection_flow_id=str(collection_flow.id),
                total_fields_required=0,
                fields_collected=0,
                fields_missing=0,
                completeness_percentage=0.0,
                data_quality_score=None,
                confidence_level=None,
                automation_coverage=None,
                critical_gaps=[],
                optional_gaps=[],
                gap_categories={},
                recommended_actions=[],
                questionnaire_requirements={},
                analyzed_at=collection_flow.created_at,
                updated_at=collection_flow.updated_at,
            )

        # Convert to response model using the model's to_dict method
        return CollectionGapAnalysisSummaryResponse(**gap_summary.to_dict())

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
    """Assess collection readiness for a specific flow with server-side thresholds.

    Returns structured readiness data with stable, typed fields and server-side
    thresholds for assessment transition decisions.

    Args:
        flow_id: Collection flow ID to assess
        db: Database session
        current_user: Current authenticated user
        context: Request context

    Returns:
        Dictionary with readiness assessment including server-side thresholds
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
            raise HTTPException(status_code=404, detail="Collection flow not found")

        # Get gap analysis summary for the flow
        from app.services.gap_analysis_summary_service import GapAnalysisSummaryService

        summary_service = GapAnalysisSummaryService(db)
        gap_summary = await summary_service.get_gap_analysis_summary(
            collection_flow_id=str(active_flow.id), context=context
        )

        # Server-side readiness thresholds (as specified in v4 plan)
        thresholds = {
            "apps_ready_for_assessment": 0,  # > 0 required
            "collection_quality_score": 60,  # >= 60 required
            "confidence_score": 50,  # >= 50 required
        }

        # Calculate apps ready for assessment
        apps_ready_count = 0
        if active_flow.collection_config and active_flow.collection_config.get(
            "has_applications"
        ):
            selected_apps = active_flow.collection_config.get(
                "selected_application_ids", []
            )
            apps_ready_count = len(selected_apps) if selected_apps else 0

        # Get quality and confidence scores
        quality_score = active_flow.collection_quality_score or 0
        confidence_score = active_flow.confidence_score or 0

        # Check each threshold and build missing requirements
        missing_requirements = []

        if apps_ready_count <= thresholds["apps_ready_for_assessment"]:
            missing_requirements.append(
                {
                    "type": "applications",
                    "message": "At least one application must be selected for assessment",
                    "current_value": apps_ready_count,
                    "required_value": thresholds["apps_ready_for_assessment"] + 1,
                    "action": "select_applications",
                }
            )

        if quality_score < thresholds["collection_quality_score"]:
            missing_requirements.append(
                {
                    "type": "quality",
                    "message": f"Collection quality score must be at least {thresholds['collection_quality_score']}%",
                    "current_value": quality_score,
                    "required_value": thresholds["collection_quality_score"],
                    "action": "complete_questionnaires",
                }
            )

        if confidence_score < thresholds["confidence_score"]:
            missing_requirements.append(
                {
                    "type": "confidence",
                    "message": f"Confidence score must be at least {thresholds['confidence_score']}%",
                    "current_value": confidence_score,
                    "required_value": thresholds["confidence_score"],
                    "action": "rerun_gap_analysis",
                }
            )

        # Determine overall readiness
        assessment_ready = len(missing_requirements) == 0

        # Calculate overall readiness score
        readiness_score = 0.0
        if apps_ready_count > 0:
            readiness_score += 0.4
        if quality_score >= thresholds["collection_quality_score"]:
            readiness_score += 0.3
        if confidence_score >= thresholds["confidence_score"]:
            readiness_score += 0.3

        return {
            # Core readiness status
            "assessment_ready": assessment_ready,
            "readiness_score": round(readiness_score, 2),
            # Application metrics
            "apps_ready_for_assessment": apps_ready_count,
            "selected_application_count": apps_ready_count,
            "total_asset_count": asset_count,
            # Quality metrics - nested structure to match frontend expectations
            "quality": {
                "collection_quality_score": quality_score,
                "confidence_score": confidence_score,
            },
            # Phase scores - nested structure to match frontend expectations
            "phase_scores": {
                "collection": quality_score,  # Use collection quality for collection phase
                "discovery": 0,  # Not applicable for collection flows
            },
            # Issues summary - nested structure to match frontend expectations
            "issues": {
                "total": len(missing_requirements),
                "critical": len(
                    [
                        req
                        for req in missing_requirements
                        if req.get("type") in ["applications", "quality"]
                    ]
                ),
                "warning": len(
                    [
                        req
                        for req in missing_requirements
                        if req.get("type") == "confidence"
                    ]
                ),
                "info": 0,
            },
            # Gap analysis metrics
            "gap_analysis_completed": gap_summary is not None,
            "critical_gaps_count": len(gap_summary.critical_gaps) if gap_summary else 0,
            "optional_gaps_count": len(gap_summary.optional_gaps) if gap_summary else 0,
            # Server-side thresholds for transparency
            "thresholds": thresholds,
            # Missing requirements for clear feedback
            "missing_requirements": missing_requirements,
            # Flow status
            "flow_status": active_flow.status,
            "current_phase": active_flow.current_phase,
            "flow_id": str(active_flow.flow_id),
            "engagement_id": str(active_flow.engagement_id),
            # Timestamp
            "updated_at": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
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


async def get_all_flows(
    db: AsyncSession,
    current_user: User,
    context: RequestContext,
    limit: int = 50,
) -> List[CollectionFlowResponse]:
    """Get all collection flows for current engagement (including completed ones).
    Args:
        db: Database session
        current_user: Current authenticated user
        context: Request context
        limit: Maximum number of flows to return
    Returns:
        List of all collection flows
    """
    try:
        result = await db.execute(
            select(CollectionFlow)
            .where(
                CollectionFlow.client_account_id == context.client_account_id,
                CollectionFlow.engagement_id == context.engagement_id,
            )
            .order_by(CollectionFlow.created_at.desc())
            .limit(limit)
        )
        flows = result.scalars().all()
        return [
            collection_serializers.serialize_collection_flow(flow) for flow in flows
        ]
    except Exception as e:
        logger.error(safe_log_format("Error getting all flows: {e}", e=e))
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
