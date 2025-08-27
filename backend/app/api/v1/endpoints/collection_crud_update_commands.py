"""
Collection Flow Update Command Operations
Handles update operations for collection flows including questionnaire response submission.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.context import RequestContext
from app.core.exceptions import ApplicationError, ConflictError, NotFoundError
from app.models import User
from app.models.collection_flow import CollectionFlow
from app.models.collection_questionnaire_response import CollectionQuestionnaireResponse
from app.schemas.collection_flow import CollectionFlowUpdate

logger = logging.getLogger(__name__)


async def update_collection_flow(
    flow_id: str,
    flow_update: CollectionFlowUpdate,
    db: AsyncSession,
    current_user: User,
    context: RequestContext,
) -> Dict[str, Any]:
    """Update an existing collection flow."""
    try:
        # Fetch the flow
        result = await db.execute(
            select(CollectionFlow)
            .where(CollectionFlow.id == flow_id)
            .where(CollectionFlow.engagement_id == context.engagement_id)
            .options(selectinload(CollectionFlow.questionnaire_responses))
        )
        flow = result.scalar_one_or_none()
        
        if not flow:
            raise NotFoundError(f"Collection flow {flow_id} not found")
        
        # Update fields if provided
        if flow_update.status is not None:
            flow.status = flow_update.status
        
        if flow_update.collection_config is not None:
            flow.collection_config = {
                **flow.collection_config,
                **flow_update.collection_config
            }
        
        if flow_update.automation_tier is not None:
            flow.automation_tier = flow_update.automation_tier
        
        # Update metadata
        flow.updated_at = datetime.utcnow()
        flow.updated_by = current_user.id
        
        await db.commit()
        await db.refresh(flow)
        
        return {
            "id": str(flow.id),
            "status": flow.status,
            "collection_config": flow.collection_config,
            "automation_tier": flow.automation_tier,
            "updated_at": flow.updated_at.isoformat(),
            "message": "Collection flow updated successfully"
        }
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to update collection flow {flow_id}: {e}")
        raise ApplicationError(f"Failed to update collection flow: {e}")


async def submit_questionnaire_response(
    flow_id: str,
    questionnaire_id: str,
    responses: Dict[str, Any],
    db: AsyncSession,
    current_user: User,
    context: RequestContext,
) -> Dict[str, Any]:
    """Submit responses to an adaptive questionnaire and save them to the database."""
    try:
        # Verify flow exists and belongs to engagement
        flow_result = await db.execute(
            select(CollectionFlow)
            .where(CollectionFlow.id == flow_id)
            .where(CollectionFlow.engagement_id == context.engagement_id)
        )
        flow = flow_result.scalar_one_or_none()
        
        if not flow:
            raise NotFoundError(f"Collection flow {flow_id} not found")
        
        # Extract responses and metadata
        form_responses = responses.get("responses", {})
        form_metadata = responses.get("form_metadata", {})
        validation_results = responses.get("validation_results", {})
        
        # Create response records for each submitted field
        response_records = []
        
        for field_id, value in form_responses.items():
            # Skip empty responses
            if value is None or value == "":
                continue
                
            # Create response record
            response = CollectionQuestionnaireResponse(
                collection_flow_id=flow.id,
                questionnaire_type="adaptive_form",
                question_category=form_metadata.get("form_id", "general"),
                question_id=field_id,
                question_text=field_id,  # This should ideally come from the questionnaire definition
                response_type="text",  # This should be determined from field type
                response_value={"value": value} if not isinstance(value, dict) else value,
                confidence_score=form_metadata.get("confidence_score"),
                validation_status="validated" if validation_results.get("isValid") else "pending",
                responded_by=current_user.id,
                responded_at=datetime.utcnow(),
                response_metadata={
                    "questionnaire_id": questionnaire_id,
                    "application_id": form_metadata.get("application_id"),
                    "completion_percentage": form_metadata.get("completion_percentage"),
                    "submitted_at": form_metadata.get("submitted_at"),
                }
            )
            
            db.add(response)
            response_records.append(response)
        
        # Update flow status if needed
        if form_metadata.get("completion_percentage", 0) >= 100:
            flow.status = "completed"
            flow.progress = 100
        else:
            flow.progress = form_metadata.get("completion_percentage", flow.progress)
        
        # Update flow metadata
        flow.updated_at = datetime.utcnow()
        flow.updated_by = current_user.id
        
        # Commit all changes
        await db.commit()
        
        logger.info(
            f"Saved {len(response_records)} questionnaire responses for flow {flow_id} "
            f"by user {current_user.id}"
        )
        
        return {
            "status": "success",
            "message": f"Successfully saved {len(response_records)} responses",
            "questionnaire_id": questionnaire_id,
            "flow_id": str(flow.id),
            "progress": flow.progress,
            "responses_saved": len(response_records)
        }
        
    except NotFoundError:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(
            f"Failed to submit questionnaire response for flow {flow_id}: {e}",
            exc_info=True
        )
        raise ApplicationError(f"Failed to submit questionnaire response: {e}")


async def batch_update_questionnaire_responses(
    flow_id: str,
    responses: List[Dict[str, Any]],
    db: AsyncSession,
    current_user: User,
    context: RequestContext,
) -> Dict[str, Any]:
    """Submit multiple questionnaire responses in batch."""
    try:
        # Verify flow exists
        flow_result = await db.execute(
            select(CollectionFlow)
            .where(CollectionFlow.id == flow_id)
            .where(CollectionFlow.engagement_id == context.engagement_id)
        )
        flow = flow_result.scalar_one_or_none()
        
        if not flow:
            raise NotFoundError(f"Collection flow {flow_id} not found")
        
        response_records = []
        
        for response_data in responses:
            response = CollectionQuestionnaireResponse(
                collection_flow_id=flow.id,
                questionnaire_type=response_data.get("questionnaire_type", "adaptive_form"),
                question_category=response_data.get("question_category", "general"),
                question_id=response_data["question_id"],
                question_text=response_data.get("question_text", response_data["question_id"]),
                response_type=response_data.get("response_type", "text"),
                response_value=response_data.get("response_value"),
                confidence_score=response_data.get("confidence_score"),
                validation_status=response_data.get("validation_status", "pending"),
                responded_by=current_user.id,
                responded_at=datetime.utcnow(),
                response_metadata=response_data.get("metadata", {})
            )
            
            db.add(response)
            response_records.append(response)
        
        await db.commit()
        
        return {
            "status": "success",
            "message": f"Successfully saved {len(response_records)} responses",
            "flow_id": str(flow.id),
            "responses_saved": len(response_records)
        }
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to batch update questionnaire responses: {e}")
        raise ApplicationError(f"Failed to batch update responses: {e}")