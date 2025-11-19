"""Command operations for collection questionnaires (writes, background tasks)."""

import asyncio
import logging
from datetime import datetime, timezone
from typing import List
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.context import RequestContext
from app.models.asset import Asset
from app.models.collection_flow import CollectionFlow, AdaptiveQuestionnaire
from app.models.collection_data_gap import CollectionDataGap
from app.schemas.collection_flow import AdaptiveQuestionnaireResponse

# Import modular functions
from app.api.v1.endpoints import collection_serializers
from .database_helpers import (
    update_questionnaire_status,
    load_assets_for_background,
    get_flow_db_id,
)

logger = logging.getLogger(__name__)

# Track background tasks to prevent memory leaks
_background_tasks: set = set()


async def _start_agent_generation(  # noqa: C901 - Complexity needed for error handling
    flow_id: str,
    flow: CollectionFlow,
    existing_assets: List[Asset],
    context: RequestContext,
    db: AsyncSession,
) -> List[AdaptiveQuestionnaireResponse]:
    """Start agent generation in background (get-or-create by asset_id, multi-asset support)."""
    from .deduplication import (
        get_existing_questionnaire_for_asset,
        should_reuse_questionnaire,
        log_questionnaire_reuse,
        log_questionnaire_creation,
    )

    try:
        # Eagerly load flow attributes to avoid SQLAlchemy lazy-loading issues
        flow_db_id = flow.id
        # CC FIX Bug #5: Eagerly load master_flow_id before passing to background task
        master_flow_id = str(flow.master_flow_id) if flow.master_flow_id else flow_id

        # Extract selected_asset_ids from flow metadata
        selected_asset_ids: List[UUID] = []
        selected_asset_ids_str: List[str] = []
        if flow.flow_metadata and isinstance(flow.flow_metadata, dict):
            raw_ids = flow.flow_metadata.get("selected_asset_ids", [])
            for aid in raw_ids:
                asset_uuid = UUID(aid) if isinstance(aid, str) else aid
                selected_asset_ids.append(asset_uuid)
                selected_asset_ids_str.append(str(asset_uuid))

        if not selected_asset_ids:
            logger.warning(
                f"No selected_asset_ids in flow {flow_id} metadata, falling back to existing_assets"
            )
            selected_asset_ids = [asset.id for asset in existing_assets]
            selected_asset_ids_str = [str(asset.id) for asset in existing_assets]

        # Get-or-create questionnaire for each selected asset
        questionnaire_responses = []

        # Optimize asset lookup: Create dictionary for O(1) access instead of O(N) filtering
        assets_by_id = {str(asset.id): asset for asset in existing_assets}

        for index, asset_id in enumerate(selected_asset_ids):
            asset_id_str = (
                selected_asset_ids_str[index]
                if index < len(selected_asset_ids_str)
                else str(asset_id)
            )
            # Check for existing questionnaire (scoped by client_account_id + engagement_id + asset_id)
            existing = await get_existing_questionnaire_for_asset(
                context.client_account_id,
                context.engagement_id,
                asset_id,
                db,
            )

            if existing:
                # CRITICAL FIX: Check if questionnaire needs updating for new gaps
                # Even completed questionnaires should be updated when new gaps are added

                # Get current gaps for this asset in the CURRENT flow
                current_gaps_result = await db.execute(
                    select(CollectionDataGap).where(
                        and_(
                            CollectionDataGap.collection_flow_id == flow.id,
                            CollectionDataGap.asset_id == asset_id,
                            CollectionDataGap.resolution_status != "resolved",
                        )
                    )
                )
                current_gaps = current_gaps_result.scalars().all()
                current_gap_fields = {gap.field_name for gap in current_gaps}

                # Get fields already covered by existing questionnaire
                existing_questions = (
                    existing.questions if isinstance(existing.questions, list) else []
                )
                existing_fields = {
                    q.get("field_id") or q.get("field_name") for q in existing_questions
                }

                # Find NEW gaps not covered by existing questionnaire
                new_gap_fields = current_gap_fields - existing_fields

                if new_gap_fields:
                    # New gaps detected - UPDATE questionnaire instead of reusing
                    logger.info(
                        f"🔄 Updating questionnaire {existing.id} for asset {asset_id}: "
                        f"{len(new_gap_fields)} new gaps detected ({', '.join(list(new_gap_fields)[:3])}...)"
                    )

                    # Update to current flow
                    existing.collection_flow_id = flow.id

                    # Reset status to trigger regeneration
                    if existing.completion_status == "completed":
                        existing.completion_status = "pending"
                        logger.info(
                            "   Status changed: completed → pending (will regenerate)"
                        )

                    existing.updated_at = datetime.now(timezone.utc)
                    existing.description = (
                        f"Updating questionnaire with {len(new_gap_fields)} new gaps..."
                    )

                    await db.commit()
                    await db.refresh(existing)

                    # Trigger background regeneration to append new questions
                    target_asset = assets_by_id.get(asset_id_str)
                    if target_asset:
                        task = asyncio.create_task(
                            _background_generate(
                                existing.id,
                                flow_id,
                                master_flow_id,
                                [asset_id_str],
                                context,
                            )
                        )
                        _background_tasks.add(task)
                        task.add_done_callback(_background_tasks.discard)

                    questionnaire_responses.append(
                        collection_serializers.build_questionnaire_response(existing)
                    )
                    continue

                # No new gaps - reuse as-is
                should_reuse, reason = await should_reuse_questionnaire(existing)

                if should_reuse:
                    # Update collection_flow_id to current flow even when reusing
                    if existing.collection_flow_id != flow.id:
                        logger.info(
                            f"📎 Linking questionnaire {existing.id} to current flow {flow.id}"
                        )
                        existing.collection_flow_id = flow.id
                        await db.commit()
                        await db.refresh(existing)

                    log_questionnaire_reuse(existing, flow_db_id, asset_id)
                    questionnaire_responses.append(
                        collection_serializers.build_questionnaire_response(existing)
                    )
                    continue  # Skip creation for this asset

            # Check if a FAILED questionnaire exists (filtered out by get_existing above)
            # If so, UPDATE it to pending instead of creating duplicate
            failed_result = await db.execute(
                select(AdaptiveQuestionnaire).where(
                    AdaptiveQuestionnaire.client_account_id
                    == context.client_account_id,
                    AdaptiveQuestionnaire.engagement_id == context.engagement_id,
                    AdaptiveQuestionnaire.asset_id == asset_id,
                    AdaptiveQuestionnaire.completion_status == "failed",
                )
            )
            failed_questionnaire = failed_result.scalar_one_or_none()

            if failed_questionnaire:
                # Reset failed questionnaire to pending for retry
                logger.info(
                    f"Found failed questionnaire {failed_questionnaire.id} for asset {asset_id}, "
                    f"resetting to pending for retry (flow {flow.id})"
                )
                failed_questionnaire.completion_status = "pending"
                failed_questionnaire.updated_at = datetime.now(timezone.utc)
                failed_questionnaire.collection_flow_id = (
                    flow.id
                )  # Update to current flow
                failed_questionnaire.description = (
                    "Generating tailored questionnaire using AI agent analysis..."
                )
                await db.commit()
                await db.refresh(failed_questionnaire)
                questionnaire_id = failed_questionnaire.id

                # Start background generation for the updated questionnaire
                target_asset = assets_by_id.get(asset_id_str)
                if target_asset:
                    task = asyncio.create_task(
                        _background_generate(
                            questionnaire_id,
                            flow_id,
                            master_flow_id,
                            [asset_id_str],
                            context,
                        )
                    )
                    _background_tasks.add(task)
                    task.add_done_callback(_background_tasks.discard)
                else:
                    logger.warning(
                        f"Asset {asset_id_str} selected in flow but not found in existing_assets list"
                    )

                questionnaire_responses.append(
                    collection_serializers.build_questionnaire_response(
                        failed_questionnaire
                    )
                )
                continue  # Skip creating new questionnaire

            # No existing questionnaire - create new
            log_questionnaire_creation(
                asset_id, flow_db_id, "No existing questionnaire found"
            )

            # CRITICAL FIX: Fetch gaps for this asset to populate target_gaps field
            # This prevents the infinite polling issue where frontend waits for target_gaps to be populated

            gaps_result = await db.execute(
                select(CollectionDataGap).where(
                    and_(
                        CollectionDataGap.collection_flow_id == flow.id,
                        CollectionDataGap.asset_id == asset_id,
                        CollectionDataGap.resolution_status != "resolved",
                    )
                )
            )
            gaps = gaps_result.scalars().all()

            # Build target_gaps array from fetched gaps
            target_gaps = []
            for gap in gaps:
                target_gaps.append(
                    {
                        "field_name": gap.field_name,
                        "gap_type": gap.gap_type,
                        "gap_category": gap.gap_category,
                        "asset_id": str(gap.asset_id),
                        "priority": gap.priority,
                        "impact_on_sixr": gap.impact_on_sixr,
                    }
                )

            questionnaire_id = uuid4()
            questionnaire_data = {
                "id": questionnaire_id,
                "client_account_id": context.client_account_id,
                "engagement_id": context.engagement_id,
                "collection_flow_id": flow_db_id,  # Audit trail: which flow triggered creation
                "asset_id": asset_id,  # CRITICAL: Asset-based deduplication key
                "title": "AI-Generated Data Collection Questionnaire",
                "description": "Generating tailored questionnaire using AI agent analysis...",
                "template_name": "agent_generated",
                "template_type": "detailed",
                "version": "2.0",
                "applicable_tiers": ["tier_1", "tier_2", "tier_3", "tier_4"],
                "question_set": {},
                "questions": [],
                "target_gaps": target_gaps,  # CRITICAL FIX: Populate target_gaps from collection gaps
                "validation_rules": {},
                "completion_status": "pending",
                "responses_collected": {},
                "is_active": True,
                "is_template": False,
                "created_at": datetime.now(timezone.utc),
            }

            # ✅ FIX: Handle race conditions with explicit IntegrityError
            # If another request created the same questionnaire between our check and INSERT,
            # catch the unique constraint violation and fetch the existing record
            # Note: We have a UNIQUE INDEX (not constraint) so ON CONFLICT won't work
            try:
                # Attempt to insert the new questionnaire
                pending_questionnaire = AdaptiveQuestionnaire(**questionnaire_data)
                db.add(pending_questionnaire)
                await db.commit()
                await db.refresh(pending_questionnaire)

            except Exception as insert_error:
                # Roll back the failed transaction
                await db.rollback()

                # Check if it's an IntegrityError (unique constraint violation)
                from sqlalchemy.exc import IntegrityError

                if isinstance(insert_error, IntegrityError) or (
                    "duplicate key" in str(insert_error).lower()
                    or "unique" in str(insert_error).lower()
                ):
                    # Race condition: Another request created this questionnaire
                    logger.info(
                        f"Questionnaire already exists for engagement {context.engagement_id} "
                        f"and asset {asset_id}, fetching existing record"
                    )

                    # CC FIX Issue #1: Filter out failed questionnaires to avoid data loss
                    # Fetch the existing questionnaire that isn't failed
                    result = await db.execute(
                        select(AdaptiveQuestionnaire).where(
                            AdaptiveQuestionnaire.engagement_id
                            == context.engagement_id,
                            AdaptiveQuestionnaire.asset_id == asset_id,
                            AdaptiveQuestionnaire.completion_status != "failed",
                        )
                    )
                    pending_questionnaire = result.scalar_one_or_none()

                    # If no valid questionnaire exists, it's safe to proceed with creating a new one
                    # The original insert failed, so we can now re-attempt it
                    if pending_questionnaire is None:
                        logger.warning(
                            f"A failed questionnaire exists for asset {asset_id}. "
                            f"Proceeding to create a new one."
                        )
                        # Create a new questionnaire (the failed one will remain in DB for audit)
                        pending_questionnaire = AdaptiveQuestionnaire(
                            **questionnaire_data
                        )
                        db.add(pending_questionnaire)
                        await db.commit()
                        await db.refresh(pending_questionnaire)
                else:
                    # Different error, re-raise
                    raise

            logger.info(
                f"Created pending questionnaire {questionnaire_id} for asset {asset_id} in flow {flow_id}"
            )

            # Start background generation task for this asset
            # Use dictionary for O(1) lookup instead of O(N) filtering
            target_asset = assets_by_id.get(asset_id_str)
            if not target_asset:
                logger.warning(
                    f"Asset {asset_id_str} selected in flow but not found in existing_assets list. Skipping generation."
                )
                continue

            task = asyncio.create_task(
                _background_generate(
                    questionnaire_id,
                    flow_id,
                    master_flow_id,  # CC FIX Bug #5: Pass master_flow_id instead of flow object
                    [asset_id_str],
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


# DB helpers in database_helpers.py: update_questionnaire_status, load_assets_for_background, get_flow_db_id


async def _background_generate(
    questionnaire_id: UUID,
    flow_id: str,
    master_flow_id: str,  # CC FIX: Accept master flow ID as parameter to avoid detached object access
    asset_ids: List[str],
    context: RequestContext,
) -> None:
    """Background task for AI questionnaire generation with Issue #980 gap detection."""
    from app.core.database import AsyncSessionLocal
    from sqlalchemy import (
        select,
        update as sql_update,
    )  # CC FIX: Move import to top level for error handler access

    try:
        logger.info(f"Starting background questionnaire generation for {flow_id}")

        # ✅ FIX 0.5: Create database session for gap detection
        async with AsyncSessionLocal() as db:
            # CC FIX Issue #2: Get flow_db_id (collection_flows.id PK)
            flow_db_id = await get_flow_db_id(db, flow_id)

            if not flow_db_id:
                logger.error(f"Collection flow {flow_id} not found in background task")
                await update_questionnaire_status(
                    questionnaire_id,
                    "failed",
                    error_message="Collection flow not found",
                    db=db,
                )
                return

            existing_assets = await load_assets_for_background(
                db, context, flow_id, asset_ids
            )

            if not existing_assets:
                logger.warning(
                    "No assets reloaded for questionnaire generation in flow %s; "
                    "marking questionnaire as failed",
                    flow_id,
                )
                await update_questionnaire_status(
                    questionnaire_id,
                    "failed",
                    error_message="No assets available for questionnaire generation",
                    db=db,
                )
                return

            # Per ADR-035: Use per-asset, per-section generation with Redis caching
            from ._generate_per_section import _generate_questionnaires_per_section

            # CC FIX Issue #2: Pass flow_db_id (collection_flows.id PK) for gap analysis
            questionnaires = await _generate_questionnaires_per_section(
                flow_id, flow_db_id, existing_assets, context, db
            )

            if questionnaires:
                # Extract questions from ALL questionnaire sections (not just first one)
                # Bug fix: Previously took only questionnaires[0].questions, losing 83% of questions
                questions = []
                for section in questionnaires:
                    # CC FIX: section is a dict, not an object - use .get() not hasattr()
                    if isinstance(section, dict) and section.get("questions"):
                        questions.extend(section["questions"])
                    elif hasattr(section, "questions") and section.questions:
                        # Fallback for object-based sections (backward compatibility)
                        questions.extend(section.questions)

                logger.info(
                    f"Collected {len(questions)} total questions from {len(questionnaires)} sections"
                )

                # CRITICAL FIX Bug #10: Deduplicate questions at flattening stage
                # Issue: Agent sometimes generates duplicate questions within the same section
                # Deduplication service only deduplicates across assets, not within sections
                # Use field_id as unique identifier per question
                seen_field_ids = set()
                deduplicated_questions = []
                duplicates_removed = 0

                for question in questions:
                    field_id = question.get("field_id") if isinstance(question, dict) else getattr(question, "field_id", None)
                    if field_id and field_id in seen_field_ids:
                        duplicates_removed += 1
                        logger.debug(f"Removed duplicate question: {field_id}")
                        continue
                    if field_id:
                        seen_field_ids.add(field_id)
                    deduplicated_questions.append(question)

                if duplicates_removed > 0:
                    logger.warning(
                        f"Removed {duplicates_removed} duplicate questions during flattening "
                        f"({len(questions)} → {len(deduplicated_questions)} questions)"
                    )
                    questions = deduplicated_questions
                else:
                    logger.info("No duplicate questions found during flattening")

                # Update questionnaire with generated questions AND progress flow status
                await update_questionnaire_status(
                    questionnaire_id,
                    "ready",  # FIX BUG#801: Set to "ready" when questions are generated for frontend display
                    questions,
                    db=db,
                )

                # Progress flow to manual_collection phase now that questionnaire is ready
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
                await update_questionnaire_status(
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
                await update_questionnaire_status(
                    questionnaire_id, "failed", error_message=error_msg, db=db
                )

                # Per ADR-035: Surface error to flow status (no silent failures)
                # Update flow status to show questionnaire generation failed
                flow_result = await db.execute(
                    select(CollectionFlow).where(
                        CollectionFlow.flow_id == UUID(flow_id)
                    )
                )
                current_flow = flow_result.scalar_one_or_none()

                if current_flow:
                    await db.execute(
                        sql_update(CollectionFlow)
                        .where(CollectionFlow.flow_id == UUID(flow_id))
                        .values(
                            status="failed",  # Mark flow as failed
                            current_phase="questionnaire_generation",  # Show which phase failed
                            updated_at=datetime.now(timezone.utc),
                        )
                    )
                    await db.commit()
                    logger.error(
                        f"Marked flow {flow_id} as failed due to questionnaire generation error"
                    )

        except Exception as update_error:
            logger.error(
                f"Failed to update questionnaire/flow status: {update_error}",
                exc_info=True,
            )
    finally:
        logger.info(f"Background generation completed for flow {flow_id}")
