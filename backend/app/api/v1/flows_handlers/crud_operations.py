"""
Flow CRUD Operations
Create, Read, Update, Delete operations for flows.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.auth_utils import get_current_user
from app.api.v1.endpoints.context.services.user_service import UserService
from app.core.context import RequestContext, get_current_context_dependency
from app.core.database import get_db
from app.models import User
from app.services.master_flow_orchestrator import MasterFlowOrchestrator

from .schemas import CreateFlowRequest, FlowListResponse, FlowResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=FlowResponse, status_code=status.HTTP_201_CREATED)
async def create_flow(
    request: CreateFlowRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context: RequestContext = Depends(get_current_context_dependency),
):
    """
    Create a new flow
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

        flow = await orchestrator.create_flow(
            flow_type=request.flow_type,
            flow_name=request.flow_name,
            configuration=request.configuration,
            initial_state=request.initial_state,
        )

        return FlowResponse(
            flow_id=flow["flow_id"],
            flow_type=flow["flow_type"],
            flow_name=flow.get("flow_name"),
            status=flow["status"],
            phase=flow.get("phase"),
            progress_percentage=flow.get("progress_percentage", 0.0),
            created_at=flow["created_at"],
            updated_at=flow["updated_at"],
            created_by=flow["created_by"],
            configuration=flow.get("configuration", {}),
            metadata=flow.get("metadata", {}),
        )

    except Exception as e:
        logger.error(f"Failed to create flow: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create flow: {str(e)}",
        )


@router.get("/", response_model=FlowListResponse)
async def list_flows(
    flow_type: Optional[str] = Query(None, description="Filter by flow type"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    phase: Optional[str] = Query(None, description="Filter by phase"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context: RequestContext = Depends(get_current_context_dependency),
):
    """
    List flows with optional filtering
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

        result = await orchestrator.list_flows(
            flow_type=flow_type,
            status=status_filter,
            phase=phase,
            page=page,
            page_size=page_size,
        )

        flows = [
            FlowResponse(
                flow_id=flow["flow_id"],
                flow_type=flow["flow_type"],
                flow_name=flow.get("flow_name"),
                status=flow["status"],
                phase=flow.get("phase"),
                progress_percentage=flow.get("progress_percentage", 0.0),
                created_at=flow["created_at"],
                updated_at=flow["updated_at"],
                created_by=flow["created_by"],
                configuration=flow.get("configuration", {}),
                metadata=flow.get("metadata", {}),
            )
            for flow in result["flows"]
        ]

        return FlowListResponse(
            flows=flows,
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"],
        )

    except Exception as e:
        logger.error(f"Failed to list flows: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list flows: {str(e)}",
        )


@router.get("/{flow_id}", response_model=FlowResponse)
async def get_flow(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context: RequestContext = Depends(get_current_context_dependency),
):
    """
    Get flow by ID
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

        flow = await orchestrator.get_flow(flow_id)

        if not flow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Flow {flow_id} not found",
            )

        return FlowResponse(
            flow_id=flow["flow_id"],
            flow_type=flow["flow_type"],
            flow_name=flow.get("flow_name"),
            status=flow["status"],
            phase=flow.get("phase"),
            progress_percentage=flow.get("progress_percentage", 0.0),
            created_at=flow["created_at"],
            updated_at=flow["updated_at"],
            created_by=flow["created_by"],
            configuration=flow.get("configuration", {}),
            metadata=flow.get("metadata", {}),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get flow {flow_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get flow: {str(e)}",
        )


@router.delete("/{flow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_flow(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context: RequestContext = Depends(get_current_context_dependency),
):
    """
    Delete a flow
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

        success = await orchestrator.delete_flow(flow_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Flow {flow_id} not found or could not be deleted",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete flow {flow_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete flow: {str(e)}",
        )
