"""
Report Transformer - Converts ComprehensiveGapReport to legacy gap dict format.

Part of Day 13 refactoring (Issue #980) to preserve backward compatibility
while using shared inspectors from gap_detection module.
"""

import logging
from typing import Any, Dict, List

from app.models.asset import Asset
from app.services.gap_detection.schemas import ComprehensiveGapReport

logger = logging.getLogger(__name__)


class ReportTransformer:
    """
    Transforms ComprehensiveGapReport to legacy gap dictionary format.

    This transformation layer preserves backward compatibility with collection flow
    which expects a flat list of gap dictionaries instead of the structured
    ComprehensiveGapReport from GapAnalyzer.
    """

    @staticmethod
    def transform_to_legacy_format(
        report: ComprehensiveGapReport, asset: Asset
    ) -> List[Dict[str, Any]]:
        """
        Transform ComprehensiveGapReport to legacy gap dict format.

        Args:
            report: ComprehensiveGapReport from GapAnalyzer
            asset: Asset SQLAlchemy model

        Returns:
            List of gap dictionaries in legacy format:
            [
                {
                    "asset_id": "uuid",
                    "asset_name": "App-001",
                    "field_name": "technology_stack",
                    "gap_type": "missing_field",
                    "gap_category": "application",
                    "priority": 1,
                    "current_value": None,
                    "suggested_resolution": "Manual collection required",
                    "confidence_score": None  # No AI yet
                }
            ]
        """
        gaps = []
        asset_id = str(asset.id)
        asset_name = getattr(asset, "name", "Unknown Asset")
        asset_type = getattr(asset, "asset_type", "other")

        # Map asset_type to gap_category
        gap_category = asset_type.lower() if asset_type else "unknown"

        # Extract gaps from column report
        for field_name in report.column_gaps.missing_attributes:
            gaps.append(
                {
                    "asset_id": asset_id,
                    "asset_name": asset_name,
                    "field_name": field_name,
                    "gap_type": "missing_field",
                    "gap_category": gap_category,
                    "priority": ReportTransformer._get_field_priority(
                        field_name, report.critical_gaps, report.high_priority_gaps
                    ),
                    "current_value": None,
                    "suggested_resolution": "Manual collection required",
                    "confidence_score": None,
                }
            )

        for field_name in report.column_gaps.empty_attributes:
            gaps.append(
                {
                    "asset_id": asset_id,
                    "asset_name": asset_name,
                    "field_name": field_name,
                    "gap_type": "empty_field",
                    "gap_category": gap_category,
                    "priority": ReportTransformer._get_field_priority(
                        field_name, report.critical_gaps, report.high_priority_gaps
                    ),
                    "current_value": "",
                    "suggested_resolution": "Manual collection required",
                    "confidence_score": None,
                }
            )

        for field_name in report.column_gaps.null_attributes:
            gaps.append(
                {
                    "asset_id": asset_id,
                    "asset_name": asset_name,
                    "field_name": field_name,
                    "gap_type": "null_field",
                    "gap_category": gap_category,
                    "priority": ReportTransformer._get_field_priority(
                        field_name, report.critical_gaps, report.high_priority_gaps
                    ),
                    "current_value": None,
                    "suggested_resolution": "Manual collection required",
                    "confidence_score": None,
                }
            )

        # Extract gaps from enrichment report
        for table_name in report.enrichment_gaps.missing_tables:
            gaps.append(
                {
                    "asset_id": asset_id,
                    "asset_name": asset_name,
                    "field_name": table_name,
                    "gap_type": "missing_enrichment",
                    "gap_category": "enrichment",
                    "priority": ReportTransformer._get_field_priority(
                        table_name, report.critical_gaps, report.high_priority_gaps
                    ),
                    "current_value": None,
                    "suggested_resolution": "Enrichment data collection required",
                    "confidence_score": None,
                }
            )

        for table_name, fields in report.enrichment_gaps.incomplete_tables.items():
            for field_name in fields:
                gaps.append(
                    {
                        "asset_id": asset_id,
                        "asset_name": asset_name,
                        "field_name": f"{table_name}.{field_name}",
                        "gap_type": "incomplete_enrichment",
                        "gap_category": "enrichment",
                        "priority": ReportTransformer._get_field_priority(
                            field_name, report.critical_gaps, report.high_priority_gaps
                        ),
                        "current_value": None,
                        "suggested_resolution": "Complete enrichment data required",
                        "confidence_score": None,
                    }
                )

        # Extract gaps from JSONB report
        for jsonb_field, missing_keys in report.jsonb_gaps.missing_keys.items():
            for key in missing_keys:
                gaps.append(
                    {
                        "asset_id": asset_id,
                        "asset_name": asset_name,
                        "field_name": f"{jsonb_field}.{key}",
                        "gap_type": "missing_jsonb_key",
                        "gap_category": "jsonb",
                        "priority": ReportTransformer._get_field_priority(
                            key, report.critical_gaps, report.high_priority_gaps
                        ),
                        "current_value": None,
                        "suggested_resolution": "JSONB field collection required",
                        "confidence_score": None,
                    }
                )

        # Extract gaps from application report (if applicable)
        for field_name in report.application_gaps.missing_metadata:
            gaps.append(
                {
                    "asset_id": asset_id,
                    "asset_name": asset_name,
                    "field_name": field_name,
                    "gap_type": "missing_metadata",
                    "gap_category": "application",
                    "priority": ReportTransformer._get_field_priority(
                        field_name, report.critical_gaps, report.high_priority_gaps
                    ),
                    "current_value": None,
                    "suggested_resolution": "Application metadata collection required",
                    "confidence_score": None,
                }
            )

        # Extract gaps from standards report (violations)
        for violation in report.standards_gaps.violated_standards:
            gaps.append(
                {
                    "asset_id": asset_id,
                    "asset_name": asset_name,
                    "field_name": violation.standard_name,
                    "gap_type": "standards_violation",
                    "gap_category": "standards",
                    "priority": 1 if violation.is_mandatory else 2,
                    "current_value": None,
                    "suggested_resolution": violation.violation_details,
                    "confidence_score": None,
                }
            )

        return gaps

    @staticmethod
    def _get_field_priority(
        field_name: str, critical_gaps: List[str], high_priority_gaps: List[str]
    ) -> int:
        """
        Determine priority (1/2/3) based on GapAnalyzer's prioritization.

        Args:
            field_name: Field name to check
            critical_gaps: Critical gaps from GapAnalyzer
            high_priority_gaps: High priority gaps from GapAnalyzer

        Returns:
            1 (critical), 2 (high), or 3 (medium)
        """
        if field_name in critical_gaps:
            return 1
        elif field_name in high_priority_gaps:
            return 2
        else:
            return 3
