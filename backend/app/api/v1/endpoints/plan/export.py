"""
Export endpoints for planning flow data.
"""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import get_current_context
from app.core.database import get_db

router = APIRouter()


@router.get("/export/{planning_flow_id}")
async def export_planning_data(
    planning_flow_id: str,
    format: Literal["json", "pdf", "excel"] = "json",
    db: AsyncSession = Depends(get_db),
    context=Depends(get_current_context),
) -> Response:
    """
    Export planning flow data in specified format (JSON, PDF, Excel).

    Generates comprehensive export containing:
    - Wave plan data
    - Resource allocations
    - Timeline/Gantt chart data
    - Cost estimations
    - Executive summary

    Args:
        planning_flow_id: Planning flow UUID to export
        format: Export format ('json', 'pdf', 'excel') - default 'json'
        db: Database session (injected)
        context: Request context with tenant scoping (injected)

    Returns:
        Response with exported file content

    Raises:
        HTTPException 404: If planning flow not found
        HTTPException 400: If export format invalid
        HTTPException 500: If export generation fails

    Example:
        GET /api/v1/plan/export/{planning_flow_id}?format=pdf
    """
    from uuid import UUID
    from app.services.planning.export_service import PlanningExportService
    from app.core.exceptions import ValidationError, FlowError

    try:
        # Parse planning flow ID
        try:
            flow_uuid = UUID(planning_flow_id)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid planning flow ID format: {planning_flow_id}",
            )

        # Initialize export service with tenant context
        export_service = PlanningExportService(db, context)

        # Generate export
        content_bytes, content_type, filename = await export_service.export(
            planning_flow_id=flow_uuid, export_format=format
        )

        # Return file response with appropriate headers
        return Response(
            content=content_bytes,
            media_type=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(len(content_bytes)),
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
            },
        )

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")
    except FlowError as e:
        # Flow not found
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=404, detail=f"Planning flow not found: {planning_flow_id}"
            )
        # Other flow errors
        raise HTTPException(
            status_code=500, detail=f"Export generation failed: {str(e)}"
        )
    except Exception as e:
        # Unexpected errors
        raise HTTPException(
            status_code=500, detail=f"Internal server error during export: {str(e)}"
        )
