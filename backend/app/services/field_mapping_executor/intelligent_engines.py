"""
Intelligent Mapping Engines
AI-powered mapping engines using embeddings, pattern learning, and ML techniques.
"""

import logging
from typing import Dict, List, Optional, Tuple

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.agent_discovered_patterns import AgentDiscoveredPatterns
from app.services.embedding_service import EmbeddingService

from .mapping_utilities import FieldSimilarityCalculator, StandardFieldRegistry

logger = logging.getLogger(__name__)


class IntelligentMappingEngine:
    """AI-powered intelligent mapping engine using embeddings and pattern learning"""

    def __init__(
        self,
        db_session: Optional[AsyncSession] = None,
        context: Optional[RequestContext] = None,
    ):
        self.similarity_calculator = FieldSimilarityCalculator()
        self.field_registry = StandardFieldRegistry()
        self.embedding_service = EmbeddingService()
        self.db_session = db_session
        self.context = context
        self.logger = logger

    async def create_intelligent_mappings(
        self, source_fields: List[str], target_fields: List[str]
    ) -> Tuple[Dict[str, str], Dict[str, float]]:
        """
        Create intelligent field mappings using AI and pattern learning.

        Args:
            source_fields: List of source field names
            target_fields: List of target field names

        Returns:
            Tuple of (mappings dict, confidence scores dict)
        """
        mappings = {}
        confidence_scores = {}

        for source_field in source_fields:
            best_match = None
            best_confidence = 0.0

            # Try learned patterns first
            if self.db_session and self.context:
                learned_mapping = await self._get_learned_mapping(source_field)
                if learned_mapping and learned_mapping in target_fields:
                    best_match = learned_mapping
                    best_confidence = 0.9

            # If no learned mapping, use AI similarity
            if not best_match:
                for target_field in target_fields:
                    try:
                        similarity = (
                            await self.similarity_calculator.calculate_similarity(
                                source_field, target_field
                            )
                        )
                        if similarity > best_confidence and similarity > 0.6:
                            best_confidence = similarity
                            best_match = target_field
                    except Exception as e:
                        self.logger.error(f"Error calculating similarity: {e}")
                        continue

            # Fall back to standard field registry
            if not best_match or best_confidence < 0.7:
                standard_field = self.field_registry.get_standard_field(source_field)
                if standard_field and standard_field in target_fields:
                    best_match = standard_field
                    best_confidence = 0.8

            if best_match and best_confidence > 0.5:
                mappings[source_field] = best_match
                confidence_scores[source_field] = best_confidence

        return mappings, confidence_scores

    async def _get_learned_mapping(self, source_field: str) -> Optional[str]:
        """Get learned mapping from discovered patterns"""
        if not self.db_session or not self.context:
            return None

        try:
            use_python_filtering = False

            # Use JSON operators for better performance and safety
            try:
                # PostgreSQL JSONB operators - preferred method
                query = (
                    select(AgentDiscoveredPatterns)
                    .where(
                        and_(
                            AgentDiscoveredPatterns.pattern_type
                            == "field_mapping_approval",
                            AgentDiscoveredPatterns.client_account_id
                            == self.context.client_account_id,
                            AgentDiscoveredPatterns.engagement_id
                            == self.context.engagement_id,
                            AgentDiscoveredPatterns.pattern_data["source_field"].astext
                            == source_field,
                        )
                    )
                    .order_by(AgentDiscoveredPatterns.confidence_score.desc())
                )
            except Exception:
                # Fallback using proper JSON path operators
                self.logger.warning(
                    f"Falling back to JSON path query for source_field: {source_field}"
                )
                try:
                    # Try standard JSON path operators
                    query = (
                        select(AgentDiscoveredPatterns)
                        .where(
                            and_(
                                AgentDiscoveredPatterns.pattern_type
                                == "field_mapping_approval",
                                AgentDiscoveredPatterns.client_account_id
                                == self.context.client_account_id,
                                AgentDiscoveredPatterns.engagement_id
                                == self.context.engagement_id,
                                AgentDiscoveredPatterns.pattern_data[
                                    "source_field"
                                ].as_string()
                                == source_field,
                            )
                        )
                        .order_by(AgentDiscoveredPatterns.confidence_score.desc())
                    )
                except Exception:
                    # Final fallback - filter in Python to avoid SQL injection
                    self.logger.warning(
                        "Using Python filtering for pattern matching as database "
                        "JSON operators are not available"
                    )
                    use_python_filtering = True
                    query = (
                        select(AgentDiscoveredPatterns)
                        .where(
                            and_(
                                AgentDiscoveredPatterns.pattern_type
                                == "field_mapping_approval",
                                AgentDiscoveredPatterns.client_account_id
                                == self.context.client_account_id,
                                AgentDiscoveredPatterns.engagement_id
                                == self.context.engagement_id,
                            )
                        )
                        .order_by(AgentDiscoveredPatterns.confidence_score.desc())
                    )

            result = await self.db_session.execute(query)

            # Handle Python filtering if we used the final fallback query
            if use_python_filtering:
                patterns = result.scalars().all()
                for pattern in patterns:
                    if (
                        pattern.pattern_data
                        and isinstance(pattern.pattern_data, dict)
                        and pattern.pattern_data.get("source_field") == source_field
                    ):
                        return pattern.pattern_data.get("target_field")
                return None
            else:
                pattern = result.scalar_one_or_none()
                if pattern and pattern.pattern_data:
                    return pattern.pattern_data.get("target_field")

        except Exception as e:
            self.logger.error(f"Error retrieving learned mapping: {e}")

        return None

    async def suggest_mappings(
        self, source_fields: List[str], target_fields: List[str], threshold: float = 0.6
    ) -> Dict[str, List[Tuple[str, float]]]:
        """
        Suggest multiple mapping options for each source field.

        Args:
            source_fields: List of source field names
            target_fields: List of target field names
            threshold: Minimum confidence threshold

        Returns:
            Dict mapping source fields to list of (target_field, confidence) tuples
        """
        suggestions = {}

        for source_field in source_fields:
            field_suggestions = []

            # Calculate similarity to all target fields
            for target_field in target_fields:
                try:
                    similarity = await self.similarity_calculator.calculate_similarity(
                        source_field, target_field
                    )
                    if similarity >= threshold:
                        field_suggestions.append((target_field, similarity))
                except Exception as e:
                    self.logger.error(f"Error calculating similarity: {e}")
                    continue

            # Sort by confidence and take top suggestions
            field_suggestions.sort(key=lambda x: x[1], reverse=True)
            suggestions[source_field] = field_suggestions[:3]  # Top 3 suggestions

        return suggestions

    def get_mapping_confidence(self, source_field: str, target_field: str) -> float:
        """Get confidence score for a specific mapping"""
        # This would normally use the similarity calculator
        # For now, return a simple heuristic
        if self.field_registry.is_standard_field(source_field):
            return 0.8
        else:
            return 0.6
