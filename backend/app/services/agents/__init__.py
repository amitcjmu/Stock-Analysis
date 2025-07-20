"""
Agents package for the AI Modernize Migration Platform.
Contains specialized agents for discovery, analysis, and orchestration.
"""

# Import key agent classes for easier access
try:
    # Import from the modular agent_service_layer package
    from .agent_service_layer import (
        AgentServiceLayer,
        get_agent_service,
        FlowHandler,
        DataHandler,
        AssetHandler,
        ServiceValidator,
        PerformanceTracker
    )
    
    # Import communication and integration layers
    from .agent_communication_protocol import AgentCommunicationProtocol
    from .agent_integration_layer import AgentIntegrationLayer
    
    # Import the MasterFlowOrchestrator for unified flow management
    from ..master_flow_orchestrator import MasterFlowOrchestrator
    
    # Import Gap Analysis agents
    from .critical_attribute_assessor_crewai import CriticalAttributeAssessorAgent
    from .gap_prioritization_agent_crewai import GapPrioritizationAgent
    
    # Import Manual Collection agents
    from .questionnaire_dynamics_agent_crewai import QuestionnaireDynamicsAgent
    from .validation_workflow_agent_crewai import ValidationWorkflowAgent
    from .progress_tracking_agent_crewai import ProgressTrackingAgent
    
    __all__ = [
        # Modular service layer
        'AgentServiceLayer',
        'get_agent_service',
        'FlowHandler',
        'DataHandler',
        'AssetHandler',
        'ServiceValidator',
        'PerformanceTracker',
        
        # Communication and integration
        'AgentCommunicationProtocol',
        'AgentIntegrationLayer',
        
        # Master Flow Orchestrator for unified flow management
        'MasterFlowOrchestrator',
        
        # Gap Analysis agents
        'CriticalAttributeAssessorAgent',
        'GapPrioritizationAgent',
        
        # Manual Collection agents
        'QuestionnaireDynamicsAgent',
        'ValidationWorkflowAgent',
        'ProgressTrackingAgent'
    ]
    
except ImportError as e:
    # Graceful fallback if some agents are not available
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Some agent modules not available: {e}")
    
    __all__ = [] 