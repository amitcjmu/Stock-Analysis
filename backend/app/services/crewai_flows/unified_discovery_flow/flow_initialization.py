"""
Flow Initialization Module

Handles initialization of flow components, agents, and phases.
"""

import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime

from app.core.context import RequestContext
from app.models.unified_discovery_flow_state import UnifiedDiscoveryFlowState

# Import handlers and bridges
from ..handlers.unified_flow_crew_manager import UnifiedFlowCrewManager
from ..handlers.phase_executors import PhaseExecutionManager
from ..handlers.unified_flow_management import UnifiedFlowManagement
from ..flow_state_bridge import FlowStateBridge

# Real CrewAI agents are managed by UnifiedFlowCrewManager - no individual agent imports needed

# Import phase classes
from .phases import (
    DataValidationPhase,
    FieldMappingPhase,
    DataCleansingPhase,
    AssetInventoryPhase,
    DependencyAnalysisPhase,
    TechDebtAssessmentPhase
)

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
        self.init_context = {
            'client_account_id': str(context.client_account_id),
            'engagement_id': str(context.engagement_id),
            'user_id': str(context.user_id),
            'flow_id': kwargs.get('flow_id', str(uuid.uuid4())),
            'flow_name': kwargs.get('flow_name', 'Unified Discovery Flow'),
            'metadata': kwargs.get('metadata', {})
        }
        
        # Store raw data if provided
        self.raw_data = kwargs.get('raw_data', [])
        self.metadata = kwargs.get('metadata', {})
    
    def create_initial_state(self) -> UnifiedDiscoveryFlowState:
        """Create the initial flow state"""
        state = UnifiedDiscoveryFlowState(**self.init_context)
        state.raw_data = self.raw_data
        state.metadata = self.metadata
        return state
    
    def initialize_flow_bridge(self) -> Optional[FlowStateBridge]:
        """Initialize the PostgreSQL flow bridge"""
        try:
            flow_bridge = FlowStateBridge(self.context)
            logger.info("✅ PostgreSQL Flow State Bridge initialized with new postgres_store")
            return flow_bridge
        except Exception as e:
            logger.warning(f"⚠️ Flow State Bridge initialization failed: {e}")
            return None
    
    def initialize_handlers(self) -> Dict[str, Any]:
        """Initialize flow handlers"""
        # Note: Both managers need state which isn't available yet
        # They will be initialized later with proper state
        return {
            'phase_executor': None,  # Will be initialized later with state
            'crew_manager': None  # Will be initialized later with state
        }
    
    def initialize_agents(self) -> Dict[str, Any]:
        """Initialize all agent instances"""
        # Real CrewAI implementation doesn't use individual agents
        # Instead, we use crews managed by UnifiedFlowCrewManager
        logger.info("✅ Using real CrewAI crews - no individual agents needed")
        return {
            'orchestrator': None,  # Not needed - UnifiedFlowCrewManager handles orchestration
            'data_validation_agent': None,  # Replaced by data_import_validation_crew
            'attribute_mapping_agent': None,  # Replaced by field_mapping_crew
            'data_cleansing_agent': None,  # Replaced by data_cleansing_crew
            'asset_inventory_agent': None,  # Replaced by inventory_building_crew
            'dependency_analysis_agent': None,  # Replaced by app_server_dependency_crew
            'tech_debt_analysis_agent': None  # Replaced by technical_debt_crew
        }
    
    def initialize_phases(self, state, agents: Dict[str, Any], flow_bridge) -> Dict[str, Any]:
        """Initialize all phase handlers"""
        # With real CrewAI crews, phases are handled by PhaseExecutionManager
        # We don't need individual phase objects
        logger.info("✅ Phase execution will be handled by PhaseExecutionManager with real CrewAI crews")
        return {
            'data_validation_phase': "crew_managed",  # Handled by data_import_validation_crew
            'field_mapping_phase': "crew_managed",  # Handled by field_mapping_crew
            'data_cleansing_phase': "crew_managed",  # Handled by data_cleansing_crew
            'asset_inventory_phase': "crew_managed",  # Handled by inventory_building_crew
            'dependency_analysis_phase': "crew_managed",  # Handled by app_server_dependency_crew
            'tech_debt_assessment_phase': "crew_managed"  # Handled by technical_debt_crew
        }