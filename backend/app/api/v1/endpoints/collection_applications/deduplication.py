"""Application deduplication and normalization logic."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset
from app.models.canonical_applications.collection_flow_app import (
    CollectionFlowApplication,
)
from app.models.collection_flow import CollectionFlow
from app.services.application_deduplication_service import create_deduplication_service

logger = logging.getLogger(__name__)


async def process_applications_with_deduplication(
    db: AsyncSession,
    normalized_ids: List[str],
    collection_flow: CollectionFlow,
    client_account_id: UUID,
    engagement_id: UUID,
    user_id: UUID,  # Fixed: Should be UUID, not int
) -> tuple[int, List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Process applications with deduplication service.

    Args:
        db: Database session
        normalized_ids: List of asset/application IDs
        collection_flow: Collection flow object
        client_account_id: Client account ID (UUID or string)
        engagement_id: Engagement ID (UUID or string)
        user_id: Current user ID (UUID or string)

    Returns:
        Tuple of (processed_count, application_details, deduplication_results)
    """
    from app.api.v1.endpoints.collection_applications.validation import (
        load_asset_with_scoping,
    )

    dedup_service = create_deduplication_service()
    processed_count = 0
    application_details = []
    deduplication_results = []

    for asset_id in normalized_ids:
        try:
            # Load asset with tenant scoping
            asset = await load_asset_with_scoping(
                db, asset_id, client_account_id, engagement_id
            )
            if not asset:
                continue

            # Get application name
            application_name = asset.name or asset.application_name
            if not application_name:
                logger.warning(f"Asset {asset_id} has no name or application_name")
                continue

            # Run deduplication service
            dedup_result = await _deduplicate_application(
                db=db,
                dedup_service=dedup_service,
                application_name=application_name,
                asset=asset,
                collection_flow=collection_flow,
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                user_id=user_id,
            )

            if dedup_result:
                application_details.append(
                    {
                        "asset_id": asset_id,
                        "application_name": application_name,
                        "environment": getattr(asset, "environment", "unknown"),
                        "selected_at": datetime.now(timezone.utc).isoformat(),
                    }
                )
                deduplication_results.append(dedup_result)
                processed_count += 1
                logger.info(f"Successfully processed application: {application_name}")

        except Exception as e:
            logger.error(f"Failed to process asset {asset_id}: {str(e)}")
            continue

    return processed_count, application_details, deduplication_results


async def _deduplicate_application(
    db: AsyncSession,
    dedup_service: Any,
    application_name: str,
    asset: Asset,
    collection_flow: CollectionFlow,
    client_account_id: UUID,
    engagement_id: UUID,
    user_id: UUID,  # Fixed: Should be UUID, not int
) -> Dict[str, Any] | None:
    """Run deduplication service for a single application.

    Returns:
        Deduplication result dict or None if failed
    """
    try:
        # Ensure UUIDs are proper UUID objects (convert from string if needed)
        # Context values may be strings, so convert them to UUID objects
        client_uuid = (
            UUID(client_account_id)
            if isinstance(client_account_id, str)
            else client_account_id
        )
        engagement_uuid = (
            UUID(engagement_id) if isinstance(engagement_id, str) else engagement_id
        )
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id

        dedup_result = await dedup_service.deduplicate_application(
            db=db,
            application_name=application_name,
            client_account_id=client_uuid,
            engagement_id=engagement_uuid,
            user_id=user_uuid,
            collection_flow_id=collection_flow.id,
            additional_metadata={
                "asset_id": str(asset.id),
                "environment": getattr(asset, "environment", "unknown"),
                "source": "collection_flow_selection",
            },
        )

        # Extract deduplication fields
        canonical_app_id = getattr(
            getattr(dedup_result, "canonical_application", None), "id", None
        )
        name_variant_id = getattr(
            getattr(dedup_result, "name_variant", None), "id", None
        )
        match_method = getattr(dedup_result, "match_method", None)
        similarity = getattr(dedup_result, "similarity_score", None)

        # Create CollectionFlowApplication record
        await _create_collection_flow_application(
            db=db,
            collection_flow=collection_flow,
            asset=asset,
            application_name=application_name,
            canonical_app_id=canonical_app_id,
            name_variant_id=name_variant_id,
            match_method=match_method,
            similarity=similarity,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
        )

        # Update asset with collection reference
        asset.collection_flow_id = collection_flow.id
        asset.updated_at = datetime.now(timezone.utc)
        db.add(asset)

        # Flush to catch FK integrity issues early
        await db.flush()

        logger.info(
            f"Successfully deduplicated '{application_name}' -> "
            f"canonical app ID: {canonical_app_id} "
            f"(method: {getattr(match_method, 'value', 'unknown')}, "
            f"score: {similarity if similarity else 0.0:.3f})"
        )

        # Return deduplication result
        return {
            "asset_id": str(asset.id),
            "canonical_application_id": str(canonical_app_id),
            "application_name": application_name,
            "match_method": getattr(match_method, "value", "unknown"),
            "similarity_score": similarity if similarity else 0.0,
            "confidence_score": getattr(dedup_result, "confidence_score", 0.0),
            "is_new_canonical": getattr(dedup_result, "is_new_canonical", False),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as dedup_error:
        logger.error(
            f"Deduplication failed for '{application_name}': {str(dedup_error)}"
        )
        return None


async def _create_collection_flow_application(
    db: AsyncSession,
    collection_flow: CollectionFlow,
    asset: Asset,
    application_name: str,
    canonical_app_id: UUID | None,
    name_variant_id: UUID | None,
    match_method: Any,
    similarity: float | None,
    client_account_id: UUID,
    engagement_id: UUID,
) -> None:
    """Create CollectionFlowApplication record.

    Creates record for ALL asset types, even if deduplication fails,
    to ensure all selected assets are tracked.
    """
    if not canonical_app_id:
        logger.warning(
            f"No canonical application ID for {application_name} "
            f"(asset type: {getattr(asset, 'asset_type', 'unknown')}), "
            f"creating CollectionFlowApplication record without canonical reference"
        )

    collection_flow_app = CollectionFlowApplication(
        collection_flow_id=collection_flow.id,
        asset_id=asset.id,
        application_name=application_name,
        canonical_application_id=canonical_app_id,
        name_variant_id=name_variant_id,
        client_account_id=client_account_id,
        engagement_id=engagement_id,
        deduplication_method=getattr(match_method, "value", None),
        match_confidence=similarity,
        collection_status="selected",
        discovery_data_snapshot={
            "asset_id": str(asset.id),
            "environment": getattr(asset, "environment", "unknown"),
            "source": "collection_flow_selection",
            "selected_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    db.add(collection_flow_app)
    logger.info(f"Created CollectionFlowApplication record for {application_name}")
