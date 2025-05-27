"""
Agent Manager for CrewAI agents and crews.
Creates and manages specialized AI agents for CMDB analysis and migration planning.
"""

import logging
from typing import Dict, Any, Optional

try:
    from crewai import Agent, Crew, Process
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    # Create mock classes for when CrewAI is not available
    class Agent:
        def __init__(self, **kwargs):
            self.role = kwargs.get('role', 'Mock Agent')
            self.goal = kwargs.get('goal', 'Mock Goal')
            self.backstory = kwargs.get('backstory', 'Mock Backstory')
    
    class Crew:
        def __init__(self, **kwargs):
            self.agents = kwargs.get('agents', [])
            self.tasks = []
    
    class Process:
        sequential = "sequential"

logger = logging.getLogger(__name__)


class AgentManager:
    """Manages creation and lifecycle of AI agents and crews."""
    
    def __init__(self, llm: Optional[Any] = None):
        self.llm = llm
        self.agents = {}
        self.crews = {}
        
        if CREWAI_AVAILABLE and self.llm:
            self._create_agents()
            self._create_crews()
            logger.info("AgentManager initialized with CrewAI agents and crews")
        else:
            logger.warning("AgentManager initialized in mock mode (CrewAI not available or no LLM)")
    
    def reinitialize_with_fresh_llm(self, fresh_llm: Any) -> None:
        """Reinitialize all agents and crews with a fresh LLM instance."""
        if not CREWAI_AVAILABLE:
            logger.warning("Cannot reinitialize agents - CrewAI not available")
            return
        
        logger.info("Reinitializing agents with fresh LLM instance")
        
        # Clear existing agents and crews
        self.agents.clear()
        self.crews.clear()
        
        # Set new LLM
        self.llm = fresh_llm
        
        # Recreate agents and crews
        self._create_agents()
        self._create_crews()
        
        logger.info(f"Successfully reinitialized {len(self.agents)} agents and {len(self.crews)} crews")
    
    def _create_agents(self):
        """Create all specialized agents."""
        
        # 1. CMDB Data Analyst Agent
        self.agents['cmdb_analyst'] = Agent(
            role='Senior CMDB Data Analyst',
            goal='Analyze CMDB data with expert precision and context awareness',
            backstory="""You are a Senior CMDB Data Analyst with over 15 years of experience 
            in enterprise asset management and cloud migration projects. You understand the 
            nuances of different asset types and their specific requirements for migration 
            planning. You excel at identifying asset types, assessing data quality, and 
            providing migration-specific recommendations.""",
            verbose=False,
            allow_delegation=False,
            llm=self.llm,
            memory=False  # Disable memory to avoid OpenAI API calls
        )
        
        # 2. AI Learning Specialist Agent
        self.agents['learning_agent'] = Agent(
            role='AI Learning Specialist',
            goal='Process feedback and continuously improve analysis accuracy',
            backstory="""You are an AI Learning Specialist focused on processing user 
            feedback to improve system accuracy. You excel at identifying patterns in 
            corrections and updating analysis models in real-time. Your expertise lies 
            in pattern recognition, error analysis, and continuous improvement of AI 
            systems through feedback loops.""",
            verbose=False,
            allow_delegation=False,
            llm=self.llm,
            memory=False  # Disable memory to avoid OpenAI API calls
        )
        
        # 3. Data Pattern Recognition Expert
        self.agents['pattern_agent'] = Agent(
            role='Data Pattern Recognition Expert',
            goal='Analyze and understand CMDB data structures and patterns',
            backstory="""You are a Data Pattern Recognition Expert specializing in CMDB 
            export formats. You can quickly identify asset types, field relationships, 
            and data quality issues across different CMDB systems like ServiceNow, BMC 
            Remedy, and others. Your expertise includes format detection, field mapping, 
            and relationship analysis.""",
            verbose=False,
            allow_delegation=False,
            llm=self.llm,
            memory=False  # Disable memory to avoid OpenAI API calls
        )
        
        # 4. Migration Strategy Expert
        self.agents['migration_strategist'] = Agent(
            role='Migration Strategy Expert',
            goal='Analyze assets and recommend optimal 6R migration strategies',
            backstory="""You are a Migration Strategy Expert with deep knowledge of the 
            6R migration strategies (Rehost, Replatform, Refactor, Rearchitect, Retire, 
            Retain). You can assess technical complexity, business impact, and recommend 
            the most appropriate migration approach for each asset. Your expertise includes 
            cloud architecture, application modernization, and migration planning.""",
            verbose=False,
            allow_delegation=False,
            llm=self.llm,
            memory=False  # Disable memory to avoid OpenAI API calls
        )
        
        # 5. Risk Assessment Specialist
        self.agents['risk_assessor'] = Agent(
            role='Risk Assessment Specialist',
            goal='Identify and assess migration risks with mitigation strategies',
            backstory="""You are a Risk Assessment Specialist with expertise in identifying 
            and mitigating migration risks. You understand technical, business, security, 
            and operational risks associated with cloud migrations. Your expertise includes 
            risk quantification, impact analysis, and developing comprehensive mitigation 
            strategies for complex migration projects.""",
            verbose=False,
            allow_delegation=False,
            llm=self.llm,
            memory=False  # Disable memory to avoid OpenAI API calls
        )
        
        # 6. Wave Planning Coordinator
        self.agents['wave_planner'] = Agent(
            role='Wave Planning Coordinator',
            goal='Optimize migration wave planning based on dependencies and priorities',
            backstory="""You are a Wave Planning Coordinator expert who creates optimal 
            migration sequences considering asset dependencies, business priorities, and 
            resource constraints while minimizing business disruption. Your expertise 
            includes dependency analysis, resource optimization, timeline management, 
            and parallel execution planning.""",
            verbose=False,
            allow_delegation=False,
            llm=self.llm,
            memory=False  # Disable memory to avoid OpenAI API calls
        )
        
        logger.info(f"Created {len(self.agents)} specialized agents")
    
    def _create_crews(self):
        """Create collaborative crews."""
        
        # 1. CMDB Analysis Crew
        self.crews['cmdb_analysis'] = Crew(
            agents=[
                self.agents['cmdb_analyst'],
                self.agents['pattern_agent']
            ],
            tasks=[],  # Tasks will be added dynamically
            verbose=False,
            memory=False,  # Disable memory to avoid OpenAI API calls
            process=Process.sequential
        )
        
        # 2. Learning Crew
        self.crews['learning'] = Crew(
            agents=[
                self.agents['learning_agent'],
                self.agents['cmdb_analyst']
            ],
            tasks=[],  # Tasks will be added dynamically
            verbose=False,
            memory=False,  # Disable memory to avoid OpenAI API calls
            process=Process.sequential
        )
        
        # 3. Migration Strategy Crew
        self.crews['migration_strategy'] = Crew(
            agents=[
                self.agents['migration_strategist'],
                self.agents['risk_assessor']
            ],
            tasks=[],  # Tasks will be added dynamically
            verbose=False,
            memory=False,  # Disable memory to avoid OpenAI API calls
            process=Process.sequential
        )
        
        # 4. Wave Planning Crew
        self.crews['wave_planning'] = Crew(
            agents=[
                self.agents['wave_planner'],
                self.agents['migration_strategist']
            ],
            tasks=[],  # Tasks will be added dynamically
            verbose=True,
            memory=True,
            process=Process.sequential
        )
        
        logger.info(f"Created {len(self.crews)} collaborative crews")
    
    def get_agent(self, agent_name: str) -> Optional[Agent]:
        """Get a specific agent by name."""
        return self.agents.get(agent_name)
    
    def get_crew(self, crew_name: str) -> Optional[Crew]:
        """Get a specific crew by name."""
        return self.crews.get(crew_name)
    
    def list_agents(self) -> Dict[str, str]:
        """List all available agents and their roles."""
        return {
            name: agent.role if hasattr(agent, 'role') else 'Unknown Role'
            for name, agent in self.agents.items()
        }
    
    def list_crews(self) -> Dict[str, list]:
        """List all available crews and their agents."""
        crew_info = {}
        for name, crew in self.crews.items():
            if hasattr(crew, 'agents'):
                agent_roles = [
                    agent.role if hasattr(agent, 'role') else 'Unknown Role'
                    for agent in crew.agents
                ]
                crew_info[name] = agent_roles
            else:
                crew_info[name] = []
        return crew_info
    
    def get_agent_capabilities(self) -> Dict[str, Dict[str, str]]:
        """Get detailed capabilities of each agent."""
        capabilities = {}
        
        if CREWAI_AVAILABLE and self.agents:
            capabilities = {
                'cmdb_analyst': {
                    'role': 'Senior CMDB Data Analyst',
                    'expertise': 'Asset type detection, data quality assessment, migration readiness',
                    'specialization': '15+ years in enterprise asset management',
                    'key_skills': 'Asset classification, field validation, migration recommendations'
                },
                'learning_agent': {
                    'role': 'AI Learning Specialist',
                    'expertise': 'Feedback processing and continuous improvement',
                    'specialization': 'Pattern recognition, accuracy enhancement, error correction',
                    'key_skills': 'Feedback analysis, pattern extraction, model updates'
                },
                'pattern_agent': {
                    'role': 'Data Pattern Recognition Expert',
                    'expertise': 'CMDB structure analysis and format adaptation',
                    'specialization': 'Field mapping, data structure understanding, format detection',
                    'key_skills': 'Format detection, field mapping, relationship analysis'
                },
                'migration_strategist': {
                    'role': 'Migration Strategy Expert',
                    'expertise': '6R strategy analysis and migration planning',
                    'specialization': 'Rehost, Replatform, Refactor, Rearchitect, Retire, Retain analysis',
                    'key_skills': 'Strategy recommendation, complexity assessment, migration planning'
                },
                'risk_assessor': {
                    'role': 'Risk Assessment Specialist',
                    'expertise': 'Migration risk analysis and mitigation planning',
                    'specialization': 'Technical, business, security, and operational risk assessment',
                    'key_skills': 'Risk identification, impact analysis, mitigation strategies'
                },
                'wave_planner': {
                    'role': 'Wave Planning Coordinator',
                    'expertise': 'Migration sequencing and dependency management',
                    'specialization': 'Wave optimization, resource planning, timeline management',
                    'key_skills': 'Dependency analysis, wave sequencing, resource optimization'
                }
            }
        
        return capabilities
    
    def validate_agents(self) -> Dict[str, bool]:
        """Validate that all agents are properly configured."""
        validation_results = {}
        
        expected_agents = [
            'cmdb_analyst', 'learning_agent', 'pattern_agent',
            'migration_strategist', 'risk_assessor', 'wave_planner'
        ]
        
        for agent_name in expected_agents:
            agent = self.agents.get(agent_name)
            if agent:
                # Check if agent has required attributes
                has_role = hasattr(agent, 'role') and agent.role
                has_goal = hasattr(agent, 'goal') and agent.goal
                has_backstory = hasattr(agent, 'backstory') and agent.backstory
                
                validation_results[agent_name] = has_role and has_goal and has_backstory
            else:
                validation_results[agent_name] = False
        
        return validation_results
    
    def validate_crews(self) -> Dict[str, bool]:
        """Validate that all crews are properly configured."""
        validation_results = {}
        
        expected_crews = [
            'cmdb_analysis', 'learning', 'migration_strategy', 'wave_planning'
        ]
        
        for crew_name in expected_crews:
            crew = self.crews.get(crew_name)
            if crew:
                # Check if crew has agents
                has_agents = hasattr(crew, 'agents') and len(crew.agents) > 0
                validation_results[crew_name] = has_agents
            else:
                validation_results[crew_name] = False
        
        return validation_results
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        return {
            'crewai_available': CREWAI_AVAILABLE,
            'llm_configured': self.llm is not None,
            'agents_created': len(self.agents),
            'crews_created': len(self.crews),
            'agent_validation': self.validate_agents(),
            'crew_validation': self.validate_crews(),
            'agent_list': self.list_agents(),
            'crew_list': self.list_crews()
        } 