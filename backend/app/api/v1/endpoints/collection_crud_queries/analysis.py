"""
Collection Flow Analysis Operations
Complex analysis operations including gap analysis and readiness assessments.
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

# Removed unused import: CollectionGapAnalysisSummaryResponse
# from app.schemas.collection_flow import CollectionGapAnalysisSummaryResponse

logger = logging.getLogger(__name__)


async def get_collection_gaps(
    flow_id: str,
    db: AsyncSession,
    current_user: User,
    context: RequestContext,
) -> List[Dict[str, Any]]:
    """Get collection data gaps for a flow.

    Args:
        flow_id: Collection flow ID
        db: Database session
        current_user: Current authenticated user
        context: Request context

    Returns:
        List of gap records

    Raises:
        HTTPException: If flow not found or unauthorized
    """
    try:
        from app.models.collection_data_gap import CollectionDataGap

        # Verify flow ownership
        flow_result = await db.execute(
            select(CollectionFlow).where(
                CollectionFlow.id == UUID(flow_id),  # Query by id (primary key)
                CollectionFlow.engagement_id == context.engagement_id,
                CollectionFlow.client_account_id == context.client_account_id,
            )
        )
        collection_flow = flow_result.scalar_one_or_none()

        if not collection_flow:
            raise HTTPException(status_code=404, detail="Collection flow not found")

        # Query gaps with asset join to get asset_name
        gaps_result = await db.execute(
            select(CollectionDataGap, Asset.name)
            .outerjoin(Asset, CollectionDataGap.asset_id == Asset.id)
            .where(CollectionDataGap.collection_flow_id == collection_flow.id)
            .order_by(CollectionDataGap.priority.desc(), CollectionDataGap.created_at)
        )

        gaps_with_assets = gaps_result.all()

        # Convert to response format matching frontend DataGap interface
        gap_list = []
        for gap, asset_name in gaps_with_assets:
            gap_list.append(
                {
                    "asset_id": str(gap.asset_id),
                    "asset_name": asset_name or "Unknown",
                    "field_name": gap.field_name,
                    "gap_type": gap.gap_type,
                    "gap_category": gap.gap_category,
                    "priority": gap.priority,
                    "current_value": gap.resolved_value,  # Current/resolved value
                    "suggested_resolution": gap.suggested_resolution or "",
                    "confidence_score": gap.confidence_score,
                    "ai_suggestions": gap.ai_suggestions or [],
                }
            )

        return gap_list

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
                CollectionFlow.flow_id
                == UUID(flow_id),  # Query by flow_id (business ID)
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

        # CRITICAL FIX: Check if all gaps are resolved before marking as assessment ready
        # Count pending gaps for this flow
        from app.models.collection_data_gap import CollectionDataGap

        pending_gaps_result = await db.execute(
            select(func.count(CollectionDataGap.id)).where(
                CollectionDataGap.collection_flow_id == active_flow.id,
                CollectionDataGap.resolution_status == "pending",
            )
        )
        pending_gaps_count = pending_gaps_result.scalar() or 0

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

        # CRITICAL FIX: Add check for pending gaps
        if pending_gaps_count > 0:
            missing_requirements.append(
                {
                    "type": "gaps",
                    "message": f"{pending_gaps_count} data gap(s) must be resolved before assessment",
                    "current_value": pending_gaps_count,
                    "required_value": 0,
                    "action": "resolve_gaps",
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
            "pending_gaps_count": pending_gaps_count,  # CRITICAL FIX: Include pending gaps count
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
