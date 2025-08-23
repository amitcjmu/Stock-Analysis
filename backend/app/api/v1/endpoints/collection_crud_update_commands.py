"""
Collection Flow Update Command Operations
Update operations for collection flows including flow updates
and questionnaire response submissions.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.security.secure_logging import safe_log_format
from app.models import User
from app.models.collection_flow import (
    AdaptiveQuestionnaire,
    CollectionFlow,
)
from app.schemas.collection_flow import (
    CollectionFlowResponse,
    CollectionFlowUpdate,
)

# Import modular functions
from app.api.v1.endpoints import collection_serializers

logger = logging.getLogger(__name__)


async def update_collection_flow(
    flow_id: str,
    flow_data: CollectionFlowUpdate,
    db: AsyncSession,
    current_user: User,
    context: RequestContext,
) -> CollectionFlowResponse:
    """Update collection flow details.

    Args:
        flow_id: Collection flow ID
        flow_data: Update data
        db: Database session
        current_user: Current authenticated user
        context: Request context

    Returns:
        Updated collection flow details

    Raises:
        HTTPException: If flow not found or update fails
    """
    try:
        result = await db.execute(
            select(CollectionFlow).where(
                CollectionFlow.flow_id == UUID(flow_id),
                CollectionFlow.engagement_id == context.engagement_id,
            )
        )
        collection_flow = result.scalar_one_or_none()

        if not collection_flow:
            raise HTTPException(status_code=404, detail="Collection flow not found")

        # Handle specific actions
        if flow_data.action == "update_applications":
            await _handle_update_applications_action(
                collection_flow, flow_data, db, context
            )
        else:
            # Handle standard updates
            if flow_data.flow_name is not None:
                collection_flow.flow_name = flow_data.flow_name
            if flow_data.automation_tier is not None:
                collection_flow.automation_tier = flow_data.automation_tier
            if flow_data.collection_config is not None:
                collection_flow.collection_config = flow_data.collection_config

        collection_flow.updated_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(collection_flow)

        logger.info(
            safe_log_format(
                "Updated collection flow: flow_id={flow_id}, action={action}",
                flow_id=flow_id,
                action=flow_data.action or "standard_update",
            )
        )

        return collection_serializers.serialize_collection_flow(collection_flow)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "Error updating collection flow: flow_id={flow_id}, error={e}",
                flow_id=flow_id,
                e=e,
            )
        )
        raise HTTPException(status_code=500, detail=str(e))


async def _handle_update_applications_action(
    collection_flow: CollectionFlow,
    flow_data: CollectionFlowUpdate,
    db: AsyncSession,
    context: RequestContext,
) -> None:
    """Handle the update_applications action specifically.

    Args:
        collection_flow: The collection flow to update
        flow_data: The update data containing application selections
        db: Database session
        context: Request context

    Raises:
        HTTPException: If validation fails or applications don't exist
    """
    from app.api.v1.endpoints import collection_validators

    if not flow_data.collection_config:
        raise HTTPException(
            status_code=400,
            detail="collection_config is required for update_applications action",
        )

    selected_application_ids = flow_data.collection_config.get(
        "selected_application_ids", []
    )

    if not selected_application_ids:
        raise HTTPException(
            status_code=400,
            detail="selected_application_ids is required for update_applications action",
        )

    # Validate that all selected applications exist and belong to this engagement
    try:
        applications = await collection_validators.validate_applications_exist(
            db, selected_application_ids, context.engagement_id
        )
        logger.info(
            safe_log_format(
                "Validated {count} applications for collection flow {flow_id}",
                count=len(applications),
                flow_id=str(collection_flow.flow_id),
            )
        )
    except Exception as e:
        logger.error(
            safe_log_format(
                "Failed to validate applications: {error}",
                error=str(e),
            )
        )
        raise HTTPException(
            status_code=400, detail=f"Application validation failed: {str(e)}"
        )

    # Update collection config with validated applications
    updated_config = (
        collection_flow.collection_config.copy()
        if collection_flow.collection_config
        else {}
    )
    updated_config.update(
        {
            "selected_application_ids": selected_application_ids,
            "discovery_flow_id": flow_data.collection_config.get("discovery_flow_id"),
            "application_count": len(selected_application_ids),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "has_applications": True,  # Mark that applications are now selected
        }
    )

    collection_flow.collection_config = updated_config

    logger.info(
        safe_log_format(
            "Updated collection flow {flow_id} with {count} selected applications",
            flow_id=str(collection_flow.flow_id),
            count=len(selected_application_ids),
        )
    )


async def submit_questionnaire_response(
    flow_id: str,
    questionnaire_id: str,
    responses: Dict[str, Any],
    db: AsyncSession,
    current_user: User,
    context: RequestContext,
) -> Dict[str, Any]:
    """Submit response to adaptive questionnaire.

    Args:
        flow_id: Collection flow ID
        questionnaire_id: Questionnaire ID
        response_value: User's response
        db: Database session
        current_user: Current authenticated user
        context: Request context

    Returns:
        Dictionary with submission status

    Raises:
        HTTPException: If flow or questionnaire not found
    """
    try:
        # Verify flow ownership
        flow_result = await db.execute(
            select(CollectionFlow).where(
                CollectionFlow.flow_id == UUID(flow_id),
                CollectionFlow.engagement_id == context.engagement_id,
            )
        )
        collection_flow = flow_result.scalar_one_or_none()

        if not collection_flow:
            raise HTTPException(status_code=404, detail="Collection flow not found")

        questionnaire: AdaptiveQuestionnaire | None = None

        # Attempt to treat questionnaire_id as UUID; if invalid, fall back to ephemeral storage
        questionnaire_uuid: UUID | None = None
        try:
            questionnaire_uuid = UUID(questionnaire_id)
        except (ValueError, TypeError):
            questionnaire_uuid = None

        if questionnaire_uuid is not None:
            questionnaire_result = await db.execute(
                select(AdaptiveQuestionnaire).where(
                    AdaptiveQuestionnaire.id == questionnaire_uuid,
                    AdaptiveQuestionnaire.collection_flow_id == collection_flow.id,
                )
            )
            questionnaire = questionnaire_result.scalar_one_or_none()

        if questionnaire is not None:
            # Merge responses into questionnaire.responses_collected JSONB
            existing = questionnaire.responses_collected or {}
            submission_record = {
                "submitted_at": datetime.now(timezone.utc).isoformat(),
                "submitted_by": str(current_user.id),
                "payload": responses,
            }
            if isinstance(existing, list):
                existing.append(submission_record)
                questionnaire.responses_collected = existing
            elif isinstance(existing, dict):
                # Keep both a history list and latest pointer
                history = existing.get("history", [])
                if not isinstance(history, list):
                    history = []
                history.append(submission_record)
                existing["history"] = history
                existing["latest_submission"] = submission_record
                questionnaire.responses_collected = existing
            else:
                questionnaire.responses_collected = [submission_record]

            questionnaire.updated_at = datetime.now(timezone.utc)
            await db.commit()
        else:
            # Ephemeral questionnaire (e.g., bootstrap_...): persist into flow phase_state
            phase_state = collection_flow.phase_state or {}
            submissions = phase_state.get("questionnaire_submissions", {})
            submissions[questionnaire_id] = {
                "submitted_at": datetime.now(timezone.utc).isoformat(),
                "submitted_by": str(current_user.id),
                "payload": responses,
            }
            phase_state["questionnaire_submissions"] = submissions
            collection_flow.phase_state = phase_state
            collection_flow.updated_at = datetime.now(timezone.utc)
            await db.commit()

        logger.info(
            safe_log_format(
                "Submitted questionnaire response: flow_id={flow_id}, "
                "questionnaire_id={questionnaire_id}",
                flow_id=flow_id,
                questionnaire_id=questionnaire_id,
            )
        )

        return {
            "status": "success",
            "message": "Response submitted successfully",
            "questionnaire_id": questionnaire_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "Error submitting questionnaire response: "
                "flow_id={flow_id}, questionnaire_id={questionnaire_id}, error={e}",
                flow_id=flow_id,
                questionnaire_id=questionnaire_id,
                e=e,
            )
        )
        raise HTTPException(status_code=500, detail=str(e))
