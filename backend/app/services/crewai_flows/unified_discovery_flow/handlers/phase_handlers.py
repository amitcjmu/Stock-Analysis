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

from .analysis_handler import AnalysisHandler
from .communication_utils import CommunicationUtils
from .data_processing_handler import DataProcessingHandler
from .data_validation_handler import DataValidationHandler
from .field_mapping_generator import FieldMappingGenerator
from .field_mapping_persistence import FieldMappingPersistence
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
        self.field_mapping_generator = FieldMappingGenerator(flow_instance)
        self.field_mapping_persistence = FieldMappingPersistence(flow_instance)

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
    async def apply_approved_field_mappings(  # noqa: C901
        self, field_mapping_approval_result
    ):
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
                    applied_mapping_result = (
                        await self.field_mapping_generator.apply_single_field_mapping(
                            mapping, field_mapping_approval_result, {}
                        )
                    )
                    applied_mapping = (
                        applied_mapping_result.get("applied_mapping")
                        if applied_mapping_result.get("status") == "success"
                        else None
                    )
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
                message = (
                    f"Applied {successful_mappings} of {total_mappings} field mappings "
                    f"({len(failed_mappings)} failed)"
                )
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

    async def generate_field_mapping_suggestions(self, data_validation_agent_result):
        """Generate field mapping suggestions - delegated to specialized handler"""
        self.logger.info(
            f"🗺️ [PhaseHandlers] Generating field mapping suggestions for flow {self.flow._flow_id}"
        )

        try:
            # Delegate to the field mapping generator
            result = (
                await self.field_mapping_generator.generate_field_mapping_suggestions(
                    data_validation_agent_result
                )
            )

            # Persist field mappings if generation was successful
            if (
                result
                and result.get("status") in ["completed", "success"]
                and result.get("field_mappings")
            ):
                await self.field_mapping_persistence.persist_field_mappings_to_database(
                    result
                )

            return result

        except Exception as e:
            self.logger.error(f"❌ Field mapping generation failed: {e}")

            # Return structured error response
            return {
                "status": "failed",
                "phase": "field_mapping",
                "error": str(e),
                "field_mappings": [],
                "suggestions": [],
                "clarifications": [],
                "message": "Field mapping generation failed",
                "timestamp": self.field_mapping_generator._get_current_timestamp(),
            }
