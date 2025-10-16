"""
Asset Service Helper Module

Utility methods for asset name generation and data conversion.
Provides smart naming logic and type conversion with error handling.

CC: Helper utilities for asset service operations
"""

import logging
import uuid
from typing import Dict, Any

logger = logging.getLogger(__name__)


def get_smart_asset_name(data: Dict[str, Any]) -> str:
    """Generate unique asset name from available data with intelligent fallbacks"""
    # Try explicit name field first
    if data.get("name"):
        return str(data["name"]).strip()

    # Try asset_name field
    if data.get("asset_name"):
        return str(data["asset_name"]).strip()

    # Try hostname (most common for servers/infrastructure)
    if data.get("hostname"):
        return str(data["hostname"]).strip()

    # Try application_name (for applications)
    if data.get("application_name"):
        return str(data["application_name"]).strip()

    # Try primary_application
    if data.get("primary_application"):
        return str(data["primary_application"]).strip()

    # Try IP address as identifier
    if data.get("ip_address"):
        return f"Asset-{data['ip_address']}"

    # Last resort: generate unique name based on asset type and UUID
    asset_type = data.get("asset_type", "Asset").replace(" ", "-")
    unique_id = str(uuid.uuid4())[:8]  # Short UUID for readability
    return f"{asset_type}-{unique_id}"


def safe_int_convert(value, default=None):
    """Convert value to integer with safe error handling"""
    if value is None or value == "":
        return default
    try:
        return int(float(str(value)))  # Handle both int and float strings
    except (ValueError, TypeError):
        logger.warning(
            f"Failed to convert '{value}' to integer, using default {default}"
        )
        return default


def safe_float_convert(value, default=None):
    """Convert value to float with safe error handling"""
    if value is None or value == "":
        return default
    try:
        return float(str(value))
    except (ValueError, TypeError):
        logger.warning(f"Failed to convert '{value}' to float, using default {default}")
        return default


def convert_numeric_fields(asset_data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert all numeric fields with proper error handling."""
    return {
        # INTEGER fields
        "cpu_cores": safe_int_convert(asset_data.get("cpu_cores"), None),
        "migration_priority": safe_int_convert(asset_data.get("migration_priority"), 5),
        "migration_wave": safe_int_convert(asset_data.get("migration_wave"), None),
        # FLOAT fields
        "memory_gb": safe_float_convert(asset_data.get("memory_gb"), None),
        "storage_gb": safe_float_convert(asset_data.get("storage_gb"), None),
        "cpu_utilization_percent": safe_float_convert(
            asset_data.get("cpu_utilization_percent"), None
        ),
        "memory_utilization_percent": safe_float_convert(
            asset_data.get("memory_utilization_percent"), None
        ),
        "disk_iops": safe_float_convert(asset_data.get("disk_iops"), None),
        "network_throughput_mbps": safe_float_convert(
            asset_data.get("network_throughput_mbps"), None
        ),
        "completeness_score": safe_float_convert(
            asset_data.get("completeness_score"), None
        ),
        "quality_score": safe_float_convert(asset_data.get("quality_score"), None),
        "confidence_score": safe_float_convert(
            asset_data.get("confidence_score"), None
        ),
        "current_monthly_cost": safe_float_convert(
            asset_data.get("current_monthly_cost"), None
        ),
        "estimated_cloud_cost": safe_float_convert(
            asset_data.get("estimated_cloud_cost"), None
        ),
        "assessment_readiness_score": safe_float_convert(
            asset_data.get("assessment_readiness_score"), None
        ),
    }


# Type conversion mapping for single field conversion
# CC: CRITICAL - Used during conflict resolution to convert CSV string values
NUMERIC_FIELD_CONVERTERS = {
    # INTEGER fields
    "cpu_cores": safe_int_convert,
    "migration_priority": safe_int_convert,
    "migration_wave": safe_int_convert,
    # FLOAT fields
    "memory_gb": safe_float_convert,
    "storage_gb": safe_float_convert,
    "cpu_utilization_percent": safe_float_convert,
    "memory_utilization_percent": safe_float_convert,
    "disk_iops": safe_float_convert,
    "network_throughput_mbps": safe_float_convert,
    "completeness_score": safe_float_convert,
    "quality_score": safe_float_convert,
    "confidence_score": safe_float_convert,
    "current_monthly_cost": safe_float_convert,
    "estimated_cloud_cost": safe_float_convert,
    "assessment_readiness_score": safe_float_convert,
}


def convert_single_field_value(field_name: str, raw_value):
    """
    Convert a single field value to proper type based on field name.

    CC: Fixes production bug where CSV imports provide string values
    but database expects typed values (e.g., cpu_cores='8' as INTEGER).

    Args:
        field_name: Name of the field
        raw_value: Raw value from data source (may be string)

    Returns:
        Properly typed value for database insertion
    """
    if raw_value is None or raw_value == "":
        return None

    # Apply type conversion if field is numeric
    if field_name in NUMERIC_FIELD_CONVERTERS:
        converter = NUMERIC_FIELD_CONVERTERS[field_name]
        return converter(raw_value, None)

    # For non-numeric fields, return as-is
    return raw_value
