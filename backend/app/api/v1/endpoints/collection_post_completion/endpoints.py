"""
Collection Post-Completion API Endpoints

Provides API endpoints for resolving unmapped assets to canonical applications
after collection flow completion, enabling seamless transition to Assessment.

This minimal implementation reuses existing infrastructure:
- CollectionFlowApplication model (already has asset_id + canonical_application_id)
- ApplicationDeduplicationService (battle-tested deduplication logic)
- TenantMemoryManager for multi-tenant isolation

Per ADR-016, Collection Flow owns data enrichment including asset resolution.
"""

import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.auth_utils import get_current_user
from app.core.context import get_request_context, RequestContext
from app.core.database import get_db
from app.models import User
from app.models.canonical_applications import (
    CollectionFlowApplication,
    CanonicalApplication,
)
from app.models.asset import Asset

from .schemas import (
    LinkAssetRequest,
    UnmappedAssetResponse,
    LinkAssetResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ========================================
# ENDPOINTS
# ========================================


@router.get("/{flow_id}/unmapped-assets", response_model=List[UnmappedAssetResponse])
async def get_unmapped_assets_in_collection(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context: RequestContext = Depends(get_request_context),
) -> List[UnmappedAssetResponse]:
    """
    Get collection flow applications with assets but no canonical mapping.

    This endpoint identifies assets that have been collected but not yet mapped
    to canonical applications, which is required before Assessment can begin.

    Args:
        flow_id: UUID of the collection flow (master flow ID from MFO)

    Returns:
        List of unmapped assets with their details

    Security:
        - Validates tenant scoping (client_account_id + engagement_id)
        - Only returns assets belonging to the user's engagement
    """
    try:
        flow_uuid = UUID(flow_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid flow_id format: {flow_id}",
        )

    # Validate context has required tenant scoping
    if not context.client_account_id or not context.engagement_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing tenant context (client_account_id or engagement_id)",
        )

    logger.info(
        f"Fetching unmapped assets for collection flow {flow_id}, "
        f"client={context.client_account_id}, engagement={context.engagement_id}"
    )

    try:
        # Query collection_flow_applications WHERE asset_id IS NOT NULL
        # AND canonical_application_id IS NULL (unmapped condition)
        # Join with assets table for name and type
        stmt = (
            select(
                CollectionFlowApplication.id.label("collection_app_id"),
                CollectionFlowApplication.asset_id,
                CollectionFlowApplication.application_name,
                Asset.name.label("asset_name"),
                Asset.asset_type,
            )
            .join(
                Asset,
                CollectionFlowApplication.asset_id == Asset.id,
            )
            .where(
                and_(
                    CollectionFlowApplication.collection_flow_id == flow_uuid,
                    CollectionFlowApplication.asset_id.is_not(None),
                    CollectionFlowApplication.canonical_application_id.is_(None),
                    CollectionFlowApplication.client_account_id
                    == UUID(context.client_account_id),
                    CollectionFlowApplication.engagement_id
                    == UUID(context.engagement_id),
                )
            )
            .order_by(Asset.name)
        )

        result = await db.execute(stmt)
        rows = result.fetchall()

        unmapped_assets = [
            UnmappedAssetResponse(
                collection_app_id=str(row.collection_app_id),
                asset_id=str(row.asset_id),
                asset_name=row.asset_name,
                asset_type=row.asset_type,
                application_name=row.application_name,
            )
            for row in rows
        ]

        logger.info(
            f"Found {len(unmapped_assets)} unmapped assets for collection flow {flow_id}"
        )

        return unmapped_assets

    except Exception as e:
        logger.error(
            f"Failed to fetch unmapped assets for collection flow {flow_id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch unmapped assets: {str(e)}",
        )


@router.post("/{flow_id}/link-asset-to-canonical", response_model=LinkAssetResponse)
async def link_asset_to_canonical_application(
    flow_id: str,
    request: LinkAssetRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context: RequestContext = Depends(get_request_context),
) -> LinkAssetResponse:
    """
    Map an asset to a canonical application using existing deduplication service.

    This endpoint updates the collection_flow_application record to link an asset
    with a canonical application, enabling Assessment flow to use properly resolved
    application data.

    Reuses: canonical_operations.create_collection_flow_link() for consistency
    with existing application deduplication workflow.

    Args:
        flow_id: UUID of the collection flow (master flow ID from MFO)
        request: Link request containing asset_id and canonical_application_id

    Returns:
        Confirmation of successful link with mapping metadata

    Security:
        - Validates tenant scoping
        - Verifies asset and canonical application belong to user's engagement
        - Uses atomic transaction for data integrity
    """
    try:
        flow_uuid = UUID(flow_id)
        asset_uuid = UUID(request.asset_id)
        canonical_app_uuid = UUID(request.canonical_application_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid UUID format: {str(e)}",
        )

    # Validate context has required tenant scoping
    if not context.client_account_id or not context.engagement_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing tenant context (client_account_id or engagement_id)",
        )

    logger.info(
        f"Linking asset {request.asset_id} to canonical application "
        f"{request.canonical_application_id} for collection flow {flow_id}"
    )

    try:
        # STEP 1: Verify asset exists and belongs to user's engagement
        asset_stmt = select(Asset).where(
            and_(
                Asset.id == asset_uuid,
                Asset.client_account_id == UUID(context.client_account_id),
                Asset.engagement_id == UUID(context.engagement_id),
            )
        )
        asset_result = await db.execute(asset_stmt)
        asset = asset_result.scalar_one_or_none()

        if not asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Asset {request.asset_id} not found or does not belong to engagement",
            )

        # STEP 2: Verify canonical application exists and belongs to engagement
        canonical_stmt = select(CanonicalApplication).where(
            and_(
                CanonicalApplication.id == canonical_app_uuid,
                CanonicalApplication.client_account_id
                == UUID(context.client_account_id),
                CanonicalApplication.engagement_id == UUID(context.engagement_id),
            )
        )
        canonical_result = await db.execute(canonical_stmt)
        canonical_app = canonical_result.scalar_one_or_none()

        if not canonical_app:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    f"Canonical application {request.canonical_application_id} "
                    f"not found or does not belong to engagement"
                ),
            )

        # STEP 3: Find the collection_flow_application record to update
        cfa_stmt = select(CollectionFlowApplication).where(
            and_(
                CollectionFlowApplication.collection_flow_id == flow_uuid,
                CollectionFlowApplication.asset_id == asset_uuid,
                CollectionFlowApplication.client_account_id
                == UUID(context.client_account_id),
                CollectionFlowApplication.engagement_id == UUID(context.engagement_id),
            )
        )
        cfa_result = await db.execute(cfa_stmt)
        collection_app = cfa_result.scalar_one_or_none()

        if not collection_app:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection flow application record not found for asset {request.asset_id}",
            )

        # STEP 4: Update the record with canonical application link
        # This sets canonical_application_id, deduplication_method, and match_confidence
        collection_app.canonical_application_id = canonical_app_uuid
        collection_app.deduplication_method = request.deduplication_method
        collection_app.match_confidence = request.match_confidence

        # Commit the transaction atomically
        await db.flush()
        await db.commit()

        logger.info(
            f"Successfully linked asset {request.asset_id} to canonical application "
            f"{canonical_app.canonical_name} (method={request.deduplication_method}, "
            f"confidence={request.match_confidence})"
        )

        return LinkAssetResponse(
            success=True,
            collection_app_id=str(collection_app.id),
            asset_id=str(asset_uuid),
            canonical_application_id=str(canonical_app_uuid),
            canonical_name=canonical_app.canonical_name,
            deduplication_method=request.deduplication_method,
            match_confidence=request.match_confidence,
        )

    except HTTPException:
        # Re-raise HTTP exceptions (404, 400, etc.)
        raise
    except Exception as e:
        logger.error(
            f"Failed to link asset {request.asset_id} to canonical application: {e}",
            exc_info=True,
        )
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create asset-to-application link: {str(e)}",
        )


@router.get(
    "/assessment/{assessment_flow_id}/unmapped-assets",
    response_model=List[UnmappedAssetResponse],
)
async def get_unmapped_assets_for_assessment(
    assessment_flow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context: RequestContext = Depends(get_request_context),
) -> List[UnmappedAssetResponse]:
    """
    Get unmapped assets for an assessment flow by looking up its source collection.

    This endpoint accepts an assessment flow ID, looks up the source collection flow ID
    from the assessment's metadata, and returns unmapped assets from that collection.

    Args:
        assessment_flow_id: UUID of the assessment flow (NOT collection flow)

    Returns:
        List of unmapped assets from the source collection flow

    Security:
        - Validates tenant scoping (client_account_id + engagement_id)
        - Verifies assessment flow belongs to user's engagement
    """
    try:
        assessment_uuid = UUID(assessment_flow_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid assessment_flow_id format: {assessment_flow_id}",
        )

    # Validate context has required tenant scoping
    if not context.client_account_id or not context.engagement_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing tenant context (client_account_id or engagement_id)",
        )

    logger.info(
        f"Fetching unmapped assets for assessment flow {assessment_flow_id}, "
        f"client={context.client_account_id}, engagement={context.engagement_id}"
    )

    try:
        # Step 1: Get assessment flow and extract collection_flow_id from metadata
        # MFO Pattern: Check both master_flow_id AND id for compatibility
        from app.models.assessment_flow import AssessmentFlow

        assessment_stmt = select(AssessmentFlow).where(
            and_(
                or_(
                    AssessmentFlow.master_flow_id == assessment_uuid,
                    AssessmentFlow.id == assessment_uuid,
                ),
                AssessmentFlow.client_account_id == UUID(context.client_account_id),
                AssessmentFlow.engagement_id == UUID(context.engagement_id),
            )
        )
        assessment_result = await db.execute(assessment_stmt)
        assessment_flow = assessment_result.scalar_one_or_none()

        if not assessment_flow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Assessment flow {assessment_flow_id} not found or access denied",
            )

        # Step 2: Extract collection_flow_id from assessment metadata
        collection_flow_id = None
        if assessment_flow.flow_metadata and isinstance(
            assessment_flow.flow_metadata, dict
        ):
            source_collection = assessment_flow.flow_metadata.get(
                "source_collection", {}
            )
            if isinstance(source_collection, dict):
                collection_flow_id = source_collection.get("collection_flow_id")

        if not collection_flow_id:
            # Assessment has no source collection - may be standalone
            logger.warning(
                f"Assessment flow {assessment_flow_id} has no source_collection metadata. "
                f"Cannot query unmapped assets. Returning empty list."
            )
            return []

        # Step 3: Query unmapped assets from the source collection
        collection_uuid = UUID(collection_flow_id)

        stmt = (
            select(
                CollectionFlowApplication.id.label("collection_app_id"),
                CollectionFlowApplication.asset_id,
                CollectionFlowApplication.application_name,
                Asset.name.label("asset_name"),
                Asset.asset_type,
            )
            .join(
                Asset,
                CollectionFlowApplication.asset_id == Asset.id,
            )
            .where(
                and_(
                    CollectionFlowApplication.collection_flow_id == collection_uuid,
                    CollectionFlowApplication.asset_id.is_not(None),
                    CollectionFlowApplication.canonical_application_id.is_(None),
                    CollectionFlowApplication.client_account_id
                    == UUID(context.client_account_id),
                    CollectionFlowApplication.engagement_id
                    == UUID(context.engagement_id),
                )
            )
            .order_by(Asset.name)
        )

        result = await db.execute(stmt)
        rows = result.fetchall()

        unmapped_assets = [
            UnmappedAssetResponse(
                collection_app_id=str(row.collection_app_id),
                asset_id=str(row.asset_id),
                asset_name=row.asset_name,
                asset_type=row.asset_type,
                application_name=row.application_name,
            )
            for row in rows
        ]

        logger.info(
            f"Found {len(unmapped_assets)} unmapped assets for assessment flow "
            f"{assessment_flow_id} (from collection {collection_flow_id})"
        )

        return unmapped_assets

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(
            f"Failed to fetch unmapped assets for assessment flow {assessment_flow_id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch unmapped assets: {str(e)}",
        )
