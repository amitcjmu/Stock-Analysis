"""
Asset Preview API Endpoint

Per Issue #907: Allow users to preview and approve assets before database persistence.

CC: Preview transformed assets from flow_persistence_data before creating in DB
"""

import logging
from datetime import datetime
from typing import List, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Body
from pydantic import BaseModel, Field, validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.context import get_request_context, RequestContext
from app.api.v1.auth.auth_utils import get_current_user
from app.models.client_account import User
from app.repositories.crewai_flow_state_extensions_repository import (
    CrewAIFlowStateExtensionsRepository,
)


class ApproveAssetsRequest(BaseModel):
    """Request model for asset approval with validation"""

    approved_asset_ids: List[str] = Field(
        ...,
        min_items=1,
        max_items=1000,
        description="List of asset IDs to approve (max 1000)",
    )

    @validator("approved_asset_ids")
    def validate_asset_ids(cls, v):
        """Ensure all asset IDs are non-empty strings"""
        if not all(isinstance(id, str) and id.strip() for id in v):
            raise ValueError("All asset IDs must be non-empty strings")
        return v


router = APIRouter(prefix="/asset-preview")
logger = logging.getLogger(__name__)


@router.get("/{flow_id}")
async def get_asset_preview(
    flow_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    request_context: RequestContext = Depends(get_request_context),
) -> Dict[str, Any]:
    """
    Get preview of assets to be created from a flow's persistence data.

    Per Issue #907: Returns transformed assets before database persistence,
    allowing user review and approval.

    Args:
        flow_id: Master flow UUID

    Returns:
        Dictionary with:
        - assets_preview: List of asset data to be created
        - flow_id: Flow UUID
        - count: Number of assets
    """
    client_account_id = UUID(request_context.client_account_id)
    engagement_id = UUID(request_context.engagement_id)

    # Get flow with persistence data
    flow_repo = CrewAIFlowStateExtensionsRepository(
        db,
        str(client_account_id),
        str(engagement_id),
    )

    flow = await flow_repo.get_by_flow_id(str(flow_id))
    if not flow:
        logger.warning(
            f"Flow {flow_id} not found for client {client_account_id}, engagement {engagement_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Flow {flow_id} not found in your account context",
        )

    # Extract asset preview data from flow_persistence_data
    persistence_data = flow.flow_persistence_data or {}
    assets_preview = persistence_data.get("assets_preview", [])

    if not assets_preview:
        logger.info(f"No asset preview data found for flow {flow_id}")
        # Check if assets are already created
        if persistence_data.get("assets_created"):
            return {
                "flow_id": str(flow_id),
                "assets_preview": [],
                "count": 0,
                "status": "assets_already_created",
                "message": "Assets have already been created for this flow",
            }

    logger.info(
        f"Retrieved {len(assets_preview)} assets for preview from flow {flow_id}"
    )

    return {
        "flow_id": str(flow_id),
        "assets_preview": assets_preview,
        "count": len(assets_preview),
        "status": "preview_ready",
    }


@router.post("/{flow_id}/approve")
async def approve_asset_preview(
    flow_id: UUID,
    request: ApproveAssetsRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    request_context: RequestContext = Depends(get_request_context),
) -> Dict[str, Any]:
    """
    Approve selected assets for creation.

    Per Issue #907: User approves assets from preview, triggering database persistence.

    Args:
        flow_id: Master flow UUID
        request: Validated request containing approved_asset_ids (1-1000 items)

    Returns:
        Dictionary with created asset count and status

    Raises:
        HTTPException: 400 if asset_ids invalid, 404 if flow not found
    """
    approved_asset_ids = request.approved_asset_ids
    client_account_id = UUID(request_context.client_account_id)
    engagement_id = UUID(request_context.engagement_id)

    flow_repo = CrewAIFlowStateExtensionsRepository(
        db,
        str(client_account_id),
        str(engagement_id),
    )

    flow = await flow_repo.get_by_flow_id(str(flow_id))
    if not flow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Flow {flow_id} not found",
        )

    # CRITICAL FIX (Issue #917): Use dictionary reassignment for SQLAlchemy change tracking
    # Creating a new dictionary triggers automatic change detection for JSONB columns
    # This is cleaner than mutating in-place and using flag_modified()
    persistence_data = flow.flow_persistence_data or {}
    flow.flow_persistence_data = {
        **persistence_data,
        "approved_asset_ids": approved_asset_ids,
        "approval_timestamp": datetime.utcnow().isoformat(),
        "approved_by_user_id": str(current_user.id),
    }

    await db.commit()

    logger.info(
        f"User {current_user.id} approved {len(approved_asset_ids)} assets for flow {flow_id}"
    )

    # Resume the flow to process approved assets
    # Import resume functionality
    from app.api.v1.endpoints.unified_discovery.flow_control_handlers import (
        resume_flow as resume_flow_handler,
    )

    try:
        # Resume the flow - this will re-run the asset_inventory phase
        # which will now see the approved_asset_ids and create the assets
        await resume_flow_handler(
            flow_id=str(flow_id),
            phase_input=None,
            db=db,
            context=request_context,
            current_user=current_user,
        )

        logger.info(f"✅ Flow {flow_id} resumed after asset approval")

    except Exception as e:
        logger.warning(
            f"⚠️ Failed to auto-resume flow {flow_id} after approval: {e}. "
            "User may need to manually resume the flow."
        )
        # Don't fail the approval if resume fails - approval is still recorded

    return {
        "flow_id": str(flow_id),
        "approved_count": len(approved_asset_ids),
        "status": "approved",
        "message": f"Assets approved for creation. Flow resumed to create {len(approved_asset_ids)} assets.",
    }
