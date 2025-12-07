"""
PDF report generator for planning flow export (Issue #714).

Generates professional PDF reports using reportlab.
"""

import io
from datetime import datetime
from typing import Any, Dict

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def _create_wave_table(wave_data: Dict[str, Any]) -> Table | None:
    """Create wave plan table for PDF."""
    if not isinstance(wave_data, dict) or not wave_data.get("waves"):
        return None

    wave_rows = [["Wave", "Assets", "Status", "Start Date", "End Date"]]
    for wave in wave_data.get("waves", []):
        wave_rows.append(
            [
                wave.get("wave_name", "N/A"),
                str(len(wave.get("assets", []))),
                wave.get("status", "planned"),
                wave.get("start_date", "TBD"),
                wave.get("end_date", "TBD"),
            ]
        )

    wave_table = Table(wave_rows, colWidths=[1.2 * inch] * 5)
    wave_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e40af")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#f9fafb")],
                ),
            ]
        )
    )
    return wave_table


def _create_cost_table(cost_data: Dict[str, Any]) -> Table | None:
    """Create cost estimation table for PDF."""
    if not isinstance(cost_data, dict) or not cost_data:
        return None

    cost_rows = [["Category", "Estimated Cost"]]
    for key, value in cost_data.items():
        if key not in ("total", "currency"):
            cost_rows.append(
                [
                    key.replace("_", " ").title(),
                    (
                        f"${value:,.2f}"
                        if isinstance(value, (int, float))
                        else str(value)
                    ),
                ]
            )
    if cost_data.get("total"):
        cost_rows.append(["Total", f"${cost_data['total']:,.2f}"])

    cost_table = Table(cost_rows, colWidths=[3 * inch, 2 * inch])
    cost_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e40af")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]
        )
    )
    return cost_table


def generate_pdf_report(planning_flow: Any, metadata: Dict[str, Any]) -> io.BytesIO:
    """Generate PDF report for planning flow data (Issue #714)."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5 * inch)
    styles = getSampleStyleSheet()
    elements = []

    # Title
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Heading1"],
        fontSize=18,
        spaceAfter=20,
        textColor=colors.HexColor("#1e40af"),
    )
    elements.append(Paragraph("Migration Planning Report", title_style))
    elements.append(Spacer(1, 12))

    # Metadata section
    meta_data = [
        ["Planning Flow ID", str(planning_flow.planning_flow_id)],
        ["Current Phase", planning_flow.current_phase or "N/A"],
        ["Phase Status", planning_flow.phase_status or "N/A"],
        ["Generated At", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")],
    ]
    meta_table = Table(meta_data, colWidths=[2 * inch, 4 * inch])
    meta_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f3f4f6")),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]
        )
    )
    elements.append(meta_table)
    elements.append(Spacer(1, 20))

    # Wave Plan Section
    elements.append(Paragraph("Wave Plan", styles["Heading2"]))
    elements.append(Spacer(1, 8))

    wave_data = planning_flow.wave_plan_data or {}
    wave_table = _create_wave_table(wave_data)
    if wave_table:
        elements.append(wave_table)
    else:
        elements.append(Paragraph("No wave plan data available.", styles["Normal"]))

    elements.append(Spacer(1, 20))

    # Cost Estimation Section
    elements.append(Paragraph("Cost Estimation", styles["Heading2"]))
    elements.append(Spacer(1, 8))

    cost_data = planning_flow.cost_estimation_data or {}
    cost_table = _create_cost_table(cost_data)
    if cost_table:
        elements.append(cost_table)
    else:
        elements.append(
            Paragraph("No cost estimation data available.", styles["Normal"])
        )

    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer
