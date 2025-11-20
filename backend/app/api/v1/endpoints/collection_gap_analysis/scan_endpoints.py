"""
Phase 1: Programmatic Gap Scanning Endpoints
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_request_context
from app.core.database import get_db
from app.schemas.collection_gap_analysis import (
    ScanGapsRequest,
    ScanGapsResponse,
)
from app.services.collection.programmatic_gap_scanner import ProgrammaticGapScanner

from .utils import resolve_collection_flow

logger = logging.getLogger(__name__)

router = APIRouter()


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

        # Persist scan summary to gap_analysis_results for frontend retrieval
        from sqlalchemy import update
        from app.models.collection_flow import CollectionFlow
        from uuid import UUID

        try:
            await db.execute(
                update(CollectionFlow)
                .where(CollectionFlow.id == UUID(str(collection_flow.id)))
                .values(
                    gap_analysis_results={
                        "summary": result.get("summary", {}),
                        "status": result.get("status", "SCAN_COMPLETE"),
                    }
                )
            )
            await db.commit()
            logger.info("💾 Persisted scan summary to gap_analysis_results")
        except Exception as store_error:
            logger.error(f"⚠️ Failed to persist scan summary: {store_error}")
            # Don't fail the request if persistence fails

        return ScanGapsResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Scan gaps failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gap scan failed: {str(e)}",
        )
