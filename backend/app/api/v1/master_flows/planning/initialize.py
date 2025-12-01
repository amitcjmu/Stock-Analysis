"""
Planning flow initialization endpoint.

Initializes planning flow from assessment results following MFO pattern.
Creates master flow in crewai_flow_state_extensions and child flow in planning_flows.

Related ADRs:
- ADR-006: Master Flow Orchestrator
- ADR-012: Two-Table Pattern (master + child flows)
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

import asyncio

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context_dependency
from app.core.database import get_db
from app.repositories.planning_flow_repository import PlanningFlowRepository
from app.repositories.crewai_flow_state_extensions_repository import (
    CrewAIFlowStateExtensionsRepository,
)
from app.utils.json_sanitization import sanitize_for_json

logger = logging.getLogger(__name__)

router = APIRouter()


class InitializePlanningRequest(BaseModel):
    """Request model for planning flow initialization.

    Note: engagement_id comes from RequestContext (X-Engagement-ID header), not request body.
    This ensures proper UUID handling and multi-tenant isolation.
    """

    selected_application_ids: List[str] = Field(
        ..., description="Asset UUIDs from assessment flow"
    )
    planning_config: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Planning configuration (max_apps_per_wave, wave_duration_limit_days, etc.)",
    )


@router.post("/initialize")
async def initialize_planning_flow(
    request: InitializePlanningRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context_dependency),
) -> Dict[str, Any]:
    """
    Initialize planning flow from assessment results.

    Creates master flow and child planning flow in atomic transaction.
    Follows MFO pattern with two-table architecture (ADR-012).

    Headers (REQUIRED):
    - X-Client-Account-ID: Client UUID (e.g., 11111111-1111-1111-1111-111111111111)
    - X-Engagement-ID: Engagement UUID (e.g., 22222222-2222-2222-2222-222222222222)

    Request Body:
    ```json
    {
        "selected_application_ids": ["uuid1", "uuid2"],
        "planning_config": {
            "max_apps_per_wave": 50,
            "wave_duration_limit_days": 90
        }
    }
    ```

    Response:
    ```json
    {
        "master_flow_id": "uuid",
        "planning_flow_id": "uuid",
        "current_phase": "wave_planning",
        "phase_status": "initialized",
        "status": "initialized"
    }
    ```
    """
    client_account_id = context.client_account_id
    engagement_id = context.engagement_id  # From X-Engagement-ID header

    if not client_account_id:
        raise HTTPException(status_code=400, detail="Client account ID required")

    if not engagement_id:
        raise HTTPException(status_code=400, detail="Engagement ID required")

    try:
        # Convert context IDs (UUID strings from headers) to UUID objects
        # Per migration 115: All tenant IDs must be valid UUIDs
        # Demo UUIDs: 11111111-1111-1111-1111-111111111111 (client), 22222222-2222-2222-2222-222222222222 (engagement)
        try:
            client_account_uuid = (
                UUID(client_account_id)
                if isinstance(client_account_id, str)
                else client_account_id
            )
            engagement_uuid = UUID(str(engagement_id)) if engagement_id else None

            if not engagement_uuid:
                raise ValueError("Engagement ID is required")
        except (ValueError, TypeError) as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid client_account_id or engagement_id format: {str(e)}",
            )

        # Generate UUIDs for master and child flows
        master_flow_id = uuid4()
        planning_flow_id = uuid4()

        # Convert application IDs to UUIDs
        try:
            selected_app_uuids = [
                UUID(app_id) for app_id in request.selected_application_ids
            ]
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid application UUID format: {str(e)}",
            )

        # Initialize repositories with tenant scoping
        # MasterFlowRepo expects string UUIDs, PlanningRepo expects UUID objects
        master_flow_repo = CrewAIFlowStateExtensionsRepository(
            db=db,
            client_account_id=str(client_account_uuid),
            engagement_id=str(engagement_uuid),
        )

        planning_repo = PlanningFlowRepository(
            db=db,
            client_account_id=client_account_uuid,
            engagement_id=engagement_uuid,
        )

        # Create master flow in crewai_flow_state_extensions (MFO pattern)
        await master_flow_repo.create_master_flow(
            flow_id=str(master_flow_id),
            flow_type="planning",
            flow_name=f"Planning Flow {engagement_uuid}",
            flow_configuration=request.planning_config or {},
            initial_state={"phase": "wave_planning", "status": "pending"},
            auto_commit=False,  # Will commit after child flow creation
        )

        # Create child planning flow
        planning_flow = await planning_repo.create_planning_flow(
            client_account_id=client_account_uuid,
            engagement_id=engagement_uuid,
            master_flow_id=master_flow_id,
            planning_flow_id=planning_flow_id,
            current_phase="wave_planning",  # First valid phase per CHECK constraint
            phase_status="pending",  # Initial status per CHECK constraint
            planning_config=request.planning_config or {},
            selected_applications=selected_app_uuids,
        )

        await db.commit()

        logger.info(
            f"Initialized planning flow: {planning_flow_id} "
            f"(master: {master_flow_id}, client: {client_account_uuid}, "
            f"engagement: {engagement_uuid})"
        )

        # Schedule wave planning to run in background (async)
        # This prevents frontend timeout - wave planning can take 2+ minutes for large app lists
        # Frontend should poll GET /status/{planning_flow_id} for completion
        async def run_wave_planning_background():
            """Background task to execute wave planning asynchronously."""
            from app.core.database import AsyncSessionLocal
            from app.services.planning import execute_wave_planning_for_flow

            bg_db = None
            try:
                # Create new session for background task
                bg_db = AsyncSessionLocal()
                logger.info(
                    f"[Background] Starting wave planning for flow: {planning_flow_id}"
                )
                result = await execute_wave_planning_for_flow(
                    db=bg_db,
                    context=context,
                    planning_flow_id=planning_flow_id,
                    planning_config=request.planning_config or {},
                )
                if result.get("status") == "success":
                    logger.info(
                        f"[Background] Wave planning completed: {planning_flow_id}"
                    )
                else:
                    logger.warning(
                        f"[Background] Wave planning failed: {planning_flow_id} - "
                        f"{result.get('error')}"
                    )
            except Exception as e:
                logger.error(
                    f"[Background] Wave planning error for {planning_flow_id}: {e}",
                    exc_info=True,
                )
            finally:
                if bg_db:
                    await bg_db.close()

        # Launch background task (non-blocking)
        asyncio.create_task(run_wave_planning_background())
        logger.info(f"Scheduled background wave planning for flow: {planning_flow_id}")

        # Return immediately with "in_progress" status
        # Frontend should poll GET /status/{planning_flow_id} for completion
        return sanitize_for_json(
            {
                "master_flow_id": str(master_flow_id),
                "planning_flow_id": str(planning_flow.planning_flow_id),
                "current_phase": "wave_planning",
                "phase_status": "in_progress",
                "status": "in_progress",
                "message": (
                    "Planning flow initialized. Wave planning in progress - "
                    "poll status endpoint for completion."
                ),
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to initialize planning flow: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize planning flow: {str(e)}",
        )
