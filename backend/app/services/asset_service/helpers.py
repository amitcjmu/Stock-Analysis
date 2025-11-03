"""
Helper utilities for AssetService.

Extracted to keep asset_service.py under 400 lines per project standards.
"""

import logging
import math
import uuid
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


def get_smart_asset_name(data: Dict[str, Any]) -> str:
    """
    Generate a smart asset name using fallback hierarchy.

    Tries multiple fields in order of preference:
    1. name (explicit)
    2. hostname
    3. server_name
    4. asset_name
    5. application_name
    6. fallback with row number if available
    """
    # Try name field first
    if data.get("name"):
        return str(data["name"]).strip()

    # Try hostname (common for servers)
    if data.get("hostname"):
        return str(data["hostname"]).strip()

    # Try server_name
    if data.get("server_name"):
        return str(data["server_name"]).strip()

    # Try asset_name field
    if data.get("asset_name"):
        return str(data["asset_name"]).strip()

    # Try application_name (for applications)
    if data.get("application_name"):
        return str(data["application_name"]).strip()

    # Fallback with row number if available
    if data.get("row_number"):
        return f"Asset-{data['row_number']}"

    # Last resort
    return "Unknown Asset"


def convert_numeric_fields(asset_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert numeric string fields to proper numeric types.

    Returns a dictionary of converted numeric fields ready for asset creation.
    """
    numeric_conversions = {
        "vcpu_cores": int,
        "memory_gb": float,
        "storage_gb": float,
        "network_bandwidth_mbps": float,
        "iops": int,
    }

    converted = {}
    for field, converter in numeric_conversions.items():
        if field in asset_data and asset_data[field]:
            try:
                converted[field] = converter(asset_data[field])
            except (ValueError, TypeError):
                logger.warning(
                    f"⚠️ Could not convert {field}={asset_data[field]} to {converter.__name__}"
                )

    return converted


async def extract_context_ids(
    asset_data: Dict[str, Any], context_info: Dict[str, Any]
) -> Tuple[uuid.UUID, uuid.UUID]:
    """
    Extract and validate client_account_id and engagement_id.

    Handles both string and UUID types from various sources.
    """
    # Try to get from asset_data first, then fall back to context_info
    client_id_str = asset_data.get("client_account_id") or context_info.get(
        "client_account_id"
    )
    engagement_id_str = asset_data.get("engagement_id") or context_info.get(
        "engagement_id"
    )

    if not client_id_str or not engagement_id_str:
        raise ValueError(
            f"Missing required context: client_account_id={client_id_str}, "
            f"engagement_id={engagement_id_str}"
        )

    # Convert to UUID if string
    try:
        if isinstance(client_id_str, str):
            client_id = uuid.UUID(client_id_str)
        else:
            client_id = client_id_str

        if isinstance(engagement_id_str, str):
            engagement_id = uuid.UUID(engagement_id_str)
        else:
            engagement_id = engagement_id_str

        return client_id, engagement_id

    except (ValueError, AttributeError) as e:
        raise ValueError(f"Invalid UUID format: {e}")


async def resolve_flow_ids(
    asset_data: Dict[str, Any], flow_id: Optional[str] = None
) -> Tuple[Optional[str], Optional[str], Optional[uuid.UUID], Optional[str]]:
    """
    Resolve and validate flow ID references.

    Returns:
        Tuple of (master_flow_id, discovery_flow_id, raw_import_records_id, effective_flow_id)
    """
    # Extract flow IDs from asset_data
    master_flow_id = asset_data.get("master_flow_id") or asset_data.get("flow_id")
    discovery_flow_id = asset_data.get("discovery_flow_id")

    # Get raw_import_records_id if available
    raw_import_records_id = asset_data.get("raw_import_records_id")
    if raw_import_records_id and isinstance(raw_import_records_id, str):
        try:
            raw_import_records_id = uuid.UUID(raw_import_records_id)
        except ValueError:
            logger.warning(
                f"Invalid raw_import_records_id format: {raw_import_records_id}"
            )
            raw_import_records_id = None

    # Determine effective flow ID (preference: master > discovery > provided)
    effective_flow_id = master_flow_id or discovery_flow_id or flow_id

    return master_flow_id, discovery_flow_id, raw_import_records_id, effective_flow_id


def safe_int_convert(value, default=None):
    """Convert value to integer with safe error handling."""
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
    """
    Convert value to float with safe error handling.

    Handles NaN and Infinity values to prevent JSON serialization errors
    at the Python → JavaScript boundary (API responses).

    Args:
        value: Value to convert to float
        default: Default value if conversion fails or result is NaN/Infinity

    Returns:
        Float value or default if conversion fails/invalid
    """
    if value is None or value == "":
        return default
    try:
        result = float(str(value))

        # CRITICAL: Check for NaN/Infinity before JSON serialization
        # These values cause JSON serialization errors in API responses
        if math.isnan(result) or math.isinf(result):
            logger.warning(
                f"NaN/Infinity detected in float conversion: {value}, "
                f"using default {default}"
            )
            return default

        return result
    except (ValueError, TypeError):
        logger.warning(f"Failed to convert '{value}' to float, using default {default}")
        return default


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

    # CC FIX: Do not attempt to convert booleans to numbers
    # Prevents True→1, False→0 incorrect conversions
    if isinstance(raw_value, bool):
        return raw_value

    # Apply type conversion if field is numeric
    if field_name in NUMERIC_FIELD_CONVERTERS:
        converter = NUMERIC_FIELD_CONVERTERS[field_name]
        return converter(raw_value, None)

    # For non-numeric fields, return as-is
    return raw_value
