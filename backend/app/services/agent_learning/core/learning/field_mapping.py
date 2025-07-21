"""
Field Mapping Learning Module - Handles field mapping patterns and suggestions
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import asdict
import uuid

from app.services.agent_learning.models import LearningContext, LearningPattern

logger = logging.getLogger(__name__)


class FieldMappingLearning:
    """Handles field mapping pattern learning and suggestions."""
    
    async def learn_field_mapping_pattern(
        self, 
        learning_data: Dict[str, Any],
        context: Optional[LearningContext] = None
    ):
        """Learn field mapping patterns with context isolation."""
        if not context:
            context = LearningContext()
        
        memory = self._get_context_memory(context)
        
        # Create learning pattern
        pattern = LearningPattern(
            pattern_id=f"field_mapping_{datetime.utcnow().timestamp()}",
            pattern_type="field_mapping",
            context=context,
            pattern_data={
                "original_field": learning_data.get("original_field"),
                "mapped_field": learning_data.get("mapped_field"),
                "field_type": learning_data.get("field_type"),
                "confidence_boost": learning_data.get("confidence_boost", 0.1),
                "validation_result": learning_data.get("validation_result", True)
            },
            confidence=learning_data.get("confidence", 0.8),
            usage_count=0,
            created_at=datetime.utcnow(),
            last_used=datetime.utcnow()
        )
        
        # Store in context-scoped patterns
        context_key = context.context_hash
        if context_key not in self.learning_patterns:
            self.learning_patterns[context_key] = []
        
        self.learning_patterns[context_key].append(pattern)
        
        # Add to memory
        memory.add_experience("learned_patterns", {
            "pattern_type": "field_mapping",
            "original_field": learning_data.get("original_field"),
            "mapped_field": learning_data.get("mapped_field"),
            "confidence": pattern.confidence,
            "context": asdict(context)
        })
        
        # Update global stats
        self.global_stats["field_mapping_patterns"] += 1
        self.global_stats["total_patterns"] += 1
        self.global_stats["total_learning_events"] += 1
        self.global_stats["last_updated"] = datetime.utcnow().isoformat()
        
        # Save patterns
        self._save_learning_patterns()
        
        logger.info(f"Learned field mapping pattern in context {context_key}: {learning_data.get('original_field')} -> {learning_data.get('mapped_field')}")
    
    async def suggest_field_mapping(
        self, 
        field_name: str, 
        context_data: Optional[Dict[str, Any]] = None,
        context: Optional[LearningContext] = None
    ) -> Dict[str, Any]:
        """Suggest field mapping based on context-scoped learning."""
        if not context:
            context = LearningContext()
        
        context_key = context.context_hash
        patterns = self.learning_patterns.get(context_key, [])
        
        # Find matching patterns
        matching_patterns = []
        for pattern in patterns:
            if pattern.pattern_type == "field_mapping":
                original_field = pattern.pattern_data.get("original_field", "").lower()
                if field_name.lower() in original_field or original_field in field_name.lower():
                    matching_patterns.append(pattern)
        
        if not matching_patterns:
            # Try global patterns if no context-specific patterns found
            for ctx_patterns in self.learning_patterns.values():
                for pattern in ctx_patterns:
                    if pattern.pattern_type == "field_mapping":
                        original_field = pattern.pattern_data.get("original_field", "").lower()
                        if field_name.lower() in original_field or original_field in field_name.lower():
                            matching_patterns.append(pattern)
                            break
        
        if matching_patterns:
            # Sort by confidence and usage
            best_pattern = max(matching_patterns, key=lambda p: (p.confidence, p.usage_count))
            
            # Update usage
            best_pattern.usage_count += 1
            best_pattern.last_used = datetime.utcnow()
            
            return {
                "suggested_mapping": best_pattern.pattern_data.get("mapped_field"),
                "confidence": best_pattern.confidence,
                "pattern_source": "context_specific" if context_key in self.learning_patterns else "global",
                "usage_count": best_pattern.usage_count
            }
        
        return {
            "suggested_mapping": None,
            "confidence": 0.0,
            "pattern_source": "none",
            "usage_count": 0
        }
    
    async def learn_from_field_mapping(
        self,
        source_field: str,
        target_field: str,
        sample_values: List[str],
        success: bool,
        context: Optional[LearningContext] = None
    ) -> Dict[str, Any]:
        """Learns from a field mapping operation."""
        if not context:
            context = LearningContext()
        
        try:
            pattern_data = {
                "context": context,
                "original_field": source_field,
                "mapped_field": target_field,
                "confidence": 0.8 if success else 0.2,
            }
            
            pattern_id = await self._store_mapping_pattern(pattern_data)
            
            return {
                "pattern_id": pattern_id,
                "confidence": pattern_data["confidence"],
                "success": True,
            }
        except Exception as e:
            logger.error(f"Error learning from mapping: {e}")
            return {"success": False, "error": str(e)}
    
    async def suggest_field_mappings(
        self,
        source_fields: List[str],
        sample_data: Dict[str, List[str]],
        context: Optional[LearningContext] = None,
        max_suggestions: int = 3
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Suggest field mappings for source fields based on learned patterns."""
        if not context:
            context = LearningContext()
            
        suggestions = {}
        for field in source_fields:
            search_text = f"{field} {' '.join(sample_data.get(field, []))}"
            similar_patterns = await self.vector_utils.find_similar_patterns(
                await self.embedding_service.embed_text(search_text),
                context.client_account_id,
                limit=max_suggestions
            )
            field_suggestions = []
            for pattern, similarity in similar_patterns:
                field_suggestions.append({
                    "target_field": pattern.target_field_name,
                    "confidence": (similarity + pattern.confidence_score) / 2,
                    "pattern_id": str(pattern.id)
                })
            suggestions[field] = field_suggestions
        return suggestions
    
    async def _store_mapping_pattern(self, pattern_data: Dict[str, Any]) -> str:
        """Store a field mapping pattern."""
        # MappingLearningPattern model removed in consolidation
        # TODO: Implement new pattern storage if needed
        logger.info("Mapping pattern storage skipped - model removed in consolidation")
        return str(uuid.uuid4())  # Return a dummy ID for now
    
    async def _update_field_mappings_from_feedback(self, patterns: List[str], context: LearningContext):
        """Update field mappings based on feedback patterns."""
        for pattern in patterns:
            if 'field mapping' in pattern.lower() or 'maps to' in pattern.lower():
                # Try to extract field mapping information from pattern
                # This is a simplified extraction - more sophisticated parsing could be added
                if 'should map' in pattern.lower():
                    # Extract field mapping suggestion and create learning pattern
                    await self.learn_field_mapping_pattern({
                        "original_field": "user_suggested_field",
                        "mapped_field": "user_suggested_mapping",
                        "field_type": "user_feedback",
                        "confidence_boost": 0.2,
                        "validation_result": True
                    }, context)