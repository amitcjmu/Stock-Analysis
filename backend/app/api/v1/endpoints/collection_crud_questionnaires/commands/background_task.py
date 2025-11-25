"""Background task for AI questionnaire generation."""

import logging
from datetime import datetime, timezone
from typing import List
from uuid import UUID

from app.core.context import RequestContext
from app.models.collection_flow import CollectionFlow
from ..database_helpers import (
    update_questionnaire_status,
    load_assets_for_background,
    get_flow_db_id,
)

logger = logging.getLogger(__name__)


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
            from .._generate_per_section import _generate_questionnaires_per_section

            # CC FIX Issue #2: Pass flow_db_id (collection_flows.id PK) for gap analysis
            questionnaires = await _generate_questionnaires_per_section(
                flow_id, flow_db_id, existing_assets, context, db
            )

            # ✅ Fix Bug #22: Distinguish between "no gaps" (asset ready) vs "generation failed"
            # If _generate_questionnaires_per_section returned empty list, check if it's because
            # the IntelligentGapScanner found no TRUE gaps (asset already has complete data)
            # vs actual generation failure (API error, parsing error, etc.)

            if questionnaires:
                # ✅ Fix Bug #22: Check for "no gaps" marker (asset already ready for assessment)
                # This happens when IntelligentGapScanner finds no TRUE gaps - the asset has complete data
                if (
                    len(questionnaires) == 1
                    and isinstance(questionnaires[0], dict)
                    and questionnaires[0].get("_no_gaps_marker")
                ):
                    logger.info(
                        f"✅ No TRUE gaps found for flow {flow_id} - marking questionnaire as completed (asset ready)"
                    )
                    # Mark questionnaire as "completed" with empty questions (no collection needed)
                    await update_questionnaire_status(
                        questionnaire_id,
                        "completed",  # ✅ "completed" not "failed" - the asset is ready for assessment
                        [],  # Empty questions list - no questions needed
                        db=db,
                    )

                    # Progress flow to completed state (collection not needed, asset is ready)
                    flow_uuid = UUID(flow_id)
                    flow_result = await db.execute(
                        select(CollectionFlow).where(
                            (CollectionFlow.flow_id == flow_uuid)
                            | (CollectionFlow.id == flow_uuid)
                        )
                    )
                    current_flow = flow_result.scalar_one_or_none()

                    if current_flow:
                        # ✅ Bug #31 Fix: Set metadata flags for "no gaps" case too
                        updated_metadata = current_flow.flow_metadata or {}
                        updated_metadata["questionnaire_ready"] = True
                        updated_metadata["agent_questionnaire_id"] = str(
                            questionnaire_id
                        )
                        updated_metadata["questionnaire_generating"] = False
                        updated_metadata["no_gaps_detected"] = (
                            True  # Signal asset is complete
                        )
                        updated_metadata["generation_completed_at"] = datetime.now(
                            timezone.utc
                        ).isoformat()

                        await db.execute(
                            sql_update(CollectionFlow)
                            .where(CollectionFlow.id == current_flow.id)
                            .values(
                                current_phase="completed",  # Collection not needed
                                status="completed",
                                progress_percentage=100.0,
                                flow_metadata=updated_metadata,  # ✅ Bug #31: Set metadata
                                updated_at=datetime.now(timezone.utc),
                            )
                        )
                        await db.commit()
                        logger.info(
                            f"✅ Flow {flow_id} completed - assets already have complete data"
                        )
                    return  # Exit early - nothing more to do

                # Extract questions from ALL questionnaire sections (not just first one)
                # Bug fix: Previously took only questionnaires[0].questions, losing 83% of questions
                questions = []
                for section in questionnaires:
                    # CC FIX: section is a dict, not an object - use .get() not hasattr()
                    if isinstance(section, dict) and section.get("questions"):
                        # CC FIX: Propagate section category to each question for frontend grouping
                        # Section structure has category field (from aggregate_sections_from_redis)
                        # but individual questions need it for frontend formDataTransformation.ts
                        section_category = section.get("category") or section.get(
                            "section_id", ""
                        ).replace("section_", "")
                        for question in section["questions"]:
                            if isinstance(question, dict):
                                question["category"] = (
                                    question.get("category") or section_category
                                )
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
                    field_id = (
                        question.get("field_id")
                        if isinstance(question, dict)
                        else getattr(question, "field_id", None)
                    )
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
                # MFO Two-Table Pattern: Query by EITHER flow_id OR id (flexible lookup)
                flow_uuid = UUID(flow_id)
                flow_result = await db.execute(
                    select(CollectionFlow).where(
                        (CollectionFlow.flow_id == flow_uuid)
                        | (CollectionFlow.id == flow_uuid)
                    )
                )
                current_flow = flow_result.scalar_one_or_none()

                if current_flow and current_flow.current_phase in [
                    "initialized",
                    "gap_analysis",
                    "questionnaire_generation",  # Fix: Include this phase for proper transition
                ]:
                    # ✅ Bug #31 Fix: Update flow_metadata with questionnaire_ready flag
                    # The /questionnaires/status endpoint checks these flags to detect completion
                    updated_metadata = current_flow.flow_metadata or {}
                    updated_metadata["questionnaire_ready"] = True
                    updated_metadata["agent_questionnaire_id"] = str(questionnaire_id)
                    updated_metadata["questionnaire_generating"] = False
                    updated_metadata["generation_completed_at"] = datetime.now(
                        timezone.utc
                    ).isoformat()

                    await db.execute(
                        sql_update(CollectionFlow)
                        # MFO Two-Table Pattern: Update using PK (we have the flow object)
                        .where(CollectionFlow.id == current_flow.id).values(
                            current_phase="manual_collection",
                            status="paused",  # FIXED: Use valid enum value (awaiting user questionnaire input)
                            progress_percentage=50.0,  # Questionnaire generated = 50% progress
                            flow_metadata=updated_metadata,  # ✅ Bug #31: Set metadata flags
                            updated_at=datetime.now(timezone.utc),
                        )
                    )
                    await db.commit()
                    logger.info(
                        f"✅ Bug #31 Fix: Set questionnaire_ready=True for flow {flow_id}"
                    )
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
        # CC Security: Log full details to DEBUG only (not INFO/ERROR) to prevent sensitive data exposure
        logger.debug(
            f"Background generation failed for flow {flow_id}: {e}", exc_info=True
        )
        logger.debug(f"Exception type: {type(e).__name__}")
        logger.debug(f"Exception details: {str(e)}")

        # CC Security: Log generic error at ERROR level (no sensitive details)
        logger.error(
            f"Background generation failed for flow {flow_id} "
            f"(exception type: {type(e).__name__})"
        )

        try:
            # CC Security: Store generic error message in DB (no sensitive exception details)
            # Per Qodo Bot review: Raw exception strings may contain secrets, SQL, tokens, or paths
            error_msg = f"Questionnaire generation failed: {type(e).__name__}"
            async with AsyncSessionLocal() as db:
                await update_questionnaire_status(
                    questionnaire_id, "failed", error_message=error_msg, db=db
                )

                # Per ADR-035: Surface error to flow status (no silent failures)
                # Update flow status to show questionnaire generation failed
                # MFO Two-Table Pattern: Query by EITHER flow_id OR id (flexible lookup)
                flow_uuid = UUID(flow_id)
                flow_result = await db.execute(
                    select(CollectionFlow).where(
                        (CollectionFlow.flow_id == flow_uuid)
                        | (CollectionFlow.id == flow_uuid)
                    )
                )
                current_flow = flow_result.scalar_one_or_none()

                if current_flow:
                    await db.execute(
                        sql_update(CollectionFlow)
                        # MFO Two-Table Pattern: Update using PK (we have the flow object)
                        .where(CollectionFlow.id == current_flow.id).values(
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
