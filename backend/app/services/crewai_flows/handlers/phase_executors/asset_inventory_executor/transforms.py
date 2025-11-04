"""
Asset Inventory Executor - Transform Methods
Contains all data transformation methods for converting raw records to assets.

CC: Transform operations for asset creation
"""

import logging
from typing import Dict, Any

from app.models.data_import.core import RawImportRecord

logger = logging.getLogger(__name__)


def transform_raw_record_to_asset(
    record: RawImportRecord,
    master_flow_id: str,
    discovery_flow_id: str = None,
    field_mappings: Dict[str, str] = None,
) -> Dict[str, Any]:
    """Transform a raw import record to asset data format.

    Args:
        record: Raw import record to transform
        master_flow_id: Master flow identifier
        discovery_flow_id: Discovery flow identifier
        field_mappings: Dict mapping source_field to target_field for transformations

    Returns:
        Asset data dictionary ready for AssetService.create_asset()
    """
    try:
        # CC: CRITICAL FIX - Handle field mappings correctly based on cleansing status
        # If cleansed_data has mappings_applied, use it directly (mappings already in lowercase)
        # Otherwise use raw_data with field_mappings parameter for mapping application
        cleansed_data: Dict[str, Any] = record.cleansed_data or {}
        raw_data: Dict[str, Any] = record.raw_data or {}

        # Check if cleansing phase already applied mappings
        mappings_already_applied = cleansed_data.get("mappings_applied", 0) > 0

        if mappings_already_applied:
            # Use cleansed data (mappings already applied, fields in lowercase)
            asset_data_source = cleansed_data
            # Don't use field_mappings parameter since they're already applied
            field_mappings_to_use = {}
            logger.debug(
                f"Using cleansed_data with {cleansed_data.get('mappings_applied')} mappings already applied"
            )
        else:
            # Use raw data and apply field_mappings
            asset_data_source = raw_data
            field_mappings_to_use = field_mappings or {}
            logger.debug(
                f"Using raw_data with {len(field_mappings_to_use)} field mappings to apply"
            )

        # Extract basic asset information with smart name resolution
        # CRITICAL FIX: Prioritize application_name over asset_name to avoid using
        # technical identifiers (serial numbers, UUIDs) as asset names
        name = (
            asset_data_source.get("name")
            or asset_data_source.get(
                "application_name"
            )  # Check application_name before asset_name
            or asset_data_source.get("hostname")
            or asset_data_source.get("server_name")
            or asset_data_source.get("asset_name")  # Demoted: only use as last resort
            or f"Asset-{record.row_number}"
        )

        # Determine asset type with intelligent classification
        # Pass the actual resolved name to ensure proper classification
        asset_data_for_classification = {**asset_data_source, "resolved_name": name}
        asset_type = classify_asset_type(asset_data_for_classification)

        # Build comprehensive asset data
        asset_data = {
            "name": str(name).strip(),
            "asset_type": asset_type,
            "description": asset_data_source.get(
                "description",
                f"Discovered asset from import row {record.row_number}",
            ),
            # Network information
            "hostname": asset_data_source.get("hostname"),
            "ip_address": asset_data_source.get("ip_address"),
            "fqdn": asset_data_source.get("fqdn"),
            # System information
            "operating_system": asset_data_source.get("operating_system"),
            "os_version": asset_data_source.get("os_version"),
            "environment": asset_data_source.get("environment", "Unknown"),
            # Physical/Virtual specifications
            "cpu_cores": asset_data_source.get("cpu_cores"),
            "memory_gb": asset_data_source.get("memory_gb"),
            "storage_gb": asset_data_source.get("storage_gb"),
            # Business context
            "business_owner": asset_data_source.get("business_owner")
            or asset_data_source.get("owner"),
            "technical_owner": asset_data_source.get("technical_owner"),
            "department": asset_data_source.get("department"),
            "criticality": asset_data_source.get("criticality", "Medium"),
            # Apply field mapping for business_criticality if approved mapping exists
            "business_criticality": (
                asset_data_source.get("business_criticality", "Medium")
                if mappings_already_applied
                else apply_field_mapping(
                    asset_data_source,
                    "criticality",
                    "business_criticality",
                    field_mappings_to_use,
                    default="Medium",
                )
            ),
            # Application information - CRITICAL FIX: Use field mappings correctly
            # If mappings already applied (cleansed_data), use direct lookup
            # Otherwise apply mappings from raw_data
            "application_name": (
                asset_data_source.get("application_name")
                or asset_data_source.get(
                    "name"
                )  # Cleansed data uses "name" for application_name
                if mappings_already_applied
                else get_mapped_value(
                    asset_data_source,
                    "application_name",
                    field_mappings_to_use,
                    fallback_fields=["app_name", "application", "name"],
                    default=None,
                )
            ),
            "technology_stack": get_mapped_value(
                asset_data_source,
                "technology_stack",
                field_mappings_to_use,
                fallback_fields=["tech_stack", "stack"],
                default=None,
            ),
            # Location information
            "location": asset_data_source.get("location"),
            "datacenter": asset_data_source.get("datacenter"),
            # CMDB Fields (PR #847) - NEW FIELDS
            # Business and organizational context
            "business_unit": asset_data_source.get("business_unit"),
            "vendor": asset_data_source.get("vendor"),
            # Application-specific fields
            "application_type": asset_data_source.get("application_type"),
            "lifecycle": asset_data_source.get("lifecycle"),
            "hosting_model": asset_data_source.get("hosting_model"),
            # Server-specific fields
            "server_role": asset_data_source.get("server_role"),
            "security_zone": asset_data_source.get("security_zone"),
            # Database-specific fields
            "database_type": asset_data_source.get("database_type"),
            "database_version": asset_data_source.get("database_version"),
            "database_size_gb": asset_data_source.get("database_size_gb"),
            # Compliance and security
            "pii_flag": asset_data_source.get("pii_flag"),
            "application_data_classification": asset_data_source.get(
                "application_data_classification"
            )
            or asset_data_source.get("data_classification"),
            # Performance metrics (max values)
            "cpu_utilization_percent_max": asset_data_source.get(
                "cpu_utilization_percent_max"
            )
            or asset_data_source.get("cpu_max_percent"),
            "memory_utilization_percent_max": asset_data_source.get(
                "memory_utilization_percent_max"
            )
            or asset_data_source.get("memory_max_percent"),
            "storage_free_gb": asset_data_source.get("storage_free_gb"),
            # Migration planning fields
            "has_saas_replacement": asset_data_source.get("has_saas_replacement"),
            "risk_level": asset_data_source.get("risk_level"),
            "tshirt_size": asset_data_source.get("tshirt_size"),
            "proposed_treatmentplan_rationale": asset_data_source.get(
                "proposed_treatmentplan_rationale"
            )
            or asset_data_source.get("proposed_rationale"),
            # Cost and backup
            "annual_cost_estimate": asset_data_source.get("annual_cost_estimate"),
            # Discovery metadata
            "discovery_source": "Discovery Flow Import",
            "raw_import_records_id": record.id if hasattr(record, "id") else None,
            # Flow association
            "master_flow_id": master_flow_id,
            "flow_id": master_flow_id,  # Backward compatibility
            "discovery_flow_id": discovery_flow_id,  # The actual discovery flow ID for proper association
            # Store complete raw data (preserve original for audit)
            "custom_attributes": asset_data_source,
            "raw_data": record.raw_data,  # Keep original raw data for audit trail
        }

        # Remove None values to avoid database issues
        cleaned_data = {k: v for k, v in asset_data.items() if v is not None}

        logger.debug(
            f"🔄 Transformed record {record.row_number} to asset '{name}' (type: {asset_type})"
        )
        return cleaned_data

    except Exception as e:
        logger.error(f"❌ Failed to transform raw record {record.row_number}: {e}")
        return None


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
        # Network device detection
        elif any(
            net_pattern in ci_type
            for net_pattern in ["network", "switch", "router", "firewall", "device"]
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
    "transform_raw_record_to_asset",
    "apply_field_mapping",
    "get_mapped_value",
    "flatten_cleansed_data",
    "classify_asset_type",
]
