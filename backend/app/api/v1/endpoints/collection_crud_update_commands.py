"""
Collection Flow Update Command Operations
Update operations for collection flows including flow updates
and questionnaire response submissions.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict

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
                CollectionFlow.id == flow_id,
                CollectionFlow.engagement_id == context.engagement_id,
            )
        )
        collection_flow = result.scalar_one_or_none()

        if not collection_flow:
            raise HTTPException(status_code=404, detail="Collection flow not found")

        # Update fields
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
                "Updated collection flow: flow_id={flow_id}",
                flow_id=flow_id,
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


async def submit_questionnaire_response(
    flow_id: str,
    questionnaire_id: str,
    response_value: str,
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
                CollectionFlow.id == flow_id,
                CollectionFlow.engagement_id == context.engagement_id,
            )
        )
        collection_flow = flow_result.scalar_one_or_none()

        if not collection_flow:
            raise HTTPException(status_code=404, detail="Collection flow not found")

        # Get questionnaire
        questionnaire_result = await db.execute(
            select(AdaptiveQuestionnaire).where(
                AdaptiveQuestionnaire.id == questionnaire_id,
                AdaptiveQuestionnaire.collection_flow_id == flow_id,
            )
        )
        questionnaire = questionnaire_result.scalar_one_or_none()

        if not questionnaire:
            raise HTTPException(status_code=404, detail="Questionnaire not found")

        # Update questionnaire with response
        questionnaire.response_value = response_value
        questionnaire.updated_at = datetime.now(timezone.utc)

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
            "response_value": response_value,
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
