"""
PDF Export Module - PDF format export generation

Generates PDF executive summary reports with professional formatting.

Architecture:
- Layer 2 (Service Layer): Format-specific export generation
- Uses reportlab for PDF generation
"""

import io
import logging
from datetime import datetime
from typing import Any, Dict, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from .base import BaseExportService

logger = logging.getLogger(__name__)


class PDFExportService(BaseExportService):
    """
    Service for exporting planning data as PDF executive summary.

    Generates professional PDF with:
    - Executive summary
    - Wave summary table
    - Resource allocation summary
    - Timeline overview
    - Cost breakdown
    """

    def __init__(self, db: AsyncSession, context: RequestContext):
        """
        Initialize PDF export service.

        Args:
            db: Async SQLAlchemy database session
            context: Request context with tenant scoping
        """
        super().__init__(db, context)

    def export_pdf(
        self, planning_data: Dict[str, Any], planning_flow_id: UUID
    ) -> Tuple[bytes, str, str]:
        """
        Export planning data as PDF executive summary.

        Args:
            planning_data: Complete planning data dictionary
            planning_flow_id: Planning flow UUID for filename

        Returns:
            Tuple of (pdf_bytes, content_type, filename)
        """
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import (
                SimpleDocTemplate,
                Paragraph,
                Spacer,
                Table,
                TableStyle,
            )
            from reportlab.lib.enums import TA_CENTER

            # Create PDF buffer
            buffer = io.BytesIO()

            # Create document (A4 size)
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18,
            )

            # Container for PDF elements
            story = []
            styles = getSampleStyleSheet()

            # Custom styles
            title_style = ParagraphStyle(
                "CustomTitle",
                parent=styles["Heading1"],
                fontSize=24,
                textColor=colors.HexColor("#1a73e8"),
                spaceAfter=30,
                alignment=TA_CENTER,
            )

            heading_style = ParagraphStyle(
                "CustomHeading",
                parent=styles["Heading2"],
                fontSize=16,
                textColor=colors.HexColor("#333333"),
                spaceAfter=12,
                spaceBefore=12,
            )

            # Title
            story.append(Paragraph("Migration Planning Report", title_style))
            story.append(Spacer(1, 0.2 * inch))

            # Executive Summary
            story.append(Paragraph("Executive Summary", heading_style))

            wave_plan = planning_data.get("wave_plan", {})
            resource_allocation = planning_data.get("resource_allocation", {})
            cost_estimation = planning_data.get("cost_estimation", {})
            timeline_data = planning_data.get("timeline", {})

            total_waves = wave_plan.get("total_waves", 0)
            total_apps = len(planning_data.get("selected_applications", []))
            total_cost = cost_estimation.get("total_estimated_cost", 0.0)

            summary_text = f"""
            <para>
            <b>Total Applications:</b> {total_apps}<br/>
            <b>Total Waves:</b> {total_waves}<br/>
            <b>Total Estimated Cost:</b> ${total_cost:,.2f}<br/>
            <b>Planning Status:</b> {planning_data.get('phase_status', 'Unknown')}<br/>
            <b>Export Date:</b> {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
            </para>
            """

            story.append(Paragraph(summary_text, styles["Normal"]))
            story.append(Spacer(1, 0.3 * inch))

            # Wave Summary Table
            if wave_plan.get("waves"):
                story.append(Paragraph("Wave Summary", heading_style))

                wave_table_data = [
                    ["Wave", "Applications", "Start Date", "End Date", "Status"]
                ]

                for wave in wave_plan["waves"]:
                    wave_table_data.append(
                        [
                            wave.get(
                                "wave_name", f"Wave {wave.get('wave_number', 'N/A')}"
                            ),
                            str(len(wave.get("applications", []))),
                            wave.get("start_date", "TBD"),
                            wave.get("end_date", "TBD"),
                            wave.get("status", "Planned"),
                        ]
                    )

                wave_table = Table(
                    wave_table_data,
                    colWidths=[2 * inch, 1 * inch, 1.5 * inch, 1.5 * inch, 1 * inch],
                )
                wave_table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a73e8")),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                            ("FONTSIZE", (0, 0), (-1, 0), 12),
                            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                            ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                            ("GRID", (0, 0), (-1, -1), 1, colors.black),
                        ]
                    )
                )

                story.append(wave_table)
                story.append(Spacer(1, 0.3 * inch))

            # Resource Allocation Summary
            if resource_allocation.get("allocations"):
                story.append(Paragraph("Resource Allocation Summary", heading_style))

                resource_table_data = [["Wave", "Role", "Hours", "Cost"]]

                for alloc in resource_allocation["allocations"][
                    :10
                ]:  # Limit to 10 rows
                    wave_num = alloc.get("wave_number", "N/A")
                    for resource in alloc.get("resources", [])[
                        :3
                    ]:  # Top 3 resources per wave
                        resource_table_data.append(
                            [
                                f"Wave {wave_num}",
                                resource.get("role_name", "Unknown"),
                                str(resource.get("allocated_hours", 0)),
                                f"${resource.get('estimated_cost', 0):,.2f}",
                            ]
                        )

                resource_table = Table(
                    resource_table_data,
                    colWidths=[1.5 * inch, 2 * inch, 1 * inch, 1.5 * inch],
                )
                resource_table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#34a853")),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                            ("FONTSIZE", (0, 0), (-1, 0), 12),
                            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                            ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                            ("GRID", (0, 0), (-1, -1), 1, colors.black),
                        ]
                    )
                )

                story.append(resource_table)
                story.append(Spacer(1, 0.3 * inch))

            # Timeline Overview
            phases = timeline_data.get("phases", [])
            if phases:
                story.append(Paragraph("Timeline Overview", heading_style))

                timeline_table_data = [
                    ["Phase", "Start Date", "End Date", "Status", "Progress"]
                ]

                for phase in phases[:8]:  # Limit to 8 phases
                    timeline_table_data.append(
                        [
                            phase.get("name", "Unknown"),
                            phase.get("start_date", "TBD"),
                            phase.get("end_date", "TBD"),
                            phase.get("status", "Pending"),
                            f"{phase.get('progress', 0):.0f}%",
                        ]
                    )

                timeline_table = Table(
                    timeline_table_data,
                    colWidths=[2 * inch, 1.5 * inch, 1.5 * inch, 1 * inch, 1 * inch],
                )
                timeline_table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#fbbc04")),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                            ("FONTSIZE", (0, 0), (-1, 0), 12),
                            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                            ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                            ("GRID", (0, 0), (-1, -1), 1, colors.black),
                        ]
                    )
                )

                story.append(timeline_table)
                story.append(Spacer(1, 0.3 * inch))

            # Cost Breakdown
            if cost_estimation:
                story.append(Paragraph("Cost Breakdown", heading_style))

                contingency = planning_data.get("planning_config", {}).get(
                    "contingency_percentage", 15
                )
                cost_summary = f"""
                <para>
                <b>Total Estimated Cost:</b> ${cost_estimation.get('total_estimated_cost', 0):,.2f}<br/>
                <b>Resource Costs:</b> ${resource_allocation.get('total_cost_estimate', 0):,.2f}<br/>
                <b>Contingency Buffer:</b> {contingency}%<br/>
                </para>
                """

                story.append(Paragraph(cost_summary, styles["Normal"]))

            # Build PDF
            doc.build(story)

            # Get PDF bytes
            pdf_bytes = buffer.getvalue()
            buffer.close()

            # Generate filename
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"planning_report_{planning_flow_id}_{timestamp}.pdf"

            logger.info(f"✅ PDF export generated: {len(pdf_bytes)} bytes")

            return (pdf_bytes, "application/pdf", filename)

        except Exception as e:
            logger.error(f"❌ PDF export failed: {e}", exc_info=True)
            raise
