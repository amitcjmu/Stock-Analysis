"""
Base Field Mapping Generator

Contains core functionality and base class for field mapping generation.

🤖 Generated with Claude Code (CC)

Co-Authored-By: Claude <noreply@anthropic.com>
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class FieldMappingGeneratorBase:
    """Base class for field mapping generation functionality"""

    def __init__(self, flow_instance):
        """Initialize with reference to the main flow instance"""
        self.flow = flow_instance
        self.logger = logger

    def _get_current_timestamp(self) -> str:
        """Get current timestamp as ISO string"""
        from datetime import datetime

        return datetime.utcnow().isoformat()

    def _validate_field_mapping(self, mapping: Dict[str, Any]) -> bool:
        """Validate a single field mapping"""
        try:
            required_fields = ["source_field", "target_field"]

            for field in required_fields:
                if not mapping.get(field):
                    return False

            return True

        except Exception:
            return False

    def _normalize_field_name(self, field_name: str) -> str:
        """Normalize field name for mapping"""
        try:
            # Convert to lowercase and replace spaces/special chars with underscores
            normalized = field_name.lower().replace(" ", "_").replace("-", "_")
            # Remove special characters except underscores
            import re

            normalized = re.sub(r"[^a-zA-Z0-9_]", "_", normalized)
            # Remove multiple consecutive underscores
            normalized = re.sub(r"_+", "_", normalized)
            # Remove leading/trailing underscores
            normalized = normalized.strip("_")
            return normalized

        except Exception:
            return field_name

    def _get_valid_asset_fields(self) -> set:
        """Get list of valid Asset model fields for mapping validation"""
        return {
            # Basic identifiers
            "name",
            "asset_name",
            "hostname",
            "asset_type",
            "description",
            # Network information
            "ip_address",
            "fqdn",
            "mac_address",
            # Location and environment
            "environment",
            "location",
            "datacenter",
            "rack_location",
            "availability_zone",
            # Technical specifications
            "operating_system",
            "os_version",
            "cpu_cores",
            "memory_gb",
            "storage_gb",
            # Business information
            "business_owner",
            "technical_owner",
            "department",
            "application_name",
            "technology_stack",
            "criticality",
            "business_criticality",
            # Migration assessment
            "six_r_strategy",
            "migration_priority",
            "migration_complexity",
            "migration_wave",
            "sixr_ready",
            # Status fields
            "status",
            "migration_status",
            # JSON fields that can accept any data
            "custom_attributes",
            "technical_details",
            "dependencies",
            "related_assets",
        }

    def _map_common_field_names(self, source_field: str) -> str:
        """Map common field names to Asset model fields"""
        # Normalize the source field first
        normalized = self._normalize_field_name(source_field)

        # Common field mappings
        common_mappings = {
            # Server/Host mappings
            "server_name": "name",
            "host": "hostname",
            "host_name": "hostname",
            "device_name": "name",
            "machine_name": "name",
            "computer_name": "name",
            # IP/Network mappings
            "ip": "ip_address",
            "ipaddress": "ip_address",
            "ip_addr": "ip_address",
            "primary_ip": "ip_address",
            # OS mappings
            "os": "operating_system",
            "os_name": "operating_system",
            "operating_system_name": "operating_system",
            "os_ver": "os_version",
            "operating_system_version": "os_version",
            # CPU/Memory/Storage mappings
            "cpu": "cpu_cores",
            "vcpu": "cpu_cores",
            "cores": "cpu_cores",
            "processors": "cpu_cores",
            "memory": "memory_gb",
            "ram": "memory_gb",
            "memory_size": "memory_gb",
            "ram_gb": "memory_gb",
            "disk": "storage_gb",
            "storage": "storage_gb",
            "disk_size": "storage_gb",
            "hard_disk": "storage_gb",
            # Environment mappings
            "env": "environment",
            "environment_name": "environment",
            "site": "location",
            "data_center": "datacenter",
            "dc": "datacenter",
            # Owner mappings
            "owner": "business_owner",
            "business_contact": "business_owner",
            "technical_contact": "technical_owner",
            "it_owner": "technical_owner",
            "dept": "department",
            "app": "application_name",
            "application": "application_name",
            # Type mappings
            "type": "asset_type",
            "device_type": "asset_type",
            "machine_type": "asset_type",
            # Priority/Criticality mappings
            "priority": "migration_priority",
            "critical": "criticality",
            "business_critical": "business_criticality",
            "importance": "criticality",
        }

        # Check if normalized field matches any common mapping
        if normalized in common_mappings:
            return common_mappings[normalized]

        # Check if the normalized field is already a valid asset field
        valid_fields = self._get_valid_asset_fields()
        if normalized in valid_fields:
            return normalized

        # Return UNMAPPED for fields without valid targets
        return "UNMAPPED"

    def _suggest_target_field(self, source_field: str, analysis: Dict[str, Any]) -> str:
        """Suggest target field based on source field and analysis"""
        try:
            # First try to map common field names
            target = self._map_common_field_names(source_field)

            # If we got a valid mapping, return it
            if target != "UNMAPPED":
                return target

            # For unmapped fields, check if they might fit in custom_attributes
            # Fields with complex data or non-standard names go to custom_attributes
            sample_value = analysis.get("sample_value")
            if sample_value and (
                isinstance(sample_value, (dict, list)) or len(str(sample_value)) > 500
            ):
                return "custom_attributes"

            # Default to UNMAPPED for truly unmappable fields
            return "UNMAPPED"

        except Exception as e:
            self.logger.warning(
                f"Error suggesting target field for {source_field}: {e}"
            )
            return "UNMAPPED"
