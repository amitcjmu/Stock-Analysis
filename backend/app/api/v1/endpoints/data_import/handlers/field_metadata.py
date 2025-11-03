"""
Field metadata utilities for field mapping.

Constants and helper functions extracted to keep field_handler.py under 400 lines.
"""

# Internal system fields that should be excluded from field mapping
INTERNAL_SYSTEM_FIELDS = {
    "id",
    "asset_id",  # Internal UUID primary key
    "created_at",
    "updated_at",
    "imported_by",
    "flow_id",
    "discovery_flow_id",
    "assessment_flow_id",
    "planning_flow_id",
    "execution_flow_id",
    "master_flow_id",
    "migration_id",
    "client_account_id",
    "engagement_id",
    "data_import_id",
    "raw_data",
    "raw_import_records_id",
    "mapping_status",
    "validation_status",
    "import_session_id",
    "created_by",
    "updated_by",
    "imported_at",
    "deleted_at",
    "version",
    "audit_log",
    "processing_status",
    "error_log",
    "sync_status",
    "source_system_id",
    "import_batch_id",
    "tenant_id",
    "metadata_version",
    "schema_version",
    "source_phase",
    "current_phase",
    "phase_context",
    "discovered_at",
    "discovery_completed_at",
    "discovery_status",
    "source_filename",
    "field_mappings_used",
}

# Field type mappings from PostgreSQL to frontend-friendly types
TYPE_MAPPINGS = {
    "varchar": "string",
    "text": "text",
    "int4": "integer",
    "int8": "integer",
    "float8": "number",
    "float4": "number",
    "bool": "boolean",
    "json": "object",
    "jsonb": "object",
    "timestamptz": "datetime",
    "timestamp": "datetime",
    "date": "date",
    "uuid": "string",
}


def categorize_field(field_name: str) -> str:
    """Categorize field based on naming patterns."""
    name = field_name.lower()

    # Identity fields
    if any(
        pattern in name
        for pattern in ["asset_id", "asset_name", "name", "hostname", "fqdn"]
    ):
        return "identification"

    # Network fields
    if any(
        pattern in name
        for pattern in ["ip_", "mac_", "dns_", "subnet", "vlan", "network"]
    ):
        return "network"

    # Technical/System fields
    if any(
        pattern in name
        for pattern in [
            "cpu_",
            "memory_",
            "ram_",
            "storage_",
            "disk_",
            "os_",
            "operating_",
        ]
    ):
        return "technical"

    # Performance fields
    if any(
        pattern in name
        for pattern in ["utilization", "performance", "throughput", "iops", "latency"]
    ):
        return "performance"

    # Location/Environment fields
    if any(
        pattern in name
        for pattern in [
            "datacenter",
            "location_",
            "region",
            "environment",
            "availability_",
            "rack",
        ]
    ):
        return "environment"

    # Business fields
    if any(
        pattern in name
        for pattern in ["owner", "business_", "department", "cost_", "application_"]
    ):
        return "business"

    # Migration fields
    if any(
        pattern in name
        for pattern in [
            "migration_",
            "six_r_",
            "criticality",
            "readiness",
            "target_",
            "cloud_",
        ]
    ):
        return "migration"

    # Financial fields
    if any(pattern in name for pattern in ["cost", "price", "budget", "financial"]):
        return "financial"

    # Quality/Assessment fields
    if any(pattern in name for pattern in ["quality_", "completeness_", "score"]):
        return "quality"

    return "other"


def is_required_field(field_name: str, is_nullable: bool) -> bool:
    """Determine if a field should be marked as required."""
    critical_fields = {
        "asset_name",
        "asset_type",
        "hostname",
        "ip_address",
        "operating_system",
        "cpu_cores",
        "memory_gb",
    }
    return field_name.lower() in critical_fields or not is_nullable


def generate_field_description(field_name: str, field_type: str) -> str:
    """Generate human-readable description for field."""
    descriptions = {
        "asset_name": "Asset name or identifier",
        "asset_type": "Type of asset (server, database, application, etc.)",
        "hostname": "System hostname",
        "fqdn": "Fully qualified domain name",
        "ip_address": "Primary IP address",
        "mac_address": "Network MAC address",
        "operating_system": "Operating system name and version",
        "os_version": "Operating system version details",
        "cpu_cores": "Number of CPU cores",
        "memory_gb": "Memory capacity in gigabytes",
        "ram_gb": "RAM capacity in gigabytes",
        "storage_gb": "Storage capacity in gigabytes",
        "cpu_utilization_percent": "CPU utilization percentage",
        "memory_utilization_percent": "Memory utilization percentage",
        "disk_iops": "Disk I/O operations per second",
        "network_throughput_mbps": "Network throughput in Mbps",
        "business_owner": "Business owner or stakeholder",
        "technical_owner": "Technical owner or administrator",
        "department": "Department or organizational unit",
        "application_name": "Primary application name",
        "technology_stack": "Technology stack or platform",
        "criticality": "Business criticality level",
        "business_criticality": "Business impact criticality",
        "six_r_strategy": "6R migration strategy (rehost, refactor, etc.)",
        "migration_priority": "Migration priority level",
        "migration_complexity": "Migration complexity assessment",
        "migration_wave": "Migration wave or phase",
        "environment": "Environment (production, staging, development, etc.)",
        "datacenter": "Datacenter or facility location",
        "location": "Physical location",
        "rack_location": "Rack location identifier",
        "current_monthly_cost": "Current monthly operational cost",
        "estimated_cloud_cost": "Estimated cloud migration cost",
        "quality_score": "Data quality assessment score",
        "completeness_score": "Data completeness percentage",
    }

    if field_name in descriptions:
        return descriptions[field_name]

    # Generate description based on field name patterns
    name_parts = field_name.replace("_", " ").title()
    return f"{name_parts} field"
