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

    CRITICAL: name and asset_name are the same thing - use either one
    application_name is metadata only (which app the asset belongs to), NOT for naming
    hostname is optional and NOT applicable for applications/components

    Tries multiple fields in order of preference:
    1. name (explicit)
    2. asset_name (same as name)
    3. hostname (only for applicable asset types: servers, databases, network devices)
    4. server_name (only for applicable asset types)
    5. fallback with row number if available
    """
    # Try name or asset_name first (they're the same thing)
    name = data.get("name") or data.get("asset_name")
    if name:
        return str(name).strip()

    # Only use hostname for asset types where it's applicable
    # NOT for applications or components
    asset_type = data.get("asset_type", "").lower()
    if asset_type not in ("application", "component", "components"):
        # Try hostname (common for servers, databases, network devices)
        if data.get("hostname"):
            return str(data["hostname"]).strip()

        # Try server_name
        if data.get("server_name"):
            return str(data["server_name"]).strip()

    # Fallback with row number if available
    if data.get("row_number"):
        return f"Asset-{data['row_number']}"

    # Last resort
    return "Unknown Asset"


def convert_numeric_fields(asset_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert numeric string fields to proper numeric types.

    Uses the comprehensive NUMERIC_FIELD_CONVERTERS mapping which includes
    safe NaN/Infinity checks per memory [[memory:10700746]].

    Returns a dictionary of converted numeric fields ready for asset creation.
    """
    converted = {}

    # Use comprehensive NUMERIC_FIELD_CONVERTERS for all numeric fields
    for field_name, converter_func in NUMERIC_FIELD_CONVERTERS.items():
        if field_name in asset_data and asset_data[field_name] is not None:
            converted_value = converter_func(asset_data[field_name])
            if converted_value is not None:
                converted[field_name] = converted_value

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
    """Convert value to float with safe error handling and NaN/Infinity checks."""
    if value is None or value == "":
        return default
    try:
        result = float(str(value))
        # Check for NaN/Infinity - not valid JSON values
        if math.isnan(result) or math.isinf(result):
            logger.warning(
                f"NaN/Infinity detected in float conversion: '{value}', "
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
    # FLOAT fields - System metrics
    "memory_gb": safe_float_convert,
    "storage_gb": safe_float_convert,
    "storage_free_gb": safe_float_convert,
    "storage_used_gb": safe_float_convert,
    # FLOAT fields - Performance metrics
    "cpu_utilization_percent": safe_float_convert,
    "memory_utilization_percent": safe_float_convert,
    "cpu_utilization_percent_max": safe_float_convert,
    "memory_utilization_percent_max": safe_float_convert,
    # FLOAT fields - Network and I/O
    "disk_iops": safe_float_convert,
    "network_throughput_mbps": safe_float_convert,
    # FLOAT fields - Database
    "database_size_gb": safe_float_convert,
    # FLOAT fields - Assessment and quality scores
    "completeness_score": safe_float_convert,
    "quality_score": safe_float_convert,
    "confidence_score": safe_float_convert,
    "complexity_score": safe_float_convert,
    "assessment_readiness_score": safe_float_convert,
    # FLOAT fields - Cost estimates
    "current_monthly_cost": safe_float_convert,
    "estimated_cloud_cost": safe_float_convert,
    "annual_cost_estimate": safe_float_convert,
}


# VARCHAR field length limits from database schema
# CC: CRITICAL - Prevents StringDataRightTruncationError during conflict resolution (Issue #921)
# PostgreSQL VARCHAR(n) limits by character count (not bytes), matching Python len()
# No safety margin needed - exact limits prevent unnecessary data loss
VARCHAR_FIELD_LIMITS = {
    # SMALL_STRING_LENGTH = 50
    "asset_type": 50,
    "status": 50,
    "source_phase": 50,
    "current_phase": 50,
    "rack_location": 50,
    "six_r_strategy": 50,
    "migration_status": 50,
    "assessment_readiness": 50,
    "environment": 50,
    # MEDIUM_STRING_LENGTH = 100
    "location": 100,
    "datacenter": 100,
    "department": 100,
    "business_owner": 100,
    "technical_owner": 100,
    "os_version": 100,
    "fqdn": 100,
    "business_criticality": 100,
    "criticality": 100,
    "technology_stack": 100,
    # LARGE_STRING_LENGTH = 255
    "name": 255,
    "asset_name": 255,
    "hostname": 255,
    "application_name": 255,
    "operating_system": 255,
}


def truncate_string_to_limit(field_name: str, value: str, limit: int) -> str:
    """
    Truncate string value to fit VARCHAR database constraint.

    Prevents StringDataRightTruncationError by enforcing field length limits
    during asset updates and conflict resolution.

    Args:
        field_name: Name of the field (for logging)
        value: String value to truncate
        limit: Maximum allowed length

    Returns:
        Truncated string if necessary, original value if within limit
    """
    if len(value) <= limit:
        return value

    truncated = value[:limit]

    # Only add ellipsis to log output if strings exceed display limit
    log_display_limit = 50
    original_display = (
        f"{value[:log_display_limit]}..." if len(value) > log_display_limit else value
    )
    truncated_display = (
        f"{truncated[:log_display_limit]}..."
        if len(truncated) > log_display_limit
        else truncated
    )

    logger.warning(
        f"⚠️ Truncated {field_name} from {len(value)} to {limit} chars: "
        f"'{original_display}' → '{truncated_display}'"
    )
    return truncated


def convert_single_field_value(field_name: str, raw_value):
    """
    Convert a single field value to proper type based on field name.

    CC: Fixes production bug where CSV imports provide string values
    but database expects typed values (e.g., cpu_cores='8' as INTEGER).

    CC: Issue #921 - Added VARCHAR truncation to prevent StringDataRightTruncationError
    during conflict resolution when merged field values exceed database constraints.

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

    # CC FIX Issue #921: Truncate VARCHAR fields to prevent database constraint violations
    # This fixes StringDataRightTruncationError during conflict resolution when users
    # select verbose field values from "new" asset that exceed VARCHAR limits
    if field_name in VARCHAR_FIELD_LIMITS and isinstance(raw_value, str):
        limit = VARCHAR_FIELD_LIMITS[field_name]
        return truncate_string_to_limit(field_name, raw_value, limit)

    # For other fields, return as-is
    return raw_value
