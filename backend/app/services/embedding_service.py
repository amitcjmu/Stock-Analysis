"""
Embedding Service for Vector Search
Provides AI-powered vector embeddings and similarity search for assets.
Falls back to mock similarity when AI services are unavailable.
"""

import logging
import random
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.cmdb_asset import CMDBAsset
from app.models.tags import Tag
from app.core.config import settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Service for generating embeddings and performing similarity search."""
    
    def __init__(self):
        self.ai_available = False
        
        # Check if AI services are configured
        if settings.DEEPINFRA_API_KEY:
            self.ai_available = True
            logger.info("AI embedding service initialized with DeepInfra")
        else:
            logger.info("AI embedding service using mock mode")
    
    async def search_similar_assets(
        self, 
        query_text: str, 
        limit: int = 10, 
        is_mock_only: bool = True
    ) -> List[CMDBAsset]:
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
    ) -> List[CMDBAsset]:
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
    
    async def _mock_text_search(self, query_text: str, limit: int, is_mock_only: bool) -> List[CMDBAsset]:
        """Mock text search using simple keyword matching."""
        db = next(get_db())
        
        try:
            query = db.query(CMDBAsset)
            
            if is_mock_only:
                query = query.filter(CMDBAsset.is_mock == True)
            
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
    
    async def _mock_similarity_search(self, asset_id: int, limit: int, is_mock_only: bool) -> List[CMDBAsset]:
        """Mock similarity search based on asset attributes."""
        db = next(get_db())
        
        try:
            # Get the reference asset
            reference_asset = db.query(CMDBAsset).filter(CMDBAsset.id == asset_id).first()
            if not reference_asset:
                return []
            
            query = db.query(CMDBAsset).filter(CMDBAsset.id != asset_id)
            
            if is_mock_only:
                query = query.filter(CMDBAsset.is_mock == True)
            
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
            asset = db.query(CMDBAsset).filter(CMDBAsset.id == asset_id).first()
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
    
    async def _ai_text_search(self, query_text: str, limit: int, is_mock_only: bool) -> List[CMDBAsset]:
        """AI-powered text search using embeddings (placeholder for real implementation)."""
        # TODO: Implement real AI text search with DeepInfra API
        logger.info("AI text search not yet implemented, falling back to mock search")
        return await self._mock_text_search(query_text, limit, is_mock_only)
    
    async def _ai_similarity_search(self, asset_id: int, limit: int, is_mock_only: bool) -> List[CMDBAsset]:
        """AI-powered similarity search using embeddings (placeholder for real implementation)."""
        # TODO: Implement real AI similarity search with DeepInfra API
        logger.info("AI similarity search not yet implemented, falling back to mock search")
        return await self._mock_similarity_search(asset_id, limit, is_mock_only)
    
    async def _ai_tag_suggestions(self, asset_id: int, is_mock_only: bool) -> List[Tag]:
        """AI-powered tag suggestions using embeddings (placeholder for real implementation)."""
        # TODO: Implement real AI tag suggestions with DeepInfra API
        logger.info("AI tag suggestions not yet implemented, falling back to mock suggestions")
        return await self._mock_tag_suggestions(asset_id, is_mock_only) 