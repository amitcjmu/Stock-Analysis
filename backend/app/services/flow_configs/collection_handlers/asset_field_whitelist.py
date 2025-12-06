"""
Asset Field Whitelist Configuration

Issue #1260: Extracted from asset_handlers.py to keep under 400 lines.
Defines mapping from questionnaire response fields to Asset model columns.
"""

# Comprehensive Whitelist (Issue #980 - Critical Bug Fix)
# Expanded from 10 fields to ~55 fields to cover all Asset model columns
# that can be populated via questionnaire responses
ASSET_FIELD_WHITELIST = {
    # === IDENTIFICATION FIELDS ===
    "name": "name",
    "asset_name": "asset_name",
    "hostname": "hostname",
    "asset_type": "asset_type",
    "description": "description",
    "fqdn": "fqdn",
    # === BUSINESS CONTEXT FIELDS ===
    "environment": "environment",
    "business_criticality": "business_criticality",
    "business_owner": "business_owner",
    "business_unit": "business_unit",
    "department": "department",
    "application_name": "application_name",
    "application_type": "application_type",
    "server_role": "server_role",
    # === TECHNOLOGY STACK FIELDS ===
    "technology_stack": "technology_stack",
    "operating_system": "operating_system",
    "operating_system_version": "operating_system",  # Alias for backward compat
    "os_version": "os_version",
    "database_type": "database_type",
    "database_version": "database_version",
    # === INFRASTRUCTURE FIELDS ===
    "cpu_cores": "cpu_cores",
    "memory_gb": "memory_gb",
    "storage_gb": "storage_gb",
    "storage_used_gb": "storage_used_gb",
    "storage_free_gb": "storage_free_gb",
    "database_size_gb": "database_size_gb",
    "virtualization_platform": "virtualization_platform",
    "virtualization_type": "virtualization_type",
    # === NETWORK FIELDS ===
    "ip_address": "ip_address",
    "mac_address": "mac_address",
    # === LOCATION FIELDS ===
    "datacenter": "datacenter",
    "location": "location",
    "rack_location": "rack_location",
    "availability_zone": "availability_zone",
    "security_zone": "security_zone",
    # === COST & PERFORMANCE FIELDS ===
    "current_monthly_cost": "current_monthly_cost",
    "annual_cost_estimate": "annual_cost_estimate",
    "estimated_cloud_cost": "estimated_cloud_cost",
    "cpu_utilization_percent": "cpu_utilization_percent",
    "memory_utilization_percent": "memory_utilization_percent",
    "network_throughput_mbps": "network_throughput_mbps",
    "disk_iops": "disk_iops",
    # === ASSESSMENT FIELDS ===
    "assessment_readiness": "assessment_readiness",
    "assessment_readiness_score": "assessment_readiness_score",
    "migration_complexity": "migration_complexity",
    "migration_priority": "migration_priority",
    "six_r_strategy": "six_r_strategy",
    "wave_number": "wave_number",
    "business_logic_complexity": "business_logic_complexity",
    "configuration_complexity": "configuration_complexity",
    "change_tolerance": "change_tolerance",
    "data_volume_characteristics": "data_volume_characteristics",
    "user_load_patterns": "user_load_patterns",
    # === DATA CLASSIFICATION & COMPLIANCE ===
    "application_data_classification": "application_data_classification",
    "pii_flag": "pii_flag",
    # === LIFECYCLE & EOL FIELDS ===
    "eol_date": "eol_date",
    "eol_risk_level": "eol_risk_level",
    "eol_technology_assessment": "eol_technology_assessment",
    "lifecycle": "lifecycle",
    # === BACKUP & RESILIENCE ===
    "backup_policy": "backup_policy",
    # === DISCOVERY METADATA ===
    "discovery_source": "discovery_source",
    "discovery_method": "discovery_method",
}

# Fields that go into technical_details JSONB column
TECHNICAL_DETAIL_FIELDS = [
    "architecture_pattern",
    "availability_requirements",
    "data_quality",
    "integration_complexity",
    "api_endpoints",
    "monitoring_enabled",
    "logging_enabled",
]

# Fields that go into custom_attributes JSONB column
CUSTOM_ATTRIBUTE_FIELDS = [
    "stakeholder_impact",
    "vm_type",
    "custom_tags",
    "notes",
]
