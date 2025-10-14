"""
Gap Update and Query Endpoints
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_request_context
from app.core.database import get_db
from app.models.collection_data_gap import CollectionDataGap
from app.schemas.collection_gap_analysis import (
    UpdateGapsRequest,
    UpdateGapsResponse,
)

from .utils import resolve_collection_flow

logger = logging.getLogger(__name__)

router = APIRouter()


@router.put("/{flow_id}/update-gaps", response_model=UpdateGapsResponse)
async def update_gaps(
    flow_id: str,
    request_body: UpdateGapsRequest,
    context: RequestContext = Depends(get_request_context),
    db: AsyncSession = Depends(get_db),
):
    """
    **Save Manual Gap Edits**

    Updates gap resolutions from user edits in AG Grid.
    Explicit save button per row (no auto-save per user requirement).

    **Request Body (PUT):**
    ```json
    {
        "updates": [{
            "gap_id": "uuid",
            "field_name": "technology_stack",
            "resolved_value": "Node.js, Express, PostgreSQL",
            "resolution_status": "resolved",
            "resolution_method": "manual_entry"
        }]
    }
    ```

    **Response:**
    ```json
    {
        "updated_gaps": 1,
        "gaps_resolved": 1,
        "remaining_gaps": 15
    }
    ```

    **Auto-skip Logic:**
    If all gaps are resolved, flow automatically transitions to assessment phase.
    """
    try:
        logger.info(
            f"💾 Update gaps request - Flow: {flow_id}, Updates: {len(request_body.updates)}"
        )
        # DEBUG: Log first update for troubleshooting
        if request_body.updates:
            first_update = request_body.updates[0]
            logger.info(
                f"DEBUG: First update - gap_id={first_update.gap_id}, "
                f"status={first_update.resolution_status}, "
                f"method={first_update.resolution_method}"
            )

        # Resolve collection flow
        collection_flow = await resolve_collection_flow(
            flow_id=flow_id,
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id,
            db=db,
        )

        updated_count = 0
        resolved_count = 0

        # Update each gap
        for update in request_body.updates:
            gap_uuid = UUID(update.gap_id)

            # Verify gap belongs to this flow (tenant isolation)
            stmt = select(CollectionDataGap).where(
                CollectionDataGap.id == gap_uuid,
                CollectionDataGap.collection_flow_id == collection_flow.id,
            )
            result = await db.execute(stmt)
            gap = result.scalar_one_or_none()

            if not gap:
                logger.warning(
                    f"⚠️ Gap {gap_uuid} not found or not in flow {collection_flow.id}"
                )
                continue

            # Update gap fields
            gap.resolved_value = update.resolved_value
            gap.resolution_status = update.resolution_status
            gap.resolution_method = update.resolution_method

            if update.resolution_status == "resolved":
                gap.resolved_at = func.now()
                gap.resolved_by = str(context.user_id) if context.user_id else "system"
                resolved_count += 1

            updated_count += 1

        await db.commit()

        # Count remaining pending gaps
        stmt = select(func.count(CollectionDataGap.id)).where(
            CollectionDataGap.collection_flow_id == collection_flow.id,
            CollectionDataGap.resolution_status == "pending",
        )
        result = await db.execute(stmt)
        remaining_gaps = result.scalar()

        logger.info(
            f"✅ Updated {updated_count} gaps ({resolved_count} resolved, {remaining_gaps} remaining)"
        )

        # TODO: Auto-skip to assessment if all gaps resolved
        # if remaining_gaps == 0:
        #     await orchestrator.execute_phase(
        #         flow_id=collection_flow.master_flow_id,
        #         phase_name="assessment",
        #         phase_input={"collection_flow_id": str(collection_flow.id)}
        #     )

        return UpdateGapsResponse(
            updated_gaps=updated_count,
            gaps_resolved=resolved_count,
            remaining_gaps=remaining_gaps,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Update gaps failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gap update failed: {str(e)}",
        )


@router.get("/{flow_id}/gaps")
async def get_gaps(
    flow_id: str,
    context: RequestContext = Depends(get_request_context),
    db: AsyncSession = Depends(get_db),
):
    """
    **Get Existing Gaps for Flow**

    Fetches all gaps (both programmatic and AI-enhanced) for a collection flow.
    Supports both collection_flow.id and master_flow_id.

    **Response:**
    ```json
    [{
        "id": "uuid",
        "asset_id": "uuid",
        "asset_name": "App-001",
        "field_name": "technology_stack",
        "gap_type": "missing_field",
        "gap_category": "application",
        "priority": 1,
        "current_value": null,
        "suggested_resolution": "Check deployment artifacts",
        "confidence_score": 0.85,
        "ai_suggestions": ["Check package.json"],
        "resolution_status": "pending"
    }]
    ```
    """
    try:
        logger.info(f"📖 Get gaps request - Flow: {flow_id}")

        # Resolve collection flow (supports both id and master_flow_id)
        collection_flow = await resolve_collection_flow(
            flow_id=flow_id,
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id,
            db=db,
        )

        # Query pending gaps for this flow with asset names (join with assets table)
        from app.models.asset.models import Asset

        stmt = (
            select(CollectionDataGap, Asset.name)
            .join(
                Asset,
                CollectionDataGap.asset_id == Asset.id,
                isouter=True,
            )
            .where(
                CollectionDataGap.collection_flow_id == collection_flow.id,
                CollectionDataGap.resolution_status
                == "pending",  # Only unresolved gaps
            )
        )
        result = await db.execute(stmt)
        rows = result.all()

        # Convert to dict format for response
        gaps_list = []
        for gap, asset_name in rows:
            gaps_list.append(
                {
                    "id": str(gap.id),
                    "asset_id": str(gap.asset_id),
                    "asset_name": asset_name or "Unknown Asset",
                    "field_name": gap.field_name,
                    "gap_type": gap.gap_type,
                    "gap_category": gap.gap_category,
                    "priority": gap.priority,
                    "current_value": gap.resolved_value,  # Use resolved_value as current_value
                    "suggested_resolution": gap.suggested_resolution,
                    "confidence_score": gap.confidence_score,
                    "ai_suggestions": gap.ai_suggestions or [],
                    "resolution_status": gap.resolution_status,
                    "resolved_value": gap.resolved_value,
                    "resolved_by": gap.resolved_by,
                    "resolved_at": (
                        gap.resolved_at.isoformat() if gap.resolved_at else None
                    ),
                }
            )

        logger.info(f"✅ Retrieved {len(gaps_list)} gaps for flow {collection_flow.id}")
        return gaps_list

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Get gaps failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve gaps: {str(e)}",
        )
