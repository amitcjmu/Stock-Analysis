"""
6R decision endpoints for assessment flows.
Handles 6R migration strategy decisions and updates.
Uses MFO integration layer per ADR-006 (Master Flow Orchestrator pattern).
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.auth_utils import get_current_user
from app.core.context_helpers import verify_client_access
from app.core.security.secure_logging import safe_log_format
from app.core.database import get_db
from app.repositories.assessment_flow_repository import AssessmentFlowRepository
from app.schemas.assessment_flow import SixRDecisionUpdate

# Import MFO integration functions (per ADR-006)
from .mfo_integration import get_assessment_status_via_mfo

# Import utilities
try:
    from app.api.v1.endpoints import assessment_flow_validators

    ASSESSMENT_FLOW_VALIDATORS_AVAILABLE = True
except ImportError:
    ASSESSMENT_FLOW_VALIDATORS_AVAILABLE = False

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{flow_id}/sixr-decisions")
async def get_sixr_decisions(
    flow_id: str,
    app_id: Optional[str] = Query(None, description="Specific application ID"),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    client_account_id: str = Depends(verify_client_access),
):
    """
    Get 6R migration decisions for all or specific application via MFO.

    - **flow_id**: Assessment flow identifier
    - **app_id**: Optional specific application ID filter
    - Returns 6R decision analysis
    - Uses MFO integration (ADR-006) to verify flow existence
    """
    try:
        # Verify flow exists via MFO (checks both master and child tables)
        try:
            await get_assessment_status_via_mfo(UUID(flow_id), db)
        except ValueError:
            raise HTTPException(status_code=404, detail="Assessment flow not found")

        repository = AssessmentFlowRepository(db, client_account_id)

        if app_id:
            sixr_decision = await repository.get_sixr_decision(flow_id, app_id)
            return {"application_id": app_id, "sixr_decision": sixr_decision}
        else:
            all_decisions = await repository.get_all_sixr_decisions(flow_id)
            return {"sixr_decisions_by_application": all_decisions}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format("Failed to get 6R decisions: {str_e}", str_e=str(e))
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve 6R decisions")


@router.put("/{flow_id}/sixr-decisions/{app_id}")
async def update_sixr_decision(
    flow_id: str,
    app_id: str,
    request: SixRDecisionUpdate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    client_account_id: str = Depends(verify_client_access),
):
    """
    Update 6R migration decision for specific application via MFO.

    - **flow_id**: Assessment flow identifier
    - **app_id**: Application identifier
    - **strategy**: 6R migration strategy (Rehost, Replatform, etc.)
    - **reasoning**: Decision reasoning and details
    - Uses MFO integration (ADR-006) to verify flow existence
    """
    try:
        # Get flow state via MFO (checks both master and child tables)
        _ = await get_assessment_status_via_mfo(UUID(flow_id), db)

        # Also get child flow for application_ids validation
        repository = AssessmentFlowRepository(db, client_account_id)
        flow_state = await repository.get_assessment_flow_state(flow_id)

        if not flow_state:
            raise HTTPException(status_code=404, detail="Assessment flow not found")

        # Validate application is part of the flow
        if app_id not in (flow_state.selected_application_ids or []):
            raise HTTPException(
                status_code=400, detail="Application not part of this assessment flow"
            )

        # Validate 6R decision if validators available
        if ASSESSMENT_FLOW_VALIDATORS_AVAILABLE:
            await assessment_flow_validators.validate_sixr_decision(
                request.strategy, request.reasoning
            )

        # Save 6R decision
        await repository.save_sixr_decision(
            flow_id,
            app_id,
            request.strategy,
            request.reasoning,
            request.confidence_level,
            current_user.email,
        )

        return {
            "application_id": app_id,
            "strategy": request.strategy,
            "confidence_level": request.confidence_level,
            "message": "6R decision updated successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format("Failed to update 6R decision: {str_e}", str_e=str(e))
        )
        raise HTTPException(status_code=500, detail="Failed to update 6R decision")
