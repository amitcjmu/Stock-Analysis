"""
Agents package for the AI Force Migration Platform.
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
    
    from .discovery_agent_orchestrator import DiscoveryAgentOrchestrator
    # ARCHIVED: base_discovery_agent moved to archive/legacy (pseudo-agent base class)
    # from .base_discovery_agent import BaseDiscoveryAgent
    # ARCHIVED: These pseudo-agents moved to archive/legacy
    # from .asset_inventory_agent import AssetInventoryAgent
    # from .data_cleansing_agent import DataCleansingAgent
    # from .attribute_mapping_agent import AttributeMappingAgent
    # from .dependency_analysis_agent import DependencyAnalysisAgent
    # ARCHIVED: These pseudo-agents also moved to archive/legacy
    # from .tech_debt_analysis_agent import TechDebtAnalysisAgent
    # from .data_import_validation_agent import DataImportValidationAgent
    from .agent_communication_protocol import AgentCommunicationProtocol
    from .agent_integration_layer import AgentIntegrationLayer
    

    
    __all__ = [
        # Modular service layer
        'AgentServiceLayer',
        'get_agent_service',
        'FlowHandler',
        'DataHandler',
        'AssetHandler',
        'ServiceValidator',
        'PerformanceTracker',
        
        # Other agents
        'DiscoveryAgentOrchestrator',
        # 'BaseDiscoveryAgent',  # ARCHIVED: pseudo-agent base class
        # 'AssetInventoryAgent',  # ARCHIVED: pseudo-agent
        # 'DataCleansingAgent',  # ARCHIVED: pseudo-agent
        # 'AttributeMappingAgent',  # ARCHIVED: pseudo-agent
        # 'DependencyAnalysisAgent',  # ARCHIVED: pseudo-agent
        # 'TechDebtAnalysisAgent',  # ARCHIVED: pseudo-agent
        'AgentCommunicationProtocol',
        'AgentIntegrationLayer',
        # 'DataImportValidationAgent'  # ARCHIVED: pseudo-agent
    ]
    
except ImportError as e:
    # Graceful fallback if some agents are not available
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Some agent modules not available: {e}")
    
    __all__ = [] 