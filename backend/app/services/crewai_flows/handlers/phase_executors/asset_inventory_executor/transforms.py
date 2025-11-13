"""
Asset Inventory Executor - Transform Methods
Contains all data transformation methods for converting raw records to assets.

CC: Transform operations for asset creation
"""

import logging
from typing import Dict, Any

from app.models.data_import.core import RawImportRecord

from .type_converters import parse_asset_tags, parse_boolean
from .field_mapping_utils import (
    apply_field_mapping,
    get_mapped_value,
    classify_asset_type,
)

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
            "pii_flag": parse_boolean(asset_data_source.get("pii_flag")),
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
            "has_saas_replacement": parse_boolean(
                asset_data_source.get("has_saas_replacement")
            ),
            "risk_level": asset_data_source.get("risk_level"),
            "tshirt_size": asset_data_source.get("tshirt_size"),
            "proposed_treatmentplan_rationale": asset_data_source.get(
                "proposed_treatmentplan_rationale"
            )
            or asset_data_source.get("proposed_rationale"),
            # Cost and backup
            "annual_cost_estimate": asset_data_source.get("annual_cost_estimate"),
            # Asset tags - convert semicolon-separated string to array
            "asset_tags": parse_asset_tags(asset_data_source.get("asset_tags")),
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
        # Empty lists are truthy and will be kept (e.g., asset_tags=[])
        cleaned_data = {k: v for k, v in asset_data.items() if v is not None}

        logger.debug(
            f"🔄 Transformed record {record.row_number} to asset '{name}' (type: {asset_type})"
        )
        return cleaned_data

    except Exception as e:
        logger.error(f"❌ Failed to transform raw record {record.row_number}: {e}")
        return None


__all__ = ["transform_raw_record_to_asset"]
