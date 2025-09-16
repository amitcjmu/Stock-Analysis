"""
Helper functions for field mapping execution.

Extracted from flow_execution_service.py to reduce file length.
"""

import logging
from typing import Any, Dict, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext

from app.models.data_import.mapping import ImportFieldMapping
from app.models.discovery_flow import DiscoveryFlow

logger = logging.getLogger(__name__)


async def check_existing_field_mappings(
    db: AsyncSession, discovery_flow: DiscoveryFlow, flow_id: str
) -> Optional[Dict[str, Any]]:
    """
    Check if field mappings already exist for the flow.

    Args:
        db: Database session
        discovery_flow: Discovery flow model
        flow_id: Flow identifier

    Returns:
        Result dictionary if mappings exist, None otherwise
    """
    # Only check if field mapping is marked as completed and data_import_id exists
    if not (discovery_flow.field_mapping_completed and discovery_flow.data_import_id):
        return None

    # Check if mappings actually exist for this import
    count_stmt = select(func.count(ImportFieldMapping.id)).where(
        ImportFieldMapping.data_import_id == discovery_flow.data_import_id
    )
    mapping_count = await db.scalar(count_stmt)

    if mapping_count and mapping_count > 0:
        logger.info(
            f"✅ Field mapping already completed for flow {flow_id} with {mapping_count} mappings"
        )
        return {
            "success": True,
            "status": "already_completed",
            "phase": "field_mapping_suggestions",
            "message": f"Field mapping already completed with {mapping_count} mappings",
            "mapping_count": mapping_count,
        }
    else:
        logger.warning(
            "⚠️ Field mapping marked as completed but no mappings found, regenerating..."
        )
        return None


async def auto_generate_field_mappings(
    db: AsyncSession, context: RequestContext, discovery_flow: DiscoveryFlow
) -> None:
    """
    Auto-generate field mappings for the import.

    Args:
        db: Database session
        context: Request context
        discovery_flow: Discovery flow model
    """
    if not discovery_flow.data_import_id:
        return

    logger.info(
        f"🔄 Auto-generating field mappings for import {discovery_flow.data_import_id}"
    )

    try:
        from app.api.v1.endpoints.data_import.field_mapping.services.mapping_service import (
            MappingService,
        )

        # Create mapping service with context
        mapping_service = MappingService(db, context)

        # Generate mappings for the import
        mapping_result = await mapping_service.generate_mappings_for_import(
            str(discovery_flow.data_import_id)
        )

        logger.info(
            f"✅ Auto-generated {mapping_result.get('mappings_created', 0)} field mappings"
        )

    except Exception as mapping_error:
        logger.warning(f"⚠️ Failed to auto-generate field mappings: {mapping_error}")
        # Don't fail the phase if mapping generation fails
