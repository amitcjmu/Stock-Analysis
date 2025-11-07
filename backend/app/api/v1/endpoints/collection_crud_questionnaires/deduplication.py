"""
Questionnaire Deduplication Logic
Implements get_or_create pattern for asset-based questionnaire reuse across flows.
"""

import logging
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.collection_flow import AdaptiveQuestionnaire

logger = logging.getLogger(__name__)


async def get_existing_questionnaire_for_asset(
    engagement_id: UUID,
    asset_id: UUID,
    db: AsyncSession,
) -> Optional[AdaptiveQuestionnaire]:
    """Check if questionnaire already exists for this asset in this engagement.

    Args:
        engagement_id: Current engagement ID (tenant scope)
        asset_id: Asset ID to check
        db: Database session

    Returns:
        Existing AdaptiveQuestionnaire if found, None otherwise

    Note:
        Only returns questionnaires that are NOT failed.
        Failed questionnaires are treated as non-existent (retry generation).
    """
    try:
        result = await db.execute(
            select(AdaptiveQuestionnaire).where(
                AdaptiveQuestionnaire.engagement_id == engagement_id,
                AdaptiveQuestionnaire.asset_id == asset_id,
                AdaptiveQuestionnaire.completion_status != "failed",
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Note: IDs logged for debugging only - ensure production logs are scrubbed
            logger.info(
                f"♻️ Found existing questionnaire {str(existing.id)[:8]}... for asset {str(asset_id)[:8]}... "
                f"(status: {existing.completion_status})"
            )
            return existing

        logger.info(
            f"🆕 No existing questionnaire found for asset {str(asset_id)[:8]}..."
        )
        return None

    except Exception as e:
        logger.error(
            f"Error checking for existing questionnaire (asset {asset_id}): {e}",
            exc_info=True,
        )
        return None


async def should_reuse_questionnaire(
    questionnaire: AdaptiveQuestionnaire,
) -> tuple[bool, str]:
    """Determine if existing questionnaire should be reused or regenerated.

    Args:
        questionnaire: Existing questionnaire to evaluate

    Returns:
        Tuple of (should_reuse: bool, reason: str)

    Decision Matrix:
        - completed: REUSE (user already answered, don't make them re-enter)
        - in_progress: REUSE (let user continue where they left off)
        - pending: REUSE (generation in progress, don't duplicate)
        - ready: REUSE (generated but not yet answered)
        - failed: REGENERATE (treated as non-existent by caller)
    """
    status = questionnaire.completion_status

    if status == "completed":
        return True, "Questionnaire already completed - reusing existing responses"

    if status == "in_progress":
        return (
            True,
            "Questionnaire in progress - allowing user to continue from where they left off",
        )

    if status == "pending":
        return True, "Questionnaire generation in progress - reusing pending record"

    if status == "ready":
        return (
            True,
            "Questionnaire ready but not yet answered - reusing generated questions",
        )

    # Should never reach here (failed filtered out by caller)
    return False, f"Unexpected status: {status}"


def log_questionnaire_reuse(
    questionnaire: AdaptiveQuestionnaire,
    flow_id: UUID,
    asset_id: UUID,
) -> None:
    """Log questionnaire reuse for audit trail.

    Args:
        questionnaire: Questionnaire being reused
        flow_id: New collection flow ID using this questionnaire
        asset_id: Asset ID
    """
    logger.info(
        f"📋 Reusing questionnaire {questionnaire.id} for flow {flow_id}:\n"
        f"   Asset: {asset_id}\n"
        f"   Status: {questionnaire.completion_status}\n"
        f"   Question Count: {questionnaire.question_count}\n"
        f"   Original Flow: {questionnaire.collection_flow_id}\n"
        f"   Created: {questionnaire.created_at}\n"
        f"   ✅ User will NOT have to re-answer questions"
    )


def log_questionnaire_creation(
    asset_id: UUID,
    flow_id: UUID,
    reason: str,
) -> None:
    """Log new questionnaire creation.

    Args:
        asset_id: Asset ID
        flow_id: Collection flow ID
        reason: Why new questionnaire is being created
    """
    logger.info(
        f"🆕 Creating NEW questionnaire for flow {flow_id}:\n"
        f"   Asset: {asset_id}\n"
        f"   Reason: {reason}"
    )
