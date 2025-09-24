"""
Collection Flow Execution - Command Operations
Write operations including execution, continuation, and gap analysis re-runs.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.rbac_utils import COLLECTION_CREATE_ROLES, require_role
from app.core.security.secure_logging import safe_log_format
from app.models import User
from app.models.collection_flow import CollectionFlow
from app.services.master_flow_orchestrator import MasterFlowOrchestrator
from app.services.master_flow_sync_service import MasterFlowSyncService

# Import modular functions
from app.api.v1.endpoints import collection_utils
from app.api.v1.endpoints import collection_validators
from app.api.v1.endpoints import collection_serializers
from .base import sanitize_mfo_result

# Import for orphaned flow handling
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions

logger = logging.getLogger(__name__)


async def create_master_flow_for_orphan(
    collection_flow: CollectionFlow,
    db: AsyncSession,
    context: RequestContext,
) -> CrewAIFlowStateExtensions:
    """Create a new master flow for an orphaned collection flow.

    This handles cases where a collection flow exists without a master_flow_id,
    likely due to incomplete flow creation or data corruption.

    Args:
        collection_flow: The orphaned collection flow
        db: Database session
        context: Request context

    Returns:
        The newly created master flow

    Raises:
        HTTPException: If master flow creation fails
    """
    try:
        from datetime import datetime, timezone
        from uuid import uuid4

        # Generate new master flow ID
        master_flow_id = uuid4()

        logger.info(
            safe_log_format(
                "Creating master flow {master_flow_id} for orphaned collection flow {collection_flow_id}",
                master_flow_id=str(master_flow_id),
                collection_flow_id=str(collection_flow.flow_id),
            )
        )

        # Create master flow with collection flow's metadata
        master_flow = CrewAIFlowStateExtensions(
            flow_id=master_flow_id,
            flow_type="collection",
            flow_name=f"Recovered Collection Flow - {collection_flow.flow_name}",
            flow_status="running",  # Resume as running
            flow_configuration={
                "current_phase": collection_flow.current_phase or "initialization",
                "progress_percentage": collection_flow.progress_percentage or 0.0,
                "recovery_mode": True,
                "original_collection_flow_id": str(collection_flow.flow_id),
                "recovery_timestamp": datetime.now(timezone.utc).isoformat(),
                "automation_tier": (
                    collection_flow.automation_tier.value
                    if collection_flow.automation_tier
                    else "tier_1"
                ),
                **collection_flow.collection_config,
            },
            flow_persistence_data={
                "recovery_metadata": {
                    "recovered_at": datetime.now(timezone.utc).isoformat(),
                    "recovery_reason": "orphaned_collection_flow",
                    "original_flow_data": {
                        "flow_id": str(collection_flow.flow_id),
                        "status": (
                            collection_flow.status.value
                            if collection_flow.status
                            else "unknown"
                        ),
                        "current_phase": collection_flow.current_phase,
                        "progress_percentage": collection_flow.progress_percentage,
                    },
                },
                "collection_state": {
                    "phase_state": collection_flow.phase_state,
                    "user_inputs": collection_flow.user_inputs,
                    "phase_results": collection_flow.phase_results,
                    "collection_results": collection_flow.collection_results,
                    "gap_analysis_results": collection_flow.gap_analysis_results,
                },
            },
            client_account_id=collection_flow.client_account_id,
            engagement_id=collection_flow.engagement_id,
            user_id=str(collection_flow.user_id or context.user_id),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        # Add to session and flush to get the ID
        db.add(master_flow)
        await db.flush()

        # Update collection flow with the new master_flow_id
        collection_flow.master_flow_id = master_flow.flow_id
        collection_flow.updated_at = datetime.now(timezone.utc)

        # Add recovery note to collection flow metadata
        if not collection_flow.flow_metadata:
            collection_flow.flow_metadata = {}
        collection_flow.flow_metadata["recovery_info"] = {
            "recovered_at": datetime.now(timezone.utc).isoformat(),
            "master_flow_created": str(master_flow.flow_id),
            "recovery_reason": "orphaned_flow_repair",
        }

        # Commit the transaction
        await db.commit()

        logger.info(
            safe_log_format(
                "Successfully created master flow {master_flow_id} and linked to collection flow {collection_flow_id}",
                master_flow_id=str(master_flow.flow_id),
                collection_flow_id=str(collection_flow.flow_id),
            )
        )

        return master_flow

    except Exception as e:
        logger.error(
            safe_log_format(
                "Failed to create master flow for orphaned collection flow {collection_flow_id}: {error}",
                collection_flow_id=str(collection_flow.flow_id),
                error=str(e),
            )
        )
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create master flow for orphaned collection flow: {str(e)}",
        )


async def execute_collection_flow(
    flow_id: str,
    db: AsyncSession,
    current_user: User,
    context: RequestContext,
) -> Dict[str, Any]:
    """Execute a collection flow phase through Master Flow Orchestrator.

    This function triggers actual CrewAI execution of the collection flow,
    enabling phase progression and questionnaire generation.

    Args:
        flow_id: Collection flow ID
        db: Database session
        current_user: Current authenticated user
        context: Request context

    Returns:
        Execution result dictionary
    """
    try:
        # Get the collection flow
        collection_flow = await collection_validators.validate_collection_flow_exists(
            db, flow_id, context.engagement_id
        )

        # Check if flow can be executed
        await collection_validators.validate_flow_can_be_executed(collection_flow)

        # Execute the current phase using the master flow ID if available
        # If no current_phase is set or if it's the status value "initialized", use "initialization"
        current_phase = collection_flow.current_phase
        if not current_phase or current_phase == "initialized":
            current_phase = "initialization"

        # CRITICAL FIX: Handle orphaned flows without master_flow_id
        if not collection_flow.master_flow_id:
            logger.warning(
                safe_log_format(
                    "Collection flow {flow_id} has no master_flow_id - attempting to create one for execution",
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
                        "Successfully created master flow {master_flow_id} for orphaned "
                        "collection flow {flow_id} during execution",
                        master_flow_id=str(master_flow.flow_id),
                        flow_id=flow_id,
                    )
                )

                # Update local reference
                collection_flow.master_flow_id = master_flow.flow_id

            except Exception as repair_error:
                logger.error(
                    safe_log_format(
                        "Failed to repair orphaned collection flow {flow_id} during execution: {error}",
                        flow_id=flow_id,
                        error=str(repair_error),
                    )
                )
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "orphaned_flow_repair_failed",
                        "message": "Collection flow has no master flow and repair failed during execution",
                        "flow_id": flow_id,
                        "repair_error": str(repair_error),
                        "required_action": "contact_support",
                    },
                )

        execute_flow_id = str(collection_flow.master_flow_id)

        logger.info(
            safe_log_format(
                "Executing phase {phase} for collection flow {flow_id} "
                "using MFO flow {mfo_id}",
                phase=current_phase,
                flow_id=flow_id,
                mfo_id=execute_flow_id,
            )
        )

        # Execute through MasterFlowOrchestrator directly
        orchestrator = MasterFlowOrchestrator(db, context)
        execution_result = await orchestrator.execute_phase(
            flow_id=execute_flow_id, phase_name=current_phase, phase_input={}
        )

        # Sync master flow changes back to collection flow after execution
        try:
            sync_service = MasterFlowSyncService(db, context)
            await sync_service.sync_master_to_collection_flow(
                master_flow_id=execute_flow_id, collection_flow_id=flow_id
            )
        except Exception as sync_error:
            logger.warning(
                safe_log_format(
                    "Failed to sync master flow to collection flow: {error}",
                    error=str(sync_error),
                )
            )

        logger.info(
            f"Executed collection flow {flow_id} for engagement {context.engagement_id}"
        )

        return collection_serializers.build_execution_response(
            flow_id, execution_result
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "Error executing collection flow {flow_id}: {e}", flow_id=flow_id, e=e
            )
        )
        raise HTTPException(status_code=500, detail=str(e))


async def continue_flow(
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
        has_applications = (
            collection_flow.collection_config
            and collection_flow.collection_config.get("has_applications", False)
        )

        # Determine what action is happening
        action_status = "resuming"
        action_description = "Flow is being resumed"
        next_steps = []

        if not has_applications:
            action_status = "needs_applications"
            action_description = "Flow needs application selection before continuing"
            next_steps.append(
                {
                    "action": "select_applications",
                    "endpoint": f"/api/v1/collection/flows/{flow_id}/applications",
                    "description": "Select applications for data collection",
                }
            )
        elif current_phase == "gap_analysis":
            action_status = "gap_analysis"
            action_description = "Gap analysis is running or will be triggered"
            next_steps.append(
                {
                    "action": "poll_questionnaires",
                    "endpoint": f"/api/v1/collection/flows/{flow_id}/questionnaires",
                    "description": "Check for generated questionnaires",
                }
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
            mfo_triggered = True
            mfo_result = result

            logger.info(
                safe_log_format(
                    "MFO resume successful for flow {flow_id}",
                    flow_id=flow_id,
                )
            )

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
                status_code=400,
                detail={
                    "error": "resume_failed",
                    "message": "Failed to resume collection flow through Master Flow Orchestrator",
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


async def rerun_gap_analysis(
    flow_id: str,
    db: AsyncSession,
    current_user: User,
    context: RequestContext,
) -> Dict[str, Any]:
    """Re-run gap analysis for a collection flow.

    This function re-computes gap summary and regenerates questionnaires
    based on current application selection and collection progress.

    Args:
        flow_id: Collection flow ID
        db: Database session
        current_user: Current authenticated user
        context: Request context

    Returns:
        202 Accepted with estimated completion time and polling information

    Raises:
        HTTPException: If flow not found or re-analysis fails
    """
    try:
        from uuid import UUID
        from datetime import datetime, timezone, timedelta

        # Validate flow exists and belongs to user's engagement
        flow_result = await db.execute(
            select(CollectionFlow).where(
                CollectionFlow.flow_id == UUID(flow_id),
                CollectionFlow.engagement_id == context.engagement_id,
                CollectionFlow.client_account_id == context.client_account_id,
            )
        )
        collection_flow = flow_result.scalar_one_or_none()

        if not collection_flow:
            raise HTTPException(status_code=404, detail="Collection flow not found")

        # Check if applications are selected
        if (
            not collection_flow.collection_config
            or not collection_flow.collection_config.get("has_applications")
        ):
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "no_applications_selected",
                    "message": "Applications must be selected before running gap analysis",
                    "flow_id": flow_id,
                    "required_action": "select_applications",
                },
            )

        # Check permissions
        require_role(current_user, COLLECTION_CREATE_ROLES, "rerun gap analysis")

        # Estimate completion time based on application count
        selected_apps = collection_flow.collection_config.get(
            "selected_application_ids", []
        )
        app_count = len(selected_apps)

        # Estimate: ~10-15 seconds base + 5-10 seconds per app
        base_time_seconds = 15
        per_app_seconds = 8
        estimated_seconds = base_time_seconds + (app_count * per_app_seconds)
        estimated_seconds = max(10, min(estimated_seconds, 300))  # Cap between 10s-5min

        completion_time = datetime.now(timezone.utc) + timedelta(
            seconds=estimated_seconds
        )

        # Trigger gap analysis through MFO - create master flow if missing
        if not collection_flow.master_flow_id:
            logger.warning(
                safe_log_format(
                    "Collection flow {flow_id} has no master_flow_id - attempting to create one for gap analysis",
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
                        "Successfully created master flow {master_flow_id} for orphaned "
                        "collection flow {flow_id} during gap analysis",
                        master_flow_id=str(master_flow.flow_id),
                        flow_id=flow_id,
                    )
                )

                # Update local reference
                collection_flow.master_flow_id = master_flow.flow_id

            except Exception as repair_error:
                logger.error(
                    safe_log_format(
                        "Failed to repair orphaned collection flow {flow_id} during gap analysis: {error}",
                        flow_id=flow_id,
                        error=str(repair_error),
                    )
                )
                return {
                    "status": "error",
                    "message": "Gap analysis failed - collection flow has no master flow and repair failed",
                    "flow_id": flow_id,
                    "error_code": "orphaned_flow_repair_failed",
                    "repair_error": str(repair_error),
                    "required_action": "contact_support",
                }

        # Now we should have a valid master_flow_id
        if collection_flow.master_flow_id:
            try:
                orchestrator = MasterFlowOrchestrator(db, context)

                # Execute gap analysis phase
                execution_result = await orchestrator.execute_phase(
                    flow_id=str(collection_flow.master_flow_id),
                    phase_name="GAP_ANALYSIS",
                    force_restart=True,  # Force re-analysis
                )

                # Sync master flow changes back to collection flow after gap analysis
                try:
                    sync_service = MasterFlowSyncService(db, context)
                    await sync_service.sync_master_to_collection_flow(
                        master_flow_id=str(collection_flow.master_flow_id),
                        collection_flow_id=flow_id,
                    )
                except Exception as sync_error:
                    logger.warning(
                        f"Failed to sync master flow after gap analysis: {sync_error}"
                    )

                logger.info(
                    f"Successfully triggered gap analysis re-run for collection flow {flow_id}"
                )

                return {
                    "status": "accepted",
                    "message": "Gap analysis re-run started successfully",
                    "flow_id": flow_id,
                    "estimated_completion_time": completion_time.isoformat(),
                    "estimated_duration_seconds": estimated_seconds,
                    "application_count": app_count,
                    "polling_interval_seconds": 5,
                    "max_wait_time_seconds": 300,
                    "status_check_endpoint": f"/api/v1/collection/flows/{flow_id}",
                    "questionnaires_endpoint": f"/api/v1/collection/flows/{flow_id}/questionnaires",
                    "execution_result": execution_result,
                    "started_at": datetime.now(timezone.utc).isoformat(),
                }

            except Exception as mfo_error:
                logger.error(f"MFO gap analysis execution failed: {str(mfo_error)}")
                # Return 202 but indicate MFO trigger failed
                return {
                    "status": "accepted",
                    "message": "Gap analysis re-run request accepted but execution trigger failed",
                    "flow_id": flow_id,
                    "estimated_completion_time": completion_time.isoformat(),
                    "estimated_duration_seconds": estimated_seconds,
                    "application_count": app_count,
                    "polling_interval_seconds": 10,
                    "max_wait_time_seconds": 300,
                    "status_check_endpoint": f"/api/v1/collection/flows/{flow_id}",
                    "questionnaires_endpoint": f"/api/v1/collection/flows/{flow_id}/questionnaires",
                    "mfo_execution_triggered": False,
                    "mfo_error": str(mfo_error),
                    "started_at": datetime.now(timezone.utc).isoformat(),
                }
        else:
            logger.warning(
                f"Collection flow {flow_id} has no master_flow_id - cannot trigger MFO"
            )
            return {
                "status": "accepted",
                "message": "Gap analysis re-run requested but no execution engine available",
                "flow_id": flow_id,
                "estimated_completion_time": completion_time.isoformat(),
                "estimated_duration_seconds": estimated_seconds,
                "application_count": app_count,
                "polling_interval_seconds": 10,
                "max_wait_time_seconds": 300,
                "status_check_endpoint": f"/api/v1/collection/flows/{flow_id}",
                "questionnaires_endpoint": f"/api/v1/collection/flows/{flow_id}/questionnaires",
                "mfo_execution_triggered": False,
                "warning": "no_master_flow_id",
                "started_at": datetime.now(timezone.utc).isoformat(),
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "Error rerunning gap analysis: flow_id={flow_id}, error={error}",
                flow_id=flow_id,
                error=str(e),
            )
        )
        raise HTTPException(status_code=500, detail="Gap analysis re-run failed")
