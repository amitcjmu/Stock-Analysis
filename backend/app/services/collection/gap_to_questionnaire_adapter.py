"""
Gap-to-Questionnaire Adapter

Bridges GapAnalyzer ComprehensiveGapReport to IntelligentQuestionnaireGenerator.
Transforms multi-layer gap analysis into targeted questionnaire generation.

Part of Issue #980: Intelligent Multi-Layer Gap Detection System - Day 14
Author: CC (Claude Code)
GPT-5 Recommendations: #1 (tenant scoping), #3 (async), #8 (JSON safety)
"""

import logging
from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.services.gap_detection.schemas import (
    ComprehensiveGapReport,
    FieldGap,
    GapPriority,
)

logger = logging.getLogger(__name__)


class GapToQuestionnaireAdapter:
    """
    Adapter that transforms ComprehensiveGapReport into questionnaire generation input.

    This adapter is the bridge between the new gap detection system (GapAnalyzer)
    and the existing questionnaire generation system (IntelligentQuestionnaireGenerator).

    Key Features:
    - Prioritizes critical/high gaps for questionnaire generation
    - Preserves asset context and gap metadata
    - Filters out low-priority gaps to reduce noise
    - Maintains backward compatibility with existing questionnaire format
    """

    def __init__(self):
        """Initialize the adapter."""
        pass

    async def generate_questionnaire_from_gaps(
        self,
        gap_report: ComprehensiveGapReport,
        context: RequestContext,
        db: AsyncSession,
    ) -> Dict[str, Any]:
        """
        Generate questionnaire DIRECTLY from GapAnalyzer gaps (Issue #980).

        This bypasses the critical attributes mapping system and generates questions
        directly from the gaps identified by GapAnalyzer. This ensures that ALL gaps
        blocking assessment readiness are included in the questionnaire.

        Args:
            gap_report: Comprehensive gap analysis report from GapAnalyzer
            context: Request context with tenant scoping
            db: Database session for additional lookups

        Returns:
            Questionnaire generation result with sections and questions
        """
        logger.info(
            f"Generating questionnaire DIRECTLY from gaps for asset {gap_report.asset_id} "
            f"with {len(gap_report.all_gaps)} total gaps"
        )

        # CRITICAL: Use ALL gaps that block assessment readiness, not just CRITICAL/HIGH
        # Filter to gaps that actually block assessment (based on readiness_blockers)
        blocking_gaps = [
            gap
            for gap in gap_report.all_gaps
            if gap.field_name in (gap_report.readiness_blockers or [])
            or gap.priority in [GapPriority.CRITICAL, GapPriority.HIGH]
        ]

        if not blocking_gaps:
            logger.warning(
                f"No blocking gaps found for asset {gap_report.asset_id}. "
                f"Using all gaps as fallback."
            )
            blocking_gaps = gap_report.all_gaps

        logger.info(
            f"Generating questions for {len(blocking_gaps)} blocking gaps "
            f"(out of {len(gap_report.all_gaps)} total gaps)"
        )

        # Get asset info for context
        from sqlalchemy import select
        from app.models.asset import Asset

        asset_result = await db.execute(
            select(Asset).where(Asset.id == gap_report.asset_id)
        )
        asset = asset_result.scalar_one_or_none()
        asset_name = str(gap_report.asset_id)
        asset_type = "application"
        if asset:
            asset_name = asset.name or asset.asset_name or str(gap_report.asset_id)
            asset_type = asset.asset_type or "application"

        # Group gaps by category based on layer and field name
        sections = self._build_sections_from_gaps(
            blocking_gaps, gap_report.asset_id, asset_name, asset_type
        )

        # Build result structure
        all_questions = []
        for section in sections:
            all_questions.extend(section.get("questions", []))

        result = {
            "status": "success",
            "questionnaires": sections,
            "metadata": {
                "total_sections": len(sections),
                "total_questions": len(all_questions),
                "asset_id": str(gap_report.asset_id),
                "asset_name": asset_name,
                "gaps_processed": len(blocking_gaps),
                "total_gaps": len(gap_report.all_gaps),
            },
        }

        logger.info(
            f"✅ Generated {len(sections)} sections with {len(all_questions)} questions "
            f"directly from {len(blocking_gaps)} gaps"
        )

        return result

    def _build_sections_from_gaps(
        self,
        gaps: List[FieldGap],
        asset_id: UUID,
        asset_name: str,
        asset_type: str,
    ) -> List[Dict[str, Any]]:
        """
        Build questionnaire sections directly from gap field names.

        Groups gaps by layer/category and creates questions for each gap.
        """
        # Group gaps by layer
        sections_by_layer = {
            "column": [],
            "jsonb": [],
            "enrichment": [],
            "application": [],
            "standards": [],
        }

        for gap in gaps:
            layer = gap.layer or "column"
            if layer not in sections_by_layer:
                layer = "column"  # Default fallback
            sections_by_layer[layer].append(gap)

        sections = []

        # Create section for each layer that has gaps
        layer_configs = {
            "column": {
                "section_id": "asset_fields",
                "section_title": "Asset Information",
                "section_description": "Basic asset fields required for assessment",
            },
            "jsonb": {
                "section_id": "technical_details",
                "section_title": "Technical Details",
                "section_description": "Technical specifications and configuration details",
            },
            "enrichment": {
                "section_id": "enrichment_data",
                "section_title": "Enrichment Data",
                "section_description": "Additional enrichment data for assessment",
            },
            "application": {
                "section_id": "application_metadata",
                "section_title": "Application Metadata",
                "section_description": "Application-level metadata and information",
            },
            "standards": {
                "section_id": "compliance_standards",
                "section_title": "Compliance & Standards",
                "section_description": "Compliance and architectural standards information",
            },
        }

        for layer, layer_gaps in sections_by_layer.items():
            if not layer_gaps:
                continue

            config = layer_configs.get(layer, layer_configs["column"])
            questions = []

            for gap in layer_gaps:
                question = self._build_question_from_gap(
                    gap, asset_id, asset_name, asset_type
                )
                questions.append(question)

            sections.append(
                {
                    "section_id": config["section_id"],
                    "section_title": config["section_title"],
                    "section_description": config["section_description"],
                    "questions": questions,
                }
            )

        return sections

    def _build_question_from_gap(
        self,
        gap: FieldGap,
        asset_id: UUID,
        asset_name: str,
        asset_type: str,
    ) -> Dict[str, Any]:
        """
        Build a question object directly from a gap.

        Uses gap metadata (field_name, priority, reason, layer) to create
        appropriate question text and field type.
        """
        field_name = gap.field_name
        readable_name = field_name.replace("_", " ").replace(".", " ").title()

        # Determine field type based on field name patterns
        field_type = "text"
        options = None

        # Check for common field patterns
        if any(x in field_name.lower() for x in ["criticality", "priority", "status"]):
            field_type = "select"
            options = self._get_options_for_field(field_name, asset_type)
        elif any(
            x in field_name.lower() for x in ["type", "category", "classification"]
        ):
            field_type = "select"
            options = self._get_options_for_field(field_name, asset_type)
        elif "version" in field_name.lower() or "version" in readable_name.lower():
            field_type = "text"  # Versions are free-form
        elif field_name in ["description", "notes", "comments"]:
            field_type = "textarea"
        elif any(
            x in field_name.lower() for x in ["count", "number", "cores", "gb", "mb"]
        ):
            field_type = "number"
        elif field_name.endswith("_id") or "uuid" in field_name.lower():
            field_type = "text"  # IDs are text

        # Build question text from gap reason if available
        question_text = gap.reason or f"What is the {readable_name}?"
        if not question_text.endswith("?"):
            question_text = f"{question_text}?"

        question = {
            "field_id": f"{asset_id}__{field_name}",  # Composite ID for asset-specific fields
            "question_text": question_text,
            "field_type": field_type,
            "required": gap.priority in [GapPriority.CRITICAL, GapPriority.HIGH],
            "category": gap.layer or "application",
            "metadata": {
                "asset_id": str(asset_id),
                "asset_name": asset_name,
                "gap_field_name": field_name,
                "gap_priority": (
                    gap.priority.value
                    if isinstance(gap.priority, GapPriority)
                    else str(gap.priority)
                ),
                "gap_layer": gap.layer,
                "gap_reason": gap.reason,
            },
            "help_text": f"Please provide the {readable_name.lower()} for {asset_name}.",
        }

        if options:
            question["options"] = options

        return question

    def _get_options_for_field(
        self, field_name: str, asset_type: str
    ) -> List[Dict[str, str]]:
        """Get options for select/dropdown fields based on field name."""
        field_lower = field_name.lower()

        if "criticality" in field_lower:
            return [
                {"value": "critical", "label": "Critical"},
                {"value": "high", "label": "High"},
                {"value": "medium", "label": "Medium"},
                {"value": "low", "label": "Low"},
            ]
        elif "type" in field_lower and "application" in field_lower:
            return [
                {"value": "web_application", "label": "Web Application"},
                {"value": "api_service", "label": "API Service"},
                {"value": "batch_job", "label": "Batch Job"},
                {"value": "database", "label": "Database"},
                {"value": "other", "label": "Other"},
            ]
        elif "status" in field_lower:
            return [
                {"value": "active", "label": "Active"},
                {"value": "inactive", "label": "Inactive"},
                {"value": "deprecated", "label": "Deprecated"},
                {"value": "decommissioned", "label": "Decommissioned"},
            ]

        return None

    async def transform_to_questionnaire_input(
        self,
        gap_report: ComprehensiveGapReport,
        context: RequestContext,
        db: AsyncSession,
    ) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Transform ComprehensiveGapReport into questionnaire generation inputs.

        DEPRECATED: This method uses the old critical attributes mapping system.
        Use generate_questionnaire_from_gaps() instead for Issue #980 compliance.

        Args:
            gap_report: Comprehensive gap analysis report from GapAnalyzer
            context: Request context with tenant scoping
            db: Database session for additional lookups

        Returns:
            Tuple of (data_gaps dict, business_context dict) formatted for
            QuestionnaireGenerationTool._arun()

        Performance: O(n) where n = total gaps, target <10ms for typical reports
        """
        logger.warning(
            "Using deprecated transform_to_questionnaire_input() - "
            "consider using generate_questionnaire_from_gaps() for Issue #980 compliance"
        )

        logger.info(
            f"Transforming gap report for asset {gap_report.asset_id} "
            f"with {len(gap_report.all_gaps)} total gaps"
        )

        # Extract critical and high priority gaps only
        priority_gaps = self._filter_priority_gaps(gap_report)

        # Group gaps by asset (supporting multi-asset future expansion)
        missing_critical_fields = self._build_missing_fields_map(
            priority_gaps, gap_report.asset_id
        )

        # Build data_gaps structure
        data_gaps = {
            "missing_critical_fields": missing_critical_fields,
            "data_quality_issues": {},  # Can be enhanced with enrichment gaps
            "assets_with_gaps": [str(gap_report.asset_id)],
        }

        # CRITICAL FIX: Get actual asset name from database for questionnaire context
        from sqlalchemy import select
        from app.models.asset import Asset

        asset_name = str(gap_report.asset_id)  # Fallback to UUID
        asset_type = "application"  # Default

        asset_result = await db.execute(
            select(Asset).where(Asset.id == gap_report.asset_id)
        )
        asset = asset_result.scalar_one_or_none()
        if asset:
            asset_name = asset.name or asset.asset_name or str(gap_report.asset_id)
            asset_type = asset.asset_type or "application"

        # Build business context
        business_context = {
            "client_account_id": str(context.client_account_id),
            "engagement_id": str(context.engagement_id),
            "total_assets": 1,  # Single asset for now
            "assets": {
                str(gap_report.asset_id): {
                    "name": asset_name,  # CRITICAL FIX: Use actual asset name, not UUID
                    "type": asset_type,  # Use actual asset type
                }
            },
            "gap_analysis_metadata": {
                "overall_completeness": gap_report.overall_completeness,
                "assessment_ready": gap_report.is_ready_for_assessment,
                "total_gaps_found": len(gap_report.all_gaps),
                "critical_gaps": len(
                    [
                        g
                        for g in gap_report.all_gaps
                        if g.priority == GapPriority.CRITICAL
                    ]
                ),
                "high_gaps": len(
                    [g for g in gap_report.all_gaps if g.priority == GapPriority.HIGH]
                ),
            },
        }

        logger.info(
            f"Transformed {len(priority_gaps)} priority gaps into questionnaire input "
            f"(critical: {business_context['gap_analysis_metadata']['critical_gaps']}, "
            f"high: {business_context['gap_analysis_metadata']['high_gaps']})"
        )

        return data_gaps, business_context

    def _filter_priority_gaps(
        self, gap_report: ComprehensiveGapReport
    ) -> List[FieldGap]:
        """
        Filter gaps to only critical and high priority.

        Medium and low priority gaps are excluded to avoid overwhelming users
        with questionnaires. These can be collected through less intrusive means.

        Args:
            gap_report: Comprehensive gap report

        Returns:
            List of FieldGap objects with priority >= HIGH
        """
        priority_gaps = [
            gap
            for gap in gap_report.all_gaps
            if gap.priority in [GapPriority.CRITICAL, GapPriority.HIGH]
        ]

        logger.debug(
            f"Filtered {len(priority_gaps)} priority gaps from {len(gap_report.all_gaps)} total gaps"
        )

        return priority_gaps

    def _build_missing_fields_map(
        self, priority_gaps: List[FieldGap], asset_id: UUID
    ) -> Dict[str, List[str]]:
        """
        Build missing_critical_fields map for questionnaire generation.

        Format: {"asset_id": ["field_name1", "field_name2", ...]}

        This format is required by QuestionnaireGenerationTool._process_missing_fields()
        which expects a dict mapping asset_id to list of field names (NOT field objects).

        Args:
            priority_gaps: List of high-priority gaps
            asset_id: Asset UUID

        Returns:
            Dict mapping asset_id to list of missing field names
        """
        asset_id_str = str(asset_id)
        field_names = []

        for gap in priority_gaps:
            # Extract field name from gap
            # FieldGap.field_name contains the actual field name
            if gap.field_name:
                field_names.append(gap.field_name)

        logger.debug(
            f"Built missing fields map with {len(field_names)} fields for asset {asset_id_str}"
        )

        return {asset_id_str: field_names} if field_names else {}

    async def enhance_with_existing_data(
        self,
        data_gaps: Dict[str, Any],
        asset_id: UUID,
        db: AsyncSession,
        context: RequestContext,
    ) -> Dict[str, Any]:
        """
        Enhance data_gaps with existing field values for pre-fill.

        This allows the questionnaire to show existing values for verification
        rather than asking for completely new input.

        Args:
            data_gaps: Base data_gaps dict
            asset_id: Asset UUID
            db: Database session
            context: Request context

        Returns:
            Enhanced data_gaps dict with existing_field_values
        """
        # Query asset and application enrichment data
        from sqlalchemy import select

        from app.models.asset import Asset

        result = await db.execute(
            select(Asset).where(
                Asset.id == asset_id,
                Asset.client_account_id == context.client_account_id,
                Asset.engagement_id == context.engagement_id,
            )
        )
        asset = result.scalar_one_or_none()

        if not asset:
            logger.warning(f"Asset {asset_id} not found for data enhancement")
            return data_gaps

        # Build existing field values map
        existing_values = {}
        if asset.operating_system:
            existing_values["operating_system"] = asset.operating_system
        if asset.ip_address:
            existing_values["ip_address"] = asset.ip_address

        # Add enrichment data if available
        if hasattr(asset, "enrichment_data") and asset.enrichment_data:
            enrichment = asset.enrichment_data
            if enrichment.database_version:
                existing_values["database_version"] = enrichment.database_version
            if enrichment.backup_frequency:
                existing_values["backup_frequency"] = enrichment.backup_frequency

        # Add to data_gaps
        if existing_values:
            data_gaps["existing_field_values"] = {str(asset_id): existing_values}
            logger.debug(
                f"Enhanced data_gaps with {len(existing_values)} existing field values"
            )

        return data_gaps


__all__ = ["GapToQuestionnaireAdapter"]
