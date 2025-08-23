"""
Discovery flow endpoints for managing discovery workflows.
"""

import logging
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc

from app.core.database import get_async_db
from app.core.auth import get_current_user
from app.models.user import User
from app.utils.endpoint_migration_logger import endpoint_migration_warning
from app.models.discovery_flow import DiscoveryFlow
from app.models.flow_state import CrewAIFlowStateExtension
from app.services.flow_service import FlowService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/flows/active")
@endpoint_migration_warning("/api/v1/discovery/flows/active")
async def get_active_discovery_flows(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get active discovery flows for the current user's context.

    ⚠️ MIGRATION NOTICE: This endpoint is LEGACY. Please use /api/v1/unified-discovery/flows/active instead.
    This endpoint may be deprecated in future versions.
    """
    try:
        # Get user's client_account_id and engagement_id from the current user
        client_account_id = getattr(current_user, "client_account_id", None)
        engagement_id = getattr(current_user, "engagement_id", None)

        if not client_account_id or not engagement_id:
            # Try to get from user profile
            from app.models.user_profile import UserProfile

            profile_query = select(UserProfile).where(
                UserProfile.user_id == current_user.id
            )
            profile_result = await db.execute(profile_query)
            profile = profile_result.scalar_one_or_none()

            if profile:
                client_account_id = profile.client_account_id
                engagement_id = profile.engagement_id

        if not client_account_id or not engagement_id:
            logger.warning(f"No client/engagement context for user {current_user.id}")
            return {"flows": [], "message": "No active flows found for current context"}

        # Query for active discovery flows
        query = (
            select(DiscoveryFlow)
            .where(
                and_(
                    DiscoveryFlow.client_account_id == client_account_id,
                    DiscoveryFlow.engagement_id == engagement_id,
                    or_(
                        DiscoveryFlow.status == "active",
                        DiscoveryFlow.status == "in_progress",
                        DiscoveryFlow.status == "pending",
                    ),
                )
            )
            .order_by(desc(DiscoveryFlow.updated_at))
        )

        result = await db.execute(query)
        flows = result.scalars().all()

        # Format response
        flow_data = []
        for flow in flows:
            # Get associated CrewAI state if exists
            state_query = select(CrewAIFlowStateExtension).where(
                and_(
                    CrewAIFlowStateExtension.flow_id == flow.id,
                    CrewAIFlowStateExtension.flow_type == "discovery",
                )
            )
            state_result = await db.execute(state_query)
            crew_state = state_result.scalar_one_or_none()

            flow_dict = {
                "id": str(flow.id),
                "name": flow.name or f"Discovery Flow {flow.id}",
                "status": flow.status,
                "current_phase": flow.current_phase,
                "phase_status": flow.phase_status,
                "created_at": flow.created_at.isoformat() if flow.created_at else None,
                "updated_at": flow.updated_at.isoformat() if flow.updated_at else None,
                "metadata": flow.metadata or {},
                "crew_state": (
                    {
                        "status": crew_state.status if crew_state else None,
                        "current_step": crew_state.current_step if crew_state else None,
                        "error": crew_state.error if crew_state else None,
                    }
                    if crew_state
                    else None
                ),
            }
            flow_data.append(flow_dict)

        logger.warning(
            f"LEGACY ENDPOINT USED: /discovery/flows/active by user {current_user.id} - "
            f"Consider migrating to /unified-discovery/flows/active"
        )
        logger.info(
            f"Found {len(flow_data)} active discovery flows for user {current_user.id}"
        )

        return {
            "flows": flow_data,
            "count": len(flow_data),
            "client_account_id": str(client_account_id),
            "engagement_id": str(engagement_id),
        }

    except Exception as e:
        logger.error(f"Error getting active discovery flows: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve active discovery flows: {str(e)}",
        )


@router.post("/flows/initialize")
async def initialize_discovery_flow(
    flow_data: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Initialize a new discovery flow.
    """
    try:
        # Get user context
        client_account_id = getattr(current_user, "client_account_id", None)
        engagement_id = getattr(current_user, "engagement_id", None)

        if not client_account_id or not engagement_id:
            from app.models.user_profile import UserProfile

            profile_query = select(UserProfile).where(
                UserProfile.user_id == current_user.id
            )
            profile_result = await db.execute(profile_query)
            profile = profile_result.scalar_one_or_none()

            if profile:
                client_account_id = profile.client_account_id
                engagement_id = profile.engagement_id

        if not client_account_id or not engagement_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing client account or engagement context",
            )

        # Initialize flow using FlowService
        flow_service = FlowService(db)

        # Create flow initialization data
        init_data = {
            "flow_type": "discovery",
            "client_account_id": str(client_account_id),
            "engagement_id": str(engagement_id),
            "user_id": str(current_user.id),
            "metadata": flow_data or {},
        }

        # Initialize the flow
        flow = await flow_service.initialize_flow(**init_data)

        logger.info(f"Initialized discovery flow {flow.id} for user {current_user.id}")

        return {
            "flow_id": str(flow.id),
            "status": "initialized",
            "message": "Discovery flow initialized successfully",
            "flow": {
                "id": str(flow.id),
                "status": flow.status,
                "current_phase": flow.current_phase,
                "created_at": flow.created_at.isoformat() if flow.created_at else None,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initializing discovery flow: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize discovery flow: {str(e)}",
        )


@router.get("/flows/{flow_id}")
@endpoint_migration_warning("/api/v1/discovery/flows/{flow_id}")
async def get_discovery_flow(
    flow_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get details of a specific discovery flow.
    """
    try:
        # Query for the flow
        query = select(DiscoveryFlow).where(DiscoveryFlow.id == flow_id)
        result = await db.execute(query)
        flow = result.scalar_one_or_none()

        if not flow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Discovery flow {flow_id} not found",
            )

        # Check user has access to this flow
        client_account_id = getattr(current_user, "client_account_id", None)
        engagement_id = getattr(current_user, "engagement_id", None)

        if not client_account_id or not engagement_id:
            from app.models.user_profile import UserProfile

            profile_query = select(UserProfile).where(
                UserProfile.user_id == current_user.id
            )
            profile_result = await db.execute(profile_query)
            profile = profile_result.scalar_one_or_none()

            if profile:
                client_account_id = profile.client_account_id
                engagement_id = profile.engagement_id

        if (
            flow.client_account_id != client_account_id
            or flow.engagement_id != engagement_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this discovery flow",
            )

        # Get associated CrewAI state
        state_query = select(CrewAIFlowStateExtension).where(
            and_(
                CrewAIFlowStateExtension.flow_id == flow.id,
                CrewAIFlowStateExtension.flow_type == "discovery",
            )
        )
        state_result = await db.execute(state_query)
        crew_state = state_result.scalar_one_or_none()

        return {
            "id": str(flow.id),
            "name": flow.name or f"Discovery Flow {flow.id}",
            "status": flow.status,
            "current_phase": flow.current_phase,
            "phase_status": flow.phase_status,
            "phase_metadata": flow.phase_metadata or {},
            "created_at": flow.created_at.isoformat() if flow.created_at else None,
            "updated_at": flow.updated_at.isoformat() if flow.updated_at else None,
            "metadata": flow.metadata or {},
            "crew_state": (
                {
                    "status": crew_state.status if crew_state else None,
                    "current_step": crew_state.current_step if crew_state else None,
                    "completed_steps": crew_state.completed_steps if crew_state else [],
                    "error": crew_state.error if crew_state else None,
                    "metadata": crew_state.metadata if crew_state else {},
                }
                if crew_state
                else None
            ),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting discovery flow {flow_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve discovery flow: {str(e)}",
        )


@router.put("/flows/{flow_id}/status")
@endpoint_migration_warning("/api/v1/discovery/flows/{flow_id}/status")
async def update_discovery_flow_status(
    flow_id: UUID,
    status_data: Dict[str, Any],
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Update the status of a discovery flow.
    """
    try:
        # Query for the flow
        query = select(DiscoveryFlow).where(DiscoveryFlow.id == flow_id)
        result = await db.execute(query)
        flow = result.scalar_one_or_none()

        if not flow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Discovery flow {flow_id} not found",
            )

        # Check user has access
        client_account_id = getattr(current_user, "client_account_id", None)
        engagement_id = getattr(current_user, "engagement_id", None)

        if not client_account_id or not engagement_id:
            from app.models.user_profile import UserProfile

            profile_query = select(UserProfile).where(
                UserProfile.user_id == current_user.id
            )
            profile_result = await db.execute(profile_query)
            profile = profile_result.scalar_one_or_none()

            if profile:
                client_account_id = profile.client_account_id
                engagement_id = profile.engagement_id

        if (
            flow.client_account_id != client_account_id
            or flow.engagement_id != engagement_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this discovery flow",
            )

        # Update flow status
        if "status" in status_data:
            flow.status = status_data["status"]
        if "current_phase" in status_data:
            flow.current_phase = status_data["current_phase"]
        if "phase_status" in status_data:
            flow.phase_status = status_data["phase_status"]
        if "metadata" in status_data:
            flow.metadata = {**(flow.metadata or {}), **status_data["metadata"]}

        await db.commit()
        await db.refresh(flow)

        logger.info(f"Updated discovery flow {flow_id} status to {flow.status}")

        return {
            "id": str(flow.id),
            "status": flow.status,
            "current_phase": flow.current_phase,
            "phase_status": flow.phase_status,
            "updated_at": flow.updated_at.isoformat() if flow.updated_at else None,
            "message": "Flow status updated successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error updating discovery flow {flow_id}: {str(e)}", exc_info=True
        )
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update discovery flow: {str(e)}",
        )
