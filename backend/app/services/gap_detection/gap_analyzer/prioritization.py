"""
GapAnalyzer gap prioritization by business impact.

Part of Issue #980: Intelligent Multi-Layer Gap Detection System
"""

import logging
from typing import Any, List

logger = logging.getLogger(__name__)


class PrioritizationMixin:
    """Mixin for gap prioritization by business impact."""

    def _prioritize_gaps(
        self,
        column_gaps: Any,
        enrichment_gaps: Any,
        jsonb_gaps: Any,
        application_gaps: Any,
        standards_gaps: Any,
    ) -> tuple[List[str], List[str], List[str]]:
        """
        Prioritize gaps by business impact using critical attributes.

        Uses CriticalAttributesDefinition priority levels:
        - Priority 1 (Critical): Blocks assessment, mandatory for 6R decisions
        - Priority 2 (High): Important for accurate recommendations
        - Priority 3 (Medium): Nice to have, enhances context

        Args:
            column_gaps: ColumnGapReport
            enrichment_gaps: EnrichmentGapReport
            jsonb_gaps: JSONBGapReport
            application_gaps: ApplicationGapReport
            standards_gaps: StandardsGapReport

        Returns:
            Tuple of (critical_gaps, high_priority_gaps, medium_priority_gaps)
            Each is a list of missing field names.

        Note:
            Standards violations are ALWAYS critical if mandatory.
        """
        critical = []
        high = []
        medium = []

        # Collect all missing fields from column gaps
        for field in column_gaps.missing_attributes:
            priority = self._get_field_priority(field)
            if priority == 1:
                critical.append(field)
            elif priority == 2:
                high.append(field)
            else:
                medium.append(field)

        # Collect all missing fields from empty/null attributes
        for field in column_gaps.empty_attributes + column_gaps.null_attributes:
            priority = self._get_field_priority(field)
            if priority == 1:
                critical.append(field)
            elif priority == 2:
                high.append(field)
            else:
                medium.append(field)

        # Enrichment tables (all priority 2 - important for context)
        high.extend(enrichment_gaps.missing_tables)

        # JSONB keys (priority 3 - nice to have)
        for field_name, missing_keys in jsonb_gaps.missing_keys.items():
            medium.extend([f"{field_name}.{key}" for key in missing_keys])

        # Application gaps (priority 2 - important for business context)
        high.extend(application_gaps.missing_metadata)
        high.extend(application_gaps.missing_business_context)

        # Standards violations (ALWAYS critical if mandatory)
        for violation in standards_gaps.violated_standards:
            if violation.is_mandatory:
                critical.append(f"Standard: {violation.standard_name}")

        # Deduplicate while preserving order
        critical = list(dict.fromkeys(critical))
        high = list(dict.fromkeys(high))
        medium = list(dict.fromkeys(medium))

        logger.debug(
            "Prioritized gaps",
            extra={
                "critical_count": len(critical),
                "high_count": len(high),
                "medium_count": len(medium),
            },
        )

        return critical, high, medium

    def _get_field_priority(self, field_name: str) -> int:
        """
        Get priority level for a field from critical attributes.

        Looks up field in CriticalAttributesDefinition to determine priority.

        Args:
            field_name: Name of the field (e.g., "cpu_cores", "operating_system")

        Returns:
            Priority level:
            - 1: Critical (blocks assessment)
            - 2: High (important for accuracy)
            - 3: Medium (nice to have)
            - 3: Default if not in critical attributes

        Note:
            Uses cached critical_attributes mapping loaded at init.
        """
        # Check if field is in critical attributes mapping
        for attr_name, attr_config in self._critical_attributes.items():
            # Check if field_name matches attribute name or any of its asset_fields
            if field_name == attr_name or field_name in attr_config.get(
                "asset_fields", []
            ):
                return attr_config.get("priority", 3)

        # Default to medium priority if not in critical attributes
        return 3
