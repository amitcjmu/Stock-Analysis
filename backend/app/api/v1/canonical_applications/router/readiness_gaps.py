"""
Canonical Application Readiness Gaps Endpoint.

Provides on-demand gap analysis for canonical applications without requiring
an existing assessment flow context.
"""

import logging
from typing import Any, Dict
from uuid import UUID

from fastapi import Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context_dependency
from app.core.database import get_db
from app.models.asset.models import Asset
from app.models.canonical_applications import (
    CanonicalApplication,
    CollectionFlowApplication,
)
from app.models.collection_flow import AdaptiveQuestionnaire
from app.services.assessment.asset_readiness_service import AssetReadinessService

logger = logging.getLogger(__name__)


async def get_canonical_application_readiness_gaps(  # noqa: C901
    canonical_application_id: UUID,
    update_database: bool = Query(
        False,
        description="If true, persist readiness results to Asset.assessment_readiness field",
    ),
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
        update_database: If True, persist readiness results to Asset.assessment_readiness
        db: Database session (injected)
        context: Request context with tenant scoping (injected)

    Returns:
        Dict with:
        {
            "canonical_application_id": str,
            "canonical_application_name": str,
            "missing_attributes": Dict[str, List[str]],  # asset_id -> gap field names
            "asset_count": int,
            "not_ready_count": int,
            "updated_count": int  # Only if update_database=True
        }

    Raises:
        HTTPException 404: If canonical application not found
        HTTPException 500: If gap analysis fails
    """
    try:
        # DEBUG: Log parameter value to diagnose persistence issue
        logger.warning(
            f"🔍 DEBUG readiness_gaps endpoint called: "
            f"canonical_app_id={canonical_application_id}, "
            f"update_database={update_database} (type={type(update_database).__name__})"
        )

        # CC FIX: Convert context IDs to UUID objects for database queries
        # Pattern per Serena memory: collection_gaps_qodo_bot_fixes_2025_21
        try:
            client_account_uuid = (
                UUID(context.client_account_id)
                if isinstance(context.client_account_id, str)
                else context.client_account_id
            )
            engagement_uuid = (
                UUID(context.engagement_id)
                if isinstance(context.engagement_id, str)
                else context.engagement_id
            )
        except (ValueError, TypeError) as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid tenant ID format in context: {str(e)}",
            )

        # Verify canonical application exists with tenant scoping
        app_query = select(CanonicalApplication).where(
            CanonicalApplication.id == canonical_application_id,
            CanonicalApplication.client_account_id == client_account_uuid,
            CanonicalApplication.engagement_id == engagement_uuid,
        )
        result = await db.execute(app_query)
        canonical_app = result.scalar_one_or_none()

        if not canonical_app:
            raise HTTPException(
                status_code=404,
                detail=f"Canonical application {canonical_application_id} not found",
            )

        # CC FIX: Eagerly load canonical_name BEFORE session commits to avoid lazy-load errors
        canonical_app_name = canonical_app.canonical_name

        # Get all assets linked to this canonical application
        # CC FIX: Exclude placeholder asset IDs (22222222-...) to prevent data corruption from affecting gap analysis
        assets_query = (
            select(Asset)
            .join(
                CollectionFlowApplication,
                CollectionFlowApplication.asset_id == Asset.id,
            )
            .where(
                CollectionFlowApplication.canonical_application_id
                == canonical_application_id,
                CollectionFlowApplication.client_account_id == client_account_uuid,
                CollectionFlowApplication.engagement_id == engagement_uuid,
                Asset.deleted_at.is_(
                    None
                ),  # CC FIX: Asset uses deleted_at, not is_deleted
                # CC FIX: Exclude placeholder asset IDs (test data corruption)
                ~Asset.id.in_(
                    [
                        UUID("22222222-2222-2222-2222-222222222222"),
                        UUID("22222222-2222-2222-2222-222222222221"),
                    ]
                ),
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
                "canonical_application_name": canonical_app_name,
                "missing_attributes": {},
                "asset_count": 0,
                "not_ready_count": 0,
            }

        # CC FIX: Pre-fetch questionnaire completion status for all assets
        # Assets with completed questionnaires or "no TRUE gaps" failures should be marked ready
        # This aligns with IntelligentGapScanner's assessment readiness criteria
        asset_ids = [asset.id for asset in assets]
        questionnaire_query = select(AdaptiveQuestionnaire).where(
            AdaptiveQuestionnaire.asset_id.in_(asset_ids),
            AdaptiveQuestionnaire.client_account_id == client_account_uuid,
            AdaptiveQuestionnaire.engagement_id == engagement_uuid,
        )
        questionnaire_result = await db.execute(questionnaire_query)
        questionnaires = questionnaire_result.scalars().all()

        # Build lookup: asset_id -> questionnaire status
        # Asset is ready if:
        # 1. Has a completed questionnaire, OR
        # 2. Has a "failed" questionnaire with "No questionnaires could be generated" (no TRUE gaps)
        assets_ready_by_questionnaire: set[UUID] = set()
        for q in questionnaires:
            if q.completion_status == "completed":
                assets_ready_by_questionnaire.add(q.asset_id)
            elif q.completion_status == "failed":
                # CC FIX: "No questionnaires could be generated" = asset has complete data
                description = q.description or ""
                if (
                    "No questionnaires could be generated" in description
                    or "no TRUE gaps" in description.lower()
                ):
                    assets_ready_by_questionnaire.add(q.asset_id)

        logger.info(
            f"📋 Found {len(assets_ready_by_questionnaire)} assets ready by questionnaire completion "
            f"(out of {len(assets)} total assets)"
        )

        # Analyze readiness for each asset and collect gap fields
        readiness_service = AssetReadinessService()  # CC FIX: No db in constructor
        missing_attributes: Dict[str, list[str]] = {}
        not_ready_count = 0
        updated_count = 0

        for asset in assets:
            # CC FIX: Check questionnaire completion FIRST - overrides GapAnalyzer result
            # This ensures consistency with IntelligentGapScanner's assessment readiness criteria
            if asset.id in assets_ready_by_questionnaire:
                # Asset has completed questionnaire or had no TRUE gaps - mark as ready
                is_ready = True
                logger.debug(
                    f"Asset {asset.id} marked ready by questionnaire completion (skipping GapAnalyzer)"
                )
            else:
                # Run gap analysis for this asset
                # CC FIX: Pass UUIDs as strings because analyze_asset_readiness wraps them in UUID()
                readiness_result = await readiness_service.analyze_asset_readiness(
                    asset_id=asset.id,
                    client_account_id=str(client_account_uuid),
                    engagement_id=str(engagement_uuid),
                    db=db,  # CC FIX: Pass db to method, not constructor
                )

                # Determine readiness status
                is_ready = readiness_result.is_ready_for_assessment

                # If asset is not ready by GapAnalyzer, collect critical/high-priority gap field names
                if not is_ready:
                    # critical_gaps and high_priority_gaps are List[str] of field names
                    gap_fields = list(
                        set(
                            readiness_result.critical_gaps
                            + readiness_result.high_priority_gaps
                        )
                    )
                    if gap_fields:
                        missing_attributes[str(asset.id)] = gap_fields

            new_readiness_status = "ready" if is_ready else "not_ready"

            # Update database if requested (ALWAYS update, even if value unchanged)
            # This ensures fresh gap analysis results are persisted to database
            if update_database:
                old_status = asset.assessment_readiness
                asset.assessment_readiness = new_readiness_status
                # CC FIX: Also update sixr_ready for Assessment Flow UI
                asset.sixr_ready = new_readiness_status
                updated_count += 1

                if old_status != new_readiness_status:
                    logger.debug(
                        f"Changed asset {asset.id} readiness: {old_status} → {new_readiness_status}"
                    )
                else:
                    logger.debug(
                        f"Confirmed asset {asset.id} readiness: {new_readiness_status} (unchanged)"
                    )

            # Track not_ready count (gap_fields already collected in the else block above)
            if not is_ready:
                not_ready_count += 1

        # Commit database changes if updates were made
        if update_database and updated_count > 0:
            await db.commit()
            logger.info(
                f"💾 Persisted readiness updates for {updated_count} assets in "
                f"canonical application {canonical_application_id}"
            )

        logger.info(
            f"✅ Analyzed readiness gaps for canonical application {canonical_application_id}: "
            f"{len(assets)} assets, {not_ready_count} not ready, "
            f"{len(missing_attributes)} assets with gaps"
            + (f", {updated_count} DB updates" if update_database else "")
        )

        result = {
            "canonical_application_id": str(canonical_application_id),
            "canonical_application_name": canonical_app_name,
            "missing_attributes": missing_attributes,
            "asset_count": len(assets),
            "not_ready_count": not_ready_count,
        }

        # Add updated_count if database was updated
        if update_database:
            result["updated_count"] = updated_count

        return result

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
