"""
Assessment information endpoints.

Endpoints for retrieving assessment applications, readiness, and progress data.
Enhanced in October 2025 with canonical application support.
"""

import logging
from typing import Any, Dict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context_dependency
from app.core.database import get_db
from .helpers import get_missing_critical_attributes, get_actionable_guidance

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
    client_account_id = context.client_account_id
    engagement_id = context.engagement_id

    if not client_account_id:
        raise HTTPException(status_code=400, detail="Client account ID required")

    if not engagement_id:
        raise HTTPException(status_code=400, detail="Engagement ID required")

    try:
        from app.services.assessment.application_resolver import (
            AssessmentApplicationResolver,
        )
        from app.models.assessment_flow import AssessmentFlow
        from sqlalchemy import select

        # Get assessment flow
        query = select(AssessmentFlow).where(
            AssessmentFlow.flow_id == UUID(flow_id),
            AssessmentFlow.client_account_id == UUID(client_account_id),
            AssessmentFlow.engagement_id == UUID(engagement_id),
        )
        result = await db.execute(query)
        flow = result.scalar_one_or_none()

        if not flow:
            raise HTTPException(status_code=404, detail="Assessment flow not found")

        # Use new semantic field with fallback to deprecated field
        asset_ids = flow.selected_asset_ids or flow.selected_application_ids or []

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
            client_account_id=UUID(client_account_id),
            engagement_id=UUID(engagement_id),
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
            # Convert to list of dicts if needed
            if not isinstance(application_groups, list):
                application_groups = []
        else:
            # Compute on-the-fly (fallback for old flows)
            logger.info(
                f"Computing application groups on-the-fly for flow {flow_id} "
                f"({len(asset_ids)} assets)"
            )

            # Get collection_flow_id if available
            collection_flow_id = None
            if flow.flow_metadata and isinstance(flow.flow_metadata, dict):
                source_collection = flow.flow_metadata.get("source_collection", {})
                if isinstance(source_collection, dict):
                    collection_flow_id_str = source_collection.get("collection_flow_id")
                    if collection_flow_id_str:
                        collection_flow_id = UUID(collection_flow_id_str)

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

        return {
            "flow_id": flow_id,
            "applications": application_groups,
            "total_applications": len(application_groups),
            "total_assets": len(asset_ids),
            "unmapped_assets": unmapped_count,
        }

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
    client_account_id = context.client_account_id
    engagement_id = context.engagement_id

    if not client_account_id:
        raise HTTPException(status_code=400, detail="Client account ID required")

    if not engagement_id:
        raise HTTPException(status_code=400, detail="Engagement ID required")

    try:
        from app.models.assessment_flow import AssessmentFlow
        from app.models.asset import Asset
        from app.services.assessment.application_resolver import (
            AssessmentApplicationResolver,
        )
        from sqlalchemy import select

        # Get assessment flow
        query = select(AssessmentFlow).where(
            AssessmentFlow.flow_id == UUID(flow_id),
            AssessmentFlow.client_account_id == UUID(client_account_id),
            AssessmentFlow.engagement_id == UUID(engagement_id),
        )
        result = await db.execute(query)
        flow = result.scalar_one_or_none()

        if not flow:
            raise HTTPException(status_code=404, detail="Assessment flow not found")

        # Use new semantic field with fallback
        asset_ids = flow.selected_asset_ids or flow.selected_application_ids or []

        if not asset_ids:
            return {
                "flow_id": flow_id,
                "readiness_summary": {
                    "total_assets": 0,
                    "ready": 0,
                    "not_ready": 0,
                    "in_progress": 0,
                    "avg_completeness_score": 0.0,
                },
                "enrichment_status": {
                    "compliance_flags": 0,
                    "licenses": 0,
                    "vulnerabilities": 0,
                    "resilience": 0,
                    "dependencies": 0,
                    "product_links": 0,
                    "field_conflicts": 0,
                },
                "blockers": [],
                "actionable_guidance": [],
            }

        # Initialize resolver
        resolver = AssessmentApplicationResolver(
            db=db,
            client_account_id=UUID(client_account_id),
            engagement_id=UUID(engagement_id),
        )

        # Check if flow has pre-computed summaries (fast path)
        if (
            hasattr(flow, "readiness_summary")
            and flow.readiness_summary
            and hasattr(flow, "enrichment_status")
            and flow.enrichment_status
        ):
            readiness = flow.readiness_summary
            enrichment = flow.enrichment_status
            logger.info(f"Using pre-computed readiness for flow {flow_id}")
        else:
            # Compute on-the-fly (fallback)
            logger.info(f"Computing readiness on-the-fly for flow {flow_id}")
            readiness_obj = await resolver.calculate_readiness_summary(
                [UUID(aid) if isinstance(aid, str) else aid for aid in asset_ids]
            )
            enrichment_obj = await resolver.calculate_enrichment_status(
                [UUID(aid) if isinstance(aid, str) else aid for aid in asset_ids]
            )
            readiness = readiness_obj.model_dump()
            enrichment = enrichment_obj.model_dump()

        # Get detailed asset readiness (for blockers)
        assets_query = select(Asset).where(
            Asset.id.in_(
                [UUID(aid) if isinstance(aid, str) else aid for aid in asset_ids]
            ),
            Asset.client_account_id == UUID(client_account_id),
            Asset.engagement_id == UUID(engagement_id),
        )
        assets_result = await db.execute(assets_query)
        assets = assets_result.scalars().all()

        # Build blockers list (assets not ready with missing attributes)
        blockers = []
        for asset in assets:
            if asset.assessment_readiness != "ready":
                missing_attrs = get_missing_critical_attributes(asset)
                blockers.append(
                    {
                        "asset_id": str(asset.id),
                        "asset_name": asset.asset_name or asset.name or "Unknown",
                        "asset_type": asset.asset_type or "unknown",
                        "assessment_readiness": asset.assessment_readiness
                        or "not_ready",
                        "completeness_score": float(
                            asset.assessment_readiness_score or 0.0
                        ),
                        "assessment_blockers": asset.assessment_blockers or [],
                        "missing_critical_attributes": missing_attrs,
                    }
                )

        # Generate actionable guidance
        actionable_guidance = get_actionable_guidance(blockers)

        return {
            "flow_id": flow_id,
            "readiness_summary": readiness,
            "enrichment_status": enrichment,
            "blockers": blockers,
            "actionable_guidance": actionable_guidance,
        }

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
    client_account_id = context.client_account_id
    engagement_id = context.engagement_id

    if not client_account_id:
        raise HTTPException(status_code=400, detail="Client account ID required")

    if not engagement_id:
        raise HTTPException(status_code=400, detail="Engagement ID required")

    try:
        from app.models.assessment_flow import AssessmentFlow
        from app.models.asset import Asset
        from sqlalchemy import select

        # Get assessment flow
        query = select(AssessmentFlow).where(
            AssessmentFlow.flow_id == UUID(flow_id),
            AssessmentFlow.client_account_id == UUID(client_account_id),
            AssessmentFlow.engagement_id == UUID(engagement_id),
        )
        result = await db.execute(query)
        flow = result.scalar_one_or_none()

        if not flow:
            raise HTTPException(status_code=404, detail="Assessment flow not found")

        # Use new semantic field with fallback
        asset_ids = flow.selected_asset_ids or flow.selected_application_ids or []

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
            Asset.client_account_id == UUID(client_account_id),
            Asset.engagement_id == UUID(engagement_id),
        )
        assets_result = await db.execute(assets_query)
        assets = assets_result.scalars().all()

        if not assets:
            return {
                "flow_id": flow_id,
                "categories": [],
                "overall_progress": 0.0,
            }

        # Define attribute categories (22 critical attributes)
        categories = [
            {
                "name": "Infrastructure",
                "attributes": [
                    "asset_name",
                    "technology_stack",
                    "operating_system",
                    "cpu_cores",
                    "memory_gb",
                    "storage_gb",
                ],
                "completed": 0,
                "total": 6 * len(assets),
            },
            {
                "name": "Application",
                "attributes": [
                    "business_criticality",
                    "application_type",
                    "architecture_pattern",
                    "dependencies",
                    "user_base",
                    "data_sensitivity",
                    "compliance_requirements",
                    "sla_requirements",
                ],
                "completed": 0,
                "total": 8 * len(assets),
            },
            {
                "name": "Business Context",
                "attributes": [
                    "business_owner",
                    "annual_operating_cost",
                    "business_value",
                    "strategic_importance",
                ],
                "completed": 0,
                "total": 4 * len(assets),
            },
            {
                "name": "Technical Debt",
                "attributes": [
                    "code_quality_score",
                    "last_update_date",
                    "support_status",
                    "known_vulnerabilities",
                ],
                "completed": 0,
                "total": 4 * len(assets),
            },
        ]

        # Count completed attributes for each asset
        for asset in assets:
            for category in categories:
                for attr_name in category["attributes"]:
                    # Check if attribute has a value
                    attr_value = getattr(asset, attr_name, None)
                    if attr_value is not None:
                        # Handle special cases
                        if isinstance(attr_value, list) and len(attr_value) > 0:
                            category["completed"] += 1
                        elif isinstance(attr_value, dict) and len(attr_value) > 0:
                            category["completed"] += 1
                        elif isinstance(attr_value, str) and attr_value.strip():
                            category["completed"] += 1
                        elif isinstance(attr_value, (int, float)) and attr_value > 0:
                            category["completed"] += 1
                        elif isinstance(attr_value, bool):
                            category["completed"] += 1

                # Calculate progress percent for category
                if category["total"] > 0:
                    category["progress_percent"] = round(
                        (category["completed"] / category["total"]) * 100, 1
                    )
                else:
                    category["progress_percent"] = 0.0

        # Calculate overall progress
        total_completed = sum(c["completed"] for c in categories)
        total_attributes = sum(c["total"] for c in categories)
        overall_progress = (
            round((total_completed / total_attributes) * 100, 1)
            if total_attributes > 0
            else 0.0
        )

        return {
            "flow_id": flow_id,
            "categories": categories,
            "overall_progress": overall_progress,
        }

    except Exception as e:
        logger.error(
            f"Failed to get assessment progress for flow {flow_id}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to get assessment progress: {str(e)}"
        )
