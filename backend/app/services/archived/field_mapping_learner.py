"""
Field Mapping Learner Service

Implements intelligent field mapping learning from user feedback.
Stores successful mappings and provides AI-powered suggestions for new fields.
"""

import logging
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

from app.services.learning_pattern_service import LearningPatternService
from app.services.embedding_service import EmbeddingService
from app.utils.vector_utils import VectorUtils

logger = logging.getLogger(__name__)


@dataclass
class MappingSuggestion:
    """Represents a field mapping suggestion with confidence."""
    target_field: str
    confidence: float
    reasoning: str
    pattern_id: Optional[str] = None
    sample_matches: List[str] = None


@dataclass
class FieldMappingResult:
    """Result of field mapping learning operation."""
    pattern_id: str
    confidence: float
    success: bool
    message: str


class FieldMappingLearner:
    """Service for learning and suggesting field mappings."""
    
    def __init__(self):
        self.learning_service = LearningPatternService()
        self.embedding_service = EmbeddingService()
        self.vector_utils = VectorUtils()
    
    async def learn_from_mapping(
        self,
        source_field: str,
        target_field: str,
        sample_values: List[str],
        client_account_id: str,
        success: bool = True,
        engagement_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> FieldMappingResult:
        """
        Learn from a field mapping operation.
        
        Args:
            source_field: Source field name
            target_field: Target field name  
            sample_values: Sample values from the source field
            client_account_id: Client account ID
            success: Whether the mapping was successful
            engagement_id: Optional engagement ID
            user_id: Optional user ID who made the mapping
            
        Returns:
            FieldMappingResult with operation details
        """
        try:
            # Prepare pattern data
            pattern_data = {
                "client_account_id": client_account_id,
                "engagement_id": engagement_id,
                "source_field_name": source_field,
                "target_field_name": target_field,
                "sample_values": sample_values[:10],  # Limit to first 10 samples
                "pattern_context": {
                    "sample_count": len(sample_values),
                    "mapping_timestamp": datetime.utcnow().isoformat(),
                    "success": success
                },
                "confidence_score": 0.8 if success else 0.2,  # Initial confidence based on success
                "learning_source": "user_feedback",
                "created_by": user_id
            }
            
            # Store the pattern
            pattern_id = await self.learning_service.store_pattern(
                pattern_data, 
                pattern_type="mapping"
            )
            
            # Update existing similar patterns if this was successful
            if success:
                await self._update_similar_patterns(
                    source_field, 
                    target_field, 
                    sample_values, 
                    client_account_id
                )
            
            logger.info(f"Learned mapping: {source_field} -> {target_field} (success: {success})")
            
            return FieldMappingResult(
                pattern_id=pattern_id,
                confidence=pattern_data["confidence_score"],
                success=True,
                message=f"Successfully learned mapping pattern for {source_field}"
            )
            
        except Exception as e:
            logger.error(f"Error learning from mapping: {e}")
            return FieldMappingResult(
                pattern_id="",
                confidence=0.0,
                success=False,
                message=f"Failed to learn mapping: {str(e)}"
            )
    
    async def suggest_field_mappings(
        self,
        source_fields: List[str],
        sample_data: Dict[str, List[str]],
        client_account_id: str,
        engagement_id: Optional[str] = None,
        max_suggestions: int = 3
    ) -> Dict[str, List[MappingSuggestion]]:
        """
        Suggest field mappings for source fields based on learned patterns.
        
        Args:
            source_fields: List of source field names
            sample_data: Dictionary mapping field names to sample values
            client_account_id: Client account ID
            engagement_id: Optional engagement ID
            max_suggestions: Maximum suggestions per field
            
        Returns:
            Dictionary mapping source fields to lists of suggestions
        """
        try:
            suggestions = {}
            
            for field in source_fields:
                field_suggestions = await self._suggest_for_field(
                    field,
                    sample_data.get(field, []),
                    client_account_id,
                    max_suggestions
                )
                suggestions[field] = field_suggestions
            
            logger.debug(f"Generated suggestions for {len(source_fields)} fields")
            return suggestions
            
        except Exception as e:
            logger.error(f"Error suggesting field mappings: {e}")
            return {}
    
    async def _suggest_for_field(
        self,
        source_field: str,
        sample_values: List[str],
        client_account_id: str,
        max_suggestions: int
    ) -> List[MappingSuggestion]:
        """Generate suggestions for a single field."""
        try:
            # Create search text combining field name and sample values
            sample_text = " ".join(str(v) for v in sample_values[:5]) if sample_values else ""
            search_text = f"{source_field} {sample_text}".strip()
            
            # Find similar patterns
            similar_patterns = await self.learning_service.find_similar_patterns(
                search_text,
                client_account_id,
                pattern_type="mapping",
                limit=max_suggestions * 2,  # Get more to filter
                similarity_threshold=0.5
            )
            
            # Convert patterns to suggestions
            suggestions = []
            seen_targets = set()
            
            for pattern, similarity in similar_patterns:
                if len(suggestions) >= max_suggestions:
                    break
                
                # Skip if we already have a suggestion for this target
                if pattern.target_field_name in seen_targets:
                    continue
                
                # Calculate confidence based on similarity and pattern performance
                base_confidence = similarity
                pattern_confidence = pattern.confidence_score if pattern.confidence_score else 0.5
                combined_confidence = (base_confidence + pattern_confidence) / 2
                
                # Generate reasoning
                reasoning = self._generate_reasoning(
                    source_field, 
                    pattern, 
                    similarity, 
                    sample_values
                )
                
                suggestion = MappingSuggestion(
                    target_field=pattern.target_field_name,
                    confidence=combined_confidence,
                    reasoning=reasoning,
                    pattern_id=str(pattern.id),
                    sample_matches=self._find_sample_matches(sample_values, pattern)
                )
                
                suggestions.append(suggestion)
                seen_targets.add(pattern.target_field_name)
            
            # Sort by confidence
            suggestions.sort(key=lambda x: x.confidence, reverse=True)
            
            # Add fallback suggestions if we don't have enough
            if len(suggestions) < max_suggestions:
                fallback_suggestions = self._generate_fallback_suggestions(
                    source_field, 
                    sample_values,
                    max_suggestions - len(suggestions)
                )
                suggestions.extend(fallback_suggestions)
            
            return suggestions[:max_suggestions]
            
        except Exception as e:
            logger.error(f"Error generating suggestions for field {source_field}: {e}")
            return []
    
    def _generate_reasoning(
        self,
        source_field: str,
        pattern: Any,
        similarity: float,
        sample_values: List[str]
    ) -> str:
        """Generate human-readable reasoning for a suggestion."""
        reasons = []
        
        # Field name similarity
        if similarity > 0.8:
            reasons.append(f"Field name '{source_field}' is very similar to learned pattern")
        elif similarity > 0.6:
            reasons.append(f"Field name '{source_field}' matches learned pattern")
        
        # Pattern success rate
        if hasattr(pattern, 'success_count') and hasattr(pattern, 'failure_count'):
            total_uses = pattern.success_count + pattern.failure_count
            if total_uses > 0:
                success_rate = pattern.success_count / total_uses
                if success_rate > 0.8:
                    reasons.append(f"Pattern has high success rate ({success_rate:.1%})")
                elif success_rate > 0.6:
                    reasons.append(f"Pattern has good success rate ({success_rate:.1%})")
        
        # Sample value analysis
        if sample_values and hasattr(pattern, 'source_sample_values') and pattern.source_sample_values:
            # Simple check for similar sample patterns
            if any(str(v).lower() in str(pattern.source_sample_values).lower() for v in sample_values[:3]):
                reasons.append("Sample values match learned patterns")
        
        # Learning source
        if hasattr(pattern, 'learning_source'):
            if pattern.learning_source == "user_feedback":
                reasons.append("Based on previous user mappings")
            elif pattern.learning_source == "synthetic":
                reasons.append("Based on AI-generated patterns")
        
        return "; ".join(reasons) if reasons else "Based on field name similarity"
    
    def _find_sample_matches(
        self,
        sample_values: List[str],
        pattern: Any
    ) -> List[str]:
        """Find sample values that match the pattern."""
        if not sample_values or not hasattr(pattern, 'source_sample_values') or not pattern.source_sample_values:
            return []
        
        matches = []
        pattern_samples = [str(v).lower() for v in pattern.source_sample_values]
        
        for value in sample_values[:5]:  # Check first 5 samples
            value_str = str(value).lower()
            if any(value_str in pattern_sample or pattern_sample in value_str for pattern_sample in pattern_samples):
                matches.append(str(value))
        
        return matches[:3]  # Return up to 3 matches
    
    def _generate_fallback_suggestions(
        self,
        source_field: str,
        sample_values: List[str],
        count: int
    ) -> List[MappingSuggestion]:
        """Generate fallback suggestions using heuristics."""
        fallback_mappings = {
            # Common field name patterns
            "id": ["asset_id", "identifier", "id"],
            "name": ["asset_name", "name", "hostname"],
            "type": ["asset_type", "type", "category"],
            "ip": ["ip_address", "primary_ip", "network_address"],
            "os": ["operating_system", "os_type", "platform"],
            "cpu": ["cpu_cores", "processor", "cpu_count"],
            "memory": ["memory_gb", "ram", "memory_size"],
            "disk": ["storage_gb", "disk_space", "storage_size"],
            "env": ["environment", "env_type", "deployment_env"],
            "owner": ["owner", "responsible_party", "asset_owner"],
            "location": ["location", "datacenter", "site"],
            "status": ["status", "state", "operational_status"],
            "criticality": ["business_criticality", "criticality", "importance"],
            "app": ["application_name", "application", "app_name"],
            "version": ["version", "software_version", "app_version"]
        }
        
        suggestions = []
        source_lower = source_field.lower()
        
        for pattern, targets in fallback_mappings.items():
            if pattern in source_lower and len(suggestions) < count:
                for target in targets:
                    if len(suggestions) >= count:
                        break
                    
                    # Calculate confidence based on pattern match quality
                    if source_lower == pattern:
                        confidence = 0.7
                    elif source_lower.startswith(pattern) or source_lower.endswith(pattern):
                        confidence = 0.6
                    else:
                        confidence = 0.5
                    
                    suggestion = MappingSuggestion(
                        target_field=target,
                        confidence=confidence,
                        reasoning=f"Heuristic mapping based on field name pattern '{pattern}'",
                        pattern_id=None,
                        sample_matches=[]
                    )
                    suggestions.append(suggestion)
        
        return suggestions
    
    async def _update_similar_patterns(
        self,
        source_field: str,
        target_field: str,
        sample_values: List[str],
        client_account_id: str
    ) -> None:
        """Update confidence of similar existing patterns."""
        try:
            # Find similar patterns
            search_text = f"{source_field} {' '.join(str(v) for v in sample_values[:3])}"
            similar_patterns = await self.learning_service.find_similar_patterns(
                search_text,
                client_account_id,
                pattern_type="mapping",
                limit=5,
                similarity_threshold=0.7
            )
            
            # Update patterns that map to the same target
            for pattern, similarity in similar_patterns:
                if pattern.target_field_name == target_field:
                    # This confirms the pattern is good
                    await self.learning_service.update_pattern_confidence(
                        str(pattern.id),
                        was_successful=True,
                        pattern_type="mapping"
                    )
                    logger.debug(f"Updated confidence for similar pattern {pattern.id}")
            
        except Exception as e:
            logger.error(f"Error updating similar patterns: {e}")
    
    async def get_mapping_statistics(
        self,
        client_account_id: str
    ) -> Dict[str, Any]:
        """Get statistics about field mapping patterns."""
        try:
            stats = await self.learning_service.get_pattern_statistics(
                client_account_id,
                pattern_type="mapping"
            )
            
            # Add mapping-specific statistics
            stats["mapping_specific"] = {
                "most_common_targets": await self._get_common_targets(client_account_id),
                "recent_mappings": await self._get_recent_mappings(client_account_id),
                "accuracy_trend": "improving"  # Placeholder for trend analysis
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting mapping statistics: {e}")
            return {"error": str(e)}
    
    async def _get_common_targets(self, client_account_id: str) -> List[Dict[str, Any]]:
        """Get most commonly mapped target fields."""
        # This would query the database for target field frequency
        # Placeholder implementation
        return [
            {"field": "asset_name", "count": 15},
            {"field": "ip_address", "count": 12},
            {"field": "operating_system", "count": 10},
            {"field": "asset_type", "count": 8},
            {"field": "environment", "count": 6}
        ]
    
    async def _get_recent_mappings(self, client_account_id: str) -> List[Dict[str, Any]]:
        """Get recent mapping activities."""
        # This would query recent patterns
        # Placeholder implementation
        return [
            {"source": "SERVER_NAME", "target": "asset_name", "confidence": 0.9, "timestamp": "2024-01-15T10:30:00Z"},
            {"source": "IP_ADDR", "target": "ip_address", "confidence": 0.95, "timestamp": "2024-01-15T10:25:00Z"},
            {"source": "OS_TYPE", "target": "operating_system", "confidence": 0.85, "timestamp": "2024-01-15T10:20:00Z"}
        ]


# Global instance for easy access
field_mapping_learner = FieldMappingLearner() 