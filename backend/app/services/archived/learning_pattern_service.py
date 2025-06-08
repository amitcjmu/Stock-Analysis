"""
Learning Pattern Service

Foundation service for managing learning patterns across the platform.
Provides pattern storage, retrieval, and management functionality.
"""

import logging
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.data_import import MappingLearningPattern
# from app.models.learning_patterns import (
#     AssetClassificationPattern,
#     ConfidenceThreshold,
#     UserFeedbackEvent,
#     LearningStatistics
# )
from app.services.embedding_service import EmbeddingService
from app.utils.vector_utils import VectorUtils

logger = logging.getLogger(__name__)


class LearningPatternService:
    """Foundation service for learning pattern management."""
    
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.vector_utils = VectorUtils()
    
    async def store_pattern(
        self, 
        pattern_data: Dict[str, Any],
        pattern_type: str = "mapping"
    ) -> str:
        """
        Store a learning pattern with embedding.
        
        Args:
            pattern_data: Dictionary containing pattern information
            pattern_type: Type of pattern ("mapping" or "classification")
            
        Returns:
            Pattern ID (UUID as string)
        """
        try:
            if pattern_type == "mapping":
                return await self._store_mapping_pattern(pattern_data)
            elif pattern_type == "classification":
                return await self._store_classification_pattern(pattern_data)
            else:
                raise ValueError(f"Unknown pattern type: {pattern_type}")
                
        except Exception as e:
            logger.error(f"Error storing {pattern_type} pattern: {e}")
            raise
    
    async def find_similar_patterns(
        self, 
        query_text: str,
        client_account_id: str,
        pattern_type: str = "mapping",
        limit: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[Tuple[Any, float]]:
        """
        Find similar patterns using vector search.
        
        Args:
            query_text: Text to search for similar patterns
            client_account_id: Client account ID for scoping
            pattern_type: Type of pattern to search
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score
            
        Returns:
            List of (pattern, similarity_score) tuples
        """
        try:
            # Generate embedding for query text
            query_embedding = await self.embedding_service.embed_text(query_text)
            
            if pattern_type == "mapping":
                return await self.vector_utils.find_similar_patterns(
                    query_embedding, 
                    client_account_id, 
                    limit, 
                    similarity_threshold
                )
            elif pattern_type == "classification":
                return await self.vector_utils.find_similar_asset_patterns(
                    query_text,
                    client_account_id,
                    limit,
                    similarity_threshold
                )
            else:
                raise ValueError(f"Unknown pattern type: {pattern_type}")
                
        except Exception as e:
            logger.error(f"Error finding similar {pattern_type} patterns: {e}")
            return []
    
    async def update_pattern_confidence(
        self,
        pattern_id: str,
        was_successful: bool,
        pattern_type: str = "mapping"
    ) -> None:
        """
        Update pattern confidence based on usage outcome.
        
        Args:
            pattern_id: ID of the pattern to update
            was_successful: Whether the pattern application was successful
            pattern_type: Type of pattern
        """
        try:
            await self.vector_utils.update_pattern_performance(
                pattern_id, 
                was_successful, 
                pattern_type
            )
            
            logger.debug(f"Updated {pattern_type} pattern {pattern_id} confidence: success={was_successful}")
            
        except Exception as e:
            logger.error(f"Error updating pattern confidence: {e}")
    
    async def get_pattern_statistics(
        self,
        client_account_id: str,
        pattern_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get statistics about learning patterns for a client.
        
        Args:
            client_account_id: Client account ID
            pattern_type: Optional pattern type filter
            
        Returns:
            Dictionary with pattern statistics
        """
        try:
            async with AsyncSessionLocal() as session:
                stats = {
                    "total_patterns": 0,
                    "mapping_patterns": 0,
                    "classification_patterns": 0,
                    "average_confidence": 0.0,
                    "high_confidence_patterns": 0,
                    "patterns_by_source": {}
                }
                
                # Count mapping patterns
                if pattern_type is None or pattern_type == "mapping":
                    mapping_count = await session.execute(
                        "SELECT COUNT(*) FROM migration.mapping_learning_patterns WHERE client_account_id = :client_id",
                        {"client_id": client_account_id}
                    )
                    stats["mapping_patterns"] = mapping_count.scalar()
                
                # Count classification patterns
                if pattern_type is None or pattern_type == "classification":
                    classification_count = await session.execute(
                        "SELECT COUNT(*) FROM migration.asset_classification_patterns WHERE client_account_id = :client_id",
                        {"client_id": client_account_id}
                    )
                    stats["classification_patterns"] = classification_count.scalar()
                
                stats["total_patterns"] = stats["mapping_patterns"] + stats["classification_patterns"]
                
                # Calculate average confidence (simplified)
                if stats["total_patterns"] > 0:
                    # This is a simplified calculation - in practice you'd want more sophisticated metrics
                    stats["average_confidence"] = 0.75  # Placeholder
                    stats["high_confidence_patterns"] = int(stats["total_patterns"] * 0.6)  # Placeholder
                
                return stats
                
        except Exception as e:
            logger.error(f"Error getting pattern statistics: {e}")
            return {"error": str(e)}
    
    async def cleanup_old_patterns(
        self,
        client_account_id: str,
        days_old: int = 90,
        min_confidence: float = 0.3
    ) -> int:
        """
        Clean up old, low-confidence patterns.
        
        Args:
            client_account_id: Client account ID
            days_old: Age threshold in days
            min_confidence: Minimum confidence to keep
            
        Returns:
            Number of patterns cleaned up
        """
        try:
            # Use vector utils to retire low-performing patterns
            retired_count = await self.vector_utils.retire_low_performing_patterns(
                client_account_id,
                min_uses=5,
                max_failure_rate=0.7
            )
            
            logger.info(f"Cleaned up {retired_count} old patterns for client {client_account_id}")
            return retired_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old patterns: {e}")
            return 0
    
    async def _store_mapping_pattern(self, pattern_data: Dict[str, Any]) -> str:
        """Store a field mapping pattern."""
        required_fields = ["client_account_id", "source_field_name", "target_field_name"]
        for field in required_fields:
            if field not in pattern_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Generate embedding for source field
        source_text = pattern_data["source_field_name"]
        if "sample_values" in pattern_data:
            # Include sample values in embedding
            sample_text = " ".join(str(v) for v in pattern_data["sample_values"][:5])
            source_text = f"{source_text} {sample_text}"
        
        embedding = await self.embedding_service.embed_text(source_text)
        
        async with AsyncSessionLocal() as session:
            pattern = MappingLearningPattern(
                client_account_id=pattern_data["client_account_id"],
                engagement_id=pattern_data.get("engagement_id"),
                source_field_name=pattern_data["source_field_name"],
                source_field_embedding=embedding,
                source_sample_values=pattern_data.get("sample_values"),
                target_field_name=pattern_data["target_field_name"],
                target_field_type=pattern_data.get("target_field_type"),
                pattern_context=pattern_data.get("pattern_context", {}),
                confidence_score=pattern_data.get("confidence_score", 0.5),
                learning_source=pattern_data.get("learning_source", "user_feedback"),
                created_by=pattern_data.get("created_by")
            )
            
            session.add(pattern)
            await session.commit()
            await session.refresh(pattern)
            
            logger.info(f"Stored mapping pattern: {pattern_data['source_field_name']} -> {pattern_data['target_field_name']}")
            return str(pattern.id)
    
    async def _store_classification_pattern(self, pattern_data: Dict[str, Any]) -> str:
        """Store an asset classification pattern."""
        required_fields = ["client_account_id", "pattern_name", "predicted_asset_type"]
        for field in required_fields:
            if field not in pattern_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Generate embeddings for asset name pattern
        asset_name_embedding = None
        if "asset_name_pattern" in pattern_data:
            asset_name_embedding = await self.embedding_service.embed_text(
                pattern_data["asset_name_pattern"]
            )
        
        # Generate embeddings for metadata if provided
        metadata_embedding = None
        if "metadata_patterns" in pattern_data:
            metadata_text = " ".join(
                f"{k}:{v}" for k, v in pattern_data["metadata_patterns"].items()
            )
            metadata_embedding = await self.embedding_service.embed_text(metadata_text)
        
        async with AsyncSessionLocal() as session:
            pattern = AssetClassificationPattern(
                client_account_id=pattern_data["client_account_id"],
                engagement_id=pattern_data.get("engagement_id"),
                pattern_name=pattern_data["pattern_name"],
                pattern_type=pattern_data.get("pattern_type", "name_pattern"),
                asset_name_pattern=pattern_data.get("asset_name_pattern"),
                asset_name_embedding=asset_name_embedding,
                metadata_patterns=pattern_data.get("metadata_patterns"),
                metadata_embedding=metadata_embedding,
                predicted_asset_type=pattern_data["predicted_asset_type"],
                predicted_application_type=pattern_data.get("predicted_application_type"),
                predicted_technology_stack=pattern_data.get("predicted_technology_stack"),
                confidence_score=pattern_data.get("confidence_score", 0.5),
                learning_source=pattern_data.get("learning_source", "user_feedback"),
                created_by=pattern_data.get("created_by")
            )
            
            session.add(pattern)
            await session.commit()
            await session.refresh(pattern)
            
            logger.info(f"Stored classification pattern: {pattern_data['pattern_name']} -> {pattern_data['predicted_asset_type']}")
            return str(pattern.id)
    
    async def get_patterns_by_type(
        self,
        client_account_id: str,
        pattern_type: str,
        limit: int = 50,
        min_confidence: float = 0.0
    ) -> List[Any]:
        """
        Get patterns by type for a client.
        
        Args:
            client_account_id: Client account ID
            pattern_type: Type of pattern ("mapping" or "classification")
            limit: Maximum number of patterns to return
            min_confidence: Minimum confidence threshold
            
        Returns:
            List of pattern objects
        """
        try:
            async with AsyncSessionLocal() as session:
                if pattern_type == "mapping":
                    result = await session.execute(
                        """
                        SELECT * FROM migration.mapping_learning_patterns 
                        WHERE client_account_id = :client_id 
                        AND confidence_score >= :min_confidence
                        ORDER BY confidence_score DESC, created_at DESC
                        LIMIT :limit
                        """,
                        {
                            "client_id": client_account_id,
                            "min_confidence": min_confidence,
                            "limit": limit
                        }
                    )
                elif pattern_type == "classification":
                    result = await session.execute(
                        """
                        SELECT * FROM migration.asset_classification_patterns 
                        WHERE client_account_id = :client_id 
                        AND confidence_score >= :min_confidence
                        ORDER BY confidence_score DESC, created_at DESC
                        LIMIT :limit
                        """,
                        {
                            "client_id": client_account_id,
                            "min_confidence": min_confidence,
                            "limit": limit
                        }
                    )
                else:
                    raise ValueError(f"Unknown pattern type: {pattern_type}")
                
                patterns = result.fetchall()
                logger.debug(f"Retrieved {len(patterns)} {pattern_type} patterns for client {client_account_id}")
                return patterns
                
        except Exception as e:
            logger.error(f"Error getting patterns by type: {e}")
            return []


# Global instance for easy access
learning_pattern_service = LearningPatternService() 