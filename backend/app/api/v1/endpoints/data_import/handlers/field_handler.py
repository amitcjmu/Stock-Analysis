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
from .field_metadata import (
    INTERNAL_SYSTEM_FIELDS,
    TYPE_MAPPINGS,
    categorize_field,
    is_required_field,
    generate_field_description,
)

logger = logging.getLogger(__name__)

router = APIRouter()


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
