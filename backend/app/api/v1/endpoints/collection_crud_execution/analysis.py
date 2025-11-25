"""
Collection Flow Analysis Operations
Operations for running and re-running gap analysis.
"""

import logging
from typing import Any, Dict

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
from .creation import create_master_flow_for_orphan

logger = logging.getLogger(__name__)


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
        # MFO Two-Table Pattern: Query by EITHER flow_id OR id (flexible lookup)
        flow_uuid = UUID(flow_id)
        flow_result = await db.execute(
            select(CollectionFlow).where(
                (CollectionFlow.flow_id == flow_uuid)
                | (CollectionFlow.id == flow_uuid),
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
