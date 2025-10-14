"""
Collection Flow Management Operations
Operations for continuing, resuming, and managing collection flows.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.security.secure_logging import safe_log_format
from app.models import User
from app.models.collection_flow.schemas import CollectionFlowStatus

# Import modular functions
from app.api.v1.endpoints import collection_validators
from app.api.v1.endpoints import collection_utils
from .base import sanitize_mfo_result
from .creation import create_master_flow_for_orphan

logger = logging.getLogger(__name__)


async def continue_flow(  # noqa: C901  # Complex but necessary for proper error handling
    flow_id: str,
    resume_context: Optional[Dict[str, Any]],
    db: AsyncSession,
    current_user: User,
    context: RequestContext,
) -> Dict[str, Any]:
    """Continue/resume a paused or incomplete collection flow.

    Enhanced to provide detailed status about flow state and what's happening.
    Returns status indicating questionnaires ready, processing, etc.

    Args:
        flow_id: Collection flow ID
        resume_context: Optional context for resuming
        db: Database session
        current_user: Current authenticated user
        context: Request context

    Returns:
        Continue flow response dictionary with detailed status
    """
    try:
        from datetime import datetime, timezone

        # Verify flow exists and belongs to engagement
        collection_flow = await collection_validators.validate_collection_flow_exists(
            db, flow_id, context.engagement_id
        )

        # Check if flow can be resumed
        await collection_validators.validate_flow_can_be_resumed(collection_flow)

        # CRITICAL FIX: Handle orphaned flows without master_flow_id
        if not collection_flow.master_flow_id:
            logger.warning(
                safe_log_format(
                    "Collection flow {flow_id} has no master_flow_id - attempting to create one",
                    flow_id=flow_id,
                )
            )

            try:
                # Create a new master flow for this orphaned collection flow
                master_flow = await create_master_flow_for_orphan(
                    collection_flow, db, context
                )

                logger.info(
                    safe_log_format(
                        "Successfully created master flow {master_flow_id} for orphaned collection flow {flow_id}",
                        master_flow_id=str(master_flow.flow_id),
                        flow_id=flow_id,
                    )
                )

                # Update local reference
                collection_flow.master_flow_id = master_flow.flow_id

            except Exception as repair_error:
                logger.error(
                    safe_log_format(
                        "Failed to repair orphaned collection flow {flow_id}: {error}",
                        flow_id=flow_id,
                        error=str(repair_error),
                    )
                )
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "orphaned_flow_repair_failed",
                        "message": "Collection flow has no master flow and repair failed",
                        "flow_id": flow_id,
                        "repair_error": str(repair_error),
                        "required_action": "contact_support",
                    },
                )

        # Check current flow state to provide more detailed status
        current_phase = collection_flow.current_phase
        flow_status = collection_flow.status

        # Check if applications/assets have been selected
        selected_app_ids = []
        if collection_flow.collection_config:
            selected_app_ids = collection_flow.collection_config.get(
                "selected_application_ids", []
            )

        has_applications = len(selected_app_ids) > 0

        # Determine what action is happening
        action_status = "resuming"
        action_description = "Flow is being resumed"
        next_steps = []

        # If no applications selected and we're past asset_selection phase, redirect back
        if not has_applications:
            # Update phase to asset_selection if we're in a later phase without assets
            if current_phase not in ["initialization", "asset_selection"]:
                logger.info(
                    safe_log_format(
                        "Collection flow {flow_id} in phase {phase} but has no assets "
                        "selected - redirecting to asset_selection",
                        flow_id=flow_id,
                        phase=current_phase,
                    )
                )
                collection_flow.current_phase = "asset_selection"
                # Per ADR-012: Set status to PAUSED (waiting for user input)
                collection_flow.status = CollectionFlowStatus.PAUSED
                collection_flow.updated_at = datetime.now(timezone.utc)
                await db.commit()
                current_phase = "asset_selection"

            action_status = "needs_applications"
            action_description = (
                "Flow needs application/asset selection before continuing"
            )
            next_steps.append(
                {
                    "action": "select_applications",
                    "endpoint": f"/api/v1/collection/flows/{flow_id}/applications",
                    "description": "Select applications for data collection",
                }
            )
        elif current_phase == "gap_analysis":
            # CRITICAL FIX: Gap analysis should NOT block progression
            # Gaps are informational - user can proceed to manual collection
            # But we log gap count for transparency
            from sqlalchemy import select, func
            from app.models.collection_flow.collection_flow_gaps import (
                CollectionFlowGap,
            )

            try:
                # Check for unresolved gaps using direct query
                unresolved_count_stmt = (
                    select(func.count())
                    .select_from(CollectionFlowGap)
                    .where(
                        CollectionFlowGap.collection_flow_id == collection_flow.id,
                        CollectionFlowGap.resolution_status.in_(
                            ["unresolved", "pending"]
                        ),
                    )
                )
                unresolved_result = await db.execute(unresolved_count_stmt)
                unresolved_gaps = unresolved_result.scalar() or 0

                # Always allow progression from gap_analysis
                # Gaps are recommendations, not blockers
                # Assessment transition will validate minimum data collection
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
                    current_phase = next_phase
                else:
                    action_status = "gap_analysis_complete"
                    action_description = f"Gap analysis reviewed ({unresolved_gaps} gaps) but no next phase defined"
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
                    current_phase = next_phase
                action_status = "gap_analysis"
                action_description = (
                    "Gap analysis complete - proceeding to manual collection"
                )
        elif current_phase == "manual_collection":
            action_status = "questionnaires_ready"
            action_description = "Manual collection phase - questionnaires may be ready"
            next_steps.append(
                {
                    "action": "fetch_questionnaires",
                    "endpoint": f"/api/v1/collection/flows/{flow_id}/questionnaires",
                    "description": "Fetch available questionnaires",
                }
            )

        # Resume flow through MFO
        # At this point we should have a valid master_flow_id (either existing or newly created)
        if not collection_flow.master_flow_id:
            # This should not happen after the repair logic above, but add defensive check
            logger.error(
                safe_log_format(
                    "Collection flow {flow_id} still has no master_flow_id after repair attempt",
                    flow_id=flow_id,
                )
            )
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "missing_master_flow_id",
                    "message": "Collection flow has no master flow ID and repair failed",
                    "flow_id": flow_id,
                    "required_action": "contact_support",
                },
            )

        resume_flow_id = str(collection_flow.master_flow_id)

        logger.info(
            safe_log_format(
                "Resuming collection flow {flow_id} using master flow {master_flow_id}",
                flow_id=flow_id,
                master_flow_id=resume_flow_id,
            )
        )

        try:
            result = await collection_utils.resume_mfo_flow(
                db, context, resume_flow_id, resume_context or {}
            )

            # CRITICAL FIX: MFO returns {"status": "resume_failed"} instead of raising exceptions
            # Check the result status and raise an error if resume failed
            if isinstance(result, dict) and result.get("status") == "resume_failed":
                error_msg = result.get("error", "Unknown error")
                logger.error(
                    safe_log_format(
                        "MFO resume failed for flow {flow_id}: {error}",
                        flow_id=flow_id,
                        error=error_msg,
                    )
                )
                raise HTTPException(
                    status_code=500,
                    detail={
                        "error": "resume_failed",
                        "message": (
                            "Failed to resume collection flow "
                            "through Master Flow Orchestrator"
                        ),
                        "flow_id": flow_id,
                        "master_flow_id": resume_flow_id,
                        "mfo_error": error_msg,
                        "required_action": (
                            "The flow may be in an inconsistent state. "
                            "Try navigating directly to the flow's current "
                            "phase page, or contact support if the issue persists."
                        ),
                    },
                )

            mfo_triggered = True
            mfo_result = result

            logger.info(
                safe_log_format(
                    "MFO resume successful for flow {flow_id}",
                    flow_id=flow_id,
                )
            )

            # CRITICAL FIX: Update collection flow status to RUNNING after successful MFO resume
            # This prevents the flow from remaining in "incomplete" status and causing polling loops
            collection_flow.status = CollectionFlowStatus.RUNNING
            collection_flow.updated_at = datetime.now(timezone.utc)
            await db.commit()

            logger.info(
                safe_log_format(
                    "Collection flow {flow_id} status updated to RUNNING after MFO resume",
                    flow_id=flow_id,
                )
            )

        except HTTPException:
            # Re-raise HTTPExceptions (including our custom resume_failed error)
            raise
        except Exception as mfo_error:
            logger.error(
                safe_log_format(
                    "MFO resume failed for flow {flow_id}: {error}",
                    flow_id=flow_id,
                    error=str(mfo_error),
                )
            )

            # Return proper error status instead of 200
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "resume_exception",
                    "message": "Unexpected error while resuming collection flow",
                    "flow_id": flow_id,
                    "master_flow_id": resume_flow_id,
                    "mfo_error": str(mfo_error),
                    "required_action": "retry_or_contact_support",
                },
            )

        logger.info(
            f"Resumed collection flow {flow_id} for engagement {context.engagement_id}"
        )

        return {
            "status": "success",
            "message": "Collection flow continuation initiated",
            "flow_id": flow_id,
            "action_status": action_status,
            "action_description": action_description,
            "current_phase": current_phase,
            "flow_status": flow_status,
            "has_applications": has_applications,
            "mfo_execution_triggered": mfo_triggered,
            "mfo_result": sanitize_mfo_result(mfo_result),
            "next_steps": next_steps,
            "continued_at": datetime.now(timezone.utc).isoformat(),
            "master_flow_id": str(collection_flow.master_flow_id),
            "recovery_performed": bool(
                collection_flow.flow_metadata
                and collection_flow.flow_metadata.get("recovery_info")
            ),
            # Legacy compatibility - also sanitize for backward compatibility
            "resume_result": sanitize_mfo_result(mfo_result),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "Error continuing collection flow {flow_id}: {e}", flow_id=flow_id, e=e
            )
        )
        raise HTTPException(status_code=500, detail=str(e))
