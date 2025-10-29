"""
Planning flow export endpoint.

Exports planning data in various formats (PDF, Excel, JSON).
Currently supports JSON export with PDF/Excel placeholders for future implementation.

Related ADRs:
- ADR-012: Two-Table Pattern (child flow operational state)
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context_dependency
from app.core.database import get_db
from app.repositories.planning_flow_repository import PlanningFlowRepository
from app.utils.json_sanitization import sanitize_for_json

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/export/{planning_flow_id}")
async def export_planning_data(
    planning_flow_id: str,
    format: str = "json",  # "pdf", "excel", "json"
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context_dependency),
):
    """
    Export planning data (PDF, Excel, JSON).

    Currently supports JSON export. PDF and Excel exports return 501 (Not Implemented)
    but can be added in future iterations.

    Query Parameters:
    - format: Export format (json, pdf, excel). Default: json

    Response (JSON format):
    ```json
    {
        "planning_flow_id": "uuid",
        "export_format": "json",
        "data": {
            "wave_plan": {...},
            "resource_allocation": {...},
            "timeline": {...},
            "cost_estimation": {...}
        },
        "exported_at": "2025-10-29T12:00:00"
    }
    ```
    """
    client_account_id = context.client_account_id
    engagement_id = context.engagement_id

    if not client_account_id:
        raise HTTPException(status_code=400, detail="Client account ID required")

    if not engagement_id:
        raise HTTPException(status_code=400, detail="Engagement ID required")

    # Validate format
    valid_formats = ["json", "pdf", "excel"]
    if format not in valid_formats:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid format: {format}. Must be one of {valid_formats}",
        )

    try:
        # Parse planning flow ID
        try:
            planning_flow_uuid = UUID(planning_flow_id)
        except ValueError:
            raise HTTPException(
                status_code=400, detail="Invalid planning flow UUID format"
            )

        # Initialize repository
        repo = PlanningFlowRepository(
            db=db,
            client_account_id=str(client_account_id),
            engagement_id=str(engagement_id),
        )

        # Get complete planning flow data
        planning_flow = await repo.get_planning_flow_by_id(
            planning_flow_id=planning_flow_uuid,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
        )

        if not planning_flow:
            raise HTTPException(
                status_code=404,
                detail=f"Planning flow {planning_flow_id} not found or access denied",
            )

        # Handle different export formats
        if format == "json":
            # JSON export - return complete planning data
            from datetime import datetime

            export_data = {
                "planning_flow_id": str(planning_flow.planning_flow_id),
                "master_flow_id": str(planning_flow.master_flow_id),
                "export_format": "json",
                "exported_at": datetime.utcnow().isoformat(),
                "data": {
                    "current_phase": planning_flow.current_phase,
                    "phase_status": planning_flow.phase_status,
                    "planning_config": planning_flow.planning_config,
                    "wave_plan": planning_flow.wave_plan_data,
                    "resource_allocation": planning_flow.resource_allocation_data,
                    "timeline": planning_flow.timeline_data,
                    "cost_estimation": planning_flow.cost_estimation_data,
                    "agent_execution_log": planning_flow.agent_execution_log,
                },
                "metadata": {
                    "client_account_id": client_account_id,
                    "engagement_id": engagement_id,
                    "created_at": planning_flow.created_at.isoformat(),
                    "updated_at": planning_flow.updated_at.isoformat(),
                },
            }

            logger.info(
                f"Exported planning flow {planning_flow_id} as JSON "
                f"(client: {client_account_id}, engagement: {engagement_id})"
            )

            return sanitize_for_json(export_data)

        elif format == "pdf":
            # TODO: Implement PDF generation using reportlab or similar
            raise HTTPException(
                status_code=501,
                detail="PDF export not yet implemented. Use format=json for now.",
            )

        elif format == "excel":
            # TODO: Implement Excel generation using openpyxl or similar
            raise HTTPException(
                status_code=501,
                detail="Excel export not yet implemented. Use format=json for now.",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export planning data: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to export planning data: {str(e)}",
        )
