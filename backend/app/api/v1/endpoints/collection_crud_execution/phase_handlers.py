"""
Phase-specific handlers for collection flow management.

Extracted from management.py to maintain file length under 400 lines.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.secure_logging import safe_log_format
from app.models.collection_flow.schemas import CollectionFlowStatus

logger = logging.getLogger(__name__)


async def handle_gap_analysis_phase(
    collection_flow: Any,
    flow_id: str,
    has_applications: bool,
    db: AsyncSession,
) -> Dict[str, Any]:
    """Handle gap_analysis phase progression AND execute gap detection.

    CRITICAL FIX (Issue #980): This function now EXECUTES gap detection for standalone flows.
    - Assessment-initiated flows: Skip gap scan (gaps already provided)
    - Standalone collection flows: Run GapAnalysisService to detect gaps dynamically

    Args:
        collection_flow: The collection flow model instance
        flow_id: Collection flow ID for logging
        has_applications: Whether applications are selected
        db: Database session

    Returns:
        Response dictionary with phase progression status
    """

    try:
        # OPTION 3: Check if flow came from assessment flow
        # If assessment_flow_id is present and missing_attributes exist,
        # auto-advance to questionnaire (skip gap analysis page)
        assessment_flow_id = collection_flow.assessment_flow_id
        collection_config = collection_flow.collection_config or {}
        missing_attributes = collection_config.get("missing_attributes", {})

        should_skip_gap_analysis = bool(assessment_flow_id and missing_attributes)

        if should_skip_gap_analysis:
            logger.info(
                safe_log_format(
                    "Auto-advancing from gap_analysis to questionnaire for "
                    "assessment flow {assessment_flow_id} (gaps already identified)",
                    flow_id=flow_id,
                    assessment_flow_id=str(assessment_flow_id),
                )
            )

            # Auto-advance to next phase (questionnaire_generation or manual_collection)
            next_phase = collection_flow.get_next_phase()
            if next_phase:
                collection_flow.current_phase = next_phase
                collection_flow.status = CollectionFlowStatus.RUNNING
                collection_flow.updated_at = datetime.now(timezone.utc)
                await db.commit()

                return {
                    "status": "success",
                    "message": "Auto-advanced from gap_analysis to questionnaire (assessment flow)",
                    "flow_id": flow_id,
                    "action_status": "auto_advanced",
                    "action_description": (
                        f"Gap analysis skipped - progressed directly to {next_phase} "
                        "(gaps already identified from assessment flow)"
                    ),
                    "current_phase": next_phase,
                    "flow_status": CollectionFlowStatus.RUNNING,
                    "has_applications": has_applications,
                    "mfo_execution_triggered": False,
                    "mfo_result": {
                        "status": "auto_advanced",
                        "reason": "Assessment flow - gaps already identified",
                    },
                    "skipped_gap_analysis": True,
                }

        # CRITICAL FIX: For standalone collection flows, EXECUTE gap detection
        # This was the missing piece - we were checking for gaps without ever generating them!
        logger.info(
            safe_log_format(
                "Executing gap detection for standalone collection flow {flow_id}",
                flow_id=flow_id,
            )
        )

        # Execute gap analysis using GapAnalysisService
        from app.services.collection.gap_analysis import GapAnalysisService

        # Get selected asset IDs from collection_config
        selected_asset_ids = collection_config.get("selected_application_ids", [])

        if not selected_asset_ids:
            logger.warning(
                safe_log_format(
                    "No assets selected for gap analysis - flow {flow_id}",
                    flow_id=flow_id,
                )
            )
            # Still allow progression - user can select assets later
        # ✅ Check gap_analysis_results to determine if tier_2 (agentic) analysis completed
        # This is data-driven approach (recommended by GPT Codex5)
        gap_results = collection_flow.gap_analysis_results or {}
        summary = gap_results.get("summary", {})
        questionnaire = gap_results.get("questionnaire", {})

        # Tier_2 analysis complete if we have both summary data and questionnaire
        has_tier_2_results = (
            summary.get("assets_analyzed", 0) > 0
            and len(questionnaire.get("sections", [])) > 0
        )

        if has_tier_2_results:
            logger.info(
                safe_log_format(
                    "✅ Agentic gap analysis complete (gap_analysis_results populated). "
                    "Using AI-generated questionnaire - Flow: {flow_id}",
                    flow_id=flow_id,
                )
            )

            # gap_analysis_results already contains questionnaire - just advance phase
            next_phase = collection_flow.get_next_phase()
            if next_phase:
                collection_flow.current_phase = next_phase
                collection_flow.status = CollectionFlowStatus.RUNNING
                collection_flow.updated_at = datetime.now(timezone.utc)
                await db.commit()

                return {
                    "status": "success",
                    "message": "Using AI-generated questionnaire - progressed to next phase",
                    "flow_id": flow_id,
                    "action_status": "phase_progressed_with_ai_questionnaire",
                    "action_description": (
                        f"AI-enhanced gap analysis complete - progressed to {next_phase} "
                        "with intelligent questionnaire"
                    ),
                    "current_phase": next_phase,
                    "flow_status": CollectionFlowStatus.RUNNING,
                    "has_applications": has_applications,
                    "mfo_execution_triggered": False,
                    "mfo_result": {
                        "status": "phase_progressed",
                        "reason": f"Using AI-generated questionnaire - progressed to {next_phase}",
                    },
                    "questionnaire_summary": summary,
                    "next_steps": [],
                    "continued_at": datetime.now(timezone.utc).isoformat(),
                }

        else:
            logger.warning(
                safe_log_format(
                    "⚠️ User proceeding without waiting for agentic analysis. "
                    "Generating basic questionnaire from heuristic gaps - Flow: {flow_id}",
                    flow_id=flow_id,
                )
            )

            # Generate basic questionnaire from heuristic gaps only
            gap_service = GapAnalysisService(
                client_account_id=str(collection_flow.client_account_id),
                engagement_id=str(collection_flow.engagement_id),
                collection_flow_id=str(collection_flow.id),
            )

            try:
                # Run tier_1 programmatic scan to get basic questionnaire
                await gap_service.analyze_and_generate_questionnaire(
                    selected_asset_ids=selected_asset_ids,
                    db=db,
                    automation_tier="tier_1",  # Use fast heuristic scan only
                )

                logger.info(
                    safe_log_format(
                        "✅ Basic questionnaire generated from heuristic gaps - Flow: {flow_id}",
                        flow_id=flow_id,
                    )
                )

                # Advance to next phase
                next_phase = collection_flow.get_next_phase()
                if next_phase:
                    collection_flow.current_phase = next_phase
                    collection_flow.status = CollectionFlowStatus.RUNNING
                    collection_flow.updated_at = datetime.now(timezone.utc)
                    await db.commit()

                    return {
                        "status": "success",
                        "message": "Basic questionnaire generated - progressed to next phase",
                        "flow_id": flow_id,
                        "action_status": "phase_progressed_with_basic_questionnaire",
                        "action_description": (
                            f"Basic questionnaire generated from heuristic gaps - "
                            f"progressed to {next_phase}"
                        ),
                        "current_phase": next_phase,
                        "flow_status": CollectionFlowStatus.RUNNING,
                        "has_applications": has_applications,
                        "mfo_execution_triggered": False,
                        "mfo_result": {
                            "status": "phase_progressed",
                            "reason": f"Basic questionnaire generated - progressed to {next_phase}",
                        },
                        "next_steps": [],
                        "continued_at": datetime.now(timezone.utc).isoformat(),
                    }

            except Exception as questionnaire_error:
                logger.error(
                    safe_log_format(
                        "❌ Questionnaire generation failed for flow {flow_id}: {error}",
                        flow_id=flow_id,
                        error=str(questionnaire_error),
                    ),
                    exc_info=True,
                )
                # Still allow progression with warning
                raise HTTPException(
                    status_code=500,
                    detail={
                        "error": "questionnaire_generation_failed",
                        "message": (
                            "Could not generate questionnaire. "
                            "Please retry or proceed to manual collection."
                        ),
                        "flow_id": flow_id,
                    },
                )

    except Exception as gap_check_error:
        logger.warning(
            safe_log_format(
                "Failed to check gap status for flow {flow_id}: {error}",
                flow_id=flow_id,
                error=str(gap_check_error),
            )
        )
        # Fallback: still allow progression
        next_phase = collection_flow.get_next_phase()
        if next_phase:
            collection_flow.current_phase = next_phase
            collection_flow.status = CollectionFlowStatus.RUNNING
            collection_flow.updated_at = datetime.now(timezone.utc)
            await db.commit()

            logger.info(
                safe_log_format(
                    "Gap analysis fallback progression to {next_phase}",
                    flow_id=flow_id,
                    next_phase=next_phase,
                )
            )
            return {
                "status": "success",
                "message": "Gap analysis complete - progressed to next phase (fallback)",
                "flow_id": flow_id,
                "action_status": "phase_progressed_fallback",
                "action_description": f"Gap analysis complete - progressed to {next_phase}",
                "current_phase": next_phase,
                "flow_status": CollectionFlowStatus.RUNNING,
                "has_applications": has_applications,
                "mfo_execution_triggered": False,
                "mfo_result": {
                    "status": "phase_progressed",
                    "reason": f"Gap analysis fallback progression to {next_phase}",
                },
                "next_steps": [],
                "continued_at": datetime.now(timezone.utc).isoformat(),
                "master_flow_id": (
                    str(collection_flow.master_flow_id)
                    if collection_flow.master_flow_id
                    else None
                ),
                "recovery_performed": bool(
                    collection_flow.flow_metadata
                    and collection_flow.flow_metadata.get("recovery_info")
                ),
                "resume_result": {
                    "status": "phase_progressed",
                    "from_phase": "gap_analysis",
                    "to_phase": next_phase,
                    "fallback": True,
                },
            }
        # If fallback fails, return partial status for main function to handle
        return {
            "action_status": "gap_analysis",
            "action_description": "Gap analysis complete - proceeding to manual collection",
        }
