"""
Assessment information query endpoints.

GET endpoints for retrieving assessment applications, readiness, and progress data.
Enhanced in October 2025 with saved complexity metrics support.

Note: GAP-4 FIX endpoints (components, tech-debt, sixr-decisions, treatments)
have been moved to analysis_queries.py as part of modularization.
"""

import logging
from typing import Any, Dict
from uuid import UUID

from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context_dependency
from app.core.database import get_db
from app.models.asset import Asset
from app.models.collection_flow.asset_custom_attributes import AssetCustomAttributes
from app.utils.json_sanitization import sanitize_for_json
from ..helpers import get_missing_critical_attributes, categorize_missing_attributes
from ..uuid_utils import ensure_uuid
from ..query_helpers import get_assessment_flow, get_asset_ids, get_collection_flow_id
from ..progress_calculator import calculate_progress_categories
from .readiness_utils import refresh_readiness_for_groups

from . import router

logger = logging.getLogger(__name__)


@router.get("/{flow_id}/assessment-applications")
async def get_assessment_applications_via_master(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context_dependency),
) -> Dict[str, Any]:
    """Get assessment applications with canonical grouping and saved complexity metrics."""
    try:
        from app.services.assessment.application_resolver import (
            AssessmentApplicationResolver,
        )

        # Get assessment flow with tenant scoping
        flow = await get_assessment_flow(
            db, flow_id, context.client_account_id, context.engagement_id
        )

        # Get asset IDs with semantic field fallback
        asset_ids = get_asset_ids(flow)

        if not asset_ids:
            return {
                "flow_id": flow_id,
                "applications": [],
                "total_applications": 0,
                "total_assets": 0,
                "unmapped_assets": 0,
            }

        # Initialize resolver
        resolver = AssessmentApplicationResolver(
            db=db,
            client_account_id=ensure_uuid(context.client_account_id),
            engagement_id=ensure_uuid(context.engagement_id),
        )

        # Check if flow has pre-computed application_asset_groups (fast path)
        if (
            hasattr(flow, "application_asset_groups")
            and flow.application_asset_groups
            and len(flow.application_asset_groups) > 0
        ):
            # Use pre-computed groups from initialization
            logger.info(
                f"Using pre-computed application groups for flow {flow_id} "
                f"({len(flow.application_asset_groups)} groups)"
            )
            application_groups = flow.application_asset_groups
            # Validate data type and handle corruption gracefully
            if not isinstance(application_groups, list):
                logger.warning(
                    f"Expected 'application_asset_groups' to be a list for flow "
                    f"{flow_id}, but got {type(application_groups)}. "
                    "Resetting to empty list."
                )
                application_groups = []
            else:
                # FIX: Refresh readiness_summary from current asset state
                # Pre-computed groups may have stale readiness data (Issue #XXX)
                application_groups = await refresh_readiness_for_groups(
                    db,
                    application_groups,
                    context.client_account_id,
                    context.engagement_id,
                )
        else:
            # Compute on-the-fly (fallback for old flows)
            logger.info(
                f"Computing application groups on-the-fly for flow {flow_id} "
                f"({len(asset_ids)} assets)"
            )

            # Get collection_flow_id if available
            collection_flow_id = await get_collection_flow_id(flow)

            # Resolve assets to applications using AssessmentApplicationResolver
            application_groups_objs = await resolver.resolve_assets_to_applications(
                asset_ids=[
                    UUID(aid) if isinstance(aid, str) else aid for aid in asset_ids
                ],
                collection_flow_id=collection_flow_id,
            )

            # Convert to dict format for response
            application_groups = [
                group.model_dump() for group in application_groups_objs
            ]

        # Calculate unmapped count
        unmapped_count = sum(
            1
            for group in application_groups
            if group.get("canonical_application_id") is None
        )

        # Enhance application groups with saved complexity metrics from assets table
        # Fix for: Complexity metrics saved but reset on page reload
        for group in application_groups:
            group_asset_ids = group.get("asset_ids", [])
            if not group_asset_ids:
                continue

            # Query first asset in group for complexity metrics
            first_asset_id = group_asset_ids[0]

            # Get complexity_score and application_type from assets table
            asset_result = await db.execute(
                select(Asset.complexity_score, Asset.application_type).where(
                    Asset.id == ensure_uuid(first_asset_id),
                    Asset.client_account_id == ensure_uuid(context.client_account_id),
                    Asset.engagement_id == ensure_uuid(context.engagement_id),
                )
            )
            asset_row = asset_result.first()

            if asset_row:
                # Add saved metrics to group
                if asset_row.complexity_score is not None:
                    group["complexity_score"] = float(asset_row.complexity_score)
                if asset_row.application_type:
                    group["application_type"] = asset_row.application_type

            # Get customization_level from asset_custom_attributes
            custom_attr_result = await db.execute(
                select(AssetCustomAttributes.attributes).where(
                    AssetCustomAttributes.asset_id == ensure_uuid(first_asset_id),
                    AssetCustomAttributes.client_account_id
                    == ensure_uuid(context.client_account_id),
                    AssetCustomAttributes.engagement_id
                    == ensure_uuid(context.engagement_id),
                )
            )
            custom_attr_row = custom_attr_result.first()

            if custom_attr_row and custom_attr_row.attributes:
                customization_level = custom_attr_row.attributes.get(
                    "customization_level"
                )
                if customization_level:
                    group["customization_level"] = customization_level

        return sanitize_for_json(
            {
                "flow_id": flow_id,
                "applications": application_groups,
                "total_applications": len(application_groups),
                "total_assets": len(asset_ids),
                "unmapped_assets": unmapped_count,
            }
        )

    except Exception as e:
        logger.error(
            f"Failed to get assessment applications for flow {flow_id}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to get assessment applications: {str(e)}"
        )


@router.get("/{flow_id}/assessment-readiness")
async def get_assessment_readiness(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context_dependency),
) -> Dict[str, Any]:
    """Get assessment readiness with asset-level status and missing attributes."""
    try:
        from app.services.assessment.application_resolver import (
            AssessmentApplicationResolver,
        )

        # Get assessment flow with tenant scoping
        flow = await get_assessment_flow(
            db, flow_id, context.client_account_id, context.engagement_id
        )

        # Get asset IDs with semantic field fallback
        asset_ids = get_asset_ids(flow)

        if not asset_ids:
            return {
                "total_assets": 0,  # Root level per frontend type
                "readiness_summary": {
                    "ready": 0,
                    "not_ready": 0,
                    "in_progress": 0,
                    "avg_completeness_score": 0.0,
                },
                "asset_details": [],  # Renamed from "blockers" to match frontend
            }

        # Initialize resolver
        resolver = AssessmentApplicationResolver(
            db=db,
            client_account_id=ensure_uuid(context.client_account_id),
            engagement_id=ensure_uuid(context.engagement_id),
        )

        # Check if flow has pre-computed summaries (fast path)
        if (
            hasattr(flow, "readiness_summary")
            and flow.readiness_summary
            and hasattr(flow, "enrichment_status")
            and flow.enrichment_status
        ):
            readiness = flow.readiness_summary
            logger.info(f"Using pre-computed readiness for flow {flow_id}")
        else:
            # Compute on-the-fly (fallback)
            logger.info(f"Computing readiness on-the-fly for flow {flow_id}")
            readiness_obj = await resolver.calculate_readiness_summary(
                [UUID(aid) if isinstance(aid, str) else aid for aid in asset_ids]
            )
            readiness = readiness_obj.model_dump()

        # Get detailed asset readiness (for blockers)
        assets_query = select(Asset).where(
            Asset.id.in_(
                [UUID(aid) if isinstance(aid, str) else aid for aid in asset_ids]
            ),
            Asset.client_account_id == ensure_uuid(context.client_account_id),
            Asset.engagement_id == ensure_uuid(context.engagement_id),
        )
        assets_result = await db.execute(assets_query)
        assets = assets_result.scalars().all()

        # Build blockers list (assets not ready with missing attributes)
        blockers = []
        for asset in assets:
            if asset.assessment_readiness != "ready":
                # Get flat list of missing attributes
                missing_attrs_flat = get_missing_critical_attributes(asset)

                # Categorize for frontend (infrastructure/application/business/etc)
                missing_attrs_categorized = categorize_missing_attributes(
                    missing_attrs_flat
                )

                blockers.append(
                    {
                        "asset_id": str(asset.id),
                        "asset_name": asset.asset_name or asset.name or "Unknown",
                        "asset_type": asset.asset_type or "unknown",
                        "assessment_readiness": asset.assessment_readiness
                        or "not_ready",
                        "assessment_readiness_score": float(
                            asset.assessment_readiness_score or 0.0
                        ),
                        "completeness_score": float(
                            asset.assessment_readiness_score or 0.0
                        ),
                        "assessment_blockers": asset.assessment_blockers or [],
                        "missing_attributes": missing_attrs_categorized,
                    }
                )

        # Extract total_assets from readiness_summary for root-level placement
        # Frontend expects total_assets at root, not nested in readiness_summary
        total_assets = readiness.get("total_assets", len(assets))

        # Remove total_assets from nested readiness_summary to match frontend type
        readiness_clean = (
            {k: v for k, v in readiness.items() if k != "total_assets"}
            if isinstance(readiness, dict)
            else readiness
        )

        return sanitize_for_json(
            {
                "total_assets": total_assets,  # Root level per frontend type
                "readiness_summary": readiness_clean,  # Without total_assets
                "asset_details": blockers,  # Renamed from "blockers"
            }
        )

    except Exception as e:
        logger.error(
            f"Failed to get assessment readiness for flow {flow_id}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to get assessment readiness: {str(e)}"
        )


@router.get("/{flow_id}/assessment-progress")
async def get_assessment_progress(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context_dependency),
) -> Dict[str, Any]:
    """Get attribute-level progress by category (infrastructure/app/business/tech-debt)."""
    try:
        # Get assessment flow with tenant scoping
        flow = await get_assessment_flow(
            db, flow_id, context.client_account_id, context.engagement_id
        )

        # Get asset IDs with semantic field fallback
        asset_ids = get_asset_ids(flow)

        if not asset_ids:
            return {
                "flow_id": flow_id,
                "categories": [],
                "overall_progress": 0.0,
            }

        # Get all assets
        assets_query = select(Asset).where(
            Asset.id.in_(
                [UUID(aid) if isinstance(aid, str) else aid for aid in asset_ids]
            ),
            Asset.client_account_id == ensure_uuid(context.client_account_id),
            Asset.engagement_id == ensure_uuid(context.engagement_id),
        )
        assets_result = await db.execute(assets_query)
        assets = assets_result.scalars().all()

        if not assets:
            return {
                "flow_id": flow_id,
                "categories": [],
                "overall_progress": 0.0,
            }

        # Calculate progress by category
        progress_data = calculate_progress_categories(assets)

        return sanitize_for_json(
            {
                "flow_id": flow_id,
                **progress_data,
            }
        )

    except Exception as e:
        logger.error(
            f"Failed to get assessment progress for flow {flow_id}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to get assessment progress: {str(e)}"
        )
