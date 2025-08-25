"""
Unified Flow API Layer
Task MFO-059 through MFO-073: Unified API endpoints for all flow types
Provides a single, consistent API for creating, managing, and monitoring all CrewAI flows

This file has been modularized to stay within 400 lines.
All functionality is preserved through modular imports.
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.auth_utils import get_current_user
from app.api.v1.endpoints.context.services.user_service import UserService
from app.core.context import RequestContext, get_current_context_dependency
from app.core.database import get_db
from app.models import User
from app.services.master_flow_orchestrator import MasterFlowOrchestrator

# Import modularized components
from .flows_handlers.crud_operations import router as crud_router
from .flows_handlers.execution_operations import router as execution_router
from .flows_handlers.schemas import (
    FlowAnalyticsResponse,
    FlowResponse,
    FlowStatusResponse,
)

logger = logging.getLogger(__name__)


def safe_get_flow_field(
    flow_data: dict, field_name: str, fallback_name: str = None, default=None
):
    """
    Safely get field from flow data, handling both snake_case and legacy camelCase variants.

    Args:
        flow_data: The flow dictionary
        field_name: Primary field name (snake_case)
        fallback_name: Legacy field name (camelCase) for backward compatibility
        default: Default value if field not found
    """
    value = flow_data.get(field_name, default)
    if value is default and fallback_name:
        value = flow_data.get(fallback_name, default)
    return value


# Create main router
router = APIRouter()

# Include modularized routers
router.include_router(crud_router)
router.include_router(execution_router)


# ===========================
# Status and Analytics Endpoints
# ===========================


@router.get("/active", response_model=List[FlowResponse])
async def get_active_flows(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context: RequestContext = Depends(get_current_context_dependency),
):
    """
    Get all active flows for the current context
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

        active_flows = await orchestrator.get_active_flows()

        return [
            FlowResponse(
                flow_id=flow["flow_id"],
                flow_type=flow["flow_type"],
                flow_name=flow.get("flow_name"),
                status=safe_get_flow_field(flow, "status", "flow_status", "unknown"),
                phase=safe_get_flow_field(flow, "phase", "current_phase"),
                progress_percentage=flow.get("progress_percentage", 0.0),
                created_at=flow["created_at"],
                updated_at=flow["updated_at"],
                created_by=flow["created_by"],
                configuration=flow.get("configuration", {}),
                metadata=flow.get("metadata", {}),
            )
            for flow in active_flows
        ]

    except Exception as e:
        logger.error(f"Failed to get active flows: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get active flows: {str(e)}",
        )


@router.get("/{flow_id}/status", response_model=FlowStatusResponse)
async def get_flow_status(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context: RequestContext = Depends(get_current_context_dependency),
):
    """
    Get detailed status of a flow
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

        status = await orchestrator.get_flow_status(flow_id)

        if not status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Flow {flow_id} not found",
            )

        return FlowStatusResponse(
            flow_id=status["flow_id"],
            flow_type=status["flow_type"],
            flow_name=status.get("flow_name"),
            status=safe_get_flow_field(status, "status", "flow_status", "unknown"),
            phase=safe_get_flow_field(status, "phase", "current_phase"),
            progress_percentage=status.get("progress_percentage", 0.0),
            created_at=status["created_at"],
            updated_at=status["updated_at"],
            execution_history=status.get("execution_history", []),
            current_state=status.get("current_state", {}),
            error_details=status.get("error_details"),
            performance_metrics=status.get("performance_metrics", {}),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get flow status for {flow_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get flow status: {str(e)}",
        )


@router.get("/analytics/summary", response_model=FlowAnalyticsResponse)
async def get_flow_analytics(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context: RequestContext = Depends(get_current_context_dependency),
):
    """
    Get analytics summary for a flow
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

        analytics = await orchestrator.get_flow_analytics(flow_id)

        if not analytics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Analytics for flow {flow_id} not found",
            )

        return FlowAnalyticsResponse(
            flow_id=analytics["flow_id"],
            flow_type=analytics["flow_type"],
            phase_durations=analytics.get("phase_durations", {}),
            success_rate=analytics.get("success_rate", 0.0),
            error_count=analytics.get("error_count", 0),
            retry_count=analytics.get("retry_count", 0),
            data_processed=analytics.get("data_processed", {}),
            resource_usage=analytics.get("resource_usage", {}),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get analytics for flow {flow_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get flow analytics: {str(e)}",
        )


# ===========================
# Legacy Compatibility Endpoints (Deprecated)
# ===========================


@router.post("/legacy/discovery/create", response_model=FlowResponse, deprecated=True)
async def create_discovery_flow_legacy(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context: RequestContext = Depends(get_current_context_dependency),
):
    """
    Legacy endpoint for creating discovery flows
    """
    logger.warning("Using deprecated legacy endpoint for discovery flow creation")

    # Redirect to new unified endpoint
    from .flows_handlers.schemas import CreateFlowRequest

    request = CreateFlowRequest(
        flow_type="discovery",
        flow_name="Legacy Discovery Flow",
        configuration={},
        initial_state={},
    )

    # Use the new unified create_flow endpoint logic
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
        status=safe_get_flow_field(flow, "status", "flow_status", "unknown"),
        phase=safe_get_flow_field(flow, "phase", "current_phase"),
        progress_percentage=flow.get("progress_percentage", 0.0),
        created_at=flow["created_at"],
        updated_at=flow["updated_at"],
        created_by=flow["created_by"],
        configuration=flow.get("configuration", {}),
        metadata=flow.get("metadata", {}),
    )


logger.info("Unified flow API routes initialized with modular architecture")
