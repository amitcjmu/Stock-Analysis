"""
Database helper functions for collection questionnaires.
Extracted from commands.py for modularization (400-line limit compliance).
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, select

from app.core.context import RequestContext
from app.models.asset import Asset
from app.models.collection_flow import CollectionFlow, AdaptiveQuestionnaire

logger = logging.getLogger(__name__)


async def update_questionnaire_status(
    questionnaire_id: UUID,
    status: str,
    questions: Optional[List[dict]] = None,
    error_message: Optional[str] = None,
    db: Optional[AsyncSession] = None,
    commit: bool = True,  # Qodo Bot feedback: Allow skipping commit for atomic transactions
) -> None:
    """Update questionnaire status and optionally add questions.

    Args:
        questionnaire_id: UUID of the questionnaire to update
        status: New status (e.g., 'completed', 'ready', 'failed')
        questions: Optional list of generated questions
        error_message: Optional error message for failed status
        db: Optional database session (creates new if not provided)
        commit: Whether to commit the transaction (default True).
                Set to False when caller manages the transaction atomically.
    """
    from app.core.database import AsyncSessionLocal

    # Use provided db session or create new one
    if db is None:
        async with AsyncSessionLocal() as session:
            await _do_update_questionnaire_status(
                session, questionnaire_id, status, questions, error_message, commit=True
            )
    else:
        await _do_update_questionnaire_status(
            db, questionnaire_id, status, questions, error_message, commit=commit
        )


async def _do_update_questionnaire_status(
    db: AsyncSession,
    questionnaire_id: UUID,
    status: str,
    questions: Optional[List[dict]] = None,
    error_message: Optional[str] = None,
    commit: bool = True,
) -> None:
    """Internal helper to update questionnaire status."""
    try:
        update_data = {
            "completion_status": status,
            "updated_at": datetime.now(timezone.utc),
        }

        if questions:
            update_data["questions"] = questions
            update_data["question_count"] = len(questions)
            update_data["description"] = (
                f"AI-Generated questionnaire with {len(questions)} "
                "targeted questions"
            )

        if error_message:
            update_data["description"] = f"Generation failed: {error_message}"

        await db.execute(
            update(AdaptiveQuestionnaire)
            .where(AdaptiveQuestionnaire.id == questionnaire_id)
            .values(**update_data)
        )
        # Qodo Bot feedback: Only commit if requested (for atomic transaction support)
        if commit:
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


async def load_assets_for_background(
    db: AsyncSession,
    context: RequestContext,
    flow_id: str,
    asset_ids: List[str],
) -> List[Asset]:
    """Reload assets inside the background session to avoid detached objects."""
    if not asset_ids:
        return []

    try:
        asset_uuid_list = [UUID(str(aid)) for aid in asset_ids]
    except Exception as exc:
        logger.error(
            "Failed to parse asset IDs for background questionnaire generation: %s",
            exc,
        )
        return []

    client_uuid = (
        UUID(str(context.client_account_id))
        if isinstance(context.client_account_id, str)
        else context.client_account_id
    )
    engagement_uuid = (
        UUID(str(context.engagement_id))
        if isinstance(context.engagement_id, str)
        else context.engagement_id
    )

    assets_result = await db.execute(
        select(Asset).where(
            Asset.client_account_id == client_uuid,
            Asset.engagement_id == engagement_uuid,
            Asset.id.in_(asset_uuid_list),
        )
    )
    assets = list(assets_result.scalars().all())

    logger.info(
        "Reloaded %d assets for background questionnaire in flow %s",
        len(assets),
        flow_id,
    )
    return assets


async def get_flow_db_id(db: AsyncSession, flow_id: str) -> Optional[UUID]:
    """
    Retrieve collection flow database ID from flow_id.
    Returns None if flow not found.
    """
    flow_uuid = UUID(flow_id) if isinstance(flow_id, str) else flow_id
    flow_result = await db.execute(
        select(CollectionFlow).where(CollectionFlow.flow_id == flow_uuid)
    )
    flow = flow_result.scalar_one_or_none()
    return flow.id if flow else None
