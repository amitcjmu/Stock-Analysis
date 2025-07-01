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

# Import individual agents
from app.services.agents.data_import_validation_agent import DataImportValidationAgent
from app.services.agents.attribute_mapping_agent import AttributeMappingAgent
from app.services.agents.data_cleansing_agent import DataCleansingAgent
from app.services.agents.asset_inventory_agent import AssetInventoryAgent
from app.services.agents.dependency_analysis_agent import DependencyAnalysisAgent
from app.services.agents.tech_debt_analysis_agent import TechDebtAnalysisAgent
from app.services.agents.discovery_agent_orchestrator import DiscoveryAgentOrchestrator

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
            'session_id': kwargs.get('session_id', f'disc_session_{uuid.uuid4().hex[:8]}'),
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
            flow_bridge = FlowStateBridge(
                client_account_id=self.init_context['client_account_id'],
                engagement_id=self.init_context['engagement_id'],
                use_optimistic_locking=True
            )
            logger.info("✅ PostgreSQL Flow State Bridge initialized")
            return flow_bridge
        except Exception as e:
            logger.warning(f"⚠️ Flow State Bridge initialization failed: {e}")
            return None
    
    def initialize_handlers(self) -> Dict[str, Any]:
        """Initialize flow handlers"""
        return {
            'phase_executor': PhaseExecutionManager(self.crewai_service),
            'crew_manager': UnifiedFlowCrewManager(self.crewai_service)
        }
    
    def initialize_agents(self) -> Dict[str, Any]:
        """Initialize all agent instances"""
        return {
            'orchestrator': DiscoveryAgentOrchestrator(self.crewai_service),
            'data_validation_agent': DataImportValidationAgent(self.crewai_service),
            'attribute_mapping_agent': AttributeMappingAgent(self.crewai_service),
            'data_cleansing_agent': DataCleansingAgent(self.crewai_service),
            'asset_inventory_agent': AssetInventoryAgent(self.crewai_service),
            'dependency_analysis_agent': DependencyAnalysisAgent(self.crewai_service),
            'tech_debt_analysis_agent': TechDebtAnalysisAgent(self.crewai_service)
        }
    
    def initialize_phases(self, state, agents: Dict[str, Any], flow_bridge) -> Dict[str, Any]:
        """Initialize all phase handlers"""
        return {
            'data_validation_phase': DataValidationPhase(
                state, 
                agents['data_validation_agent'], 
                self.init_context
            ),
            'field_mapping_phase': FieldMappingPhase(
                state,
                agents['attribute_mapping_agent'],
                self.init_context,
                flow_bridge
            ),
            'data_cleansing_phase': DataCleansingPhase(
                state,
                agents['data_cleansing_agent'],
                self.init_context,
                flow_bridge
            ),
            'asset_inventory_phase': AssetInventoryPhase(
                state,
                agents['asset_inventory_agent'],
                self.init_context,
                flow_bridge
            ),
            'dependency_analysis_phase': DependencyAnalysisPhase(
                state,
                agents['dependency_analysis_agent'],
                self.init_context,
                flow_bridge
            ),
            'tech_debt_assessment_phase': TechDebtAssessmentPhase(
                state,
                agents['tech_debt_analysis_agent'],
                self.init_context,
                flow_bridge
            )
        }