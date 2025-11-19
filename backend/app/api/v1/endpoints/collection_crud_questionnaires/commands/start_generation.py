"""Agent generation starter for collection questionnaires."""

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
from .shared import _background_tasks
from .background_task import _background_generate

logger = logging.getLogger(__name__)


async def _start_agent_generation(  # noqa: C901 - Complexity needed for error handling
    flow_id: str,
    flow: CollectionFlow,
    existing_assets: List[Asset],
    context: RequestContext,
    db: AsyncSession,
) -> List[AdaptiveQuestionnaireResponse]:
    """Start agent generation in background (get-or-create by asset_id, multi-asset support)."""
    from ..deduplication import (
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
