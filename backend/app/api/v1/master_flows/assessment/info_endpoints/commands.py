"""
Assessment information command endpoints.

PUT endpoints for updating assessment data (complexity metrics, etc.).
"""

import logging
from typing import Any, Dict, List
from uuid import uuid4, UUID

from fastapi import Depends, HTTPException
from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context_dependency
from app.core.database import get_db
from app.models.collection_flow.asset_custom_attributes import AssetCustomAttributes
from ..uuid_utils import ensure_uuid
from ..query_helpers import get_asset_ids, get_collection_flow_id

from . import router
from .schemas import ComplexityMetricsUpdate

logger = logging.getLogger(__name__)


@router.put("/{flow_id}/applications/{app_id}/complexity-metrics")
async def update_complexity_metrics(  # noqa: C901
    flow_id: str,
    app_id: str,
    metrics: ComplexityMetricsUpdate,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context_dependency),
) -> Dict[str, Any]:
    """
    Update complexity metrics for an application in assessment flow.

    Stores:
    - complexity_score (1-10) in assets.complexity_score
    - architecture_type in assets.application_type
    - customization_level in asset_custom_attributes.attributes

    CRITICAL: Per CLAUDE.md - PUT requests use request body, NOT query parameters.

    FIX: Frontend passes canonical_application_id (from masterFlowService transformation),
    but we need to update ALL assets in that application group.
    """
    try:
        if metrics.architecture_type not in [
            "Monolithic",
            "Microservices",
            "SOA",
            "Serverless",
            "Event-Driven",
            "Layered",
        ]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid architecture_type: {metrics.architecture_type}",
            )
        if metrics.customization_level not in ["Low", "Medium", "High"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid customization_level: {metrics.customization_level}",
            )

        client_uuid, engagement_uuid = (
            ensure_uuid(context.client_account_id),
            ensure_uuid(context.engagement_id),
        )

        # Get the assessment flow to find application groups
        from app.api.v1.master_flows.assessment.query_helpers import get_assessment_flow

        flow = await get_assessment_flow(db, flow_id, client_uuid, engagement_uuid)

        # CC FIX: Compute application groups on-the-fly if not pre-computed
        # This mirrors the logic in queries.py to handle flows created before groups were stored
        application_groups: List[Dict[str, Any]] = []

        if (
            hasattr(flow, "application_asset_groups")
            and flow.application_asset_groups
            and len(flow.application_asset_groups) > 0
        ):
            # Use pre-computed groups from initialization
            application_groups = flow.application_asset_groups
            logger.info(
                f"Using pre-computed application groups for flow {flow_id} "
                f"({len(application_groups)} groups)"
            )
        else:
            # Compute on-the-fly (fallback for old flows without pre-computed groups)
            asset_ids = get_asset_ids(flow)
            if asset_ids:
                logger.info(
                    f"Computing application groups on-the-fly for flow {flow_id} "
                    f"({len(asset_ids)} assets)"
                )

                from app.services.assessment.application_resolver import (
                    AssessmentApplicationResolver,
                )

                resolver = AssessmentApplicationResolver(
                    db=db,
                    client_account_id=client_uuid,
                    engagement_id=engagement_uuid,
                )

                collection_flow_id = await get_collection_flow_id(flow)
                application_groups_objs = await resolver.resolve_assets_to_applications(
                    asset_ids=[
                        UUID(aid) if isinstance(aid, str) else aid for aid in asset_ids
                    ],
                    collection_flow_id=collection_flow_id,
                )

                # Convert to dict format
                application_groups = [
                    group.model_dump() for group in application_groups_objs
                ]

        # Find the application group that matches app_id (canonical_application_id)
        matching_group = None

        for group in application_groups:
            # Match by canonical_application_id or unmapped key
            if isinstance(group, dict):
                canonical_id = group.get("canonical_application_id")
                if canonical_id and str(canonical_id) == app_id:
                    matching_group = group
                    break
                # Check for unmapped format: unmapped-{application_name}
                if not canonical_id and app_id.startswith("unmapped-"):
                    if group.get("canonical_application_name") in app_id:
                        matching_group = group
                        break

        if not matching_group:
            logger.error(
                f"Application group {app_id} not found. Available groups: "
                f"{[g.get('canonical_application_id') for g in application_groups]}"
            )
            raise HTTPException(
                status_code=404, detail=f"Application group {app_id} not found in flow"
            )

        # Get all asset IDs in this application group
        asset_ids = matching_group.get("asset_ids", [])
        if not asset_ids:
            raise HTTPException(
                status_code=404, detail=f"No assets found for application {app_id}"
            )

        # Convert asset IDs to UUIDs
        asset_uuids = [ensure_uuid(aid) for aid in asset_ids]

        # Update ALL assets in the application group using parameterized query
        # Use PostgreSQL's ANY() function with array binding for SQL injection protection
        update_query = text(
            """
            UPDATE migration.assets
            SET complexity_score = :complexity_score,
                application_type = :application_type,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ANY(:asset_uuids)
              AND client_account_id = :client_account_id
              AND engagement_id = :engagement_id
        """
        )

        result = await db.execute(
            update_query,
            {
                "complexity_score": float(metrics.complexity_score),
                "application_type": metrics.architecture_type,
                "asset_uuids": asset_uuids,  # Pass list directly - PostgreSQL handles array binding
                "client_account_id": client_uuid,
                "engagement_id": engagement_uuid,
            },
        )

        rows_updated = result.rowcount
        logger.info(f"Updated {rows_updated} asset rows with complexity metrics")

        # Update or create asset_custom_attributes for customization_level FOR EACH ASSET
        for asset_uuid in asset_uuids:
            result = await db.execute(
                select(AssetCustomAttributes).where(
                    AssetCustomAttributes.asset_id == asset_uuid,
                    AssetCustomAttributes.client_account_id == client_uuid,
                    AssetCustomAttributes.engagement_id == engagement_uuid,
                )
            )
            custom_attr = result.scalar_one_or_none()

            if custom_attr:
                (attrs := custom_attr.attributes or {}).update(
                    {"customization_level": metrics.customization_level}
                )
                await db.execute(
                    update(AssetCustomAttributes)
                    .where(AssetCustomAttributes.id == custom_attr.id)
                    .values(attributes=attrs)
                )
            else:
                new_attr = AssetCustomAttributes(
                    id=uuid4(),
                    client_account_id=client_uuid,
                    engagement_id=engagement_uuid,
                    asset_id=asset_uuid,
                    asset_type="application",
                    attributes={"customization_level": metrics.customization_level},
                    source="assessment_flow_complexity",
                )
                db.add(new_attr)

        await db.commit()
        logger.info(
            f"Updated complexity metrics for application {app_id} ({rows_updated}/{len(asset_ids)} assets): "
            f"score={metrics.complexity_score}, arch={metrics.architecture_type}, "
            f"custom={metrics.customization_level}"
        )

        return {
            "app_id": app_id,
            "complexity_score": metrics.complexity_score,
            "architecture_type": metrics.architecture_type,
            "customization_level": metrics.customization_level,
        }
    except Exception as e:
        await db.rollback()
        if isinstance(e, HTTPException):
            raise
        logger.error(f"Failed to update complexity metrics for {app_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update complexity metrics: {str(e)}"
        )
