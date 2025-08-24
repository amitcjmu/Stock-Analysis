"""
Flow Execution Operations
Execute, pause, resume flow operations.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.auth_utils import get_current_user
from app.api.v1.endpoints.context.services.user_service import UserService
from app.core.context import RequestContext, get_current_context_dependency
from app.core.database import get_db
from app.models import User
from app.services.master_flow_orchestrator import MasterFlowOrchestrator

from .schemas import ExecutePhaseRequest, FlowResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/{flow_id}/execute", response_model=FlowResponse)
async def execute_flow_phase(
    flow_id: str,
    request: ExecutePhaseRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context: RequestContext = Depends(get_current_context_dependency),
):
    """
    Execute the next phase of a flow or a specific phase
    """
    try:
        user_service = UserService(db)
        is_admin = await user_service.is_admin(current_user.id)

        orchestrator = MasterFlowOrchestrator(
            db_session=db,
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id,
            current_user_id=str(current_user.id),
            is_admin=is_admin,
        )

        # Check if flow exists and is in valid state
        flow = await orchestrator.get_flow(flow_id)
        if not flow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Flow {flow_id} not found",
            )

        if flow["status"] in ["completed", "failed", "cancelled"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot execute phase for flow in {flow['status']} status",
            )

        # Execute the phase
        result = await orchestrator.execute_phase(
            flow_id=flow_id,
            phase_input=request.phase_input,
            force_execution=request.force_execution,
        )

        return FlowResponse(
            flow_id=result["flow_id"],
            flow_type=result["flow_type"],
            flow_name=result.get("flow_name"),
            status=result["status"],
            phase=result.get("phase"),
            progress_percentage=result.get("progress_percentage", 0.0),
            created_at=result["created_at"],
            updated_at=result["updated_at"],
            created_by=result["created_by"],
            configuration=result.get("configuration", {}),
            metadata=result.get("metadata", {}),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute phase for flow {flow_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute flow phase: {str(e)}",
        )


@router.post("/{flow_id}/pause", response_model=FlowResponse)
async def pause_flow(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context: RequestContext = Depends(get_current_context_dependency),
):
    """
    Pause a running flow
    """
    try:
        user_service = UserService(db)
        is_admin = await user_service.is_admin(current_user.id)

        orchestrator = MasterFlowOrchestrator(
            db_session=db,
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id,
            current_user_id=str(current_user.id),
            is_admin=is_admin,
        )

        result = await orchestrator.pause_flow(flow_id)

        return FlowResponse(
            flow_id=result["flow_id"],
            flow_type=result["flow_type"],
            flow_name=result.get("flow_name"),
            status=result["status"],
            phase=result.get("phase"),
            progress_percentage=result.get("progress_percentage", 0.0),
            created_at=result["created_at"],
            updated_at=result["updated_at"],
            created_by=result["created_by"],
            configuration=result.get("configuration", {}),
            metadata=result.get("metadata", {}),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to pause flow {flow_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to pause flow: {str(e)}",
        )


@router.post("/{flow_id}/resume", response_model=FlowResponse)
async def resume_flow(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context: RequestContext = Depends(get_current_context_dependency),
):
    """
    Resume a paused flow
    """
    try:
        user_service = UserService(db)
        is_admin = await user_service.is_admin(current_user.id)

        orchestrator = MasterFlowOrchestrator(
            db_session=db,
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id,
            current_user_id=str(current_user.id),
            is_admin=is_admin,
        )

        result = await orchestrator.resume_flow(flow_id)

        return FlowResponse(
            flow_id=result["flow_id"],
            flow_type=result["flow_type"],
            flow_name=result.get("flow_name"),
            status=result["status"],
            phase=result.get("phase"),
            progress_percentage=result.get("progress_percentage", 0.0),
            created_at=result["created_at"],
            updated_at=result["updated_at"],
            created_by=result["created_by"],
            configuration=result.get("configuration", {}),
            metadata=result.get("metadata", {}),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resume flow {flow_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resume flow: {str(e)}",
        )
