"""
Asset serialization utilities for collection questionnaires.
Functions for analyzing and extracting asset data for questionnaire generation.
"""

import logging
from typing import Any, List, Optional, Tuple

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


def _build_asset_dict(asset: Asset, eol_technology: Optional[str]) -> dict:
    """Build asset dictionary with all required fields.

    Extracted helper to reduce complexity in _analyze_selected_assets.
    """
    asset_id_str = str(asset.id)
    operating_system = getattr(asset, "operating_system", None) or ""
    os_version = getattr(asset, "os_version", None) or ""
    technology_stack = getattr(asset, "technology_stack", [])

    return {
        "id": asset_id_str,  # CRITICAL: Use "id" not "asset_id" - section_builders.py expects "id" key
        "asset_id": asset_id_str,  # Also include asset_id for compatibility
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


def _process_asset_for_analysis(asset: Asset, asset_analysis: dict) -> None:
    """Process single asset to populate analysis data.

    Extracted helper to reduce complexity in _analyze_selected_assets.
    """
    asset_id_str = str(asset.id)

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


async def _fetch_gaps_from_database(
    flow_id: str, db: Any, asset_analysis: dict
) -> dict:
    """Fetch gaps from collection_data_gaps table (Issue #980).

    Extracted async helper to reduce complexity in _analyze_selected_assets.

    Args:
        flow_id: Collection flow UUID string
        db: Database session
        asset_analysis: Mutable dict to populate with quality issues

    Returns:
        Dictionary mapping asset_id_str to list of gap field names
    """
    from uuid import UUID
    from sqlalchemy import select
    from app.models.collection_flow import CollectionFlow
    from app.models.collection_data_gap import CollectionDataGap

    # Get collection flow internal ID
    flow_result = await db.execute(
        select(CollectionFlow.id).where(CollectionFlow.flow_id == UUID(flow_id))
    )
    collection_flow_id = flow_result.scalar_one_or_none()

    if not collection_flow_id:
        logger.warning(f"Collection flow {flow_id} not found for gap analysis")
        return {}

    # Fetch pending gaps from Issue #980's gap detection
    gap_result = await db.execute(
        select(CollectionDataGap).where(
            CollectionDataGap.collection_flow_id == collection_flow_id,
            CollectionDataGap.resolution_status == "pending",
        )
    )
    gaps = gap_result.scalars().all()

    logger.info(
        f"✅ FIX 0.5: Loaded {len(gaps)} gaps from Issue #980 gap detection (collection_data_gaps table)"
    )

    # Group gaps by asset_id
    gaps_by_asset = {}
    for gap in gaps:
        asset_id_str = str(gap.asset_id)
        if asset_id_str not in gaps_by_asset:
            gaps_by_asset[asset_id_str] = []
        gaps_by_asset[asset_id_str].append(gap.field_name)

        # Also track quality issues if confidence is low
        if gap.confidence_score and gap.confidence_score < 0.7:
            if asset_id_str not in asset_analysis["data_quality_issues"]:
                asset_analysis["data_quality_issues"][asset_id_str] = {}
            asset_analysis["data_quality_issues"][asset_id_str][
                "confidence"
            ] = gap.confidence_score

    return gaps_by_asset


async def _analyze_selected_assets(
    existing_assets: List[Asset],
    flow_id: Optional[str] = None,
    db: Optional[Any] = None,
) -> Tuple[List[dict], dict]:
    """Analyze selected assets using Issue #980's intelligent gap detection.

    ✅ FIX 0.5 (Issue #980): Replace legacy gap detection with database-backed gap analysis.
    Reads from collection_data_gaps table instead of analyzing assets directly.

    Args:
        existing_assets: List of Asset objects to analyze
        flow_id: Collection flow ID (required for gap detection integration)
        db: Database session (required for gap detection integration)

    Returns:
        Tuple of (selected_assets, asset_analysis) with gap data from Issue #980
    """
    from app.api.v1.endpoints.collection_crud_questionnaires.eol_detection import (
        _determine_eol_status,
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

    # Process each asset to build selected_assets list and initial analysis
    for asset in existing_assets:
        # Eagerly load SQLAlchemy attributes to avoid MissingGreenlet errors
        # getattr() forces attribute loading while session is active
        operating_system = getattr(asset, "operating_system", None) or ""
        os_version = getattr(asset, "os_version", None) or ""
        technology_stack = getattr(asset, "technology_stack", [])

        # Determine EOL status for intelligent option ordering
        eol_technology = _determine_eol_status(
            operating_system, os_version, technology_stack
        )

        # Build asset dictionary with helper function
        asset_dict = _build_asset_dict(asset, eol_technology)
        selected_assets.append(asset_dict)

        # Process asset for analysis with helper function
        _process_asset_for_analysis(asset, asset_analysis)

    # ✅ FIX 0.5: Use Issue #980's gap detection instead of legacy code
    # Read from collection_data_gaps table (created by GapAnalyzer with 5 inspectors)
    if flow_id and db:
        # Use await instead of run_until_complete (we're already in async context)
        try:
            gaps_by_asset = await _fetch_gaps_from_database(flow_id, db, asset_analysis)

            # Populate missing_critical_fields from database gaps
            for asset_id_str, field_names in gaps_by_asset.items():
                if field_names:
                    asset_analysis["missing_critical_fields"][
                        asset_id_str
                    ] = field_names
                    if asset_id_str not in asset_analysis["assets_with_gaps"]:
                        asset_analysis["assets_with_gaps"].append(asset_id_str)

                    logger.info(
                        f"Asset {asset_id_str}: {len(field_names)} gaps from database: {field_names}"
                    )
        except Exception as e:
            logger.error(f"Failed to load gaps from database: {e}", exc_info=True)
            # Fallback: Continue without gap data rather than failing
    else:
        logger.warning(
            "⚠️ FIX 0.5: flow_id or db not provided - cannot use Issue #980 gap detection. "
            "Questionnaire generation will have NO gap data!"
        )

    asset_analysis["total_assets"] = len(selected_assets)
    return selected_assets, asset_analysis
