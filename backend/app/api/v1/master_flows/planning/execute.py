"""
Planning flow phase execution endpoint.

Executes specific planning phases (wave_planning, resource_allocation, timeline_generation, etc.)
through CrewAI agents integrated with MFO pattern.

Related ADRs:
- ADR-006: Master Flow Orchestrator
- ADR-015: Persistent Multi-Tenant Agent Architecture
- ADR-024: TenantMemoryManager (CrewAI memory DISABLED)
"""

import logging
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context_dependency
from app.core.database import get_db
from app.repositories.planning_flow_repository import PlanningFlowRepository
from app.utils.json_sanitization import sanitize_for_json

logger = logging.getLogger(__name__)

router = APIRouter()


class ExecutePhaseRequest(BaseModel):
    """Request model for phase execution."""

    planning_flow_id: str = Field(..., description="Planning flow UUID")
    phase: str = Field(
        ...,
        description=(
            "Phase to execute: wave_planning, resource_allocation, "
            "timeline_generation, cost_estimation, synthesis"
        ),
    )
    manual_override: Optional[bool] = Field(
        default=False, description="Manual override for resource allocation"
    )
    phase_input: Optional[Dict[str, Any]] = Field(
        default=None, description="Optional phase-specific input data"
    )


@router.post("/execute-phase")
async def execute_planning_phase(
    request: ExecutePhaseRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context_dependency),
) -> Dict[str, Any]:
    """
    Execute specific planning phase.

    Phases:
    - **wave_planning**: Organize apps into waves using WavePlanningSpecialist
    - **resource_allocation**: Allocate resources (AI + manual override)
    - **timeline_generation**: Create Gantt chart timeline
    - **cost_estimation**: Calculate migration costs
    - **synthesis**: Aggregate all planning results

    Request Body:
    ```json
    {
        "planning_flow_id": "uuid",
        "phase": "wave_planning",
        "manual_override": false,
        "phase_input": {"some_config": "value"}
    }
    ```

    Response:
    ```json
    {
        "phase": "wave_planning",
        "status": "completed",
        "result": {
            "waves": [...],
            "groups": [...]
        }
    }
    ```
    """
    client_account_id = context.client_account_id
    engagement_id = context.engagement_id

    if not client_account_id:
        raise HTTPException(status_code=400, detail="Client account ID required")

    if not engagement_id:
        raise HTTPException(status_code=400, detail="Engagement ID required")

    # Validate phase name
    valid_phases = [
        "wave_planning",
        "resource_allocation",
        "timeline_generation",
        "cost_estimation",
        "synthesis",
    ]
    if request.phase not in valid_phases:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid phase: {request.phase}. Must be one of {valid_phases}",
        )

    try:
        # Parse planning flow ID and convert tenant IDs to UUIDs (per migration 115)
        try:
            planning_flow_uuid = UUID(request.planning_flow_id)
            client_account_uuid = (
                UUID(client_account_id)
                if isinstance(client_account_id, str)
                else client_account_id
            )
            engagement_uuid = (
                UUID(engagement_id) if isinstance(engagement_id, str) else engagement_id
            )
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid UUID format: {str(e)}",
            )

        # Initialize repository with UUIDs
        repo = PlanningFlowRepository(
            db=db,
            client_account_id=client_account_uuid,
            engagement_id=engagement_uuid,
        )

        # Get planning flow (verify existence and tenant scoping)
        planning_flow = await repo.get_planning_flow_by_id(
            planning_flow_id=planning_flow_uuid,
            client_account_id=client_account_uuid,
            engagement_id=engagement_uuid,
        )

        if not planning_flow:
            raise HTTPException(
                status_code=404,
                detail=f"Planning flow {request.planning_flow_id} not found",
            )

        # TODO: Execute phase using PlanningFlowService
        # This requires PlanningFlowService implementation with CrewAI agent integration
        # For now, return placeholder response with structured error

        logger.info(
            f"Phase execution requested: {request.phase} for flow {request.planning_flow_id} "
            f"(client: {client_account_uuid}, engagement: {engagement_uuid})"
        )

        # Return structured response indicating service not yet implemented
        return sanitize_for_json(
            {
                "phase": request.phase,
                "status": "pending",
                "error_code": "PHASE_EXECUTION_NOT_IMPLEMENTED",
                "details": {
                    "planning_flow_id": request.planning_flow_id,
                    "phase": request.phase,
                    "message": "Phase execution service integration pending (requires PlanningFlowService with CrewAI)",
                    "current_phase": planning_flow.current_phase,
                    "phase_status": planning_flow.phase_status,
                },
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to execute phase {request.phase}: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute phase: {str(e)}",
        )
