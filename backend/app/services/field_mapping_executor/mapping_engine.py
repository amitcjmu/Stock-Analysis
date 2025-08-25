"""
Field Mapping Engine Module

Handles field mapping logic and transformations using AI-powered embeddings,
pattern learning, and fuzzy string matching for intelligent field mapping.

This module provides a centralized interface to various mapping engines.
The actual implementations are modularized into separate files for maintainability.
"""

import logging
from typing import Any, Dict

# Import utility classes directly
from .mapping_utilities import (
    FieldMappingRule,
    FieldSimilarityCalculator,
    MappingContext,
    StandardFieldRegistry,
)

logger = logging.getLogger(__name__)


def _get_intelligent_mapping_engine():
    """Lazy import of IntelligentMappingEngine to prevent import-time errors"""
    try:
        from .intelligent_engines import IntelligentMappingEngine
        return IntelligentMappingEngine
    except ImportError as e:
        logger.warning(f"Could not import IntelligentMappingEngine: {e}")
        return None


# Make IntelligentMappingEngine available through lazy loading
def __getattr__(name):
    """Lazy loading of IntelligentMappingEngine for backward compatibility"""
    if name == "IntelligentMappingEngine":
        engine_class = _get_intelligent_mapping_engine()
        if engine_class is None:
            raise ImportError(f"Could not import {name}. Check if required dependencies are installed.")
        return engine_class
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


class MappingEngine:
    """Base mapping engine with simple pattern matching"""

    def __init__(self):
        self.mappings = {}
        self.logger = logger

    def apply_mapping(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply simple mapping transformations to data"""
        if not self.mappings:
            return data

        mapped_data = {}
        for key, value in data.items():
            # Apply mapping if exists, otherwise keep original key
            mapped_key = self.mappings.get(key, key)
            mapped_data[mapped_key] = value

        return mapped_data


class FallbackMappingEngine(MappingEngine):
    """Fallback mapping engine for when AI services are unavailable"""

    def __init__(self):
        super().__init__()
        self.field_registry = StandardFieldRegistry()
        self.similarity_calculator = FieldSimilarityCalculator()

    async def create_basic_mappings(
        self, source_fields: list, target_fields: list
    ) -> Dict[str, str]:
        """Create basic mappings using string similarity"""
        mappings = {}

        for source_field in source_fields:
            best_match = None
            best_score = 0.0

            # Check against target fields
            for target_field in target_fields:
                try:
                    similarity = await self.similarity_calculator.calculate_similarity(
                        source_field, target_field
                    )
                    if similarity > best_score and similarity > 0.6:
                        best_score = similarity
                        best_match = target_field
                except Exception as e:
                    self.logger.error(f"Error calculating similarity: {e}")
                    continue

            # Check against standard field registry
            standard_field = self.field_registry.get_standard_field(source_field)
            if standard_field and (not best_match or best_score < 0.8):
                # Prefer standard field mappings for lower confidence matches
                if standard_field in target_fields:
                    best_match = standard_field
                    best_score = 0.9

            if best_match:
                mappings[source_field] = best_match

        return mappings

    def get_confidence_scores(self, mappings: Dict[str, str]) -> Dict[str, float]:
        """Get confidence scores for fallback mappings"""
        confidence_scores = {}
        for source_field, target_field in mappings.items():
            # Use a simple heuristic based on field registry knowledge
            if self.field_registry.is_standard_field(source_field):
                confidence_scores[source_field] = 0.8
            else:
                confidence_scores[source_field] = 0.6
        return confidence_scores


# Export all classes for backward compatibility
# Note: IntelligentMappingEngine is available through lazy loading via __getattr__
__all__ = [
    "MappingEngine",
    "FallbackMappingEngine",
    "FieldMappingRule",
    "MappingContext",
    "FieldSimilarityCalculator",
    "StandardFieldRegistry",
]
