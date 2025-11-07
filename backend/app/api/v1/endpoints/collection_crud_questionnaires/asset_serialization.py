"""
Asset serialization utilities for collection questionnaires.
Functions for analyzing and extracting asset data for questionnaire generation.
"""

import logging
from typing import List, Optional, Tuple

from app.models.asset import Asset
from app.models.collection_flow import CollectionFlow

logger = logging.getLogger(__name__)


def _suggest_field_mapping(field_name: str) -> str:
    """Suggest potential mapping for unmapped field."""
    field_lower = field_name.lower()
    mappings = {
        "app": "application_name",
        "application": "application_name",
        "server": "hostname",
        "host": "hostname",
        "ip": "ip_address",
        "owner": "business_owner",
        "tech_owner": "technical_owner",
        "tech_lead": "technical_owner",
        "os": "operating_system",
        "env": "environment",
        "environment": "environment",
        "location": "location",
        "dc": "datacenter",
        "data_center": "datacenter",
        "cpu": "cpu_cores",
        "memory": "memory_gb",
        "ram": "memory_gb",
        "storage": "storage_gb",
        "disk": "storage_gb",
        "criticality": "criticality",
        "priority": "migration_priority",
        "complexity": "migration_complexity",
        "strategy": "six_r_strategy",
        "6r": "six_r_strategy",
    }
    for key, value in mappings.items():
        if key in field_lower:
            return value
    return "custom_attribute"


def _get_asset_raw_data_safely(asset, asset_id_str: str) -> tuple:
    """Safely extract raw_data and field_mappings from asset."""
    try:
        raw_data = getattr(asset, "raw_data", {}) or {}
        if not isinstance(raw_data, dict):
            logger.debug(
                f"Asset {asset_id_str} raw_data is {type(raw_data)}, using empty dict"
            )
            raw_data = {}

        field_mappings = getattr(asset, "field_mappings_used", {}) or {}
        if not isinstance(field_mappings, dict):
            logger.debug(
                f"Asset {asset_id_str} field_mappings is {type(field_mappings)}, using empty dict"
            )
            field_mappings = {}
    except Exception as e:
        logger.warning(f"Error processing asset {asset_id_str} data: {e}")
        raw_data = {}
        field_mappings = {}

    return raw_data, field_mappings


def _find_unmapped_attributes(raw_data: dict, field_mappings: dict) -> List[dict]:
    """Find unmapped attributes in raw data."""
    unmapped = []
    if raw_data:
        mapped_fields = set(field_mappings.values()) if field_mappings else set()
        for key, value in raw_data.items():
            if key not in mapped_fields and value:
                unmapped.append(
                    {
                        "field": key,
                        "value": str(value)[:100],  # Truncate long values
                        "potential_mapping": _suggest_field_mapping(key),
                    }
                )
    return unmapped


def _get_selected_application_info(
    flow: CollectionFlow, existing_assets: List[Asset]
) -> tuple[Optional[str], Optional[str]]:
    """Extract selected application info from flow config."""
    if not (
        flow.collection_config
        and flow.collection_config.get("selected_application_ids")
    ):
        return None, None

    selected_app_ids = flow.collection_config["selected_application_ids"]
    if not selected_app_ids:
        return None, None

    selected_id = selected_app_ids[0]
    for asset in existing_assets:
        if str(asset.id) == selected_id:
            return asset.name or asset.application_name, selected_id
    return None, selected_id


def _analyze_selected_assets(existing_assets: List[Asset]) -> Tuple[List[dict], dict]:
    """Analyze selected assets and extract comprehensive analysis."""
    from app.api.v1.endpoints.collection_crud_questionnaires.eol_detection import (
        _determine_eol_status,
    )
    from app.api.v1.endpoints.collection_crud_questionnaires.gap_detection import (
        _check_missing_critical_fields,
        _assess_data_quality,
    )

    selected_assets = []
    asset_analysis = {
        "total_assets": 0,
        "assets_with_gaps": [],
        "unmapped_attributes": {},
        "failed_mappings": {},
        "missing_critical_fields": {},
        "data_quality_issues": {},
    }

    for asset in existing_assets:
        asset_id_str = str(asset.id)

        # Extract OS and tech stack for EOL determination
        operating_system = getattr(asset, "operating_system", None) or ""
        os_version = getattr(asset, "os_version", None) or ""
        technology_stack = getattr(asset, "technology_stack", [])

        # Determine EOL status for intelligent option ordering
        eol_technology = _determine_eol_status(
            operating_system, os_version, technology_stack
        )

        selected_assets.append(
            {
                "id": asset_id_str,  # CRITICAL: Use "id" not "asset_id" - section_builders.py expects "id" key
                "asset_name": asset.name or getattr(asset, "application_name", None),
                "asset_type": getattr(asset, "asset_type", "application"),
                "criticality": getattr(asset, "criticality", "unknown"),
                "environment": getattr(asset, "environment", "unknown"),
                "technology_stack": technology_stack,
                # CRITICAL: Add OS data for OS-aware questionnaire generation
                "operating_system": operating_system,
                "os_version": os_version,
                # CRITICAL: Add EOL status for security vulnerabilities intelligent ordering
                "eol_technology": eol_technology,
            }
        )

        raw_data, field_mappings = _get_asset_raw_data_safely(asset, asset_id_str)

        unmapped = _find_unmapped_attributes(raw_data, field_mappings)
        if unmapped:
            asset_analysis["unmapped_attributes"][asset_id_str] = unmapped

        mapping_status = getattr(asset, "mapping_status", None)
        if mapping_status and mapping_status != "complete":
            asset_analysis["failed_mappings"][asset_id_str] = {
                "status": mapping_status,
                "reason": "Incomplete field mapping during import",
            }

        missing_fields, existing_values = _check_missing_critical_fields(asset)
        if missing_fields:
            asset_analysis["missing_critical_fields"][asset_id_str] = missing_fields
            # Store existing values for pre-fill (e.g., operating_system for verification)
            if existing_values:
                if "existing_field_values" not in asset_analysis:
                    asset_analysis["existing_field_values"] = {}
                asset_analysis["existing_field_values"][asset_id_str] = existing_values
            asset_analysis["assets_with_gaps"].append(asset_id_str)

        quality_issues = _assess_data_quality(asset)
        if quality_issues:
            asset_analysis["data_quality_issues"][asset_id_str] = quality_issues

    asset_analysis["total_assets"] = len(selected_assets)
    return selected_assets, asset_analysis
