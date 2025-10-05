"""
Phase 2: AI-Enhanced Gap Analysis Endpoints
"""

import logging
import time

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_request_context
from app.core.database import get_db
from app.schemas.collection_gap_analysis import (
    AnalyzeGapsRequest,
    AnalyzeGapsResponse,
)

from .utils import resolve_collection_flow

logger = logging.getLogger(__name__)

router = APIRouter()


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
        start_time = time.time()

        logger.info(
            f"🤖 AI analysis request - Flow: {flow_id}, Gaps: {len(request_body.gaps)}"
        )

        # Resolve collection flow (validates tenant access)
        collection_flow = await resolve_collection_flow(
            flow_id=flow_id,
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id,
            db=db,
        )

        # Load assets for AI context
        from app.services.collection.gap_analysis.data_loader import load_assets

        assets = await load_assets(
            request_body.selected_asset_ids,
            str(context.client_account_id),
            str(context.engagement_id),
            db,
        )

        if not assets:
            logger.warning(
                "⚠️ No assets found for AI analysis - returning gaps unchanged"
            )
            return AnalyzeGapsResponse(
                enhanced_gaps=request_body.gaps,
                summary={
                    "total_gaps": len(request_body.gaps),
                    "enhanced_gaps": 0,
                    "execution_time_ms": int((time.time() - start_time) * 1000),
                    "agent_duration_ms": 0,
                },
                status="AI_ANALYSIS_COMPLETE",
            )

        # Initialize gap analysis service
        from app.services.collection.gap_analysis.service import GapAnalysisService

        gap_service = GapAnalysisService(
            client_account_id=str(context.client_account_id),
            engagement_id=str(context.engagement_id),
            collection_flow_id=str(collection_flow.id),
        )

        # Convert Pydantic gaps to dict format for AI enhancement
        gaps_for_ai = [gap.model_dump() for gap in request_body.gaps]

        # Run tier_2 AI analysis to enhance gaps (no persistence to avoid duplicates)
        logger.info(
            f"🤖 Running tier_2 AI analysis to enhance {len(gaps_for_ai)} programmatic gaps"
        )
        ai_result = await gap_service._run_tier_2_ai_analysis_no_persist(
            assets=assets,
            collection_flow_id=str(collection_flow.id),
            gaps=gaps_for_ai,  # Pass programmatic gaps for enhancement
        )

        # Extract AI-enhanced gaps from result
        ai_gaps_dict = ai_result.get("gaps", {})
        all_ai_gaps = []
        for priority_list in ai_gaps_dict.values():
            if isinstance(priority_list, list):
                all_ai_gaps.extend(priority_list)

        # Merge AI enhancements with input gaps
        enhanced_gaps = []
        for input_gap in request_body.gaps:
            # Find matching AI gap by field_name and asset_id
            # Note: input_gap is a DataGap Pydantic model, use dot notation
            # AI gaps are dictionaries from parse_task_output, use .get()
            matching_ai_gap = next(
                (
                    ag
                    for ag in all_ai_gaps
                    if ag.get("field_name") == input_gap.field_name
                    and ag.get("asset_id") == input_gap.asset_id
                ),
                None,
            )

            if matching_ai_gap:
                # Merge AI enhancements into input gap
                # Convert Pydantic model to dict first
                enhanced_gap = input_gap.model_dump()  # Convert to dict
                enhanced_gap["confidence_score"] = matching_ai_gap.get(
                    "confidence_score"
                )
                enhanced_gap["ai_suggestions"] = matching_ai_gap.get(
                    "ai_suggestions", []
                )
                enhanced_gap["suggested_resolution"] = matching_ai_gap.get(
                    "suggested_resolution", input_gap.suggested_resolution
                )
                enhanced_gaps.append(enhanced_gap)
            else:
                # No AI match, keep original (convert to dict)
                enhanced_gaps.append(input_gap.model_dump())

        execution_time_ms = int((time.time() - start_time) * 1000)
        enhanced_count = sum(
            1 for g in enhanced_gaps if g.get("confidence_score") is not None
        )

        logger.info(
            f"✅ AI analysis complete - Enhanced {enhanced_count}/{len(enhanced_gaps)} gaps in {execution_time_ms}ms"
        )

        return AnalyzeGapsResponse(
            enhanced_gaps=enhanced_gaps,
            summary={
                "total_gaps": len(enhanced_gaps),
                "enhanced_gaps": enhanced_count,
                "execution_time_ms": execution_time_ms,
                "agent_duration_ms": ai_result.get("summary", {}).get(
                    "execution_time_ms", 0
                ),
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
