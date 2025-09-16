"""
Field mapping learning service for pattern storage and retrieval.
Integrates with AgentDiscoveredPatterns to enable continuous improvement.
"""

import logging
import uuid
from typing import Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.security.secure_logging import safe_log_format
from app.models.data_import.mapping import ImportFieldMapping

from ..models.mapping_schemas import (
    BulkLearningRequest,
    BulkLearningResponse,
    LearnedPatternsResponse,
    LearningApprovalRequest,
    LearningRejectionRequest,
    LearningResponse,
)
from .bulk_operations import BulkLearningOperations
from .pattern_manager import PatternManager

logger = logging.getLogger(__name__)


class FieldMappingLearningService:
    """Service for learning from field mapping approvals and rejections."""

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        self.client_account_id = context.client_account_id
        self.engagement_id = context.engagement_id
        self.pattern_manager = PatternManager(db, context)
        self.bulk_operations = BulkLearningOperations(db, context, self)

    async def learn_from_approval(
        self, mapping_id: str, approval_request: LearningApprovalRequest
    ) -> LearningResponse:
        """
        Learn from a field mapping approval to improve future suggestions.

        Args:
            mapping_id: ID of the approved mapping
            approval_request: Approval details and learning parameters

        Returns:
            LearningResponse with operation results
        """
        try:
            # Get the mapping with tenant security
            mapping = await self._get_mapping_by_id(mapping_id)
            if not mapping:
                return LearningResponse(
                    mapping_id=mapping_id,
                    action="approval",
                    success=False,
                    error_message="Mapping not found or access denied",
                )

            # Update mapping status if learn_from_approval is enabled
            if approval_request.learn_from_approval:
                await self._update_mapping_status(mapping, "approved")

            # Create learning patterns
            patterns_created, patterns_updated = (
                await self.pattern_manager.create_approval_pattern(
                    mapping, approval_request
                )
            )

            # Commit the transaction
            await self.db.commit()

            logger.info(
                safe_log_format(
                    "✅ Learning from approval successful: mapping {mapping_id}, "
                    "{patterns_created} patterns created, {patterns_updated} updated",
                    mapping_id=mapping_id,
                    patterns_created=patterns_created,
                    patterns_updated=patterns_updated,
                )
            )

            return LearningResponse(
                mapping_id=mapping_id,
                action="approval",
                success=True,
                message="Learning from approval completed successfully",
                patterns_created=patterns_created,
                patterns_updated=patterns_updated,
            )

        except Exception as e:
            await self.db.rollback()
            logger.error(
                safe_log_format(
                    "❌ Error learning from approval: {error}", error=str(e)
                )
            )
            return LearningResponse(
                mapping_id=mapping_id,
                action="approval",
                success=False,
                error_message=f"Failed to learn from approval: {str(e)}",
            )

    async def learn_from_rejection(
        self, mapping_id: str, rejection_request: LearningRejectionRequest
    ) -> LearningResponse:
        """
        Learn from a field mapping rejection to improve future suggestions.

        Args:
            mapping_id: ID of the rejected mapping
            rejection_request: Rejection details and learning parameters

        Returns:
            LearningResponse with operation results
        """
        try:
            # Get the mapping with tenant security
            mapping = await self._get_mapping_by_id(mapping_id)
            if not mapping:
                return LearningResponse(
                    mapping_id=mapping_id,
                    action="rejection",
                    success=False,
                    error_message="Mapping not found or access denied",
                )

            # Update mapping status if learn_from_rejection is enabled
            if rejection_request.learn_from_rejection:
                await self._update_mapping_status(mapping, "rejected")

            # Create learning patterns
            patterns_created, patterns_updated = (
                await self.pattern_manager.create_rejection_pattern(
                    mapping, rejection_request
                )
            )

            # Commit the transaction
            await self.db.commit()

            logger.info(
                safe_log_format(
                    "✅ Learning from rejection successful: mapping {mapping_id}, "
                    "{patterns_created} patterns created, {patterns_updated} updated",
                    mapping_id=mapping_id,
                    patterns_created=patterns_created,
                    patterns_updated=patterns_updated,
                )
            )

            return LearningResponse(
                mapping_id=mapping_id,
                action="rejection",
                success=True,
                message="Learning from rejection completed successfully",
                patterns_created=patterns_created,
                patterns_updated=patterns_updated,
            )

        except Exception as e:
            await self.db.rollback()
            logger.error(
                safe_log_format(
                    "❌ Error learning from rejection: {error}", error=str(e)
                )
            )
            return LearningResponse(
                mapping_id=mapping_id,
                action="rejection",
                success=False,
                error_message=f"Failed to learn from rejection: {str(e)}",
            )

    async def bulk_learn(self, request: BulkLearningRequest) -> BulkLearningResponse:
        """Delegate bulk learning to the bulk operations module."""
        return await self.bulk_operations.bulk_learn(request)

    async def get_learned_patterns(
        self,
        pattern_type: Optional[str] = None,
        insight_type: Optional[str] = None,
        limit: int = 100,
    ) -> LearnedPatternsResponse:
        """Delegate pattern retrieval to the bulk operations module."""
        return await self.bulk_operations.get_learned_patterns(
            pattern_type, insight_type, limit
        )

    async def _get_mapping_by_id(self, mapping_id: str) -> Optional[ImportFieldMapping]:
        """Get mapping by ID with proper tenant security."""
        try:
            mapping_uuid = uuid.UUID(mapping_id)
            query = select(ImportFieldMapping).where(
                and_(
                    ImportFieldMapping.id == mapping_uuid,
                    ImportFieldMapping.client_account_id == self.client_account_id,
                )
            )
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except ValueError:
            logger.warning(f"Invalid UUID format for mapping_id: {mapping_id}")
            return None

    async def _update_mapping_status(self, mapping: ImportFieldMapping, status: str):
        """Update mapping status and commit to database."""
        from datetime import datetime

        mapping.status = status

        # If approving, also set approval metadata
        if status == "approved":
            mapping.approved_by = (
                str(self.context.user_id) if self.context.user_id else "system"
            )
            mapping.approved_at = datetime.utcnow()

        await self.db.flush()
