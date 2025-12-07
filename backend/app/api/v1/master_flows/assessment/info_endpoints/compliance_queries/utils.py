"""
Utility functions for compliance queries

Helper functions for parsing and processing compliance data.
"""

import logging
import re
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

logger = logging.getLogger(__name__)


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


async def _get_eol_status_for_tech_stack(
    tech_stack: Dict[str, str],
) -> List[Dict[str, Any]]:
    """
    Get EOL status for technologies in a stack.

    Uses EOLLifecycleService for authoritative EOL data.

    Args:
        tech_stack: Dict of technology -> version pairs

    Returns:
        List of EOL status dicts for each technology
    """
    from app.services.eol_lifecycle.eol_lifecycle_service import get_eol_service

    eol_results = []

    try:
        eol_service = await get_eol_service()

        for tech, version in tech_stack.items():
            if not version or version == "unknown":
                continue

            try:
                # Determine product type based on technology name
                # Use word boundaries to prevent false matches like "mysql-connector-java" -> "sql"
                tech_lower = tech.lower()
                if any(
                    re.search(rf"\b{os_name}\b", tech_lower)
                    for os_name in [
                        "windows",
                        "linux",
                        "rhel",
                        "ubuntu",
                        "debian",
                        "centos",
                    ]
                ):
                    product_type = "os"
                elif any(
                    re.search(rf"\b{db_name}\b", tech_lower)
                    for db_name in [
                        "sql server",
                        "sqlserver",
                        "oracle",
                        "postgres",
                        "postgresql",
                        "mysql",
                        "mongodb",
                        "mongo",
                        "redis",
                        "mariadb",
                    ]
                ):
                    product_type = "database"
                else:
                    product_type = "runtime"

                eol_status = await eol_service.get_eol_status(
                    tech, version, product_type
                )

                eol_results.append(
                    {
                        "product": eol_status.product,
                        "version": eol_status.version,
                        "status": eol_status.status.value,
                        "eol_date": (
                            eol_status.eol_date.isoformat()
                            if eol_status.eol_date
                            else None
                        ),
                        "support_type": eol_status.support_type.value,
                        "source": eol_status.source.value,
                        "confidence": eol_status.confidence,
                    }
                )
            except Exception as e:
                logger.debug(f"Failed to get EOL status for {tech} {version}: {e}")
                continue

    except Exception as e:
        logger.warning(f"Failed to initialize EOL service: {e}")

    return eol_results


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
