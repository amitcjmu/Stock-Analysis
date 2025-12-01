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

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context_dependency
from app.core.database import get_db
from app.repositories.crewai_flow_state_extensions_repository import (
    CrewAIFlowStateExtensionsRepository,
)
from app.repositories.planning_flow_repository import PlanningFlowRepository
from app.utils.json_sanitization import sanitize_for_json

from .shared_utils import (
    parse_tenant_uuids,
    parse_uuid,
    schedule_wave_planning_task,
)

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
    migration_start_date: Optional[str] = Field(
        default=None,
        description="Migration start date in ISO format (YYYY-MM-DD).",
    )
    planning_config: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Planning configuration (max_apps_per_wave, wave_duration_limit_days)",
    )


def _parse_application_uuids(application_ids: List[str]) -> List[UUID]:
    """Parse and validate application UUIDs."""
    return [
        parse_uuid(app_id, f"application_id[{i}]")
        for i, app_id in enumerate(application_ids)
    ]


@router.post("/initialize")
async def initialize_planning_flow(
    request: InitializePlanningRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context_dependency),
) -> Dict[str, Any]:
    """
    Initialize planning flow from assessment results.

    Creates master flow and child planning flow in atomic transaction.
    Follows MFO pattern with two-table architecture (ADR-012).

    Headers (REQUIRED):
    - X-Client-Account-ID: Client UUID
    - X-Engagement-ID: Engagement UUID

    Request Body:
    ```json
    {
        "selected_application_ids": ["uuid1", "uuid2"],
        "migration_start_date": "2025-03-01",
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
        "phase_status": "in_progress",
        "status": "in_progress"
    }
    ```
    """
    client_account_id = context.client_account_id
    engagement_id = context.engagement_id

    if not client_account_id:
        raise HTTPException(status_code=400, detail="Client account ID required")

    if not engagement_id:
        raise HTTPException(status_code=400, detail="Engagement ID required")

    try:
        # Parse and validate UUIDs using shared utility
        client_account_uuid, engagement_uuid = parse_tenant_uuids(
            client_account_id, engagement_id
        )
        selected_app_uuids = _parse_application_uuids(request.selected_application_ids)

        # Generate UUIDs for master and child flows
        master_flow_id = uuid4()
        planning_flow_id = uuid4()

        # Initialize repositories with tenant scoping
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

        # Build planning config with migration_start_date
        planning_config = request.planning_config or {}
        # Per Qodo Bot: Use `is not None` for consistent optional param checks
        if request.migration_start_date is not None:
            planning_config["migration_start_date"] = request.migration_start_date

        # Create master flow in crewai_flow_state_extensions (MFO pattern)
        await master_flow_repo.create_master_flow(
            flow_id=str(master_flow_id),
            flow_type="planning",
            flow_name=f"Planning Flow {engagement_uuid}",
            flow_configuration=planning_config,
            initial_state={"phase": "wave_planning", "status": "pending"},
            auto_commit=False,
        )

        # Create child planning flow
        planning_flow = await planning_repo.create_planning_flow(
            client_account_id=client_account_uuid,
            engagement_id=engagement_uuid,
            master_flow_id=master_flow_id,
            planning_flow_id=planning_flow_id,
            current_phase="wave_planning",
            phase_status="pending",
            planning_config=planning_config,
            selected_applications=selected_app_uuids,
        )

        await db.commit()

        logger.info(
            f"Initialized planning flow: {planning_flow_id} "
            f"(master: {master_flow_id}, client: {client_account_uuid}, "
            f"engagement: {engagement_uuid})"
        )

        # Launch background wave planning task with proper lifecycle management (Qodo Bot fix)
        schedule_wave_planning_task(
            planning_flow_id=planning_flow_id,
            context=context,
            planning_config=planning_config,
        )

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
