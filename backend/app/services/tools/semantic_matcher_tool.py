"""
Semantic Matcher Tool for intelligent field matching using ML embeddings
"""

import json
import logging
from typing import Any, Dict, List, Tuple

import numpy as np

from app.services.tools.base_tool import AsyncBaseDiscoveryTool
from app.services.tools.registry import ToolMetadata

logger = logging.getLogger(__name__)

class SemanticMatcherTool(AsyncBaseDiscoveryTool):
    """Uses ML embeddings to find semantic similarities between field names"""
    
    name: str = "semantic_matcher"
    description: str = "Find semantic similarities between source and target field names using ML"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._embedding_service = None
    
    @classmethod
    def tool_metadata(cls) -> ToolMetadata:
        return ToolMetadata(
            name="semantic_matcher",
            description="Semantic field matching using ML embeddings",
            tool_class=cls,
            categories=["mapping", "analysis", "ml"],
            required_params=["source_fields", "target_fields"],
            optional_params=["confidence_threshold"],
            context_aware=True,
            async_tool=True
        )
    
    async def arun(
        self,
        source_fields: List[str],
        target_fields: List[str],
        confidence_threshold: float = 0.3
    ) -> str:
        """
        Find semantic matches between source and target fields.
        
        Args:
            source_fields: List of source field names
            target_fields: List of target field names  
            confidence_threshold: Minimum confidence for matches
            
        Returns:
            JSON string with semantic matching results
        """
        try:
            # Initialize embedding service if needed
            if not self._embedding_service:
                from app.services.embedding_service import EmbeddingService
                self._embedding_service = EmbeddingService()
            
            # Generate embeddings for source and target fields
            source_embeddings = await self._get_field_embeddings(source_fields)
            target_embeddings = await self._get_field_embeddings(target_fields)
            
            # Calculate similarity matrix
            similarities = self._calculate_similarity_matrix(
                source_embeddings, target_embeddings
            )
            
            # Find best matches
            matches = []
            for i, source_field in enumerate(source_fields):
                best_matches = self._find_best_matches(
                    i, similarities, target_fields, confidence_threshold
                )
                
                for target_idx, confidence in best_matches:
                    matches.append({
                        "source_field": source_field,
                        "target_field": target_fields[target_idx],
                        "confidence": float(confidence),
                        "match_type": "semantic",
                        "reasoning": f"Semantic similarity: {confidence:.3f}"
                    })
            
            # Add exact name matches with higher confidence
            exact_matches = self._find_exact_matches(source_fields, target_fields)
            matches.extend(exact_matches)
            
            # Sort by confidence
            matches.sort(key=lambda x: x["confidence"], reverse=True)
            
            result = {
                "status": "success",
                "total_matches": len(matches),
                "matches": matches,
                "source_fields_count": len(source_fields),
                "target_fields_count": len(target_fields),
                "average_confidence": np.mean([m["confidence"] for m in matches]) if matches else 0.0
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Semantic matching failed: {e}")
            return json.dumps({
                "status": "error",
                "error": str(e),
                "matches": []
            })
    
    async def _get_field_embeddings(self, fields: List[str]) -> np.ndarray:
        """Generate embeddings for field names"""
        try:
            # Clean and prepare field names for embedding
            cleaned_fields = []
            for field in fields:
                # Convert camelCase/snake_case to readable text
                cleaned = field.replace('_', ' ').replace('-', ' ')
                # Split camelCase
                import re
                cleaned = re.sub(r'([a-z])([A-Z])', r'\1 \2', cleaned)
                cleaned_fields.append(cleaned.lower().strip())
            
            # Get embeddings
            embeddings = await self._embedding_service.get_embeddings(cleaned_fields)
            return np.array(embeddings)
            
        except Exception as e:
            logger.warning(f"Failed to get embeddings: {e}")
            # Fallback to simple string similarity
            return self._simple_string_embeddings(fields)
    
    def _simple_string_embeddings(self, fields: List[str]) -> np.ndarray:
        """Fallback simple string-based embeddings"""
        # Create simple character-based vectors as fallback
        max(len(field) for field in fields) if fields else 0
        embeddings = []
        
        for field in fields:
            # Simple character frequency vector
            vector = [0] * 128  # ASCII range
            for char in field.lower():
                if ord(char) < 128:
                    vector[ord(char)] += 1
            
            # Normalize
            total = sum(vector)
            if total > 0:
                vector = [v / total for v in vector]
            
            embeddings.append(vector)
        
        return np.array(embeddings)
    
    def _calculate_similarity_matrix(
        self, 
        source_embeddings: np.ndarray, 
        target_embeddings: np.ndarray
    ) -> np.ndarray:
        """Calculate cosine similarity matrix"""
        # Normalize embeddings
        source_norm = source_embeddings / (np.linalg.norm(source_embeddings, axis=1, keepdims=True) + 1e-8)
        target_norm = target_embeddings / (np.linalg.norm(target_embeddings, axis=1, keepdims=True) + 1e-8)
        
        # Calculate cosine similarity
        return np.dot(source_norm, target_norm.T)
    
    def _find_best_matches(
        self,
        source_idx: int,
        similarities: np.ndarray,
        target_fields: List[str],
        threshold: float
    ) -> List[Tuple[int, float]]:
        """Find best matches for a source field"""
        source_similarities = similarities[source_idx]
        
        matches = []
        for target_idx, similarity in enumerate(source_similarities):
            if similarity >= threshold:
                matches.append((target_idx, similarity))
        
        # Sort by similarity and return top 3
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[:3]
    
    def _find_exact_matches(self, source_fields: List[str], target_fields: List[str]) -> List[Dict[str, Any]]:
        """Find exact or near-exact string matches"""
        exact_matches = []
        
        for source in source_fields:
            source_lower = source.lower()
            source_clean = source_lower.replace('_', '').replace('-', '').replace(' ', '')
            
            for target in target_fields:
                target_lower = target.lower()
                target_clean = target_lower.replace('_', '').replace('-', '').replace(' ', '')
                
                confidence = 0.0
                reasoning = ""
                
                # Exact match
                if source_lower == target_lower:
                    confidence = 1.0
                    reasoning = "Exact field name match"
                
                # Exact match after cleaning
                elif source_clean == target_clean:
                    confidence = 0.95
                    reasoning = "Exact match ignoring separators"
                
                # Contains match
                elif source_clean in target_clean or target_clean in source_clean:
                    confidence = 0.8
                    reasoning = "Field name contains other"
                
                if confidence > 0:
                    exact_matches.append({
                        "source_field": source,
                        "target_field": target,
                        "confidence": confidence,
                        "match_type": "exact",
                        "reasoning": reasoning
                    })
        
        return exact_matches