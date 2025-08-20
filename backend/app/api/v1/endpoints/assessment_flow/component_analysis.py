"""
Component analysis endpoints for assessment flows.
Handles application component identification and updates.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.auth_utils import get_current_user
from app.core.context_helpers import verify_client_access
from app.core.security.secure_logging import safe_log_format
from app.core.database import get_db
from app.repositories.assessment_flow_repository import AssessmentFlowRepository
from app.schemas.assessment_flow import ComponentUpdate

# Import utilities
try:
    from app.api.v1.endpoints import assessment_flow_utils

    ASSESSMENT_FLOW_UTILS_AVAILABLE = True
except ImportError:
    ASSESSMENT_FLOW_UTILS_AVAILABLE = False

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{flow_id}/components")
async def get_application_components(
    flow_id: str,
    app_id: Optional[str] = Query(None, description="Specific application ID"),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    client_account_id: str = Depends(verify_client_access),
):
    """
    Get identified components for all or specific application.

    - **flow_id**: Assessment flow identifier
    - **app_id**: Optional specific application ID filter
    - Returns component analysis results
    """
    try:
        repository = AssessmentFlowRepository(db, client_account_id)

        if not await repository.flow_exists(flow_id):
            raise HTTPException(status_code=404, detail="Assessment flow not found")

        if app_id:
            components = await repository.get_application_components(flow_id, app_id)
            return {"application_id": app_id, "components": components}
        else:
            all_components = await repository.get_all_application_components(flow_id)
            return {"components_by_application": all_components}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "Failed to get application components: {str_e}", str_e=str(e)
            )
        )
        raise HTTPException(
            status_code=500, detail="Failed to retrieve application components"
        )


@router.put("/{flow_id}/components/{app_id}")
async def update_application_components(
    flow_id: str,
    app_id: str,
    request: ComponentUpdate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    client_account_id: str = Depends(verify_client_access),
):
    """
    Update identified components for specific application.

    - **flow_id**: Assessment flow identifier
    - **app_id**: Application identifier
    - **components**: Updated component list with analysis
    """
    try:
        repository = AssessmentFlowRepository(db, client_account_id)
        flow_state = await repository.get_assessment_flow_state(flow_id)

        if not flow_state:
            raise HTTPException(status_code=404, detail="Assessment flow not found")

        # Validate application is part of the flow
        if app_id not in (flow_state.selected_application_ids or []):
            raise HTTPException(
                status_code=400, detail="Application not part of this assessment flow"
            )

        # Update components with validation if utils available
        if ASSESSMENT_FLOW_UTILS_AVAILABLE:
            validated_components = await assessment_flow_utils.validate_components(
                request.components
            )
        else:
            validated_components = request.components

        # Save component updates
        await repository.save_application_components(
            flow_id, app_id, validated_components, current_user.email
        )

        return {
            "application_id": app_id,
            "components_updated": len(validated_components),
            "message": "Application components updated successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "Failed to update application components: {str_e}", str_e=str(e)
            )
        )
        raise HTTPException(
            status_code=500, detail="Failed to update application components"
        )
