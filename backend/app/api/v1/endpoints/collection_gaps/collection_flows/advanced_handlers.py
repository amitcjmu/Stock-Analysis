"""
Advanced route handlers for collection flows API endpoints.

This module contains complex handlers extracted from handlers.py for better organization:
- refresh_completeness_metrics_handler: Force recalculation of metrics
- transition_to_assessment_handler: Create assessment flow from collection
"""

import logging
from typing import Any, Dict

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.repositories.collection_flow_repository import CollectionFlowRepository

from .utils import (
    calculate_completeness_metrics,
    calculate_pending_gaps,
    get_existing_data_snapshot,
)

logger = logging.getLogger(__name__)


async def refresh_completeness_metrics_handler(
    flow_id: str,
    db: AsyncSession,
    context: RequestContext,
) -> Dict[str, Any]:
    """
    Refresh completeness metrics for a collection flow.

    Forces recalculation of all completeness metrics and returns updated values.
    """
    try:
        # Verify flow exists
        collection_repo = CollectionFlowRepository(
            db, context.client_account_id, context.engagement_id
        )
        collection_flow = await collection_repo.get_by_filters(flow_id=flow_id)

        if not collection_flow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Collection flow not found",
            )

        # Force refresh by clearing any cached data (if applicable)
        # This would typically invalidate caches or trigger recalculation

        # Get fresh data snapshot
        existing_data_snapshot = await get_existing_data_snapshot(
            db, context.client_account_id, context.engagement_id
        )

        # Recalculate completeness metrics
        completeness_by_category = await calculate_completeness_metrics(
            db, context.client_account_id, context.engagement_id
        )

        # Calculate overall completeness
        if completeness_by_category:
            overall_completeness = sum(completeness_by_category.values()) / len(
                completeness_by_category
            )
        else:
            overall_completeness = 0.0

        # Get updated gaps count
        pending_gaps = await calculate_pending_gaps(
            db, context.client_account_id, context.engagement_id
        )

        logger.info(
            f"✅ Refreshed completeness metrics for flow {flow_id} - "
            f"Overall: {overall_completeness:.1f}%, Pending gaps: {pending_gaps}"
        )

        return {
            "flow_id": flow_id,
            "overall_completeness": round(overall_completeness, 2),
            "completeness_by_category": completeness_by_category,
            "pending_gaps": pending_gaps,
            "last_calculated": "now",  # Could add actual timestamp
            "categories": (
                list(completeness_by_category.keys())
                if completeness_by_category
                else []
            ),
            "refreshed": True,
            "data_points_analyzed": (
                len(existing_data_snapshot) if existing_data_snapshot else 0
            ),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to refresh completeness metrics for flow {flow_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh completeness metrics",
        )


async def transition_to_assessment_handler(
    flow_id: str,
    db: AsyncSession,
    context: RequestContext,
) -> Dict[str, Any]:
    """
    Create assessment flow from completed collection flow.

    This endpoint uses CollectionTransitionService to:
    1. Validate collection flow is ready for assessment
    2. Create new assessment flow via AssessmentFlowRepository
    3. Link assessment_flow_id to collection flow metadata
    4. Return assessment flow details for navigation

    Per docs/planning/dependency-to-assessment/README.md, this enables
    Collection Complete page to show "Continue to Assessment" button.
    """
    try:
        from uuid import UUID

        from app.services.collection_transition_service import (
            CollectionTransitionService,
        )

        # Verify flow exists and get UUID
        collection_repo = CollectionFlowRepository(
            db, context.client_account_id, context.engagement_id
        )
        collection_flow = await collection_repo.get_by_filters(flow_id=flow_id)

        if not collection_flow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection flow {flow_id} not found",
            )

        flow_uuid = UUID(flow_id) if isinstance(flow_id, str) else flow_id

        # Initialize transition service
        transition_service = CollectionTransitionService(db, context)

        # Validate readiness (checks assessment_ready flag + gaps)
        readiness = await transition_service.validate_readiness(flow_uuid)

        if not readiness.is_ready:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "collection_not_ready",
                    "message": readiness.reason,
                    "missing_requirements": readiness.missing_requirements,
                    "confidence": readiness.confidence,
                },
            )

        # Create assessment flow (uses AssessmentFlowRepository + MFO pattern)
        transition_result = await transition_service.create_assessment_flow(flow_uuid)

        # Commit transaction
        await db.commit()

        logger.info(
            f"✅ Created assessment flow {transition_result.assessment_flow_id} "
            f"from collection flow {flow_id}"
        )

        return {
            "status": "success",
            "message": "Assessment flow created successfully",
            "assessment_flow_id": str(transition_result.assessment_flow_id),
            "collection_flow_id": flow_id,
            "transitioned_at": transition_result.created_at.isoformat(),
            "readiness_confidence": readiness.confidence,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to transition flow {flow_id} to assessment: {e}", exc_info=True
        )
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create assessment flow: {str(e)}",
        )
