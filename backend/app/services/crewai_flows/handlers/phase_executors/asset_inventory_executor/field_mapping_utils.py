"""
Asset Inventory Executor - Field Mapping Utilities
Contains utility functions for field mapping and asset type classification.

CC: Extracted from transforms.py to maintain <400 line limit per file
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def apply_field_mapping(
    asset_data_source: Dict[str, Any],
    source_field: str,
    target_field: str,
    field_mappings: Dict[str, str],
    default: Any = None,
) -> Any:
    """Apply field mapping transformation if approved mapping exists.

    Args:
        asset_data_source: Source data dictionary
        source_field: Name of the source field to map from
        target_field: Name of the target field to map to
        field_mappings: Dict of approved mappings (source -> target)
        default: Default value if no mapping found

    Returns:
        Transformed value or default
    """
    # Check if there's an approved mapping for this source field
    if field_mappings.get(source_field) == target_field:
        # Mapping exists and matches - use the source field value
        value = asset_data_source.get(source_field, default)
        logger.debug(
            f"📋 Applied field mapping: {source_field} → {target_field} = {value}"
        )
        return value
    else:
        # No mapping - return default
        return default


def get_mapped_value(
    asset_data_source: Dict[str, Any],
    target_field: str,
    field_mappings: Dict[str, str],
    fallback_fields: list = None,
    default: Any = None,
) -> Any:
    """Get value for a target field by applying field mappings with reverse lookup.

    Args:
        asset_data_source: Source data dictionary
        target_field: Name of the target field to get value for
        field_mappings: Dict of approved mappings (source -> target)
        fallback_fields: List of fallback field names to try if no mapping found
        default: Default value if no mapping found and target field doesn't exist

    Returns:
        Mapped value, fallback value, or default
    """
    # First, try to find a source field that maps to this target
    for source_field, mapped_target in field_mappings.items():
        if mapped_target == target_field:
            # Found a mapping! Use the source field value
            value = asset_data_source.get(source_field)
            if value is not None:
                logger.debug(
                    f"📋 Applied field mapping: {source_field} → {target_field} = {value}"
                )
                return value

    # No mapping found, try direct lookup
    value = asset_data_source.get(target_field)
    if value is not None:
        return value

    # Try fallback fields if provided
    if fallback_fields:
        for fallback_field in fallback_fields:
            value = asset_data_source.get(fallback_field)
            if value is not None:
                return value

    # Not found, return default
    return default


def flatten_cleansed_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Flatten nested cleansed_data structures.

    Args:
        data: Dictionary that may contain nested cleansed_data structures

    Returns:
        Flattened dictionary with all cleansed_data content at top level
    """
    if not isinstance(data, dict):
        return {}

    result = {}
    for key, value in data.items():
        if key == "cleansed_data" and isinstance(value, dict):
            # Recursively flatten nested cleansed_data
            result.update(flatten_cleansed_data(value))
        else:
            result[key] = value

    return result


def classify_asset_type(asset_data_source: Dict[str, Any]) -> str:
    """
    Intelligently classify asset type based on available data.

    Args:
        asset_data_source: Dictionary containing asset data (cleansed or raw)

    Returns:
        String representing the asset type classification
    """
    # CRITICAL FIX: Flatten nested cleansed_data structures before classification
    flattened_data = flatten_cleansed_data(asset_data_source)

    # Use resolved_name if available, otherwise check multiple name fields
    resolved_name = str(flattened_data.get("resolved_name", "")).lower()
    name = str(flattened_data.get("name", "")).lower()
    hostname = str(flattened_data.get("hostname", "")).lower()
    server_name = str(flattened_data.get("server_name", "")).lower()
    asset_name = str(flattened_data.get("asset_name", "")).lower()
    app_name = str(flattened_data.get("application_name", "")).lower()
    asset_type = str(flattened_data.get("type", "")).lower()

    # CRITICAL FIX: Check CI Type field with both common field names and case-insensitive matching
    ci_type = (
        str(flattened_data.get("CI Type", "")).lower()
        or str(flattened_data.get("ci_type", "")).lower()
        or str(flattened_data.get("CI_Type", "")).lower()
        or str(flattened_data.get("asset_type", "")).lower()
    )

    # Combine all name fields for comprehensive checking
    all_names = f"{resolved_name} {name} {hostname} {server_name} {asset_name} {app_name}".lower()

    # Add debug logging to track classification process
    has_os = bool(flattened_data.get("OS") or flattened_data.get("os"))
    logger.debug(
        f"🔍 Classifying asset: name='{name}', ci_type='{ci_type}', has_os={has_os}"
    )

    # CRITICAL FIX: Enhanced CI Type detection with better pattern matching
    # Priority 1: Check explicit CI Type first (most reliable for CMDB data)
    if ci_type:
        # Application detection
        if any(app_pattern in ci_type for app_pattern in ["application", "app"]):
            logger.debug(f"✅ Classified as 'application' via CI Type: '{ci_type}'")
            return "application"
        # Server detection
        elif any(srv_pattern in ci_type for srv_pattern in ["server", "srv"]):
            logger.debug(f"✅ Classified as 'server' via CI Type: '{ci_type}'")
            return "server"
        # Database detection
        elif any(db_pattern in ci_type for db_pattern in ["database", "db"]):
            logger.debug(f"✅ Classified as 'database' via CI Type: '{ci_type}'")
            return "database"
        # Bug #404 Fix: Network device detection - removed generic "device" to prevent
        # all assets with "device" in CI Type being classified as network devices
        # Use more specific patterns to only match actual network devices
        elif any(
            net_pattern in ci_type
            for net_pattern in [
                "network",
                "switch",
                "router",
                "firewall",
                "network_device",
                "net_device",
            ]
        ):
            logger.debug(f"✅ Classified as 'network' via CI Type: '{ci_type}'")
            return "network"  # Use valid AssetType enum value

    # Priority 2: Database detection (specific patterns)
    database_keywords = [
        "db",
        "database",
        "sql",
        "oracle",
        "mysql",
        "postgres",
        "mongodb",
        "cassandra",
        "redis",
        "mariadb",
        "mssql",
        "sqlite",
    ]
    if any(keyword in all_names for keyword in database_keywords):
        return "database"
    if any(keyword in asset_type for keyword in ["db", "database"]):
        return "database"

    # Priority 3: Application detection (enhanced patterns)
    application_keywords = [
        "app",
        "application",
        "service",
        "api",
        "web",
        "portal",
        "system",
        "platform",
        "tool",
        "suite",
        "software",
        "crm",
        "erp",
        "hr",
        "analytics",
        "email",
        "backup",
        "monitoring",
        "pipeline",
    ]
    if any(keyword in all_names for keyword in application_keywords):
        return "application"
    if flattened_data.get("application_name") or flattened_data.get("app_name"):
        return "application"

    # Priority 4: Network device detection
    network_keywords = [
        "switch",
        "router",
        "firewall",
        "gateway",
        "loadbalancer",
        "lb",
        "proxy",
        "vpn",
        "wifi",
        "access point",
        "hub",
    ]
    if any(keyword in all_names for keyword in network_keywords):
        return "network"  # Use valid AssetType enum value
    if any(keyword in asset_type for keyword in ["network", "switch", "router"]):
        return "network"  # Use valid AssetType enum value

    # Priority 5: Server detection (most conservative) - ENHANCED WITH FLATTENED DATA
    server_keywords = ["server", "srv", "host", "vm", "virtual", "node"]
    # CRITICAL FIX: Check for operating system with multiple field names (both 'OS' and 'operating_system')
    has_os = (
        flattened_data.get("os")
        or flattened_data.get("OS")
        or flattened_data.get("operating_system")
        or flattened_data.get("Operating System")
    )

    if any(keyword in all_names for keyword in server_keywords) or hostname or has_os:
        return "server"

    # Priority 6: Storage detection
    storage_keywords = ["storage", "san", "nas", "disk", "volume"]
    if any(keyword in all_names for keyword in storage_keywords):
        return "storage"

    logger.debug(f"⚠️ Using default classification 'other' for asset: '{name}'")
    return "other"  # Default fallback using valid AssetType enum value


__all__ = [
    "apply_field_mapping",
    "get_mapped_value",
    "flatten_cleansed_data",
    "classify_asset_type",
]
