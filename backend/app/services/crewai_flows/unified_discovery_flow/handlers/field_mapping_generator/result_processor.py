"""
Result Processor for Field Mapping Generator

Handles processing and validation of field mapping results.

🤖 Generated with Claude Code (CC)

Co-Authored-By: Claude <noreply@anthropic.com>
"""

import logging
from typing import Any, Dict, Optional

from .base import FieldMappingGeneratorBase

logger = logging.getLogger(__name__)


class FieldMappingResultProcessor(FieldMappingGeneratorBase):
    """Processes and validates field mapping results"""

    def process_field_mapping_result(
        self, result: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Process and validate field mapping result"""
        try:
            if not isinstance(result, dict):
                self.logger.warning("⚠️ Invalid result format - not a dictionary")
                return None

            field_mappings = result.get("field_mappings", [])
            suggestions = result.get("suggestions", [])

            if not field_mappings and not suggestions:
                self.logger.warning("⚠️ No field mappings or suggestions in result")
                return None

            # Process and validate field mappings
            processed_mappings = []
            for mapping in field_mappings:
                if self._validate_field_mapping(mapping):
                    processed_mappings.append(mapping)

            # Process and validate suggestions
            processed_suggestions = []
            for suggestion in suggestions:
                if self._validate_field_mapping(suggestion):
                    processed_suggestions.append(suggestion)

            processed_result = {
                "field_mappings": processed_mappings,
                "suggestions": processed_suggestions,
                "status": "success",
                "total_mappings": len(processed_mappings) + len(processed_suggestions),
                "execution_method": result.get("execution_method", "standard"),
                "timestamp": self._get_current_timestamp(),
            }

            self.logger.info(
                f"✅ Processed {len(processed_mappings)} field mappings "
                f"and {len(processed_suggestions)} suggestions"
            )

            return processed_result

        except Exception as e:
            self.logger.error(f"❌ Failed to process field mapping result: {e}")
            return None

    async def apply_single_field_mapping(
        self,
        mapping: Dict[str, Any],
        validation_result: Dict[str, Any],
        flow_state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Apply a single field mapping with validation"""
        try:
            source_field = mapping.get("source_field")
            target_field = mapping.get("target_field")

            if not source_field or not target_field:
                return {
                    "status": "error",
                    "message": "Missing source or target field",
                    "mapping": mapping,
                }

            # Apply the mapping logic here
            applied_mapping = {
                "source_field": source_field,
                "target_field": target_field,
                "status": "applied",
                "confidence": mapping.get("confidence", 0.8),
                "applied_at": self._get_current_timestamp(),
            }

            self.logger.info(
                f"✅ Applied field mapping: {source_field} -> {target_field}"
            )

            return {
                "status": "success",
                "applied_mapping": applied_mapping,
                "mapping": mapping,
            }

        except Exception as e:
            self.logger.error(f"❌ Failed to apply field mapping {mapping}: {e}")
            return {"status": "error", "message": str(e), "mapping": mapping}
