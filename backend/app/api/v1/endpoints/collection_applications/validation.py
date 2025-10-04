"""Validation utilities for collection application selection."""

import logging
from typing import List
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints import collection_validators
from app.models.asset import Asset
from app.models.collection_flow import CollectionFlow

logger = logging.getLogger(__name__)


async def validate_and_normalize_application_ids(
    selected_application_ids: List[str],
    flow_id: str,
) -> List[str]:
    """Normalize and deduplicate application IDs while preserving order.

    Args:
        selected_application_ids: Raw list of application IDs from request
        flow_id: Collection flow ID for logging context

    Returns:
        List of normalized, deduplicated application IDs

    Raises:
        HTTPException: If no valid application IDs provided
    """
    normalized_ids = []
    seen_ids = set()

    for app_id in selected_application_ids:
        # Validate non-empty strings
        if not app_id or not isinstance(app_id, str) or not app_id.strip():
            logger.warning(
                f"Skipping invalid application ID: {repr(app_id)} for flow {flow_id}"
            )
            continue

        normalized_id = app_id.strip()
        if normalized_id not in seen_ids:
            normalized_ids.append(normalized_id)
            seen_ids.add(normalized_id)

    logger.debug(
        f"Normalized application IDs - "
        f"Original: {len(selected_application_ids)}, "
        f"After dedup: {len(normalized_ids)}"
    )

    if not normalized_ids:
        logger.warning(f"No valid application IDs provided for flow {flow_id}")
        raise HTTPException(
            status_code=400,
            detail="No valid application IDs provided. Please select at least one valid application.",
        )

    return normalized_ids


async def validate_applications_ownership(
    db: AsyncSession,
    normalized_ids: List[str],
    engagement_id: UUID,
) -> List[Asset]:
    """Validate that all applications belong to the specified engagement.

    Args:
        db: Database session
        normalized_ids: List of application IDs to validate
        engagement_id: Engagement ID for ownership validation

    Returns:
        List of validated Asset objects

    Raises:
        HTTPException: If validation fails (403 for authorization, 400 for other errors)
    """
    logger.info(
        f"Validating {len(normalized_ids)} applications for engagement {engagement_id}"
    )

    try:
        validated_applications = (
            await collection_validators.validate_applications_exist(
                db, normalized_ids, engagement_id
            )
        )
        logger.info(
            f"Successfully validated {len(validated_applications)} applications"
        )
        return validated_applications

    except Exception as validation_error:
        logger.warning(f"Application validation failed: {validation_error}")

        # Check if it's a validation failure vs permission issue
        error_msg = str(validation_error).lower()
        if (
            "engagement" in error_msg
            or "permission" in error_msg
            or "authorization" in error_msg
        ):
            raise HTTPException(
                status_code=403,
                detail="Authorization failed: Some applications don't belong to your engagement.",
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="Validation failed: Some selected applications are invalid or not found.",
            )


async def load_collection_flow(
    db: AsyncSession,
    flow_id: str,
    engagement_id: UUID,
    client_account_id: UUID,
) -> CollectionFlow:
    """Load collection flow with tenant scoping.

    Args:
        db: Database session
        flow_id: Collection flow ID
        engagement_id: Engagement ID for scoping
        client_account_id: Client account ID for scoping

    Returns:
        CollectionFlow object

    Raises:
        HTTPException: If flow not found
    """
    flow_result = await db.execute(
        select(CollectionFlow)
        .where(CollectionFlow.flow_id == flow_id)
        .where(CollectionFlow.engagement_id == engagement_id)
        .where(CollectionFlow.client_account_id == client_account_id)
    )
    collection_flow = flow_result.scalar_one_or_none()

    if not collection_flow:
        raise HTTPException(404, "Collection flow not found")

    return collection_flow


async def load_asset_with_scoping(
    db: AsyncSession,
    asset_id: str,
    client_account_id: UUID,
    engagement_id: UUID,
) -> Asset | None:
    """Load asset with tenant scoping.

    Args:
        db: Database session
        asset_id: Asset ID to load
        client_account_id: Client account ID for scoping
        engagement_id: Engagement ID for scoping

    Returns:
        Asset object or None if not found/out of scope
    """
    asset = await db.scalar(
        select(Asset).where(
            and_(
                Asset.id == asset_id,
                Asset.client_account_id == client_account_id,
                Asset.engagement_id == engagement_id,
            )
        )
    )

    if not asset:
        logger.warning(f"Asset not found or out of scope: {asset_id}")

    return asset
