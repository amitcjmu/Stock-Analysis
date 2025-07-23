"""
Flow Lifecycle Endpoints

This module handles flow lifecycle operations:
- Flow creation and initialization
- Flow deletion and cleanup
- Flow state transitions
"""

import logging
import time
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context
from app.core.database import get_db

from .response_mappers import (
    FlowInitializeResponse,
    FlowOperationResponse,
    ResponseMappers,
)
from .status_calculator import StatusCalculator

logger = logging.getLogger(__name__)

lifecycle_router = APIRouter(tags=["discovery-lifecycle"])


@lifecycle_router.post("/flows/initialize", response_model=FlowInitializeResponse)
async def initialize_flow(
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db),
):
    """
    Initialize a new discovery flow.

    NOTE: This is a placeholder endpoint. In proper flow architecture,
    discovery flows should be created during data import process, not on-demand.
    """
    try:
        logger.warning(
            f"⚠️ PLACEHOLDER: Discovery flow initialization requested for client {context.client_account_id}"
        )
        logger.warning(
            "⚠️ This indicates flows are not being created during data import as expected"
        )

        # Generate a flow ID for placeholder response
        import uuid

        flow_id = f"placeholder_{uuid.uuid4().hex[:8]}"

        # Return placeholder response - do not create actual database records
        return {
            "flow_id": flow_id,
            "status": "placeholder",
            "type": "discovery",
            "client_account_id": str(context.client_account_id),
            "engagement_id": str(context.engagement_id),
            "message": "PLACEHOLDER: Flows should be created during data import, not on-demand",
            "next_steps": [
                "Use proper data import workflow",
                "Fix flow creation during import process",
            ],
            "metadata": {
                "note": "This is a placeholder response - fix the data import flow creation process"
            },
        }

    except Exception as e:
        logger.error(f"Error in placeholder flow initialization: {e}")
        raise HTTPException(
            status_code=500, detail=f"Placeholder endpoint error: {str(e)}"
        )


@lifecycle_router.post("/flow/{flow_id}/pause", response_model=FlowOperationResponse)
async def pause_discovery_flow(
    flow_id: str,
    request: Dict[str, Any] = {},
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db),
):
    """
    Pause an active discovery flow.

    This endpoint pauses a running flow and updates both the discovery flow
    and master flow status to reflect the paused state.
    """
    try:
        logger.info(f"⏸️ Pausing discovery flow {flow_id}")

        # Import required models
        import uuid as uuid_lib

        from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
        from app.models.discovery_flow import DiscoveryFlow

        # Convert flow_id to UUID if needed
        try:
            flow_uuid = uuid_lib.UUID(flow_id)
        except ValueError:
            logger.warning(f"Invalid UUID format for flow_id: {flow_id}")
            flow_uuid = flow_id

        # Get the flow
        stmt = select(DiscoveryFlow).where(DiscoveryFlow.flow_id == flow_uuid)
        result = await db.execute(stmt)
        flow = result.scalar_one_or_none()

        if not flow:
            raise HTTPException(status_code=404, detail=f"Flow {flow_id} not found")

        # Check if flow can be paused
        if flow.status == "deleted":
            raise HTTPException(status_code=400, detail="Cannot pause a deleted flow")

        if flow.status == "completed":
            raise HTTPException(status_code=400, detail="Cannot pause a completed flow")

        if flow.status == "paused":
            logger.info(f"Flow {flow_id} is already paused")
            return ResponseMappers.create_success_response(
                flow_id=str(flow_id),
                message="Flow is already paused",
                data={"success": True, "status": "already_paused"},
            )

        # Store the previous status for potential resume
        previous_status = flow.status
        flow.status = "paused"
        flow.updated_at = datetime.utcnow()

        # Store pause metadata in flow_state
        if not flow.flow_state:
            flow.flow_state = {}
        flow.flow_state["pause_metadata"] = {
            "paused_at": datetime.utcnow().isoformat(),
            "paused_by": context.user_id,
            "previous_status": previous_status,
            "pause_reason": request.get("reason", "User requested pause"),
        }

        # Update master flow if exists
        if flow.master_flow_id:
            master_stmt = select(CrewAIFlowStateExtensions).where(
                CrewAIFlowStateExtensions.flow_id == flow.master_flow_id
            )
            master_result = await db.execute(master_stmt)
            master_flow = master_result.scalar_one_or_none()

            if master_flow:
                master_flow.flow_status = "paused"
                master_flow.updated_at = datetime.utcnow()

                # Add pause event to collaboration log
                master_flow.add_agent_collaboration_entry(
                    agent_name="system",
                    action="pause_flow",
                    details={
                        "child_flow_id": str(flow_id),
                        "child_flow_type": "discovery",
                        "previous_status": previous_status,
                        "paused_by": context.user_id,
                    },
                )

        await db.commit()

        logger.info(f"✅ Flow {flow_id} paused successfully")

        return {
            "success": True,
            "flow_id": str(flow_id),
            "status": "paused",
            "message": "Discovery flow paused successfully",
            "current_phase": flow.current_phase,
            "next_phase": None,
            "method": "lifecycle_pause",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pausing flow {flow_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to pause flow: {str(e)}")


@lifecycle_router.delete("/flow/{flow_id}", response_model=FlowOperationResponse)
async def delete_discovery_flow(
    flow_id: str,
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db),
):
    """
    Mark a discovery flow as deleted (soft delete).

    This endpoint performs a soft delete on the flow, maintaining audit trail
    and updating related master flow status.
    """
    try:
        logger.info(f"🗑️ Marking discovery flow {flow_id} as deleted")

        # Import required models
        import uuid as uuid_lib

        from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
        from app.models.discovery_flow import DiscoveryFlow
        from app.models.flow_deletion_audit import FlowDeletionAudit

        start_time = time.time()

        # Convert flow_id to UUID if needed
        try:
            flow_uuid = uuid_lib.UUID(flow_id)
        except ValueError:
            logger.warning(f"Invalid UUID format for flow_id: {flow_id}")
            flow_uuid = flow_id

        # Get the discovery flow
        stmt = select(DiscoveryFlow).where(
            and_(
                DiscoveryFlow.flow_id == flow_uuid,
                DiscoveryFlow.client_account_id == context.client_account_id,
                DiscoveryFlow.engagement_id == context.engagement_id,
            )
        )
        result = await db.execute(stmt)
        flow = result.scalar_one_or_none()

        if not flow:
            logger.warning(f"Discovery flow {flow_id} not found")
            return {
                "success": False,
                "flow_id": str(flow_id),
                "status": "not_found",
                "message": "Flow not found",
            }

        if flow.status == "deleted":
            logger.info(f"Discovery flow {flow_id} already marked as deleted")
            return {
                "success": True,
                "flow_id": str(flow_id),
                "status": "already_deleted",
                "message": "Flow already deleted",
            }

        # Check if flow can be deleted
        if not StatusCalculator.can_flow_be_deleted(flow):
            raise HTTPException(
                status_code=400, detail="Flow cannot be deleted in current state"
            )

        # Prepare deletion data for audit
        deletion_data = {
            "flow_type": "discovery",
            "previous_status": flow.status,
            "flow_name": flow.flow_name,
            "progress_percentage": flow.progress_percentage,
            "phases_completed": StatusCalculator.build_phase_completion_dict(flow),
        }

        # Mark discovery flow as deleted
        flow.status = "deleted"
        flow.updated_at = datetime.utcnow()

        # Update master flow if exists
        if flow.master_flow_id:
            master_stmt = select(CrewAIFlowStateExtensions).where(
                CrewAIFlowStateExtensions.flow_id == flow.master_flow_id
            )
            master_result = await db.execute(master_stmt)
            master_flow = master_result.scalar_one_or_none()

            if master_flow:
                master_flow.flow_status = "child_flows_deleted"
                master_flow.updated_at = datetime.utcnow()

                # Update persistence data
                if not master_flow.flow_persistence_data:
                    master_flow.flow_persistence_data = {}
                master_flow.flow_persistence_data["discovery_flow_deleted"] = True
                master_flow.flow_persistence_data["deletion_timestamp"] = (
                    datetime.utcnow().isoformat()
                )
                master_flow.flow_persistence_data["deleted_by"] = context.user_id

        # Create audit record
        duration_ms = int((time.time() - start_time) * 1000)
        audit_record = FlowDeletionAudit.create_audit_record(
            flow_id=str(flow_uuid),
            client_account_id=str(context.client_account_id),
            engagement_id=str(context.engagement_id),
            user_id=context.user_id,
            deletion_type="user_requested",
            deletion_method="api",
            deleted_by=context.user_id,
            deletion_reason="User requested deletion via UI",
            data_deleted=deletion_data,
            deletion_impact={"flow_type": "discovery", "soft_delete": True},
            cleanup_summary={
                "status_updated": True,
                "master_flow_updated": bool(flow.master_flow_id),
            },
            deletion_duration_ms=duration_ms,
        )
        db.add(audit_record)

        # Commit all changes
        await db.commit()

        logger.info(f"✅ Discovery flow {flow_id} marked as deleted successfully")

        return {
            "success": True,
            "flow_id": str(flow_id),
            "status": "deleted",
            "message": "Discovery flow marked as deleted",
            "current_phase": None,
            "next_phase": None,
            "method": "lifecycle_delete",
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error marking discovery flow {flow_id} as deleted: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete flow: {str(e)}")


@lifecycle_router.post("/flow/{flow_id}/clone", response_model=FlowInitializeResponse)
async def clone_discovery_flow(
    flow_id: str,
    request: Dict[str, Any] = {},
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db),
):
    """
    Clone an existing discovery flow.

    This endpoint creates a new flow based on an existing flow's configuration
    and data, useful for reprocessing or creating similar flows.
    """
    try:
        logger.info(f"🔄 Cloning discovery flow {flow_id}")

        # Import required models
        import uuid as uuid_lib

        from app.models.discovery_flow import DiscoveryFlow

        # Convert flow_id to UUID if needed
        try:
            flow_uuid = uuid_lib.UUID(flow_id)
        except ValueError:
            flow_uuid = flow_id

        # Get the source flow
        stmt = select(DiscoveryFlow).where(
            and_(
                DiscoveryFlow.flow_id == flow_uuid,
                DiscoveryFlow.client_account_id == context.client_account_id,
                DiscoveryFlow.engagement_id == context.engagement_id,
            )
        )
        result = await db.execute(stmt)
        source_flow = result.scalar_one_or_none()

        if not source_flow:
            raise HTTPException(
                status_code=404, detail=f"Source flow {flow_id} not found"
            )

        # Generate new flow ID
        import uuid

        new_flow_id = f"flow_{uuid.uuid4().hex[:8]}"

        # Get clone name from request or generate one
        clone_name = request.get(
            "flow_name", f"Clone of {source_flow.flow_name or flow_id}"
        )

        # TODO: Implement actual flow cloning with CrewAI integration
        # For now, return initialization response
        return {
            "flow_id": new_flow_id,
            "status": "initialized",
            "type": "discovery",
            "client_account_id": str(context.client_account_id),
            "engagement_id": str(context.engagement_id),
            "message": f"Discovery flow cloned from {flow_id}",
            "next_steps": [
                "Review cloned configuration",
                "Modify settings if needed",
                "Start cloned flow",
            ],
            "metadata": {
                "cloned_from": str(flow_id),
                "clone_name": clone_name,
                "note": "Flow cloning implementation pending",
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cloning flow {flow_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clone flow: {str(e)}")


@lifecycle_router.post("/flow/{flow_id}/archive", response_model=FlowOperationResponse)
async def archive_discovery_flow(
    flow_id: str,
    request: Dict[str, Any] = {},
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db),
):
    """
    Archive a discovery flow.

    This endpoint archives a completed or inactive flow, preserving data
    but removing it from active listings.
    """
    try:
        logger.info(f"📦 Archiving discovery flow {flow_id}")

        # Import required models
        import uuid as uuid_lib

        from app.models.discovery_flow import DiscoveryFlow

        # Convert flow_id to UUID if needed
        try:
            flow_uuid = uuid_lib.UUID(flow_id)
        except ValueError:
            flow_uuid = flow_id

        # Get the flow
        stmt = select(DiscoveryFlow).where(
            and_(
                DiscoveryFlow.flow_id == flow_uuid,
                DiscoveryFlow.client_account_id == context.client_account_id,
                DiscoveryFlow.engagement_id == context.engagement_id,
            )
        )
        result = await db.execute(stmt)
        flow = result.scalar_one_or_none()

        if not flow:
            raise HTTPException(status_code=404, detail=f"Flow {flow_id} not found")

        if flow.status == "deleted":
            raise HTTPException(status_code=400, detail="Cannot archive a deleted flow")

        if flow.status == "archived":
            logger.info(f"Flow {flow_id} is already archived")
            return {
                "success": True,
                "flow_id": str(flow_id),
                "status": "already_archived",
                "message": "Flow is already archived",
            }

        # Check if flow can be archived (typically completed or inactive flows)
        if flow.status in ["running", "processing", "active"]:
            raise HTTPException(
                status_code=400,
                detail="Cannot archive an active flow. Please pause or complete it first.",
            )

        # Archive the flow
        previous_status = flow.status
        flow.status = "archived"
        flow.updated_at = datetime.utcnow()

        # Store archive metadata
        if not flow.flow_state:
            flow.flow_state = {}
        flow.flow_state["archive_metadata"] = {
            "archived_at": datetime.utcnow().isoformat(),
            "archived_by": context.user_id,
            "previous_status": previous_status,
            "archive_reason": request.get("reason", "User requested archive"),
        }

        await db.commit()

        logger.info(f"✅ Flow {flow_id} archived successfully")

        return {
            "success": True,
            "flow_id": str(flow_id),
            "status": "archived",
            "message": "Discovery flow archived successfully",
            "current_phase": flow.current_phase,
            "next_phase": None,
            "method": "lifecycle_archive",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error archiving flow {flow_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to archive flow: {str(e)}")


@lifecycle_router.post("/flow/{flow_id}/restore", response_model=FlowOperationResponse)
async def restore_discovery_flow(
    flow_id: str,
    request: Dict[str, Any] = {},
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db),
):
    """
    Restore an archived discovery flow.

    This endpoint restores an archived flow back to active status.
    """
    try:
        logger.info(f"🔄 Restoring discovery flow {flow_id}")

        # Import required models
        import uuid as uuid_lib

        from app.models.discovery_flow import DiscoveryFlow

        # Convert flow_id to UUID if needed
        try:
            flow_uuid = uuid_lib.UUID(flow_id)
        except ValueError:
            flow_uuid = flow_id

        # Get the flow
        stmt = select(DiscoveryFlow).where(
            and_(
                DiscoveryFlow.flow_id == flow_uuid,
                DiscoveryFlow.client_account_id == context.client_account_id,
                DiscoveryFlow.engagement_id == context.engagement_id,
            )
        )
        result = await db.execute(stmt)
        flow = result.scalar_one_or_none()

        if not flow:
            raise HTTPException(status_code=404, detail=f"Flow {flow_id} not found")

        if flow.status != "archived":
            raise HTTPException(
                status_code=400, detail="Only archived flows can be restored"
            )

        # Restore the flow to previous status or paused
        previous_status = "paused"  # Default to paused for safety
        if flow.flow_state and "archive_metadata" in flow.flow_state:
            archive_metadata = flow.flow_state["archive_metadata"]
            previous_status = archive_metadata.get("previous_status", "paused")

        flow.status = previous_status
        flow.updated_at = datetime.utcnow()

        # Store restore metadata
        if not flow.flow_state:
            flow.flow_state = {}
        flow.flow_state["restore_metadata"] = {
            "restored_at": datetime.utcnow().isoformat(),
            "restored_by": context.user_id,
            "restored_to_status": previous_status,
            "restore_reason": request.get("reason", "User requested restore"),
        }

        await db.commit()

        logger.info(
            f"✅ Flow {flow_id} restored successfully to status: {previous_status}"
        )

        return {
            "success": True,
            "flow_id": str(flow_id),
            "status": previous_status,
            "message": f"Discovery flow restored to {previous_status} status",
            "current_phase": flow.current_phase,
            "next_phase": StatusCalculator.get_next_phase(
                flow.current_phase or "unknown"
            ),
            "method": "lifecycle_restore",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restoring flow {flow_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to restore flow: {str(e)}")
