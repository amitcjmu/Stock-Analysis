"""
Tech debt analysis endpoints for assessment flows.
Handles tech debt analysis retrieval and updates.
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
from app.schemas.assessment_flow import TechDebtUpdates

# Import utilities
try:
    from app.api.v1.endpoints import assessment_flow_utils

    ASSESSMENT_FLOW_UTILS_AVAILABLE = True
except ImportError:
    ASSESSMENT_FLOW_UTILS_AVAILABLE = False

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{flow_id}/tech-debt")
async def get_tech_debt_analysis(
    flow_id: str,
    app_id: Optional[str] = Query(None, description="Specific application ID"),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    client_account_id: str = Depends(verify_client_access),
):
    """
    Get tech debt analysis for all or specific application.

    - **flow_id**: Assessment flow identifier
    - **app_id**: Optional specific application ID filter
    - Returns tech debt analysis results
    """
    try:
        repository = AssessmentFlowRepository(db, client_account_id)

        if not await repository.flow_exists(flow_id):
            raise HTTPException(status_code=404, detail="Assessment flow not found")

        if app_id:
            tech_debt = await repository.get_tech_debt_analysis(flow_id, app_id)
            return {"application_id": app_id, "tech_debt_analysis": tech_debt}
        else:
            all_tech_debt = await repository.get_all_tech_debt_analysis(flow_id)
            return {"tech_debt_by_application": all_tech_debt}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format("Failed to get tech debt analysis: {str_e}", str_e=str(e))
        )
        raise HTTPException(
            status_code=500, detail="Failed to retrieve tech debt analysis"
        )


@router.put("/{flow_id}/tech-debt/{app_id}")
async def update_tech_debt_analysis(
    flow_id: str,
    app_id: str,
    request: TechDebtUpdates,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    client_account_id: str = Depends(verify_client_access),
):
    """
    Update tech debt analysis for specific application.

    - **flow_id**: Assessment flow identifier
    - **app_id**: Application identifier
    - **tech_debt_items**: Updated tech debt analysis
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

        # Validate tech debt items if utils available
        if ASSESSMENT_FLOW_UTILS_AVAILABLE:
            validated_tech_debt = await assessment_flow_utils.validate_tech_debt_items(
                request.tech_debt_items
            )
        else:
            validated_tech_debt = request.tech_debt_items

        # Save tech debt analysis
        await repository.save_tech_debt_analysis(
            flow_id, app_id, validated_tech_debt, current_user.email
        )

        return {
            "application_id": app_id,
            "tech_debt_items_updated": len(validated_tech_debt),
            "message": "Tech debt analysis updated successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "Failed to update tech debt analysis: {str_e}", str_e=str(e)
            )
        )
        raise HTTPException(
            status_code=500, detail="Failed to update tech debt analysis"
        )
