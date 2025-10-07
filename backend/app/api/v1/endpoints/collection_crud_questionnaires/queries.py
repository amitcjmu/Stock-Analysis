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
    return flow


async def _get_existing_questionnaires_tenant_scoped(
    flow: CollectionFlow, db: AsyncSession, context: RequestContext
) -> List[AdaptiveQuestionnaireResponse]:
    """Get existing questionnaires from database with tenant scoping.

    CRITICAL: Only returns questionnaires that are NOT completed.
    Completed questionnaires should not be returned to prevent submission loops.
    """
    questionnaires_result = await db.execute(
        select(AdaptiveQuestionnaire)
        .where(
            AdaptiveQuestionnaire.collection_flow_id
            == flow.id,  # Use .id (PRIMARY KEY) for FK relationship
            AdaptiveQuestionnaire.client_account_id == context.client_account_id,
            AdaptiveQuestionnaire.engagement_id == context.engagement_id,
            AdaptiveQuestionnaire.completion_status
            != "completed",  # Exclude completed questionnaires
        )
        .order_by(AdaptiveQuestionnaire.created_at.desc())
    )
    questionnaires = questionnaires_result.scalars().all()

    if questionnaires:
        logger.info(
            f"Found {len(questionnaires)} incomplete questionnaires in database"
        )
        return [
            collection_serializers.build_questionnaire_response(q)
            for q in questionnaires
        ]

    logger.info(
        "No incomplete questionnaires found - collection may be ready for assessment"
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
                f"Returning {len(existing_questionnaires)} existing questionnaires"
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
        if flow.collection_config and flow.collection_config.get(
            "selected_application_ids"
        ):
            selected_asset_ids = flow.collection_config["selected_application_ids"]
            logger.info(f"Flow has {len(selected_asset_ids)} selected application IDs")

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
