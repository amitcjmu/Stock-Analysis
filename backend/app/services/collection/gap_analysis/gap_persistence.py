"""Gap persistence utilities."""

import logging
import math
from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset
from app.models.collection_data_gap import CollectionDataGap

logger = logging.getLogger(__name__)


async def persist_gaps(
    result_dict: Dict[str, Any],
    assets: List[Asset],
    db: AsyncSession,
    collection_flow_id: str,
) -> int:
    """Persist gaps to collection_data_gaps table.

    Args:
        result_dict: Parsed gap analysis result
        assets: List of analyzed assets (for logging)
        db: Database session
        collection_flow_id: Collection flow ID for FK reference

    Returns:
        Number of gaps persisted
    """
    gaps_by_priority = result_dict.get("gaps", {})
    gaps_persisted = 0
    gaps_failed = 0

    logger.debug(
        f"📥 Persisting gaps - Priority levels: {list(gaps_by_priority.keys())}"
    )

    for priority_level, gaps in gaps_by_priority.items():
        if not isinstance(gaps, list):
            logger.warning(
                f"⚠️ Skipping non-list gaps for priority '{priority_level}': {type(gaps)}"
            )
            continue

        priority_map = {"critical": 1, "high": 2, "medium": 3, "low": 4}
        priority_value = priority_map.get(priority_level, 3)

        logger.debug(
            f"📝 Processing {len(gaps)} {priority_level} gaps (priority={priority_value})"
        )

        for gap in gaps:
            try:
                # Extract asset_id from gap data (required NOT NULL column)
                asset_id_str = gap.get("asset_id")
                if not asset_id_str:
                    logger.warning(
                        f"⚠️ Skipping gap without asset_id - Field: {gap.get('field_name', 'unknown')}"
                    )
                    gaps_failed += 1
                    continue

                # Sanitize confidence_score (no NaN/Inf)
                confidence_score = gap.get("confidence_score")
                if confidence_score is not None and (
                    math.isnan(confidence_score) or math.isinf(confidence_score)
                ):
                    confidence_score = None

                # Build gap record dictionary for upsert
                gap_record = {
                    "collection_flow_id": UUID(collection_flow_id),
                    "asset_id": UUID(asset_id_str),
                    "gap_type": gap.get("gap_type", "missing_field"),
                    "gap_category": gap.get("gap_category", "unknown"),
                    "field_name": gap.get("field_name", "unknown"),
                    "description": gap.get("description", ""),
                    "impact_on_sixr": gap.get("impact_on_sixr", "medium"),
                    "priority": priority_value,
                    "suggested_resolution": gap.get(
                        "suggested_resolution",
                        "Manual collection required",
                    ),
                    "resolution_status": "pending",
                    "confidence_score": confidence_score,  # AI enhancement field
                    "ai_suggestions": gap.get("ai_suggestions"),  # AI enhancement field
                }

                # ✅ FIX Bug #1: Use PostgreSQL upsert with conflict resolution
                # CRITICAL: Include collection_flow_id in update set to handle gaps moving between flows
                # Constraint: uq_gaps_dedup (collection_flow_id, field_name, gap_type, asset_id)
                stmt = insert(CollectionDataGap).values(**gap_record)
                stmt = stmt.on_conflict_do_update(
                    constraint="uq_gaps_dedup",
                    set_={
                        "collection_flow_id": gap_record["collection_flow_id"],  # Allow gaps to move between flows
                        "priority": gap_record["priority"],
                        "suggested_resolution": gap_record["suggested_resolution"],
                        "description": gap_record["description"],
                        "impact_on_sixr": gap_record["impact_on_sixr"],
                        "confidence_score": gap_record[
                            "confidence_score"
                        ],  # AI enhancement
                        "ai_suggestions": gap_record[
                            "ai_suggestions"
                        ],  # AI enhancement
                        "updated_at": func.now(),
                    },
                )
                await db.execute(stmt)
                gaps_persisted += 1

            except Exception as e:
                gaps_failed += 1
                logger.error(
                    f"❌ Failed to persist gap - Field: {gap.get('field_name', 'unknown')}, "
                    f"Asset: {gap.get('asset_id', 'unknown')}, Error: {e}"
                )
                continue

    await db.commit()
    logger.info(
        f"💾 Persisted {gaps_persisted} gaps to database "
        f"(failed: {gaps_failed}, flow: {collection_flow_id})"
    )

    return gaps_persisted


async def persist_ai_questionnaires(
    result_dict: Dict[str, Any],
    collection_flow_id: str,
    db: AsyncSession,
) -> int:
    """Persist AI-generated questionnaires to adaptive_questionnaires table.

    Args:
        result_dict: AI analysis result containing questionnaire sections
        collection_flow_id: Collection flow UUID
        db: Database session

    Returns:
        Number of questionnaire sections persisted (usually 1 combined questionnaire)
    """
    from datetime import datetime, timezone

    from app.models.collection_flow.adaptive_questionnaire_model import (
        AdaptiveQuestionnaire,
    )
    from app.models.collection_flow.collection_flow_model import CollectionFlow
    from sqlalchemy import select

    questionnaire_data = result_dict.get("questionnaire", {})
    sections = questionnaire_data.get("sections", [])

    if not sections:
        logger.warning("No questionnaire sections to persist")
        return 0

    # Flatten all questions from all sections
    all_questions = []
    for section in sections:
        questions = section.get("questions", [])
        all_questions.extend(questions)

    if not all_questions:
        logger.warning("No questions found in questionnaire sections")
        return 0

    # Get client_account_id and engagement_id from collection_flow
    stmt = select(CollectionFlow).where(CollectionFlow.id == UUID(collection_flow_id))
    result = await db.execute(stmt)
    collection_flow = result.scalar_one_or_none()

    if not collection_flow:
        logger.error(
            f"Collection flow {collection_flow_id} not found - cannot persist questionnaires"
        )
        return 0

    # CRITICAL FIX: Build target_gaps from result_dict gaps
    # This populates the field that frontend polls to show questionnaires
    target_gaps = []
    gaps_by_priority = result_dict.get("gaps", {})

    # Per Qodo Bot: Map string priorities to numeric (1=highest, 4=lowest)
    priority_map = {"critical": 1, "high": 2, "medium": 3, "low": 4}

    for priority_level, gaps in gaps_by_priority.items():
        if isinstance(gaps, list):
            for gap in gaps:
                # Convert priority to numeric for type consistency
                if isinstance(priority_level, str):
                    numeric_priority = priority_map.get(priority_level.lower(), 3)
                elif isinstance(priority_level, int):
                    numeric_priority = priority_level
                else:
                    numeric_priority = 3  # Default to medium

                target_gaps.append(
                    {
                        "field_name": gap.get("field_name"),
                        "gap_type": gap.get("gap_type", "missing_field"),
                        "gap_category": gap.get("gap_category", "unknown"),
                        "asset_id": gap.get("asset_id"),
                        "priority": numeric_priority,
                        "impact_on_sixr": gap.get("impact_on_sixr", "medium"),
                    }
                )

    # Create AdaptiveQuestionnaire record
    questionnaire = AdaptiveQuestionnaire(
        client_account_id=collection_flow.client_account_id,
        engagement_id=collection_flow.engagement_id,
        collection_flow_id=UUID(collection_flow_id),
        title="AI-Generated Data Gap Collection Questionnaire",
        description=f"Generated by AI from comprehensive gap analysis ({len(all_questions)} questions)",
        template_name="ai_gap_based_questionnaire",
        template_type="detailed",
        version="1.0",
        applicable_tiers=["tier_2"],  # Only AI tier generates these
        questions=all_questions,
        question_count=len(all_questions),
        target_gaps=target_gaps,  # CRITICAL FIX: Populate target_gaps from AI analysis result
        validation_rules={},
        scoring_rules={},
        completion_status="pending",
        responses_collected={},
        is_active=True,
        is_template=False,
        created_at=datetime.now(timezone.utc),
    )

    db.add(questionnaire)
    await db.commit()
    await db.refresh(questionnaire)

    logger.info(
        f"✅ Persisted AI questionnaire {questionnaire.id} with {len(all_questions)} questions "
        f"from {len(sections)} sections"
    )

    return (
        1  # Return count of questionnaires persisted (always 1 combined questionnaire)
    )
