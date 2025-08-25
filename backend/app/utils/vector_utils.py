"""
Vector Utilities for pgvector Operations

Provides utility functions for storing and querying vector embeddings
using pgvector for pattern storage and similarity search.
"""

import logging
import uuid
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import text

from app.core.database import AsyncSessionLocal
from app.models.agent_discovered_patterns import AgentDiscoveredPatterns
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class VectorUtils:
    """Utility class for vector operations with pgvector."""

    def __init__(self):
        self.embedding_service = EmbeddingService()
        logger.info("VectorUtils initialized with AgentDiscoveredPatterns model")

    async def store_pattern_embedding(
        self,
        pattern_text: str,
        pattern_type: str,
        pattern_name: str,
        client_account_id: str,
        engagement_id: Optional[str] = None,
        pattern_context: Optional[Dict[str, Any]] = None,
        confidence_score: float = 0.5,
    ) -> str:
        """
        Store a pattern with its embedding.

        Args:
            pattern_text: Text to generate embedding for
            pattern_type: Type of pattern (e.g., 'field_mapping', 'asset_classification')
            pattern_name: Human-readable name of the pattern
            client_account_id: Client account ID for multi-tenancy
            engagement_id: Optional engagement ID
            pattern_context: Additional context about the pattern
            confidence_score: Initial confidence score

        Returns:
            Pattern ID (UUID as string)
        """
        try:
            # Generate embedding for the pattern text
            embedding = await self.embedding_service.embed_text(pattern_text)

            # Ensure embedding is 1536 dimensions for pgvector
            if len(embedding) < 1536:
                embedding.extend([0.0] * (1536 - len(embedding)))
            elif len(embedding) > 1536:
                embedding = embedding[:1536]

            async with AsyncSessionLocal() as session:
                # Create new pattern
                pattern = AgentDiscoveredPatterns(
                    pattern_id=str(uuid.uuid4()),
                    pattern_type=pattern_type,
                    pattern_name=pattern_name,
                    pattern_description=pattern_text,
                    discovered_by_agent="field_mapping_engine",
                    confidence_score=confidence_score,
                    evidence_count=1,
                    embedding=embedding,
                    pattern_metadata=pattern_context or {},
                    client_account_id=client_account_id,
                    engagement_id=engagement_id,
                    is_active=True,
                    is_validated=False,
                )

                session.add(pattern)
                await session.commit()
                await session.refresh(pattern)

                logger.info(
                    f"Stored pattern embedding: {pattern_name} (ID: {pattern.id})"
                )
                return str(pattern.id)

        except Exception as e:
            logger.error(f"Error storing pattern embedding: {e}")
            raise

    async def find_similar_patterns(
        self,
        query_embedding: List[float],
        client_account_id: str,
        pattern_type: Optional[str] = None,
        limit: int = 5,
        similarity_threshold: float = 0.7,
    ) -> List[Tuple[Any, float]]:
        """
        Find similar patterns using vector similarity search.

        Args:
            query_embedding: Query vector to search for
            client_account_id: Client account ID for scoping
            pattern_type: Optional filter by pattern type
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score

        Returns:
            List of (pattern, similarity_score) tuples
        """
        try:
            # Ensure embedding is 1536 dimensions
            if len(query_embedding) < 1536:
                query_embedding.extend([0.0] * (1536 - len(query_embedding)))
            elif len(query_embedding) > 1536:
                query_embedding = query_embedding[:1536]

            async with AsyncSessionLocal() as session:
                # Build the query with optional pattern type filter
                type_filter = ""
                if pattern_type:
                    type_filter = "AND pattern_type = :pattern_type"

                # Use pgvector cosine similarity search
                query = text(
                    f"""
                    SELECT
                        id,
                        pattern_id,
                        pattern_type,
                        pattern_name,
                        pattern_description,
                        discovered_by_agent,
                        confidence_score,
                        evidence_count,
                        times_referenced,
                        pattern_effectiveness_score,
                        pattern_metadata,
                        is_active,
                        is_validated,
                        created_at,
                        updated_at,
                        (embedding <=> :embedding::vector) as similarity_distance
                    FROM migration.agent_discovered_patterns
                    WHERE client_account_id = :client_account_id
                    {type_filter}
                    AND is_active = true
                    AND (embedding <=> :embedding::vector) < :distance_threshold
                    ORDER BY embedding <=> :embedding::vector
                    LIMIT :limit
                """
                )

                # Convert similarity threshold to distance threshold
                distance_threshold = 1.0 - similarity_threshold

                # Convert embedding to string format for pgvector
                embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"

                # Build parameters
                params = {
                    "embedding": embedding_str,
                    "client_account_id": client_account_id,
                    "distance_threshold": distance_threshold,
                    "limit": limit,
                }
                if pattern_type:
                    params["pattern_type"] = pattern_type

                result = await session.execute(query, params)

                patterns_with_similarity = []
                for row in result.fetchall():
                    # Convert distance back to similarity
                    similarity = 1.0 - row.similarity_distance

                    # Create pattern object from row data
                    pattern = {
                        "id": str(row.id),
                        "pattern_id": row.pattern_id,
                        "pattern_type": row.pattern_type,
                        "pattern_name": row.pattern_name,
                        "pattern_description": row.pattern_description,
                        "discovered_by_agent": row.discovered_by_agent,
                        "confidence_score": float(row.confidence_score),
                        "evidence_count": row.evidence_count,
                        "times_referenced": row.times_referenced,
                        "pattern_effectiveness_score": (
                            float(row.pattern_effectiveness_score)
                            if row.pattern_effectiveness_score
                            else None
                        ),
                        "pattern_metadata": row.pattern_metadata,
                        "is_active": row.is_active,
                        "is_validated": row.is_validated,
                        "created_at": row.created_at,
                        "updated_at": row.updated_at,
                    }

                    patterns_with_similarity.append((pattern, similarity))

                logger.debug(f"Found {len(patterns_with_similarity)} similar patterns")
                return patterns_with_similarity

        except Exception as e:
            logger.error(f"Error finding similar patterns: {e}")
            return []

    async def search_patterns_by_text(
        self,
        search_text: str,
        client_account_id: str,
        pattern_type: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Search patterns by text content.

        Args:
            search_text: Text to search for
            client_account_id: Client account ID for scoping
            pattern_type: Optional filter by pattern type
            limit: Maximum number of results

        Returns:
            List of pattern dictionaries
        """
        try:
            # Generate embedding for search text
            query_embedding = await self.embedding_service.embed_text(search_text)

            # Find similar patterns using vector search
            patterns_with_scores = await self.find_similar_patterns(
                query_embedding=query_embedding,
                client_account_id=client_account_id,
                pattern_type=pattern_type,
                limit=limit,
                similarity_threshold=0.5,  # Lower threshold for text search
            )

            # Extract just the patterns
            patterns = [pattern for pattern, _ in patterns_with_scores]
            return patterns

        except Exception as e:
            logger.error(f"Error searching patterns by text: {e}")
            return []

    async def get_pattern_by_id(
        self, pattern_id: str, client_account_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a pattern by its ID.

        Args:
            pattern_id: Pattern ID (UUID)
            client_account_id: Client account ID for scoping

        Returns:
            Pattern dictionary or None if not found
        """
        try:
            async with AsyncSessionLocal() as session:
                query = text(
                    """
                    SELECT
                        id,
                        pattern_id,
                        pattern_type,
                        pattern_name,
                        pattern_description,
                        discovered_by_agent,
                        confidence_score,
                        evidence_count,
                        times_referenced,
                        pattern_effectiveness_score,
                        pattern_metadata,
                        is_active,
                        is_validated,
                        created_at,
                        updated_at
                    FROM migration.agent_discovered_patterns
                    WHERE id = :id
                    AND client_account_id = :client_account_id
                """
                )

                result = await session.execute(
                    query, {"id": pattern_id, "client_account_id": client_account_id}
                )

                row = result.fetchone()
                if row:
                    return {
                        "id": str(row.id),
                        "pattern_id": row.pattern_id,
                        "pattern_type": row.pattern_type,
                        "pattern_name": row.pattern_name,
                        "pattern_description": row.pattern_description,
                        "discovered_by_agent": row.discovered_by_agent,
                        "confidence_score": float(row.confidence_score),
                        "evidence_count": row.evidence_count,
                        "times_referenced": row.times_referenced,
                        "pattern_effectiveness_score": (
                            float(row.pattern_effectiveness_score)
                            if row.pattern_effectiveness_score
                            else None
                        ),
                        "pattern_metadata": row.pattern_metadata,
                        "is_active": row.is_active,
                        "is_validated": row.is_validated,
                        "created_at": row.created_at,
                        "updated_at": row.updated_at,
                    }

                return None

        except Exception as e:
            logger.error(f"Error getting pattern by ID: {e}")
            return None

    async def update_pattern_feedback(
        self,
        pattern_id: str,
        client_account_id: str,
        is_positive: bool,
        update_confidence: bool = True,
    ) -> bool:
        """
        Update pattern feedback based on user interaction.

        Args:
            pattern_id: Pattern ID (UUID)
            client_account_id: Client account ID for scoping
            is_positive: Whether the feedback is positive
            update_confidence: Whether to update confidence score

        Returns:
            True if successful, False otherwise
        """
        try:
            async with AsyncSessionLocal() as session:
                # Update evidence count and optionally confidence
                if is_positive:
                    update_query = text(
                        """
                        UPDATE migration.agent_discovered_patterns
                        SET
                            evidence_count = evidence_count + 1,
                            times_referenced = times_referenced + 1,
                            confidence_score = LEAST(1.0, confidence_score + 0.05),
                            pattern_effectiveness_score = CASE
                                WHEN pattern_effectiveness_score IS NULL THEN 0.8
                                ELSE LEAST(1.0, pattern_effectiveness_score + 0.02)
                            END,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = :id
                        AND client_account_id = :client_account_id
                    """
                        if update_confidence
                        else """
                        UPDATE migration.agent_discovered_patterns
                        SET
                            evidence_count = evidence_count + 1,
                            times_referenced = times_referenced + 1,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = :id
                        AND client_account_id = :client_account_id
                    """
                    )
                else:
                    update_query = text(
                        """
                        UPDATE migration.agent_discovered_patterns
                        SET
                            times_referenced = times_referenced + 1,
                            confidence_score = GREATEST(0.0, confidence_score - 0.1),
                            pattern_effectiveness_score = CASE
                                WHEN pattern_effectiveness_score IS NULL THEN 0.4
                                ELSE GREATEST(0.0, pattern_effectiveness_score - 0.05)
                            END,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = :id
                        AND client_account_id = :client_account_id
                    """
                        if update_confidence
                        else """
                        UPDATE migration.agent_discovered_patterns
                        SET
                            times_referenced = times_referenced + 1,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = :id
                        AND client_account_id = :client_account_id
                    """
                    )

                result = await session.execute(
                    update_query,
                    {"id": pattern_id, "client_account_id": client_account_id},
                )
                await session.commit()

                return result.rowcount > 0

        except Exception as e:
            logger.error(f"Error updating pattern feedback: {e}")
            return False


# Create singleton instance
vector_utils = VectorUtils()
