"""
Assessment Flow - 6R Recommendations Endpoint

Extracts and returns 6R migration recommendations from phase_results.

Fix for Issue #7: Frontend not displaying recommendations because they're
stored in phase_results JSONB but frontend expects structured decisions array.
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context_dependency
from app.core.database import get_db
from app.utils.json_sanitization import sanitize_for_json

logger = logging.getLogger(__name__)

router = APIRouter()


def _extract_from_recommendation_generation(
    phase_results: Dict[str, Any], flow_id: str
) -> Dict[str, Dict[str, Any]]:
    """
    Extract 6R decisions from recommendation_generation phase.

    Args:
        phase_results: Phase results dictionary
        flow_id: Flow ID for logging

    Returns:
        Dictionary mapping application_id to decision objects
    """
    decisions = {}

    if "recommendation_generation" not in phase_results:
        return decisions

    rec_gen = phase_results["recommendation_generation"]
    if not isinstance(rec_gen, dict) or "applications" not in rec_gen:
        return decisions

    applications = rec_gen["applications"]
    if not isinstance(applications, list):
        return decisions

    for app_rec in applications:
        if not isinstance(app_rec, dict) or "application_id" not in app_rec:
            continue

        app_id = app_rec["application_id"]
        decisions[app_id] = {
            "application_id": app_id,
            "overall_strategy": app_rec.get("six_r_strategy", "retain"),
            "confidence_score": app_rec.get("confidence_score", 0.0),
            "rationale": app_rec.get("rationale", ""),
            "architecture_exceptions": app_rec.get("architecture_exceptions", []),
            "component_treatments": app_rec.get("component_treatments", []),
            "move_group_hints": app_rec.get("move_group_hints", []),
        }

    if decisions:
        logger.info(
            f"Extracted {len(decisions)} decisions from recommendation_generation "
            f"for flow {flow_id}"
        )

    return decisions


def _extract_from_risk_assessment(
    phase_results: Dict[str, Any], flow_id: str
) -> Dict[str, Dict[str, Any]]:
    """
    Extract 6R decisions from risk_assessment phase (legacy format).

    Args:
        phase_results: Phase results dictionary
        flow_id: Flow ID for logging

    Returns:
        Dictionary mapping application_id to decision objects
    """
    decisions = {}

    if "risk_assessment" not in phase_results:
        return decisions

    risk_assessment = phase_results["risk_assessment"]
    if not isinstance(risk_assessment, dict) or "results" not in risk_assessment:
        return decisions

    results = risk_assessment["results"]
    if not isinstance(results, dict) or "six_r_recommendations" not in results:
        return decisions

    six_r_recs = results["six_r_recommendations"]
    if not isinstance(six_r_recs, dict):
        return decisions

    # Legacy format: {"app_name": "strategy or strategy"}
    for app_name, strategy_str in six_r_recs.items():
        strategies = strategy_str.split(" or ")
        primary_strategy = strategies[0].strip().lower()

        decisions[app_name] = {
            "application_id": app_name,
            "overall_strategy": primary_strategy,
            "confidence_score": 0.5 if len(strategies) > 1 else 0.7,
            "rationale": f"Recommended {strategy_str}",
            "architecture_exceptions": [],
            "component_treatments": [],
            "move_group_hints": [],
        }

    if decisions:
        logger.info(
            f"Extracted {len(decisions)} decisions from risk_assessment "
            f"(legacy format) for flow {flow_id}"
        )

    return decisions


@router.get("/{flow_id}/sixr-decisions")
async def get_sixr_decisions(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context_dependency),
) -> Dict[str, Any]:
    """
    Get 6R migration recommendations from assessment flow phase_results.

    Extracts recommendations from:
    - phase_results.recommendation_generation.applications (new format)
    - phase_results.risk_assessment.results.six_r_recommendations (legacy format)

    Returns:
        decisions: Dict mapping application_id to SixRDecision objects
    """
    client_account_id = context.client_account_id
    if not client_account_id:
        raise HTTPException(status_code=400, detail="Client account ID required")

    try:
        from app.repositories.assessment_flow_repository import AssessmentFlowRepository

        repository = AssessmentFlowRepository(db, client_account_id)
        flow_state = await repository.get_assessment_flow_state(flow_id)

        if not flow_state:
            raise HTTPException(status_code=404, detail="Assessment flow not found")

        if not flow_state.phase_results:
            logger.warning(f"No phase_results found for flow {flow_id}")
            return sanitize_for_json({"decisions": {}})

        # Try new format first
        decisions = _extract_from_recommendation_generation(
            flow_state.phase_results, flow_id
        )

        # Fallback to legacy format if no decisions found
        if not decisions:
            decisions = _extract_from_risk_assessment(flow_state.phase_results, flow_id)

        if not decisions:
            logger.warning(
                f"No 6R recommendations found in phase_results for flow {flow_id}. "
                f"Available phases: {list(flow_state.phase_results.keys())}"
            )

        return sanitize_for_json({"decisions": decisions})

    except Exception as e:
        logger.error(f"Failed to get 6R decisions for flow {flow_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get 6R decisions: {str(e)}"
        )
