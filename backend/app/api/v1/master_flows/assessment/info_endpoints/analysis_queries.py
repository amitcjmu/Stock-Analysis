"""
Assessment analysis query endpoints (GAP-4 FIX).

GET endpoints for retrieving assessment analysis data:
- Application components
- Tech debt analysis
- 6R decisions
- Component treatments

These endpoints provide access to assessment analysis data stored in database tables,
replacing the deprecated assessment-status workaround.
"""

import logging
from typing import Any, Dict

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context_dependency
from app.core.database import get_db
from app.utils.json_sanitization import sanitize_for_json
from ..query_helpers import get_assessment_flow

from . import router

logger = logging.getLogger(__name__)


@router.get("/{flow_id}/components")
async def get_assessment_components(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context_dependency),
) -> Dict[str, Any]:
    """
    Get application components for assessment flow.

    GAP-4 FIX: Implements proper endpoint to retrieve components from
    application_components table instead of deprecated assessment-status workaround.

    Returns components grouped by application_id.
    """
    try:
        from app.repositories.assessment_flow_repository import AssessmentFlowRepository

        client_account_id = context.client_account_id
        engagement_id = context.engagement_id

        if not client_account_id or not engagement_id:
            raise HTTPException(
                status_code=400, detail="Client account ID and Engagement ID required"
            )

        # Verify flow exists
        flow = await get_assessment_flow(db, flow_id, client_account_id, engagement_id)
        if not flow:
            raise HTTPException(status_code=404, detail="Assessment flow not found")

        # Get components via repository
        repo = AssessmentFlowRepository(db, client_account_id, engagement_id)
        components = await repo._get_application_components(flow_id)

        return sanitize_for_json(
            {
                "flow_id": flow_id,
                "applications": components,
                "total_applications": len(components),
                "total_components": sum(len(c) for c in components.values()),
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to get components for flow {flow_id}: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to get application components: {str(e)}"
        )


@router.get("/{flow_id}/tech-debt")
async def get_assessment_tech_debt(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context_dependency),
) -> Dict[str, Any]:
    """
    Get tech debt analysis for assessment flow.

    GAP-4 FIX: Implements proper endpoint to retrieve tech debt from
    tech_debt_analyses table instead of deprecated assessment-status workaround.

    Returns tech debt items and scores grouped by application_id.
    """
    try:
        from app.repositories.assessment_flow_repository import AssessmentFlowRepository

        client_account_id = context.client_account_id
        engagement_id = context.engagement_id

        if not client_account_id or not engagement_id:
            raise HTTPException(
                status_code=400, detail="Client account ID and Engagement ID required"
            )

        # Verify flow exists
        flow = await get_assessment_flow(db, flow_id, client_account_id, engagement_id)
        if not flow:
            raise HTTPException(status_code=404, detail="Assessment flow not found")

        # Get tech debt via repository
        repo = AssessmentFlowRepository(db, client_account_id, engagement_id)
        tech_debt = await repo._get_tech_debt_analysis(flow_id)

        return sanitize_for_json(
            {
                "flow_id": flow_id,
                "applications": tech_debt.get("analysis", {}),
                "scores": tech_debt.get("scores", {}),
                "total_applications": len(tech_debt.get("analysis", {})),
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to get tech debt for flow {flow_id}: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to get tech debt analysis: {str(e)}"
        )


@router.get("/{flow_id}/sixr-decisions")
async def get_assessment_sixr_decisions(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context_dependency),
) -> Dict[str, Any]:
    """
    Get 6R decisions for assessment flow via MFO.

    GAP-4 FIX: Provides MFO-routed endpoint for retrieving 6R decisions.
    Uses decision_queries which queries phase_results for AI recommendations.

    Returns decisions keyed by application_id.
    """
    try:
        from app.repositories.assessment_flow_repository import AssessmentFlowRepository

        client_account_id = context.client_account_id
        engagement_id = context.engagement_id

        if not client_account_id or not engagement_id:
            raise HTTPException(
                status_code=400, detail="Client account ID and Engagement ID required"
            )

        # Verify flow exists
        flow = await get_assessment_flow(db, flow_id, client_account_id, engagement_id)
        if not flow:
            raise HTTPException(status_code=404, detail="Assessment flow not found")

        # Get 6R decisions via repository (uses decision_queries)
        repo = AssessmentFlowRepository(db, client_account_id, engagement_id)
        decisions = await repo.get_all_sixr_decisions(flow_id)

        return sanitize_for_json(
            {
                "flow_id": flow_id,
                "decisions": decisions,
                "total_applications": len(decisions),
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to get 6R decisions for flow {flow_id}: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to get 6R decisions: {str(e)}"
        )


@router.get("/{flow_id}/component-treatments")
async def get_assessment_component_treatments(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context_dependency),
) -> Dict[str, Any]:
    """
    Get component-level treatments for assessment flow.

    GAP-4 FIX: Implements endpoint to retrieve component treatments from
    component_treatments table with application grouping.

    Returns treatments grouped by application_id.
    """
    try:
        from app.repositories.assessment_flow_repository import AssessmentFlowRepository

        client_account_id = context.client_account_id
        engagement_id = context.engagement_id

        if not client_account_id or not engagement_id:
            raise HTTPException(
                status_code=400, detail="Client account ID and Engagement ID required"
            )

        # Verify flow exists
        flow = await get_assessment_flow(db, flow_id, client_account_id, engagement_id)
        if not flow:
            raise HTTPException(status_code=404, detail="Assessment flow not found")

        # Get component treatments via repository
        repo = AssessmentFlowRepository(db, client_account_id, engagement_id)
        treatments = await repo._get_component_treatments(flow_id)

        return sanitize_for_json(
            {
                "flow_id": flow_id,
                "treatments": treatments,
                "total_applications": len(treatments),
                "total_treatments": sum(len(t) for t in treatments.values()),
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to get component treatments for flow {flow_id}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to get component treatments: {str(e)}"
        )
