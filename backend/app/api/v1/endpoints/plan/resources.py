"""
Resource planning endpoints for migration planning.

ARCHITECTURE NOTE:
Resource estimation is now derived from wave_plan_data.applications and their 6R strategies.
This ensures Resources page reflects actual staffing needs based on migration complexity.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import get_current_context
from app.core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/resources")
async def get_resources(
    planning_flow_id: Optional[str] = Query(
        None,
        description="Planning flow ID for 6R-based resource estimation from wave data",
    ),
    db: AsyncSession = Depends(get_db),
    context=Depends(get_current_context),
) -> Dict[str, Any]:
    """
    Get resource planning data with AI-estimated teams based on 6R strategies.

    When planning_flow_id is provided, analyzes wave applications by migration strategy
    to estimate required staffing. Returns team recommendations, utilization metrics,
    skill coverage analysis, and optimization recommendations.

    Args:
        planning_flow_id: Optional planning flow UUID for wave-based estimation

    Returns:
        - teams: Estimated teams with skills and FTE counts based on 6R strategies
        - metrics: Resource summary (total teams, resources, utilization)
        - recommendations: AI-generated staffing recommendations
        - upcoming_needs: Skill gaps identified from wave analysis
    """
    from app.services.planning.resource_service import ResourceService
    from uuid import UUID

    # Initialize service with tenant context
    resource_service = ResourceService(db, context)

    # Convert planning_flow_id if provided
    planning_flow_uuid = None
    if planning_flow_id:
        try:
            planning_flow_uuid = UUID(planning_flow_id)
        except (ValueError, TypeError):
            logger.warning(f"Invalid planning_flow_id format: {planning_flow_id}")

    # Get aggregated resource planning data (now with 6R estimation)
    resource_data = await resource_service.get_resources_for_planning(
        planning_flow_id=planning_flow_uuid
    )

    # Convert Pydantic model to dict for API response
    return resource_data.model_dump()
