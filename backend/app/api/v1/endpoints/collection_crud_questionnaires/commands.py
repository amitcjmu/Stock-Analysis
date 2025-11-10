"""
Command operations for collection questionnaires.
Write operations and background task management for questionnaire generation.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, select
from sqlalchemy.dialects.postgresql import insert

from app.core.context import RequestContext
from app.models.asset import Asset
from app.models.collection_flow import CollectionFlow, AdaptiveQuestionnaire
from app.schemas.collection_flow import AdaptiveQuestionnaireResponse

# Import modular functions
from app.api.v1.endpoints import collection_serializers

logger = logging.getLogger(__name__)

# Track background tasks to prevent memory leaks
_background_tasks: set = set()


async def _start_agent_generation(
    flow_id: str,
    flow: CollectionFlow,
    existing_assets: List[Asset],
    context: RequestContext,
    db: AsyncSession,
) -> List[AdaptiveQuestionnaireResponse]:
    """
    Start agent generation in background and return pending questionnaire record.

    Uses get-or-create pattern: Checks for existing questionnaire by asset_id before creating new one.
    Supports multi-asset selection - generates/reuses questionnaire per asset.
    """
    from .deduplication import (
        get_existing_questionnaire_for_asset,
        should_reuse_questionnaire,
        log_questionnaire_reuse,
        log_questionnaire_creation,
    )

    try:
        # Extract selected_asset_ids from flow metadata
        selected_asset_ids = []
        if flow.flow_metadata and isinstance(flow.flow_metadata, dict):
            raw_ids = flow.flow_metadata.get("selected_asset_ids", [])
            selected_asset_ids = [
                UUID(aid) if isinstance(aid, str) else aid for aid in raw_ids
            ]

        if not selected_asset_ids:
            logger.warning(
                f"No selected_asset_ids in flow {flow_id} metadata, falling back to existing_assets"
            )
            selected_asset_ids = [asset.id for asset in existing_assets]

        # Get-or-create questionnaire for each selected asset
        questionnaire_responses = []

        # Optimize asset lookup: Create dictionary for O(1) access instead of O(N) filtering
        assets_by_id = {asset.id: asset for asset in existing_assets}

        for asset_id in selected_asset_ids:
            # Check for existing questionnaire (scoped by engagement_id + asset_id)
            existing = await get_existing_questionnaire_for_asset(
                context.engagement_id,
                asset_id,
                db,
            )

            if existing:
                # Decide whether to reuse based on completion status
                should_reuse, reason = await should_reuse_questionnaire(existing)

                if should_reuse:
                    log_questionnaire_reuse(existing, flow.id, asset_id)
                    questionnaire_responses.append(
                        collection_serializers.build_questionnaire_response(existing)
                    )
                    continue  # Skip creation for this asset

            # No existing questionnaire or needs regeneration - create new
            log_questionnaire_creation(
                asset_id, flow.id, "No existing questionnaire found"
            )

            questionnaire_id = uuid4()
            questionnaire_data = {
                "id": questionnaire_id,
                "client_account_id": context.client_account_id,
                "engagement_id": context.engagement_id,
                "collection_flow_id": flow.id,  # Audit trail: which flow triggered creation
                "asset_id": asset_id,  # CRITICAL: Asset-based deduplication key
                "title": "AI-Generated Data Collection Questionnaire",
                "description": "Generating tailored questionnaire using AI agent analysis...",
                "template_name": "agent_generated",
                "template_type": "detailed",
                "version": "2.0",
                "applicable_tiers": ["tier_1", "tier_2", "tier_3", "tier_4"],
                "question_set": {},
                "questions": [],
                "validation_rules": {},
                "completion_status": "pending",
                "responses_collected": {},
                "is_active": True,
                "is_template": False,
                "created_at": datetime.now(timezone.utc),
            }

            # ✅ FIX: Use UPSERT to handle race conditions (phantom duplicate key errors)
            # If another request created the same questionnaire between our check and INSERT,
            # PostgreSQL's ON CONFLICT will handle it gracefully instead of throwing IntegrityError
            stmt = insert(AdaptiveQuestionnaire).values(**questionnaire_data)

            # On conflict (engagement_id + asset_id already exists), do nothing and return existing
            # CRITICAL: uq_questionnaire_per_asset_per_engagement is a PARTIAL UNIQUE INDEX (not constraint)
            # with WHERE asset_id IS NOT NULL. Must use index_elements + index_where, NOT constraint name.
            # PostgreSQL partial indexes cannot be referenced by name in ON CONFLICT ON CONSTRAINT.
            stmt = stmt.on_conflict_do_nothing(
                index_elements=["engagement_id", "asset_id"],
                index_where=(AdaptiveQuestionnaire.asset_id.isnot(None)),
            )

            # Execute UPSERT
            await db.execute(stmt)
            await db.commit()

            # Fetch the actual record (either newly inserted or existing from race condition)
            result = await db.execute(
                select(AdaptiveQuestionnaire).where(
                    AdaptiveQuestionnaire.engagement_id == context.engagement_id,
                    AdaptiveQuestionnaire.asset_id == asset_id,
                )
            )
            pending_questionnaire = result.scalar_one()

            logger.info(
                f"Created pending questionnaire {questionnaire_id} for asset {asset_id} in flow {flow_id}"
            )

            # Start background generation task for this asset
            # Use dictionary for O(1) lookup instead of O(N) filtering
            target_asset = assets_by_id.get(asset_id)
            if not target_asset:
                logger.warning(
                    f"Asset {asset_id} selected in flow but not found in existing_assets list. Skipping generation."
                )
                continue

            task = asyncio.create_task(
                _background_generate(
                    questionnaire_id,
                    flow_id,
                    flow,
                    [target_asset],  # Pass only this asset (O(1) lookup)
                    context,
                )
            )

            # Add task to background tasks set and remove when done
            _background_tasks.add(task)
            task.add_done_callback(_background_tasks.discard)

            questionnaire_responses.append(
                collection_serializers.build_questionnaire_response(
                    pending_questionnaire
                )
            )

        if not questionnaire_responses:
            logger.warning(f"No questionnaires generated or reused for flow {flow_id}")
            raise Exception("No questionnaires could be generated or reused")

        logger.info(
            f"Returning {len(questionnaire_responses)} questionnaire(s) for flow {flow_id} "
            f"({len(selected_asset_ids)} assets processed)"
        )
        return questionnaire_responses

    except Exception as e:
        logger.error(
            f"Error starting agent generation for flow {flow_id}: {e}", exc_info=True
        )
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(f"Exception details: {str(e)}")
        # Store error information for debugging
        error_msg = f"{type(e).__name__}: {str(e)}"
        logger.error(f"Failed to start agent generation - error: {error_msg}")
        raise


async def _update_questionnaire_status(
    questionnaire_id: UUID,
    status: str,
    questions: Optional[List[dict]] = None,
    error_message: Optional[str] = None,
    db: Optional[AsyncSession] = None,
) -> None:
    """Update questionnaire status and optionally add questions."""
    from app.core.database import AsyncSessionLocal

    # Use provided db session or create new one
    if db is None:
        async with AsyncSessionLocal() as session:
            await _do_update_questionnaire_status(
                session, questionnaire_id, status, questions, error_message
            )
    else:
        await _do_update_questionnaire_status(
            db, questionnaire_id, status, questions, error_message
        )


async def _do_update_questionnaire_status(
    db: AsyncSession,
    questionnaire_id: UUID,
    status: str,
    questions: Optional[List[dict]] = None,
    error_message: Optional[str] = None,
) -> None:
    """Internal helper to update questionnaire status."""
    try:
        update_data = {
            "completion_status": status,
            "updated_at": datetime.now(timezone.utc),
        }

        if questions:
            update_data["questions"] = questions
            update_data["question_count"] = len(
                questions
            )  # Update question_count column
            update_data["description"] = (
                f"AI-Generated questionnaire with {len(questions)} targeted questions"
            )

        if error_message:
            update_data["description"] = f"Generation failed: {error_message}"

        await db.execute(
            update(AdaptiveQuestionnaire)
            .where(AdaptiveQuestionnaire.id == questionnaire_id)
            .values(**update_data)
        )
        await db.commit()

        logger.info(f"Updated questionnaire {questionnaire_id} status to {status}")
    except Exception as e:
        logger.error(
            f"Error updating questionnaire {questionnaire_id} status: {e}",
            exc_info=True,
        )
        logger.error(f"Update error type: {type(e).__name__}")
        logger.error(f"Update error details: {str(e)}")
        raise


async def _background_generate(
    questionnaire_id: UUID,
    flow_id: str,
    flow: CollectionFlow,
    existing_assets: List[Asset],
    context: RequestContext,
) -> None:
    """
    Background task to generate questionnaires using AI agent with Issue #980 gap detection.

    ✅ FIX 0.5 (Issue #980): Passes database session for gap detection integration.

    This runs in background and updates the pending questionnaire record
    when generation is complete or fails.
    """
    from app.core.database import AsyncSessionLocal

    try:
        logger.info(f"Starting background questionnaire generation for {flow_id}")

        # ✅ FIX 0.5: Create database session for gap detection
        async with AsyncSessionLocal() as db:
            # Use agent generation with Issue #980 gap detection
            from .agents import _generate_agent_questionnaires

            questionnaires = await _generate_agent_questionnaires(
                flow_id, existing_assets, context, db
            )

            if questionnaires:
                # Extract questions from ALL questionnaire sections (not just first one)
                # Bug fix: Previously took only questionnaires[0].questions, losing 83% of questions
                questions = []
                for section in questionnaires:
                    if hasattr(section, "questions") and section.questions:
                        questions.extend(section.questions)

                logger.info(
                    f"Collected {len(questions)} total questions from {len(questionnaires)} sections"
                )

                # Update questionnaire with generated questions AND progress flow status
                await _update_questionnaire_status(
                    questionnaire_id,
                    "ready",  # FIX BUG#801: Set to "ready" when questions are generated for frontend display
                    questions,
                    db=db,
                )

                # Progress flow to manual_collection phase now that questionnaire is ready
                from sqlalchemy import select, update as sql_update

                flow_result = await db.execute(
                    select(CollectionFlow).where(
                        CollectionFlow.flow_id == UUID(flow_id)
                    )
                )
                current_flow = flow_result.scalar_one_or_none()

                if current_flow and current_flow.current_phase in [
                    "initialized",
                    "gap_analysis",
                    "questionnaire_generation",  # Fix: Include this phase for proper transition
                ]:
                    await db.execute(
                        sql_update(CollectionFlow)
                        .where(CollectionFlow.flow_id == UUID(flow_id))
                        .values(
                            current_phase="manual_collection",
                            status="paused",  # FIXED: Use valid enum value (awaiting user questionnaire input)
                            progress_percentage=50.0,  # Questionnaire generated = 50% progress
                            updated_at=datetime.now(timezone.utc),
                        )
                    )
                    await db.commit()
                    logger.info(
                        f"Progressed flow {flow_id} to manual_collection phase with status=paused"
                    )

                logger.info(
                    f"Successfully generated {len(questions)} questions for flow {flow_id}"
                )
            else:
                # No questionnaires generated - mark as failed
                await _update_questionnaire_status(
                    questionnaire_id,
                    "failed",
                    error_message="No questionnaires could be generated",
                    db=db,
                )
                logger.warning(f"No questionnaires generated for flow {flow_id}")

    except Exception as e:
        # Log full exception with stack trace for debugging
        logger.error(
            f"Background generation failed for flow {flow_id}: {e}", exc_info=True
        )
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(f"Exception details: {str(e)}")

        try:
            # Mark questionnaire as failed with detailed error
            error_msg = f"{type(e).__name__}: {str(e)}"
            async with AsyncSessionLocal() as db:
                await _update_questionnaire_status(
                    questionnaire_id, "failed", error_message=error_msg, db=db
                )
        except Exception as update_error:
            logger.error(
                f"Failed to update questionnaire status: {update_error}", exc_info=True
            )
    finally:
        logger.info(f"Background generation completed for flow {flow_id}")
