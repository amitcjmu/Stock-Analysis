"""
Decommission flow management endpoints.

Handles initialization, status, resume, pause, and cancellation operations.
Uses MFO integration layer per ADR-006 (Master Flow Orchestrator pattern).

Reference pattern: backend/app/api/v1/endpoints/assessment_flow/flow_management.py
Per ADR-027: Phase names match FlowTypeConfig exactly
"""

import logging
from typing import Optional
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
from app.schemas.decommission_flow import (
    DecommissionFlowCreateRequest,
    DecommissionFlowResponse,
    DecommissionFlowStatusResponse,
    ResumeFlowRequest,
    UpdatePhaseRequest,
)

# Import MFO integration functions (per ADR-006)
from .mfo_integration import (
    create_decommission_via_mfo,
    get_decommission_status_via_mfo,
    pause_decommission_flow,
    resume_decommission_flow,
    cancel_decommission_flow,
    update_decommission_phase_via_mfo,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/initialize", response_model=DecommissionFlowResponse)
async def initialize_decommission_flow(
    request: DecommissionFlowCreateRequest,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    client_account_id: str = Depends(verify_client_access),
    engagement_id: str = Header(..., alias="X-Engagement-ID"),
):
    """
    Initialize new decommission flow for selected systems.

    Eligible systems:
    - Pre-migration: 6R strategy = "Retire"
    - Post-migration: Successfully migrated assets past grace period

    - **selected_system_ids**: List of asset UUIDs to decommission (1-100 systems)
    - **flow_name**: Optional descriptive name for the flow
    - **decommission_strategy**: Strategy configuration (priority, execution_mode, rollback_enabled)
    - Returns flow_id and initial status
    - Starts background decommission planning process
    """
    try:
        logger.info(
            safe_log_format(
                "Initializing decommission flow for {system_count} systems",
                system_count=len(request.selected_system_ids),
            )
        )

        # Verify user has access to engagement
        await verify_engagement_access(db, engagement_id, client_account_id)

        # Convert string UUIDs to UUID objects for MFO
        system_ids_uuid = [UUID(sid) for sid in request.selected_system_ids]

        # Create decommission flow via MFO (ADR-006: Two-table pattern)
        result = await create_decommission_via_mfo(
            client_account_id=UUID(client_account_id),
            engagement_id=UUID(engagement_id),
            system_ids=system_ids_uuid,
            user_id=str(current_user.id),  # Convert UUID to str for user_id column
            flow_name=request.flow_name,
            decommission_strategy=request.decommission_strategy,
            db=db,
        )

        flow_id = result["flow_id"]

        # Start flow execution in background
        # TODO: Implement execute_decommission_planning_phase in Issue #936
        # background_tasks.add_task(
        #     execute_decommission_planning_phase,
        #     flow_id,
        #     client_account_id,
        #     engagement_id,
        #     current_user.id,
        # )

        logger.info(
            safe_log_format(
                "Decommission flow {flow_id} initialized successfully",
                flow_id=flow_id,
            )
        )

        return DecommissionFlowResponse(
            flow_id=flow_id,
            status=result["status"],
            current_phase=result["current_phase"],
            next_phase="data_migration",  # Per ADR-027 FlowTypeConfig
            selected_systems=result["selected_systems"],
            message=result["message"],
        )

    except ValueError as e:
        logger.warning(
            safe_log_format(
                "Decommission flow initialization validation error: {str_e}",
                str_e=str(e),
            )
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(
            safe_log_format(
                "Decommission flow initialization failed: {str_e}", str_e=str(e)
            )
        )
        raise HTTPException(
            status_code=500, detail="Decommission flow initialization failed"
        )


@router.get("/{flow_id}/status", response_model=DecommissionFlowStatusResponse)
async def get_decommission_flow_status(
    flow_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    client_account_id: str = Depends(verify_client_access),
    engagement_id: Optional[str] = Header(None, alias="X-Engagement-ID"),
):
    """
    Get current status and progress of decommission flow via MFO.

    - **flow_id**: Decommission flow identifier
    - Returns detailed status including phase data and progress
    - Uses MFO integration (ADR-006) for unified state view
    - Per ADR-012: Returns child flow operational status
    """
    try:
        # Fixed per CodeRabbit: Verify engagement authorization before MFO operation
        if engagement_id:
            await verify_engagement_access(db, engagement_id, client_account_id)

        # Get unified status via MFO (queries child flow operational state)
        status = await get_decommission_status_via_mfo(
            flow_id=UUID(flow_id),
            db=db,
            client_account_id=UUID(client_account_id),
            engagement_id=UUID(engagement_id) if engagement_id else None,
        )

        return DecommissionFlowStatusResponse(**status)

    except ValueError:
        logger.warning(
            safe_log_format(
                "Decommission flow not found: flow_id={flow_id}", flow_id=flow_id
            )
        )
        raise HTTPException(status_code=404, detail="Decommission flow not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "Failed to get decommission flow status: {str_e}", str_e=str(e)
            )
        )
        raise HTTPException(status_code=500, detail="Failed to get flow status")


@router.post("/{flow_id}/resume", response_model=DecommissionFlowResponse)
async def resume_decommission_flow_endpoint(
    flow_id: str,
    request: ResumeFlowRequest,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    client_account_id: str = Depends(verify_client_access),
    engagement_id: Optional[str] = Header(None, alias="X-Engagement-ID"),
):
    """
    Resume paused decommission flow from specific phase via MFO.

    - **flow_id**: Decommission flow identifier
    - **phase**: Optional phase to resume from (continues from current if not specified)
    - **user_input**: Optional user input data for resuming execution
    - Restarts flow processing
    - Uses MFO integration (ADR-006) for atomic state updates
    """
    try:
        # Fixed per CodeRabbit: Verify engagement authorization before MFO operation
        if engagement_id:
            await verify_engagement_access(db, engagement_id, client_account_id)

        # Get current flow state to validate
        current_status = await get_decommission_status_via_mfo(
            flow_id=UUID(flow_id),
            db=db,
            client_account_id=UUID(client_account_id),
            engagement_id=UUID(engagement_id) if engagement_id else None,
        )

        if current_status["status"] == "completed":
            raise HTTPException(
                status_code=400, detail="Decommission flow already completed"
            )

        # Resume via MFO (updates both master and child tables atomically)
        # Fixed per CodeRabbit: Pass through user_input
        result = await resume_decommission_flow(
            UUID(flow_id),
            UUID(client_account_id),
            UUID(engagement_id) if engagement_id else None,
            request.phase,
            request.user_input,  # Pass through user input from request
            db,
        )

        resume_phase = result["current_phase"]

        # Start flow processing in background
        # TODO: Implement continue_decommission_flow in Issue #936
        # background_tasks.add_task(
        #     continue_decommission_flow,
        #     flow_id,
        #     client_account_id,
        #     engagement_id,
        #     resume_phase,
        #     current_user.id,
        # )

        logger.info(
            safe_log_format(
                "Decommission flow {flow_id} resumed from phase {phase}",
                flow_id=flow_id,
                phase=resume_phase,
            )
        )

        # Determine next phase
        next_phase = _get_next_phase(resume_phase)

        return DecommissionFlowResponse(
            flow_id=flow_id,
            status=result["status"],
            current_phase=resume_phase,
            next_phase=next_phase,
            selected_systems=result["selected_systems"],
            message=f"Decommission flow resumed from {resume_phase}",
        )

    except ValueError:
        logger.warning(
            safe_log_format(
                "Decommission flow not found: flow_id={flow_id}", flow_id=flow_id
            )
        )
        raise HTTPException(status_code=404, detail="Decommission flow not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format("Failed to resume decommission flow: {str_e}", str_e=str(e))
        )
        raise HTTPException(status_code=500, detail="Failed to resume flow")


@router.post(
    "/{flow_id}/phases/{phase_name}", response_model=DecommissionFlowStatusResponse
)
async def update_phase_status_endpoint(
    flow_id: str,
    phase_name: str,
    request: UpdatePhaseRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    client_account_id: str = Depends(verify_client_access),
    engagement_id: Optional[str] = Header(None, alias="X-Engagement-ID"),
):
    """
    Update decommission phase status via MFO.

    - **flow_id**: Decommission flow identifier
    - **phase_name**: Phase to update (decommission_planning, data_migration, system_shutdown)
    - **phase_status**: New status (pending/running/completed/failed)
    - Uses MFO integration (ADR-006) for atomic state updates
    """
    try:
        # Fixed per CodeRabbit: Verify engagement authorization before MFO operation
        if engagement_id:
            await verify_engagement_access(db, engagement_id, client_account_id)

        # Update phase via MFO (updates both master and child tables atomically)
        result = await update_decommission_phase_via_mfo(
            flow_id=UUID(flow_id),
            phase_name=phase_name,
            phase_status=request.phase_status,
            phase_data=request.phase_data,
            db=db,
        )

        logger.info(
            safe_log_format(
                "Updated decommission phase: flow_id={flow_id}, phase={phase}, status={status}",
                flow_id=flow_id,
                phase=phase_name,
                status=request.phase_status,
            )
        )

        # Return the updated flow status
        return DecommissionFlowStatusResponse(**result)

    except ValueError as e:
        logger.warning(
            safe_log_format(
                "Invalid phase update request: flow_id={flow_id}, error={str_e}",
                flow_id=flow_id,
                str_e=str(e),
            )
        )
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "Failed to update decommission phase: {str_e}", str_e=str(e)
            )
        )
        raise HTTPException(status_code=500, detail="Failed to update phase status")


@router.post("/{flow_id}/pause")
async def pause_decommission_flow_endpoint(
    flow_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    client_account_id: str = Depends(verify_client_access),
    engagement_id: Optional[str] = Header(None, alias="X-Engagement-ID"),
):
    """
    Pause running decommission flow via MFO.

    - **flow_id**: Decommission flow identifier
    - Pauses flow execution (can be resumed later)
    - Uses MFO integration (ADR-006) for atomic state updates
    """
    try:
        # Fixed per CodeRabbit: Verify engagement authorization before MFO operation
        if engagement_id:
            await verify_engagement_access(db, engagement_id, client_account_id)

        # Pause via MFO (updates both master and child tables atomically)
        result = await pause_decommission_flow(
            UUID(flow_id),
            UUID(client_account_id),
            UUID(engagement_id) if engagement_id else None,
            db,
        )

        logger.info(
            safe_log_format(
                "Decommission flow {flow_id} paused at phase {phase}",
                flow_id=flow_id,
                phase=result["current_phase"],
            )
        )

        return {
            "flow_id": flow_id,
            "status": result["status"],
            "current_phase": result["current_phase"],
            "message": f"Decommission flow paused at {result['current_phase']}",
        }

    except ValueError:
        logger.warning(
            safe_log_format(
                "Decommission flow not found: flow_id={flow_id}", flow_id=flow_id
            )
        )
        raise HTTPException(status_code=404, detail="Decommission flow not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format("Failed to pause decommission flow: {str_e}", str_e=str(e))
        )
        raise HTTPException(status_code=500, detail="Failed to pause flow")


@router.post("/{flow_id}/cancel")
async def cancel_decommission_flow_endpoint(
    flow_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    client_account_id: str = Depends(verify_client_access),
    engagement_id: Optional[str] = Header(None, alias="X-Engagement-ID"),
):
    """
    Cancel decommission flow via MFO.

    - **flow_id**: Decommission flow identifier
    - Cancels flow execution (marks as failed/deleted)
    - Uses MFO integration (ADR-006) for atomic state updates
    """
    try:
        # Fixed per CodeRabbit: Verify engagement authorization before MFO operation
        if engagement_id:
            await verify_engagement_access(db, engagement_id, client_account_id)

        # Cancel via MFO (updates both master and child tables atomically)
        result = await cancel_decommission_flow(
            UUID(flow_id),
            UUID(client_account_id),
            UUID(engagement_id) if engagement_id else None,
            db,
        )

        logger.info(
            safe_log_format(
                "Decommission flow {flow_id} cancelled",
                flow_id=flow_id,
            )
        )

        return {
            "flow_id": flow_id,
            "status": result["status"],
            "message": "Decommission flow cancelled successfully",
        }

    except ValueError:
        logger.warning(
            safe_log_format(
                "Decommission flow not found: flow_id={flow_id}", flow_id=flow_id
            )
        )
        raise HTTPException(status_code=404, detail="Decommission flow not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format("Failed to cancel decommission flow: {str_e}", str_e=str(e))
        )
        raise HTTPException(status_code=500, detail="Failed to cancel flow")


def _get_next_phase(current_phase: str) -> str | None:
    """
    Get the next phase in the decommission flow (ADR-027 canonical phases).

    Per FlowTypeConfig:
    - decommission_planning -> data_migration
    - data_migration -> system_shutdown
    - system_shutdown -> None (completed)
    """
    phase_progression = {
        "decommission_planning": "data_migration",
        "data_migration": "system_shutdown",
        "system_shutdown": None,  # Final phase
    }

    return phase_progression.get(current_phase)
