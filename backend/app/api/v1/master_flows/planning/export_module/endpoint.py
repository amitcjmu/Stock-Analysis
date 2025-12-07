"""
Planning flow export endpoint (Issue #714).

Exports planning data in various formats (PDF, Excel, JSON).
"""

import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context_dependency
from app.core.database import get_db
from app.repositories.planning_flow_repository import PlanningFlowRepository
from app.utils.json_sanitization import sanitize_for_json

from .excel_generator import generate_excel_report
from .pdf_generator import generate_pdf_report

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
        # Parse planning flow ID and convert tenant IDs to UUIDs (per migration 115)
        try:
            planning_flow_uuid = UUID(planning_flow_id)
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

        # Get complete planning flow data
        planning_flow = await repo.get_planning_flow_by_id(
            planning_flow_id=planning_flow_uuid,
            client_account_id=client_account_uuid,
            engagement_id=engagement_uuid,
        )

        if not planning_flow:
            raise HTTPException(
                status_code=404,
                detail=f"Planning flow {planning_flow_id} not found or access denied",
            )

        # Handle different export formats
        if format == "json":
            return _handle_json_export(
                planning_flow, planning_flow_id, client_account_id, engagement_id
            )
        elif format == "pdf":
            return _handle_pdf_export(
                planning_flow, planning_flow_id, client_account_id, engagement_id
            )
        elif format == "excel":
            return _handle_excel_export(
                planning_flow, planning_flow_id, client_account_id, engagement_id
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export planning data: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to export planning data: {str(e)}",
        )


def _handle_json_export(
    planning_flow, planning_flow_id, client_account_id, engagement_id
):
    """Handle JSON export format."""
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


def _handle_pdf_export(
    planning_flow, planning_flow_id, client_account_id, engagement_id
):
    """Handle PDF export format."""
    try:
        pdf_buffer = generate_pdf_report(
            planning_flow,
            {
                "client_account_id": client_account_id,
                "engagement_id": engagement_id,
            },
        )
        filename = f"planning_report_{planning_flow_id[:8]}.pdf"
        logger.info(
            f"Exported planning flow {planning_flow_id} as PDF "
            f"(client: {client_account_id}, engagement: {engagement_id})"
        )
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except ImportError as e:
        logger.error(f"PDF generation library not available: {e}")
        raise HTTPException(
            status_code=501,
            detail="PDF export requires reportlab library. Please contact admin.",
        )


def _handle_excel_export(
    planning_flow, planning_flow_id, client_account_id, engagement_id
):
    """Handle Excel export format."""
    try:
        excel_buffer = generate_excel_report(
            planning_flow,
            {
                "client_account_id": client_account_id,
                "engagement_id": engagement_id,
            },
        )
        filename = f"planning_report_{planning_flow_id[:8]}.xlsx"
        logger.info(
            f"Exported planning flow {planning_flow_id} as Excel "
            f"(client: {client_account_id}, engagement: {engagement_id})"
        )
        return StreamingResponse(
            excel_buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except ImportError as e:
        logger.error(f"Excel generation library not available: {e}")
        raise HTTPException(
            status_code=501,
            detail="Excel export requires openpyxl library. Please contact admin.",
        )
