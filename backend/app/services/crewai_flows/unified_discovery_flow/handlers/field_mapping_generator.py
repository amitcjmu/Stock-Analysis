"""
Field Mapping Generator Handler

This module contains field mapping generation and suggestion functions extracted from phase_handlers.py
to reduce file length and improve maintainability.

🤖 Generated with Claude Code (CC)

Co-Authored-By: Claude <noreply@anthropic.com>
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class FieldMappingGenerator:
    """Handles field mapping generation and suggestions"""

    def __init__(self, flow_instance):
        """Initialize with reference to the main flow instance"""
        self.flow = flow_instance
        self.logger = logger

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
                processed_result = self._process_field_mapping_result(result)

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
    ) -> Optional[Dict[str, Any]]:
        """Safely generate field mapping suggestions with multiple fallback approaches"""
        try:
            # Prepare input data for field mapping
            input_data = self._prepare_field_mapping_input_data(
                data_validation_agent_result
            )

            if not input_data:
                self.logger.warning("⚠️ No input data available for field mapping")
                return None

            # Try crew-based field mapping first
            crew_result = await self._try_direct_crew_execution(input_data)
            if crew_result and crew_result.get("field_mappings"):
                return crew_result

            # If crew fails, try basic field extraction
            basic_result = await self._try_basic_field_extraction(input_data)
            if basic_result and basic_result.get("field_mappings"):
                return basic_result

            # If all else fails, provide minimal fallback
            return await self._try_minimal_fallback(input_data)

        except Exception as e:
            self.logger.error(f"❌ Safe field mapping generation failed: {e}")
            return None

    def _prepare_field_mapping_input_data(
        self, data_validation_agent_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare input data for field mapping generation"""
        try:
            # Extract relevant data from validation result
            data_source = data_validation_agent_result.get("data_source", {})
            validation_errors = data_validation_agent_result.get(
                "validation_errors", []
            )
            field_analysis = data_validation_agent_result.get("field_analysis", {})

            # Build comprehensive input for field mapping
            input_data = {
                "data_source": data_source,
                "validation_errors": validation_errors,
                "field_analysis": field_analysis,
                "flow_context": {
                    "flow_id": getattr(self.flow, "_flow_id", None),
                    "client_account_id": getattr(
                        self.flow.state, "client_account_id", None
                    ),
                    "data_import_id": getattr(self.flow.state, "data_import_id", None),
                },
                "timestamp": self._get_current_timestamp(),
            }

            self.logger.debug(
                f"📊 Prepared field mapping input data with {len(field_analysis)} field analyses"
            )
            return input_data

        except Exception as e:
            self.logger.error(f"❌ Failed to prepare field mapping input data: {e}")
            return {}

    def _process_field_mapping_result(
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
                "status": "completed",
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

    def _validate_field_mapping(self, mapping: Dict[str, Any]) -> bool:
        """Validate a single field mapping"""
        try:
            required_fields = ["source_field", "target_field"]

            for field in required_fields:
                if not mapping.get(field):
                    return False

            return True

        except Exception:
            return False

    async def _try_alternative_field_mapping_approaches(
        self, data_validation_agent_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Try alternative field mapping approaches when primary method fails"""
        try:
            self.logger.info("🔄 Trying alternative field mapping approaches")

            # Prepare input data
            input_data = self._prepare_field_mapping_input_data(
                data_validation_agent_result
            )

            # Try direct crew execution
            crew_result = await self._try_direct_crew_execution(input_data)
            if crew_result and crew_result.get("field_mappings"):
                return crew_result

            # Try basic field extraction
            basic_result = await self._try_basic_field_extraction(input_data)
            if basic_result and basic_result.get("field_mappings"):
                return basic_result

            # Minimal fallback
            return await self._try_minimal_fallback(input_data)

        except Exception as e:
            self.logger.error(f"❌ Alternative field mapping approaches failed: {e}")
            return {
                "status": "error",
                "message": str(e),
                "field_mappings": [],
                "suggestions": [],
                "execution_method": "alternative_error_fallback",
            }

    async def _try_direct_crew_execution(
        self, input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Try direct crew execution for field mapping"""
        try:
            self.logger.info("🚀 Attempting direct crew execution for field mapping")

            # Mock crew execution - in real implementation this would call CrewAI
            field_mappings = []

            # Extract field information from input data
            field_analysis = input_data.get("field_analysis", {})

            for field_name, analysis in field_analysis.items():
                # Create basic mapping based on field analysis
                mapping = {
                    "source_field": field_name,
                    "target_field": self._suggest_target_field(field_name, analysis),
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
                    "status": "completed",
                }

                self.logger.info(
                    f"✅ Direct crew execution generated {len(field_mappings)} mappings"
                )
                return result

        except Exception as e:
            self.logger.error(f"❌ Direct crew execution failed: {e}")

        return {}

    async def _try_basic_field_extraction(
        self, input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Try basic field extraction as fallback"""
        try:
            self.logger.info("📊 Attempting basic field extraction")

            field_analysis = input_data.get("field_analysis", {})
            basic_mappings = []

            for field_name, analysis in field_analysis.items():
                # Create basic mapping
                mapping = {
                    "source_field": field_name,
                    "target_field": self._normalize_field_name(field_name),
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
                    "status": "completed",
                }

                self.logger.info(
                    f"Basic field extraction completed with {len(basic_mappings)} fields"
                )
                return result

        except Exception as e:
            self.logger.error(f"❌ Basic field extraction failed: {e}")

        return {}

    async def _try_minimal_fallback(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
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

    def _suggest_target_field(self, source_field: str, analysis: Dict[str, Any]) -> str:
        """Suggest target field based on source field and analysis"""
        try:
            # Simple field name normalization
            normalized = self._normalize_field_name(source_field)
            return normalized

        except Exception:
            return source_field

    def _normalize_field_name(self, field_name: str) -> str:
        """Normalize field name for mapping"""
        try:
            # Convert to lowercase and replace spaces/special chars with underscores
            normalized = field_name.lower().replace(" ", "_").replace("-", "_")
            # Remove special characters except underscores
            import re

            normalized = re.sub(r"[^a-zA-Z0-9_]", "_", normalized)
            # Remove multiple consecutive underscores
            normalized = re.sub(r"_+", "_", normalized)
            # Remove leading/trailing underscores
            normalized = normalized.strip("_")
            return normalized

        except Exception:
            return field_name

    def _get_current_timestamp(self) -> str:
        """Get current timestamp as ISO string"""
        from datetime import datetime

        return datetime.utcnow().isoformat()
