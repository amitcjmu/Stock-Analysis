"""
Agent Coordinator Handler
Handles agent management and coordination operations.
"""

import logging

logger = logging.getLogger(__name__)

class AgentCoordinator:
    """Handles agent coordination with graceful fallbacks."""
    
    def __init__(self):
        self.service_available = False
        self._initialize_dependencies()
    
    def _initialize_dependencies(self):
        """Initialize dependencies with graceful fallbacks."""
        try:
            from app.services.agents import AgentManager
            from app.services.memory import AgentMemory
            
            self.memory = AgentMemory()
            self.agent_manager = None
            self.service_available = True
            logger.info("Agent coordinator initialized successfully")
        except (ImportError, AttributeError, Exception) as e:
            logger.warning(f"Agent coordinator services not available: {e}")
            self.service_available = False
    
    def is_available(self) -> bool:
        """Check if the handler is properly initialized."""
        return True  # Always available with fallbacks
    
    def initialize_agent_manager(self, llm):
        """Initialize agent manager with LLM."""
        try:
            if self.service_available and llm:
                from app.services.agents import AgentManager
                self.agent_manager = AgentManager(llm)
                logger.info("Agent manager initialized with LLM")
        except Exception as e:
            logger.warning(f"Error initializing agent manager: {e}")
    
    def get_agents(self):
        """Get available agents."""
        try:
            if self.agent_manager:
                return self.agent_manager.get_agents()
            return self._fallback_get_agents()
        except Exception as e:
            logger.warning(f"Error getting agents: {e}")
            return self._fallback_get_agents()
    
    def get_crews(self):
        """Get available crews."""
        try:
            if self.agent_manager:
                return self.agent_manager.get_crews()
            return self._fallback_get_crews()
        except Exception as e:
            logger.warning(f"Error getting crews: {e}")
            return self._fallback_get_crews()
    
    def _fallback_get_agents(self):
        """Fallback agents when service unavailable."""
        return {
            "6r_analyst": {"name": "6R Analyst", "role": "Migration Strategy Analyst"},
            "risk_assessor": {"name": "Risk Assessor", "role": "Risk Analysis Specialist"},
            "fallback_mode": True
        }
    
    def _fallback_get_crews(self):
        """Fallback crews when service unavailable."""
        return {
            "migration_crew": {"name": "Migration Analysis Crew", "agents": ["6r_analyst", "risk_assessor"]},
            "fallback_mode": True
        } 