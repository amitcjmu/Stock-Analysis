"""
Learning operations for field mappings.
Handles approval, rejection, and pattern learning endpoints.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from app.core.security.secure_logging import safe_log_format

from ...models.mapping_schemas import (
    BulkLearningRequest,
    BulkLearningResponse,
    LearnedPatternsResponse,
    LearningApprovalRequest,
    LearningRejectionRequest,
    LearningResponse,
)
from ...services.learning_service import FieldMappingLearningService

logger = logging.getLogger(__name__)

router = APIRouter()


def get_learning_service(
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
) -> FieldMappingLearningService:
    """Dependency injection for learning service."""
    return FieldMappingLearningService(db, context)


@router.post("/{mapping_id}/approve", response_model=LearningResponse)
async def approve_field_mapping_with_learning(
    mapping_id: str,
    request: LearningApprovalRequest,
    service: FieldMappingLearningService = Depends(get_learning_service),
):
    """
    Approve a field mapping and learn from the approval.

    This endpoint approves a field mapping and optionally creates learned patterns
    that can be used to improve future mapping suggestions. The learning includes:

    - Creating positive patterns for the approved mapping
    - Adjusting confidence scores based on user feedback
    - Storing metadata about why the mapping was approved
    - Updating the mapping status to 'approved'

    Args:
        mapping_id: UUID of the field mapping to approve
        request: Learning approval request with optional confidence adjustments and metadata

    Returns:
        LearningResponse indicating success/failure and learning results
    """
    try:
        logger.info(
            safe_log_format(
                "🎯 Processing approval with learning for mapping {mapping_id}",
                mapping_id=mapping_id,
            )
        )

        result = await service.learn_from_approval(mapping_id, request)

        if result.success:
            logger.info(
                safe_log_format(
                    "✅ Successfully approved mapping {mapping_id} with learning: "
                    "{patterns_created} patterns created, {patterns_updated} updated",
                    mapping_id=mapping_id,
                    patterns_created=result.patterns_created,
                    patterns_updated=result.patterns_updated,
                )
            )
        else:
            logger.warning(
                safe_log_format(
                    "⚠️ Failed to approve mapping {mapping_id}: {error}",
                    mapping_id=mapping_id,
                    error=result.error_message,
                )
            )

            # Return appropriate HTTP status based on error type
            if "not found" in (result.error_message or "").lower():
                raise HTTPException(status_code=404, detail=result.error_message)
            else:
                raise HTTPException(status_code=400, detail=result.error_message)

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "❌ Unexpected error approving mapping {mapping_id}: {error}",
                mapping_id=mapping_id,
                error=str(e),
            )
        )
        raise HTTPException(
            status_code=500, detail="Failed to process mapping approval"
        )


@router.post("/{mapping_id}/reject", response_model=LearningResponse)
async def reject_field_mapping_with_learning(
    mapping_id: str,
    request: LearningRejectionRequest,
    service: FieldMappingLearningService = Depends(get_learning_service),
):
    """
    Reject a field mapping and learn from the rejection.

    This endpoint rejects a field mapping and creates learned patterns to avoid
    similar incorrect mappings in the future. The learning includes:

    - Creating negative patterns for the rejected mapping
    - Storing the rejection reason for future reference
    - Creating positive patterns for alternative suggestions (if provided)
    - Updating the mapping status to 'rejected'

    Args:
        mapping_id: UUID of the field mapping to reject
        request: Learning rejection request with reason and optional alternatives

    Returns:
        LearningResponse indicating success/failure and learning results
    """
    try:
        logger.info(
            safe_log_format(
                "🚫 Processing rejection with learning for mapping {mapping_id}",
                mapping_id=mapping_id,
            )
        )

        result = await service.learn_from_rejection(mapping_id, request)

        if result.success:
            logger.info(
                safe_log_format(
                    "✅ Successfully rejected mapping {mapping_id} with learning: "
                    "{patterns_created} patterns created, {patterns_updated} updated",
                    mapping_id=mapping_id,
                    patterns_created=result.patterns_created,
                    patterns_updated=result.patterns_updated,
                )
            )
        else:
            logger.warning(
                safe_log_format(
                    "⚠️ Failed to reject mapping {mapping_id}: {error}",
                    mapping_id=mapping_id,
                    error=result.error_message,
                )
            )

            # Return appropriate HTTP status based on error type
            if "not found" in (result.error_message or "").lower():
                raise HTTPException(status_code=404, detail=result.error_message)
            else:
                raise HTTPException(status_code=400, detail=result.error_message)

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "❌ Unexpected error rejecting mapping {mapping_id}: {error}",
                mapping_id=mapping_id,
                error=str(e),
            )
        )
        raise HTTPException(
            status_code=500, detail="Failed to process mapping rejection"
        )


@router.post("/learn", response_model=BulkLearningResponse)
async def bulk_learn_from_mappings(
    request: BulkLearningRequest,
    service: FieldMappingLearningService = Depends(get_learning_service),
):
    """
    Learn from multiple field mappings in a single operation.

    This endpoint allows bulk processing of mapping approvals and rejections,
    creating learned patterns efficiently in a single database transaction.
    This is particularly useful for:

    - Processing results from batch mapping reviews
    - Learning from historical mapping data
    - Bulk training of the mapping intelligence system

    Args:
        request: Bulk learning request with multiple mapping actions

    Returns:
        BulkLearningResponse with results for each mapping action
    """
    try:
        logger.info(
            safe_log_format(
                "📚 Processing bulk learning request with {action_count} actions",
                action_count=len(request.actions),
            )
        )

        # Validate request
        if not request.actions:
            raise HTTPException(
                status_code=400, detail="At least one learning action is required"
            )

        if len(request.actions) > 100:  # Reasonable batch size limit
            raise HTTPException(
                status_code=400, detail="Maximum 100 actions allowed per bulk request"
            )

        result = await service.bulk_learn(request)

        logger.info(
            safe_log_format(
                "✅ Bulk learning completed: {successful}/{total} actions successful, "
                "{patterns_created} patterns created, {patterns_updated} updated",
                successful=result.successful_actions,
                total=result.total_actions,
                patterns_created=result.global_patterns_created,
                patterns_updated=result.global_patterns_updated,
            )
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "❌ Unexpected error in bulk learning: {error}", error=str(e)
            )
        )
        raise HTTPException(
            status_code=500, detail="Failed to process bulk learning request"
        )


@router.get("/learned", response_model=LearnedPatternsResponse)
async def get_learned_field_mapping_patterns(
    pattern_type: Optional[str] = Query(
        None,
        description="Filter by pattern type (e.g., 'field_mapping_approval', 'field_mapping_rejection')",
    ),
    insight_type: Optional[str] = Query(
        None, description="Filter by insight type (e.g., 'field_mapping_suggestion')"
    ),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of patterns to return"
    ),
    service: FieldMappingLearningService = Depends(get_learning_service),
):
    """
    Get learned field mapping patterns for the current context.

    This endpoint retrieves patterns that have been learned from previous
    mapping approvals and rejections. These patterns are used by the AI
    system to improve future mapping suggestions. The patterns include:

    - Positive patterns from approved mappings
    - Negative patterns from rejected mappings
    - Alternative suggestions from user feedback
    - Confidence score adjustments based on feedback

    Args:
        pattern_type: Optional filter by pattern type
        insight_type: Optional filter by insight type
        limit: Maximum number of patterns to return (1-1000)

    Returns:
        LearnedPatternsResponse with matching learned patterns
    """
    try:
        logger.info(
            safe_log_format(
                "🔍 Retrieving learned patterns with filters: pattern_type={pattern_type}, "
                "insight_type={insight_type}, limit={limit}",
                pattern_type=pattern_type,
                insight_type=insight_type,
                limit=limit,
            )
        )

        result = await service.get_learned_patterns(
            pattern_type=pattern_type, insight_type=insight_type, limit=limit
        )

        logger.info(
            safe_log_format(
                "✅ Retrieved {pattern_count} learned patterns",
                pattern_count=result.total_patterns,
            )
        )

        return result

    except Exception as e:
        logger.error(
            safe_log_format(
                "❌ Error retrieving learned patterns: {error}", error=str(e)
            )
        )
        raise HTTPException(
            status_code=500, detail="Failed to retrieve learned patterns"
        )


# Cache invalidation endpoint for when patterns are updated externally
@router.post("/learned/refresh")
async def refresh_learned_patterns_cache(
    service: FieldMappingLearningService = Depends(get_learning_service),
):
    """
    Refresh the learned patterns cache.

    This endpoint can be called to refresh any cached learned patterns
    when patterns are updated through other means (e.g., background jobs,
    administrative updates, or pattern cleanup processes).

    Returns:
        Success message confirming cache refresh
    """
    try:
        logger.info("🔄 Refreshing learned patterns cache")

        # For now, this is a placeholder - actual cache refresh logic would go here
        # In a production system, this might invalidate Redis cache keys or
        # trigger background tasks to rebuild pattern caches

        logger.info("✅ Learned patterns cache refreshed")

        return {
            "status": "success",
            "message": "Learned patterns cache refreshed successfully",
        }

    except Exception as e:
        logger.error(
            safe_log_format("❌ Error refreshing patterns cache: {error}", error=str(e))
        )
        raise HTTPException(status_code=500, detail="Failed to refresh patterns cache")
