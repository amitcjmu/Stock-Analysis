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

        # CRITICAL UX FIX: Extract asset_ids from response records (they have the correct asset_id per field)
        # Response records extract asset_id from composite field IDs (format: {asset_id}__{field_id})
        asset_ids_to_reanalyze = set()
        for response_record in response_records:
            if response_record.asset_id:
                asset_ids_to_reanalyze.add(response_record.asset_id)

        # Fallback: Extract asset_id from validated_asset if available
        if not asset_ids_to_reanalyze and validated_asset:
            asset_ids_to_reanalyze.add(validated_asset.id)

        # Fallback: Extract asset_id from form_metadata
        if not asset_ids_to_reanalyze and asset_id:
            try:
                asset_ids_to_reanalyze.add(
                    UUID(asset_id) if isinstance(asset_id, str) else asset_id
                )
            except (ValueError, TypeError):
                logger.warning(f"Invalid asset_id in form_metadata: {asset_id}")

        # Fallback: Extract asset_ids from composite field IDs (format: {asset_id}__{field_id})
        if not asset_ids_to_reanalyze:
            for field_id in form_responses.keys():
                if "__" in field_id:
                    parts = field_id.split("__", 1)
                    if len(parts) == 2:
                        potential_asset_id = parts[0]
                        try:
                            asset_uuid = UUID(potential_asset_id)
                            asset_ids_to_reanalyze.add(asset_uuid)
                        except (ValueError, TypeError):
                            # Not a UUID, skip
                            pass

        # Fallback: Check if flow has selected assets
        if not asset_ids_to_reanalyze and flow.flow_metadata:
            selected_asset_ids = flow.flow_metadata.get("selected_asset_ids", [])
            if selected_asset_ids:
                try:
                    for aid in selected_asset_ids[:5]:  # Limit to 5 for performance
                        asset_ids_to_reanalyze.add(
                            UUID(aid) if isinstance(aid, str) else aid
                        )
                except (ValueError, TypeError):
                    logger.warning(
                        f"Invalid asset IDs in flow metadata: {selected_asset_ids}"
                    )

        # Convert set to list for iteration
        asset_ids_to_reanalyze = list(asset_ids_to_reanalyze)
        logger.info(
            f"📋 Extracted {len(asset_ids_to_reanalyze)} asset ID(s) "
            f"for readiness re-analysis: {[str(aid) for aid in asset_ids_to_reanalyze]}"
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
            .where(
                AdaptiveQuestionnaire.id == questionnaire_uuid
            )  # Use normalized UUID
            .where(AdaptiveQuestionnaire.collection_flow_id == flow.id)
        )
        questionnaire = questionnaire_result.scalar_one_or_none()

        if questionnaire:
            # CRITICAL FIX (Issue #692): Check save_type to determine completion status
            # - save_progress: Keep as in_progress, skip assessment check
            # - submit_complete: Mark as completed, trigger assessment check
            if request_data.save_type == "submit_complete":
                questionnaire.completion_status = "completed"
                questionnaire.completed_at = datetime.utcnow()
                logger.info(
                    f"✅ FIX#692: Marking questionnaire {questionnaire_id} as completed "
                    f"(save_type={request_data.save_type})"
                )

                # Check if collection is complete and ready for assessment
                # Required attributes: business_criticality, environment
                await check_and_set_assessment_ready(
                    flow, form_responses, db, context, logger
                )
            else:
                # save_progress: Keep as in_progress
                questionnaire.completion_status = "in_progress"
                logger.info(
                    f"💾 FIX#692: Saving progress for questionnaire {questionnaire_id} "
                    f"(save_type={request_data.save_type}, status=in_progress)"
                )

            # Always update responses_collected for both save types
            questionnaire.responses_collected = form_responses
        else:
            logger.warning(
                f"⚠️ Could not find questionnaire {questionnaire_id} to mark as completed"
            )

        # Apply resolved gaps to assets via write-back service before commit
        # This preserves atomicity - both DB changes and writeback succeed or both fail
        await apply_asset_writeback(gaps_resolved, flow, context, current_user, db)

        # Commit all changes (including writeback updates) atomically
        logger.info(f"Committing {len(response_records)} response records to database")
        await db.commit()

        readiness_updated = False
        if asset_ids_to_reanalyze and request_data.save_type == "submit_complete":
            try:
                logger.info(
                    f"🔄 Re-analyzing readiness for {len(asset_ids_to_reanalyze)} asset(s) "
                    f"after questionnaire submission"
                )

                from app.services.assessment.asset_readiness_service import (
                    AssetReadinessService,
                )

                readiness_service = AssetReadinessService()

                # Re-analyze each asset and update readiness
                for asset_uuid in asset_ids_to_reanalyze:
                    try:
                        gap_report = await readiness_service.analyze_asset_readiness(
                            asset_id=asset_uuid,
                            client_account_id=str(context.client_account_id),
                            engagement_id=str(context.engagement_id),
                            db=db,
                        )

                        # Update asset readiness fields
                        from sqlalchemy import update
                        from app.models.asset import Asset

                        update_stmt = (
                            update(Asset)
                            .where(
                                Asset.id == asset_uuid,
                                Asset.client_account_id == context.client_account_id,
                                Asset.engagement_id == context.engagement_id,
                            )
                            .values(
                                assessment_readiness=(
                                    "ready"
                                    if gap_report.is_ready_for_assessment
                                    else "not_ready"
                                ),
                                assessment_readiness_score=gap_report.overall_completeness,
                                assessment_blockers=(
                                    gap_report.readiness_blockers
                                    if gap_report.readiness_blockers
                                    else []
                                ),
                            )
                        )
                        await db.execute(update_stmt)
                        readiness_updated = True

                        logger.info(
                            f"✅ Updated readiness for asset {asset_uuid}: "
                            f"ready={gap_report.is_ready_for_assessment}, "
                            f"completeness={gap_report.overall_completeness:.2f}"
                        )
                    except Exception as e:
                        logger.warning(
                            f"Failed to re-analyze readiness for asset {asset_uuid}: {e}"
                        )
                        continue

                if readiness_updated:
                    await db.commit()
                    logger.info(
                        "✅ Asset readiness updated after questionnaire submission"
                    )
            except Exception as e:
                logger.error(
                    f"Failed to re-analyze readiness after submission: {e}",
                    exc_info=True,
                )
                # Don't fail the submission if readiness update fails

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
