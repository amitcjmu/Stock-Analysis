"""
Pattern management operations for field mapping learning.
Handles creation, retrieval, and updates of learned patterns.
"""

import logging
from datetime import datetime
from typing import Optional, Tuple

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.agent_discovered_patterns import AgentDiscoveredPatterns

# from app.models.agent_memory import PatternType  # No longer needed - using string literals
from app.models.data_import.mapping import ImportFieldMapping

from ..models.mapping_schemas import (
    LearningApprovalRequest,
    LearningRejectionRequest,
)

logger = logging.getLogger(__name__)


class PatternManager:
    """Manages pattern creation, updates, and retrieval for field mapping learning."""

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        self.client_account_id = context.client_account_id
        self.engagement_id = context.engagement_id

    async def create_approval_pattern(
        self, mapping: ImportFieldMapping, approval_request: LearningApprovalRequest
    ) -> Tuple[int, int]:
        """Create or update patterns based on mapping approval."""
        patterns_created = 0
        patterns_updated = 0

        # Create positive field mapping pattern
        pattern_id = (
            f"field_mapping_positive_{mapping.source_field}_{mapping.target_field}"
        )

        existing_pattern = await self._get_existing_pattern(pattern_id)
        if existing_pattern:
            # Update existing pattern with new evidence
            existing_pattern.add_evidence(
                {
                    "mapping_id": str(mapping.id),
                    "source_field": mapping.source_field,
                    "target_field": mapping.target_field,
                    "confidence_score": mapping.confidence_score,
                    "approval_metadata": approval_request.metadata,
                }
            )
            existing_pattern.increment_reference_count()
            patterns_updated += 1
        else:
            # Create new positive pattern
            # CC FIX: Must use UPPERCASE to match PostgreSQL enum patterntype
            pattern_type_value = "FIELD_MAPPING_APPROVAL"
            logger.debug(f"Creating pattern with type: {pattern_type_value}")
            logger.info(
                f"DEBUG: pattern_type_value = {pattern_type_value!r}, type = {type(pattern_type_value)}"
            )
            new_pattern = AgentDiscoveredPatterns(
                pattern_id=pattern_id,
                pattern_type=pattern_type_value,
                pattern_name=f"Approved mapping: {mapping.source_field} → {mapping.target_field}",
                pattern_description=(
                    f"User approved the mapping from '{mapping.source_field}' "
                    f"to '{mapping.target_field}'"
                ),
                discovered_by_agent="field_mapping_learning_service",
                confidence_score=approval_request.confidence_adjustment
                or mapping.confidence_score
                or 0.8,
                evidence_count=1,
                pattern_data={
                    "source_field": mapping.source_field,
                    "target_field": mapping.target_field,
                    "original_confidence": mapping.confidence_score,
                    "adjusted_confidence": approval_request.confidence_adjustment,
                    "approval_metadata": approval_request.metadata,
                    "match_type": mapping.match_type,
                },
                execution_context={
                    "import_id": str(mapping.data_import_id),
                    "approval_note": approval_request.approval_note,
                    "learned_at": datetime.utcnow().isoformat(),
                },
                client_account_id=self.client_account_id,
                engagement_id=self.engagement_id,
            )
            new_pattern.set_insight_type("field_mapping_suggestion")
            logger.info(
                f"DEBUG BEFORE ADD: new_pattern.pattern_type = {new_pattern.pattern_type!r}"
            )
            self.db.add(new_pattern)
            logger.info(
                f"DEBUG AFTER ADD: new_pattern.pattern_type = {new_pattern.pattern_type!r}"
            )
            patterns_created += 1

        return patterns_created, patterns_updated

    async def create_rejection_pattern(
        self, mapping: ImportFieldMapping, rejection_request: LearningRejectionRequest
    ) -> Tuple[int, int]:
        """Create or update patterns based on mapping rejection."""
        patterns_created = 0
        patterns_updated = 0

        # Create negative field mapping pattern
        pattern_id = (
            f"field_mapping_negative_{mapping.source_field}_{mapping.target_field}"
        )

        existing_pattern = await self._get_existing_pattern(pattern_id)
        if existing_pattern:
            # Update existing pattern with new evidence
            existing_pattern.add_evidence(
                {
                    "mapping_id": str(mapping.id),
                    "source_field": mapping.source_field,
                    "target_field": mapping.target_field,
                    "rejection_reason": rejection_request.rejection_reason,
                    "alternative_suggestion": rejection_request.alternative_suggestion,
                    "rejection_metadata": rejection_request.metadata,
                }
            )
            existing_pattern.increment_reference_count()
            patterns_updated += 1
        else:
            # Create new negative pattern
            # CC FIX: Must use UPPERCASE to match PostgreSQL enum patterntype
            new_pattern = AgentDiscoveredPatterns(
                pattern_id=pattern_id,
                pattern_type="FIELD_MAPPING_REJECTION",
                pattern_name=f"Rejected mapping: {mapping.source_field} → {mapping.target_field}",
                pattern_description=(
                    f"User rejected the mapping from '{mapping.source_field}' "
                    f"to '{mapping.target_field}': {rejection_request.rejection_reason}"
                ),
                discovered_by_agent="field_mapping_learning_service",
                confidence_score=0.1,  # Low confidence for rejected mappings
                evidence_count=1,
                pattern_data={
                    "source_field": mapping.source_field,
                    "target_field": mapping.target_field,
                    "rejection_reason": rejection_request.rejection_reason,
                    "alternative_suggestion": rejection_request.alternative_suggestion,
                    "original_confidence": mapping.confidence_score,
                    "rejection_metadata": rejection_request.metadata,
                    "match_type": mapping.match_type,
                },
                execution_context={
                    "import_id": str(mapping.data_import_id),
                    "learned_at": datetime.utcnow().isoformat(),
                },
                client_account_id=self.client_account_id,
                engagement_id=self.engagement_id,
            )
            new_pattern.set_insight_type("field_mapping_suggestion")
            self.db.add(new_pattern)
            patterns_created += 1

        # Create positive pattern for alternative suggestion if provided
        if rejection_request.alternative_suggestion:
            alt_pattern_id = (
                f"field_mapping_alternative_{mapping.source_field}_"
                f"{rejection_request.alternative_suggestion}"
            )

            existing_alt_pattern = await self._get_existing_pattern(alt_pattern_id)
            if existing_alt_pattern:
                existing_alt_pattern.add_evidence(
                    {
                        "original_mapping_id": str(mapping.id),
                        "source_field": mapping.source_field,
                        "suggested_target": rejection_request.alternative_suggestion,
                        "rejection_reason": rejection_request.rejection_reason,
                    }
                )
                existing_alt_pattern.increment_reference_count()
                patterns_updated += 1
            else:
                # CC FIX: Must use UPPERCASE to match PostgreSQL enum patterntype
                alt_pattern = AgentDiscoveredPatterns(
                    pattern_id=alt_pattern_id,
                    pattern_type="FIELD_MAPPING_SUGGESTION",
                    pattern_name=(
                        f"Alternative mapping: {mapping.source_field} → "
                        f"{rejection_request.alternative_suggestion}"
                    ),
                    pattern_description=(
                        f"User suggested mapping '{mapping.source_field}' "
                        f"to '{rejection_request.alternative_suggestion}' instead"
                    ),
                    discovered_by_agent="field_mapping_learning_service",
                    confidence_score=0.9,  # High confidence for user suggestions
                    evidence_count=1,
                    pattern_data={
                        "source_field": mapping.source_field,
                        "suggested_target": rejection_request.alternative_suggestion,
                        "original_target": mapping.target_field,
                        "rejection_reason": rejection_request.rejection_reason,
                        "rejection_metadata": rejection_request.metadata,
                    },
                    execution_context={
                        "original_import_id": str(mapping.data_import_id),
                        "learned_at": datetime.utcnow().isoformat(),
                    },
                    client_account_id=self.client_account_id,
                    engagement_id=self.engagement_id,
                )
                alt_pattern.set_insight_type("field_mapping_suggestion")
                self.db.add(alt_pattern)
                patterns_created += 1

        return patterns_created, patterns_updated

    async def _get_existing_pattern(
        self, pattern_id: str
    ) -> Optional[AgentDiscoveredPatterns]:
        """Get existing pattern by pattern_id with proper tenant security."""
        query = select(AgentDiscoveredPatterns).where(
            and_(
                AgentDiscoveredPatterns.pattern_id == pattern_id,
                AgentDiscoveredPatterns.client_account_id == self.client_account_id,
                AgentDiscoveredPatterns.engagement_id == self.engagement_id,
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
