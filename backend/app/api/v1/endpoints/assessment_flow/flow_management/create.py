"""
Assessment flow creation endpoint.
Handles initialization of new assessment flows with selected applications.
Uses MFO integration layer per ADR-006 (Master Flow Orchestrator pattern).
"""

import logging
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.auth_utils import get_current_user
from app.core.context_helpers import (
    verify_client_access,
    verify_engagement_access,
)
from app.core.security.secure_logging import safe_log_format
from app.core.database import get_db
from app.models.assessment_flow import AssessmentPhase
from app.schemas.assessment_flow import (
    AssessmentFlowCreateRequest,
    AssessmentFlowResponse,
)

# Import MFO integration functions (per ADR-006)
from ..mfo_integration import create_assessment_via_mfo

# Import integration services
try:
    from app.services.integrations.discovery_integration import DiscoveryFlowIntegration

    DISCOVERY_INTEGRATION_AVAILABLE = True
except ImportError:
    DISCOVERY_INTEGRATION_AVAILABLE = False

try:
    from app.api.v1.endpoints import assessment_flow_processors

    ASSESSMENT_FLOW_SERVICE_AVAILABLE = True
except ImportError:
    ASSESSMENT_FLOW_SERVICE_AVAILABLE = False

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/initialize", response_model=AssessmentFlowResponse)
async def initialize_assessment_flow(
    request: AssessmentFlowCreateRequest,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    client_account_id: str = Depends(verify_client_access),
    engagement_id: str = Header(..., alias="X-Engagement-ID"),
):
    """
    Initialize new assessment flow with selected applications.

    - **selected_application_ids**: List of application IDs to assess (1-100 applications)
    - Returns flow_id and initial status
    - Starts background assessment process
    """
    try:
        logger.info(
            f"Initializing assessment flow for {len(request.selected_application_ids)} applications"
        )

        # Verify user has access to engagement
        await verify_engagement_access(db, engagement_id, client_account_id)

        # Verify applications are ready for assessment (if Discovery integration available)
        if DISCOVERY_INTEGRATION_AVAILABLE:
            discovery_integration = DiscoveryFlowIntegration()
            await discovery_integration.verify_applications_ready_for_assessment(
                db, request.selected_application_ids, client_account_id
            )

        # Convert string UUIDs to UUID objects for MFO
        application_ids_uuid = [
            UUID(app_id) for app_id in request.selected_application_ids
        ]

        # Create assessment flow via MFO (ADR-006: Two-table pattern)
        # Issue #861: Pass source_collection_id to enable application loading
        result = await create_assessment_via_mfo(
            client_account_id=UUID(client_account_id),
            engagement_id=UUID(engagement_id),
            application_ids=application_ids_uuid,
            user_id=str(current_user.id),  # Convert UUID to string for VARCHAR column
            flow_name=request.flow_name if hasattr(request, "flow_name") else None,
            source_collection_id=request.source_collection_id,  # Fix for Issue #861
            db=db,
        )

        flow_id = result["flow_id"]

        # Start flow execution in background
        if ASSESSMENT_FLOW_SERVICE_AVAILABLE:
            background_tasks.add_task(
                assessment_flow_processors.execute_assessment_flow_initialization,
                flow_id,
                client_account_id,
                engagement_id,
                current_user.id,
            )

        return AssessmentFlowResponse(
            flow_id=flow_id,  # Master flow_id from MFO
            status=result["status"],
            current_phase=result["current_phase"],
            # Per ADR-027: Use READINESS_ASSESSMENT not deprecated ARCHITECTURE_MINIMUMS
            next_phase=AssessmentPhase.READINESS_ASSESSMENT,
            selected_applications=result["selected_applications"],
            message=result["message"],
        )

    except ValueError as e:
        logger.warning(
            safe_log_format(
                "Assessment flow initialization validation error: {str_e}", str_e=str(e)
            )
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(
            safe_log_format(
                "Assessment flow initialization failed: {str_e}", str_e=str(e)
            )
        )
        raise HTTPException(
            status_code=500, detail="Assessment flow initialization failed"
        )
