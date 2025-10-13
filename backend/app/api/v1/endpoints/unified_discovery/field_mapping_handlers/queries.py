"""
Field Mapping Query Operations (Read-only).

CC: Extracted from field_mapping_handlers.py for modularity.
"""

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException

from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from app.core.security.secure_logging import safe_log_format
from ..field_mapping_schemas import FieldMappingsResponse
from .helpers import (
    get_discovery_flow,
    ensure_field_mappings_exist,
    get_field_mappings_from_db,
    create_field_mapping_item,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/flows/{flow_id}/field-mappings", response_model=FieldMappingsResponse)
async def get_field_mappings(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
) -> FieldMappingsResponse:
    """Get field mappings for a discovery flow."""
    try:
        logger.info(
            safe_log_format(
                "Getting field mappings for flow: {flow_id}", flow_id=flow_id
            )
        )

        # Get the discovery flow with tenant scoping
        flow = await get_discovery_flow(flow_id, db, context)

        # Ensure field mappings exist (auto-generate if needed)
        await ensure_field_mappings_exist(flow, db, context)

        # Get field mappings from database
        mappings = await get_field_mappings_from_db(flow, db, context)

        # Convert SQLAlchemy models to Pydantic field mappings
        field_mapping_items = []
        for mapping in mappings:
            item = create_field_mapping_item(mapping)
            if item:
                field_mapping_items.append(item)

        # Return the response using Pydantic model
        return FieldMappingsResponse(
            success=True,
            flow_id=flow_id,
            field_mappings=field_mapping_items,
            count=len(field_mapping_items),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(safe_log_format("Failed to get field mappings: {e}", e=e))
        raise HTTPException(status_code=500, detail=str(e))
