"""
Enhanced collection applications API endpoints - modular implementation
"""

import logging
import uuid
from typing import Any, Dict

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.auth_utils import get_current_user
from app.core.context import get_request_context
from app.core.database import get_db
from app.models import User
from app.models.canonical_applications import (
    CanonicalApplication,
)
from app.services.application_deduplication_service import (
    ApplicationDeduplicationService,
    DeduplicationConfig,
    create_deduplication_service,
)

from .schemas import (
    BulkDeduplicationRequest,
    CanonicalApplicationRequest,
    CanonicalApplicationResponse,
)

logger = logging.getLogger(__name__)


async def process_canonical_applications(
    request_data: CanonicalApplicationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context=Depends(get_request_context),
) -> Dict[str, Any]:
    """
    Process application names through canonical deduplication system.
    """

    try:
        # Create deduplication service with request configuration
        config = DeduplicationConfig(
            fuzzy_text_threshold=request_data.similarity_threshold or 0.85,
            enable_vector_search=request_data.enable_vector_search,
            auto_merge_high_confidence=request_data.auto_merge_high_confidence,
        )
        dedup_service = ApplicationDeduplicationService(config)

        # Generate idempotency keys for each application
        idempotency_keys = {}
        for app_name in request_data.application_names:
            # Business key: normalized_name + engagement_id for idempotency
            normalized = CanonicalApplication.normalize_name(app_name)
            business_key = f"{normalized}:{context.engagement_id}"
            idempotency_key = CanonicalApplication.generate_name_hash(business_key)
            idempotency_keys[app_name] = idempotency_key

        logger.info(
            "🔄 Processing %d applications for canonical deduplication in engagement %s",
            len(request_data.application_names),
            context.engagement_id,
        )

        results = []
        processing_stats = {
            "total_processed": 0,
            "new_canonical_created": 0,
            "existing_matched": 0,
            "variants_created": 0,
            "requires_verification": 0,
        }

        # Process each application through deduplication
        for app_name in request_data.application_names:
            try:
                dedup_result = await dedup_service.deduplicate_application(
                    db=db,
                    application_name=app_name,
                    client_account_id=context.client_account_id,
                    engagement_id=context.engagement_id,
                    user_id=current_user.id,  # type: ignore[arg-type]
                )

                response = CanonicalApplicationResponse(
                    canonical_application=dedup_result.canonical_application.to_dict(),
                    name_variant=(
                        dedup_result.name_variant.to_dict()
                        if dedup_result.name_variant
                        else None
                    ),
                    is_new_canonical=dedup_result.is_new_canonical,
                    is_new_variant=dedup_result.is_new_variant,
                    match_method=dedup_result.match_method.value,
                    similarity_score=dedup_result.similarity_score,
                    confidence_score=dedup_result.confidence_score,
                    requires_verification=dedup_result.requires_verification,
                    idempotency_key=idempotency_keys[app_name],
                )

                results.append(response.dict())

                # Update processing stats
                processing_stats["total_processed"] += 1
                if dedup_result.is_new_canonical:
                    processing_stats["new_canonical_created"] += 1
                else:
                    processing_stats["existing_matched"] += 1
                if dedup_result.is_new_variant:
                    processing_stats["variants_created"] += 1
                if dedup_result.requires_verification:
                    processing_stats["requires_verification"] += 1

            except Exception as app_error:
                logger.warning(
                    "Failed to process application '%s': %s",
                    app_name,
                    str(app_error),
                )
                # CC: Rollback the database session to restore clean transaction boundary
                # This ensures that partial failures don't affect subsequent operations
                try:
                    await db.rollback()
                    logger.debug(
                        "Database session rolled back after application '%s' processing failure",
                        app_name,
                    )
                except Exception as rollback_error:
                    logger.error(
                        "Failed to rollback database session: %s",
                        str(rollback_error),
                    )
                # Continue processing other applications
                continue

        logger.info(
            "✅ Canonical application processing completed: %d processed, %d new canonical, %d matched existing, %d variants created",  # noqa: E501
            processing_stats["total_processed"],
            processing_stats["new_canonical_created"],
            processing_stats["existing_matched"],
            processing_stats["variants_created"],
        )

        return {
            "success": True,
            "message": f"Successfully processed {len(results)} applications",
            "results": results,
            "processing_stats": processing_stats,
            "idempotency_keys": idempotency_keys,
        }

    except Exception as e:
        logger.error(
            "❌ Canonical application processing failed for engagement %s: %s",
            context.engagement_id,
            str(e),
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process canonical applications: {str(e)}",
        )


async def bulk_deduplicate_applications(
    request_data: BulkDeduplicationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context=Depends(get_request_context),
) -> Dict[str, Any]:
    """
    Bulk deduplication endpoint for processing large sets of applications.
    """

    try:
        # Validate collection flow ID if provided
        collection_flow_uuid = None
        if request_data.collection_flow_id:
            try:
                collection_flow_uuid = uuid.UUID(request_data.collection_flow_id)
            except ValueError:
                raise HTTPException(
                    status_code=400, detail="Invalid collection flow ID format"
                )

        # Create optimized deduplication service for bulk operations
        dedup_service = create_deduplication_service(
            similarity_threshold=request_data.similarity_threshold,
            enable_vector_search=True,
        )

        logger.info(
            "🔄 Starting bulk deduplication for %d applications in engagement %s",
            len(request_data.applications),
            context.engagement_id,
        )

        # Process applications in bulk with optimizations
        results = await dedup_service.bulk_deduplicate_applications(
            db=db,
            applications=request_data.applications,
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id,
            user_id=current_user.id,  # type: ignore[arg-type]
            collection_flow_id=collection_flow_uuid,
            batch_size=request_data.batch_size,
        )

        # Compile processing statistics
        stats = {
            "total_requested": len(request_data.applications),
            "successfully_processed": len(results),
            "new_canonical_created": sum(1 for r in results if r.is_new_canonical),
            "existing_matched": sum(1 for r in results if not r.is_new_canonical),
            "variants_created": sum(1 for r in results if r.is_new_variant),
            "requires_verification": sum(1 for r in results if r.requires_verification),
            "match_methods": {},
        }

        # Analyze match methods distribution
        for result in results:
            method = result.match_method.value
            match_methods = stats["match_methods"]
            if isinstance(match_methods, dict):
                match_methods[method] = match_methods.get(method, 0) + 1

        # Convert results to dict format for API response
        result_dicts = []
        for result in results:
            result_dicts.append(
                {
                    "canonical_application": result.canonical_application.to_dict(),
                    "name_variant": (
                        result.name_variant.to_dict() if result.name_variant else None
                    ),
                    "is_new_canonical": result.is_new_canonical,
                    "is_new_variant": result.is_new_variant,
                    "match_method": result.match_method.value,
                    "similarity_score": result.similarity_score,
                    "confidence_score": result.confidence_score,
                    "requires_verification": result.requires_verification,
                }
            )

        logger.info(
            "✅ Bulk deduplication completed: %d/%d successful",
            stats["successfully_processed"],
            stats["total_requested"],
        )

        return {
            "success": True,
            "message": f"Bulk deduplication completed for {stats['successfully_processed']} applications",
            "results": result_dicts,
            "statistics": stats,
            "collection_flow_id": request_data.collection_flow_id,
        }

    except Exception as e:
        logger.error(
            "❌ Bulk deduplication failed for engagement %s: %s",
            context.engagement_id,
            str(e),
        )
        raise HTTPException(
            status_code=500, detail=f"Bulk deduplication failed: {str(e)}"
        )
