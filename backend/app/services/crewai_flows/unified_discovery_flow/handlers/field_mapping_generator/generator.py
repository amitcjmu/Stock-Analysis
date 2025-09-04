"""
Main Field Mapping Generator

Orchestrates field mapping generation using various strategies and processors.

🤖 Generated with Claude Code (CC)

Co-Authored-By: Claude <noreply@anthropic.com>
"""

import logging
from typing import Any, Dict

from .base import FieldMappingGeneratorBase
from .data_extractor import FieldMappingDataExtractor
from .mapping_strategies import FieldMappingStrategies
from .result_processor import FieldMappingResultProcessor

logger = logging.getLogger(__name__)


class FieldMappingGenerator(FieldMappingGeneratorBase):
    """Main field mapping generator that orchestrates all functionality"""

    def __init__(self, flow_instance):
        """Initialize with reference to the main flow instance"""
        super().__init__(flow_instance)
        self.data_extractor = FieldMappingDataExtractor(flow_instance)
        self.strategies = FieldMappingStrategies(flow_instance)
        self.result_processor = FieldMappingResultProcessor(flow_instance)

    async def generate_field_mapping_suggestions(
        self, data_validation_agent_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate field mapping suggestions with comprehensive error handling"""
        try:
            self.logger.info("🔍 Starting field mapping suggestion generation")

            # Safe generate field mapping suggestions
            result = await self._safe_generate_field_mapping_suggestions(
                data_validation_agent_result
            )

            # Process and validate the result
            if result and result.get("field_mappings"):
                processed_result = self.result_processor.process_field_mapping_result(
                    result
                )

                if processed_result:
                    self.logger.info(
                        "✅ Field mapping suggestions generated successfully"
                    )
                    return processed_result

            # If primary method fails, try alternatives
            self.logger.warning(
                "⚠️ Primary field mapping generation failed, trying alternatives"
            )
            return await self._try_alternative_field_mapping_approaches(
                data_validation_agent_result
            )

        except Exception as e:
            self.logger.error(f"❌ Field mapping suggestion generation failed: {e}")
            return {
                "status": "error",
                "message": str(e),
                "field_mappings": [],
                "suggestions": [],
                "execution_method": "error_fallback",
            }

    async def _safe_generate_field_mapping_suggestions(
        self, data_validation_agent_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Safely generate field mapping suggestions with multiple fallback approaches"""
        try:
            # Prepare input data for field mapping
            input_data = self.data_extractor.prepare_field_mapping_input_data(
                data_validation_agent_result
            )

            if not input_data:
                self.logger.warning("⚠️ No input data available for field mapping")
                return {}

            # Try crew-based field mapping first
            crew_result = await self.strategies.try_direct_crew_execution(input_data)
            if crew_result and crew_result.get("field_mappings"):
                return crew_result

            # If crew fails, try basic field extraction
            basic_result = await self.strategies.try_basic_field_extraction(input_data)
            if basic_result and basic_result.get("field_mappings"):
                return basic_result

            # If all else fails, provide minimal fallback
            return await self.strategies.try_minimal_fallback(input_data)

        except Exception as e:
            self.logger.error(f"❌ Safe field mapping generation failed: {e}")
            return {}

    async def _try_alternative_field_mapping_approaches(
        self, data_validation_agent_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Try alternative field mapping approaches when primary method fails"""
        try:
            self.logger.info("🔄 Trying alternative field mapping approaches")

            # Prepare input data
            input_data = self.data_extractor.prepare_field_mapping_input_data(
                data_validation_agent_result
            )

            # Try direct crew execution
            crew_result = await self.strategies.try_direct_crew_execution(input_data)
            if crew_result and crew_result.get("field_mappings"):
                return crew_result

            # Try basic field extraction
            basic_result = await self.strategies.try_basic_field_extraction(input_data)
            if basic_result and basic_result.get("field_mappings"):
                return basic_result

            # Minimal fallback
            return await self.strategies.try_minimal_fallback(input_data)

        except Exception as e:
            self.logger.error(f"❌ Alternative field mapping approaches failed: {e}")
            return {
                "status": "error",
                "message": str(e),
                "field_mappings": [],
                "suggestions": [],
                "execution_method": "alternative_error_fallback",
            }

    async def apply_single_field_mapping(
        self,
        mapping: Dict[str, Any],
        validation_result: Dict[str, Any],
        flow_state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Apply a single field mapping with validation"""
        return await self.result_processor.apply_single_field_mapping(
            mapping, validation_result, flow_state
        )
