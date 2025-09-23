"""
Collection Agent Questionnaire Helpers
Utility functions for building agent context and managing generation state.
"""

import logging
from typing import Dict, Any, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.context import RequestContext
from app.models import Asset
from app.models.collection_flow import CollectionFlow

logger = logging.getLogger(__name__)


async def build_agent_context(
    db: AsyncSession,
    flow_id: int,
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
    # Get flow details
    flow_result = await db.execute(
        select(CollectionFlow).where(CollectionFlow.id == flow_id)
    )
    flow = flow_result.scalar_one()

    # Get assets
    assets_query = select(Asset).where(
        Asset.engagement_id == context.engagement_id,
        Asset.client_account_id == context.client_account_id,
    )

    if selected_asset_ids:
        assets_query = assets_query.where(
            Asset.id.in_([UUID(aid) for aid in selected_asset_ids])
        )

    assets_result = await db.execute(assets_query)
    assets = assets_result.scalars().all()

    # Build context
    return {
        "flow_id": str(flow.flow_id),
        "scope": (
            flow.collection_config.get("scope", "engagement")
            if flow.collection_config
            else "engagement"
        ),
        "selected_asset_ids": selected_asset_ids or [],
        "assets": [
            {
                "id": str(asset.id),
                "name": asset.name or asset.application_name,
                "type": asset.asset_type,
                "completeness": calculate_completeness(asset),
                "gaps": identify_gaps(asset),
            }
            for asset in assets
        ],
        "gaps": [],  # TODO: Get actual gaps from gap analysis
        "tenant_id": str(context.client_account_id),
        "engagement_id": str(context.engagement_id),
    }


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


def calculate_completeness(asset: Asset) -> float:
    """
    Calculate asset completeness score based on filled fields.

    Args:
        asset: Asset instance to evaluate

    Returns:
        Completeness score between 0.0 and 1.0
    """
    required_fields = [
        "name",
        "asset_type",
        "description",
        "business_criticality",
        "technical_stack",
        "deployment_environment",
    ]
    optional_fields = [
        "data_classification",
        "compliance_requirements",
        "disaster_recovery",
        "maintenance_windows",
    ]

    required_complete = sum(
        1 for field in required_fields if getattr(asset, field, None) is not None
    ) / len(required_fields)

    optional_complete = (
        sum(1 for field in optional_fields if getattr(asset, field, None) is not None)
        / len(optional_fields)
        if optional_fields
        else 0
    )

    return (required_complete * 0.7) + (optional_complete * 0.3)


def identify_gaps(asset: Asset) -> list[str]:
    """
    Identify data gaps in asset based on missing critical fields.

    Args:
        asset: Asset instance to evaluate

    Returns:
        List of gap descriptions
    """
    gaps = []
    critical_fields = {
        "business_criticality": "Business criticality not specified",
        "technical_stack": "Technical stack information missing",
        "deployment_environment": "Deployment environment not documented",
        "data_classification": "Data classification required",
    }

    for field, message in critical_fields.items():
        if not getattr(asset, field, None):
            gaps.append(message)

    return gaps
