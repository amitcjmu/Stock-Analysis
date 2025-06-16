"""
App-Server Dependency Crew - Hosting Relationship Mapping Phase
Enhanced implementation with CrewAI best practices:
- Hierarchical management with Dependency Manager
- Hosting relationship analysis between applications and servers
- Cross-crew collaboration with inventory insights
- Shared memory integration for dependency patterns
"""

import logging
import json
from typing import Dict, List, Any, Optional
from crewai import Agent, Task, Crew, Process

# Import advanced CrewAI features with fallbacks
try:
    from crewai.memory import LongTermMemory
    from crewai.knowledge import KnowledgeBase
    CREWAI_ADVANCED_AVAILABLE = True
except ImportError:
    CREWAI_ADVANCED_AVAILABLE = False
    # Fallback classes
    class LongTermMemory:
        def __init__(self, **kwargs):
            pass
    class KnowledgeBase:
        def __init__(self, **kwargs):
            pass

logger = logging.getLogger(__name__)

class AppServerDependencyCrew:
    """Enhanced App-Server Dependency Crew for hosting relationship mapping"""
    
    def __init__(self, crewai_service, shared_memory=None, knowledge_base=None):
        self.crewai_service = crewai_service
        self.llm = getattr(crewai_service, 'llm', None)
        
        # Setup shared memory and knowledge base
        self.shared_memory = shared_memory or self._setup_shared_memory()
        self.knowledge_base = knowledge_base or self._setup_knowledge_base()
        
        logger.info("✅ App-Server Dependency Crew initialized with hosting analysis")
    
    def _setup_shared_memory(self) -> Optional[LongTermMemory]:
        """Setup shared memory for dependency pattern insights"""
        if not CREWAI_ADVANCED_AVAILABLE:
            logger.warning("Shared memory not available - using fallback")
            return None
        
        try:
            return LongTermMemory(
                storage_type="vector",
                embedder_config={
                    "provider": "openai", 
                    "model": "text-embedding-3-small"
                }
            )
        except Exception as e:
            logger.warning(f"Failed to setup shared memory: {e}")
            return None
    
    def _setup_knowledge_base(self) -> Optional[KnowledgeBase]:
        """Setup knowledge base for dependency analysis patterns"""
        if not CREWAI_ADVANCED_AVAILABLE:
            logger.warning("Knowledge base not available - using fallback")
            return None
        
        try:
            return KnowledgeBase(
                sources=[
                    "backend/app/knowledge_bases/dependency_analysis_patterns.json"
                ],
                embedder_config={
                    "provider": "openai",
                    "model": "text-embedding-3-small"
                }
            )
        except Exception as e:
            logger.warning(f"Failed to setup knowledge base: {e}")
            return None
    
    def create_agents(self):
        """Create agents with hierarchical management for dependency analysis"""
        
        # Manager Agent for dependency coordination
        dependency_manager = Agent(
            role="Dependency Analysis Manager",
            goal="Coordinate comprehensive app-server hosting relationship mapping for migration planning",
            backstory="""You are a systems architect with expertise in enterprise application hosting 
            and dependency mapping. You excel at coordinating dependency analysis across complex 
            enterprise environments and ensuring comprehensive hosting relationship discovery.""",
            llm=self.llm,
            memory=self.shared_memory,
            knowledge=self.knowledge_base,
            verbose=True,
            allow_delegation=True,
            max_delegation=2,
            planning=True if CREWAI_ADVANCED_AVAILABLE else False
        )
        
        # Hosting Relationship Expert - specialist agent
        hosting_expert = Agent(
            role="Hosting Relationship Expert", 
            goal="Identify and map application-to-server hosting relationships with migration impact analysis",
            backstory="""You are an expert in application hosting with deep knowledge of enterprise 
            infrastructure dependencies. You excel at identifying which applications run on which 
            servers and understanding the hosting implications for migration planning.""",
            llm=self.llm,
            memory=self.shared_memory,
            knowledge=self.knowledge_base,
            verbose=True,
            collaboration=True if CREWAI_ADVANCED_AVAILABLE else False,
            tools=self._create_hosting_analysis_tools()
        )
        
        # Migration Impact Analyst - specialist agent  
        migration_impact_analyst = Agent(
            role="Migration Impact Analyst",
            goal="Assess migration complexity and risk based on app-server dependencies",
            backstory="""You are a migration specialist with extensive experience in assessing the 
            impact of hosting relationships on migration projects. You excel at identifying migration 
            risks, complexity factors, and sequencing requirements based on dependencies.""",
            llm=self.llm,
            memory=self.shared_memory, 
            knowledge=self.knowledge_base,
            verbose=True,
            collaboration=True if CREWAI_ADVANCED_AVAILABLE else False,
            tools=self._create_impact_analysis_tools()
        )
        
        return [dependency_manager, hosting_expert, migration_impact_analyst]
    
    def create_tasks(self, agents, asset_inventory: Dict[str, Any]):
        """Create hierarchical tasks for app-server dependency analysis"""
        manager, hosting_expert, migration_impact_analyst = agents
        
        servers = asset_inventory.get("servers", [])
        applications = asset_inventory.get("applications", [])
        
        # Planning Task - Manager coordinates dependency analysis approach
        planning_task = Task(
            description=f"""Plan comprehensive app-server dependency analysis strategy.
            
            Available assets for analysis:
            - Servers: {len(servers)} identified server assets
            - Applications: {len(applications)} identified application assets
            
            Create a dependency analysis plan that:
            1. Assigns hosting relationship discovery priorities
            2. Defines dependency mapping methodology
            3. Establishes migration impact assessment criteria
            4. Plans collaboration between hosting and impact specialists
            5. Leverages inventory insights from shared memory
            
            Use your planning capabilities to coordinate comprehensive dependency mapping.""",
            expected_output="Comprehensive dependency analysis execution plan with hosting discovery strategy and impact assessment approach",
            agent=manager,
            tools=[]
        )
        
        # Hosting Relationship Discovery Task
        hosting_discovery_task = Task(
            description=f"""Identify and map application-to-server hosting relationships.
            
            Assets to analyze:
            - Server inventory: {len(servers)} servers
            - Application inventory: {len(applications)} applications
            - Sample servers: {servers[:3] if servers else []}
            - Sample applications: {applications[:3] if applications else []}
            
            Hosting Analysis Requirements:
            1. Map applications to their hosting servers
            2. Identify virtual machine and container relationships
            3. Determine database hosting patterns
            4. Map web application server dependencies
            5. Identify shared hosting platforms
            6. Generate hosting relationship matrix
            7. Store hosting insights in shared memory for impact analysis
            
            Collaborate with migration impact analyst to share hosting discoveries.""",
            expected_output="Comprehensive hosting relationship matrix with app-server mappings and hosting patterns",
            agent=hosting_expert,
            context=[planning_task],
            tools=self._create_hosting_analysis_tools()
        )
        
        # Migration Impact Assessment Task
        impact_assessment_task = Task(
            description=f"""Assess migration complexity and risk based on hosting dependencies.
            
            Hosting relationships: Use insights from hosting expert
            Server inventory: {len(servers)} servers with hosting dependencies
            Application inventory: {len(applications)} applications with hosting requirements
            
            Impact Analysis Requirements:
            1. Assess migration complexity for each hosting relationship
            2. Identify single points of failure in hosting patterns
            3. Determine migration sequencing requirements
            4. Evaluate infrastructure consolidation opportunities
            5. Assess cloud readiness based on hosting patterns
            6. Generate migration risk assessment
            7. Use hosting expert insights from shared memory
            
            Collaborate with hosting expert to validate impact assessments.""",
            expected_output="Comprehensive migration impact assessment with complexity scoring and risk analysis",
            agent=migration_impact_analyst,
            context=[hosting_discovery_task],
            tools=self._create_impact_analysis_tools()
        )
        
        return [planning_task, hosting_discovery_task, impact_assessment_task]
    
    def create_crew(self, asset_inventory: Dict[str, Any]):
        """Create hierarchical crew for app-server dependency analysis"""
        agents = self.create_agents()
        tasks = self.create_tasks(agents, asset_inventory)
        
        # Use hierarchical process if advanced features available
        process = Process.hierarchical if CREWAI_ADVANCED_AVAILABLE else Process.sequential
        
        crew_config = {
            "agents": agents,
            "tasks": tasks,
            "process": process,
            "verbose": True
        }
        
        # Add advanced features if available
        if CREWAI_ADVANCED_AVAILABLE:
            crew_config.update({
                "manager_llm": self.llm,
                "planning": True,
                "memory": True,
                "knowledge": self.knowledge_base,
                "share_crew": True,
                "collaboration": True
            })
        
        logger.info(f"Creating App-Server Dependency Crew with {process.name if hasattr(process, 'name') else 'sequential'} process")
        return Crew(**crew_config)
    
    def _create_hosting_analysis_tools(self):
        """Create tools for hosting relationship analysis"""
        # For now, return empty list - tools will be implemented in Task 7
        return []
    
    def _create_impact_analysis_tools(self):
        """Create tools for migration impact analysis"""
        # For now, return empty list - tools will be implemented in Task 7  
        return []

def create_app_server_dependency_crew(crewai_service, asset_inventory: Dict[str, Any], 
                                     shared_memory=None, knowledge_base=None) -> Crew:
    """Factory function to create enhanced App-Server Dependency Crew"""
    crew_instance = AppServerDependencyCrew(crewai_service, shared_memory, knowledge_base)
    return crew_instance.create_crew(asset_inventory)
