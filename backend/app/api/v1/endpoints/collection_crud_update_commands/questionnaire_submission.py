"""
Questionnaire Submission Operations
Handles submission of questionnaire responses.
"""

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models import User
from app.models.collection_flow import CollectionFlow, AdaptiveQuestionnaire

# Import modular helper functions
from ..collection_crud_helpers import (
    validate_asset_access,
    fetch_and_index_gaps,
    create_response_records,
    resolve_data_gaps,
    apply_asset_writeback,
    update_flow_progress,
)

from .assessment_validation import check_and_set_assessment_ready

if TYPE_CHECKING:
    from app.schemas.collection_flow import QuestionnaireSubmissionRequest

logger = logging.getLogger(__name__)


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

        # Add debug logging for tracking questionnaire processing
        logger.info(f"Processing questionnaire {questionnaire_id} for flow {flow_id}")

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

        # CRITICAL FIX: Asset selection should NOT be handled through questionnaire submission
        # Check for asset selection questionnaire attempts and redirect to proper endpoint
        if questionnaire_id == "bootstrap_asset_selection":
            logger.warning(
                f"Asset selection attempt through questionnaire submission for flow {flow_id}. "
                "Redirecting to proper endpoint."
            )

            # Return clear error message directing to proper endpoint
            raise HTTPException(
                status_code=422,  # Changed from 400 to align with frontend error handling
                detail={
                    "code": "invalid_asset_selection_endpoint",
                    "error": "Invalid endpoint for asset selection",
                    "message": (
                        "Asset selection must be done through the dedicated applications endpoint, "
                        "not through questionnaire submission."
                    ),
                    "correct_endpoint": f"/api/v1/collection/flows/{flow_id}/applications",
                    "method": "POST",
                    "expected_payload": {
                        "selected_application_ids": ["<application-id>", "..."],
                        "action": "select_applications",
                    },
                    "flow_id": flow_id,
                    "questionnaire_id": questionnaire_id,
                    "reason": "Separation of concerns - asset selection vs questionnaire responses",
                },
            )

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

        # CRITICAL FIX: Mark questionnaire as completed after successful submission
        # This prevents the same questionnaire from being returned in a loop
        questionnaire_result = await db.execute(
            select(AdaptiveQuestionnaire)
            .where(AdaptiveQuestionnaire.id == UUID(questionnaire_id))
            .where(AdaptiveQuestionnaire.collection_flow_id == flow.id)
        )
        questionnaire = questionnaire_result.scalar_one_or_none()

        if questionnaire:
            questionnaire.completion_status = "completed"
            questionnaire.completed_at = datetime.utcnow()
            questionnaire.responses_collected = form_responses
            logger.info(f"✅ Marked questionnaire {questionnaire_id} as completed")

            # Check if collection is complete and ready for assessment
            # Required attributes: business_criticality, environment
            await check_and_set_assessment_ready(
                flow, form_responses, db, context, logger
            )
        else:
            logger.warning(
                f"⚠️ Could not find questionnaire {questionnaire_id} to mark as completed"
            )

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
