"""
Agents package for the AI Force Migration Platform.
Contains specialized agents for discovery, analysis, and orchestration.
"""

# Import key agent classes for easier access
try:
    from .discovery_agent_orchestrator import DiscoveryAgentOrchestrator
    from .base_discovery_agent import BaseDiscoveryAgent
    from .asset_inventory_agent import AssetInventoryAgent
    from .data_cleansing_agent import DataCleansingAgent
    from .attribute_mapping_agent import AttributeMappingAgent
    from .dependency_analysis_agent import DependencyAnalysisAgent
    from .tech_debt_analysis_agent import TechDebtAnalysisAgent
    from .agent_communication_protocol import AgentCommunicationProtocol
    from .agent_integration_layer import AgentIntegrationLayer
    from .data_import_validation_agent import DataImportValidationAgent
    

    
    __all__ = [
        'DiscoveryAgentOrchestrator',
        'BaseDiscoveryAgent', 
        'AssetInventoryAgent',
        'DataCleansingAgent',
        'AttributeMappingAgent',
        'DependencyAnalysisAgent',
        'TechDebtAnalysisAgent',
        'AgentCommunicationProtocol',
        'AgentIntegrationLayer',
        'DataImportValidationAgent'
    ]
    
except ImportError as e:
    # Graceful fallback if some agents are not available
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Some agent modules not available: {e}")
    
    __all__ = [] 