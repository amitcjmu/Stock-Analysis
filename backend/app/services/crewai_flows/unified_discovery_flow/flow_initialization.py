"""
Flow Initialization Module

Handles initialization of flow components, agents, and phases.
"""

import logging
import uuid
from typing import Any, Dict, Optional

from app.core.context import RequestContext
from app.models.unified_discovery_flow_state import UnifiedDiscoveryFlowState

from ..flow_state_bridge import FlowStateBridge

# Import handlers and bridges

# Real CrewAI agents are managed by UnifiedFlowCrewManager - no individual agent imports needed

# Import phase classes
# Phase modules removed - using Executor pattern instead

logger = logging.getLogger(__name__)


class FlowInitializer:
    """Handles flow initialization and component setup"""

    def __init__(self, crewai_service, context: RequestContext, **kwargs):
        """
        Initialize the flow initializer

        Args:
            crewai_service: The CrewAI service instance
            context: Request context for multi-tenant operations
            **kwargs: Additional flow configuration
        """
        self.crewai_service = crewai_service
        self.context = context

        # Extract initialization parameters
        logger.info("🔍 DEBUG: FlowInitializer context values:")
        logger.info(f"   - context.client_account_id: {context.client_account_id}")
        logger.info(f"   - context.engagement_id: {context.engagement_id}")
        logger.info(f"   - context.user_id: {context.user_id}")
        logger.info(f"   - kwargs.flow_id: {kwargs.get('flow_id', 'NOT PROVIDED')}")

        self.init_context = {
            "client_account_id": str(context.client_account_id),
            "engagement_id": str(context.engagement_id),
            "user_id": str(context.user_id),
            "flow_id": kwargs.get("flow_id", str(uuid.uuid4())),
            "flow_name": kwargs.get("flow_name", "Unified Discovery Flow"),
            "metadata": kwargs.get("metadata", {}),
        }

        logger.info("🔍 DEBUG: FlowInitializer init_context:")
        logger.info(f"   - client_account_id: {self.init_context['client_account_id']}")
        logger.info(f"   - engagement_id: {self.init_context['engagement_id']}")
        logger.info(f"   - user_id: {self.init_context['user_id']}")
        logger.info(f"   - flow_id: {self.init_context['flow_id']}")

        # Store raw data if provided
        self.raw_data = kwargs.get("raw_data", [])
        self.metadata = kwargs.get("metadata", {})

        # Debug logging
        logger.info(
            f"🔍 DEBUG: FlowInitializer received {len(self.raw_data) if self.raw_data else 0} raw data records"
        )
        logger.info(f"🔍 DEBUG: Metadata received: {self.metadata}")
        logger.info(
            f"🔍 DEBUG: Master flow ID in metadata: {self.metadata.get('master_flow_id', 'NOT FOUND')}"
        )
        if self.raw_data and len(self.raw_data) > 0:
            logger.info(
                f"🔍 DEBUG: First record keys in initializer: {list(self.raw_data[0].keys())}"
            )
            logger.info(f"🔍 DEBUG: First record sample: {self.raw_data[0]}")

    def create_initial_state(self) -> UnifiedDiscoveryFlowState:
        """Create the initial flow state"""
        # Create state with explicit field initialization
        state = UnifiedDiscoveryFlowState()

        # Explicitly set all required fields from init_context
        state.flow_id = self.init_context.get("flow_id", "")
        state.client_account_id = self.init_context.get("client_account_id", "")
        state.engagement_id = self.init_context.get("engagement_id", "")
        state.user_id = self.init_context.get("user_id", "")

        # Set data fields
        state.raw_data = self.raw_data
        state.metadata = self.metadata

        # Set data_import_id to flow_id for direct raw data flows
        # This ensures field mapping persistence works correctly
        state.data_import_id = state.flow_id

        # Log the initialized values
        logger.info(
            f"🔍 State initialized with flow_id: {state.flow_id}, "
            f"client: {state.client_account_id}, engagement: {state.engagement_id}, "
            f"user: {state.user_id}"
        )

        # If we have raw data, it means data import is already complete
        if self.raw_data and len(self.raw_data) > 0:
            # Mark data import as completed since we have data
            # state.data_import_completed = True  # This field doesn't exist
            state.phase_completion["data_import"] = True
            state.progress_percentage = 16.7  # 1/6 phases complete
            state.current_phase = "field_mapping"  # Ready for field mapping
            logger.info(
                f"✅ Data import already complete with {len(self.raw_data)} records, setting initial progress to 16.7%"
            )
        else:
            # Initialize with default phase_completion dictionary
            state.phase_completion = {
                "data_import": False,
                "field_mapping": False,
                "data_cleansing": False,
                "asset_creation": False,
                "asset_inventory": False,
                "dependency_analysis": False,
                "tech_debt_analysis": False,
            }
            state.progress_percentage = 0.0
            state.current_phase = "data_import"

        # Debug logging
        logger.info(
            f"🔍 DEBUG: Created initial state with {len(self.raw_data) if self.raw_data else 0} raw data records"
        )
        logger.info(
            f"🔍 DEBUG: Initial progress: {state.progress_percentage}%, current phase: {state.current_phase}"
        )
        if self.raw_data and len(self.raw_data) > 0:
            logger.info(f"🔍 DEBUG: First record in initial state: {self.raw_data[0]}")

        return state

    def initialize_flow_bridge(self) -> Optional[FlowStateBridge]:
        """Initialize the PostgreSQL flow bridge"""
        try:
            flow_bridge = FlowStateBridge(self.context)
            logger.info(
                "✅ PostgreSQL Flow State Bridge initialized with new postgres_store"
            )
            return flow_bridge
        except Exception as e:
            logger.warning(f"⚠️ Flow State Bridge initialization failed: {e}")
            return None

    def initialize_handlers(self) -> Dict[str, Any]:
        """Initialize flow handlers"""
        # Note: Both managers need state which isn't available yet
        # They will be initialized later with proper state
        return {
            "phase_executor": None,  # Will be initialized later with state
            "crew_manager": None,  # Will be initialized later with state
        }

    def initialize_agents(self) -> Dict[str, Any]:
        """Initialize all agent instances"""
        # Real CrewAI implementation doesn't use individual agents
        # Instead, we use crews managed by UnifiedFlowCrewManager
        logger.info("✅ Using real CrewAI crews - no individual agents needed")
        return {
            "orchestrator": None,  # Not needed - UnifiedFlowCrewManager handles orchestration
            "data_validation_agent": None,  # Replaced by data_import_validation_crew
            "attribute_mapping_agent": None,  # Replaced by field_mapping_crew
            "data_cleansing_agent": None,  # Replaced by data_cleansing_crew
            "asset_inventory_agent": None,  # Replaced by inventory_building_crew
            "dependency_analysis_agent": None,  # Replaced by app_server_dependency_crew
            "tech_debt_analysis_agent": None,  # Replaced by technical_debt_crew
        }

    def initialize_phases(
        self, state, agents: Dict[str, Any], flow_bridge
    ) -> Dict[str, Any]:
        """Initialize all phase handlers"""
        # With real CrewAI crews, phases are handled by PhaseExecutionManager
        # We don't need individual phase objects
        logger.info(
            "✅ Phase execution will be handled by PhaseExecutionManager with real CrewAI crews"
        )
        return {
            "data_validation_phase": "crew_managed",  # Handled by data_import_validation_crew
            "field_mapping_phase": "crew_managed",  # Handled by field_mapping_crew
            "data_cleansing_phase": "crew_managed",  # Handled by data_cleansing_crew
            "asset_inventory_phase": "crew_managed",  # Handled by inventory_building_crew
            "dependency_analysis_phase": "crew_managed",  # Handled by app_server_dependency_crew
            "tech_debt_assessment_phase": "crew_managed",  # Handled by technical_debt_crew
        }
