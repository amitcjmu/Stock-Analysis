"""
Deduplication Module Constants

Field allowlists and never-merge lists for secure asset deduplication.
Defines which fields can be safely merged during asset updates.

CC: Field merge security configuration for asset deduplication
"""

from typing import Set

# ============================================================================
# FIELD MERGE ALLOWLIST - CRITICAL FOR SECURITY
# ============================================================================

# Fields that CAN be merged (safe to update)
DEFAULT_ALLOWED_MERGE_FIELDS: Set[str] = {
    # Technical specs
    "operating_system",
    "os_version",
    "cpu_cores",
    "memory_gb",
    "storage_gb",
    # Network info
    "ip_address",
    "fqdn",
    "mac_address",
    # Infrastructure
    "environment",
    "location",
    "datacenter",
    "rack_location",
    "availability_zone",
    # Business info
    "business_owner",
    "technical_owner",
    "department",
    "application_name",
    "technology_stack",
    "criticality",
    "business_criticality",
    # Migration planning
    "six_r_strategy",
    "migration_priority",
    "migration_complexity",
    "migration_wave",
    # Metadata
    "description",
    "custom_attributes",
    # Performance metrics
    "cpu_utilization_percent",
    "memory_utilization_percent",
    "disk_iops",
    "network_throughput_mbps",
    "current_monthly_cost",
    "estimated_cloud_cost",
}

# Fields that MUST NEVER be merged (immutable identifiers and tenant context)
NEVER_MERGE_FIELDS: Set[str] = {
    "id",
    "client_account_id",
    "engagement_id",
    "flow_id",
    "master_flow_id",
    "discovery_flow_id",
    "assessment_flow_id",
    "planning_flow_id",
    "execution_flow_id",
    "raw_import_records_id",
    "created_at",
    "created_by",
    "name",
    "asset_name",  # Part of identity
    "hostname",  # Part of unique constraint - never merge
}
