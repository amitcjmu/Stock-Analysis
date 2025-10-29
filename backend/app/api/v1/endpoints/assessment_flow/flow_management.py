"""
Assessment flow management endpoints.
Handles initialization, status, resume, and navigation operations.
Uses MFO integration layer per ADR-006 (Master Flow Orchestrator pattern).
"""

import logging
from datetime import datetime
from typing import List
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
from app.models.assessment_flow import AssessmentFlowStatus, AssessmentPhase
from app.repositories.assessment_flow_repository import AssessmentFlowRepository
from app.schemas.assessment_flow import (
    AssessmentApplicationInfo,
    AssessmentFlowCreateRequest,
    AssessmentFlowResponse,
    AssessmentFlowStatusResponse,
    ResumeFlowRequest,
)

# Import MFO integration functions (per ADR-006)
from .mfo_integration import (
    create_assessment_via_mfo,
    get_assessment_status_via_mfo,
    resume_assessment_flow as resume_via_mfo,
    update_assessment_via_mfo,
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

        # Convert string UUIDs to UUID objects for MFO
        application_ids_uuid = [
            UUID(app_id) for app_id in request.selected_application_ids
        ]

        # Create assessment flow via MFO (ADR-006: Two-table pattern)
        result = await create_assessment_via_mfo(
            client_account_id=UUID(client_account_id),
            engagement_id=UUID(engagement_id),
            application_ids=application_ids_uuid,
            user_id=current_user.id,
            flow_name=request.flow_name if hasattr(request, "flow_name") else None,
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
            next_phase=AssessmentPhase.ARCHITECTURE_MINIMUMS,
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


@router.get("/{flow_id}/status", response_model=AssessmentFlowStatusResponse)
async def get_assessment_flow_status(
    flow_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    client_account_id: str = Depends(verify_client_access),
):
    """
    Get current status and progress of assessment flow via MFO.

    - **flow_id**: Assessment flow identifier
    - Returns detailed status including phase data and progress
    - Uses MFO integration (ADR-006) for unified state view
    """
    try:
        # Get unified status via MFO (queries both master and child tables)
        mfo_state = await get_assessment_status_via_mfo(UUID(flow_id), db)

        # For backward compatibility, also get child flow data for phase_data
        repository = AssessmentFlowRepository(db, client_account_id)
        flow_state = await repository.get_assessment_flow_state(flow_id)

        # Calculate progress based on completed phases
        progress_percentage = mfo_state.get("progress", 0)

        return AssessmentFlowStatusResponse(
            flow_id=flow_id,
            status=mfo_state["status"],
            current_phase=mfo_state["current_phase"],
            progress_percentage=progress_percentage,
            phase_data=flow_state.phase_data if flow_state else {},
            created_at=mfo_state["created_at"],
            updated_at=mfo_state["updated_at"],
            selected_applications=mfo_state["selected_applications"],
            assessment_complete=(
                mfo_state["status"] == AssessmentFlowStatus.COMPLETED.value
            ),
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
            safe_log_format(
                "Failed to get assessment flow status: {str_e}", str_e=str(e)
            )
        )
        raise HTTPException(status_code=500, detail="Failed to get flow status")


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


@router.get("/{flow_id}/applications", response_model=List[AssessmentApplicationInfo])
async def get_assessment_flow_applications(
    flow_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    client_account_id: str = Depends(verify_client_access),
):
    """
    Get applications in assessment flow with their details.

    - **flow_id**: Assessment flow identifier
    - Returns list of applications with names, types, and other metadata
    """
    try:
        repository = AssessmentFlowRepository(db, client_account_id)
        flow_state = await repository.get_assessment_flow_state(flow_id)

        if not flow_state:
            raise HTTPException(status_code=404, detail="Assessment flow not found")

        if not flow_state.selected_application_ids:
            return []

        # Get application details using Discovery Integration
        applications = []
        if DISCOVERY_INTEGRATION_AVAILABLE:
            discovery_integration = DiscoveryFlowIntegration()

            for app_id in flow_state.selected_application_ids:
                try:
                    # Get application metadata from discovery
                    metadata = await discovery_integration.get_application_metadata(
                        db, str(app_id), client_account_id
                    )

                    # Extract basic info for the response
                    basic_info = metadata.get("basic_info", {})
                    technical_info = metadata.get("technical_info", {})
                    assessment_readiness = metadata.get("assessment_readiness", {})
                    discovery_info = metadata.get("discovery_info", {})

                    app_info = AssessmentApplicationInfo(
                        id=basic_info.get("id", str(app_id)),
                        name=basic_info.get("name", f"Application {app_id}"),
                        type=basic_info.get("type"),
                        environment=basic_info.get("environment"),
                        business_criticality=basic_info.get("business_criticality"),
                        technology_stack=technical_info.get("technology_stack", []),
                        complexity_score=metadata.get("performance_metrics", {}).get(
                            "complexity_score"
                        ),
                        readiness_score=assessment_readiness.get("score"),
                        discovery_completed_at=discovery_info.get("completed_at"),
                    )
                    applications.append(app_info)

                except Exception as e:
                    logger.warning(
                        safe_log_format(
                            "Failed to get metadata for application {app_id}: {str_e}",
                            app_id=str(app_id),
                            str_e=str(e),
                        )
                    )
                    # Add fallback entry with just ID and name
                    applications.append(
                        AssessmentApplicationInfo(
                            id=str(app_id),
                            name=f"Application {app_id}",
                        )
                    )
        else:
            # Fallback when Discovery Integration is not available
            for app_id in flow_state.selected_application_ids:
                applications.append(
                    AssessmentApplicationInfo(
                        id=str(app_id),
                        name=f"Application {app_id}",
                    )
                )

        return applications

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "Failed to get assessment flow applications: {str_e}", str_e=str(e)
            )
        )
        raise HTTPException(status_code=500, detail="Failed to get applications")


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
        # Check if flow is completed
        if (
            hasattr(flow_state, "status")
            and flow_state.status == AssessmentFlowStatus.COMPLETED
        ):
            return 100

        # Calculate 1-based progress
        current_index = phase_order.index(flow_state.current_phase)
        return int(((current_index + 1) / len(phase_order)) * 100)
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
