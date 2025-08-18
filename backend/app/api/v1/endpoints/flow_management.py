"""
Flow Management API Endpoints

This module contains all flow lifecycle management endpoints,
extracted from unified_discovery.py for better modularity.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from app.core.security.secure_logging import safe_log_format
from app.models.discovery_flow import DiscoveryFlow
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.services.master_flow_orchestrator import MasterFlowOrchestrator
from app.utils.flow_constants.flow_states import FlowStatus
from app.repositories.discovery_flow_repository import DiscoveryFlowRepository

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/{flow_id}")
async def get_flow_status(
    flow_id: str,
    include_details: bool = Query(
        True, description="Include detailed flow information"
    ),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Get comprehensive flow status and metadata.

    This endpoint provides detailed information about a discovery flow,
    including current status, phases, progress, and metadata.
    """
    try:
        logger.info(safe_log_format("Getting flow status: {flow_id}", flow_id=flow_id))

        # Get flow repository with proper context
        flow_repo = DiscoveryFlowRepository(
            db, context.client_account_id, context.engagement_id
        )

        # Verify flow exists and user has access
        try:
            flow = await flow_repo.get_by_flow_id(flow_id)
            if not flow:
                raise HTTPException(
                    status_code=404,
                    detail=f"Flow {flow_id} not found",
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Failed to retrieve flow {flow_id}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to access flow: {str(e)}",
            )

        # Build comprehensive flow status response
        flow_status = {
            "flow_id": flow.flow_id,
            "status": flow.status,
            "current_phase": flow.current_phase,
            "next_phase": flow.next_phase,
            "progress_percentage": flow.progress_percentage or 0,
            "created_at": flow.created_at.isoformat() if flow.created_at else None,
            "updated_at": flow.updated_at.isoformat() if flow.updated_at else None,
            "client_account_id": flow.client_account_id,
            "engagement_id": flow.engagement_id,
        }

        if include_details:
            # Add detailed information
            flow_status.update(
                {
                    "data_import_id": flow.data_import_id,
                    "master_flow_id": flow.master_flow_id,
                    "field_mappings": flow.field_mappings,
                    "phases": flow.phases or {},
                    "error_details": flow.error_details,
                    "metadata": {
                        "total_assets": getattr(flow, "total_assets", 0),
                        "processed_assets": getattr(flow, "processed_assets", 0),
                        "agent_status": getattr(flow, "agent_status", {}),
                    },
                }
            )

            # Get extended state information if available
            try:
                extended_state_query = select(CrewAIFlowStateExtensions).where(
                    CrewAIFlowStateExtensions.flow_id == flow_id
                )
                extended_result = await db.execute(extended_state_query)
                extended_state = extended_result.scalar_one_or_none()

                if extended_state:
                    flow_status["extended_state"] = {
                        "flow_configuration": extended_state.flow_configuration,
                        "execution_metadata": extended_state.execution_metadata,
                        "current_state_data": extended_state.current_state_data,
                        "agent_interactions": extended_state.agent_interactions,
                        "checkpoint_data": extended_state.checkpoint_data,
                    }
            except Exception as e:
                logger.warning(f"Failed to get extended state for flow {flow_id}: {e}")
                flow_status["extended_state"] = None

        logger.info(f"✅ Flow status retrieved for flow {flow_id}")
        return flow_status

    except HTTPException:
        raise
    except Exception as e:
        logger.error(safe_log_format("Failed to get flow status: {e}", e=e))
        raise HTTPException(
            status_code=500, detail=f"Failed to get flow status: {str(e)}"
        )


@router.post("/{flow_id}/pause")
async def pause_flow(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """Pause a running discovery flow."""
    try:
        logger.info(safe_log_format("Pausing flow: {flow_id}", flow_id=flow_id))

        orchestrator = MasterFlowOrchestrator(db, context)
        result = await orchestrator.pause_flow(flow_id)

        return {
            "success": True,
            "flow_id": flow_id,
            "status": "paused",
            "result": result,
        }

    except Exception as e:
        logger.error(safe_log_format("Failed to pause flow: {e}", e=e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{flow_id}/resume")
async def resume_flow(
    flow_id: str,
    phase_input: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """Resume a paused discovery flow."""
    try:
        logger.info(safe_log_format("Resuming flow: {flow_id}", flow_id=flow_id))

        # Get the flow's current state
        stmt = select(DiscoveryFlow).where(
            and_(
                DiscoveryFlow.flow_id == flow_id,
                DiscoveryFlow.client_account_id == context.client_account_id,
                DiscoveryFlow.engagement_id == context.engagement_id,
            )
        )
        result = await db.execute(stmt)
        flow = result.scalar_one_or_none()

        if not flow:
            raise HTTPException(status_code=404, detail="Flow not found")

        if flow.status not in ["paused", "waiting_for_approval", "failed"]:
            raise HTTPException(
                status_code=400,
                detail=f"Flow cannot be resumed from status: {flow.status}",
            )

        # Resume through orchestrator
        orchestrator = MasterFlowOrchestrator(db, context)
        result = await orchestrator.resume_flow(flow_id, phase_input or {})

        return {
            "success": True,
            "flow_id": flow_id,
            "status": "resumed",
            "current_phase": flow.current_phase,
            "result": result,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(safe_log_format("Failed to resume flow: {e}", e=e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{flow_id}")
async def delete_flow(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """Delete a discovery flow."""
    try:
        logger.info(safe_log_format("Deleting flow: {flow_id}", flow_id=flow_id))

        # First check if the flow exists and belongs to the current context
        stmt = select(DiscoveryFlow).where(
            and_(
                DiscoveryFlow.flow_id == flow_id,
                DiscoveryFlow.client_account_id == context.client_account_id,
                DiscoveryFlow.engagement_id == context.engagement_id,
            )
        )
        result = await db.execute(stmt)
        flow = result.scalar_one_or_none()

        if not flow:
            raise HTTPException(status_code=404, detail="Flow not found")

        # Soft delete by updating status
        flow.status = FlowStatus.ARCHIVED.value
        flow.updated_at = datetime.now(timezone.utc)

        await db.commit()

        # Also update CrewAI Flow State if it exists
        master_stmt = (
            update(CrewAIFlowStateExtensions)
            .where(
                and_(
                    CrewAIFlowStateExtensions.flow_id == flow_id,
                    CrewAIFlowStateExtensions.client_account_id
                    == context.client_account_id,
                    CrewAIFlowStateExtensions.engagement_id == context.engagement_id,
                )
            )
            .values(
                flow_status=FlowStatus.ARCHIVED.value,
                updated_at=datetime.now(timezone.utc),
            )
        )

        await db.execute(master_stmt)
        await db.commit()

        return {
            "success": True,
            "flow_id": flow_id,
            "message": "Flow deleted successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(safe_log_format("Failed to delete flow: {e}", e=e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{flow_id}/retry")
async def retry_flow(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """Retry a failed discovery flow phase."""
    try:
        logger.info(safe_log_format("Retrying flow: {flow_id}", flow_id=flow_id))

        # Get the flow's current state
        stmt = select(DiscoveryFlow).where(
            and_(
                DiscoveryFlow.flow_id == flow_id,
                DiscoveryFlow.client_account_id == context.client_account_id,
                DiscoveryFlow.engagement_id == context.engagement_id,
            )
        )
        result = await db.execute(stmt)
        flow = result.scalar_one_or_none()

        if not flow:
            raise HTTPException(status_code=404, detail="Flow not found")

        if flow.status not in ["failed", "error"]:
            raise HTTPException(
                status_code=400,
                detail=f"Flow cannot be retried from status: {flow.status}",
            )

        # Retry through orchestrator
        orchestrator = MasterFlowOrchestrator(db, context)
        result = await orchestrator.retry_phase(flow_id, flow.current_phase)

        return {
            "success": True,
            "flow_id": flow_id,
            "phase_retried": flow.current_phase,
            "result": result,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(safe_log_format("Failed to retry flow: {e}", e=e))
        raise HTTPException(status_code=500, detail=str(e))
