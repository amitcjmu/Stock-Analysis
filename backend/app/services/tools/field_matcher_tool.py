"""
Field Matcher Tool for intelligent field mapping
"""

from typing import Dict, Any, List, Tuple
from app.services.tools.base_tool import BaseDiscoveryTool
from app.services.tools.registry import ToolMetadata
from difflib import SequenceMatcher
import re

class FieldMatcherTool(BaseDiscoveryTool):
    """Matches source fields to target fields using various algorithms"""
    
    name: str = "field_matcher"
    description: str = "Match source fields to target fields using semantic and pattern matching"
    
    @classmethod
    def tool_metadata(cls) -> ToolMetadata:
        return ToolMetadata(
            name="field_matcher",
            description="Intelligent field matching with multiple algorithms",
            tool_class=cls,
            categories=["mapping", "analysis"],
            required_params=[],
            optional_params=["threshold"],
            context_aware=True,
            async_tool=False
        )
    
    def run(
        self,
        source_fields: List[str],
        target_fields: List[Dict[str, Any]],
        threshold: float = 0.6
    ) -> List[Dict[str, Any]]:
        """
        Match source fields to target fields.
        
        Args:
            source_fields: List of source field names
            target_fields: List of target field definitions
            threshold: Minimum confidence threshold
            
        Returns:
            List of field mappings with confidence scores
        """
        mappings = []
        
        for source_field in source_fields:
            best_match = None
            best_score = 0.0
            
            # Normalize source field name
            normalized_source = self._normalize_field_name(source_field)
            
            for target in target_fields:
                target_name = target.get("name", "")
                normalized_target = self._normalize_field_name(target_name)
                
                # Calculate match scores
                scores = []
                
                # Exact match
                if normalized_source == normalized_target:
                    scores.append(1.0)
                
                # Fuzzy string matching
                fuzzy_score = SequenceMatcher(
                    None, 
                    normalized_source, 
                    normalized_target
                ).ratio()
                scores.append(fuzzy_score)
                
                # Token-based matching
                source_tokens = self._tokenize(normalized_source)
                target_tokens = self._tokenize(normalized_target)
                token_score = self._calculate_token_similarity(
                    source_tokens, 
                    target_tokens
                )
                scores.append(token_score)
                
                # Semantic similarity (simplified)
                semantic_score = self._calculate_semantic_similarity(
                    source_field,
                    target_name,
                    target.get("description", "")
                )
                scores.append(semantic_score)
                
                # Overall score (weighted average)
                overall_score = (
                    scores[0] * 0.4 +  # Exact match weight
                    scores[1] * 0.3 +  # Fuzzy match weight
                    scores[2] * 0.2 +  # Token match weight
                    scores[3] * 0.1    # Semantic weight
                )
                
                if overall_score > best_score:
                    best_score = overall_score
                    best_match = target
            
            # Add mapping if above threshold
            if best_score >= threshold and best_match:
                mappings.append({
                    "source_field": source_field,
                    "target_field": best_match["name"],
                    "confidence": round(best_score, 3),
                    "match_type": self._determine_match_type(best_score),
                    "target_info": best_match
                })
        
        # Sort by confidence
        mappings.sort(key=lambda x: x["confidence"], reverse=True)
        
        return mappings
    
    def _normalize_field_name(self, field_name: str) -> str:
        """Normalize field name for comparison"""
        # Convert to lowercase
        normalized = field_name.lower()
        
        # Replace common separators with space
        normalized = re.sub(r'[_\-\.]', ' ', normalized)
        
        # Remove extra spaces
        normalized = ' '.join(normalized.split())
        
        return normalized
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into words"""
        # Split on spaces and filter empty
        tokens = [t for t in text.split() if t]
        
        # Also split camelCase
        expanded_tokens = []
        for token in tokens:
            # Insert spaces before uppercase letters
            expanded = re.sub(r'([a-z])([A-Z])', r'\1 \2', token)
            expanded_tokens.extend(expanded.lower().split())
        
        return expanded_tokens
    
    def _calculate_token_similarity(
        self, 
        tokens1: List[str], 
        tokens2: List[str]
    ) -> float:
        """Calculate similarity between token lists"""
        if not tokens1 or not tokens2:
            return 0.0
        
        # Find common tokens
        common = set(tokens1).intersection(set(tokens2))
        
        # Jaccard similarity
        union = set(tokens1).union(set(tokens2))
        
        return len(common) / len(union) if union else 0.0
    
    def _calculate_semantic_similarity(
        self,
        source: str,
        target: str,
        description: str
    ) -> float:
        """Calculate semantic similarity (simplified)"""
        # Common field name synonyms
        synonyms = {
            "id": ["identifier", "key", "code"],
            "name": ["title", "label", "description"],
            "date": ["time", "timestamp", "datetime"],
            "user": ["person", "individual", "account"],
            "status": ["state", "condition", "phase"],
            "type": ["category", "class", "kind"],
            "value": ["amount", "quantity", "measure"],
            "location": ["address", "place", "site"]
        }
        
        source_lower = source.lower()
        target_lower = target.lower()
        
        # Check if source and target are synonyms
        for key, syns in synonyms.items():
            all_terms = [key] + syns
            if source_lower in all_terms and target_lower in all_terms:
                return 0.9
        
        # Check if description contains source field
        if description and source_lower in description.lower():
            return 0.7
        
        return 0.0
    
    def _determine_match_type(self, score: float) -> str:
        """Determine match type based on score"""
        if score >= 0.95:
            return "exact"
        elif score >= 0.8:
            return "strong"
        elif score >= 0.6:
            return "moderate"
        else:
            return "weak"