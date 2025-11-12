"""
Assessment information endpoints.

Endpoints for retrieving assessment applications, readiness, and progress data.
Enhanced in October 2025 with canonical application support.
"""

import logging
from typing import Any, Dict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context_dependency
from app.core.database import get_db
from app.utils.json_sanitization import sanitize_for_json
from .helpers import get_missing_critical_attributes, categorize_missing_attributes
from .uuid_utils import ensure_uuid
from .query_helpers import get_assessment_flow, get_asset_ids, get_collection_flow_id
from .progress_calculator import calculate_progress_categories

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{flow_id}/assessment-applications")
async def get_assessment_applications_via_master(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context_dependency),
) -> Dict[str, Any]:
    """
    Get assessment flow applications with canonical application grouping.

    ENHANCED (October 2025): Returns application-centric view using
    canonical_applications and collection_flow_applications junction table.
    Multiple assets (server, database, network_device) are grouped under
    their canonical application.

    Returns:
        Application groups with:
        - canonical_application_id (or None for unmapped)
        - canonical_application_name
        - asset_ids (list of assets in this app)
        - asset_types (server, database, etc.)
        - readiness_summary (how many assets ready/not_ready)
    """
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
                    f"Expected 'application_asset_groups' to be a list for flow {flow_id}, "
                    f"but got {type(application_groups)}. Resetting to empty list."
                )
                application_groups = []
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
    """
    Get detailed assessment readiness information.

    Returns:
        - Asset-level readiness status
        - Missing attributes per asset (22 critical attributes)
        - Assessment blockers with actionable guidance
        - Completeness scores
        - Enrichment status summary

    Use Case: Powers the ReadinessDashboard widget in frontend.
    """
    try:
        from app.models.asset import Asset
        from app.services.assessment.application_resolver import (
            AssessmentApplicationResolver,
        )
        from sqlalchemy import select

        # Get assessment flow with tenant scoping
        flow = await get_assessment_flow(
            db, flow_id, context.client_account_id, context.engagement_id
        )

        # Get asset IDs with semantic field fallback
        asset_ids = get_asset_ids(flow)

        if not asset_ids:
            return {
                "total_assets": 0,  # ← Root level per frontend type
                "readiness_summary": {
                    "ready": 0,
                    "not_ready": 0,
                    "in_progress": 0,
                    "avg_completeness_score": 0.0,
                },
                "asset_details": [],  # ← Renamed from "blockers" to match frontend
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

                # Categorize for frontend (infrastructure/application/business/technical_debt)
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
                "total_assets": total_assets,  # ← Root level per frontend type
                "readiness_summary": readiness_clean,  # ← Without total_assets
                "asset_details": blockers,  # ← Renamed from "blockers" to match frontend
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
    """
    Get attribute-level assessment progress tracking.

    Returns progress by category:
    - Infrastructure (6 attributes)
    - Application (8 attributes)
    - Business Context (4 attributes)
    - Technical Debt (4 attributes)

    Use Case: Powers the ProgressTracker widget in frontend.
    """
    try:
        from app.models.asset import Asset
        from sqlalchemy import select

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


class ComplexityMetricsUpdate(BaseModel):
    """Request body for complexity metrics update."""

    complexity_score: int = Field(
        ..., ge=1, le=10, description="Complexity score from 1-10"
    )
    architecture_type: str = Field(
        ..., description="Architecture type (Monolithic, Microservices, etc.)"
    )
    customization_level: str = Field(
        ..., description="Customization level (Low, Medium, High)"
    )


@router.put("/{flow_id}/applications/{app_id}/complexity-metrics")
async def update_complexity_metrics(
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
    """
    from sqlalchemy import select, update
    from app.models.asset import Asset
    from app.models.collection_flow.asset_custom_attributes import AssetCustomAttribute

    try:
        # Validate architecture_type and customization_level
        # (complexity_score already validated by Field(..., ge=1, le=10))

        valid_arch_types = [
            "Monolithic",
            "Microservices",
            "SOA",
            "Serverless",
            "Event-Driven",
            "Layered",
        ]
        if metrics.architecture_type not in valid_arch_types:
            raise HTTPException(
                status_code=400,
                detail=f"architecture_type must be one of: {', '.join(valid_arch_types)}",
            )

        valid_custom_levels = ["Low", "Medium", "High"]
        if metrics.customization_level not in valid_custom_levels:
            raise HTTPException(
                status_code=400,
                detail=f"customization_level must be one of: {', '.join(valid_custom_levels)}",
            )

        app_uuid = ensure_uuid(app_id)
        client_uuid = ensure_uuid(context.client_account_id)
        engagement_uuid = ensure_uuid(context.engagement_id)

        # Update assets table: complexity_score and application_type
        await db.execute(
            update(Asset)
            .where(
                Asset.id == app_uuid,
                Asset.client_account_id == client_uuid,
                Asset.engagement_id == engagement_uuid,
            )
            .values(
                complexity_score=float(metrics.complexity_score),
                application_type=metrics.architecture_type,
            )
        )

        # Update or create asset_custom_attributes for customization_level
        result = await db.execute(
            select(AssetCustomAttribute).where(
                AssetCustomAttribute.asset_id == app_uuid,
                AssetCustomAttribute.client_account_id == client_uuid,
                AssetCustomAttribute.engagement_id == engagement_uuid,
            )
        )
        custom_attr = result.scalar_one_or_none()

        if custom_attr:
            # Update existing attributes
            attributes = custom_attr.attributes or {}
            attributes["customization_level"] = metrics.customization_level
            await db.execute(
                update(AssetCustomAttribute)
                .where(AssetCustomAttribute.id == custom_attr.id)
                .values(attributes=attributes)
            )
        else:
            # Create new custom attribute record
            from uuid import uuid4

            new_attr = AssetCustomAttribute(
                id=uuid4(),
                client_account_id=client_uuid,
                engagement_id=engagement_uuid,
                asset_id=app_uuid,
                asset_type="application",
                attributes={"customization_level": metrics.customization_level},
                source="assessment_flow_complexity",
            )
            db.add(new_attr)

        await db.commit()

        logger.info(
            f"Updated complexity metrics for app {app_id}: "
            f"score={metrics.complexity_score}, arch={metrics.architecture_type}, custom={metrics.customization_level}"
        )

        return {
            "success": True,
            "app_id": app_id,
            "complexity_score": metrics.complexity_score,
            "architecture_type": metrics.architecture_type,
            "customization_level": metrics.customization_level,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update complexity metrics for {app_id}: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to update complexity metrics: {str(e)}"
        )
