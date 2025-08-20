"""
Architecture standards management endpoints for assessment flows.
Handles standards retrieval and updates for assessments.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.auth_utils import get_current_user
from app.core.context_helpers import (
    verify_client_access,
    verify_standards_modification_permission,
)
from app.core.security.secure_logging import safe_log_format
from app.core.database import get_db
from app.repositories.assessment_flow_repository import AssessmentFlowRepository
from app.schemas.assessment_flow import ArchitectureStandardsUpdateRequest

# Import utilities
try:
    from app.api.v1.endpoints import assessment_flow_utils

    ASSESSMENT_FLOW_UTILS_AVAILABLE = True
except ImportError:
    ASSESSMENT_FLOW_UTILS_AVAILABLE = False

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{flow_id}/architecture-minimums")
async def get_architecture_standards(
    flow_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    client_account_id: str = Depends(verify_client_access),
):
    """
    Get architecture standards for assessment flow.

    - **flow_id**: Assessment flow identifier
    - Returns engagement standards and application overrides
    """
    try:
        repository = AssessmentFlowRepository(db, client_account_id)
        flow_state = await repository.get_assessment_flow_state(flow_id)

        if not flow_state:
            raise HTTPException(status_code=404, detail="Assessment flow not found")

        # Get engagement standards
        engagement_standards = await repository.get_engagement_standards(
            flow_state.engagement_id
        )

        # Get application overrides
        app_overrides = await repository.get_application_overrides(flow_id)

        # Get available templates if utils available
        templates_available = []
        if ASSESSMENT_FLOW_UTILS_AVAILABLE:
            templates_available = await assessment_flow_utils.get_available_templates()

        return {
            "engagement_standards": engagement_standards,
            "application_overrides": app_overrides,
            "templates_available": templates_available,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "Failed to get architecture standards: {str_e}", str_e=str(e)
            )
        )
        raise HTTPException(
            status_code=500, detail="Failed to retrieve architecture standards"
        )


@router.put("/{flow_id}/architecture-minimums")
async def update_architecture_standards(
    flow_id: str,
    request: ArchitectureStandardsUpdateRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    client_account_id: str = Depends(verify_client_access),
):
    """
    Update architecture standards and application overrides.

    - **flow_id**: Assessment flow identifier
    - **engagement_standards**: Engagement-level standards
    - **application_overrides**: Application-specific overrides
    """
    try:
        # Verify user permissions for standards modification
        await verify_standards_modification_permission(current_user, client_account_id)

        repository = AssessmentFlowRepository(db, client_account_id)
        flow_state = await repository.get_assessment_flow_state(flow_id)

        if not flow_state:
            raise HTTPException(status_code=404, detail="Assessment flow not found")

        # Update engagement standards
        if request.engagement_standards:
            await repository.save_architecture_standards(
                flow_state.engagement_id,
                request.engagement_standards,
                current_user.email,
            )

        # Update application overrides
        if request.application_overrides:
            await repository.save_application_overrides(
                flow_id, request.application_overrides, current_user.email
            )

        # Mark architecture as captured
        await repository.update_architecture_captured_status(flow_id, True)

        return {"message": "Architecture standards updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "Failed to update architecture standards: {str_e}", str_e=str(e)
            )
        )
        raise HTTPException(
            status_code=500, detail="Failed to update architecture standards"
        )
