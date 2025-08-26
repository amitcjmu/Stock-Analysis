"""Collection Application Selection endpoints.

This module handles application selection for collection flows,
enabling targeted questionnaire generation based on selected applications.
"""

import logging
from typing import Dict, Any
from datetime import datetime, timezone

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.auth_utils import get_current_user
from app.core.context import get_request_context
from app.core.database import get_db
from app.models import User
from app.schemas.collection_flow import (
    CollectionFlowUpdate,
    CollectionApplicationSelectionRequest,
)
from app.api.v1.endpoints import collection_crud
from app.api.v1.endpoints import collection_validators

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

    Args:
        flow_id: The collection flow ID to update
        request_data: Validated request containing selected_application_ids and optional action

    Returns:
        Dict indicating success/failure and updated flow status

    Raises:
        HTTPException: If applications don't belong to the engagement or validation fails
    """
    try:
        # Extract validated data from Pydantic model
        selected_application_ids = request_data.selected_application_ids
        action = request_data.action

        # CC: Normalize and deduplicate application IDs while preserving order
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

        if not normalized_ids:
            logger.warning(f"No valid application IDs provided for flow {flow_id}")
            raise HTTPException(
                status_code=400,
                detail="No valid application IDs provided. Please select at least one valid application.",
            )

        # SECURITY VALIDATION: Validate that all applications belong to this engagement
        # This prevents authorization bypass where users could specify arbitrary application IDs
        logger.info(
            f"Validating {len(normalized_ids)} applications for engagement {context.engagement_id}"
        )

        try:
            validated_applications = (
                await collection_validators.validate_applications_exist(
                    db, normalized_ids, context.engagement_id
                )
            )
            logger.info(
                f"Successfully validated {len(validated_applications)} applications for collection flow {flow_id}"
            )
        except Exception as validation_error:
            logger.warning(
                f"Application validation failed for flow {flow_id}: validation error occurred"
            )
            # CC: Check if it's a validation failure vs permission issue
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

        logger.info(
            f"Updating collection flow {flow_id} with {len(normalized_ids)} applications"
        )

        # CC: Fetch current flow's collection_config to preserve existing settings
        current_flow_result = await collection_crud.get_collection_flow(
            flow_id=flow_id, db=db, current_user=current_user, context=context
        )

        # Preserve existing config and merge with new application selections
        existing_config = (
            current_flow_result.collection_config
            if hasattr(current_flow_result, "collection_config")
            and current_flow_result.collection_config
            else {}
        )

        # Create update data for the collection flow with timezone-aware timestamp
        merged_config = existing_config.copy()  # Preserve existing settings
        merged_config.update(
            {
                "selected_application_ids": normalized_ids,
                "has_applications": True,
                "application_count": len(normalized_ids),
                "updated_at": datetime.now(
                    timezone.utc
                ).isoformat(),  # Fix: Use timezone-aware UTC timestamp
                "action": action,
            }
        )

        update_data = CollectionFlowUpdate(
            collection_config=merged_config,
            trigger_questionnaire_generation=True,  # Trigger questionnaire generation after application selection
        )

        # Update the collection flow
        result = await collection_crud.update_collection_flow(
            flow_id=flow_id,
            flow_data=update_data,
            db=db,
            current_user=current_user,
            context=context,
        )

        return {
            "success": True,
            "message": f"Successfully updated collection flow with {len(normalized_ids)} applications",
            "flow_id": flow_id,
            "selected_application_count": len(normalized_ids),
            "flow": result.model_dump() if hasattr(result, "model_dump") else result,
        }

    except HTTPException:
        raise
    except Exception:
        logger.error(
            f"Error updating collection flow {flow_id} applications: internal error occurred"
        )
        # CC: Don't echo exception text in responses (security concern)
        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to update collection flow applications. "
                "Please try again or contact support if the issue persists."
            ),
        )
