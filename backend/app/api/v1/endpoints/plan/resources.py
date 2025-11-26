"""
Resource planning endpoints for migration planning.
"""

from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import get_current_context
from app.core.database import get_db

router = APIRouter()


@router.get("/resources")
async def get_resources(
    db: AsyncSession = Depends(get_db), context=Depends(get_current_context)
) -> Dict[str, Any]:
    """
    Get resource planning data with teams, metrics, and recommendations.

    Returns team allocations, utilization metrics, skill coverage analysis,
    and resource optimization recommendations.

    Now wired to real database (migration 114: resource_pools, resource_allocations, resource_skills).
    """
    from app.services.planning.resource_service import ResourceService

    # Initialize service with tenant context
    resource_service = ResourceService(db, context)

    # Get aggregated resource planning data
    resource_data = await resource_service.get_resources_for_planning()

    # Convert Pydantic model to dict for API response
    return resource_data.model_dump()
