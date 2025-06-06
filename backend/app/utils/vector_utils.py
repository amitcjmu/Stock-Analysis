"""
Vector Utilities for pgvector Operations

Provides utility functions for storing and querying vector embeddings
using pgvector for pattern storage and similarity search.
"""

import logging
from typing import List, Dict, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, AsyncSessionLocal
from app.models.learning_patterns import MappingLearningPattern, AssetClassificationPattern
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class VectorUtils:
    """Utility class for vector operations with pgvector."""
    
    def __init__(self):
        self.embedding_service = EmbeddingService()
    
    async def store_pattern_embedding(
        self, 
        pattern_text: str, 
        target_field: str,
        client_account_id: str,
        engagement_id: Optional[str] = None,
        pattern_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store a field mapping pattern with its embedding.
        
        Args:
            pattern_text: Text to generate embedding for (field name + sample values)
            target_field: Target field this pattern maps to
            client_account_id: Client account ID for multi-tenancy
            engagement_id: Optional engagement ID
            pattern_context: Additional context about the mapping
            
        Returns:
            Pattern ID (UUID as string)
        """
        try:
            # Generate embedding for the pattern text
            embedding = await self.embedding_service.embed_text(pattern_text)
            
            async with AsyncSessionLocal() as session:
                # Create new mapping pattern
                pattern = MappingLearningPattern(
                    client_account_id=client_account_id,
                    engagement_id=engagement_id,
                    source_field_name=pattern_text.split()[0] if pattern_text else "unknown",
                    source_field_embedding=embedding,
                    target_field_name=target_field,
                    pattern_context=pattern_context or {},
                    confidence_score=0.5,  # Initial confidence
                    learning_source="user_feedback"
                )
                
                session.add(pattern)
                await session.commit()
                await session.refresh(pattern)
                
                logger.info(f"Stored pattern embedding for '{pattern_text}' -> '{target_field}' (ID: {pattern.id})")
                return str(pattern.id)
                
        except Exception as e:
            logger.error(f"Error storing pattern embedding: {e}")
            raise
    
    async def find_similar_patterns(
        self, 
        query_embedding: List[float], 
        client_account_id: str,
        limit: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[Tuple[MappingLearningPattern, float]]:
        """
        Find similar mapping patterns using vector similarity search.
        
        Args:
            query_embedding: Query vector to search for
            client_account_id: Client account ID for scoping
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score
            
        Returns:
            List of (pattern, similarity_score) tuples
        """
        try:
            async with AsyncSessionLocal() as session:
                # Use pgvector cosine similarity search
                query = text("""
                    SELECT 
                        id,
                        client_account_id,
                        engagement_id,
                        source_field_name,
                        target_field_name,
                        pattern_context,
                        confidence_score,
                        success_count,
                        failure_count,
                        learning_source,
                        created_at,
                        updated_at,
                        (source_field_embedding <=> $1::vector) as similarity_distance
                    FROM migration.mapping_learning_patterns 
                    WHERE client_account_id = $2
                    AND (source_field_embedding <=> $1::vector) < $3
                    ORDER BY source_field_embedding <=> $1::vector
                    LIMIT $4
                """)
                
                # Convert similarity threshold to distance threshold (cosine distance = 1 - cosine similarity)
                distance_threshold = 1.0 - similarity_threshold
                
                # Convert embedding to string format for pgvector
                embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
                
                result = await session.execute(
                    query,
                    (embedding_str, client_account_id, distance_threshold, limit)
                )
                
                patterns_with_similarity = []
                for row in result.fetchall():
                    # Convert distance back to similarity
                    similarity = 1.0 - row.similarity_distance
                    
                    # Create pattern object from row data
                    pattern = MappingLearningPattern(
                        id=row.id,
                        client_account_id=row.client_account_id,
                        engagement_id=row.engagement_id,
                        source_field_name=row.source_field_name,
                        target_field_name=row.target_field_name,
                        pattern_context=row.pattern_context,
                        confidence_score=row.confidence_score,
                        success_count=row.success_count,
                        failure_count=row.failure_count,
                        learning_source=row.learning_source,
                        created_at=row.created_at,
                        updated_at=row.updated_at
                    )
                    
                    patterns_with_similarity.append((pattern, similarity))
                
                logger.debug(f"Found {len(patterns_with_similarity)} similar patterns for client {client_account_id}")
                return patterns_with_similarity
                
        except Exception as e:
            logger.error(f"Error finding similar patterns: {e}")
            return []
    
    async def find_similar_asset_patterns(
        self,
        asset_name: str,
        client_account_id: str,
        limit: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[Tuple[AssetClassificationPattern, float]]:
        """
        Find similar asset classification patterns.
        
        Args:
            asset_name: Asset name to find patterns for
            client_account_id: Client account ID for scoping
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score
            
        Returns:
            List of (pattern, similarity_score) tuples
        """
        try:
            # Generate embedding for asset name
            query_embedding = await self.embedding_service.embed_text(asset_name)
            
            async with AsyncSessionLocal() as session:
                # Use pgvector cosine similarity search
                query = text("""
                    SELECT 
                        id,
                        client_account_id,
                        engagement_id,
                        pattern_name,
                        pattern_type,
                        asset_name_pattern,
                        predicted_asset_type,
                        predicted_application_type,
                        predicted_technology_stack,
                        confidence_score,
                        success_count,
                        failure_count,
                        accuracy_rate,
                        learning_source,
                        created_at,
                        updated_at,
                        (asset_name_embedding <=> $1::vector) as similarity_distance
                    FROM migration.asset_classification_patterns 
                    WHERE client_account_id = $2
                    AND asset_name_embedding IS NOT NULL
                    AND (asset_name_embedding <=> $1::vector) < $3
                    ORDER BY asset_name_embedding <=> $1::vector
                    LIMIT $4
                """)
                
                # Convert similarity threshold to distance threshold
                distance_threshold = 1.0 - similarity_threshold
                
                # Convert embedding to string format for pgvector
                embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
                
                result = await session.execute(
                    query,
                    (embedding_str, client_account_id, distance_threshold, limit)
                )
                
                patterns_with_similarity = []
                for row in result.fetchall():
                    # Convert distance back to similarity
                    similarity = 1.0 - row.similarity_distance
                    
                    # Create pattern object from row data
                    pattern = AssetClassificationPattern(
                        id=row.id,
                        client_account_id=row.client_account_id,
                        engagement_id=row.engagement_id,
                        pattern_name=row.pattern_name,
                        pattern_type=row.pattern_type,
                        asset_name_pattern=row.asset_name_pattern,
                        predicted_asset_type=row.predicted_asset_type,
                        predicted_application_type=row.predicted_application_type,
                        predicted_technology_stack=row.predicted_technology_stack,
                        confidence_score=row.confidence_score,
                        success_count=row.success_count,
                        failure_count=row.failure_count,
                        accuracy_rate=row.accuracy_rate,
                        learning_source=row.learning_source,
                        created_at=row.created_at,
                        updated_at=row.updated_at
                    )
                    
                    patterns_with_similarity.append((pattern, similarity))
                
                logger.debug(f"Found {len(patterns_with_similarity)} similar asset patterns for '{asset_name}'")
                return patterns_with_similarity
                
        except Exception as e:
            logger.error(f"Error finding similar asset patterns: {e}")
            return []
    
    def calculate_cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Cosine similarity score between -1 and 1
        """
        return self.embedding_service.calculate_cosine_similarity(vec1, vec2)
    
    async def update_pattern_performance(
        self,
        pattern_id: str,
        was_successful: bool,
        pattern_type: str = "mapping"
    ) -> None:
        """
        Update pattern performance metrics based on usage outcome.
        
        Args:
            pattern_id: ID of the pattern to update
            was_successful: Whether the pattern application was successful
            pattern_type: Type of pattern ("mapping" or "classification")
        """
        try:
            async with AsyncSessionLocal() as session:
                if pattern_type == "mapping":
                    pattern = await session.get(MappingLearningPattern, pattern_id)
                    if pattern:
                        if was_successful:
                            pattern.success_count += 1
                        else:
                            pattern.failure_count += 1
                        
                        # Recalculate confidence score
                        total_uses = pattern.success_count + pattern.failure_count
                        if total_uses > 0:
                            pattern.confidence_score = pattern.success_count / total_uses
                        
                        await session.commit()
                        logger.debug(f"Updated mapping pattern {pattern_id} performance: success={was_successful}")
                
                elif pattern_type == "classification":
                    pattern = await session.get(AssetClassificationPattern, pattern_id)
                    if pattern:
                        if was_successful:
                            pattern.success_count += 1
                        else:
                            pattern.failure_count += 1
                        
                        # Recalculate accuracy rate
                        total_uses = pattern.success_count + pattern.failure_count
                        if total_uses > 0:
                            pattern.accuracy_rate = pattern.success_count / total_uses
                            pattern.confidence_score = pattern.accuracy_rate
                        
                        await session.commit()
                        logger.debug(f"Updated classification pattern {pattern_id} performance: success={was_successful}")
                
        except Exception as e:
            logger.error(f"Error updating pattern performance: {e}")
    
    async def retire_low_performing_patterns(
        self,
        client_account_id: str,
        min_uses: int = 10,
        max_failure_rate: float = 0.7
    ) -> int:
        """
        Retire patterns that consistently perform poorly.
        
        Args:
            client_account_id: Client account to clean up patterns for
            min_uses: Minimum number of uses before considering retirement
            max_failure_rate: Maximum failure rate before retirement
            
        Returns:
            Number of patterns retired
        """
        try:
            retired_count = 0
            
            async with AsyncSessionLocal() as session:
                # Find poorly performing mapping patterns
                mapping_query = text("""
                    DELETE FROM migration.mapping_learning_patterns
                    WHERE client_account_id = :client_account_id
                    AND (success_count + failure_count) >= :min_uses
                    AND (failure_count::float / (success_count + failure_count)) > :max_failure_rate
                """)
                
                result = await session.execute(
                    mapping_query,
                    {
                        "client_account_id": client_account_id,
                        "min_uses": min_uses,
                        "max_failure_rate": max_failure_rate
                    }
                )
                retired_count += result.rowcount
                
                # Find poorly performing classification patterns
                classification_query = text("""
                    DELETE FROM migration.asset_classification_patterns
                    WHERE client_account_id = :client_account_id
                    AND (success_count + failure_count) >= :min_uses
                    AND (failure_count::float / (success_count + failure_count)) > :max_failure_rate
                """)
                
                result = await session.execute(
                    classification_query,
                    {
                        "client_account_id": client_account_id,
                        "min_uses": min_uses,
                        "max_failure_rate": max_failure_rate
                    }
                )
                retired_count += result.rowcount
                
                await session.commit()
                
                if retired_count > 0:
                    logger.info(f"Retired {retired_count} low-performing patterns for client {client_account_id}")
                
                return retired_count
                
        except Exception as e:
            logger.error(f"Error retiring low-performing patterns: {e}")
            return 0


# Global instance for easy access
vector_utils = VectorUtils() 