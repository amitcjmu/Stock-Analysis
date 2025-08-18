"""
Field Handler - Provides field mapping and target field information.
"""

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context
from app.core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()

# Internal system fields that should be excluded from field mapping
INTERNAL_SYSTEM_FIELDS = {
    "id",
    "created_at",
    "updated_at",
    "imported_by",
    "flow_id",
    "client_account_id",
    "engagement_id",
    "data_import_id",
    "raw_data",
    "mapping_status",
    "validation_status",
    "import_session_id",
    "created_by",
    "updated_by",
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


# Field categorization based on naming patterns
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


async def get_assets_table_fields(db: AsyncSession) -> List[Dict[str, Any]]:
    """Get actual fields from the assets table schema."""
    try:
        # Get table schema information
        result = await db.execute(
            text(
                """
            SELECT
                column_name,
                data_type,
                is_nullable,
                column_default,
                character_maximum_length,
                numeric_precision,
                numeric_scale
            FROM information_schema.columns
            WHERE table_name = 'assets'
            AND table_schema = 'migration'
            ORDER BY ordinal_position
        """
            )
        )

        columns = result.fetchall()
        fields = []

        for col in columns:
            field_name = col.column_name

            # Skip internal system fields
            if field_name in INTERNAL_SYSTEM_FIELDS:
                continue

            # Map PostgreSQL type to frontend type
            pg_type = col.data_type
            field_type = TYPE_MAPPINGS.get(pg_type, "string")

            # Determine if field is nullable
            is_nullable = col.is_nullable == "YES"

            # Generate field description
            description = generate_field_description(field_name, field_type)

            field_info = {
                "name": field_name,
                "type": field_type,
                "required": is_required_field(field_name, is_nullable),
                "description": description,
                "category": categorize_field(field_name),
                "nullable": is_nullable,
                "max_length": col.character_maximum_length,
                "precision": col.numeric_precision,
                "scale": col.numeric_scale,
            }

            fields.append(field_info)

        logger.info(f"Retrieved {len(fields)} fields from assets table schema")
        return fields

    except Exception as e:
        logger.error(f"Error getting assets table fields: {e}")
        # Fallback to minimal essential fields only if database query fails
        # This prevents hardcoded fields from appearing when they don't
        # exist in uploaded data
        logger.warning(
            "Using minimal fallback fields due to database error - "
            "only essential fields included"
        )
        return [
            # Only include the most essential identification fields
            {
                "name": "asset_name",
                "type": "string",
                "required": True,
                "description": "Asset name or identifier",
                "category": "identification",
                "nullable": False,
                "max_length": None,
                "precision": None,
                "scale": None,
            },
            {
                "name": "hostname",
                "type": "string",
                "required": True,
                "description": "Asset hostname",
                "category": "identification",
                "nullable": False,
                "max_length": None,
                "precision": None,
                "scale": None,
            },
            {
                "name": "ip_address",
                "type": "string",
                "required": True,
                "description": "Primary IP address",
                "category": "network",
                "nullable": False,
                "max_length": None,
                "precision": None,
                "scale": None,
            },
        ]


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


# Keep the original standard fields as fallback
STANDARD_TARGET_FIELDS = [
    # Identification fields
    {
        "name": "asset_id",
        "type": "string",
        "required": True,
        "description": "Unique asset identifier",
        "category": "identification",
    },
    {
        "name": "name",
        "type": "string",
        "required": True,
        "description": "Asset name or identifier",
        "category": "identification",
    },
    {
        "name": "hostname",
        "type": "string",
        "required": True,
        "description": "Asset hostname",
        "category": "identification",
    },
    {
        "name": "fqdn",
        "type": "string",
        "required": False,
        "description": "Fully qualified domain name",
        "category": "identification",
    },
    {
        "name": "asset_name",
        "type": "string",
        "required": False,
        "description": "Friendly asset name",
        "category": "identification",
    },
    # Technical fields
    {
        "name": "asset_type",
        "type": "enum",
        "required": True,
        "description": "Type of asset (server, vm, container, etc.)",
        "category": "technical",
    },
    {
        "name": "operating_system",
        "type": "string",
        "required": True,
        "description": "Operating system name and version",
        "category": "technical",
    },
    {
        "name": "os_version",
        "type": "string",
        "required": False,
        "description": "Detailed OS version",
        "category": "technical",
    },
    {
        "name": "cpu_cores",
        "type": "integer",
        "required": True,
        "description": "Number of CPU cores",
        "category": "technical",
    },
    {
        "name": "memory_gb",
        "type": "number",
        "required": True,
        "description": "Memory in gigabytes",
        "category": "technical",
    },
    {
        "name": "storage_gb",
        "type": "number",
        "required": False,
        "description": "Total storage in gigabytes",
        "category": "technical",
    },
    {
        "name": "architecture",
        "type": "string",
        "required": False,
        "description": "System architecture (x86_64, arm64, etc.)",
        "category": "technical",
    },
    # Network fields
    {
        "name": "ip_address",
        "type": "string",
        "required": True,
        "description": "Primary IP address",
        "category": "network",
    },
    {
        "name": "mac_address",
        "type": "string",
        "required": False,
        "description": "MAC address",
        "category": "network",
    },
    {
        "name": "subnet",
        "type": "string",
        "required": False,
        "description": "Network subnet",
        "category": "network",
    },
    {
        "name": "vlan",
        "type": "string",
        "required": False,
        "description": "VLAN identifier",
        "category": "network",
    },
    {
        "name": "dns_name",
        "type": "string",
        "required": False,
        "description": "DNS name",
        "category": "network",
    },
    # Environment fields
    {
        "name": "environment",
        "type": "enum",
        "required": True,
        "description": "Environment (production, staging, dev, etc.)",
        "category": "environment",
    },
    {
        "name": "datacenter",
        "type": "string",
        "required": False,
        "description": "Datacenter location",
        "category": "environment",
    },
    {
        "name": "region",
        "type": "string",
        "required": False,
        "description": "Geographic region",
        "category": "environment",
    },
    {
        "name": "availability_zone",
        "type": "string",
        "required": False,
        "description": "Availability zone",
        "category": "environment",
    },
    {
        "name": "rack",
        "type": "string",
        "required": False,
        "description": "Rack location",
        "category": "environment",
    },
    # Business fields
    {
        "name": "owner",
        "type": "string",
        "required": True,
        "description": "Technical owner",
        "category": "business",
    },
    {
        "name": "business_owner",
        "type": "string",
        "required": False,
        "description": "Business owner",
        "category": "business",
    },
    {
        "name": "department",
        "type": "string",
        "required": False,
        "description": "Department",
        "category": "business",
    },
    {
        "name": "cost_center",
        "type": "string",
        "required": False,
        "description": "Cost center",
        "category": "business",
    },
    {
        "name": "business_unit",
        "type": "string",
        "required": False,
        "description": "Business unit",
        "category": "business",
    },
    {
        "name": "application",
        "type": "string",
        "required": False,
        "description": "Application name",
        "category": "business",
    },
    {
        "name": "criticality",
        "type": "enum",
        "required": False,
        "description": "Business criticality level",
        "category": "business",
    },
    # Cloud readiness fields
    {
        "name": "virtualization_platform",
        "type": "string",
        "required": False,
        "description": "Current virtualization platform",
        "category": "cloud_readiness",
    },
    {
        "name": "is_virtual",
        "type": "boolean",
        "required": False,
        "description": "Is this a virtual machine",
        "category": "cloud_readiness",
    },
    {
        "name": "migration_readiness",
        "type": "enum",
        "required": False,
        "description": "Migration readiness status",
        "category": "cloud_readiness",
    },
    {
        "name": "target_cloud",
        "type": "string",
        "required": False,
        "description": "Target cloud platform",
        "category": "cloud_readiness",
    },
    # Metadata fields
    {
        "name": "created_date",
        "type": "datetime",
        "required": False,
        "description": "Asset creation date",
        "category": "metadata",
    },
    {
        "name": "last_updated",
        "type": "datetime",
        "required": False,
        "description": "Last update timestamp",
        "category": "metadata",
    },
    {
        "name": "tags",
        "type": "array",
        "required": False,
        "description": "Asset tags",
        "category": "metadata",
    },
    {
        "name": "notes",
        "type": "text",
        "required": False,
        "description": "Additional notes",
        "category": "metadata",
    },
]


@router.get("/available-target-fields")
async def get_available_target_fields(
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get available target fields for field mapping.

    Returns actual asset table fields from database schema,
    excluding internal system fields.
    """
    try:
        logger.info(
            f"Getting available target fields for client {context.client_account_id}"
        )

        # Get actual fields from database schema
        fields = await get_assets_table_fields(db)

        # Group fields by category
        categories = {}
        for field in fields:
            category = field["category"]
            if category not in categories:
                categories[category] = []
            categories[category].append(field)

        # Count required fields
        required_count = sum(1 for field in fields if field["required"])

        # Log field details for debugging
        logger.info(f"Retrieved {len(fields)} target fields from assets table schema:")
        for category, category_fields in categories.items():
            logger.info(f"  {category}: {len(category_fields)} fields")

        return {
            "success": True,
            "fields": fields,
            "categories": categories,
            "total_fields": len(fields),
            "required_fields": required_count,
            "category_count": len(categories),
            "source": "database_schema",
            "excluded_internal_fields": len(INTERNAL_SYSTEM_FIELDS),
            "message": (
                f"Retrieved {len(fields)} target fields from assets table schema "
                f"across {len(categories)} categories"
            ),
        }

    except Exception as e:
        logger.error(f"Error getting available target fields: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve target fields: {str(e)}"
        )


@router.get("/target-field-categories")
async def get_target_field_categories(
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get available target field categories.
    """
    try:
        categories = list(set(field["category"] for field in STANDARD_TARGET_FIELDS))
        categories.sort()

        return {"success": True, "categories": categories, "total": len(categories)}

    except Exception as e:
        logger.error(f"Error getting field categories: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve field categories: {str(e)}"
        )
