"""
Collection Flow Update Command Operations
Handles update operations for collection flows including questionnaire response submission.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.context import RequestContext
from fastapi import HTTPException
from app.models import User
from app.models.collection_flow import CollectionFlow
from app.models.collection_questionnaire_response import CollectionQuestionnaireResponse
from app.schemas.collection_flow import CollectionFlowUpdate

# Import helper functions from separate module to keep file under 400 lines
from .collection_crud_helpers import (
    validate_asset_access,
    fetch_and_index_gaps,
    create_response_records,
    resolve_data_gaps,
    apply_asset_writeback,
    update_flow_progress,
)

if TYPE_CHECKING:
    from app.schemas.collection_flow import QuestionnaireSubmissionRequest

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
        # Fetch the flow by flow_id (not id) with proper multi-tenant validation
        result = await db.execute(
            select(CollectionFlow)
            .where(CollectionFlow.flow_id == flow_id)
            .where(CollectionFlow.engagement_id == context.engagement_id)
            .where(CollectionFlow.client_account_id == context.client_account_id)
            .options(selectinload(CollectionFlow.questionnaire_responses))
        )
        flow = result.scalar_one_or_none()

        if not flow:
            raise HTTPException(
                status_code=404, detail=f"Collection flow {flow_id} not found"
            )

        # Update fields if provided
        # Note: CollectionFlowUpdate doesn't have a status field
        # Status updates should be handled through action field or separate endpoints

        if flow_update.collection_config is not None:
            flow.collection_config = {
                **flow.collection_config,
                **flow_update.collection_config,
            }

        if flow_update.automation_tier is not None:
            flow.automation_tier = flow_update.automation_tier

        # Update metadata
        flow.updated_at = datetime.utcnow()
        # Note: collection_flows table doesn't have updated_by column

        await db.commit()
        await db.refresh(flow)

        return {
            "id": str(flow.id),
            "status": flow.status,
            "collection_config": flow.collection_config,
            "automation_tier": flow.automation_tier,
            "updated_at": flow.updated_at.isoformat(),
            "message": "Collection flow updated successfully",
        }

    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to update collection flow {flow_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update collection flow: {e}"
        )


async def get_questionnaire_responses(
    flow_id: str,
    questionnaire_id: Optional[str],
    db: AsyncSession,
    current_user: User,
    context: RequestContext,
) -> Dict[str, Any]:
    """Retrieve saved questionnaire responses for a flow."""
    try:
        # First get the collection flow to get the internal ID with proper multi-tenant validation
        flow_result = await db.execute(
            select(CollectionFlow)
            .where(CollectionFlow.flow_id == flow_id)
            .where(CollectionFlow.engagement_id == context.engagement_id)
            .where(CollectionFlow.client_account_id == context.client_account_id)
        )
        flow = flow_result.scalar_one_or_none()

        if not flow:
            logger.warning(f"Collection flow {flow_id} not found")
            return {
                "flow_id": str(flow_id),
                "questionnaire_id": questionnaire_id,
                "responses": {},
                "response_count": 0,
                "last_updated": None,
            }

        # Build query using the internal collection flow ID
        query = select(CollectionQuestionnaireResponse).where(
            CollectionQuestionnaireResponse.collection_flow_id == flow.id
        )

        # Filter by questionnaire_id if provided (database-agnostic JSON filtering)
        if questionnaire_id:
            # Use SQLAlchemy's JSON operators which are database-agnostic
            from sqlalchemy import cast, String

            # Database-agnostic JSON filtering approach
            # This works across PostgreSQL (with JSONB/JSON), MySQL (JSON), and SQLite (JSON1 extension)
            try:
                # For PostgreSQL, use the -> operator for JSON/JSONB
                query = query.where(
                    CollectionQuestionnaireResponse.response_metadata[
                        "questionnaire_id"
                    ].astext
                    == questionnaire_id
                )
            except Exception:
                # Fallback to cast as String and use LIKE for broader compatibility
                query = query.where(
                    cast(
                        CollectionQuestionnaireResponse.response_metadata, String
                    ).like(f'%"questionnaire_id": "{questionnaire_id}"%')
                )

        # Execute query
        result = await db.execute(query)
        responses = result.scalars().all()

        # Format responses
        formatted_responses = {}
        for response in responses:
            # Extract the actual value from response_value
            value = (
                response.response_value.get("value")
                if response.response_value
                else None
            )
            formatted_responses[response.question_id] = value

        return {
            "flow_id": str(flow_id),
            "questionnaire_id": questionnaire_id,
            "responses": formatted_responses,
            "response_count": len(responses),
            "last_updated": (
                max([r.responded_at for r in responses]).isoformat()
                if responses
                else None
            ),
        }

    except Exception as e:
        logger.error(
            f"Failed to retrieve questionnaire responses for flow {flow_id}: {e}"
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve questionnaire responses: {e}"
        )


async def submit_questionnaire_response(
    flow_id: str,
    questionnaire_id: str,
    request_data: "QuestionnaireSubmissionRequest",
    db: AsyncSession,
    current_user: User,
    context: RequestContext,
) -> Dict[str, Any]:
    """Submit responses to an adaptive questionnaire and save them to the database."""
    try:
        logger.info(
            f"Processing questionnaire submission - Flow ID: {flow_id}, "
            f"Questionnaire ID: {questionnaire_id}, User ID: {current_user.id}, "
            f"Engagement ID: {context.engagement_id}"
        )

        # Verify flow exists and belongs to engagement with proper multi-tenant validation
        flow_result = await db.execute(
            select(CollectionFlow)
            .where(CollectionFlow.flow_id == flow_id)  # Fixed: Use flow_id not id
            .where(CollectionFlow.engagement_id == context.engagement_id)
            .where(CollectionFlow.client_account_id == context.client_account_id)
        )
        flow = flow_result.scalar_one_or_none()

        if not flow:
            logger.error(
                f"Collection flow {flow_id} not found for engagement {context.engagement_id}"
            )
            raise HTTPException(
                status_code=404, detail=f"Collection flow {flow_id} not found"
            )

        logger.info(f"Found collection flow: {flow.id} (flow_id: {flow.flow_id})")

        # Extract responses and metadata from request data
        form_responses = request_data.responses
        form_metadata = request_data.form_metadata or {}
        validation_results = request_data.validation_results or {}

        # Extract and validate asset_id for optional linking to asset inventory
        asset_id = form_metadata.get("application_id") or form_metadata.get("asset_id")
        validated_asset = await validate_asset_access(asset_id, context, db)

        if asset_id and not validated_asset:
            asset_id = None  # Clear invalid asset_id
        elif not asset_id:
            logger.info(
                "No asset_id provided - questionnaire responses will be flow-level only (new/manual application entry)"
            )

        # CRITICAL: Fetch and index gaps first to enable proper gap_id linkage
        gap_index = await fetch_and_index_gaps(flow, db)

        # Create response records with proper gap_id linkage
        response_records = await create_response_records(
            form_responses,
            form_metadata,
            validation_results,
            questionnaire_id,
            flow,
            asset_id,
            current_user,
            gap_index,
            db,
        )

        # Update flow status based on completion
        update_flow_progress(flow, form_metadata, flow_id)

        # Update flow metadata
        flow.updated_at = datetime.utcnow()

        # Mark gaps as resolved for fields that received responses
        gaps_resolved = 0
        if response_records:
            gaps_resolved = await resolve_data_gaps(gap_index, form_responses, db)

        # Commit all changes
        logger.info(f"Committing {len(response_records)} response records to database")
        await db.commit()

        # Apply resolved gaps to assets via write-back service
        await apply_asset_writeback(gaps_resolved, flow, context, current_user, db)

        logger.info(
            f"Successfully saved {len(response_records)} questionnaire responses for flow {flow_id} "
            f"by user {current_user.id}. Flow progress: {flow.progress_percentage}%, Status: {flow.status}"
        )

        return {
            "status": "success",
            "message": f"Successfully saved {len(response_records)} responses",
            "questionnaire_id": questionnaire_id,
            "flow_id": str(flow.flow_id),  # Fixed: Return flow_id UUID, not database ID
            "progress": flow.progress_percentage,
            "responses_saved": len(response_records),
        }

    except HTTPException as he:
        logger.warning(
            f"HTTP error in questionnaire submission for flow {flow_id}: {he.detail}"
        )
        raise
    except Exception as e:
        await db.rollback()
        logger.error(
            f"Failed to submit questionnaire response for flow {flow_id}, questionnaire {questionnaire_id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to submit questionnaire response: {e}"
        )


async def batch_update_questionnaire_responses(
    flow_id: str,
    responses: List[Dict[str, Any]],
    db: AsyncSession,
    current_user: User,
    context: RequestContext,
) -> Dict[str, Any]:
    """Submit multiple questionnaire responses in batch."""
    try:
        # Verify flow exists and belongs to engagement
        flow_result = await db.execute(
            select(CollectionFlow)
            .where(CollectionFlow.flow_id == flow_id)  # Fixed: Use flow_id not id
            .where(CollectionFlow.engagement_id == context.engagement_id)
            .where(CollectionFlow.client_account_id == context.client_account_id)
        )
        flow = flow_result.scalar_one_or_none()

        if not flow:
            raise HTTPException(
                status_code=404,
                detail=f"Collection flow {flow_id} not found or access denied",
            )

        response_records = []

        for response_data in responses:
            # Validate asset ownership if asset_id is provided
            asset_id = response_data.get("asset_id")
            validated_asset = None

            if asset_id:
                from app.models.asset import Asset

                try:
                    asset_result = await db.execute(
                        select(Asset)
                        .where(Asset.id == asset_id)
                        .where(Asset.engagement_id == context.engagement_id)
                        .where(Asset.client_account_id == context.client_account_id)
                    )
                    validated_asset = asset_result.scalar_one_or_none()

                    if not validated_asset:
                        logger.warning(
                            f"Asset {asset_id} not found or not accessible for user {current_user.id} "
                            f"in engagement {context.engagement_id} - skipping response"
                        )
                        continue  # Skip this response if asset doesn't belong to user's context

                except Exception as e:
                    logger.warning(
                        f"Failed to validate asset {asset_id}: {e} - skipping response"
                    )
                    continue  # Skip this response on validation error

            response = CollectionQuestionnaireResponse(
                collection_flow_id=flow.id,
                asset_id=asset_id if validated_asset else None,
                questionnaire_type=response_data.get(
                    "questionnaire_type", "adaptive_form"
                ),
                question_category=response_data.get("question_category", "general"),
                question_id=response_data["question_id"],
                question_text=response_data.get(
                    "question_text", response_data["question_id"]
                ),
                response_type=response_data.get("response_type", "text"),
                response_value=response_data.get("response_value"),
                confidence_score=response_data.get("confidence_score"),
                validation_status=response_data.get("validation_status", "pending"),
                responded_by=current_user.id,
                responded_at=datetime.utcnow(),
                response_metadata=response_data.get("metadata", {}),
            )

            db.add(response)
            response_records.append(response)

        await db.commit()

        return {
            "status": "success",
            "message": f"Successfully saved {len(response_records)} responses",
            "flow_id": str(flow.flow_id),  # Fixed: Return flow_id UUID, not database ID
            "responses_saved": len(response_records),
        }

    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to batch update questionnaire responses: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to batch update responses: {e}"
        )
