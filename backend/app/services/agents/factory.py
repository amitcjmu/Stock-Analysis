"""
Agent Factory for dynamic agent creation
"""

from typing import List, Dict, Any, Optional
from app.services.agents.registry import agent_registry
from app.services.tools.registry import tool_registry
from app.services.llm_config import get_crewai_llm
import logging

logger = logging.getLogger(__name__)

class AgentFactory:
    """
    Factory for creating CrewAI agents with proper configuration.
    Handles:
    - Dynamic agent instantiation
    - Tool assignment based on requirements
    - LLM configuration
    - Context injection
    """
    
    def __init__(self):
        self.llm = get_crewai_llm()
        self.tool_registry = tool_registry
        self.agent_registry = agent_registry
    
    def create_agent(
        self, 
        agent_name: str,
        additional_tools: Optional[List[Any]] = None,
        **kwargs
    ) -> Optional[Any]:
        """
        Create an agent instance with required tools.
        
        Args:
            agent_name: Name of the agent to create
            additional_tools: Extra tools beyond required ones
            **kwargs: Additional agent configuration
        
        Returns:
            Instantiated agent or None if creation fails
        """
        # Get agent metadata
        agent_metadata = self.agent_registry._agents.get(agent_name)
        if not agent_metadata:
            logger.error(f"Agent {agent_name} not found in registry")
            return None
        
        # Gather required tools
        tools = []
        for tool_name in agent_metadata.required_tools:
            tool = self.tool_registry.get_tool(tool_name, for_agent=True)
            if tool:
                tools.append(tool)
            else:
                logger.warning(f"Required tool {tool_name} not found for agent {agent_name}")
        
        # Add any additional tools
        if additional_tools:
            tools.extend(additional_tools)
        
        # Create agent instance
        try:
            agent = self.agent_registry.get_agent(
                name=agent_name,
                tools=tools,
                llm=self.llm,
                **kwargs
            )
            
            logger.info(f"Successfully created agent: {agent_name}")
            return agent
            
        except Exception as e:
            logger.error(f"Failed to create agent {agent_name}: {e}")
            return None
    
    def create_validation_crew(self) -> List[Any]:
        """Create all agents needed for data validation"""
        agents = []
        agent_names = ["data_validation_agent"]
        
        for agent_name in agent_names:
            agent = self.create_agent(agent_name)
            if agent:
                agents.append(agent)
        
        return agents
    
    def create_mapping_crew(self) -> List[Any]:
        """Create all agents needed for field mapping"""
        agents = []
        agent_names = ["field_mapping_agent"]
        
        for agent_name in agent_names:
            agent = self.create_agent(agent_name)
            if agent:
                agents.append(agent)
        
        return agents
    
    def create_discovery_crew(self) -> List[Any]:
        """Create all agents needed for full discovery"""
        agents = []
        
        # Create agents in dependency order
        agent_names = [
            "data_validation_agent",
            "field_mapping_agent",
            "data_cleansing_agent",
            "asset_inventory_agent",
            "dependency_analysis_agent",
            "tech_debt_agent"
        ]
        
        for agent_name in agent_names:
            agent = self.create_agent(agent_name)
            if agent:
                agents.append(agent)
            else:
                logger.warning(f"Agent {agent_name} not available, skipping")
        
        return agents

# Global factory instance
agent_factory = AgentFactory()