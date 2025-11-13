"""
Phase-specific handlers for collection flow management.

Extracted from management.py to maintain file length under 400 lines.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import HTTPException
from sqlalchemy import select, func
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
    from app.models.collection_data_gap import CollectionDataGap

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
        else:
            try:
                # Create GapAnalysisService instance with tenant scoping
                gap_service = GapAnalysisService(
                    client_account_id=str(collection_flow.client_account_id),
                    engagement_id=str(collection_flow.engagement_id),
                    collection_flow_id=str(collection_flow.id),
                )

                # Execute gap analysis with 5-minute timeout
                automation_tier = collection_flow.automation_tier or "tier_2"

                try:
                    gap_result = await asyncio.wait_for(
                        gap_service.analyze_and_generate_questionnaire(
                            selected_asset_ids=selected_asset_ids,
                            db=db,
                            automation_tier=automation_tier,
                        ),
                        timeout=300.0,  # 5 minutes timeout for LLM agent execution
                    )

                    logger.info(
                        safe_log_format(
                            "✅ Gap analysis completed for flow {flow_id}: {summary}",
                            flow_id=flow_id,
                            summary=gap_result.get("summary", {}),
                        )
                    )
                except asyncio.TimeoutError:
                    logger.error(
                        safe_log_format(
                            "⏱️ Gap analysis timed out after 300s for flow {flow_id}",
                            flow_id=flow_id,
                        )
                    )
                    # Mark flow with timeout metadata for retry tracking
                    if not collection_flow.flow_metadata:
                        collection_flow.flow_metadata = {}
                    collection_flow.flow_metadata["gap_analysis_timeout"] = (
                        datetime.now(timezone.utc).isoformat()
                    )
                    collection_flow.flow_metadata["gap_analysis_retry_needed"] = True
                    await db.commit()

                    # Return user-friendly response allowing progression or retry
                    raise HTTPException(
                        status_code=504,
                        detail={
                            "error": "gap_analysis_timeout",
                            "message": (
                                "Gap analysis is taking longer than expected. "
                                "You can proceed to manual collection or retry later."
                            ),
                            "flow_id": str(flow_id),
                            "timeout_seconds": 300,
                            "next_actions": [
                                "Proceed to manual collection (gaps can be filled later)",
                                "Retry gap analysis from the flow management page",
                            ],
                        },
                    )
            except HTTPException:
                raise  # Re-raise HTTPException to propagate to client
            except Exception as gap_exec_error:
                logger.error(
                    safe_log_format(
                        "Gap analysis execution failed for flow {flow_id}: {error}",
                        flow_id=flow_id,
                        error=str(gap_exec_error),
                    ),
                    exc_info=True,
                )
                # Continue anyway - gaps are recommendations, not blockers

        # Now check for unresolved gaps (after execution)
        unresolved_count_stmt = (
            select(func.count())
            .select_from(CollectionDataGap)
            .where(
                CollectionDataGap.collection_flow_id == collection_flow.id,
                CollectionDataGap.resolution_status.in_(["unresolved", "pending"]),
            )
        )
        unresolved_result = await db.execute(unresolved_count_stmt)
        unresolved_gaps = unresolved_result.scalar() or 0

        # Always allow progression from gap_analysis
        # Gaps are recommendations, not blockers
        next_phase = collection_flow.get_next_phase()
        if next_phase:
            logger.info(
                safe_log_format(
                    "Progressing from gap_analysis to {next_phase} "
                    "({unresolved_gaps} unresolved gaps remain)",
                    flow_id=flow_id,
                    next_phase=next_phase,
                    unresolved_gaps=unresolved_gaps,
                )
            )
            collection_flow.current_phase = next_phase
            collection_flow.status = CollectionFlowStatus.RUNNING
            collection_flow.updated_at = datetime.now(timezone.utc)
            await db.commit()

            action_status = "phase_progressed"
            if unresolved_gaps == 0:
                action_description = (
                    f"Gap analysis complete - progressed to {next_phase}"
                )
            else:
                action_description = (
                    f"Proceeding to {next_phase} with {unresolved_gaps} "
                    f"unresolved gaps (data can be collected manually)"
                )

            logger.info(
                safe_log_format(
                    "Returning after gap_analysis progression - "
                    "phase {next_phase} will be handled on next navigation",
                    flow_id=flow_id,
                    next_phase=next_phase,
                )
            )
            return {
                "status": "success",
                "message": "Gap analysis complete - progressed to next phase",
                "flow_id": flow_id,
                "action_status": action_status,
                "action_description": action_description,
                "current_phase": next_phase,
                "flow_status": CollectionFlowStatus.RUNNING,
                "has_applications": has_applications,
                "mfo_execution_triggered": False,
                "mfo_result": {
                    "status": "phase_progressed",
                    "reason": f"Gap analysis complete - progressed from gap_analysis to {next_phase}",
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
                },
            }
        else:
            return {
                "action_status": "gap_analysis_complete",
                "action_description": f"Gap analysis reviewed ({unresolved_gaps} gaps) but no next phase defined",
            }
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
