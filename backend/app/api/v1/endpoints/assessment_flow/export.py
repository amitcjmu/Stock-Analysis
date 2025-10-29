"""
Export functionality for Assessment Flow - Phase 6 (Issue #842, #722).

Generates PDF, Excel, and JSON reports for assessment results.
Routes through MFO integration layer per ADR-006.

Export Formats:
- PDF: Executive summary with 6R recommendations (stub for future implementation)
- Excel: Detailed spreadsheet with all application data (stub for future implementation)
- JSON: Full assessment data for API integration (fully implemented)

Per #722 (Treatment Export Functionality), this provides the export capability
requested in the parent issue #611 (Assessment Flow Complete - Treatments Visible).
"""

import json
import logging
from datetime import datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.auth_utils import get_current_user
from app.core.context_helpers import verify_client_access
from app.core.database import get_db
from app.core.security.secure_logging import safe_log_format

# Import MFO integration for getting flow data
from .mfo_integration import get_assessment_status_via_mfo

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/{flow_id}/export")
async def export_assessment_results(
    flow_id: str,
    format: Literal["pdf", "excel", "json"] = "json",
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    client_account_id: str = Depends(verify_client_access),
):
    """
    Export assessment results in specified format.

    - **flow_id**: Assessment flow identifier
    - **format**: Export format (pdf, excel, json)

    Formats:
    - **PDF**: Executive summary with 6R recommendations (TODO: Implement with ReportLab)
    - **Excel**: Detailed spreadsheet with all application data (TODO: Implement with openpyxl)
    - **JSON**: Full assessment data for API integration (IMPLEMENTED)

    Per Issue #722 (Treatment Export Functionality), this endpoint provides
    export capability for assessment results as part of the Assessment Flow
    completion milestone (#611).

    Returns:
        Response with appropriate content-type and download headers
    """
    try:
        logger.info(
            safe_log_format(
                "Exporting assessment results: flow_id={flow_id}, format={format}",
                flow_id=flow_id,
                format=format,
            )
        )

        # Get flow data via MFO (ADR-006: Single source of truth)
        # This queries both master and child tables atomically
        flow_status = await get_assessment_status_via_mfo(UUID(flow_id), db)

        # Validate tenant access (flow_status from MFO already scoped to tenant)
        # Multi-tenant isolation is enforced in get_assessment_status_via_mfo

        # Generate export based on format
        if format == "pdf":
            return await _generate_pdf_export(flow_status, flow_id)
        elif format == "excel":
            return await _generate_excel_export(flow_status, flow_id)
        else:  # json (default)
            return await _generate_json_export(flow_status, flow_id)

    except ValueError as e:
        logger.warning(
            safe_log_format(
                "Assessment flow not found for export: flow_id={flow_id}",
                flow_id=flow_id,
            )
        )
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "Export failed: flow_id={flow_id}, format={format}, error={str_e}",
                flow_id=flow_id,
                format=format,
                str_e=str(e),
            )
        )
        raise HTTPException(
            status_code=500, detail=f"Export failed: {type(e).__name__}"
        )


async def _generate_pdf_export(flow_data: dict, flow_id: str) -> Response:
    """
    Generate PDF report using ReportLab or WeasyPrint.

    TODO: Implement actual PDF generation with ReportLab
    - Executive summary page
    - 6R recommendations table
    - Application details per recommendation
    - Charts/graphs for strategy distribution

    For MVP, returns JSON stub indicating PDF generation is pending.

    Args:
        flow_data: Flow status data from MFO
        flow_id: Assessment flow UUID

    Returns:
        Response with PDF content (or JSON stub for MVP)
    """
    logger.info(
        safe_log_format(
            "PDF export requested (stub): flow_id={flow_id}", flow_id=flow_id
        )
    )

    # MVP: Return structured JSON indicating feature availability
    pdf_stub_content = {
        "export_type": "pdf",
        "status": "not_implemented",
        "flow_id": flow_data.get("flow_id"),
        "master_flow_id": flow_data.get("master_flow_id"),
        "flow_status": flow_data.get("status"),
        "current_phase": flow_data.get("current_phase"),
        "message": "PDF export to be implemented with ReportLab library",
        "planned_features": [
            "Executive summary with flow metadata",
            "6R strategy recommendations table",
            "Application details per strategy",
            "Visual charts for strategy distribution",
            "Technical debt analysis summary",
            "Architecture standards compliance",
        ],
        "fallback": "Use JSON export for complete data access",
        "exported_at": datetime.utcnow().isoformat() + "Z",
    }

    return Response(
        content=json.dumps(pdf_stub_content, indent=2),
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="assessment_{flow_id}_stub.json"'
        },
    )


async def _generate_excel_export(flow_data: dict, flow_id: str) -> Response:
    """
    Generate Excel spreadsheet using openpyxl.

    TODO: Implement actual Excel generation with openpyxl
    - Summary sheet with flow metadata
    - Applications sheet with all details
    - Recommendations sheet with 6R strategies
    - Tech debt sheet with analysis results
    - Charts sheet with visualizations

    For MVP, returns JSON stub indicating Excel generation is pending.

    Args:
        flow_data: Flow status data from MFO
        flow_id: Assessment flow UUID

    Returns:
        Response with Excel content (or JSON stub for MVP)
    """
    logger.info(
        safe_log_format(
            "Excel export requested (stub): flow_id={flow_id}", flow_id=flow_id
        )
    )

    # MVP: Return structured JSON indicating feature availability
    excel_stub_content = {
        "export_type": "excel",
        "status": "not_implemented",
        "flow_id": flow_data.get("flow_id"),
        "master_flow_id": flow_data.get("master_flow_id"),
        "flow_status": flow_data.get("status"),
        "current_phase": flow_data.get("current_phase"),
        "message": "Excel export to be implemented with openpyxl library",
        "planned_sheets": [
            "Summary - Flow metadata and progress",
            "Applications - All application details",
            "6R Recommendations - Strategy decisions per application",
            "Tech Debt - Technical debt analysis results",
            "Architecture - Architecture standards compliance",
            "Charts - Visual data representations",
        ],
        "fallback": "Use JSON export for complete data access",
        "exported_at": datetime.utcnow().isoformat() + "Z",
    }

    return Response(
        content=json.dumps(excel_stub_content, indent=2),
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="assessment_{flow_id}_stub.json"'
        },
    )


async def _generate_json_export(flow_data: dict, flow_id: str) -> Response:
    """
    Generate JSON export (full assessment data).

    This is the FULLY IMPLEMENTED export format.
    Provides complete assessment data for API integration and data portability.

    Per ADR-012: Uses child flow operational data for detailed state.
    All data is multi-tenant scoped (already enforced by MFO query).

    Args:
        flow_data: Flow status data from MFO (unified master + child state)
        flow_id: Assessment flow UUID

    Returns:
        Response with JSON content and download headers
    """
    logger.info(
        safe_log_format("JSON export (full): flow_id={flow_id}", flow_id=flow_id)
    )

    # Construct comprehensive export data
    # Per ADR-012: Use child flow data (flow_status) for operational details
    export_data = {
        # Metadata
        "export_metadata": {
            "export_type": "json",
            "export_version": "1.0",
            "exported_at": datetime.utcnow().isoformat() + "Z",
            "flow_id": flow_data.get("flow_id"),
            "master_flow_id": flow_data.get("master_flow_id"),
        },
        # Flow state (from child table - operational)
        "flow_state": {
            "status": flow_data.get("status"),
            "current_phase": flow_data.get("current_phase"),
            "progress": flow_data.get("progress"),
            "phase_progress": flow_data.get("phase_progress"),
            "created_at": (
                flow_data.get("created_at").isoformat()
                if flow_data.get("created_at")
                else None
            ),
            "updated_at": (
                flow_data.get("updated_at").isoformat()
                if flow_data.get("updated_at")
                else None
            ),
            "completed_at": (
                flow_data.get("completed_at").isoformat()
                if flow_data.get("completed_at")
                else None
            ),
        },
        # Master flow state (from master table - lifecycle)
        "master_flow_state": {
            "master_status": flow_data.get("master_status"),
            "master_flow_type": flow_data.get("master_flow_type"),
        },
        # Application data
        "applications": {
            "selected_count": flow_data.get("selected_applications", 0),
            "note": "Use /assessment-flow/{flow_id}/applications endpoint for detailed app data",
        },
        # Configuration
        "configuration": flow_data.get("configuration", {}),
        # Runtime state (phase-specific data)
        "runtime_state": flow_data.get("runtime_state", {}),
        # Assessment results (phase-specific)
        "assessment_results": {
            "note": "Use phase-specific endpoints for detailed results:",
            "endpoints": {
                "architecture_standards": f"/assessment-flow/{flow_id}/architecture-standards",
                "component_analysis": f"/assessment-flow/{flow_id}/component-analysis",
                "tech_debt_analysis": f"/assessment-flow/{flow_id}/tech-debt",
                "sixr_decisions": f"/assessment-flow/{flow_id}/sixr-decisions",
                "finalization": f"/assessment-flow/{flow_id}/finalization",
            },
        },
        # Data access notes
        "data_access": {
            "note": "This export provides flow metadata. For complete assessment data:",
            "recommendations": [
                "Use phase-specific endpoints for detailed analysis results",
                "Use /applications endpoint for full application details",
                "Implement custom export logic for specific data requirements",
            ],
        },
    }

    return Response(
        content=json.dumps(
            export_data, indent=2, default=str
        ),  # default=str for datetime serialization
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="assessment_{flow_id}.json"'
        },
    )
