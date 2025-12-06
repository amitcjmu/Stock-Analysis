"""
Utility functions for compliance queries

Helper functions for parsing and processing compliance data.
"""

from typing import Any, Dict, List, Optional

from .schemas import (
    CheckedItem,
    ComplianceIssue,
    LevelComplianceResult,
    ThreeLevelComplianceResult,
)


def _get_default_standards() -> List[Dict[str, Any]]:
    """
    Get default engagement standards when none are configured.

    Returns the standards in the format expected by validate_technology_compliance:
    List of dicts with supported_versions key.
    """
    from app.core.seed_data.standards.technology_versions import TECH_VERSION_STANDARDS

    return TECH_VERSION_STANDARDS


def _parse_by_level(
    by_level_data: Optional[Dict[str, Any]],
) -> Optional[ThreeLevelComplianceResult]:
    """
    Parse by_level data from phase_results into ThreeLevelComplianceResult.

    Issue #1243: Three-level compliance validation support.
    """
    if not by_level_data:
        return None

    def _parse_level(
        level_data: Optional[Dict[str, Any]], level_name: str
    ) -> LevelComplianceResult:
        """Parse a single level's data."""
        if not level_data:
            return LevelComplianceResult(level_name=level_name)

        return LevelComplianceResult(
            level_name=level_name,
            is_compliant=level_data.get("is_compliant", True),
            checked_count=level_data.get("checked_count", 0),
            passed_count=level_data.get("passed_count", 0),
            failed_count=level_data.get("failed_count", 0),
            checked_items=[
                CheckedItem(**item) for item in level_data.get("checked_items", [])
            ],
            issues=[ComplianceIssue(**issue) for issue in level_data.get("issues", [])],
        )

    return ThreeLevelComplianceResult(
        os_compliance=_parse_level(by_level_data.get("os_compliance"), "os"),
        application_compliance=_parse_level(
            by_level_data.get("application_compliance"), "application"
        ),
        component_compliance=_parse_level(
            by_level_data.get("component_compliance"), "component"
        ),
    )
