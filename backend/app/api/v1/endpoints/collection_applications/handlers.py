"""Main handler for collection application selection."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.auth_utils import get_current_user
from app.core.context import get_request_context
from app.core.database import get_db
from app.models import User
from app.schemas.collection_flow import CollectionApplicationSelectionRequest

from .deduplication import process_applications_with_deduplication
from .phase_transition import transition_to_gap_analysis
from .validation import (
    load_collection_flow,
    validate_and_normalize_application_ids,
    validate_applications_ownership,
)

logger = logging.getLogger(__name__)


async def update_flow_applications(
    flow_id: str,
    request_data: CollectionApplicationSelectionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context=Depends(get_request_context),
) -> Dict[str, Any]:
    """Update collection flow with selected applications for questionnaire generation.

    This endpoint allows users to specify which applications should be included
    in a collection flow, enabling targeted questionnaire generation and gap analysis.

    SECURITY: Validates that all selected applications belong to the current user's engagement.

    FIXED (v3 Diagnostic Report - Correction 1):
    - Loads Asset/Application objects to get names (not pass IDs directly)
    - Uses the deduplication service with application names
    - Creates CollectionFlowApplication records in normalized tables
    - Maintains both JSON config AND normalized table consistency
    - Triggers MFO execution if master_flow_id exists
    - Uses proper tenant scoping and atomic transactions

    Args:
        flow_id: The collection flow ID to update
        request_data: Validated request containing selected_application_ids and optional action

    Returns:
        Dict indicating success/failure and updated flow status

    Raises:
        HTTPException: If applications don't belong to the engagement or validation fails
    """
    try:
        logger.debug(
            f"update_flow_applications called - Flow ID: {flow_id}, "
            f"User ID: {current_user.id}, Engagement ID: {context.engagement_id}, "
            f"Raw request data: {request_data.dict()}"
        )

        # Extract validated data from Pydantic model
        selected_application_ids = request_data.selected_application_ids
        action = request_data.action

        logger.debug(
            f"Parsed application IDs - Count: {len(selected_application_ids)}, "
            f"IDs: {selected_application_ids}, Action: {action}"
        )

        # Normalize and deduplicate application IDs
        normalized_ids = await validate_and_normalize_application_ids(
            selected_application_ids, flow_id
        )

        logger.debug(
            f"Normalized IDs - Original: {len(selected_application_ids)}, "
            f"After dedup: {len(normalized_ids)}"
        )

        # Validate application ownership
        await validate_applications_ownership(db, normalized_ids, context.engagement_id)

        # Load collection flow with tenant scoping
        collection_flow = await load_collection_flow(
            db, flow_id, context.engagement_id, context.client_account_id
        )

        logger.info(
            f"Updating collection flow {flow_id} with {len(normalized_ids)} applications"
        )

        # Update JSON config
        await _update_collection_config(collection_flow, normalized_ids, action)

        # Flush to persist flow updates
        await db.flush()

        # CC FIX: Eagerly load collection_config before deduplication to prevent lazy-load errors
        # Without this, accessing collection_flow.collection_config after commit triggers
        # MissingGreenlet error because session is expired
        _ = collection_flow.collection_config

        # Process applications with deduplication service
        (
            processed_count,
            application_details,
            deduplication_results,
        ) = await process_applications_with_deduplication(
            db=db,
            normalized_ids=normalized_ids,
            collection_flow=collection_flow,
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id,
            user_id=current_user.id,
        )

        # Update config with processing results
        await _update_config_with_results(
            collection_flow,
            application_details,
            deduplication_results,
            processed_count,
        )

        logger.info(
            f"Processed {processed_count}/{len(normalized_ids)} applications, "
            f"created {len(deduplication_results)} normalized records"
        )

        # Commit application processing
        await db.commit()

        logger.debug(
            f"Database update successful - {processed_count} applications processed"
        )

        # Transition to gap analysis phase
        return await transition_to_gap_analysis(
            db=db,
            collection_flow=collection_flow,
            normalized_ids=normalized_ids,
            flow_id=flow_id,
            context=context,
            processed_count=processed_count,
            normalized_records_count=len(deduplication_results),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.debug(
            f"Database update failed for flow {flow_id} - "
            f"User: {current_user.id}, Engagement: {context.engagement_id}, "
            f"Exception: {type(e).__name__}: {str(e)}"
        )
        logger.error(f"Error updating collection flow {flow_id} applications: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to update collection flow applications. "
                "Please try again or contact support if the issue persists."
            ),
        )


async def _update_collection_config(
    collection_flow,
    normalized_ids: list[str],
    action: str,
) -> None:
    """Update collection flow JSON config with selected applications."""
    # Update collection_config
    existing_config = collection_flow.collection_config or {}
    merged_config = existing_config.copy()
    merged_config.update(
        {
            "selected_application_ids": normalized_ids,
            "has_applications": True,
            "application_count": len(normalized_ids),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "action": action,
        }
    )
    collection_flow.collection_config = merged_config

    # CRITICAL FIX (Bug #2): Also update flow_metadata for gap scanner
    # The ProgrammaticGapScanner reads from flow_metadata.selected_asset_ids
    existing_metadata = collection_flow.flow_metadata or {}
    merged_metadata = existing_metadata.copy()
    merged_metadata.update(
        {
            "selected_asset_ids": normalized_ids,  # Gap scanner expects this field
            # Bug #997 Fix: Preserve asset selection action and timestamp for tracking
            "asset_selection_action": action,
            "asset_selection_count": len(normalized_ids),
            "asset_selection_timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )
    collection_flow.flow_metadata = merged_metadata


async def _update_config_with_results(
    collection_flow,
    application_details: list,
    deduplication_results: list,
    processed_count: int,
) -> None:
    """Update config with application processing results."""
    merged_config = collection_flow.collection_config.copy()
    merged_config.update(
        {
            "application_details": application_details,
            "deduplication_results": deduplication_results,
            "processed_application_count": processed_count,
            "normalized_records_created": len(deduplication_results),
        }
    )
    collection_flow.collection_config = merged_config
