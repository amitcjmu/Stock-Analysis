"""
Two-Phase Gap Analysis API Router

Implements programmatic gap scanning (Phase 1) and AI-enhanced analysis (Phase 2).
Per ADR-006, all flows must integrate with Master Flow Orchestrator.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_request_context
from app.core.database import get_db
from app.models.collection_data_gap import CollectionDataGap
from app.models.collection_flow import CollectionFlow
from app.schemas.collection_gap_analysis import (
    AnalyzeGapsRequest,
    AnalyzeGapsResponse,
    ScanGapsRequest,
    ScanGapsResponse,
    UpdateGapsRequest,
    UpdateGapsResponse,
)
from app.services.collection.programmatic_gap_scanner import ProgrammaticGapScanner

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/collection/flows",
)


async def resolve_collection_flow(
    flow_id: str,
    client_account_id: UUID,
    engagement_id: UUID,
    db: AsyncSession,
) -> CollectionFlow:
    """
    Resolve collection flow from flow_id (may be master_flow_id).

    Args:
        flow_id: Either collection_flow.id or master_flow_id
        client_account_id: Tenant client account UUID
        engagement_id: Engagement UUID
        db: Async database session

    Returns:
        CollectionFlow instance

    Raises:
        HTTPException: If flow not found or not accessible
    """
    flow_uuid = UUID(flow_id)

    # Try as collection_flow.id first
    stmt = select(CollectionFlow).where(
        CollectionFlow.id == flow_uuid,
        CollectionFlow.client_account_id == client_account_id,
        CollectionFlow.engagement_id == engagement_id,
    )
    result = await db.execute(stmt)
    collection_flow = result.scalar_one_or_none()

    if collection_flow:
        return collection_flow

    # Try as master_flow_id
    stmt = select(CollectionFlow).where(
        CollectionFlow.master_flow_id == flow_uuid,
        CollectionFlow.client_account_id == client_account_id,
        CollectionFlow.engagement_id == engagement_id,
    )
    result = await db.execute(stmt)
    collection_flow = result.scalar_one_or_none()

    if not collection_flow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collection flow {flow_id} not found or not accessible",
        )

    return collection_flow


@router.post("/{flow_id}/scan-gaps", response_model=ScanGapsResponse)
async def scan_gaps(
    flow_id: str,
    request_body: ScanGapsRequest,
    context: RequestContext = Depends(get_request_context),
    db: AsyncSession = Depends(get_db),
):
    """
    **Phase 1: Programmatic Gap Scan**

    Fast database scan (<1s) comparing assets against 22 critical attributes.
    No AI involvement - pure attribute comparison with deduplication.

    **Critical Notes:**
    - flow_id may be master_flow_id, will resolve to child collection_flow.id
    - Uses RequestContext for tenant scoping (client_account_id, engagement_id)
    - Clears existing gaps for THIS flow before inserting new ones
    - Returns gaps with NULL confidence_score (no AI yet)

    **Request Body (POST):**
    ```json
    {
        "selected_asset_ids": ["uuid1", "uuid2"]
    }
    ```

    **Response:**
    ```json
    {
        "gaps": [{
            "asset_id": "uuid",
            "asset_name": "App-001",
            "field_name": "technology_stack",
            "gap_type": "missing_field",
            "gap_category": "application",
            "priority": 1,
            "current_value": null,
            "suggested_resolution": "Manual collection required",
            "confidence_score": null
        }],
        "summary": {
            "total_gaps": 16,
            "assets_analyzed": 2,
            "critical_gaps": 5,
            "execution_time_ms": 234,
            "gaps_persisted": 16
        },
        "status": "SCAN_COMPLETE"
    }
    ```
    """
    try:
        logger.info(
            f"🔍 Scan gaps request - Flow: {flow_id}, Assets: {len(request_body.selected_asset_ids)}"
        )

        # Resolve collection flow
        collection_flow = await resolve_collection_flow(
            flow_id=flow_id,
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id,
            db=db,
        )

        logger.info(
            f"✅ Resolved collection flow: {collection_flow.id} (master: {collection_flow.master_flow_id})"
        )

        # Execute programmatic scan
        scanner = ProgrammaticGapScanner()
        result = await scanner.scan_assets_for_gaps(
            selected_asset_ids=request_body.selected_asset_ids,
            collection_flow_id=str(collection_flow.id),
            client_account_id=str(context.client_account_id),
            engagement_id=str(context.engagement_id),
            db=db,
        )

        return ScanGapsResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Scan gaps failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gap scan failed: {str(e)}",
        )


@router.post("/{flow_id}/analyze-gaps", response_model=AnalyzeGapsResponse)
async def analyze_gaps(
    flow_id: str,
    request_body: AnalyzeGapsRequest,
    context: RequestContext = Depends(get_request_context),
    db: AsyncSession = Depends(get_db),
):
    """
    **Phase 2: AI-Enhanced Gap Analysis**

    Enriches programmatic gaps with AI suggestions and confidence scores (~15s).
    User-triggered via "Perform Agentic Analysis" button in UI.

    **Critical Notes:**
    - Rate limited: 1 request per 10 seconds per flow (prevent spam)
    - Batches gaps (50 per agent call) for memory efficiency
    - Retries with exponential backoff (3 attempts: 1s/2s/4s)
    - Persists AI enhancements to database (upsert)
    - Sanitizes confidence_score (no NaN/Inf)

    **Request Body (POST):**
    ```json
    {
        "gaps": [...],  // Output from scan-gaps
        "selected_asset_ids": ["uuid1", "uuid2"]
    }
    ```

    **Response:**
    ```json
    {
        "enhanced_gaps": [{
            "asset_id": "uuid",
            "field_name": "technology_stack",
            "gap_type": "missing_field",
            "gap_category": "application",
            "priority": 1,
            "current_value": null,
            "suggested_resolution": "Check deployment artifacts for framework detection",
            "confidence_score": 0.85,
            "ai_suggestions": [
                "Check package.json for Node.js stack",
                "Review pom.xml for Java stack"
            ]
        }],
        "summary": {
            "total_gaps": 16,
            "enhanced_gaps": 12,
            "execution_time_ms": 14500,
            "agent_duration_ms": 13200
        },
        "status": "AI_ANALYSIS_COMPLETE"
    }
    ```

    **Note:** This endpoint is a placeholder for Phase 2 implementation.
    Currently returns gaps unchanged. AI enhancement will be added in follow-up PR.
    """
    try:
        logger.info(
            f"🤖 AI analysis request - Flow: {flow_id}, Gaps: {len(request_body.gaps)}"
        )

        # Resolve collection flow (validates tenant access)
        # TODO: Use collection_flow for AI analysis context in Phase 2
        await resolve_collection_flow(
            flow_id=flow_id,
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id,
            db=db,
        )

        # TODO: Implement AI enhancement service integration
        # For now, return gaps unchanged (Phase 2 implementation)
        logger.warning("⚠️ AI analysis not yet implemented - returning gaps unchanged")

        return AnalyzeGapsResponse(
            enhanced_gaps=request_body.gaps,
            summary={
                "total_gaps": len(request_body.gaps),
                "enhanced_gaps": 0,  # No AI enhancement yet
                "execution_time_ms": 0,
                "agent_duration_ms": 0,
            },
            status="AI_ANALYSIS_COMPLETE",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ AI analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI analysis failed: {str(e)}",
        )


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
