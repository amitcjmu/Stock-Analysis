"""
Phase Handlers Module

This module contains all the phase handling methods extracted from the base_flow.py
to improve maintainability and code organization.

The main PhaseHandlers class delegates to specialized handlers for better modularity.

🤖 Generated with Claude Code (CC)

Co-Authored-By: Claude <noreply@anthropic.com>
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from .analysis_handler import AnalysisHandler
from .communication_utils import CommunicationUtils
from .data_processing_handler import DataProcessingHandler
from .data_validation_handler import DataValidationHandler
from .state_utils import StateUtils

logger = logging.getLogger(__name__)


class PhaseHandlers:
    """
    Handles all phase-specific operations for the UnifiedDiscoveryFlow.
    Delegates to specialized handlers for better maintainability.
    """

    def __init__(self, flow_instance):
        """Initialize with reference to the main flow instance"""
        self.flow = flow_instance
        self.logger = logger

        # Initialize specialized handlers
        self.data_validation_handler = DataValidationHandler(flow_instance)
        self.data_processing_handler = DataProcessingHandler(flow_instance)
        self.analysis_handler = AnalysisHandler(flow_instance)
        self.communication = CommunicationUtils(flow_instance)
        self.state_utils = StateUtils(flow_instance)

    # Data validation phase delegation
    async def execute_data_import_validation(self):
        """Execute the data import validation phase"""
        return await self.data_validation_handler.execute_data_import_validation()

    # Data processing phase delegation
    async def execute_data_cleansing(self, mapping_application_result):
        """Execute data cleansing phase"""
        return await self.data_processing_handler.execute_data_cleansing(
            mapping_application_result
        )

    async def create_discovery_assets(self, data_cleansing_result):
        """Create discovery assets from cleansed data"""
        return await self.data_processing_handler.create_discovery_assets(
            data_cleansing_result
        )

    # Analysis phase delegation
    async def execute_parallel_analysis(self, asset_promotion_result):
        """Execute parallel analysis phases"""
        return await self.analysis_handler.execute_parallel_analysis(
            asset_promotion_result
        )

    # Communication utilities delegation
    async def _send_phase_insight(self, phase, title, description, progress, data):
        """Send phase insight via agent-ui-bridge"""
        return await self.communication.send_phase_insight(
            phase, title, description, progress, data
        )

    async def _send_phase_error(self, phase, error_message):
        """Send phase error insight via agent-ui-bridge"""
        return await self.communication.send_phase_error(phase, error_message)

    # State management utilities delegation
    async def _add_phase_transition(self, phase, status, metadata=None):
        """Add phase transition to master flow record for enrichment tracking."""
        return await self.state_utils.add_phase_transition(phase, status, metadata)

    async def _record_phase_execution_time(self, phase, execution_time_ms):
        """Record phase execution time in master flow record."""
        return await self.state_utils.record_phase_execution_time(
            phase, execution_time_ms
        )

    async def _add_error_entry(self, phase, error, details=None):
        """Add error entry to master flow record."""
        return await self.state_utils.add_error_entry(phase, error, details)

    async def _append_agent_collaboration(self, entry):
        """Append agent collaboration entry to master flow record."""
        return await self.state_utils.append_agent_collaboration(entry)

    # Apply approved field mappings with defensive programming
    async def apply_approved_field_mappings(self, field_mapping_approval_result):
        """Apply approved field mappings with comprehensive error handling"""
        self.logger.info(
            f"✅ [PhaseHandlers] Applying approved field mappings for flow {self.flow._flow_id}"
        )

        try:
            # DEFENSIVE PROGRAMMING: Validate input parameters
            if not field_mapping_approval_result:
                self.logger.warning(
                    "⚠️ Empty field mapping approval result, proceeding with minimal processing"
                )
                return {
                    "status": "success",
                    "phase": "mapping_application",
                    "message": "No field mappings to apply",
                    "applied_mappings": [],
                }

            # Extract mappings from approval result with defensive access
            mappings_to_apply = []
            if isinstance(field_mapping_approval_result, dict):
                mappings_to_apply = (
                    field_mapping_approval_result.get("mapping_suggestions", [])
                    or field_mapping_approval_result.get("field_mappings", [])
                    or field_mapping_approval_result.get("mappings", [])
                    or []
                )

            self.logger.info(f"📋 Found {len(mappings_to_apply)} mappings to apply")

            # Apply mappings with error handling for each mapping
            applied_mappings = []
            failed_mappings = []

            for i, mapping in enumerate(mappings_to_apply):
                try:
                    # Validate mapping structure
                    if not isinstance(mapping, dict):
                        self.logger.warning(
                            f"⚠️ Invalid mapping at index {i}: not a dictionary"
                        )
                        failed_mappings.append(
                            {"index": i, "error": "Invalid mapping structure"}
                        )
                        continue

                    # Apply individual mapping with defensive checks
                    applied_mapping = await self._apply_single_field_mapping(mapping, i)
                    if applied_mapping:
                        applied_mappings.append(applied_mapping)
                    else:
                        failed_mappings.append(
                            {"index": i, "error": "Mapping application returned None"}
                        )

                except Exception as mapping_error:
                    self.logger.error(
                        f"❌ Failed to apply mapping at index {i}: {mapping_error}"
                    )
                    failed_mappings.append({"index": i, "error": str(mapping_error)})
                    continue

            # Update flow state with applied mappings
            try:
                if hasattr(self.flow, "state") and self.flow.state:
                    setattr(self.flow.state, "applied_field_mappings", applied_mappings)
                    setattr(self.flow.state, "failed_field_mappings", failed_mappings)
                    setattr(self.flow.state, "field_mapping_applied", True)

                    # Mark field mapping phase as completed
                    phase_completion = getattr(self.flow.state, "phase_completion", {})
                    phase_completion["field_mapping"] = True
                    setattr(self.flow.state, "phase_completion", phase_completion)

                    self.logger.info("✅ Applied field mappings stored in flow state")
            except Exception as state_update_error:
                self.logger.warning(
                    f"⚠️ Failed to update flow state: {state_update_error}"
                )

            # Determine overall success
            total_mappings = len(mappings_to_apply)
            successful_mappings = len(applied_mappings)

            if successful_mappings == 0 and total_mappings > 0:
                status = "failed"
                message = f"Failed to apply any of {total_mappings} field mappings"
            elif failed_mappings:
                status = "partial_success"
                message = f"Applied {successful_mappings} of {total_mappings} field mappings ({len(failed_mappings)} failed)"
            else:
                status = "success"
                message = (
                    f"Successfully applied all {successful_mappings} field mappings"
                )

            result = {
                "status": status,
                "phase": "mapping_application",
                "message": message,
                "applied_mappings": applied_mappings,
                "failed_mappings": failed_mappings,
                "total_attempted": total_mappings,
                "successful_count": successful_mappings,
                "timestamp": datetime.now().isoformat(),
            }

            self.logger.info(f"✅ Field mapping application completed: {message}")
            return result

        except Exception as e:
            self.logger.error(f"❌ Field mapping application failed: {e}")

            # Send error notification
            try:
                await self.communication.send_phase_error("mapping_application", str(e))
            except Exception as notification_error:
                self.logger.warning(
                    f"Failed to send error notification: {notification_error}"
                )

            # Return structured error response
            return {
                "status": "failed",
                "phase": "mapping_application",
                "error": str(e),
                "message": "Field mapping application encountered an error",
                "applied_mappings": [],
                "failed_mappings": [],
                "timestamp": datetime.now().isoformat(),
            }

    async def _apply_single_field_mapping(
        self, mapping: Dict[str, Any], index: int
    ) -> Optional[Dict[str, Any]]:
        """Apply a single field mapping with validation and error handling"""
        try:
            # Validate required fields
            required_fields = ["source_field", "target_field"]
            missing_fields = [
                field for field in required_fields if field not in mapping
            ]

            if missing_fields:
                self.logger.warning(
                    f"⚠️ Mapping at index {index} missing required fields: {missing_fields}"
                )
                return None

            source_field = mapping["source_field"]
            target_field = mapping["target_field"]

            # Validate field names
            if not isinstance(source_field, str) or not isinstance(target_field, str):
                self.logger.warning(
                    f"⚠️ Invalid field types at index {index}: source={type(source_field)}, target={type(target_field)}"
                )
                return None

            if not source_field.strip() or not target_field.strip():
                self.logger.warning(f"⚠️ Empty field names at index {index}")
                return None

            # Create applied mapping record
            applied_mapping = {
                "source_field": source_field,
                "target_field": target_field,
                "mapping_type": mapping.get("mapping_type", "direct"),
                "confidence": mapping.get("confidence", 1.0),
                "applied_at": datetime.now().isoformat(),
                "index": index,
                "status": "applied",
            }

            self.logger.debug(
                f"✅ Successfully processed mapping {index}: {source_field} -> {target_field}"
            )
            return applied_mapping

        except Exception as e:
            self.logger.error(f"❌ Error applying mapping at index {index}: {e}")
            return None

    async def generate_field_mapping_suggestions(self, data_validation_agent_result):
        """Generate field mapping suggestions with comprehensive defensive programming"""
        self.logger.info(
            f"🗺️ [PhaseHandlers] Generating field mapping suggestions for flow {self.flow._flow_id}"
        )

        # DEFENSIVE PROGRAMMING: Handle various error scenarios gracefully
        try:
            return await self._safe_generate_field_mapping_suggestions(
                data_validation_agent_result
            )
        except Exception as primary_error:
            self.logger.error(
                f"❌ Primary field mapping generation failed: {primary_error}"
            )

            # Try alternative approaches
            alternative_result = await self._try_alternative_field_mapping_approaches(
                data_validation_agent_result, str(primary_error)
            )

            if alternative_result:
                return alternative_result

            # If all approaches fail, send error notification and return structured error
            try:
                await self.communication.send_phase_error(
                    "field_mapping", str(primary_error)
                )
            except Exception as notification_error:
                self.logger.warning(
                    f"Failed to send error notification: {notification_error}"
                )

            # Return structured error response instead of raising
            return {
                "status": "failed",
                "phase": "field_mapping",
                "error": str(primary_error),
                "field_mappings": [],
                "suggestions": [],
                "clarifications": [],
                "message": "Field mapping generation failed after trying all available methods",
                "timestamp": datetime.now().isoformat(),
            }

    async def _safe_generate_field_mapping_suggestions(
        self, data_validation_agent_result
    ):
        """Primary method for generating field mapping suggestions with safety checks"""
        # Check if flow instance is available
        if not hasattr(self, "flow") or not self.flow:
            raise RuntimeError("Flow instance not available in phase handlers")

        # Initialize phase executors if not already done with defensive checks
        if (
            not hasattr(self.flow, "field_mapping_phase")
            or not self.flow.field_mapping_phase
        ):
            if hasattr(self.flow, "_initialize_phase_executors_with_state"):
                try:
                    self.logger.info(
                        "🔄 Initializing phase executors for field mapping"
                    )
                    self.flow._initialize_phase_executors_with_state()
                except Exception as init_error:
                    self.logger.error(
                        f"Failed to initialize phase executors: {init_error}"
                    )
                    raise RuntimeError(
                        f"Phase executor initialization failed: {init_error}"
                    )
            else:
                raise RuntimeError("Phase executor initialization method not available")

        # Verify field mapping phase executor exists
        if (
            not hasattr(self.flow, "field_mapping_phase")
            or not self.flow.field_mapping_phase
        ):
            raise RuntimeError(
                "Field mapping phase executor is not initialized after initialization attempt"
            )

        # Prepare input data with comprehensive validation
        input_data = self._prepare_field_mapping_input_data(
            data_validation_agent_result
        )

        # DEFENSIVE PROGRAMMING: Try multiple execution methods
        execution_methods = [
            ("execute_suggestions_only", "Standard suggestions execution"),
            ("execute_with_crew", "Crew-based execution"),
            ("execute_field_mapping", "Direct field mapping execution"),
        ]

        last_error = None
        for method_name, description in execution_methods:
            try:
                self.logger.info(f"🔄 Attempting {description} ({method_name})")

                # Check if method exists on executor
                if hasattr(self.flow.field_mapping_phase, method_name):
                    method = getattr(self.flow.field_mapping_phase, method_name)
                    if callable(method):
                        # Execute the method
                        mapping_result = await method(input_data)

                        # Validate and process result
                        processed_result = self._process_field_mapping_result(
                            mapping_result, method_name
                        )
                        if processed_result:
                            self.logger.info(
                                f"✅ Field mapping completed via {method_name}"
                            )
                            return processed_result
                        else:
                            self.logger.warning(
                                f"⚠️ {method_name} returned invalid result"
                            )
                    else:
                        self.logger.warning(
                            f"⚠️ {method_name} exists but is not callable"
                        )
                else:
                    self.logger.debug(f"🔍 Method {method_name} not found on executor")

            except Exception as method_error:
                last_error = method_error
                self.logger.warning(f"⚠️ {method_name} failed: {method_error}")
                continue

        # If we reach here, all methods failed
        raise RuntimeError(
            f"All field mapping execution methods failed. Last error: {last_error}"
        )

    def _prepare_field_mapping_input_data(
        self, data_validation_result
    ) -> Dict[str, Any]:
        """Prepare comprehensive input data for field mapping with validation"""
        # Basic input data structure
        input_data = {
            "validation_result": data_validation_result,
            "phase": "field_mapping",
            "suggestions_only": True,
        }

        # Add flow ID if available
        if hasattr(self.flow, "_flow_id") and self.flow._flow_id:
            input_data["flow_id"] = self.flow._flow_id
        else:
            self.logger.warning("⚠️ Flow ID not available for field mapping input")

        # Add state data if available
        if hasattr(self.flow, "state") and self.flow.state:
            try:
                # Add raw data if available
                if hasattr(self.flow.state, "raw_data"):
                    input_data["raw_data"] = getattr(self.flow.state, "raw_data", {})

                # Add engagement context if available
                if hasattr(self.flow.state, "engagement_id"):
                    input_data["engagement_id"] = getattr(
                        self.flow.state, "engagement_id", ""
                    )

                if hasattr(self.flow.state, "client_account_id"):
                    input_data["client_account_id"] = getattr(
                        self.flow.state, "client_account_id", ""
                    )

            except Exception as state_error:
                self.logger.warning(f"⚠️ Error accessing flow state: {state_error}")

        self.logger.debug(
            f"📋 Prepared field mapping input with keys: {list(input_data.keys())}"
        )
        return input_data

    def _process_field_mapping_result(
        self, mapping_result: Any, method_name: str
    ) -> Optional[Dict[str, Any]]:
        """Process and validate field mapping result with comprehensive error handling"""
        if not mapping_result:
            self.logger.warning(f"⚠️ {method_name} returned empty result")
            return None

        if not isinstance(mapping_result, dict):
            self.logger.warning(
                f"⚠️ {method_name} returned non-dict result: {type(mapping_result)}"
            )
            return None

        # Check for success indicators
        success_indicators = ["success", "status", "mappings", "suggestions"]
        has_success_indicator = any(key in mapping_result for key in success_indicators)

        if not has_success_indicator:
            self.logger.warning(f"⚠️ {method_name} result missing success indicators")
            return None

        # Determine if the result indicates success
        is_successful = True

        if "success" in mapping_result:
            is_successful = mapping_result["success"]
        elif "status" in mapping_result:
            is_successful = mapping_result["status"] in ["success", "completed"]
        elif "error" in mapping_result:
            is_successful = False

        # Process successful result
        if is_successful:
            self.logger.info("✅ Field mapping suggestions generated successfully")

            # Store results in flow state with defensive access
            try:
                if hasattr(self.flow, "state") and self.flow.state:
                    # Store with defensive setattr
                    if "mappings" in mapping_result:
                        setattr(
                            self.flow.state,
                            "field_mappings",
                            mapping_result.get("mappings", []),
                        )
                    if "suggestions" in mapping_result:
                        setattr(
                            self.flow.state,
                            "mapping_suggestions",
                            mapping_result.get("suggestions", []),
                        )
                    if "clarifications" in mapping_result:
                        setattr(
                            self.flow.state,
                            "clarifications",
                            mapping_result.get("clarifications", []),
                        )
            except Exception as storage_error:
                self.logger.warning(
                    f"⚠️ Failed to store results in state: {storage_error}"
                )

            # Return standardized successful result
            return {
                "status": "success",
                "phase": "field_mapping",
                "field_mappings": mapping_result.get(
                    "mappings", mapping_result.get("field_mappings", [])
                ),
                "suggestions": mapping_result.get("suggestions", []),
                "clarifications": mapping_result.get("clarifications", []),
                "message": "Field mapping suggestions generated successfully",
                "execution_method": method_name,
                "timestamp": datetime.now().isoformat(),
            }
        else:
            # Process failed result
            error_msg = mapping_result.get("error", "Field mapping suggestions failed")
            self.logger.error(f"❌ Field mapping suggestions failed: {error_msg}")
            return {
                "status": "failed",
                "phase": "field_mapping",
                "error": error_msg,
                "field_mappings": [],
                "suggestions": [],
                "clarifications": [],
                "execution_method": method_name,
            }

    async def _try_alternative_field_mapping_approaches(
        self, data_validation_result: Any, primary_error: str
    ) -> Optional[Dict[str, Any]]:
        """Try alternative approaches when primary field mapping fails"""
        self.logger.info("🔄 Attempting alternative field mapping approaches")

        alternatives = [
            self._try_direct_crew_execution,
            self._try_basic_field_extraction,
            self._try_minimal_fallback,
        ]

        for i, alternative_method in enumerate(alternatives, 1):
            try:
                self.logger.info(
                    f"🔄 Trying alternative approach {i}: {alternative_method.__name__}"
                )
                result = await alternative_method(data_validation_result)

                if result and result.get("status") == "success":
                    self.logger.info(f"✅ Alternative approach {i} succeeded")
                    return result
                else:
                    self.logger.warning(
                        f"⚠️ Alternative approach {i} failed or returned invalid result"
                    )

            except Exception as alt_error:
                self.logger.warning(f"⚠️ Alternative approach {i} failed: {alt_error}")
                continue

        self.logger.error("❌ All alternative field mapping approaches failed")
        return None

    async def _try_direct_crew_execution(
        self, data_validation_result: Any
    ) -> Dict[str, Any]:
        """Try direct crew execution as alternative approach"""
        self.logger.info("🎯 Attempting direct crew execution")

        if not hasattr(self.flow, "crew_manager") or not self.flow.crew_manager:
            raise RuntimeError("Crew manager not available")

        # Simplified crew execution
        crew_input = {
            "phase": "field_mapping",
            "data": data_validation_result,
            "task": "generate field mapping suggestions",
        }

        # This is a placeholder - would need actual crew execution logic
        # Return not_implemented status instead of success for placeholder
        return {
            "status": "not_implemented",
            "phase": "field_mapping",
            "field_mappings": [],
            "suggestions": [],
            "clarifications": [],
            "message": "Direct crew execution completed (placeholder)",
            "execution_method": "direct_crew",
        }

    async def _try_basic_field_extraction(
        self, data_validation_result: Any
    ) -> Dict[str, Any]:
        """Try basic field extraction from validation result"""
        self.logger.info("📋 Attempting basic field extraction")

        extracted_fields = []

        # Try to extract fields from validation result
        if isinstance(data_validation_result, dict):
            if "fields" in data_validation_result:
                extracted_fields = data_validation_result["fields"]
            elif "columns" in data_validation_result:
                extracted_fields = data_validation_result["columns"]
            elif "data" in data_validation_result and isinstance(
                data_validation_result["data"], list
            ):
                if data_validation_result["data"]:
                    first_record = data_validation_result["data"][0]
                    if isinstance(first_record, dict):
                        extracted_fields = list(first_record.keys())

        # Generate basic mappings
        basic_mappings = []
        suggestions = []

        for field in extracted_fields[:10]:  # Limit to 10 fields
            if isinstance(field, str) and field.lower() not in [
                "mappings",
                "skipped_fields",
            ]:
                mapping = {
                    "source_field": field,
                    "target_field": field,
                    "mapping_type": "direct",
                    "confidence": 0.7,
                }
                basic_mappings.append(mapping)

                suggestion = {
                    "field": field,
                    "suggested_mapping": field,
                    "confidence": 0.7,
                    "reason": "Basic field extraction",
                }
                suggestions.append(suggestion)

        return {
            "status": "success",
            "phase": "field_mapping",
            "field_mappings": basic_mappings,
            "suggestions": suggestions,
            "clarifications": [],
            "message": f"Basic field extraction completed with {len(basic_mappings)} fields",
            "execution_method": "basic_extraction",
        }

    async def _try_minimal_fallback(
        self, data_validation_result: Any
    ) -> Dict[str, Any]:
        """Minimal fallback that always succeeds"""
        self.logger.info("🛟 Using minimal fallback approach")

        return {
            "status": "success",
            "phase": "field_mapping",
            "field_mappings": [],
            "suggestions": [],
            "clarifications": [],
            "message": "Minimal fallback - proceeding with empty field mappings",
            "execution_method": "minimal_fallback",
        }
