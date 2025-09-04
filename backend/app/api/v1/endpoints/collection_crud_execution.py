"""
Collection Flow Execution Operations
Flow lifecycle operations including ensuring flow existence, execution,
and continuation/resumption of collection flows.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.rbac_utils import COLLECTION_CREATE_ROLES, require_role
from app.core.security.secure_logging import safe_log_format
from app.utils.security_utils import InputSanitizer
from app.models import User
from app.models.collection_flow import (
    AutomationTier,
    CollectionFlow,
    CollectionFlowStatus,
)
from app.schemas.collection_flow import CollectionFlowCreate, CollectionFlowResponse

# Import modular functions
from app.api.v1.endpoints import collection_utils
from app.services.master_flow_orchestrator import MasterFlowOrchestrator
from app.api.v1.endpoints import collection_validators
from app.api.v1.endpoints import collection_serializers
from app.api.v1.endpoints.collection_crud_commands import create_collection_flow

logger = logging.getLogger(__name__)


def sanitize_mfo_result(mfo_result: Any) -> Dict[str, Any]:
    """
    Sanitize MFO result to prevent sensitive data leaks.

    Only returns whitelisted fields from the MFO result to prevent
    exposure of internal system details, credentials, or other sensitive data.

    Args:
        mfo_result: Raw MFO result that may contain sensitive data

    Returns:
        Sanitized dictionary with only whitelisted fields
    """
    # Define whitelisted fields that are safe to expose
    WHITELISTED_FIELDS = {
        "status",
        "message",
        "flow_id",
        "phase",
        "progress",
        "error",  # Allow error messages but sanitize them
        "success",
        "completed",
        "timestamp",
        "next_phase",
        "summary",
    }

    if not mfo_result:
        return {"status": "no_result"}

    if isinstance(mfo_result, dict):
        sanitized = {}
        for key, value in mfo_result.items():
            if key in WHITELISTED_FIELDS:
                # Sanitize the value based on type
                if isinstance(value, str):
                    sanitized[key] = InputSanitizer.sanitize_string(
                        value, max_length=1000
                    )
                elif isinstance(value, dict):
                    # For nested dicts, only allow basic status information
                    if key == "error" and isinstance(value, dict):
                        sanitized[key] = {
                            "message": InputSanitizer.sanitize_string(
                                str(value.get("message", "")), max_length=500
                            ),
                            "type": InputSanitizer.sanitize_string(
                                str(value.get("type", "unknown")), max_length=100
                            ),
                        }
                    else:
                        # For other nested objects, convert to safe string representation
                        sanitized[key] = InputSanitizer.sanitize_string(
                            str(value), max_length=500
                        )
                elif isinstance(value, (int, float, bool)) or value is None:
                    sanitized[key] = value
                else:
                    # Convert other types to sanitized string
                    sanitized[key] = InputSanitizer.sanitize_string(
                        str(value), max_length=500
                    )
        return sanitized
    else:
        # If mfo_result is not a dict, return a safe string representation
        return {
            "status": "processed",
            "message": InputSanitizer.sanitize_string(str(mfo_result), max_length=500),
        }


async def ensure_collection_flow(
    db: AsyncSession,
    current_user: User,
    context: RequestContext,
) -> CollectionFlowResponse:
    """Return an active Collection flow for the engagement, or create one via MFO.

    This enables seamless navigation from Discovery to Collection without users
    needing to manually start a flow. It reuses any non-completed flow; if none
    exist, it creates a new one and returns it immediately.

    Args:
        db: Database session
        current_user: Current authenticated user
        context: Request context

    Returns:
        CollectionFlowResponse for existing or newly created flow
    """
    require_role(current_user, COLLECTION_CREATE_ROLES, "ensure collection flows")

    # Validate tenant context early
    collection_validators.validate_tenant_context(context)

    try:
        # Try to find an active collection flow for this engagement
        result = await db.execute(
            select(CollectionFlow)
            .where(
                CollectionFlow.client_account_id == context.client_account_id,
                CollectionFlow.engagement_id == context.engagement_id,
                CollectionFlow.status.notin_(
                    [
                        CollectionFlowStatus.COMPLETED.value,
                        CollectionFlowStatus.CANCELLED.value,
                    ]
                ),
            )
            .order_by(CollectionFlow.created_at.desc())
            .limit(1)  # Ensure we only get one row
        )
        existing = result.scalar_one_or_none()

        if existing:
            return collection_serializers.build_collection_flow_response(existing)

        # Otherwise, create a new one (delegates to existing create logic)
        flow_data = CollectionFlowCreate(automation_tier=AutomationTier.TIER_2.value)
        return await create_collection_flow(flow_data, db, current_user, context)

    except HTTPException:
        # Pass through known HTTP exceptions intact
        raise
    except Exception:
        logger.error("Error ensuring collection flow", exc_info=True)
        # Sanitize error exposure
        raise HTTPException(status_code=500, detail="Failed to ensure collection flow")


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
        current_phase = collection_flow.current_phase or "initialization"

        # Use master_flow_id if it exists, otherwise try with collection flow_id
        execute_flow_id = (
            str(collection_flow.master_flow_id)
            if collection_flow.master_flow_id
            else flow_id
        )

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
        # Use master_flow_id if available, otherwise fallback to collection flow_id
        resume_flow_id = (
            str(collection_flow.master_flow_id)
            if collection_flow.master_flow_id
            else flow_id
        )

        try:
            result = await collection_utils.resume_mfo_flow(
                db, context, resume_flow_id, resume_context or {}
            )
            mfo_triggered = True
            mfo_result = result
        except Exception as mfo_error:
            logger.warning(
                f"MFO resume failed, but flow can still continue: {str(mfo_error)}"
            )
            mfo_triggered = False
            mfo_result = {"error": str(mfo_error)}

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

        # Trigger gap analysis through MFO if available
        if collection_flow.master_flow_id:
            try:
                orchestrator = MasterFlowOrchestrator(db, context)

                # Execute gap analysis phase
                execution_result = await orchestrator.execute_phase(
                    flow_id=str(collection_flow.master_flow_id),
                    phase_name="GAP_ANALYSIS",
                    force_restart=True,  # Force re-analysis
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
