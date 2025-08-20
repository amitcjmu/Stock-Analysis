"""
Assessment flow management endpoints.
Handles initialization, status, resume, and navigation operations.
"""

import logging
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.auth_utils import get_current_user
from app.core.context_helpers import (
    verify_client_access,
    verify_engagement_access,
)
from app.core.security.secure_logging import safe_log_format
from app.core.database import get_db
from app.models.assessment_flow import AssessmentFlowStatus, AssessmentPhase
from app.repositories.assessment_flow_repository import AssessmentFlowRepository
from app.schemas.assessment_flow import (
    AssessmentFlowCreateRequest,
    AssessmentFlowResponse,
    AssessmentFlowStatusResponse,
    ResumeFlowRequest,
)

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

        # Create assessment flow repository
        repository = AssessmentFlowRepository(db, client_account_id)

        # Initialize flow
        flow_id = await repository.create_assessment_flow(
            engagement_id=engagement_id,
            selected_application_ids=request.selected_application_ids,
            created_by=current_user.email,
        )

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
            flow_id=flow_id,
            status=AssessmentFlowStatus.INITIALIZED,
            current_phase=AssessmentPhase.ARCHITECTURE_MINIMUMS,
            next_phase=AssessmentPhase.ARCHITECTURE_MINIMUMS,
            selected_applications=len(request.selected_application_ids),
            message="Assessment flow initialized successfully",
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


@router.get("/{flow_id}/status", response_model=AssessmentFlowStatusResponse)
async def get_assessment_flow_status(
    flow_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    client_account_id: str = Depends(verify_client_access),
):
    """
    Get current status and progress of assessment flow.

    - **flow_id**: Assessment flow identifier
    - Returns detailed status including phase data and progress
    """
    try:
        repository = AssessmentFlowRepository(db, client_account_id)
        flow_state = await repository.get_assessment_flow_state(flow_id)

        if not flow_state:
            raise HTTPException(status_code=404, detail="Assessment flow not found")

        # Calculate progress based on completed phases
        progress_percentage = _calculate_progress_percentage(flow_state)

        return AssessmentFlowStatusResponse(
            flow_id=flow_id,
            status=flow_state.status,
            current_phase=flow_state.current_phase,
            progress_percentage=progress_percentage,
            phase_data=flow_state.phase_data or {},
            created_at=flow_state.created_at,
            updated_at=flow_state.updated_at,
            selected_applications=len(flow_state.selected_application_ids or []),
            assessment_complete=(flow_state.status == AssessmentFlowStatus.COMPLETED),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "Failed to get assessment flow status: {str_e}", str_e=str(e)
            )
        )
        raise HTTPException(status_code=500, detail="Failed to get flow status")


@router.post("/{flow_id}/resume", response_model=AssessmentFlowResponse)
async def resume_assessment_flow(
    flow_id: str,
    request: ResumeFlowRequest,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    client_account_id: str = Depends(verify_client_access),
):
    """
    Resume paused assessment flow from specific phase.

    - **flow_id**: Assessment flow identifier
    - **phase**: Phase to resume from (optional, continues from current if not specified)
    - Restarts flow processing
    """
    try:
        repository = AssessmentFlowRepository(db, client_account_id)
        flow_state = await repository.get_assessment_flow_state(flow_id)

        if not flow_state:
            raise HTTPException(status_code=404, detail="Assessment flow not found")

        if flow_state.status == AssessmentFlowStatus.COMPLETED:
            raise HTTPException(
                status_code=400, detail="Assessment flow already completed"
            )

        # Update flow to resume from specified phase or current phase
        resume_phase = request.phase or flow_state.current_phase

        await repository.update_flow_status(
            flow_id, AssessmentFlowStatus.IN_PROGRESS, current_phase=resume_phase
        )

        # Start flow processing in background
        if ASSESSMENT_FLOW_SERVICE_AVAILABLE:
            background_tasks.add_task(
                assessment_flow_processors.continue_assessment_flow,
                flow_id,
                client_account_id,
                resume_phase,
                current_user.id,
            )

        return AssessmentFlowResponse(
            flow_id=flow_id,
            status=AssessmentFlowStatus.IN_PROGRESS,
            current_phase=resume_phase,
            next_phase=_get_next_phase(resume_phase),
            selected_applications=len(flow_state.selected_application_ids or []),
            message=f"Assessment flow resumed from {resume_phase.value}",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format("Failed to resume assessment flow: {str_e}", str_e=str(e))
        )
        raise HTTPException(status_code=500, detail="Failed to resume flow")


@router.put("/{flow_id}/navigate-to-phase/{phase}")
async def navigate_to_assessment_phase(
    flow_id: str,
    phase: AssessmentPhase,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    client_account_id: str = Depends(verify_client_access),
):
    """
    Navigate assessment flow to specific phase.

    - **flow_id**: Assessment flow identifier
    - **phase**: Target phase to navigate to
    - Updates current phase without triggering automatic progression
    """
    try:
        repository = AssessmentFlowRepository(db, client_account_id)
        flow_state = await repository.get_assessment_flow_state(flow_id)

        if not flow_state:
            raise HTTPException(status_code=404, detail="Assessment flow not found")

        # Update current phase
        await repository.update_flow_phase(flow_id, phase)

        return {
            "flow_id": flow_id,
            "previous_phase": flow_state.current_phase.value,
            "current_phase": phase.value,
            "next_phase": (
                _get_next_phase(phase).value if _get_next_phase(phase) else None
            ),
            "message": f"Successfully navigated to {phase.value}",
            "timestamp": datetime.utcnow(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format("Failed to navigate to phase: {str_e}", str_e=str(e))
        )
        raise HTTPException(status_code=500, detail="Failed to navigate to phase")


def _calculate_progress_percentage(flow_state) -> int:
    """Calculate progress percentage based on completed phases."""
    phase_order = [
        AssessmentPhase.ARCHITECTURE_MINIMUMS,
        AssessmentPhase.COMPONENT_ANALYSIS,
        AssessmentPhase.TECH_DEBT_ANALYSIS,
        AssessmentPhase.SIX_R_DECISION,
        AssessmentPhase.FINALIZATION,
    ]

    try:
        current_index = phase_order.index(flow_state.current_phase)
        return int((current_index / len(phase_order)) * 100)
    except ValueError:
        return 0


def _get_next_phase(current_phase: AssessmentPhase) -> AssessmentPhase:
    """Get the next phase in the assessment flow."""
    phase_progression = {
        AssessmentPhase.ARCHITECTURE_MINIMUMS: AssessmentPhase.COMPONENT_ANALYSIS,
        AssessmentPhase.COMPONENT_ANALYSIS: AssessmentPhase.TECH_DEBT_ANALYSIS,
        AssessmentPhase.TECH_DEBT_ANALYSIS: AssessmentPhase.SIX_R_DECISION,
        AssessmentPhase.SIX_R_DECISION: AssessmentPhase.FINALIZATION,
        AssessmentPhase.FINALIZATION: None,
    }

    return phase_progression.get(current_phase)
