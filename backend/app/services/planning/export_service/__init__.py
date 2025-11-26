"""
Planning Export Service - Multi-Format Export Generation

Generates PDF, Excel, and JSON exports of planning flow data for stakeholder review
and documentation purposes.

Architecture:
- Layer 2 (Service Layer): Export orchestration and format-specific generation
- Uses PlanningFlow model data for comprehensive export content
- Supports JSON, PDF (reportlab), and Excel (openpyxl) formats

Related Issues:
- #1152 (Backend Export Service Implementation)

ADRs:
- ADR-012: Flow Status Management Separation (Two-Table Pattern)
"""

import logging
from typing import Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.exceptions import ValidationError, FlowError
from .json_export import JSONExportService
from .pdf_export import PDFExportService
from .excel_export import ExcelExportService

logger = logging.getLogger(__name__)


class PlanningExportService:
    """
    Service for exporting planning flow data in multiple formats.

    Generates comprehensive exports containing:
    - Wave plan data
    - Resource allocations
    - Timeline/Gantt chart data
    - Cost estimations
    - Executive summary

    Formats supported: JSON, PDF, Excel
    """

    def __init__(self, db: AsyncSession, context: RequestContext):
        """
        Initialize export service with database session and request context.

        Args:
            db: Async SQLAlchemy database session
            context: Request context with tenant scoping
        """
        self.db = db
        self.context = context

        # Initialize format-specific export services
        self.json_service = JSONExportService(db, context)
        self.pdf_service = PDFExportService(db, context)
        self.excel_service = ExcelExportService(db, context)

        logger.info(
            f"PlanningExportService initialized - Client: {context.client_account_id}, "
            f"Engagement: {context.engagement_id}"
        )

    async def export(
        self, planning_flow_id: UUID, export_format: str
    ) -> Tuple[bytes, str, str]:
        """
        Export planning flow data in specified format.

        Args:
            planning_flow_id: UUID of planning flow to export
            export_format: Export format ('json', 'pdf', 'excel')

        Returns:
            Tuple of (content_bytes, content_type, filename)

        Raises:
            ValidationError: If planning flow not found or export format invalid
            FlowError: If export generation fails
        """
        try:
            logger.info(
                f"🔄 Exporting planning flow {planning_flow_id} as {export_format}"
            )

            # Validate export format
            if export_format not in ["json", "pdf", "excel"]:
                raise ValidationError(
                    f"Invalid export format: {export_format}. Must be one of: json, pdf, excel",
                    field="format",
                    value=export_format,
                )

            # Get comprehensive planning data (using base service method)
            # We can use any of the format-specific services as they all inherit from BaseExportService
            planning_data = await self.json_service.get_full_planning_data(
                planning_flow_id
            )

            # Route to format-specific export method
            if export_format == "json":
                return self.json_service.export_json(planning_data, planning_flow_id)
            elif export_format == "pdf":
                return self.pdf_service.export_pdf(planning_data, planning_flow_id)
            elif export_format == "excel":
                return self.excel_service.export_excel(planning_data, planning_flow_id)

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"❌ Export generation failed: {e}", exc_info=True)
            raise FlowError(
                f"Export generation failed: {str(e)}",
                flow_name="planning",
                flow_id=str(planning_flow_id),
            )


# Export public API for backward compatibility
__all__ = ["PlanningExportService"]
