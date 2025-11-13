"""
Assessment Enrichment Endpoints

Endpoints for triggering and managing automated asset enrichment.
Created October 2025 for Phase 5 integration testing.
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context_dependency
from app.core.database import get_db
from app.utils.json_sanitization import sanitize_for_json
from app.services.enrichment.auto_enrichment_pipeline import AutoEnrichmentPipeline
from .uuid_utils import ensure_uuid
from .query_helpers import get_assessment_flow, get_asset_ids

logger = logging.getLogger(__name__)

router = APIRouter()


class TriggerEnrichmentRequest(BaseModel):
    """Request model for triggering enrichment"""

    asset_ids: Optional[List[str]] = Field(
        None,
        description="Optional list of asset UUIDs to enrich. If not provided, enriches all flow assets.",
    )


class TriggerEnrichmentResponse(BaseModel):
    """Response model for enrichment trigger (Phase 2.3 - October 2025)"""

    flow_id: str = Field(..., description="Assessment flow UUID")
    total_assets: int = Field(..., description="Total number of assets enriched")
    enrichment_results: Dict[str, int] = Field(
        ..., description="Count of enriched assets per enrichment type"
    )
    elapsed_time_seconds: float = Field(..., description="Time taken for enrichment")
    batches_processed: Optional[int] = Field(
        None, description="Number of batches processed (configurable batch size)"
    )
    avg_batch_time_seconds: Optional[float] = Field(
        None, description="Average time per batch in seconds"
    )
    assets_per_minute: Optional[float] = Field(
        None, description="Enrichment throughput (assets per minute)"
    )
    readiness_recalculated: Optional[int] = Field(
        None, description="Number of assets with recalculated assessment readiness"
    )
    error: Optional[str] = Field(None, description="Error message if enrichment failed")


@router.post(
    "/{flow_id}/trigger-enrichment",
    response_model=TriggerEnrichmentResponse,
    summary="Trigger Asset Enrichment",
    description="""
    Triggers automated enrichment for assets in the assessment flow.

    This endpoint:
    1. Validates flow exists and user has access
    2. Gets asset IDs (from request or from flow)
    3. Runs 7 enrichment agents concurrently:
       - ComplianceEnrichmentAgent → asset_compliance_flags
       - LicensingEnrichmentAgent → asset_licenses
       - VulnerabilityEnrichmentAgent → asset_vulnerabilities
       - ResilienceEnrichmentAgent → asset_resilience
       - DependencyEnrichmentAgent → asset_dependencies
       - ProductMatchingAgent → asset_product_links
       - FieldConflictAgent → asset_field_conflicts
    4. Recalculates assessment readiness scores
    5. Returns enrichment statistics

    **Phase 2.3 Performance Optimization (October 2025)**:
    - Batch processing: Configurable batch size (default 10 assets)
    - Backpressure control: Max 3 concurrent batches (configurable)
    - Rate limiting: Max 10 batches per minute (configurable)
    - Progress tracking: ETA logging and metrics
    - Performance target: 100 assets in < 5 minutes

    **ADR Compliance**:
    - ADR-015: Uses TenantScopedAgentPool for persistent agents
    - ADR-024: Uses TenantMemoryManager (CrewAI memory=False)
    - LLM Tracking: All calls use multi_model_service.generate_response()
    """,
)
async def trigger_enrichment(
    flow_id: str,
    request: TriggerEnrichmentRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context_dependency),
) -> TriggerEnrichmentResponse:
    """
    Trigger automated enrichment for assessment flow assets.

    Args:
        flow_id: Assessment flow UUID
        request: Optional asset_ids to enrich (enriches all if not provided)
        db: Database session
        context: Request context with tenant scoping

    Returns:
        Enrichment statistics including counts per enrichment type
    """
    try:
        # Get assessment flow with tenant scoping
        flow = await get_assessment_flow(
            db, flow_id, context.client_account_id, context.engagement_id
        )

        # Determine which assets to enrich
        if request.asset_ids:
            # Validate provided asset IDs
            try:
                asset_uuids = [UUID(aid) for aid in request.asset_ids]
            except (ValueError, TypeError) as e:
                raise HTTPException(
                    status_code=400, detail=f"Invalid asset_id format: {str(e)}"
                )

            # Verify assets belong to this flow
            flow_asset_ids = get_asset_ids(flow)
            flow_asset_id_set = {str(aid) for aid in flow_asset_ids}
            invalid_ids = [
                aid for aid in request.asset_ids if aid not in flow_asset_id_set
            ]

            if invalid_ids:
                raise HTTPException(
                    status_code=400,
                    detail=f"Asset IDs not found in flow: {invalid_ids}",
                )

            logger.info(
                f"Triggering enrichment for {len(asset_uuids)} specific assets in flow {flow_id}"
            )
        else:
            # Enrich all flow assets
            flow_asset_ids = get_asset_ids(flow)
            asset_uuids = [
                UUID(aid) if isinstance(aid, str) else aid for aid in flow_asset_ids
            ]

            logger.info(
                f"Triggering enrichment for all {len(asset_uuids)} assets in flow {flow_id}"
            )

        if not asset_uuids:
            return TriggerEnrichmentResponse(
                flow_id=flow_id,
                total_assets=0,
                enrichment_results={},
                elapsed_time_seconds=0.0,
                error="No assets to enrich in flow",
            )

        # Initialize AutoEnrichmentPipeline
        pipeline = AutoEnrichmentPipeline(
            db=db,
            client_account_id=ensure_uuid(context.client_account_id),
            engagement_id=ensure_uuid(context.engagement_id),
        )

        # Trigger enrichment (runs 7 agents concurrently)
        result = await pipeline.trigger_auto_enrichment(asset_uuids)

        logger.info(
            f"Enrichment completed for flow {flow_id}: "
            f"{result['total_assets']} assets in {result['elapsed_time_seconds']:.2f}s"
        )

        # Sanitize result data before creating Pydantic model (ADR-029)
        sanitized_result = sanitize_for_json(result)

        return TriggerEnrichmentResponse(
            flow_id=flow_id,
            total_assets=sanitized_result["total_assets"],
            enrichment_results=sanitized_result["enrichment_results"],
            elapsed_time_seconds=sanitized_result["elapsed_time_seconds"],
            batches_processed=sanitized_result.get("batches_processed"),
            avg_batch_time_seconds=sanitized_result.get("avg_batch_time_seconds"),
            assets_per_minute=sanitized_result.get("assets_per_minute"),
            readiness_recalculated=sanitized_result.get("readiness_recalculated"),
            error=sanitized_result.get("error"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to trigger enrichment for flow {flow_id}: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to trigger enrichment: {str(e)}"
        )


@router.get(
    "/{flow_id}/enrichment-status",
    summary="Get Enrichment Status",
    description="""
    Gets current enrichment status for assessment flow assets.

    Returns counts of how many assets have data in each enrichment table:
    - asset_compliance_flags
    - asset_licenses
    - asset_vulnerabilities
    - asset_resilience
    - asset_dependencies
    - asset_product_links
    - asset_field_conflicts
    """,
)
async def get_enrichment_status(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context_dependency),
) -> Dict[str, Any]:
    """
    Get enrichment status for assessment flow.

    Returns:
        Counts of enriched assets per enrichment table
    """
    try:
        from app.services.assessment.application_resolver import (
            AssessmentApplicationResolver,
        )

        # Get assessment flow with tenant scoping
        flow = await get_assessment_flow(
            db, flow_id, context.client_account_id, context.engagement_id
        )

        # Get asset IDs
        asset_ids = get_asset_ids(flow)

        if not asset_ids:
            return {
                "flow_id": flow_id,
                "total_assets": 0,
                "enrichment_status": {
                    "compliance_flags": 0,
                    "licenses": 0,
                    "vulnerabilities": 0,
                    "resilience": 0,
                    "dependencies": 0,
                    "product_links": 0,
                    "field_conflicts": 0,
                },
            }

        # Initialize resolver
        resolver = AssessmentApplicationResolver(
            db=db,
            client_account_id=ensure_uuid(context.client_account_id),
            engagement_id=ensure_uuid(context.engagement_id),
        )

        # Calculate enrichment status
        enrichment_status_obj = await resolver.calculate_enrichment_status(
            [UUID(aid) if isinstance(aid, str) else aid for aid in asset_ids]
        )

        return sanitize_for_json(
            {
                "flow_id": flow_id,
                "total_assets": len(asset_ids),
                "enrichment_status": enrichment_status_obj.model_dump(),
            }
        )

    except Exception as e:
        logger.error(
            f"Failed to get enrichment status for flow {flow_id}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to get enrichment status: {str(e)}"
        )
