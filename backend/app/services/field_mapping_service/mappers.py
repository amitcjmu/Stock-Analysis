"""
Core field mapping logic for analyzing and finding field mappings.

This module contains the core logic for mapping analysis, learning,
and finding the best field mappings between source and target fields.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from uuid import UUID

from .base import (
    MappingAnalysis,
    MappingRule,
    BASE_MAPPINGS,
    REQUIRED_FIELDS,
    CONFIDENCE_THRESHOLDS,
    MAX_SUGGESTIONS,
    logger,
)


class FieldMappingAnalyzer:
    """Core field mapping analysis logic"""

    def __init__(
        self,
        learned_mappings_cache: Optional[Dict[str, List[MappingRule]]] = None,
        negative_mappings_cache: Optional[Set[tuple]] = None,
    ):
        self.learned_mappings_cache = learned_mappings_cache
        self.negative_mappings_cache = negative_mappings_cache or set()

    async def analyze_columns(
        self,
        columns: List[str],
        asset_type: str = "server",
        sample_data: Optional[List[List[Any]]] = None,
    ) -> MappingAnalysis:
        """
        Analyze columns and provide mapping insights.

        Args:
            columns: List of column names to analyze
            asset_type: Type of asset being analyzed
            sample_data: Optional sample data for content analysis

        Returns:
            MappingAnalysis with mapping suggestions and confidence scores
        """
        try:
            logger.debug(f"Analyzing {len(columns)} columns for {asset_type} assets")

            mapped_fields = {}
            unmapped_fields = []
            suggested_mappings = {}
            confidence_scores = {}

            for column in columns:
                normalized_column = self._normalize_field_name(column)

                # Try to find mapping
                mapping_result = await self._find_best_mapping(
                    normalized_column, asset_type, sample_data
                )

                if mapping_result:
                    mapped_fields[column] = mapping_result.target_field
                    confidence_scores[column] = mapping_result.confidence

                    # Add to suggestions if confidence is not perfect
                    if mapping_result.confidence < 1.0:
                        alternatives = await self._find_alternative_mappings(
                            normalized_column, mapping_result.target_field
                        )
                        if alternatives:
                            suggested_mappings[column] = alternatives
                else:
                    unmapped_fields.append(column)
                    confidence_scores[column] = 0.0

                    # Try to suggest possible mappings
                    suggestions = await self._suggest_mappings_for_field(
                        normalized_column, asset_type
                    )
                    if suggestions:
                        suggested_mappings[column] = suggestions

            # Identify missing required fields
            required_fields = REQUIRED_FIELDS.get(asset_type, [])
            mapped_field_values = set(mapped_fields.values())
            missing_required = [
                field for field in required_fields if field not in mapped_field_values
            ]

            # Calculate overall confidence
            overall_confidence = (
                sum(confidence_scores.values()) / len(confidence_scores)
                if confidence_scores
                else 0.0
            )

            return MappingAnalysis(
                mapped_fields=mapped_fields,
                unmapped_fields=unmapped_fields,
                suggested_mappings=suggested_mappings,
                confidence_scores=confidence_scores,
                missing_required_fields=missing_required,
                overall_confidence=overall_confidence,
            )

        except Exception as e:
            logger.error(f"Column analysis failed: {e}")
            # Return empty analysis on failure
            return MappingAnalysis(
                mapped_fields={},
                unmapped_fields=columns,
                suggested_mappings={},
                confidence_scores={col: 0.0 for col in columns},
                missing_required_fields=REQUIRED_FIELDS.get(asset_type, []),
                overall_confidence=0.0,
            )

    async def _find_best_mapping(
        self,
        field_name: str,
        asset_type: str,
        sample_data: Optional[List[List[Any]]] = None,
    ) -> Optional[MappingRule]:
        """Find the best mapping for a field."""
        candidates = []

        # Check base mappings
        for canonical, variations in BASE_MAPPINGS.items():
            normalized_variations = [self._normalize_field_name(v) for v in variations]
            if field_name in normalized_variations:
                candidates.append(
                    MappingRule(
                        source_field=field_name,
                        target_field=canonical,
                        confidence=1.0,
                        source="base",
                    )
                )

        # Check learned mappings
        if self.learned_mappings_cache:
            for target, rules in self.learned_mappings_cache.items():
                for rule in rules:
                    if self._normalize_field_name(rule.source_field) == field_name:
                        candidates.append(rule)

        # Return highest confidence mapping
        if candidates:
            return max(candidates, key=lambda r: r.confidence)

        return None

    async def _find_alternative_mappings(
        self, field_name: str, exclude_target: str
    ) -> List[str]:
        """Find alternative mapping suggestions."""
        alternatives = []

        # Check base mappings
        for canonical, variations in BASE_MAPPINGS.items():
            if canonical != exclude_target:
                normalized_variations = [
                    self._normalize_field_name(v) for v in variations
                ]
                # Check for partial matches
                for variation in normalized_variations:
                    if field_name in variation or variation in field_name:
                        alternatives.append(canonical)
                        break

        return alternatives[:MAX_SUGGESTIONS]  # Return top 3 alternatives

    async def _suggest_mappings_for_field(
        self, field_name: str, asset_type: str
    ) -> List[str]:
        """Suggest possible mappings for an unmapped field."""
        suggestions = []

        # Use fuzzy matching on field name components
        field_parts = set(field_name.replace("_", " ").split())

        for canonical in BASE_MAPPINGS.keys():
            canonical_parts = set(canonical.replace("_", " ").split())

            # Check for word overlap
            if field_parts & canonical_parts:
                suggestions.append(canonical)

        # Prioritize required fields for the asset type
        required = REQUIRED_FIELDS.get(asset_type, [])
        prioritized = [s for s in suggestions if s in required]
        others = [s for s in suggestions if s not in required]

        return prioritized + others

    def _normalize_field_name(self, field_name: str) -> str:
        """Normalize field name for comparison."""
        return field_name.lower().strip().replace(" ", "_").replace("-", "_")

    def get_field_mappings(
        self, asset_type: Optional[str] = None
    ) -> Dict[str, List[str]]:
        """
        Get all field mappings for the current context.

        Args:
            asset_type: Optional asset type filter

        Returns:
            Dictionary of canonical fields to their variations
        """
        try:
            # Start with base mappings
            mappings = dict(BASE_MAPPINGS)

            # Merge learned mappings
            if self.learned_mappings_cache:
                for target_field, rules in self.learned_mappings_cache.items():
                    if target_field not in mappings:
                        mappings[target_field] = []

                    for rule in rules:
                        if rule.source_field not in mappings[target_field]:
                            mappings[target_field].append(rule.source_field)

            # Filter by asset type if specified
            if asset_type and asset_type in REQUIRED_FIELDS:
                required = REQUIRED_FIELDS[asset_type]
                filtered_mappings = {
                    field: variations
                    for field, variations in mappings.items()
                    if field in required or field in BASE_MAPPINGS
                }
                return filtered_mappings

            return mappings

        except Exception as e:
            logger.error(f"Failed to get field mappings: {e}")
            return dict(BASE_MAPPINGS)  # Fallback to base mappings

    def update_cache(
        self, source_field: str, target_field: str, confidence: float, source: str
    ) -> None:
        """Update the learned mappings cache."""
        if self.learned_mappings_cache is None:
            self.learned_mappings_cache = {}

        if target_field not in self.learned_mappings_cache:
            self.learned_mappings_cache[target_field] = []

        # Check if mapping already exists in cache
        existing_index = None
        for i, rule in enumerate(self.learned_mappings_cache[target_field]):
            if rule.source_field == source_field:
                existing_index = i
                break

        new_rule = MappingRule(
            source_field=source_field,
            target_field=target_field,
            confidence=confidence,
            source=source,
            created_at=datetime.utcnow(),
        )

        if existing_index is not None:
            # Update existing rule
            self.learned_mappings_cache[target_field][existing_index] = new_rule
        else:
            # Add new rule
            self.learned_mappings_cache[target_field].append(new_rule)

    def check_negative_mapping(self, source_field: str, target_field: str) -> bool:
        """Check if a mapping is in the negative cache."""
        normalized_source = self._normalize_field_name(source_field)
        normalized_target = self._normalize_field_name(target_field)
        return (normalized_source, normalized_target) in self.negative_mappings_cache

    def add_negative_mapping(self, source_field: str, target_field: str) -> None:
        """Add a mapping to the negative cache."""
        normalized_source = self._normalize_field_name(source_field)
        normalized_target = self._normalize_field_name(target_field)
        self.negative_mappings_cache.add((normalized_source, normalized_target))
