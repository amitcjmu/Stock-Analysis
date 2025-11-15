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
    "id",
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
}


async def get_assets_table_fields(db: AsyncSession) -> List[Dict[str, Any]]:
    """Get actual fields from the assets table schema."""
    try:
        # Get Asset model for metadata extraction
        from app.models.asset import Asset

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
            }

            fields.append(field_info)

        logger.info(f"Retrieved {len(fields)} fields from assets table schema")

        # Add fields from related tables for complete CMDB mapping support
        # asset_resilience: RTO/RPO fields
        fields.extend(
            [
                {
                    "name": "rto_minutes",
                    "display_name": "RTO (Minutes)",
                    "short_hint": "Recovery Time Objective",
                    "type": "integer",
                    "required": False,
                    "description": "Recovery Time Objective in minutes (Asset Resilience)",
                    "category": "resilience",
                    "nullable": True,
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
                },
            ]
        )

        # asset_dependencies: key relationship attributes needed for application dependency imports
        dependency_fields = [
            {
                "name": "dependency_type",
                "display_name": "Dependency Type",
                "short_hint": "Category of the dependency (database, API, storage, etc.)",
                "type": "string",
                "required": False,
                "description": "Type of relationship between the source and target assets.",
                "category": "dependency",
                "nullable": False,
            },
            {
                "name": "description",
                "display_name": "Dependency Description",
                "short_hint": "Narrative describing how the assets interact",
                "type": "text",
                "required": False,
                "description": "Describes the nature or purpose of the dependency.",
                "category": "dependency",
                "nullable": True,
            },
            {
                "name": "relationship_nature",
                "display_name": "Relationship Nature",
                "short_hint": "Logical nature such as hosting, data, API",
                "type": "string",
                "required": False,
                "description": "Nature of the relationship (e.g., hosting, API, data feed).",
                "category": "dependency",
                "nullable": True,
            },
            {
                "name": "direction",
                "display_name": "Direction",
                "short_hint": "Flow direction between source and target",
                "type": "string",
                "required": False,
                "description": "Indicates if the dependency flows inbound, outbound, or bidirectional.",
                "category": "dependency",
                "nullable": True,
            },
            {
                "name": "port",
                "display_name": "Port",
                "short_hint": "Network port observed for this dependency",
                "type": "integer",
                "required": False,
                "description": "Network port number observed for the dependency connection.",
                "category": "dependency",
                "nullable": True,
            },
            {
                "name": "protocol_name",
                "display_name": "Protocol",
                "short_hint": "Protocol such as TCP, UDP, HTTP",
                "type": "string",
                "required": False,
                "description": "Protocol name detected for the dependency traffic.",
                "category": "dependency",
                "nullable": True,
            },
            {
                "name": "conn_count",
                "display_name": "Connection Count",
                "short_hint": "Number of observed connections",
                "type": "integer",
                "required": False,
                "description": "Total number of connections observed between the assets.",
                "category": "dependency",
                "nullable": True,
            },
            {
                "name": "first_seen",
                "display_name": "First Seen",
                "short_hint": "Timestamp when the dependency was first observed",
                "type": "datetime",
                "required": False,
                "description": "First time this dependency was detected.",
                "category": "dependency",
                "nullable": True,
            },
            {
                "name": "last_seen",
                "display_name": "Last Seen",
                "short_hint": "Most recent observation timestamp",
                "type": "datetime",
                "required": False,
                "description": "Most recent time this dependency was detected.",
                "category": "dependency",
                "nullable": True,
            },
        ]
        fields.extend(dependency_fields)

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

        if resolved_category == "app_discovery":
            fields = await get_application_dependency_target_fields(db)
        else:
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
    Get available target field categories from actual database schema.
    """
    try:
        fields = await get_assets_table_fields(db)
        categories = list(set(field["category"] for field in fields))
        categories.sort()

        return {"success": True, "categories": categories, "total": len(categories)}

    except Exception as e:
        logger.error(f"Error getting field categories: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve field categories: {str(e)}"
        )
