"""
Field Similarity Tool for advanced field comparison and scoring
"""

import json
import logging
import re
from difflib import SequenceMatcher
from typing import Any, Dict, List, Tuple

from app.services.tools.base_tool import AsyncBaseDiscoveryTool
from app.services.tools.registry import ToolMetadata

logger = logging.getLogger(__name__)

class FieldSimilarityTool(AsyncBaseDiscoveryTool):
    """Advanced field similarity analysis using multiple algorithms"""
    
    name: str = "field_similarity"
    description: str = "Calculate field similarity using multiple algorithms and pattern matching"
    
    @classmethod
    def tool_metadata(cls) -> ToolMetadata:
        return ToolMetadata(
            name="field_similarity",
            description="Multi-algorithm field similarity analysis",
            tool_class=cls,
            categories=["analysis", "mapping", "comparison"],
            required_params=["field1", "field2"],
            optional_params=["algorithms", "context_data"],
            context_aware=True,
            async_tool=True
        )
    
    async def arun(
        self,
        field1: str,
        field2: str,
        algorithms: List[str] = None,
        context_data: List[Dict[str, Any]] = None
    ) -> str:
        """
        Calculate similarity between two fields using multiple algorithms.
        
        Args:
            field1: First field name to compare
            field2: Second field name to compare
            algorithms: List of algorithms to use (default: all)
            context_data: Sample data for context-aware comparison
            
        Returns:
            JSON string with similarity analysis results
        """
        try:
            if algorithms is None:
                algorithms = [
                    "lexical", "semantic", "structural", 
                    "phonetic", "contextual", "pattern"
                ]
            
            similarities = {}
            
            # Lexical similarity (string-based)
            if "lexical" in algorithms:
                similarities["lexical"] = self._calculate_lexical_similarity(field1, field2)
            
            # Semantic similarity (meaning-based)
            if "semantic" in algorithms:
                similarities["semantic"] = await self._calculate_semantic_similarity(field1, field2)
            
            # Structural similarity (format-based)
            if "structural" in algorithms:
                similarities["structural"] = self._calculate_structural_similarity(field1, field2)
            
            # Phonetic similarity (sound-based)
            if "phonetic" in algorithms:
                similarities["phonetic"] = self._calculate_phonetic_similarity(field1, field2)
            
            # Contextual similarity (data-based)
            if "contextual" in algorithms and context_data:
                similarities["contextual"] = self._calculate_contextual_similarity(
                    field1, field2, context_data
                )
            
            # Pattern similarity (regex-based)
            if "pattern" in algorithms:
                similarities["pattern"] = self._calculate_pattern_similarity(field1, field2)
            
            # Calculate weighted overall similarity
            overall_similarity = self._calculate_overall_similarity(similarities)
            
            result = {
                "field1": field1,
                "field2": field2,
                "similarities": similarities,
                "overall_similarity": overall_similarity,
                "confidence": self._calculate_confidence(similarities),
                "match_recommendation": self._get_match_recommendation(overall_similarity),
                "analysis": self._generate_analysis(field1, field2, similarities)
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Field similarity calculation failed: {e}")
            return json.dumps({
                "error": str(e),
                "field1": field1,
                "field2": field2,
                "overall_similarity": 0.0
            })
    
    def _calculate_lexical_similarity(self, field1: str, field2: str) -> float:
        """Calculate lexical similarity using string matching"""
        # Normalize fields
        norm1 = self._normalize_field_name(field1)
        norm2 = self._normalize_field_name(field2)
        
        # Multiple lexical metrics
        metrics = []
        
        # 1. Sequence matcher ratio
        metrics.append(SequenceMatcher(None, norm1, norm2).ratio())
        
        # 2. Exact match
        if norm1 == norm2:
            metrics.append(1.0)
        else:
            metrics.append(0.0)
        
        # 3. Contains match
        if norm1 in norm2 or norm2 in norm1:
            metrics.append(0.8)
        else:
            metrics.append(0.0)
        
        # 4. Word overlap
        words1 = set(norm1.split())
        words2 = set(norm2.split())
        if words1 and words2:
            overlap = len(words1.intersection(words2)) / len(words1.union(words2))
            metrics.append(overlap)
        else:
            metrics.append(0.0)
        
        return max(metrics)
    
    async def _calculate_semantic_similarity(self, field1: str, field2: str) -> float:
        """Calculate semantic similarity using embeddings"""
        try:
            # Try to use embedding service if available
            from app.services.embedding_service import EmbeddingService
            embedding_service = EmbeddingService()
            
            # Prepare field names for embedding
            text1 = self._field_to_text(field1)
            text2 = self._field_to_text(field2)
            
            # Get embeddings
            embeddings = await embedding_service.get_embeddings([text1, text2])
            
            if len(embeddings) == 2:
                # Calculate cosine similarity
                import numpy as np
                vec1 = np.array(embeddings[0])
                vec2 = np.array(embeddings[1])
                
                cosine_sim = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
                return float(cosine_sim)
            
        except Exception as e:
            logger.debug(f"Semantic similarity fallback: {e}")
        
        # Fallback to simple semantic rules
        return self._simple_semantic_similarity(field1, field2)
    
    def _calculate_structural_similarity(self, field1: str, field2: str) -> float:
        """Calculate structural similarity based on naming patterns"""
        patterns = {
            "snake_case": re.compile(r'^[a-z]+(_[a-z]+)*$'),
            "camelCase": re.compile(r'^[a-z]+([A-Z][a-z]*)*$'),
            "PascalCase": re.compile(r'^[A-Z][a-z]*([A-Z][a-z]*)*$'),
            "kebab-case": re.compile(r'^[a-z]+(-[a-z]+)*$'),
            "UPPER_CASE": re.compile(r'^[A-Z]+(_[A-Z]+)*$')
        }
        
        pattern1 = None
        pattern2 = None
        
        for name, pattern in patterns.items():
            if pattern.match(field1):
                pattern1 = name
            if pattern.match(field2):
                pattern2 = name
        
        # Same pattern structure
        if pattern1 and pattern2 and pattern1 == pattern2:
            return 0.8
        
        # Similar length and character distribution
        len_similarity = 1.0 - abs(len(field1) - len(field2)) / max(len(field1), len(field2))
        
        # Character type similarity
        char_types1 = self._get_character_types(field1)
        char_types2 = self._get_character_types(field2)
        
        type_similarity = len(char_types1.intersection(char_types2)) / len(char_types1.union(char_types2))
        
        return (len_similarity + type_similarity) / 2
    
    def _calculate_phonetic_similarity(self, field1: str, field2: str) -> float:
        """Calculate phonetic similarity using Soundex-like algorithm"""
        def simple_soundex(word):
            word = word.upper()
            soundex = word[0] if word else ''
            
            # Mapping for consonants
            mapping = {
                'B': '1', 'F': '1', 'P': '1', 'V': '1',
                'C': '2', 'G': '2', 'J': '2', 'K': '2', 'Q': '2', 'S': '2', 'X': '2', 'Z': '2',
                'D': '3', 'T': '3',
                'L': '4',
                'M': '5', 'N': '5',
                'R': '6'
            }
            
            for char in word[1:]:
                if char in mapping:
                    soundex += mapping[char]
            
            return soundex[:4].ljust(4, '0')
        
        # Clean field names for phonetic comparison
        clean1 = re.sub(r'[^A-Za-z]', '', field1)
        clean2 = re.sub(r'[^A-Za-z]', '', field2)
        
        if not clean1 or not clean2:
            return 0.0
        
        soundex1 = simple_soundex(clean1)
        soundex2 = simple_soundex(clean2)
        
        return 1.0 if soundex1 == soundex2 else 0.0
    
    def _calculate_contextual_similarity(
        self, 
        field1: str, 
        field2: str, 
        context_data: List[Dict[str, Any]]
    ) -> float:
        """Calculate similarity based on data context"""
        # Extract values for both fields from context data
        values1 = []
        values2 = []
        
        for record in context_data[:100]:  # Limit to first 100 records
            if field1 in record:
                values1.append(str(record[field1]))
            if field2 in record:
                values2.append(str(record[field2]))
        
        if not values1 or not values2:
            return 0.0
        
        similarities = []
        
        # 1. Data type similarity
        types1 = set(type(v).__name__ for v in values1[:10])
        types2 = set(type(v).__name__ for v in values2[:10])
        type_sim = len(types1.intersection(types2)) / len(types1.union(types2))
        similarities.append(type_sim)
        
        # 2. Value pattern similarity
        patterns1 = self._extract_value_patterns(values1[:20])
        patterns2 = self._extract_value_patterns(values2[:20])
        pattern_sim = len(patterns1.intersection(patterns2)) / len(patterns1.union(patterns2))
        similarities.append(pattern_sim)
        
        # 3. Value overlap
        set1 = set(values1[:50])
        set2 = set(values2[:50])
        if set1 and set2:
            overlap_sim = len(set1.intersection(set2)) / len(set1.union(set2))
            similarities.append(overlap_sim)
        
        return max(similarities) if similarities else 0.0
    
    def _calculate_pattern_similarity(self, field1: str, field2: str) -> float:
        """Calculate similarity based on common field patterns"""
        # Common field patterns
        patterns = {
            "id_field": r".*(?:id|key|identifier).*",
            "name_field": r".*(?:name|title|label).*",
            "date_field": r".*(?:date|time|created|updated|modified).*",
            "address_field": r".*(?:address|location|street|city).*",
            "contact_field": r".*(?:phone|email|contact).*",
            "status_field": r".*(?:status|state|condition).*",
            "type_field": r".*(?:type|category|class|kind).*",
            "count_field": r".*(?:count|number|num|qty|quantity).*"
        }
        
        matches1 = set()
        matches2 = set()
        
        field1_lower = field1.lower()
        field2_lower = field2.lower()
        
        for pattern_name, pattern in patterns.items():
            if re.match(pattern, field1_lower):
                matches1.add(pattern_name)
            if re.match(pattern, field2_lower):
                matches2.add(pattern_name)
        
        if matches1 and matches2:
            return len(matches1.intersection(matches2)) / len(matches1.union(matches2))
        
        return 0.0
    
    def _calculate_overall_similarity(self, similarities: Dict[str, float]) -> float:
        """Calculate weighted overall similarity"""
        weights = {
            "lexical": 0.25,
            "semantic": 0.30,
            "structural": 0.15,
            "phonetic": 0.10,
            "contextual": 0.15,
            "pattern": 0.20
        }
        
        # Normalize weights for available similarities
        available_weights = {k: v for k, v in weights.items() if k in similarities}
        total_weight = sum(available_weights.values())
        
        if total_weight == 0:
            return 0.0
        
        weighted_sum = sum(
            similarities[algo] * (weight / total_weight)
            for algo, weight in available_weights.items()
        )
        
        return round(weighted_sum, 3)
    
    def _calculate_confidence(self, similarities: Dict[str, float]) -> float:
        """Calculate confidence in the similarity score"""
        # More algorithms = higher confidence
        algorithm_confidence = len(similarities) / 6  # 6 total algorithms
        
        # Consistency across algorithms
        if len(similarities) > 1:
            values = list(similarities.values())
            avg = sum(values) / len(values)
            variance = sum((v - avg) ** 2 for v in values) / len(values)
            consistency = 1.0 - min(variance, 1.0)
        else:
            consistency = 0.5
        
        return round((algorithm_confidence + consistency) / 2, 3)
    
    def _get_match_recommendation(self, similarity: float) -> str:
        """Get recommendation based on similarity score"""
        if similarity >= 0.9:
            return "Strong match - high confidence"
        elif similarity >= 0.7:
            return "Good match - recommend with review"
        elif similarity >= 0.5:
            return "Possible match - requires validation"
        elif similarity >= 0.3:
            return "Weak match - manual review needed"
        else:
            return "No match - different fields"
    
    def _generate_analysis(self, field1: str, field2: str, similarities: Dict[str, float]) -> str:
        """Generate human-readable analysis"""
        analysis_parts = []
        
        # Highest similarity factor
        if similarities:
            best_algo = max(similarities.items(), key=lambda x: x[1])
            analysis_parts.append(f"Strongest similarity: {best_algo[0]} ({best_algo[1]:.3f})")
        
        # Specific observations
        if "lexical" in similarities and similarities["lexical"] > 0.8:
            analysis_parts.append("High lexical similarity - similar text structure")
        
        if "semantic" in similarities and similarities["semantic"] > 0.7:
            analysis_parts.append("High semantic similarity - similar meaning")
        
        if "pattern" in similarities and similarities["pattern"] > 0.5:
            analysis_parts.append("Similar field patterns detected")
        
        return " | ".join(analysis_parts) if analysis_parts else "No significant similarities found"
    
    # Helper methods
    def _normalize_field_name(self, field: str) -> str:
        """Normalize field name for comparison"""
        # Convert to lowercase and replace separators with spaces
        normalized = field.lower()
        normalized = re.sub(r'[_\-\.]', ' ', normalized)
        # Split camelCase
        normalized = re.sub(r'([a-z])([A-Z])', r'\1 \2', normalized)
        return normalized.strip()
    
    def _field_to_text(self, field: str) -> str:
        """Convert field name to descriptive text"""
        text = self._normalize_field_name(field)
        # Add context words
        context_mappings = {
            'id': 'identifier',
            'num': 'number',
            'qty': 'quantity',
            'addr': 'address',
            'tel': 'telephone',
            'desc': 'description'
        }
        
        for abbrev, full in context_mappings.items():
            text = text.replace(abbrev, full)
        
        return text
    
    def _simple_semantic_similarity(self, field1: str, field2: str) -> float:
        """Simple semantic similarity fallback"""
        # Common synonyms
        synonyms = {
            'name': ['title', 'label', 'identifier'],
            'id': ['key', 'identifier', 'code'],
            'type': ['category', 'class', 'kind'],
            'status': ['state', 'condition'],
            'date': ['time', 'timestamp'],
            'address': ['location', 'place']
        }
        
        norm1 = self._normalize_field_name(field1)
        norm2 = self._normalize_field_name(field2)
        
        for base_word, synonym_list in synonyms.items():
            if base_word in norm1 and any(syn in norm2 for syn in synonym_list):
                return 0.8
            if base_word in norm2 and any(syn in norm1 for syn in synonym_list):
                return 0.8
        
        return 0.0
    
    def _get_character_types(self, field: str) -> set:
        """Get character types present in field"""
        types = set()
        if any(c.islower() for c in field):
            types.add('lowercase')
        if any(c.isupper() for c in field):
            types.add('uppercase')
        if any(c.isdigit() for c in field):
            types.add('digits')
        if any(c in '_-.' for c in field):
            types.add('separators')
        return types
    
    def _extract_value_patterns(self, values: List[str]) -> set:
        """Extract patterns from data values"""
        patterns = set()
        
        for value in values:
            if not value:
                continue
                
            # Length patterns
            if len(value) < 5:
                patterns.add('short_text')
            elif len(value) > 50:
                patterns.add('long_text')
            
            # Content patterns
            if value.isdigit():
                patterns.add('numeric')
            if '@' in value:
                patterns.add('email_like')
            if re.match(r'\d{4}-\d{2}-\d{2}', value):
                patterns.add('date_like')
            if re.match(r'^\d+\.\d+\.\d+\.\d+$', value):
                patterns.add('ip_like')
        
        return patterns