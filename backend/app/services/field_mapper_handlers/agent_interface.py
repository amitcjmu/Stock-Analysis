"""
Agent Interface Handler
Handles AI agent interfaces for field mapping operations.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class AgentInterfaceHandler:
    """Handles agent interface operations for field mapping with graceful fallbacks."""

    def __init__(self, mapping_engine=None):
        self.mapping_engine = mapping_engine
        self.service_available = True
        logger.info("Agent interface handler initialized successfully")

    def is_available(self) -> bool:
        """Check if the handler is properly initialized."""
        return True  # Always available with fallbacks

    def set_mapping_engine(self, mapping_engine):
        """Set mapping engine reference."""
        self.mapping_engine = mapping_engine

    def agent_query_field_mapping(self, field_name: str) -> Dict[str, Any]:
        """
        External tool for agents to query field mappings.
        Returns all known variations for a canonical field name.
        """
        try:
            if not self.mapping_engine:
                return self._fallback_query_response(field_name)

            mappings = self.mapping_engine.get_field_mappings()

            # Try exact match first
            if field_name in mappings:
                return {
                    "canonical_field": field_name,
                    "variations": mappings[field_name],
                    "source": "exact_match",
                    "confidence": 1.0,
                    "query_timestamp": datetime.utcnow().isoformat(),
                }

            # Try fuzzy matching
            field_lower = field_name.lower().replace(" ", "_")
            for canonical, variations in mappings.items():
                canonical_lower = canonical.lower().replace(" ", "_")
                if field_lower in canonical_lower or canonical_lower in field_lower:
                    return {
                        "canonical_field": canonical,
                        "variations": variations,
                        "source": "fuzzy_match",
                        "confidence": 0.8,
                        "query_timestamp": datetime.utcnow().isoformat(),
                    }

                # Check if field matches any variation
                for variation in variations:
                    if (
                        field_lower == variation.lower()
                        or variation.lower() in field_lower
                    ):
                        return {
                            "canonical_field": canonical,
                            "variations": variations,
                            "source": "variation_match",
                            "confidence": 0.9,
                            "query_timestamp": datetime.utcnow().isoformat(),
                        }

            return {
                "canonical_field": None,
                "variations": [],
                "source": "no_match",
                "confidence": 0.0,
                "suggestion": "Consider learning this as a new field mapping",
                "query_timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Agent field mapping query failed: {e}")
            return self._fallback_query_response(field_name, error=str(e))

    def agent_learn_field_mapping(
        self, source_field: str, target_field: str, context: str = ""
    ) -> Dict[str, Any]:
        """
        External tool for agents to learn new field mappings from data analysis or feedback.

        Args:
            source_field: The field name found in data
            target_field: The canonical field name it should map to
            context: Additional context about where this mapping was learned
        """
        try:
            if not self.mapping_engine:
                return self._fallback_learn_response(
                    source_field, target_field, context
                )

            # Determine canonical field
            canonical_field = self._determine_canonical_field(
                source_field, target_field
            )

            # Learn the mapping
            variations = [source_field.lower().strip(), target_field.lower().strip()]
            result = self.mapping_engine.learn_field_mapping(
                canonical_field, variations, f"agent_learning_{context}"
            )

            if result.get("success"):
                return {
                    "success": True,
                    "canonical_field": canonical_field,
                    "learned_variations": variations,
                    "context": context,
                    "message": f"Successfully learned mapping: {source_field} → {canonical_field}",
                    "learning_timestamp": datetime.utcnow().isoformat(),
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Unknown error"),
                    "message": f"Failed to learn mapping: {source_field} → {target_field}",
                    "learning_timestamp": datetime.utcnow().isoformat(),
                }

        except Exception as e:
            logger.error(f"Agent failed to learn field mapping: {e}")
            return self._fallback_learn_response(
                source_field, target_field, context, error=str(e)
            )

    def agent_analyze_columns(
        self, columns: List[str], asset_type: str = "server"
    ) -> Dict[str, Any]:
        """
        External tool for agents to analyze available columns and identify mappings.

        Args:
            columns: List of column names from data
            asset_type: Type of asset being analyzed

        Returns:
            Analysis of field mappings and missing fields
        """
        try:
            if not self.mapping_engine:
                return self._fallback_analyze_response(columns, asset_type)

            # Get current mappings
            self.mapping_engine.get_field_mappings(asset_type)

            # Analyze each column
            column_analysis = {}
            for col in columns:
                mapping_result = self.agent_query_field_mapping(col)
                column_analysis[col] = mapping_result

            # Find potential new mappings
            unmapped_columns = [
                col for col in columns if column_analysis[col]["confidence"] == 0.0
            ]

            # Generate mapping suggestions
            suggestions = self._generate_mapping_suggestions(
                unmapped_columns, asset_type
            )

            return {
                "total_columns": len(columns),
                "mapped_columns": len(columns) - len(unmapped_columns),
                "unmapped_columns": unmapped_columns,
                "column_mappings": column_analysis,
                "asset_type": asset_type,
                "mapping_suggestions": suggestions,
                "analysis_timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Agent column analysis failed: {e}")
            return self._fallback_analyze_response(columns, asset_type, error=str(e))

    def agent_get_mapping_context(self) -> Dict[str, Any]:
        """
        External tool for agents to get context about the current state of field mappings.
        Useful for agents to understand what they've learned so far.
        """
        try:
            if not self.mapping_engine:
                return self._fallback_context_response()

            stats = self.mapping_engine.get_mapping_statistics()

            # Get recent learning activity
            learned_mappings = getattr(self.mapping_engine, "learned_mappings", {})
            recent_mappings = {}
            for field, variations in learned_mappings.items():
                if variations:  # Only include fields with learned variations
                    recent_mappings[field] = variations

            base_mappings = getattr(self.mapping_engine, "base_mappings", {})

            return {
                "mapping_statistics": stats,
                "learned_mappings": recent_mappings,
                "base_field_types": list(base_mappings.keys()),
                "total_variations_learned": sum(
                    len(v) for v in learned_mappings.values()
                ),
                "learning_effectiveness": stats.get("learning_effectiveness", 0),
                "context_message": f"Currently tracking {len(base_mappings)} base field types with {stats.get('learned_fields', 0)} learned fields",
                "context_timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to get mapping context: {e}")
            return self._fallback_context_response(error=str(e))

    def learn_from_feedback_text(
        self, feedback_text: str, context: str = "user_feedback"
    ) -> Dict[str, Any]:
        """
        Extract and learn field mappings from user feedback text.

        Args:
            feedback_text: User feedback containing field mapping information
            context: Context about the feedback source

        Returns:
            Mappings learned from the feedback text
        """
        try:
            # Extract potential field mappings from feedback text
            patterns = self._extract_field_patterns(feedback_text)

            learned_count = 0
            learned_mappings = []

            # Process extracted patterns
            for pattern in patterns:
                if pattern.get("source_field") and pattern.get("target_field"):
                    result = self.agent_learn_field_mapping(
                        pattern["source_field"],
                        pattern["target_field"],
                        f"{context}_extracted",
                    )
                    if result.get("success"):
                        learned_count += 1
                        learned_mappings.append(result)

            return {
                "success": True,
                "patterns_processed": len(patterns),
                "mappings_learned": learned_count,
                "learned_mappings": learned_mappings,
                "context": context,
                "message": f"Processed feedback text and learned {learned_count} new mappings",
                "processing_timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to learn from feedback text: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to process feedback text",
                "processing_timestamp": datetime.utcnow().isoformat(),
            }

    # Helper methods
    def _determine_canonical_field(self, field1: str, field2: str) -> str:
        """Determine which field name should be the canonical one."""
        try:
            if not self.mapping_engine:
                return field1.title().replace("_", " ")

            base_mappings = getattr(self.mapping_engine, "base_mappings", {})
            learned_mappings = getattr(self.mapping_engine, "learned_mappings", {})

            # Check if either field matches our known canonical names
            all_canonical_names = list(base_mappings.keys()) + list(
                learned_mappings.keys()
            )

            for canonical in all_canonical_names:
                if (
                    canonical.lower().replace(" ", "_") in field1.lower()
                    or canonical.lower() in field1.lower()
                ):
                    return canonical
                if (
                    canonical.lower().replace(" ", "_") in field2.lower()
                    or canonical.lower() in field2.lower()
                ):
                    return canonical

            # Special mappings for common business terms
            business_mappings = {
                "application_owner": "Business Owner",
                "business_owner": "Business Owner",
                "owner": "Business Owner",
                "dr_tier": "Criticality",
                "business_criticality": "Criticality",
                "criticality": "Criticality",
                "ram_gb": "Memory (GB)",
                "memory_gb": "Memory (GB)",
                "memory": "Memory (GB)",
            }

            # Check if either field has a known business mapping
            field1_lower = field1.lower()
            field2_lower = field2.lower()

            if field1_lower in business_mappings:
                return business_mappings[field1_lower]
            if field2_lower in business_mappings:
                return business_mappings[field2_lower]

            # If neither matches, prefer the more descriptive one
            if len(field1) > len(field2):
                return field1.title().replace("_", " ")
            else:
                return field2.title().replace("_", " ")

        except Exception as e:
            logger.error(f"Error determining canonical field: {e}")
            return field1.title().replace("_", " ")

    def _extract_field_patterns(self, text: str) -> List[Dict[str, str]]:
        """Extract potential field mapping patterns from text."""
        try:
            import re

            patterns = []

            # Pattern 1: "field1 should be field2" or "map field1 to field2"
            mapping_pattern = r"(?:map\s+|should\s+be\s+)?(\w+(?:_\w+)*)\s+(?:should\s+be\s+|to\s+|→\s+|maps?\s+to\s+)(\w+(?:_\w+)*|\w+(?:\s+\w+)*)"
            matches = re.findall(mapping_pattern, text.lower(), re.IGNORECASE)

            for match in matches:
                if len(match) == 2:
                    patterns.append(
                        {
                            "source_field": match[0].strip(),
                            "target_field": match[1].strip(),
                            "pattern_type": "explicit_mapping",
                        }
                    )

            # Pattern 2: "field1 is actually field2" or "field1 means field2"
            equivalence_pattern = r"(\w+(?:_\w+)*)\s+(?:is\s+actually\s+|means\s+|equals\s+|=\s+)(\w+(?:_\w+)*|\w+(?:\s+\w+)*)"
            matches = re.findall(equivalence_pattern, text.lower(), re.IGNORECASE)

            for match in matches:
                if len(match) == 2:
                    patterns.append(
                        {
                            "source_field": match[0].strip(),
                            "target_field": match[1].strip(),
                            "pattern_type": "equivalence",
                        }
                    )

            return patterns

        except Exception as e:
            logger.error(f"Error extracting field patterns: {e}")
            return []

    def _generate_mapping_suggestions(
        self, unmapped_columns: List[str], asset_type: str
    ) -> List[Dict[str, str]]:
        """Generate suggestions for potential field mappings."""
        try:
            suggestions = []

            # Common field patterns by asset type
            common_patterns = {
                "server": {
                    "hostname": "Asset Name",
                    "ip": "IP Address",
                    "memory": "Memory (GB)",
                    "cpu": "CPU Cores",
                    "os": "Operating System",
                },
                "application": {
                    "app": "Application Service",
                    "owner": "Business Owner",
                    "version": "Version",
                    "env": "Environment",
                },
                "database": {
                    "db": "Application Service",
                    "size": "Storage (GB)",
                    "version": "Version",
                },
            }

            patterns = common_patterns.get(asset_type, common_patterns["server"])

            for unmapped_col in unmapped_columns:
                col_lower = unmapped_col.lower()

                for pattern, canonical_field in patterns.items():
                    if pattern in col_lower:
                        suggestions.append(
                            {
                                "unmapped_column": unmapped_col,
                                "suggested_mapping": canonical_field,
                                "reason": f"Column '{unmapped_col}' contains keyword '{pattern}'",
                                "confidence": 0.7,
                            }
                        )
                        break

            return suggestions

        except Exception as e:
            logger.error(f"Error generating mapping suggestions: {e}")
            return []

    # Fallback methods
    def _fallback_query_response(
        self, field_name: str, error: str = None
    ) -> Dict[str, Any]:
        """Fallback response for query operations."""
        return {
            "canonical_field": None,
            "variations": [],
            "source": "fallback",
            "confidence": 0.0,
            "suggestion": "Mapping engine not available - consider manual mapping",
            "query_timestamp": datetime.utcnow().isoformat(),
            "error": error,
        }

    def _fallback_learn_response(
        self, source_field: str, target_field: str, context: str, error: str = None
    ) -> Dict[str, Any]:
        """Fallback response for learning operations."""
        return {
            "success": False,
            "error": error or "Mapping engine not available",
            "message": f"Cannot learn mapping: {source_field} → {target_field}",
            "learning_timestamp": datetime.utcnow().isoformat(),
            "fallback_mode": True,
        }

    def _fallback_analyze_response(
        self, columns: List[str], asset_type: str, error: str = None
    ) -> Dict[str, Any]:
        """Fallback response for analysis operations."""
        return {
            "total_columns": len(columns),
            "mapped_columns": 0,
            "unmapped_columns": columns,
            "column_mappings": {},
            "asset_type": asset_type,
            "mapping_suggestions": [],
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "error": error,
            "fallback_mode": True,
        }

    def _fallback_context_response(self, error: str = None) -> Dict[str, Any]:
        """Fallback response for context operations."""
        return {
            "mapping_statistics": {},
            "learned_mappings": {},
            "base_field_types": [],
            "total_variations_learned": 0,
            "learning_effectiveness": 0,
            "context_message": "Mapping engine not available",
            "context_timestamp": datetime.utcnow().isoformat(),
            "error": error,
            "fallback_mode": True,
        }
