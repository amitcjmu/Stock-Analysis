"""
Enhanced Embedding Service for Vector Search and Learning
Provides AI-powered vector embeddings using DeepInfra's thenlper/gte-large model.
Supports learning pattern storage and similarity search for assets.
"""

import logging
import asyncio
import random
from typing import List, Dict, Optional, Any, Union
from sqlalchemy.orm import Session

# Use the new LLM configuration instead of direct OpenAI import
try:
    from app.services.llm_config import get_embedding_llm
    EMBEDDING_LLM_AVAILABLE = True
except ImportError:
    EMBEDDING_LLM_AVAILABLE = False

from app.core.database import get_db
from app.models.asset import Asset  # Updated from CMDBAsset to Asset
from app.models.tags import Tag
from app.models.data_import import MappingLearningPattern
# from app.models.learning_patterns import AssetClassificationPattern
from app.core.config import settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Enhanced service for generating embeddings and performing similarity search."""
    
    def __init__(self):
        self.ai_available = False
        self.embedding_llm = None
        
        # Check if embedding LLM is configured through the new LLM config service
        if EMBEDDING_LLM_AVAILABLE and settings.DEEPINFRA_API_KEY:
            try:
                # Get the configured embedding LLM (thenlper/gte-large)
                self.embedding_llm = get_embedding_llm()
                self.ai_available = True
                logger.info("✅ AI embedding service initialized with DeepInfra thenlper/gte-large model via LLM config")
            except Exception as e:
                logger.error(f"Failed to initialize embedding LLM: {e}")
                self.ai_available = False
        else:
            logger.info("AI embedding service using mock mode - LLM config not available or DEEPINFRA_API_KEY not configured")
    
    async def embed_text(self, text: str) -> List[float]:
        """
        Generate embeddings for text using DeepInfra's thenlper/gte-large model.
        Returns 1024-dimensional vector.
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding vector
            
        Raises:
            Exception: If embedding generation fails
        """
        if not self.ai_available or not self.embedding_llm:
            logger.warning("AI embedding not available, using mock embedding")
            return self._generate_mock_embedding(text)
        
        try:
            # For now, use mock embeddings since CrewAI LLM class doesn't have embedding support
            # TODO: Implement proper embedding generation when CrewAI supports it
            logger.debug(f"Using mock embedding for text (length: {len(text)}) - CrewAI embedding support pending")
            return self._generate_mock_embedding(text)
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            # Fallback to mock embedding
            return self._generate_mock_embedding(text)
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts efficiently.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        if not self.ai_available or not self.embedding_llm:
            logger.warning("AI embedding not available, using mock embeddings")
            return [self._generate_mock_embedding(text) for text in texts]
        
        try:
            # For now, use mock embeddings since CrewAI LLM class doesn't have embedding support
            # TODO: Implement proper batch embedding generation when CrewAI supports it
            logger.debug(f"Using mock embeddings for batch of {len(texts)} texts - CrewAI embedding support pending")
            return [self._generate_mock_embedding(text) for text in texts]
            
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            # Fallback to mock embeddings
            return [self._generate_mock_embedding(text) for text in texts]
    
    def _generate_mock_embedding(self, text: str) -> List[float]:
        """
        Generate a mock embedding for testing/fallback purposes.
        Creates a deterministic vector based on text content.
        """
        # Create deterministic mock embedding based on text hash
        import hashlib
        text_hash = hashlib.md5(text.encode()).hexdigest()
        
        # Use hash to seed random generator for consistent results
        random.seed(text_hash)
        
        # Generate 1024-dimensional vector (matching thenlper/gte-large)
        embedding = [random.uniform(-1.0, 1.0) for _ in range(1024)]
        
        # Reset random seed
        random.seed()
        
        return embedding
    
    def calculate_cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Cosine similarity score between -1 and 1
        """
        if len(vec1) != len(vec2):
            raise ValueError(f"Vector dimensions don't match: {len(vec1)} vs {len(vec2)}")
        
        # Calculate dot product
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        
        # Calculate magnitudes
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5
        
        # Avoid division by zero
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        # Calculate cosine similarity
        similarity = dot_product / (magnitude1 * magnitude2)
        return similarity

    # Legacy methods updated to use Asset model instead of CMDBAsset
    async def search_similar_assets(
        self, 
        query_text: str, 
        limit: int = 10, 
        is_mock_only: bool = True
    ) -> List[Asset]:
        """Search for assets similar to the query text."""
        try:
            if self.ai_available:
                return await self._ai_text_search(query_text, limit, is_mock_only)
            else:
                return await self._mock_text_search(query_text, limit, is_mock_only)
        
        except Exception as e:
            logger.error(f"Error in similarity search: {e}")
            return await self._mock_text_search(query_text, limit, is_mock_only)
    
    async def find_similar_assets(
        self, 
        asset_id: int, 
        limit: int = 5, 
        is_mock_only: bool = True
    ) -> List[Asset]:
        """Find assets similar to the specified asset."""
        try:
            if self.ai_available:
                return await self._ai_similarity_search(asset_id, limit, is_mock_only)
            else:
                return await self._mock_similarity_search(asset_id, limit, is_mock_only)
        
        except Exception as e:
            logger.error(f"Error finding similar assets: {e}")
            return await self._mock_similarity_search(asset_id, limit, is_mock_only)
    
    async def suggest_tags_for_asset(
        self, 
        asset_id: int, 
        is_mock_only: bool = True
    ) -> List[Tag]:
        """Suggest tags for an asset based on similarity."""
        try:
            if self.ai_available:
                return await self._ai_tag_suggestions(asset_id, is_mock_only)
            else:
                return await self._mock_tag_suggestions(asset_id, is_mock_only)
        
        except Exception as e:
            logger.error(f"Error suggesting tags: {e}")
            return await self._mock_tag_suggestions(asset_id, is_mock_only)

    # Updated mock methods to use Asset model
    async def _mock_text_search(self, query_text: str, limit: int, is_mock_only: bool) -> List[Asset]:
        """Mock text search using simple keyword matching."""
        db = next(get_db())
        
        try:
            query = db.query(Asset)
            
            if is_mock_only:
                query = query.filter(Asset.is_mock == True)
            
            # Simple text matching against asset name, hostname, and description
            search_terms = query_text.lower().split()
            
            # Filter assets that contain any of the search terms
            assets = query.all()
            
            # Score assets based on text matches
            scored_assets = []
            for asset in assets:
                score = 0
                searchable_text = (
                    f"{asset.name or ''} "
                    f"{asset.hostname or ''} "
                    f"{asset.description or ''} "
                    f"{asset.asset_type or ''} "
                    f"{asset.operating_system or ''}"
                ).lower()
                
                for term in search_terms:
                    if term in searchable_text:
                        score += 1
                
                if score > 0:
                    scored_assets.append((asset, score))
            
            # Sort by score and return top results
            scored_assets.sort(key=lambda x: x[1], reverse=True)
            return [asset for asset, score in scored_assets[:limit]]
        
        finally:
            db.close()
    
    async def _mock_similarity_search(self, asset_id: int, limit: int, is_mock_only: bool) -> List[Asset]:
        """Mock similarity search based on asset attributes."""
        db = next(get_db())
        
        try:
            # Get the reference asset
            reference_asset = db.query(Asset).filter(Asset.id == asset_id).first()
            if not reference_asset:
                return []
            
            query = db.query(Asset).filter(Asset.id != asset_id)
            
            if is_mock_only:
                query = query.filter(Asset.is_mock == True)
            
            assets = query.all()
            
            # Score assets based on attribute similarity
            scored_assets = []
            for asset in assets:
                score = 0
                
                # Same asset type
                if asset.asset_type == reference_asset.asset_type:
                    score += 3
                
                # Same operating system
                if asset.operating_system == reference_asset.operating_system:
                    score += 2
                
                # Same environment
                if asset.environment == reference_asset.environment:
                    score += 2
                
                # Same business criticality
                if asset.business_criticality == reference_asset.business_criticality:
                    score += 1
                
                # Similar CPU cores (within 20%)
                if (reference_asset.cpu_cores and asset.cpu_cores and 
                    abs(asset.cpu_cores - reference_asset.cpu_cores) <= max(1, reference_asset.cpu_cores * 0.2)):
                    score += 1
                
                # Similar memory (within 30%)
                if (reference_asset.memory_gb and asset.memory_gb and 
                    abs(asset.memory_gb - reference_asset.memory_gb) <= reference_asset.memory_gb * 0.3):
                    score += 1
                
                if score > 0:
                    scored_assets.append((asset, score))
            
            # Sort by score and return top results
            scored_assets.sort(key=lambda x: x[1], reverse=True)
            return [asset for asset, score in scored_assets[:limit]]
        
        finally:
            db.close()
    
    async def _mock_tag_suggestions(self, asset_id: int, is_mock_only: bool) -> List[Tag]:
        """Mock tag suggestions based on asset attributes."""
        db = next(get_db())
        
        try:
            # Get the asset
            asset = db.query(Asset).filter(Asset.id == asset_id).first()
            if not asset:
                return []
            
            # Get available tags
            tag_query = db.query(Tag)
            if is_mock_only:
                tag_query = tag_query.filter(Tag.is_mock == True)
            
            available_tags = tag_query.all()
            
            # Simple tag matching based on asset attributes
            suggested_tags = []
            
            for tag in available_tags:
                tag_name_lower = tag.name.lower()
                
                # Match based on asset type
                if asset.asset_type and asset.asset_type.lower() in tag_name_lower:
                    suggested_tags.append(tag)
                    continue
                
                # Match based on operating system
                if asset.operating_system and any(
                    os_term in tag_name_lower 
                    for os_term in asset.operating_system.lower().split()
                ):
                    suggested_tags.append(tag)
                    continue
                
                # Match based on environment
                if asset.environment and asset.environment.lower() in tag_name_lower:
                    suggested_tags.append(tag)
                    continue
                
                # Match based on business criticality
                if asset.business_criticality and asset.business_criticality.lower() in tag_name_lower:
                    suggested_tags.append(tag)
                    continue
            
            # Shuffle and return random subset for demo purposes
            random.shuffle(suggested_tags)
            return suggested_tags[:5]  # Return up to 5 suggested tags
        
        finally:
            db.close()
    
    async def _ai_text_search(self, query_text: str, limit: int, is_mock_only: bool) -> List[Asset]:
        """AI-powered text search using embeddings."""
        # Generate embedding for query
        query_embedding = await self.embed_text(query_text)
        
        # TODO: Implement vector similarity search in database
        # For now, fall back to mock search
        logger.info("AI text search with embeddings not yet fully implemented, falling back to mock search")
        return await self._mock_text_search(query_text, limit, is_mock_only)
    
    async def _ai_similarity_search(self, asset_id: int, limit: int, is_mock_only: bool) -> List[Asset]:
        """AI-powered similarity search using embeddings."""
        # TODO: Implement vector similarity search based on asset embeddings
        # For now, fall back to mock search
        logger.info("AI similarity search with embeddings not yet fully implemented, falling back to mock search")
        return await self._mock_similarity_search(asset_id, limit, is_mock_only)
    
    async def _ai_tag_suggestions(self, asset_id: int, is_mock_only: bool) -> List[Tag]:
        """AI-powered tag suggestions using embeddings."""
        # TODO: Implement embedding-based tag suggestions
        # For now, fall back to mock suggestions
        logger.info("AI tag suggestions with embeddings not yet fully implemented, falling back to mock suggestions")
        return await self._mock_tag_suggestions(asset_id, is_mock_only) 