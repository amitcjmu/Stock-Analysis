"""
Phase Handlers - Defensive Field Mapping Methods

Contains defensive field mapping execution strategies and phase handling logic.
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class PhaseHandlerMethods:
    """Mixin class containing defensive phase handling methods"""

    # ========================================
    # DEFENSIVE FIELD MAPPING METHODS
    # ========================================

    async def _safe_execute_field_mapping_via_handler(self, data_validation_result):
        """
        Strategy 1: Execute field mapping via phase handlers with defensive checks.

        This is the primary method that should work in normal circumstances.
        """
        logger.info("🛡️ Executing field mapping via phase handlers (Strategy 1)")

        # Check if phase handlers exist and are properly initialized
        if not hasattr(self, "phase_handlers") or not self.phase_handlers:
            raise RuntimeError("Phase handlers not initialized")

        # Check for the field mapping method using defensive resolver
        from ..defensive_method_resolver import create_method_resolver

        handler_resolver = create_method_resolver(self.phase_handlers)

        # Try multiple method name variants
        method_variants = [
            "generate_field_mapping_suggestions",
            "generate_field_mapping_suggestion",  # Common typo
            "generate_mapping_suggestions",
            "field_mapping_suggestions",
        ]

        mapping_method = None
        for variant in method_variants:
            mapping_method = handler_resolver.resolve_method(variant)
            if mapping_method:
                logger.info(f"✅ Resolved field mapping method: {variant}")
                break

        if not mapping_method:
            method_info = handler_resolver.get_method_info(
                "generate_field_mapping_suggestions"
            )
            logger.error(
                f"❌ Field mapping method resolution failed. Info: {method_info}"
            )
            raise AttributeError("Field mapping method not found on phase handlers")

        # Execute the mapping method
        result = await mapping_method(data_validation_result)

        # Validate result structure
        if not isinstance(result, dict):
            raise ValueError(
                f"Field mapping returned invalid result type: {type(result)}"
            )

        # Ensure required fields are present
        if "status" not in result:
            result["status"] = "success" if "error" not in result else "failed"

        logger.info("✅ Field mapping via phase handlers completed successfully")
        return result

    async def _safe_execute_field_mapping_via_resolver(self, data_validation_result):
        """
        Strategy 2: Execute field mapping directly via method resolver.

        This method attempts to call field mapping methods directly on the flow
        instance when phase handlers fail.
        """
        logger.info("🛡️ Executing field mapping via method resolver (Strategy 2)")

        # Check if field mapping phase executor exists
        if not hasattr(self, "field_mapping_phase") or not self.field_mapping_phase:
            # Try to initialize phase executors
            if hasattr(self, "_initialize_phase_executors_with_state"):
                logger.info("🔄 Attempting to initialize phase executors")
                self._initialize_phase_executors_with_state()
            else:
                raise RuntimeError("Cannot initialize phase executors")

        if not self.field_mapping_phase:
            raise RuntimeError("Field mapping phase executor still not available")

        # Use defensive method resolution on the phase executor
        from ..defensive_method_resolver import create_method_resolver

        executor_resolver = create_method_resolver(self.field_mapping_phase)

        # Try to find the execution method
        execution_method = executor_resolver.resolve_method(
            "execute_suggestions_only",
            fallback_variants=["execute", "execute_field_mapping", "run", "process"],
        )

        if not execution_method:
            method_info = executor_resolver.get_method_info("execute_suggestions_only")
            logger.error(
                f"❌ Field mapping execution method not found. Info: {method_info}"
            )
            raise AttributeError("Field mapping execution method not found")

        # Prepare input data
        input_data = {
            "validation_result": data_validation_result,
            "flow_id": self._flow_id,
            "phase": "field_mapping",
            "suggestions_only": True,
        }

        # Execute the method
        result = await execution_method(input_data)

        # Process and validate result
        if not isinstance(result, dict):
            raise ValueError(
                f"Field mapping executor returned invalid result type: {type(result)}"
            )

        # Convert result to expected format if needed
        if "success" in result and result["success"]:
            result["status"] = "success"
        elif "success" in result and not result["success"]:
            result["status"] = "failed"

        logger.info("✅ Field mapping via method resolver completed successfully")
        return result

    async def _fallback_field_mapping_execution(self, data_validation_result):
        """
        Strategy 3: Fallback field mapping execution.

        This method provides a basic field mapping implementation as a last resort
        when all other methods fail.
        """
        logger.info("🛡️ Executing fallback field mapping (Strategy 3)")

        try:
            # Basic field mapping logic as fallback
            raw_data = getattr(self.state, "raw_data", {})

            if not raw_data:
                logger.warning("⚠️ No raw data available for fallback field mapping")
                return {
                    "status": "success",
                    "phase": "field_mapping",
                    "field_mappings": [],
                    "suggestions": [],
                    "clarifications": [],
                    "message": "Fallback: No raw data available, proceeding with empty mappings",
                }

            # Extract field names from raw data
            field_names = []
            if isinstance(raw_data, dict):
                if (
                    "data" in raw_data
                    and isinstance(raw_data["data"], list)
                    and raw_data["data"]
                ):
                    # Handle nested data structure
                    first_record = raw_data["data"][0]
                    if isinstance(first_record, dict):
                        field_names = list(first_record.keys())
                elif isinstance(raw_data, dict):
                    # Direct dictionary format
                    field_names = list(raw_data.keys())

            logger.info(
                f"📋 Fallback extracted {len(field_names)} field names: {field_names[:5]}..."
            )

            # Generate basic mappings (identity mapping as fallback)
            basic_mappings = []
            suggestions = []

            for field_name in field_names[:20]:  # Limit to first 20 fields
                # Skip metadata fields
                if field_name.lower() in [
                    "mappings",
                    "skipped_fields",
                    "synthesis_required",
                ]:
                    continue

                mapping = {
                    "source_field": field_name,
                    "target_field": field_name,  # Identity mapping
                    "mapping_type": "direct",
                    "confidence": 0.5,  # Low confidence for fallback
                    "method": "fallback",
                }
                basic_mappings.append(mapping)

                # Add suggestion
                suggestion = {
                    "field": field_name,
                    "suggested_mapping": field_name,
                    "confidence": 0.5,
                    "reason": "Fallback identity mapping",
                }
                suggestions.append(suggestion)

            result = {
                "status": "success",
                "phase": "field_mapping",
                "field_mappings": basic_mappings,
                "mappings": basic_mappings,  # Alternative key name
                "suggestions": suggestions,
                "clarifications": [],
                "message": f"Fallback field mapping completed with {len(basic_mappings)} basic mappings",
                "execution_method": "fallback",
                "timestamp": datetime.now().isoformat(),
            }

            logger.info(
                f"✅ Fallback field mapping generated {len(basic_mappings)} mappings"
            )
            return result

        except Exception as fallback_error:
            logger.error(f"❌ Even fallback field mapping failed: {fallback_error}")
            # Return minimal response to prevent complete failure
            return {
                "status": "failed",
                "phase": "field_mapping",
                "error": f"Fallback field mapping failed: {fallback_error}",
                "field_mappings": [],
                "suggestions": [],
                "clarifications": [],
                "message": "All field mapping strategies failed including fallback",
                "execution_method": "fallback_failed",
            }
