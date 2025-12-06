"""
Helper functions for architecture minimums execution

Utility functions for data aggregation, validation, and result building.
"""

from datetime import datetime
from typing import Any, Dict, List

from app.core.logging import get_logger

logger = get_logger(__name__)


async def aggregate_asset_data(
    data_repo: Any,
    applications: List[Dict[str, Any]],
    assessment_flow_id: str,
) -> List[Dict[str, Any]]:
    """Aggregate asset data for compliance validation."""
    assets_data = []

    for app in applications or []:
        app_id = str(app.get("id") or app.get("application_id", "unknown"))
        app_name = app.get("name") or app.get("application_name", "Unknown")

        # Get asset data for this application
        asset = await data_repo.get_asset_by_application_id(app_id)

        asset_info = {
            "asset_id": str(asset.id) if asset else app_id,
            "application_name": app_name,
            "operating_system": getattr(asset, "operating_system", None),
            "os_version": getattr(asset, "os_version", None),
            "database_type": getattr(asset, "database_types", None),
            "database_version": getattr(asset, "database_version", None),
            "technology_stack": app.get("technology_stack", {}),
            "collected_responses": app.get("collected_responses", {}),
        }

        assets_data.append(asset_info)

    return assets_data


def fallback_deterministic_validation(
    assets_data: List[Dict[str, Any]],
    engagement_standards: Dict[str, Any],
) -> Dict[str, Any]:
    """Fallback to deterministic validation when agent fails."""
    from app.core.seed_data.assessment_standards import (
        validate_technology_compliance,
    )

    checked_items = []
    compliant_count = 0

    for asset in assets_data:
        tech_stack = asset.get("technology_stack", {})
        if isinstance(tech_stack, list):
            tech_stack = {t: "unknown" for t in tech_stack}

        compliance_result = validate_technology_compliance(
            technology_stack=tech_stack,
            engagement_standards=engagement_standards,
        )

        is_compliant = compliance_result.get("compliant", True)
        if is_compliant:
            compliant_count += 1

        # Add OS check
        if asset.get("operating_system"):
            checked_items.append(
                {
                    "asset_id": asset.get("asset_id"),
                    "application_name": asset.get("application_name"),
                    "level": "os",
                    "category": "operating_system",
                    "technology": asset.get("operating_system"),
                    "current_version": asset.get("os_version"),
                    "eol_date": None,
                    "eol_status": "unknown",
                    "is_compliant": is_compliant,
                    "issue": (
                        None
                        if is_compliant
                        else "Unable to validate - agent unavailable"
                    ),
                    "severity": None if is_compliant else "medium",
                    "source": "fallback",
                }
            )

    return {
        "checked_items": checked_items,
        "summary": {
            "total_checked": len(checked_items),
            "compliant": compliant_count,
            "non_compliant": len(assets_data) - compliant_count,
            "eol_expired": 0,
            "eol_soon": 0,
            "by_level": {
                "os": {"checked": len(checked_items), "compliant": compliant_count},
                "application": {"checked": 0, "compliant": 0},
                "component": {"checked": 0, "compliant": 0},
            },
        },
        "recommendations": [
            "Agent-based validation unavailable - results may be incomplete"
        ],
    }


def transform_agent_result(
    compliance_result: Dict[str, Any],
    engagement_standards: Dict[str, Any],
    total_apps: int,
) -> Dict[str, Any]:
    """Transform agent result to the expected schema."""
    checked_items = compliance_result.get("checked_items", [])
    summary = compliance_result.get("summary", {})

    # Group by application
    apps_by_id: Dict[str, Dict[str, Any]] = {}
    for item in checked_items:
        asset_id = item.get("asset_id", "unknown")
        if asset_id not in apps_by_id:
            apps_by_id[asset_id] = {
                "application_name": item.get("application_name"),
                "is_compliant": True,
                "issues": [],
                "checked_fields": 0,
                "passed_fields": 0,
                "checked_items": [],
            }

        apps_by_id[asset_id]["checked_fields"] += 1
        if item.get("is_compliant"):
            apps_by_id[asset_id]["passed_fields"] += 1
        else:
            apps_by_id[asset_id]["is_compliant"] = False
            if item.get("issue"):
                apps_by_id[asset_id]["issues"].append(item.get("issue"))

        apps_by_id[asset_id]["checked_items"].append(item)

    compliant_count = sum(1 for app in apps_by_id.values() if app["is_compliant"])
    non_compliant_count = total_apps - compliant_count

    return {
        "engagement_standards": engagement_standards,
        "compliance_validation": {
            "overall_compliant": compliant_count == total_apps,
            "standards_applied": engagement_standards,
            "summary": {
                "total_applications": total_apps,
                "compliant_count": compliant_count,
                "non_compliant_count": non_compliant_count,
            },
            "by_level": summary.get(
                "by_level",
                {
                    "os": {"checked": 0, "compliant": 0},
                    "application": {"checked": 0, "compliant": 0},
                    "component": {"checked": 0, "compliant": 0},
                },
            ),
            "applications": apps_by_id,
            "checked_items": checked_items,
            "eol_status": [
                item
                for item in checked_items
                if item.get("eol_status") in ("eol_expired", "eol_soon")
            ],
            "recommendations": compliance_result.get("recommendations", []),
            "validated_at": datetime.utcnow().isoformat(),
            # Legacy fields for backward compatibility
            "total_applications": total_apps,
            "compliant_applications": compliant_count,
            "non_compliant_applications": non_compliant_count,
        },
        "validated_at": datetime.utcnow().isoformat(),
    }


def build_empty_result(
    engagement_standards: Dict[str, Any],
) -> Dict[str, Any]:
    """Build result for when no applications are found."""
    return {
        "phase": "architecture_minimums",
        "status": "completed",
        "agent": "compliance_validator",
        "engagement_standards": engagement_standards,
        "compliance_validation": {
            "overall_compliant": True,
            "standards_applied": engagement_standards,
            "summary": {
                "total_applications": 0,
                "compliant_count": 0,
                "non_compliant_count": 0,
            },
            "by_level": {
                "os": {"checked": 0, "compliant": 0},
                "application": {"checked": 0, "compliant": 0},
                "component": {"checked": 0, "compliant": 0},
            },
            "applications": {},
            "checked_items": [],
            "eol_status": [],
            "recommendations": [],
            "validated_at": datetime.utcnow().isoformat(),
        },
        "validated_at": datetime.utcnow().isoformat(),
    }


def build_error_result(error: str) -> Dict[str, Any]:
    """Build result for error cases."""
    return {
        "phase": "architecture_minimums",
        "status": "error",
        "error": error,
        "engagement_standards": {},
        "compliance_validation": {
            "overall_compliant": False,
            "standards_applied": {},
            "summary": {
                "total_applications": 0,
                "compliant_count": 0,
                "non_compliant_count": 0,
            },
            "by_level": {
                "os": {"checked": 0, "compliant": 0},
                "application": {"checked": 0, "compliant": 0},
                "component": {"checked": 0, "compliant": 0},
            },
            "applications": {},
            "checked_items": [],
            "eol_status": [],
            "validated_at": datetime.utcnow().isoformat(),
            "error": error,
        },
        "validated_at": datetime.utcnow().isoformat(),
    }


def get_default_standards() -> Dict[str, Any]:
    """Get default engagement standards when none are configured."""
    return {
        "supported_languages": [
            {"name": "Java", "min_version": "11", "max_version": "21"},
            {"name": "Python", "min_version": "3.8", "max_version": "3.12"},
            {"name": "Node.js", "min_version": "18", "max_version": "22"},
        ],
        "supported_databases": [
            {"name": "PostgreSQL", "min_version": "13", "max_version": "16"},
            {"name": "MySQL", "min_version": "8.0", "max_version": "8.0"},
        ],
        "supported_operating_systems": [
            {"name": "RHEL", "min_version": "8", "max_version": "9"},
            {
                "name": "Windows Server",
                "min_version": "2019",
                "max_version": "2022",
            },
            {"name": "Oracle Linux", "min_version": "8", "max_version": "9"},
        ],
        "cloud_providers": ["AWS", "Azure", "GCP"],
        "compliance_frameworks": [],
    }
