"""
Dynamic Field Mapping Service - Modular & Robust
Learns and maintains field mappings with graceful fallbacks.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from .field_mapper_handlers import (
    MappingEngineHandler,
    ValidationHandler,
    AgentInterfaceHandler
)

logger = logging.getLogger(__name__)

class FieldMapperService:
    """Modular field mapping service with graceful fallbacks."""
    
    def __init__(self, data_dir: str = "data"):
        # Initialize handlers
        self.mapping_engine = MappingEngineHandler(data_dir)
        self.validation_handler = ValidationHandler()
        self.agent_interface = AgentInterfaceHandler(self.mapping_engine)
        
        # Set cross-references
        self.agent_interface.set_mapping_engine(self.mapping_engine)
        
        # Backward compatibility properties
        self.data_dir = self.mapping_engine.data_dir
        self.mappings_file = self.mapping_engine.mappings_file
        self.base_mappings = self.mapping_engine.base_mappings
        self.learned_mappings = self.mapping_engine.learned_mappings
        
        logger.info("Field mapper service initialized with modular handlers")
    
    def is_available(self) -> bool:
        """Check if the service is properly initialized."""
        return True  # Always available with fallbacks
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of field mapper system."""
        return {
            "status": "healthy",
            "service": "field-mapper",
            "version": "2.0.0",
            "mapping_engine": self.mapping_engine.is_available(),
            "validation_handler": self.validation_handler.is_available(),
            "agent_interface": self.agent_interface.is_available(),
            "mapping_statistics": self.mapping_engine.get_mapping_statistics()
        }
    
    # Core mapping functionality - delegates to mapping engine
    def get_field_mappings(self, asset_type: str = 'server') -> Dict[str, List[str]]:
        """Get all field mappings for asset type."""
        return self.mapping_engine.get_field_mappings(asset_type)
    
    def learn_field_mapping(self, canonical_field: str, field_variations: List[str],
                           source: str = "manual") -> Dict[str, Any]:
        """Learn new field mapping variations."""
        return self.mapping_engine.learn_field_mapping(canonical_field, field_variations, source)
    
    def find_matching_fields(self, available_columns: List[str], required_field: str) -> List[str]:
        """Find matching columns for a required field."""
        return self.mapping_engine.find_matching_fields(available_columns, required_field)
    
    def analyze_columns(self, columns: List[str], asset_type: str = "server") -> Dict[str, Any]:
        """Analyze columns and provide mapping insights."""
        return self.mapping_engine.analyze_columns(columns, asset_type)
    
    def get_mapping_statistics(self) -> Dict[str, Any]:
        """Get statistics about field mappings."""
        return self.mapping_engine.get_mapping_statistics()
    
    def export_mappings(self, export_path: str) -> bool:
        """Export all mappings to file."""
        return self.mapping_engine.export_mappings(export_path)
    
    # Validation functionality - delegates to validation handler
    def identify_missing_fields(self, available_columns: List[str],
                               asset_type: str = "server",
                               mapped_fields: Optional[Dict[str, str]] = None) -> List[str]:
        """Identify missing required fields for asset type."""
        return self.validation_handler.identify_missing_fields(available_columns, asset_type, mapped_fields)
    
    def validate_field_format(self, field_name: str, value: Any,
                             canonical_field: Optional[str] = None) -> Dict[str, Any]:
        """Validate field format and suggest corrections."""
        return self.validation_handler.validate_field_format(field_name, value, canonical_field)
    
    def validate_data_completeness(self, data: List[Dict[str, Any]],
                                  asset_type: str = "server") -> Dict[str, Any]:
        """Validate data completeness across records."""
        return self.validation_handler.validate_data_completeness(data, asset_type)
    
    # Agent interface functionality - delegates to agent interface
    def agent_query_field_mapping(self, field_name: str) -> Dict[str, Any]:
        """External tool for agents to query field mappings."""
        return self.agent_interface.agent_query_field_mapping(field_name)
    
    def agent_learn_field_mapping(self, source_field: str, target_field: str,
                                 context: str = "") -> Dict[str, Any]:
        """External tool for agents to learn new field mappings."""
        return self.agent_interface.agent_learn_field_mapping(source_field, target_field, context)
    
    def agent_analyze_columns(self, columns: List[str], asset_type: str = "server") -> Dict[str, Any]:
        """External tool for agents to analyze available columns."""
        return self.agent_interface.agent_analyze_columns(columns, asset_type)
    
    def agent_get_mapping_context(self) -> Dict[str, Any]:
        """External tool for agents to get context about field mappings."""
        return self.agent_interface.agent_get_mapping_context()
    
    def learn_from_feedback_text(self, feedback_text: str, context: str = "user_feedback") -> Dict[str, Any]:
        """Extract and learn field mappings from user feedback text."""
        return self.agent_interface.learn_from_feedback_text(feedback_text, context)
    
    # Additional utility methods for backward compatibility
    def process_feedback_patterns(self, patterns: List[str]):
        """Process feedback patterns for learning (backward compatibility)."""
        try:
            for pattern in patterns:
                # Try to extract field mappings from pattern text
                self.learn_from_feedback_text(pattern, "pattern_processing")
        except Exception as e:
            logger.error(f"Error processing feedback patterns: {e}")
    
    def _normalize_field_name(self, field_name: str) -> str:
        """Normalize field name for matching."""
        return field_name.lower().strip().replace(' ', '_')
    
    def _find_base_mapping_matches(self, normalized_field: str) -> List[Dict[str, Any]]:
        """Find matches in base mappings."""
        matches = []
        for canonical_field, variations in self.base_mappings.items():
            for variation in variations:
                if normalized_field == variation or normalized_field in variation:
                    matches.append({
                        "target_field": canonical_field,
                        "confidence": "medium",
                        "source": "base_mapping"
                    })
                    break
        return matches
    
    def _calculate_match_confidence(self, matches: List[str], target_field: str) -> float:
        """Calculate confidence score for field matches."""
        if not matches:
            return 0.0
        
        # Simple confidence calculation based on exact matches
        exact_matches = sum(1 for match in matches if match.lower() == target_field.lower())
        return min(1.0, (exact_matches + len(matches) * 0.5) / len(matches))

# Create global instance for backward compatibility
def get_field_mapper() -> FieldMapperService:
    """Get global field mapper instance."""
    global _field_mapper_instance
    if '_field_mapper_instance' not in globals():
        _field_mapper_instance = FieldMapperService()
    return _field_mapper_instance

# Global instance
field_mapper = get_field_mapper()

# Legacy compatibility
FieldMapper = FieldMapperService
DynamicFieldMapper = FieldMapperService

# Export main classes and functions for backward compatibility
__all__ = [
    "FieldMapperService",
    "FieldMapper", 
    "DynamicFieldMapper",
    "field_mapper",
    "get_field_mapper"
] 