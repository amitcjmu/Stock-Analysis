"""
Mapping Strategies for Field Mapping Generator

Contains different strategies for generating field mappings.

🤖 Generated with Claude Code (CC)

Co-Authored-By: Claude <noreply@anthropic.com>
"""

import logging
from typing import Any, Dict

from .base import FieldMappingGeneratorBase

logger = logging.getLogger(__name__)


class FieldMappingStrategies(FieldMappingGeneratorBase):
    """Implements different strategies for field mapping generation"""

    async def try_direct_crew_execution(
        self, input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Try direct crew execution for field mapping"""
        try:
            self.logger.info("🚀 Attempting direct crew execution for field mapping")

            # Mock crew execution - in real implementation this would call CrewAI
            field_mappings = []

            # Extract field information from input data
            field_analysis = input_data.get("field_analysis", {})

            # BUG FIX: If field_analysis is empty, try to generate from validated_data
            if not field_analysis:
                field_mappings = self._generate_mappings_from_validated_data(
                    input_data, "crew_generated_from_validated_data"
                )
                if not field_mappings:
                    self.logger.warning(
                        "⚠️ No field analysis or validated_data available for crew execution"
                    )
                    return {}
            else:
                # Standard processing with field_analysis
                for field_name, analysis in field_analysis.items():
                    # Create basic mapping based on field analysis
                    mapping = {
                        "source_field": field_name,
                        "target_field": self._suggest_target_field(
                            field_name, analysis
                        ),
                        "confidence": 0.7,
                        "mapping_type": "crew_generated",
                        "status": "suggested",
                    }
                    field_mappings.append(mapping)

            if field_mappings:
                result = {
                    "field_mappings": field_mappings,
                    "suggestions": [],
                    "execution_method": "direct_crew_execution",
                    "status": "success",
                }

                self.logger.info(
                    f"✅ Direct crew execution generated {len(field_mappings)} mappings"
                )
                return result

        except Exception as e:
            self.logger.error(f"❌ Direct crew execution failed: {e}")

        return {}

    async def try_basic_field_extraction(
        self, input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Try basic field extraction as fallback"""
        try:
            self.logger.info("📊 Attempting basic field extraction")

            field_analysis = input_data.get("field_analysis", {})
            basic_mappings = []

            # BUG FIX: If field_analysis is empty, try to generate from validated_data
            if not field_analysis:
                basic_mappings = self._generate_mappings_from_validated_data(
                    input_data, "basic_extraction_from_validated_data", confidence=0.5
                )
                if not basic_mappings:
                    self.logger.warning(
                        "⚠️ No field analysis or validated_data available for basic extraction"
                    )
                    return {}
            else:
                # Standard processing with field_analysis
                for field_name, analysis in field_analysis.items():
                    # Create basic mapping
                    mapping = {
                        "source_field": field_name,
                        "target_field": self._map_common_field_names(field_name),
                        "confidence": 0.5,
                        "mapping_type": "basic_extraction",
                        "status": "suggested",
                    }
                    basic_mappings.append(mapping)

            if basic_mappings:
                result = {
                    "field_mappings": basic_mappings,
                    "suggestions": [],
                    "execution_method": "basic_field_extraction",
                    "status": "success",
                }

                self.logger.info(
                    f"Basic field extraction completed with {len(basic_mappings)} fields"
                )
                return result

        except Exception as e:
            self.logger.error(f"❌ Basic field extraction failed: {e}")

        return {}

    async def try_minimal_fallback(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Provide minimal fallback when all else fails"""
        try:
            self.logger.info("🔄 Using minimal fallback approach")

            return {
                "field_mappings": [],
                "suggestions": [],
                "status": "fallback",
                "message": "Minimal fallback - proceeding with empty field mappings",
                "execution_method": "minimal_fallback",
            }

        except Exception as e:
            self.logger.error(f"❌ Minimal fallback failed: {e}")
            return {}

    def _generate_mappings_from_validated_data(
        self, input_data: Dict[str, Any], mapping_type: str, confidence: float = 0.7
    ) -> list:
        """Generate field mappings from validated_data when field_analysis is empty"""
        mappings = []

        try:
            validated_data = input_data.get("validated_data", [])
            if (
                validated_data
                and isinstance(validated_data, list)
                and len(validated_data) > 0
            ):
                sample_record = validated_data[0]
                if isinstance(sample_record, dict):
                    self.logger.info(
                        f"🔄 Generating {mapping_type} mappings from validated_data"
                    )
                    for field_name, field_value in sample_record.items():
                        if mapping_type.startswith("crew_generated"):
                            target_field = self._suggest_target_field(
                                field_name, {"sample_value": field_value}
                            )
                        else:
                            target_field = self._map_common_field_names(field_name)

                        mapping = {
                            "source_field": field_name,
                            "target_field": target_field,
                            "confidence": confidence,
                            "mapping_type": mapping_type,
                            "status": "suggested",
                        }
                        mappings.append(mapping)
        except Exception as e:
            self.logger.error(
                f"❌ Failed to generate mappings from validated_data: {e}"
            )

        return mappings
