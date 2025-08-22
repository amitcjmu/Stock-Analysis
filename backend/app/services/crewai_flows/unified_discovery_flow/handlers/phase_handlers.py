"""
Phase Handlers Module

This module contains all the phase handling methods extracted from the base_flow.py
to improve maintainability and code organization.

The main PhaseHandlers class delegates to specialized handlers for better modularity.
"""

import logging

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

    async def generate_field_mapping_suggestions(self, data_validation_agent_result):
        """Generate field mapping suggestions using the field mapping executor"""
        self.logger.info(
            f"🗺️ [PhaseHandlers] Generating field mapping suggestions for flow {self.flow._flow_id}"
        )

        try:
            # Initialize phase executors if not already done
            if (
                not hasattr(self.flow, "field_mapping_phase")
                or not self.flow.field_mapping_phase
            ):
                if hasattr(self.flow, "_initialize_phase_executors_with_state"):
                    self.flow._initialize_phase_executors_with_state()

            if not self.flow.field_mapping_phase:
                raise RuntimeError(
                    "Field mapping phase executor is not initialized. This is a critical error."
                )

            # Prepare input data for field mapping
            input_data = {
                "validation_result": data_validation_agent_result,
                "flow_id": self.flow._flow_id,
                "phase": "field_mapping",
                "suggestions_only": True,  # Request suggestions without full execution
            }

            # Execute field mapping suggestions
            mapping_result = (
                await self.flow.field_mapping_phase.execute_suggestions_only(input_data)
            )

            if mapping_result and mapping_result.get("success", True):
                self.logger.info("✅ Field mapping suggestions generated successfully")

                # Store results in flow state
                self.flow.state.field_mappings = mapping_result.get("mappings", [])
                self.flow.state.mapping_suggestions = mapping_result.get(
                    "suggestions", []
                )
                self.flow.state.clarifications = mapping_result.get(
                    "clarifications", []
                )

                return {
                    "status": "success",
                    "phase": "field_mapping",
                    "field_mappings": mapping_result.get("mappings", []),
                    "suggestions": mapping_result.get("suggestions", []),
                    "clarifications": mapping_result.get("clarifications", []),
                    "message": "Field mapping suggestions generated successfully",
                }
            else:
                error_msg = mapping_result.get(
                    "error", "Field mapping suggestions failed"
                )
                self.logger.error(f"❌ Field mapping suggestions failed: {error_msg}")
                return {
                    "status": "failed",
                    "phase": "field_mapping",
                    "error": error_msg,
                    "field_mappings": [],
                    "suggestions": [],
                    "clarifications": [],
                }

        except Exception as e:
            self.logger.error(
                f"❌ Field mapping suggestions execution failed: {str(e)}"
            )
            # Send phase error notification
            await self.communication.send_phase_error("field_mapping", str(e))
            raise
