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
