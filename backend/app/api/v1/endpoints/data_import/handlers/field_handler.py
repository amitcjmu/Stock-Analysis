"""
Field Handler - Provides field mapping and target field information.
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from app.models.asset import Asset
from app.models.data_import import DataImport
from .field_metadata import (
    INTERNAL_SYSTEM_FIELDS,
    TYPE_MAPPINGS,
    categorize_field,
    is_required_field,
    generate_field_description,
)

logger = logging.getLogger(__name__)

router = APIRouter()

APP_DISCOVERY_ASSET_FIELDS = {
    "name",
    "hostname",
    "application_name",
    "asset_type",
}
APP_DISCOVERY_EXCLUDED_DEP_FIELDS = {
    "id",
    "asset_id",
    "depends_on_asset_id",
    "client_account_id",
    "engagement_id",
    "created_at",
    "updated_at",
    "confidence_score",  # Not required for app dependency imports
}

# Derived/Computed fields that should not appear in CMDB imports
# These are calculated fields, not actual CMDB data fields
DERIVED_FIELDS_EXCLUDED = {
    "ai_gap_analysis_status",
    "ai_gap_analysis_timestamp",
    "assessment_readiness",
    "assessment_readiness_score",
    "assessment_blockers",
    "assessment_recommendations",
    "quality_score",
    "completeness_score",
    "confidence_score",
    "complexity_score",  # Already excluded via assessment category, but adding for clarity
}

# Field-to-Import-Type Mapping
# Explicit mapping for specific fields that need precise control
# Extend this as new import types are added or fields need specific mappings
FIELD_IMPORT_TYPES = {
    # Universal fields - appear in all import types
    "hostname": ["cmdb", "app_discovery", "infrastructure"],
    "asset_name": ["cmdb", "app_discovery", "infrastructure"],
    "asset_type": [
        "cmdb",
        "infrastructure",
    ],  # Removed app_discovery - not required for app dependency
    "name": ["cmdb", "app_discovery", "infrastructure"],
    "id": [
        "cmdb",
        "infrastructure",
    ],  # Removed app_discovery - not required for app dependency
    "description": ["cmdb", "app_discovery", "infrastructure"],
    # Infrastructure-specific fields (NOT in app_discovery)
    "ip_address": ["cmdb", "infrastructure"],
    "mac_address": ["cmdb", "infrastructure"],
    "subnet": ["cmdb", "infrastructure"],
    "vlan": ["cmdb", "infrastructure"],
    "rack_location": ["cmdb", "infrastructure"],
    "datacenter": ["cmdb", "infrastructure"],
    "availability_zone": [
        "cmdb",
        "infrastructure",
    ],  # Cloud infrastructure, not app discovery
    "fqdn": ["cmdb", "infrastructure"],  # Network infrastructure
    "location": ["cmdb", "infrastructure"],  # Physical location
    "environment": ["cmdb", "infrastructure"],  # Infrastructure environment
    "operating_system": ["cmdb", "infrastructure"],
    "os_version": ["cmdb", "infrastructure"],
    "cpu_cores": ["cmdb", "infrastructure"],
    "memory_gb": ["cmdb", "infrastructure"],
    "storage_gb": ["cmdb", "infrastructure"],
    "technology_stack": ["cmdb", "infrastructure"],
    "criticality": ["cmdb", "infrastructure"],
    "hosting_model": ["cmdb", "infrastructure"],
    "server_role": ["cmdb", "infrastructure"],
    "database_type": ["cmdb", "infrastructure"],
    "database_version": ["cmdb", "infrastructure"],
    "database_size_gb": ["cmdb", "infrastructure"],
    # Performance fields (NOT in app_discovery)
    "cpu_utilization_percent": ["cmdb", "infrastructure"],
    "memory_utilization_percent": ["cmdb", "infrastructure"],
    "disk_iops": ["cmdb", "infrastructure"],
    "network_throughput_mbps": ["cmdb", "infrastructure"],
    "cpu_utilization_percent_max": ["cmdb", "infrastructure"],
    "memory_utilization_percent_max": ["cmdb", "infrastructure"],
    "storage_free_gb": ["cmdb", "infrastructure"],
    "storage_used_gb": ["cmdb", "infrastructure"],
    "tech_debt_flags": ["cmdb", "infrastructure"],
    # Resilience fields (NOT in app_discovery)
    "rto_minutes": ["cmdb", "infrastructure"],
    "rpo_minutes": ["cmdb", "infrastructure"],
    # App discovery specific fields
    "application_name": ["cmdb", "app_discovery"],
    # CMDB-specific fields
    "serial_number": ["cmdb"],
    "architecture_type": ["cmdb"],
    "asset_status": ["cmdb"],
    # Dependency fields are handled separately in get_asset_dependency_fields()
}

# Category-to-Import-Type default mapping
# Used as fallback when field is not in explicit FIELD_IMPORT_TYPES mapping
# NOTE: Do NOT add app_discovery to category fallbacks - only explicit fields should have it
CATEGORY_TO_IMPORT_TYPES = {
    "identification": [
        "cmdb",
        "infrastructure",
    ],  # Removed app_discovery - only explicit fields get it
    "technical": ["cmdb", "infrastructure"],
    "performance": ["cmdb", "infrastructure"],
    "business": ["cmdb"],
    "migration": ["cmdb"],  # Migration planning fields (6R, waves, readiness)
    "assessment": ["cmdb"],  # Assessment fields (complexity, architecture analysis)
    "dependency": ["app_discovery"],  # Dependency fields
    "resilience": ["cmdb", "infrastructure"],
    "other": ["cmdb"],  # Default fallback
}


def get_field_import_types(field_name: str, category: str) -> List[str]:
    """
    Determine which import types a field applies to.

    Priority:
    1. Check explicit FIELD_IMPORT_TYPES mapping (field-specific)
    2. Fall back to CATEGORY_TO_IMPORT_TYPES (category-based)
    3. Default to ["cmdb"] if nothing matches

    This ensures all dynamically discovered fields get import_types metadata.
    """
    # Check explicit field mapping first
    if field_name in FIELD_IMPORT_TYPES:
        return FIELD_IMPORT_TYPES[field_name]

    # Fall back to category-based mapping
    if category in CATEGORY_TO_IMPORT_TYPES:
        return CATEGORY_TO_IMPORT_TYPES[category]

    # Default fallback
    return ["cmdb"]


def generate_display_name_from_field_name(field_name: str) -> str:
    """
    Generate a display name from a snake_case field name.
    Converts 'field_name' to 'Field Name'.
    """
    return field_name.replace("_", " ").replace("-", " ").title()


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

            # Skip derived/computed fields (not actual CMDB data fields)
            if field_name in DERIVED_FIELDS_EXCLUDED:
                continue

            # Map PostgreSQL type to frontend type
            pg_type = col.data_type
            field_type = TYPE_MAPPINGS.get(pg_type, "string")

            # Determine if field is nullable
            is_nullable = col.is_nullable == "YES"

            # Generate base description
            description = generate_field_description(field_name, field_type)

            # Extract metadata from SQLAlchemy Column.info if available
            display_name = None
            short_hint = None
            category = categorize_field(field_name)

            try:
                sa_column = getattr(Asset, field_name, None)
                if sa_column and hasattr(sa_column, "info"):
                    column_info = sa_column.info
                    display_name = column_info.get("display_name")
                    short_hint = column_info.get("short_hint")
                    # Use category from Column.info if provided, else use categorize_field
                    category = column_info.get("category", category)
            except Exception as e:
                # Log but don't fail - just use defaults
                logger.debug(f"Could not extract metadata for {field_name}: {e}")

            # REMOVED: No longer filtering assessment/migration fields - they're valid for CMDB imports
            # Migration and assessment fields are now available via CATEGORY_TO_IMPORT_TYPES mapping

            # Ensure display_name is never None - generate from field_name if needed
            if display_name is None:
                display_name = generate_display_name_from_field_name(field_name)

            # Determine import types for this field
            import_types = get_field_import_types(field_name, category)

            # Audit logging: Log when fields become available for import (Qodo compliance)
            logger.info(
                "Field available for import",
                extra={
                    "field_name": field_name,
                    "import_types": import_types,
                    "category": category,
                },
            )

            field_info = {
                "name": field_name,
                "display_name": display_name,
                "short_hint": short_hint,
                "type": field_type,
                "required": is_required_field(field_name, is_nullable),
                "description": description,
                "category": category,
                "nullable": is_nullable,
                "max_length": col.character_maximum_length,
                "precision": col.numeric_precision,
                "scale": col.numeric_scale,
                "import_types": import_types,
            }

            fields.append(field_info)

        logger.info(f"Retrieved {len(fields)} fields from assets table schema")

        # Add fields from related tables for complete CMDB mapping support
        # asset_resilience: RTO/RPO fields
        related_table_fields = [
            {
                "name": "rto_minutes",
                "display_name": "RTO (Minutes)",
                "short_hint": "Recovery Time Objective",
                "type": "integer",
                "required": False,
                "description": "Recovery Time Objective in minutes (Asset Resilience)",
                "category": "resilience",
                "nullable": True,
                "import_types": get_field_import_types("rto_minutes", "resilience"),
            },
            {
                "name": "rpo_minutes",
                "display_name": "RPO (Minutes)",
                "short_hint": "Recovery Point Objective",
                "type": "integer",
                "required": False,
                "description": "Recovery Point Objective in minutes (Asset Resilience)",
                "category": "resilience",
                "nullable": True,
                "import_types": get_field_import_types("rpo_minutes", "resilience"),
            },
        ]

        # Audit logging for related table fields
        for field in related_table_fields:
            logger.info(
                "Field available for import",
                extra={
                    "field_name": field["name"],
                    "import_types": field["import_types"],
                    "category": field["category"],
                },
            )

        fields.extend(related_table_fields)

        # Note: Dependency fields are NOT added here for CMDB imports.
        # They are only included when explicitly requested for app_discovery imports
        # via get_application_dependency_target_fields() or get_asset_dependency_fields().

        logger.info(f"Total fields including related tables: {len(fields)}")
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
                "import_types": get_field_import_types("asset_name", "identification"),
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
                "import_types": get_field_import_types("hostname", "identification"),
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
                "import_types": get_field_import_types("ip_address", "identification"),
            },
        ]


async def get_asset_dependency_fields(db: AsyncSession) -> List[Dict[str, Any]]:
    """Get target fields from the asset_dependencies table."""
    result = await db.execute(
        text(
            """
            SELECT
                column_name,
                data_type,
                is_nullable,
                character_maximum_length,
                numeric_precision,
                numeric_scale
            FROM information_schema.columns
            WHERE table_name = 'asset_dependencies'
              AND table_schema = 'migration'
            ORDER BY ordinal_position
            """
        )
    )

    columns = result.fetchall()
    fields: List[Dict[str, Any]] = []

    for col in columns:
        field_name = col.column_name
        if field_name in APP_DISCOVERY_EXCLUDED_DEP_FIELDS:
            continue

        pg_type = col.data_type
        field_type = TYPE_MAPPINGS.get(pg_type, "string")
        is_nullable = col.is_nullable == "YES"

        fields.append(
            {
                "name": field_name,
                "display_name": field_name.replace("_", " ").title(),
                "short_hint": None,
                "type": field_type,
                "required": False,
                "description": f"Dependency attribute '{field_name}'",
                "category": "dependency",
                "nullable": is_nullable,
                "max_length": col.character_maximum_length,
                "precision": col.numeric_precision,
                "scale": col.numeric_scale,
                "import_types": get_field_import_types(field_name, "dependency"),
            }
        )

    return fields


async def get_application_dependency_target_fields(
    db: AsyncSession,
) -> List[Dict[str, Any]]:
    """Return curated fields for application dependency imports."""
    asset_fields = await get_assets_table_fields(db)
    curated_assets = [
        field for field in asset_fields if field["name"] in APP_DISCOVERY_ASSET_FIELDS
    ]

    dependency_fields = await get_asset_dependency_fields(db)

    logger.info(
        "Prepared application dependency target fields: %s asset fields, %s dependency fields",
        len(curated_assets),
        len(dependency_fields),
    )
    return curated_assets + dependency_fields


async def resolve_import_category(
    *,
    flow_id: Optional[str],
    explicit_category: Optional[str],
    db: AsyncSession,
) -> Optional[str]:
    """Resolve import category via explicit parameter or master flow lookup."""
    if explicit_category:
        return explicit_category.lower()

    if not flow_id:
        return None

    try:
        flow_uuid = UUID(flow_id)
    except (ValueError, TypeError):
        logger.warning("Invalid flow_id provided for target field lookup: %s", flow_id)
        return None

    result = await db.execute(
        select(DataImport.import_category).where(
            DataImport.master_flow_id == flow_uuid,
            DataImport.import_category.isnot(None),
        )
    )
    category = result.scalar_one_or_none()
    return category.lower() if category else None


@router.get("/available-target-fields")
async def get_available_target_fields(
    flow_id: Optional[str] = Query(
        None, description="Optional master flow ID to scope target fields"
    ),
    import_category: Optional[str] = Query(
        None, description="Optional import category override"
    ),
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

        resolved_category = await resolve_import_category(
            flow_id=flow_id, explicit_category=import_category, db=db
        )
        logger.info(
            "Resolved target field import category: %s (flow_id=%s)",
            resolved_category or "default",
            flow_id,
        )

        # Get all fields with import_types metadata
        fields = await get_assets_table_fields(db)

        # Normalize category for filtering: "app-discovery" -> "app_discovery", "cmdb_export" -> "cmdb"
        normalized_category = resolved_category or "cmdb_export"
        normalized_category = (
            normalized_category.lower().replace("-", "_").replace("cmdb_export", "cmdb")
        )

        # For app_discovery import type, also include dependency fields from asset_dependencies table
        # These include: port, protocol_name (communication type), conn_count (count),
        # bytes_total, criticality, first_seen, last_seen, etc.
        if normalized_category == "app_discovery":
            dependency_fields = await get_asset_dependency_fields(db)
            fields.extend(dependency_fields)
            logger.info(
                f"Added {len(dependency_fields)} dependency fields for app_discovery import type: "
                f"{[f['name'] for f in dependency_fields]}"
            )

        # Backend filtering: Only return fields that match the resolved import_category
        # This reduces data transfer and ensures frontend gets only relevant fields
        # Frontend filtering remains as a safety net for other use cases
        fields_before_filter = len(fields)
        logger.info(
            f"🔍 Backend filtering START: {fields_before_filter} fields "
            f"before filter for category '{normalized_category}'"
        )

        filtered_fields = []
        skipped_no_import_types = []
        skipped_wrong_category = []

        for field in fields:
            field_name = field.get("name", "unknown")
            # Field must have import_types defined
            field_import_types = field.get("import_types", [])
            if not field_import_types:
                # Skip fields without import_types metadata
                skipped_no_import_types.append(field_name)
                continue

            # Check if field's import_types includes the normalized category
            if normalized_category in field_import_types:
                filtered_fields.append(field)
            else:
                skipped_wrong_category.append(
                    f"{field_name} (has {field_import_types})"
                )

        # CRITICAL: Replace fields with filtered list
        # This MUST happen - fields after this point should only contain filtered results
        fields = filtered_fields

        # Verify filtering worked
        if len(fields) > fields_before_filter:
            logger.error(
                f"❌ FILTERING ERROR: Filtered fields ({len(fields)}) > "
                f"original fields ({fields_before_filter})! "
                f"This should never happen. Check filtering logic."
            )

        logger.info(
            f"✅ Backend filtering COMPLETE: {fields_before_filter} → {len(fields)} fields "
            f"for category '{normalized_category}'. "
            f"Skipped: {len(skipped_no_import_types)} no import_types, "
            f"{len(skipped_wrong_category)} wrong category"
        )

        # Summary-level logging only (Qodo bot: reduce excessive logging)
        logger.info(
            f"📋 Returning {len(fields)} fields for category '{normalized_category}'"
        )

        # Summary logging for app_discovery (counts only, no field names)
        if normalized_category == "app_discovery":
            asset_field_count = sum(
                1 for f in filtered_fields if f.get("category") != "dependency"
            )
            dependency_field_count = sum(
                1 for f in filtered_fields if f.get("category") == "dependency"
            )
            logger.info(
                f"📊 app_discovery fields: {asset_field_count} asset fields, "
                f"{dependency_field_count} dependency fields"
            )

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
        logger.info(
            f"Retrieved {len(fields)} target fields from assets table schema (filtered for '{normalized_category}'):"
        )
        for category, category_fields in categories.items():
            logger.info(f"  {category}: {len(category_fields)} fields")

        return {
            "success": True,
            "import_category": resolved_category or "cmdb_export",
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
        logger.error(f"Error getting available target fields: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to retrieve target fields. "
                "Please check that the database connection is available and try again."
            ),
        )


@router.get("/target-field-categories")
async def get_target_field_categories(
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get available target field categories from actual database schema.
    """
    try:
        fields = await get_assets_table_fields(db)
        categories = list(set(field["category"] for field in fields))
        categories.sort()

        return {"success": True, "categories": categories, "total": len(categories)}

    except Exception as e:
        logger.error(f"Error getting field categories: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to retrieve field categories. "
                "Please check that the database connection is available and try again."
            ),
        )
