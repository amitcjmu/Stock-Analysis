"""
Assessment flow update endpoints.
Handles resume, phase navigation, and phase updates.
Uses MFO integration layer per ADR-006 (Master Flow Orchestrator pattern).
"""

import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.auth_utils import get_current_user
from app.core.context_helpers import verify_client_access
from app.core.security.secure_logging import safe_log_format
from app.core.database import get_db
from app.models.assessment_flow import AssessmentFlowStatus, AssessmentPhase
from app.repositories.assessment_flow_repository import AssessmentFlowRepository
from app.schemas.assessment_flow import (
    AssessmentFlowResponse,
    ResumeFlowRequest,
)

# Import MFO integration functions (per ADR-006)
from ..mfo_integration import (
    get_assessment_status_via_mfo,
    resume_assessment_flow as resume_via_mfo,
    update_assessment_via_mfo,
)

try:
    from app.api.v1.endpoints import assessment_flow_processors

    ASSESSMENT_FLOW_SERVICE_AVAILABLE = True
except ImportError:
    ASSESSMENT_FLOW_SERVICE_AVAILABLE = False

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_next_phase(current_phase: AssessmentPhase) -> AssessmentPhase:
    """Get the next phase in the assessment flow (ADR-027 canonical phases)."""
    phase_progression = {
        AssessmentPhase.INITIALIZATION: AssessmentPhase.READINESS_ASSESSMENT,
        AssessmentPhase.READINESS_ASSESSMENT: AssessmentPhase.COMPLEXITY_ANALYSIS,
        AssessmentPhase.COMPLEXITY_ANALYSIS: AssessmentPhase.DEPENDENCY_ANALYSIS,
        AssessmentPhase.DEPENDENCY_ANALYSIS: AssessmentPhase.TECH_DEBT_ASSESSMENT,
        AssessmentPhase.TECH_DEBT_ASSESSMENT: AssessmentPhase.RISK_ASSESSMENT,
        AssessmentPhase.RISK_ASSESSMENT: AssessmentPhase.RECOMMENDATION_GENERATION,
        AssessmentPhase.RECOMMENDATION_GENERATION: AssessmentPhase.FINALIZATION,
        AssessmentPhase.FINALIZATION: None,
    }

    return phase_progression.get(current_phase)


@router.post("/{flow_id}/resume", response_model=AssessmentFlowResponse)
async def resume_assessment_flow_endpoint(
    flow_id: str,
    request: ResumeFlowRequest,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    client_account_id: str = Depends(verify_client_access),
):
    """
    Resume paused assessment flow from specific phase via MFO.

    - **flow_id**: Assessment flow identifier
    - **phase**: Phase to resume from (optional, continues from current if not specified)
    - Restarts flow processing
    - Uses MFO integration (ADR-006) for atomic state updates
    """
    try:
        # Get current flow state to validate
        mfo_state = await get_assessment_status_via_mfo(UUID(flow_id), db)

        if mfo_state["status"] == AssessmentFlowStatus.COMPLETED.value:
            raise HTTPException(
                status_code=400, detail="Assessment flow already completed"
            )

        # Resume via MFO (updates both master and child tables atomically)
        result = await resume_via_mfo(UUID(flow_id), db)

        # If specific phase requested, update phase
        if request.phase:
            result = await update_assessment_via_mfo(
                flow_id=UUID(flow_id),
                updates={"current_phase": request.phase.value},
                db=db,
            )

        resume_phase = result["current_phase"]

        # FIX FOR ISSUE #999: Start flow processing in background with comprehensive logging
        logger.info(
            safe_log_format(
                "[ISSUE-999] Resume flow result: flow_id={flow_id}, "
                "phase={phase}, status={status}, service_available={svc_avail}",
                flow_id=flow_id,
                phase=resume_phase,
                status=result["status"],
                svc_avail=ASSESSMENT_FLOW_SERVICE_AVAILABLE,
            )
        )

        if ASSESSMENT_FLOW_SERVICE_AVAILABLE:
            # Skip background task for finalization phase (no agents needed)
            try:
                phase_enum = AssessmentPhase(resume_phase)
                if phase_enum == AssessmentPhase.FINALIZATION:
                    logger.info(
                        "[ISSUE-999] Skipping agent execution for finalization phase"
                    )
                else:
                    # Get engagement_id from flow state
                    # FIX FOR ISSUE #999: This endpoint needs engagement_id but doesn't have it
                    # Get it from the MFO state
                    mfo_state = await get_assessment_status_via_mfo(UUID(flow_id), db)
                    engagement_id = mfo_state.get("engagement_id")

                    # CRITICAL: Validate engagement_id before queueing background task
                    if not engagement_id:
                        logger.error(
                            f"[ISSUE-999] CRITICAL: Could not retrieve engagement_id for flow {flow_id}. "
                            f"Aborting background task to prevent multi-tenant scoping violations."
                        )
                        raise HTTPException(
                            status_code=500,
                            detail=f"Failed to retrieve engagement_id for flow {flow_id}",
                        )

                    logger.info(
                        f"[ISSUE-999] Adding background task for phase {resume_phase}, "
                        f"engagement_id={engagement_id}"
                    )
                    background_tasks.add_task(
                        assessment_flow_processors.continue_assessment_flow,
                        flow_id,
                        str(client_account_id),  # Ensure string type
                        str(engagement_id),  # Validated engagement_id from flow state
                        phase_enum,
                        str(current_user.id),  # Ensure string type
                    )
                    logger.info(
                        f"[ISSUE-999] Successfully queued background agent execution for phase {resume_phase}"
                    )
            except ValueError as e:
                logger.error(
                    f"[ISSUE-999] Invalid phase '{resume_phase}' - ValueError: {e}. "
                    f"This will prevent agent execution!"
                )
            except Exception as e:
                logger.error(
                    f"[ISSUE-999] Failed to add background task: {e}", exc_info=True
                )
        else:
            logger.error(
                "[ISSUE-999] CRITICAL: Assessment flow service NOT AVAILABLE! "
                "Background task cannot be added. Check import of assessment_flow_processors."
            )

        return AssessmentFlowResponse(
            flow_id=flow_id,
            status=result["status"],
            current_phase=resume_phase,
            next_phase=_get_next_phase(AssessmentPhase(resume_phase)),
            selected_applications=result["selected_applications"],
            message=f"Assessment flow resumed from {resume_phase}",
        )

    except ValueError:
        logger.warning(
            safe_log_format(
                "Assessment flow not found: flow_id={flow_id}", flow_id=flow_id
            )
        )
        raise HTTPException(status_code=404, detail="Assessment flow not found")
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
