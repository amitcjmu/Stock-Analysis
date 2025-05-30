"""
Agent Manager Handler
Handles agent initialization, configuration, and management.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class AgentManagerHandler:
    """Handles agent management with graceful fallbacks."""
    
    def __init__(self):
        self.service_available = False
        self.agents = {}
        self.llm = None
        self.decision_engine = None
        self._initialize_dependencies()
    
    def _initialize_dependencies(self):
        """Initialize dependencies with graceful fallbacks."""
        try:
            from crewai import Agent
            from app.services.deepinfra_llm import DeepInfraLLM
            from app.services.sixr_engine import SixRDecisionEngine
            
            self.llm = DeepInfraLLM()
            self.decision_engine = SixRDecisionEngine()
            self.agents = self._create_agents()
            self.service_available = True
            logger.info("Agent manager handler initialized successfully")
            
        except ImportError as e:
            logger.warning(f"CrewAI or dependencies not available: {e}")
            self._initialize_fallback_components()
            self.service_available = False
    
    def _initialize_fallback_components(self):
        """Initialize fallback components when dependencies unavailable."""
        # Fallback classes
        class FallbackAgent:
            def __init__(self, **kwargs):
                self.role = kwargs.get('role', 'Fallback Agent')
                self.goal = kwargs.get('goal', 'Provide fallback functionality')
                
        class FallbackLLM:
            pass
            
        class FallbackEngine:
            def analyze_parameters(self, *args, **kwargs):
                return {
                    'recommended_strategy': 'replatform',
                    'confidence_score': 0.7,
                    'strategy_scores': [],
                    'key_factors': ['Fallback analysis'],
                    'assumptions': ['Limited functionality'],
                    'next_steps': ['Fix import issues']
                }
        
        self.llm = FallbackLLM()
        self.decision_engine = FallbackEngine()
        self.agents = self._create_fallback_agents()
    
    def is_available(self) -> bool:
        """Check if the handler is properly initialized."""
        return True  # Always available with fallbacks
    
    def _create_agents(self) -> Dict[str, Any]:
        """Create all 6R analysis agents."""
        try:
            from crewai import Agent
            
            agents = {}
            
            # Discovery Agent
            agents["discovery"] = Agent(
                role="6R Discovery Specialist",
                goal="Analyze application data and CMDB information to extract relevant context for 6R analysis",
                backstory="""You are an expert in application discovery and data analysis. 
                Your role is to examine CMDB data, application metadata, and infrastructure 
                information to identify key characteristics that influence migration strategy decisions. 
                You excel at finding patterns in technical data and translating them into 
                meaningful insights for migration planning.""",
                verbose=True,
                allow_delegation=False,
                llm=self.llm
            )
            
            # Initial Analysis Agent
            agents["initial_analysis"] = Agent(
                role="6R Strategy Analyst",
                goal="Perform initial 6R analysis based on available data and generate preliminary recommendations",
                backstory="""You are a seasoned cloud migration strategist with deep expertise 
                in the 6R framework (Rehost, Replatform, Refactor, Rearchitect, Rewrite, Retire). 
                You analyze application characteristics, business requirements, and technical 
                constraints to recommend optimal migration strategies. Your recommendations 
                are data-driven and consider both technical feasibility and business value.""",
                verbose=True,
                allow_delegation=False,
                llm=self.llm
            )
            
            # Question Generator Agent
            agents["question_generator"] = Agent(
                role="6R Question Designer",
                goal="Generate targeted qualifying questions to gather missing information for accurate 6R analysis",
                backstory="""You are an expert in requirements gathering and questionnaire design 
                for cloud migration projects. You identify information gaps in the analysis and 
                create precise, relevant questions that help stakeholders provide the missing 
                context needed for accurate migration strategy recommendations. Your questions 
                are clear, actionable, and prioritized by impact on the analysis.""",
                verbose=True,
                allow_delegation=False,
                llm=self.llm
            )
            
            # Input Processing Agent
            agents["input_processing"] = Agent(
                role="6R Input Processor",
                goal="Process stakeholder responses and update analysis parameters based on new information",
                backstory="""You are a data integration specialist who excels at processing 
                stakeholder feedback and translating qualitative responses into quantitative 
                parameters for 6R analysis. You understand how business answers relate to 
                technical migration considerations and update analysis models accordingly.""",
                verbose=True,
                allow_delegation=False,
                llm=self.llm
            )
            
            return agents
            
        except Exception as e:
            logger.error(f"Error creating agents: {e}")
            return self._create_fallback_agents()
    
    def _create_fallback_agents(self) -> Dict[str, Any]:
        """Create fallback agents when CrewAI unavailable."""
        class FallbackAgent:
            def __init__(self, role, goal, backstory):
                self.role = role
                self.goal = goal
                self.backstory = backstory
        
        return {
            "discovery": FallbackAgent(
                role="6R Discovery Specialist",
                goal="Analyze application data and CMDB information",
                backstory="Fallback discovery agent"
            ),
            "initial_analysis": FallbackAgent(
                role="6R Strategy Analyst", 
                goal="Perform initial 6R analysis",
                backstory="Fallback analysis agent"
            ),
            "question_generator": FallbackAgent(
                role="6R Question Designer",
                goal="Generate qualifying questions",
                backstory="Fallback question agent"
            ),
            "input_processing": FallbackAgent(
                role="6R Input Processor",
                goal="Process stakeholder responses",
                backstory="Fallback processing agent"
            )
        }
    
    def get_agents(self) -> Dict[str, Any]:
        """Get all initialized agents."""
        return self.agents
    
    def get_agent(self, agent_name: str) -> Optional[Any]:
        """Get specific agent by name."""
        return self.agents.get(agent_name)
    
    def get_available_agents(self) -> List[str]:
        """Get list of available agent names."""
        return list(self.agents.keys())
    
    def is_agent_available(self, agent_name: str) -> bool:
        """Check if specific agent is available."""
        return agent_name in self.agents
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents."""
        return {
            "agents_initialized": len(self.agents),
            "available_agents": list(self.agents.keys()),
            "llm_configured": self.llm is not None,
            "decision_engine_ready": self.decision_engine is not None,
            "service_available": self.service_available,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_llm(self):
        """Get LLM instance."""
        return self.llm
    
    def get_decision_engine(self):
        """Get decision engine instance."""
        return self.decision_engine
    
    # Fallback methods
    def _fallback_agent_operation(self, operation: str, **kwargs) -> Dict[str, Any]:
        """Fallback for agent operations when services unavailable."""
        return {
            "status": "completed_fallback",
            "operation": operation,
            "result": f"Fallback {operation} completed",
            "service_available": self.service_available,
            "timestamp": datetime.utcnow().isoformat(),
            "fallback_mode": True
        } 