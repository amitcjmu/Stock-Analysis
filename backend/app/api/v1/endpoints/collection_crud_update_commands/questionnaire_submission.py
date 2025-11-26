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
from app.models.collection_flow import CollectionFlow

# Import modular helper functions
from ..collection_crud_helpers import (
    validate_asset_access,
    fetch_and_index_gaps,
    create_response_records,
    update_flow_progress,
)

# Import refactored helper functions for Issue #980
from .questionnaire_helpers import (
    _flush_response_records,
    _extract_asset_ids_for_reanalysis,
    _resolve_gaps_and_update_flow,
    _commit_with_writeback,
    _update_asset_readiness,
    _create_canonical_app_for_questionnaire,
)

if TYPE_CHECKING:
    from app.schemas.collection_flow import QuestionnaireSubmissionRequest

logger = logging.getLogger(__name__)


async def submit_questionnaire_response(  # noqa: C901 - Reduced from 19 to 16, orchestrates workflow
    flow_id: str,
    questionnaire_id: str,
    request_data: "QuestionnaireSubmissionRequest",
    db: AsyncSession,
    current_user: User,
    context: RequestContext,
) -> Dict[str, Any]:
    """Submit responses to an adaptive questionnaire and save them to the database."""
    try:
        # Normalize flow_id and questionnaire_id to UUID objects for proper type safety
        try:
            flow_uuid = UUID(flow_id) if isinstance(flow_id, str) else flow_id
        except (ValueError, AttributeError) as exc:
            raise HTTPException(
                status_code=422, detail="Invalid collection flow ID format"
            ) from exc

        try:
            questionnaire_uuid = (
                UUID(questionnaire_id)
                if isinstance(questionnaire_id, str)
                else questionnaire_id
            )
        except (ValueError, AttributeError) as exc:
            raise HTTPException(
                status_code=422, detail="Invalid questionnaire ID format"
            ) from exc

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
            .where(CollectionFlow.flow_id == flow_uuid)  # Use normalized UUID
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

        # ✅ CRITICAL FIX (Issue #980): Flush response records to database immediately
        await _flush_response_records(db, response_records, flow.id)

        # ISSUE-999 Phase 2: Create canonical application and junction record
        # This ensures questionnaire path has same behavior as bulk import path
        application_name = None

        # Extract application_name from multiple sources (prioritized)
        if form_metadata and "application_name" in form_metadata:
            application_name = form_metadata.get("application_name")
        elif (
            validated_asset
            and hasattr(validated_asset, "application_name")
            and validated_asset.application_name
        ):
            application_name = validated_asset.application_name

        if application_name and application_name.strip():
            await _create_canonical_app_for_questionnaire(
                application_name=application_name,
                asset_id=asset_id,
                flow=flow,
                context=context,
                current_user=current_user,
                db=db,
            )

        # CRITICAL UX FIX: Extract asset_ids from response records for readiness re-analysis
        asset_ids_to_reanalyze = await _extract_asset_ids_for_reanalysis(
            response_records, validated_asset, asset_id, form_responses, flow
        )

        # Update flow status based on completion
        update_flow_progress(flow, form_metadata, flow_id)

        # Update flow metadata
        flow.updated_at = datetime.utcnow()

        # Mark gaps as resolved and update questionnaire completion status
        gaps_resolved = await _resolve_gaps_and_update_flow(
            response_records,
            gap_index,
            form_responses,
            flow,
            questionnaire_uuid,
            request_data,
            context,
            db,
        )

        # Apply asset writeback and commit all changes atomically
        await _commit_with_writeback(
            gaps_resolved, flow, context, current_user, response_records, db
        )

        # Re-analyze asset readiness after successful submission
        readiness_updated = await _update_asset_readiness(
            asset_ids_to_reanalyze, request_data, context, db
        )

        # CC FIX: Commit asset readiness updates
        # _update_asset_readiness stages changes but does not commit (per its docstring)
        # We must commit these changes after the main transaction is complete
        if readiness_updated:
            await db.commit()
            logger.info(
                f"✅ CC FIX: Committed asset readiness updates for {len(asset_ids_to_reanalyze)} asset(s)"
            )

        logger.info(
            f"Successfully saved {len(response_records)} questionnaire responses for flow {flow_id} "
            f"by user {current_user.id}. Flow progress: {flow.progress_percentage}%, Status: {flow.status}"
        )

        # Build response with assessment flow redirect info
        response_data = {
            "status": "success",
            "message": f"Successfully saved {len(response_records)} responses",
            "questionnaire_id": questionnaire_id,
            "flow_id": str(flow.flow_id),  # Fixed: Return flow_id UUID, not database ID
            "progress": flow.progress_percentage,
            "responses_saved": len(response_records),
            "readiness_updated": readiness_updated,
        }

        # CRITICAL UX FIX: Return assessment_flow_id if collection came from assessment flow
        # This allows frontend to redirect back to assessment flow
        if flow.assessment_flow_id:
            response_data["assessment_flow_id"] = str(flow.assessment_flow_id)
            response_data["redirect_to_assessment"] = True
            logger.info(
                f"📋 Collection flow came from assessment flow {flow.assessment_flow_id} - will redirect back"
            )

        return response_data

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
