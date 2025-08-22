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
