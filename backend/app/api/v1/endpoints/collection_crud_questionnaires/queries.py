"""
Query operations for collection questionnaires.
Read-only functions for retrieving questionnaire and related data.
"""

import logging
from datetime import datetime, timezone
from typing import List
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.context import RequestContext
from app.models.asset import Asset
from app.models.collection_flow import CollectionFlow, AdaptiveQuestionnaire
from app.schemas.collection_flow import AdaptiveQuestionnaireResponse

# Import modular functions
from app.api.v1.endpoints import collection_serializers

from .commands import _start_agent_generation

logger = logging.getLogger(__name__)


async def _get_flow_by_id(
    flow_id: str, db: AsyncSession, context: RequestContext
) -> CollectionFlow:
    """Get and validate collection flow by ID."""
    logger.debug(f"🔍 _get_flow_by_id called with flow_id={flow_id}")
    flow_result = await db.execute(
        select(CollectionFlow).where(
            CollectionFlow.flow_id == UUID(flow_id),
            CollectionFlow.engagement_id == context.engagement_id,
            CollectionFlow.client_account_id == context.client_account_id,
        )
    )
    flow = flow_result.scalar_one_or_none()
    if not flow:
        logger.warning(f"Collection flow not found: {flow_id}")
        raise HTTPException(status_code=404, detail="Collection flow not found")
    logger.debug(
        f"✅ Found flow: flow_id={flow.flow_id}, id={flow.id}, phase={flow.current_phase}"
    )
    return flow


async def _get_existing_questionnaires_tenant_scoped(
    flow: CollectionFlow, db: AsyncSession, context: RequestContext
) -> List[AdaptiveQuestionnaireResponse]:
    """Get existing questionnaires from database with tenant scoping.

    CRITICAL DEFENSIVE BEHAVIOR:
    - Excludes COMPLETED questionnaires (prevent submission loops)
    - Excludes FAILED questionnaires (allow automatic retry)

    This ensures failed generation attempts don't block new attempts.
    """
    logger.debug(f"🔍 Querying questionnaires with collection_flow_id={flow.id}")
    logger.debug(
        f"   client_account_id={context.client_account_id}, engagement_id={context.engagement_id}"
    )

    questionnaires_result = await db.execute(
        select(AdaptiveQuestionnaire)
        .where(
            AdaptiveQuestionnaire.collection_flow_id
            == flow.id,  # Use .id (PRIMARY KEY) for FK relationship
            AdaptiveQuestionnaire.client_account_id == context.client_account_id,
            AdaptiveQuestionnaire.engagement_id == context.engagement_id,
            # CC Bug #9: Exclude both completed AND failed questionnaires
            # Failed questionnaires with 0 questions should not block new generation
            AdaptiveQuestionnaire.completion_status.notin_(["completed", "failed"]),
        )
        .order_by(AdaptiveQuestionnaire.created_at.desc())
    )
    questionnaires = questionnaires_result.scalars().all()

    if questionnaires:
        logger.info(
            f"✅ Found {len(questionnaires)} incomplete questionnaires in database"
        )
        for q in questionnaires:
            logger.debug(
                f"   - Questionnaire {q.id}: {len(q.questions)} questions, status={q.completion_status}"
            )

        serialized = [
            collection_serializers.build_questionnaire_response(q)
            for q in questionnaires
        ]
        logger.debug(f"📦 Serialized {len(serialized)} questionnaire responses")
        return serialized

    logger.info(
        "❌ No incomplete questionnaires found - collection may be ready for assessment"
    )
    return []


async def _get_existing_assets(
    db: AsyncSession, context: RequestContext
) -> List[Asset]:
    """Get existing assets for engagement."""
    assets_result = await db.execute(
        select(Asset)
        .where(Asset.engagement_id == context.engagement_id)
        .where(Asset.client_account_id == context.client_account_id)
        .order_by(Asset.created_at.desc())
    )
    return list(assets_result.scalars().all())


async def get_questionnaire_by_asset(
    engagement_id: UUID,
    asset_id: UUID,
    db: AsyncSession,
    context: RequestContext,
) -> AdaptiveQuestionnaireResponse:
    """
    Get questionnaire for a specific asset in an engagement.

    Uses asset-based deduplication: returns the same questionnaire across flows
    for the same asset. Enables questionnaire reuse and prevents duplicate data entry.

    Args:
        engagement_id: Engagement ID (tenant scope)
        asset_id: Asset ID to look up
        db: Database session
        context: Request context for authorization

    Returns:
        AdaptiveQuestionnaireResponse for the asset

    Raises:
        HTTPException(404): If no questionnaire found for this asset
    """
    from .deduplication import get_existing_questionnaire_for_asset

    try:
        # Check for existing questionnaire (scoped by engagement_id + asset_id)
        existing = await get_existing_questionnaire_for_asset(
            engagement_id,
            asset_id,
            db,
        )

        if not existing:
            logger.warning(
                f"No questionnaire found for asset {asset_id} in engagement {engagement_id}"
            )
            raise HTTPException(
                status_code=404,
                detail=f"No questionnaire found for asset {asset_id}. Please create a collection flow first.",
            )

        logger.info(
            f"Found questionnaire {existing.id} for asset {asset_id} "
            f"(status: {existing.completion_status})"
        )

        return collection_serializers.build_questionnaire_response(existing)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error getting questionnaire for asset {asset_id}: {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail=str(e))


async def get_adaptive_questionnaires(
    flow_id: str, db: AsyncSession, context: RequestContext
) -> List[AdaptiveQuestionnaireResponse]:
    """
    Get adaptive questionnaires for a collection flow.

    Returns existing questionnaires if available, otherwise generates new ones
    using AI agent analysis or falls back to template-based generation.
    """
    try:
        logger.info(f"Getting adaptive questionnaires for flow {flow_id}")

        # Get flow with tenant scoping
        flow = await _get_flow_by_id(flow_id, db, context)

        # Check for existing questionnaires in database with tenant scoping
        existing_questionnaires = await _get_existing_questionnaires_tenant_scoped(
            flow, db, context
        )

        if existing_questionnaires:
            logger.info(
                f"✅ Returning {len(existing_questionnaires)} existing questionnaires to frontend"
            )
            for q in existing_questionnaires:
                logger.debug(
                    f"   - Questionnaire {q.id}: {len(q.questions) if q.questions else 0} questions"
                )

            # ✅ DEFENSIVE FIX: Check if phase transition was missed (e.g., background task interrupted)
            # If questionnaire exists with questions but phase is still questionnaire_generation,
            # transition to manual_collection now
            has_questions = any(
                hasattr(q, "questions") and q.questions and len(q.questions) > 0
                for q in existing_questionnaires
            )

            if has_questions and flow.current_phase == "questionnaire_generation":
                logger.warning(
                    f"⚠️ Flow {flow_id} has questionnaire with questions but phase "
                    f"is still 'questionnaire_generation'. Performing defensive phase "
                    f"transition to 'manual_collection'"
                )

                try:
                    from sqlalchemy import update as sql_update

                    await db.execute(
                        sql_update(CollectionFlow)
                        .where(CollectionFlow.flow_id == UUID(flow_id))
                        .values(
                            current_phase="manual_collection",
                            status="paused",  # Awaiting user questionnaire input
                            progress_percentage=50.0,  # Questionnaire generated = 50% progress
                            updated_at=datetime.now(timezone.utc),
                        )
                    )
                    await db.commit()

                    logger.info(
                        f"✅ Defensive phase transition successful: {flow_id} → manual_collection"
                    )
                except Exception as phase_error:
                    # Don't fail the request if phase transition fails
                    # Questionnaire retrieval already succeeded
                    logger.error(
                        f"❌ Defensive phase transition failed for {flow_id}: {phase_error}",
                        exc_info=True,
                    )

            return existing_questionnaires

        # CRITICAL: If no incomplete questionnaires AND assessment_ready is true, return empty array
        # This signals that collection is complete and should transition to assessment
        if flow.assessment_ready:
            logger.info(
                f"✅ Collection flow {flow_id} is assessment-ready with no incomplete questionnaires. "
                "Returning empty array to signal completion."
            )
            return []

        # Get existing assets for this engagement
        all_assets = await _get_existing_assets(db, context)
        logger.info(f"Found {len(all_assets)} total assets for engagement")

        # Debug logging for metadata check
        logger.info(f"flow.flow_metadata = {flow.flow_metadata}")
        logger.info(f"flow.current_phase = {flow.current_phase}")
        use_agent_gen = (
            flow.flow_metadata.get("use_agent_generation", True)
            if flow.flow_metadata
            else True
        )
        logger.info(f"use_agent_generation = {use_agent_gen}")

        # CRITICAL FIX: Check if we're in asset_selection phase FIRST
        # This phase DOES NOT require selected_application_ids yet - it generates the bootstrap questionnaire
        # that allows users TO SELECT assets
        if flow.current_phase == "asset_selection":
            logger.info(
                f"Flow {flow_id} is in asset_selection phase - checking for bootstrap questionnaire or recovery needs"
            )

            # Check if flow has bootstrap questionnaire in collection_config
            bootstrap_q = (
                flow.collection_config.get("bootstrap_questionnaire")
                if flow.collection_config
                else None
            )
            if bootstrap_q:
                logger.info(
                    "Returning existing bootstrap questionnaire for asset selection phase"
                )
                # Convert bootstrap format to AdaptiveQuestionnaireResponse format
                return [
                    AdaptiveQuestionnaireResponse(
                        id=bootstrap_q.get(
                            "questionnaire_id", "bootstrap_asset_selection"
                        ),
                        collection_flow_id=flow_id,
                        title=bootstrap_q.get(
                            "title", "Select Applications for Collection"
                        ),
                        description=bootstrap_q.get(
                            "description",
                            "Choose which applications you want to collect detailed information about.",
                        ),
                        target_gaps=[],
                        questions=bootstrap_q.get("fields", []),
                        validation_rules=bootstrap_q.get("validation_rules", {}),
                        completion_status="pending",
                        responses_collected={},
                        created_at=datetime.now(timezone.utc),
                        completed_at=None,
                    )
                ]
            else:
                # Generate bootstrap questionnaire for asset selection (including stuck flow recovery)
                logger.info(
                    "No bootstrap questionnaire found - generating new one (handles stuck flows)"
                )
                from app.services.collection.asset_selection_bootstrap import (
                    generate_asset_selection_bootstrap,
                )

                try:
                    bootstrap_result = await generate_asset_selection_bootstrap(
                        flow, db, context
                    )

                    if bootstrap_result.get(
                        "status"
                    ) == "bootstrap_generated" and bootstrap_result.get(
                        "questionnaire"
                    ):
                        bootstrap_q = bootstrap_result["questionnaire"]
                        logger.info(
                            f"Successfully generated bootstrap questionnaire for flow {flow_id}"
                        )
                        return [
                            AdaptiveQuestionnaireResponse(
                                id=bootstrap_q.get(
                                    "questionnaire_id", "bootstrap_asset_selection"
                                ),
                                collection_flow_id=flow_id,
                                title=bootstrap_q.get(
                                    "title", "Select Applications for Collection"
                                ),
                                description=bootstrap_q.get(
                                    "description",
                                    "Choose which applications you want to collect detailed information about.",
                                ),
                                target_gaps=[],
                                questions=bootstrap_q.get("fields", []),
                                validation_rules=bootstrap_q.get(
                                    "validation_rules", {}
                                ),
                                completion_status="pending",
                                responses_collected={},
                                created_at=datetime.now(timezone.utc),
                                completed_at=None,
                            )
                        ]
                    elif bootstrap_result.get("status") == "no_assets_available":
                        # Handle case where no assets are available
                        logger.warning(
                            f"No assets available for flow {flow_id} - creating informational questionnaire"
                        )
                        return [
                            AdaptiveQuestionnaireResponse(
                                id=str(UUID("00000000-0000-0000-0000-000000000002")),
                                collection_flow_id=flow_id,
                                title="No Applications Available",
                                description=bootstrap_result.get(
                                    "message",
                                    (
                                        "No applications found. Please run Discovery flow first "
                                        "or add applications manually."
                                    ),
                                ),
                                target_gaps=[],
                                questions=[
                                    {
                                        "id": "no_assets_message",
                                        "question_text": (
                                            "No applications are currently available for collection. "
                                            "Please ensure you have run a Discovery flow or manually "
                                            "added applications to your engagement."
                                        ),
                                        "field_type": "informational",
                                        "required": False,
                                        "category": "system_message",
                                    }
                                ],
                                validation_rules={},
                                completion_status="pending",
                                responses_collected={},
                                created_at=datetime.now(timezone.utc),
                                completed_at=None,
                            )
                        ]
                    elif bootstrap_result.get("status") == "assets_already_selected":
                        # Flow has assets but bootstrap wasn't generated - recovery scenario
                        logger.info(
                            f"Flow {flow_id} has assets already selected but no bootstrap - triggering recovery"
                        )
                        # This is a stuck flow recovery case - let it continue to agent generation
                        pass
                    else:
                        # Handle other bootstrap generation failures
                        logger.error(
                            f"Bootstrap generation failed for flow {flow_id}: {bootstrap_result}"
                        )
                        error_msg = bootstrap_result.get("error", "Unknown error")
                        raise HTTPException(
                            status_code=500,
                            detail=f"Failed to generate bootstrap questionnaire: {error_msg}",
                        )

                except Exception as e:
                    logger.error(
                        f"Error generating bootstrap questionnaire for flow {flow_id}: {e}",
                        exc_info=True,
                    )
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to generate bootstrap questionnaire: {str(e)}",
                    )

        # CRITICAL: For non-asset-selection phases, require selected assets
        # Filter to only the selected assets from the collection flow
        selected_asset_ids = []
        if flow.flow_metadata and flow.flow_metadata.get("selected_asset_ids"):
            selected_asset_ids = flow.flow_metadata["selected_asset_ids"]
            logger.info(f"Flow has {len(selected_asset_ids)} selected asset IDs")

        # Filter assets to only those that were selected
        existing_assets = []
        if selected_asset_ids:
            for asset in all_assets:
                if str(asset.id) in selected_asset_ids:
                    existing_assets.append(asset)
            logger.info(
                f"Filtered to {len(existing_assets)} selected assets for questionnaire generation"
            )
        else:
            # CRITICAL: Do NOT generate questionnaires without asset selection
            # This prevents generating irrelevant questions for all assets
            logger.warning(
                f"Flow {flow_id} in {flow.current_phase} phase but no assets selected. "
                "Cannot generate questionnaire without asset selection."
            )
            raise HTTPException(
                status_code=400,
                detail=(
                    "Asset selection required before questionnaire generation. "
                    "Please select at least one asset first."
                ),
            )

        # AI agent generation should be the ONLY approach for non-asset-selection phases
        # Disable fallback mechanism to identify actual issues
        if not flow.flow_metadata or not flow.flow_metadata.get(
            "use_agent_generation", True
        ):
            logger.error(
                f"Flow {flow_id} does not have agent generation enabled in metadata"
            )
            raise HTTPException(
                status_code=500,
                detail="Flow must have agent generation enabled. No fallback allowed.",
            )

        logger.info("Using AI agent generation for questionnaires - NO FALLBACKS")
        return await _start_agent_generation(
            flow_id, flow, existing_assets, context, db
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting adaptive questionnaires for flow {flow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
