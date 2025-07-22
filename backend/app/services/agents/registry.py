"""
Central Agent Registry with auto-discovery
Manages all CrewAI agents and their capabilities
"""

import importlib
import inspect
import logging
import os
from typing import Any, Dict, List, Optional, Type

from app.services.agents.metadata import AgentMetadata

# Optional CrewAI import
try:
    from crewai import Agent
    CREWAI_AVAILABLE = True
except ImportError:
    # Create a dummy Agent class for type hints when CrewAI is not available
    class Agent:
        pass
    CREWAI_AVAILABLE = False

logger = logging.getLogger(__name__)
if not CREWAI_AVAILABLE:
    logger.warning("CrewAI not available - agent functionality limited")

class AgentRegistry:
    """
    Central registry for all CrewAI agents with auto-discovery.
    Features:
    - Automatic agent discovery on startup
    - Dynamic agent instantiation
    - Tool assignment based on requirements
    - Capability-based agent selection
    """
    
    _instance = None
    _agents: Dict[str, AgentMetadata] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._initialized = True
            self.discover_agents()
    
    def discover_agents(self) -> None:
        """Auto-discover all agents in the agents directory"""
        agents_dir = os.path.dirname(__file__)
        
        # Skip base and registry modules
        skip_modules = ['base_agent', 'registry', 'factory', '__init__']
        
        for filename in os.listdir(agents_dir):
            if (filename.endswith('_agent.py') or filename.endswith('_agent_crewai.py')) and not filename.startswith('_'):
                module_name = filename[:-3]
                
                # Skip base modules
                if module_name in skip_modules:
                    continue
                
                try:
                    module = importlib.import_module(f'.{module_name}', package='app.services.agents')
                    
                    # Find all Agent subclasses in the module
                    for name, obj in inspect.getmembers(module):
                        if (inspect.isclass(obj) and 
                            issubclass(obj, Agent) and 
                            obj != Agent and
                            hasattr(obj, 'agent_metadata') and
                            not inspect.isabstract(obj)):
                            
                            try:
                                metadata = obj.agent_metadata()
                                self.register_agent(metadata)
                                logger.info(f"Discovered agent: {metadata.name}")
                            except Exception as e:
                                logger.warning(f"Failed to get metadata for {name}: {e}")
                            
                except Exception as e:
                    logger.error(f"Failed to load agent module {module_name}: {e}")
    
    def register_agent(self, metadata: AgentMetadata) -> None:
        """Register an agent with the registry"""
        self._agents[metadata.name] = metadata
    
    def get_agent(
        self, 
        name: str, 
        tools: List[Any], 
        llm: Any,
        **kwargs
    ) -> Optional[Agent]:
        """Get an instantiated agent by name"""
        if name not in self._agents:
            logger.error(f"Agent {name} not found in registry")
            return None
        
        metadata = self._agents[name]
        
        # Filter tools based on agent requirements
        # Tools have a 'name' attribute that matches the registry name
        agent_tools = [
            tool for tool in tools 
            if hasattr(tool, 'name') and tool.name in metadata.required_tools
        ]
        
        try:
            agent = metadata.agent_class(
                tools=agent_tools,
                llm=llm,
                max_iter=metadata.max_iter,
                memory=metadata.memory,
                verbose=metadata.verbose,
                allow_delegation=metadata.allow_delegation,
                **kwargs
            )
            return agent
        except Exception as e:
            logger.error(f"Failed to instantiate agent {name}: {e}")
            return None
    
    def get_agents_by_capability(self, capability: str) -> List[AgentMetadata]:
        """Get all agents with a specific capability"""
        return [
            metadata for metadata in self._agents.values()
            if capability in metadata.capabilities
        ]
    
    def list_agents(self) -> List[str]:
        """List all registered agent names"""
        return list(self._agents.keys())

# Global registry instance
agent_registry = AgentRegistry()