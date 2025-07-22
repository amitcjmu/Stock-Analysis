"""
Base CrewAI Agent implementation
All discovery agents must inherit from this class
"""

import logging
from abc import abstractmethod
from typing import Any, Dict, List, Optional

from app.core.context import get_current_context
from app.services.agents.metadata import AgentMetadata

# Optional CrewAI import
try:
    from crewai import Agent
except ImportError:
    # Create a dummy Agent class when CrewAI is not available
    class Agent:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

logger = logging.getLogger(__name__)

class BaseCrewAIAgent(Agent):
    """
    Base class for all CrewAI agents.
    Provides:
    - Proper CrewAI Agent inheritance
    - Context awareness for multi-tenancy
    - Standard logging and error handling
    - Metadata registration
    """
    
    def __init__(
        self,
        role: str,
        goal: str,
        backstory: str,
        tools: List[Any],
        llm: Any,
        **kwargs
    ):
        """Initialize base agent with CrewAI patterns"""
        super().__init__(
            role=role,
            goal=goal,
            backstory=backstory,
            tools=tools,
            llm=llm,
            **kwargs
        )
        
        # Multi-tenant context - store without setting as agent attribute
        try:
            self._request_context = get_current_context()
        except:
            # Context may not be available during agent discovery
            self._request_context = None
        
        # Ensure all tools are context-aware
        self._inject_context_into_tools()
    
    def _inject_context_into_tools(self) -> None:
        """Inject tenant context into all tools"""
        if not self._request_context:
            return
            
        for tool in self.tools:
            if hasattr(tool, 'set_context'):
                tool.set_context(self._request_context)
    
    @classmethod
    @abstractmethod
    def agent_metadata(cls) -> AgentMetadata:
        """Return metadata for agent registration"""
        raise NotImplementedError("Each agent must define its metadata")
    
    def execute_with_context(self, inputs: Dict[str, Any]) -> Any:
        """Execute agent task with proper context"""
        # Ensure context is available
        if not self._request_context:
            raise ValueError("No context available for multi-tenant execution")
        
        # Log execution start
        logger.info(
            f"Agent {self.role} executing for client {self._request_context.client_account_id}"
        )
        
        try:
            # Execute through CrewAI's execution method
            result = self.execute(inputs)
            logger.info(f"Agent {self.role} completed successfully")
            return result
        except Exception as e:
            logger.error(f"Agent {self.role} failed: {e}")
            raise