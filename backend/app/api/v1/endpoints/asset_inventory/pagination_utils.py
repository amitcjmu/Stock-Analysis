"""
Utility functions for asset pagination endpoints.
Contains data transformation, analysis, and response formatting functions.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


def _create_empty_response(
    page: int, page_size: int, data_source: str = "fallback"
) -> Dict[str, Any]:
    """Create standardized empty response structure."""
    return {
        "assets": [],
        "pagination": {
            "current_page": page,
            "page_size": page_size,
            "total_items": 0,
            "total_pages": 0,
            "has_next": False,
            "has_previous": False,
        },
        "summary": {
            "total": 0,
            "filtered": 0,
            "applications": 0,
            "servers": 0,
            "databases": 0,
            "devices": 0,
            "unknown": 0,
            "discovered": 0,
            "pending": 0,
            "device_breakdown": {},
        },
        "last_updated": None,
        "data_source": data_source,
        "suggested_headers": [],
        "app_mappings": [],
        "unlinked_assets": [],
        "unlinked_summary": {
            "total_unlinked": 0,
            "by_type": {},
            "by_environment": {},
            "by_criticality": {},
            "migration_impact": "none",
        },
    }


def _convert_assets_to_dicts(assets) -> List[Dict[str, Any]]:
    """Convert SQLAlchemy asset objects to dictionaries."""
    asset_dicts = []
    for asset in assets:
        asset_dict = {
            "id": str(asset.id),
            "name": asset.name,
            "asset_type": asset.asset_type,
            "environment": asset.environment,
            "criticality": asset.criticality,
            "status": asset.status,
            "six_r_strategy": asset.six_r_strategy,
            "migration_wave": asset.migration_wave,
            "application_name": asset.application_name,
            "hostname": asset.hostname,
            "operating_system": asset.operating_system,
            "cpu_cores": asset.cpu_cores,
            "memory_gb": asset.memory_gb,
            "storage_gb": asset.storage_gb,
            "created_at": (asset.created_at.isoformat() if asset.created_at else None),
            "updated_at": (asset.updated_at.isoformat() if asset.updated_at else None),
            # CMDB Enhancement Fields (Issue #833)
            "business_unit": asset.business_unit,
            "vendor": asset.vendor,
            "application_type": asset.application_type,
            "lifecycle": asset.lifecycle,
            "hosting_model": asset.hosting_model,
            "server_role": asset.server_role,
            "security_zone": asset.security_zone,
            "database_type": asset.database_type,
            "database_version": asset.database_version,
            "database_size_gb": asset.database_size_gb,
            "cpu_utilization_percent_max": asset.cpu_utilization_percent_max,
            "memory_utilization_percent_max": asset.memory_utilization_percent_max,
            "storage_free_gb": asset.storage_free_gb,
            "storage_used_gb": asset.storage_used_gb,
            "tech_debt_flags": asset.tech_debt_flags,
            "pii_flag": asset.pii_flag,
            "application_data_classification": asset.application_data_classification,
            "has_saas_replacement": asset.has_saas_replacement,
            "risk_level": asset.risk_level,
            "tshirt_size": asset.tshirt_size,
            "proposed_treatmentplan_rationale": asset.proposed_treatmentplan_rationale,
            "annual_cost_estimate": asset.annual_cost_estimate,
            "backup_policy": asset.backup_policy,
            "asset_tags": asset.asset_tags,
            # Child table relationships
            "contacts": (
                [c.to_dict() for c in asset.contacts]
                if hasattr(asset, "contacts") and asset.contacts
                else []
            ),
            "eol_assessments": (
                [e.to_dict() for e in asset.eol_assessments]
                if hasattr(asset, "eol_assessments") and asset.eol_assessments
                else []
            ),
        }
        asset_dicts.append(asset_dict)
    return asset_dicts


def _analyze_asset_types(
    asset_dicts: List[Dict[str, Any]],
) -> Tuple[Dict[str, int], int, bool]:
    """Analyze asset types and determine if classification is needed."""
    logger.info(f"🔍 Asset Inventory Debug: Found {len(asset_dicts)} assets")

    asset_types_found = {}
    unclassified_count = 0

    for asset_dict in asset_dicts:
        asset_type = asset_dict.get("asset_type")
        if asset_type:
            asset_types_found[asset_type] = asset_types_found.get(asset_type, 0) + 1
        else:
            unclassified_count += 1

    logger.info(f"🔍 Asset types in database: {asset_types_found}")
    logger.info(f"🔍 Unclassified assets: {unclassified_count}")

    needs_classification = (
        unclassified_count > 0
        or len(asset_types_found) == 0
        or all(
            asset_type in ["unknown", "other", None]
            for asset_type in asset_types_found.keys()
        )
    )

    if needs_classification and len(asset_dicts) > 0:
        logger.warning(
            f"🚨 Assets need CrewAI classification: {unclassified_count} unclassified, "
            f"types found: {asset_types_found}"
        )

    return asset_types_found, unclassified_count, needs_classification


def _calculate_summary_stats(
    asset_dicts: List[Dict[str, Any]], total_items: int
) -> Dict[str, Any]:
    """Calculate summary statistics for assets."""
    summary_stats = {
        "total": total_items,
        "filtered": total_items,
        "applications": 0,
        "servers": 0,
        "databases": 0,
        "devices": 0,
        "unknown": 0,
        "discovered": 0,
        "pending": 0,
        "device_breakdown": {},
    }

    device_terms = ["device", "network", "storage", "security", "infrastructure"]

    for asset_dict in asset_dicts:
        asset_type = (asset_dict.get("asset_type") or "").lower()
        status = asset_dict.get("status")

        # Count by asset type
        if asset_type == "application":
            summary_stats["applications"] += 1
        elif asset_type == "server":
            summary_stats["servers"] += 1
        elif asset_type == "database":
            summary_stats["databases"] += 1
        elif any(term in asset_type for term in device_terms):
            summary_stats["devices"] += 1
        elif not asset_type or asset_type == "unknown":
            summary_stats["unknown"] += 1

        # Count by status
        if status == "discovered":
            summary_stats["discovered"] += 1
        elif status == "pending":
            summary_stats["pending"] += 1

    return summary_stats


def _find_last_updated(asset_dicts: List[Dict[str, Any]]) -> Optional[str]:
    """Find the most recent updated_at timestamp."""
    last_updated = None
    for asset_dict in asset_dicts:
        updated_at = asset_dict.get("updated_at")
        if updated_at and (not last_updated or updated_at > last_updated):
            last_updated = updated_at
    return last_updated
