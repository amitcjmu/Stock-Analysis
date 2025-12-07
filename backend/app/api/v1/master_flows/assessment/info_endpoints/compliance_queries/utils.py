"""
Utility functions for compliance queries

Helper functions for parsing and processing compliance data.
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .schemas import (
    CheckedItem,
    ComplianceIssue,
    LevelComplianceResult,
    ThreeLevelComplianceResult,
)

# Re-export EOL functions for backward compatibility
from .eol_utils import (
    _get_eol_status_for_assets,
    _get_eol_status_for_tech_stack,
)

logger = logging.getLogger(__name__)

# Explicitly export EOL functions
__all__ = [
    "_normalize_issue",
    "_normalize_app_data",
    "_load_tenant_standards",
    "_get_default_standards",
    "_parse_by_level",
    "_get_eol_status_for_assets",
    "_get_eol_status_for_tech_stack",
]


def _normalize_issue(issue: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize a compliance issue to match ComplianceIssue schema.

    Handles both new format (field, current, required) and legacy format
    (technology, current_version, required_version).

    Args:
        issue: Raw issue dict from phase_results or validate_technology_compliance

    Returns:
        Normalized issue dict compatible with ComplianceIssue schema
    """
    return {
        "field": issue.get("field") or issue.get("technology", "Unknown"),
        "current": issue.get("current") or issue.get("current_version", "Unknown"),
        "required": issue.get("required") or issue.get("required_version", "Unknown"),
        "severity": issue.get(
            "severity", "critical" if issue.get("mandatory", True) else "medium"
        ),
        "recommendation": issue.get(
            "recommendation",
            f"Upgrade to {issue.get('required') or issue.get('required_version', 'required version')}",
        ),
    }


def _normalize_app_data(app_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize application compliance data to handle key variations.

    Handles both 'compliant' and 'is_compliant' keys for backward compatibility.

    Args:
        app_data: Raw application data from phase_results

    Returns:
        Normalized application data with consistent keys
    """
    # Handle is_compliant vs compliant key mismatch
    is_compliant = app_data.get("is_compliant")
    if is_compliant is None:
        is_compliant = app_data.get("compliant", True)

    # Normalize issues
    raw_issues = app_data.get("issues", [])
    normalized_issues = [_normalize_issue(issue) for issue in raw_issues]

    # Calculate checked_fields with sensible default
    checked_fields = app_data.get("checked_fields", len(raw_issues))

    return {
        "application_name": app_data.get("application_name"),
        "is_compliant": is_compliant,
        "issues": normalized_issues,
        "checked_fields": checked_fields,
        # Calculate passed_fields as checked - failed (issues count)
        "passed_fields": app_data.get(
            "passed_fields", max(0, checked_fields - len(raw_issues))
        ),
    }


async def _load_tenant_standards(
    db: AsyncSession,
    client_account_id: int,
    engagement_id: UUID,
) -> List[Dict[str, Any]]:
    """
    Load tenant-specific engagement standards from database.

    Falls back to default standards if none configured.

    Args:
        db: Async database session
        client_account_id: Client account ID
        engagement_id: Engagement UUID

    Returns:
        List of standards in validate_technology_compliance format
    """
    from app.models.assessment_flow import EngagementArchitectureStandard

    try:
        stmt = select(EngagementArchitectureStandard).where(
            EngagementArchitectureStandard.client_account_id == client_account_id,
            EngagementArchitectureStandard.engagement_id == engagement_id,
        )
        result = await db.execute(stmt)
        tenant_standards = result.scalars().all()

        if tenant_standards:
            # Convert DB records to validate_technology_compliance format
            standards = []
            for std in tenant_standards:
                standard_dict = {
                    "requirement_type": std.requirement_type,
                    "description": std.description or "",
                    "mandatory": std.is_mandatory,
                    "supported_versions": std.preferred_patterns or {},
                    "priority": std.priority or 5,
                }
                standards.append(standard_dict)

            logger.info(
                f"Loaded {len(standards)} tenant standards for engagement {engagement_id}"
            )
            return standards

    except Exception as e:
        logger.warning(f"Failed to load tenant standards: {e}, using defaults")

    # Fall back to defaults
    return _get_default_standards()


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
