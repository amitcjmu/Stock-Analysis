"""
Agent Manager for CrewAI agents and crews.
Creates and manages specialized AI agents for CMDB analysis and migration planning.
"""

import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime

# Check for required environment variables early
CHROMA_OPENAI_API_KEY = os.getenv('CHROMA_OPENAI_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
DEEPINFRA_API_KEY = os.getenv('DEEPINFRA_API_KEY')

# Determine if full CrewAI functionality is available
CREWAI_AVAILABLE = bool(CHROMA_OPENAI_API_KEY or OPENAI_API_KEY or DEEPINFRA_API_KEY)

if not CREWAI_AVAILABLE:
    logging.warning("No AI API keys found. CrewAI functionality will be limited.")

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
    """Manages all CrewAI agents and crews."""
    
    def __init__(self, llm=None):
        """Initialize the agent manager with optional LLM."""
        self.agents = {}
        self.crews = {}
        self.llm = llm
        
        if CREWAI_AVAILABLE and self.llm:
            self._create_agents()
            self._create_crews()
            logger.info(f"Created {len(self.agents)} specialized agents")
            logger.info(f"Created {len(self.crews)} collaborative crews")
        else:
            logger.warning("AgentManager initialized in limited mode (CrewAI not available or no LLM)")
    
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
        """Create all specialized agents with graceful error handling."""
        try:
            from crewai import Agent
            
            # Import asset intelligence tools
            try:
                from app.services.tools.asset_intelligence_tools import get_asset_intelligence_tools
                asset_tools = get_asset_intelligence_tools(field_mapper=None)  # Will be injected later
            except ImportError:
                logger.warning("Asset intelligence tools not available")
                asset_tools = []
            
            agents = {}
            
            # Existing agents...
            # CMDB Data Analyst Agent
            agents["cmdb_analyst"] = Agent(
                role="Senior CMDB Data Analyst", 
                goal="Analyze CMDB data with expert precision using advanced field mapping tools",
                backstory="""You are a world-class expert in enterprise asset management and CMDB data analysis. 
                Your expertise spans across multiple domains including infrastructure discovery, data quality assessment, 
                and migration planning. You have deep knowledge of field mapping patterns and can intelligently 
                interpret data structures from various sources. You use advanced field mapping tools to understand 
                data relationships and provide actionable insights for enterprise IT asset management.""",
                verbose=True,
                allow_delegation=False,
                llm=self.llm,
                memory=False
            )

            # NEW: Asset Intelligence Agent for inventory management
            agents["asset_intelligence"] = Agent(
                role="Asset Inventory Intelligence Specialist",
                goal="Intelligently manage asset inventory operations with advanced learning capabilities and field mapping intelligence",
                backstory="""You are an expert IT Asset Management specialist with deep knowledge of:
                - Enterprise asset classification and categorization patterns
                - Advanced data quality assessment for inventory management
                - Intelligent bulk operations optimization using learned patterns
                - Asset lifecycle management and relationship mapping
                - Field mapping intelligence and data structure analysis
                
                You excel at analyzing asset data patterns using AI intelligence rather than hard-coded rules.
                You leverage field mapping tools to understand data relationships and provide increasingly 
                intelligent inventory management recommendations. You learn from user interactions and asset 
                data patterns to continuously improve your analysis and recommendations.
                
                Your approach is always data-driven, using learned patterns and content analysis to provide
                actionable insights for asset inventory optimization.""",
                tools=asset_tools,  # Asset-specific AI tools
                verbose=True,
                allow_delegation=False, 
                llm=self.llm,
                memory=False
            )

            # Learning Agent with enhanced asset learning capabilities
            agents["learning_agent"] = Agent(
                role="AI Learning Specialist",
                goal="Process feedback and continuously improve analysis accuracy using advanced field mapping learning and asset management insights",
                backstory="""You are an advanced AI learning specialist focused on continuous improvement 
                of the migration analysis platform. Your core competencies include:
                
                - Processing user feedback to extract actionable learning patterns
                - Enhancing field mapping accuracy through experience analysis
                - Improving asset classification and data quality assessment
                - Learning from bulk operation outcomes to optimize future recommendations
                - Identifying patterns in user workflows and preferences
                
                You work closely with field mapping tools to learn new data structure patterns and
                asset management optimization strategies. You ensure the platform becomes more intelligent
                and accurate with each user interaction.""",
                verbose=True,
                allow_delegation=False,
                llm=self.llm,
                memory=False
            )

            # 3. Data Pattern Recognition Expert
            agents['pattern_agent'] = Agent(
                role='Data Pattern Recognition Expert',
                goal='Analyze and understand CMDB data structures and patterns using field mapping intelligence',
                backstory="""You are a Data Pattern Recognition Expert specializing in CMDB 
                export formats. You can quickly identify asset types, field relationships, 
                and data quality issues across different CMDB systems like ServiceNow, BMC 
                Remedy, and others. Your expertise includes format detection, field mapping, 
                and relationship analysis.
                
                ESSENTIAL: You have access to a field_mapping_tool that enables you to:
                - Analyze data columns and identify existing field mappings
                - Discover new field mapping patterns in unfamiliar data formats
                - Learn field mappings from data structure analysis
                - Suggest mappings between available columns and missing required fields
                
                Use this tool to understand data patterns and continuously improve field 
                recognition across different CMDB export formats.""",
                verbose=False,
                allow_delegation=False,
                llm=self.llm,
                memory=True  # Enable memory for OpenAI API calls
            )
            
            # 4. Migration Strategy Expert
            agents['migration_strategist'] = Agent(
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
                memory=True  # Enable memory for OpenAI API calls
            )
            
            # 5. Risk Assessment Specialist
            agents['risk_assessor'] = Agent(
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
                memory=True  # Enable memory for OpenAI API calls
            )
            
            # 6. Wave Planning Coordinator
            agents['wave_planner'] = Agent(
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
                memory=True  # Enable memory for OpenAI API calls
            )
            
            self.agents = agents
            logger.info(f"Created {len(self.agents)} specialized agents")
        
        except Exception as e:
            logger.error(f"Failed to create agents: {e}")
            # Create empty agents as fallback
            self.agents = {}
    
    def _create_crews(self):
        """Create collaborative crews from agents with graceful error handling."""
        try:
            # Import Process here to avoid import errors
            from crewai import Process
            
            # 1. Data Analysis Crew (CMDB analysis and learning)
            self.crews['data_analysis'] = Crew(
                agents=[
                    self.agents['learning_agent'],
                    self.agents['cmdb_analyst']
                ],
                tasks=[],  # Tasks will be added dynamically
                verbose=False,
                memory=True,  # Enable memory for OpenAI API calls
                process=Process.sequential
            )
            
            # 2. Migration Strategy Crew
            self.crews['migration_strategy'] = Crew(
                agents=[
                    self.agents['migration_strategist'],
                    self.agents['risk_assessor']
                ],
                tasks=[],  # Tasks will be added dynamically
                verbose=False,
                memory=True,  # Enable memory for OpenAI API calls
                process=Process.sequential
            )
            
            # 3. Wave Planning Crew
            self.crews['wave_planning'] = Crew(
                agents=[
                    self.agents['wave_planner'],
                    self.agents['migration_strategist']
                ],
                tasks=[],  # Tasks will be added dynamically
                verbose=False,
                memory=True,  # Enable memory for OpenAI API calls
                process=Process.sequential
            )
            
        except Exception as e:
            logger.error(f"Failed to create crews: {e}")
            # Create empty crews as fallback
            self.crews = {
                'data_analysis': None,
                'migration_strategy': None,
                'wave_planning': None
            }
    
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
            'data_analysis', 'migration_strategy', 'wave_planning'
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