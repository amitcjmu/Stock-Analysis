"""
Core helper functions for collection agent questionnaire generation.
Contains main public API functions and orchestration logic.
"""

import logging
from typing import Dict, Any, Optional, Union
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.context import RequestContext
from app.models.collection_flow import CollectionFlow

from .context import (
    _validate_and_convert_flow_id,
    _get_flow_with_tenant_scoping,
    _get_filtered_assets,
    _process_assets_with_gaps,
    _get_dependency_summary,
    _build_context_response,
)

logger = logging.getLogger(__name__)


async def build_agent_context(
    db: AsyncSession,
    flow_id: Union[int, str, UUID],
    context: RequestContext,
    selected_asset_ids: Optional[list[str]] = None,
) -> Dict[str, Any]:
    """
    Build context for agent to generate questionnaire.

    Args:
        db: Database session
        flow_id: Internal flow ID
        context: Request context with tenant information
        selected_asset_ids: Optional list of selected asset IDs

    Returns:
        Dictionary with context data for agent generation
    """
    # Validate and convert flow_id
    validated_flow_id = _validate_and_convert_flow_id(flow_id)

    # Get flow details with tenant scoping
    flow = await _get_flow_with_tenant_scoping(db, validated_flow_id, context)

    # Get filtered assets
    assets = await _get_filtered_assets(db, context, selected_asset_ids)

    # Process assets with gaps and collected data
    assets_with_gaps, all_gaps = await _process_assets_with_gaps(
        db, assets, flow, context
    )

    # Get dependency summary
    dependency_summary = await _get_dependency_summary(db)

    # Build enhanced context
    return _build_context_response(
        flow,
        assets_with_gaps,
        all_gaps,
        dependency_summary,
        context,
        selected_asset_ids,
    )


async def mark_generation_failed(db: AsyncSession, flow_id: int) -> None:
    """
    Mark questionnaire generation as failed.

    Args:
        db: Database session
        flow_id: Internal flow ID
    """
    flow_result = await db.execute(
        select(CollectionFlow).where(CollectionFlow.id == flow_id)
    )
    flow = flow_result.scalar_one_or_none()

    if flow:
        if not flow.flow_metadata:
            flow.flow_metadata = {}
        flow.flow_metadata["questionnaire_generating"] = False
        flow.flow_metadata["generation_failed"] = True
        await db.commit()
