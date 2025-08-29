"""
Bulk operations for field mapping learning.
Handles batch processing of learning actions.
"""

import logging
from typing import Optional

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.security.secure_logging import safe_log_format
from app.models.agent_discovered_patterns import AgentDiscoveredPatterns

from ..models.mapping_schemas import (
    BulkLearningRequest,
    BulkLearningResponse,
    LearnedPatternsResponse,
    LearnedPatternSummary,
    LearningApprovalRequest,
    LearningRejectionRequest,
    LearningResponse,
)

logger = logging.getLogger(__name__)


class BulkLearningOperations:
    """Handles bulk learning operations for field mapping patterns."""

    def __init__(self, db: AsyncSession, context: RequestContext, learning_service):
        self.db = db
        self.context = context
        self.client_account_id = context.client_account_id
        self.engagement_id = context.engagement_id
        self.learning_service = learning_service

    async def bulk_learn(self, request: BulkLearningRequest) -> BulkLearningResponse:
        """
        Learn from multiple mappings in a single transaction.

        Args:
            request: Bulk learning request with multiple actions

        Returns:
            BulkLearningResponse with results for each action
        """
        results = []
        total_patterns_created = 0
        total_patterns_updated = 0

        try:
            for action in request.actions:
                if action.action == "approve":
                    approval_req = LearningApprovalRequest(
                        confidence_adjustment=action.confidence_adjustment,
                        metadata=action.metadata,
                        learn_from_approval=True,
                        approval_note=f"Bulk approval: {action.mapping_id}",
                    )
                    result = await self.learning_service.learn_from_approval(
                        action.mapping_id, approval_req
                    )

                elif action.action == "reject":
                    rejection_req = LearningRejectionRequest(
                        rejection_reason=action.rejection_reason or "Bulk rejection",
                        alternative_suggestion=action.alternative_suggestion,
                        metadata=action.metadata,
                        learn_from_rejection=True,
                    )
                    result = await self.learning_service.learn_from_rejection(
                        action.mapping_id, rejection_req
                    )

                else:
                    result = LearningResponse(
                        mapping_id=action.mapping_id,
                        action=action.action,
                        success=False,
                        error_message=f"Invalid action: {action.action}",
                    )

                results.append(result)
                if result.success:
                    total_patterns_created += result.patterns_created
                    total_patterns_updated += result.patterns_updated

            successful_count = sum(1 for r in results if r.success)
            failed_count = len(results) - successful_count

            logger.info(
                safe_log_format(
                    "✅ Bulk learning completed: {successful}/{total} actions successful, "
                    "{patterns_created} patterns created, {patterns_updated} updated",
                    successful=successful_count,
                    total=len(results),
                    patterns_created=total_patterns_created,
                    patterns_updated=total_patterns_updated,
                )
            )

            return BulkLearningResponse(
                total_actions=len(results),
                successful_actions=successful_count,
                failed_actions=failed_count,
                results=results,
                global_patterns_created=total_patterns_created,
                global_patterns_updated=total_patterns_updated,
            )

        except Exception as e:
            logger.error(
                safe_log_format("❌ Error in bulk learning: {error}", error=str(e))
            )
            await self.db.rollback()
            raise

    async def get_learned_patterns(
        self,
        pattern_type: Optional[str] = None,
        insight_type: Optional[str] = None,
        limit: int = 100,
    ) -> LearnedPatternsResponse:
        """
        Get learned patterns for the current context.

        Args:
            pattern_type: Optional filter by pattern type
            insight_type: Optional filter by insight type
            limit: Maximum number of patterns to return

        Returns:
            LearnedPatternsResponse with matching patterns
        """
        try:
            query = (
                select(AgentDiscoveredPatterns)
                .where(
                    and_(
                        AgentDiscoveredPatterns.client_account_id
                        == self.client_account_id,
                        AgentDiscoveredPatterns.engagement_id == self.engagement_id,
                    )
                )
                .order_by(desc(AgentDiscoveredPatterns.created_at))
                .limit(limit)
            )

            if pattern_type:
                # Use raw SQL with enum casting for PostgreSQL comparison
                from sqlalchemy import text

                query = query.where(
                    text(f"pattern_type = '{pattern_type}'::patterntype")
                )

            if insight_type:
                query = query.where(
                    AgentDiscoveredPatterns.insight_type == insight_type
                )

            result = await self.db.execute(query)
            patterns = result.scalars().all()

            pattern_summaries = []
            for pattern in patterns:
                summary = LearnedPatternSummary(
                    pattern_id=str(pattern.id),
                    pattern_type=pattern.pattern_type,
                    pattern_name=pattern.pattern_name,
                    confidence_score=float(pattern.confidence_score),
                    evidence_count=pattern.evidence_count,
                    times_referenced=pattern.times_referenced,
                    effectiveness_score=(
                        float(pattern.pattern_effectiveness_score)
                        if pattern.pattern_effectiveness_score
                        else None
                    ),
                    insight_type=pattern.insight_type,
                    created_at=pattern.created_at,
                    last_used_at=pattern.last_used_at,
                )
                pattern_summaries.append(summary)

            return LearnedPatternsResponse(
                total_patterns=len(pattern_summaries),
                patterns=pattern_summaries,
                context_type="field_mapping",
                engagement_id=str(self.engagement_id),
            )

        except Exception as e:
            logger.error(
                safe_log_format(
                    "❌ Error retrieving learned patterns: {error}", error=str(e)
                )
            )
            raise
