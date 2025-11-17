"""
Canonical Application Readiness Gaps Endpoint.

Provides on-demand gap analysis for canonical applications without requiring
an existing assessment flow context.
"""

import logging
from typing import Any, Dict
from uuid import UUID

from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_context_dependency
from app.core.context import RequestContext
from app.core.database import get_db
from app.models.asset.models import Asset
from app.models.canonical_applications import CanonicalApplication
from app.models.collection_flow_application import CollectionFlowApplication
from app.services.assessment.asset_readiness_service import AssetReadinessService

logger = logging.getLogger(__name__)


async def get_canonical_application_readiness_gaps(
    canonical_application_id: UUID,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context_dependency),
) -> Dict[str, Any]:
    """
    Get assessment readiness gaps for all assets in a canonical application.

    Returns a mapping of asset_id -> list of critical/high-priority gap field names.
    This endpoint is used when starting a collection flow from the "New Assessment" modal
    where no assessment flow exists yet.

    Args:
        canonical_application_id: Canonical application UUID
        db: Database session (injected)
        context: Request context with tenant scoping (injected)

    Returns:
        Dict with:
        {
            "canonical_application_id": str,
            "canonical_application_name": str,
            "missing_attributes": Dict[str, List[str]],  # asset_id -> gap field names
            "asset_count": int,
            "not_ready_count": int
        }

    Raises:
        HTTPException 404: If canonical application not found
        HTTPException 500: If gap analysis fails
    """
    try:
        # Verify canonical application exists with tenant scoping
        app_query = select(CanonicalApplication).where(
            CanonicalApplication.id == canonical_application_id,
            CanonicalApplication.client_account_id == context.client_account_id,
            CanonicalApplication.engagement_id == context.engagement_id,
        )
        result = await db.execute(app_query)
        canonical_app = result.scalar_one_or_none()

        if not canonical_app:
            raise HTTPException(
                status_code=404,
                detail=f"Canonical application {canonical_application_id} not found",
            )

        # Get all assets linked to this canonical application
        assets_query = (
            select(Asset)
            .join(
                CollectionFlowApplication,
                CollectionFlowApplication.asset_id == Asset.id,
            )
            .where(
                CollectionFlowApplication.canonical_application_id
                == canonical_application_id,
                CollectionFlowApplication.client_account_id
                == context.client_account_id,
                CollectionFlowApplication.engagement_id == context.engagement_id,
                Asset.deleted_at.is_(
                    None
                ),  # CC FIX: Asset uses deleted_at, not is_deleted
            )
        )
        result = await db.execute(assets_query)
        assets = result.scalars().all()

        if not assets:
            logger.warning(
                f"No assets found for canonical application {canonical_application_id}"
            )
            return {
                "canonical_application_id": str(canonical_application_id),
                "canonical_application_name": canonical_app.canonical_name,
                "missing_attributes": {},
                "asset_count": 0,
                "not_ready_count": 0,
            }

        # Analyze readiness for each asset and collect gap fields
        readiness_service = AssetReadinessService()  # CC FIX: No db in constructor
        missing_attributes: Dict[str, list[str]] = {}
        not_ready_count = 0

        for asset in assets:
            # Run gap analysis for this asset
            readiness_result = await readiness_service.analyze_asset_readiness(
                asset_id=asset.id,
                client_account_id=context.client_account_id,
                engagement_id=context.engagement_id,
                db=db,  # CC FIX: Pass db to method, not constructor
            )

            # If asset is not ready, collect critical/high-priority gap field names
            # CC FIX: readiness_result is ComprehensiveGapReport object, not dict
            if not readiness_result.is_ready_for_assessment:
                not_ready_count += 1
                # critical_gaps and high_priority_gaps are List[str] of field names
                gap_fields = list(
                    set(
                        readiness_result.critical_gaps
                        + readiness_result.high_priority_gaps
                    )
                )

                if gap_fields:
                    missing_attributes[str(asset.id)] = gap_fields

        logger.info(
            f"✅ Analyzed readiness gaps for canonical application {canonical_application_id}: "
            f"{len(assets)} assets, {not_ready_count} not ready, "
            f"{len(missing_attributes)} assets with gaps"
        )

        return {
            "canonical_application_id": str(canonical_application_id),
            "canonical_application_name": canonical_app.canonical_name,
            "missing_attributes": missing_attributes,
            "asset_count": len(assets),
            "not_ready_count": not_ready_count,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to get readiness gaps for canonical application {canonical_application_id}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to analyze readiness gaps: {str(e)}"
        )
