"""Collection Application Selection endpoints.

This module handles application selection for collection flows,
enabling targeted questionnaire generation based on selected applications.
"""

import logging
from typing import Dict, Any
from datetime import datetime

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.auth_utils import get_current_user
from app.core.context import get_request_context
from app.core.database import get_db
from app.models import User
from app.schemas.collection_flow import CollectionFlowUpdate
from app.api.v1.endpoints import collection_crud

logger = logging.getLogger(__name__)


async def update_flow_applications(
    flow_id: str,
    request_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context=Depends(get_request_context),
) -> Dict[str, Any]:
    """Update collection flow with selected applications for questionnaire generation.

    This endpoint allows users to specify which applications should be included
    in a collection flow, enabling targeted questionnaire generation and gap analysis.

    Args:
        flow_id: The collection flow ID to update
        request_data: Request containing selected_application_ids and optional action

    Returns:
        Dict indicating success/failure and updated flow status
    """
    try:
        selected_application_ids = request_data.get("selected_application_ids", [])
        action = request_data.get("action", "update_applications")

        if not selected_application_ids:
            raise HTTPException(
                status_code=400,
                detail="selected_application_ids is required and cannot be empty",
            )

        logger.info(
            f"Updating collection flow {flow_id} with {len(selected_application_ids)} applications"
        )

        # Create update data for the collection flow
        update_data = CollectionFlowUpdate(
            collection_config={
                "selected_application_ids": selected_application_ids,
                "has_applications": True,
                "application_count": len(selected_application_ids),
                "updated_at": str(datetime.utcnow()),
                "action": action,
            },
            trigger_questionnaire_generation=True,  # Trigger questionnaire generation after application selection
        )

        # Update the collection flow
        result = await collection_crud.update_collection_flow(
            flow_id=flow_id,
            flow_data=update_data,
            db=db,
            current_user=current_user,
            context=context,
        )

        return {
            "success": True,
            "message": f"Successfully updated collection flow with {len(selected_application_ids)} applications",
            "flow_id": flow_id,
            "selected_application_count": len(selected_application_ids),
            "flow": result.model_dump() if hasattr(result, "model_dump") else result,
        }

    except HTTPException:
        raise
    except Exception as error:
        logger.error(f"Error updating collection flow {flow_id} applications: {error}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update collection flow applications: {str(error)}",
        )
