"""
App-App Dependency Crew - Integration Dependency Analysis Phase
Enhanced implementation with CrewAI best practices:
- Hierarchical management with Integration Manager
- Application-to-application dependency mapping
- Cross-crew collaboration with hosting and inventory insights
- Shared memory integration for dependency patterns
"""

import logging
import json
from typing import Dict, List, Any, Optional
from crewai import Agent, Task, Crew, Process

# Import advanced CrewAI features with fallbacks
try:
    from crewai.memory import LongTermMemory
    from crewai.knowledge.knowledge import Knowledge
    CREWAI_ADVANCED_AVAILABLE = True
except ImportError:
    CREWAI_ADVANCED_AVAILABLE = False
    # Fallback classes
    class LongTermMemory:
        def __init__(self, **kwargs):
            pass
    class Knowledge:
        def __init__(self, **kwargs):
            pass

logger = logging.getLogger(__name__)

class AppAppDependencyCrew:
    """Enhanced App-App Dependency Crew for integration dependency analysis"""
    
    def __init__(self, crewai_service, shared_memory=None, knowledge_base=None):
        self.crewai_service = crewai_service
        
        # Get proper LLM configuration from our LLM config service
        try:
            from app.services.llm_config import get_crewai_llm
            self.llm_model = get_crewai_llm()
            logger.info("✅ App-App Dependency Crew using configured DeepInfra LLM")
        except Exception as e:
            logger.warning(f"Failed to get configured LLM, using fallback: {e}")
            self.llm_model = getattr(crewai_service, 'llm', None)
        
        # Setup shared memory and knowledge base
        self.shared_memory = shared_memory or self._setup_shared_memory()
        self.knowledge_base = knowledge_base or self._setup_knowledge_base()
        
        logger.info("✅ App-App Dependency Crew initialized with integration analysis")
    
    def _setup_shared_memory(self) -> Optional[LongTermMemory]:
        """Setup shared memory for integration pattern insights"""
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
    
    def _setup_knowledge_base(self) -> Optional[Knowledge]:
        """Setup knowledge base for integration patterns"""
        if not CREWAI_ADVANCED_AVAILABLE:
            logger.warning("Knowledge base not available - using fallback")
            return None
        
        try:
            return Knowledge(
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
        """Create agents with hierarchical management for integration analysis"""
        
        # Manager Agent for integration coordination
        integration_manager = Agent(
            role="Integration Analysis Manager",
            goal="Coordinate comprehensive app-to-app integration dependency mapping for migration planning",
            backstory="""You are an enterprise integration architect with expertise in application 
            integration patterns and dependency mapping. You excel at coordinating integration analysis 
            across complex enterprise application portfolios and ensuring comprehensive dependency discovery.""",
            llm=self.llm_model,
            memory=self.shared_memory,
            knowledge=self.knowledge_base,
            verbose=True,
            allow_delegation=True,
            max_delegation=2,
            planning=True if CREWAI_ADVANCED_AVAILABLE else False
        )
        
        # Integration Pattern Expert - specialist agent
        integration_expert = Agent(
            role="Integration Pattern Expert", 
            goal="Identify and map application integration patterns and dependencies",
            backstory="""You are an expert in enterprise application integration with deep knowledge of 
            integration patterns, APIs, messaging, and data flows. You excel at identifying how applications 
            communicate and depend on each other for business functionality.""",
            llm=self.llm_model,
            memory=self.shared_memory,
            knowledge=self.knowledge_base,
            verbose=True,
            collaboration=True if CREWAI_ADVANCED_AVAILABLE else False,
            tools=self._create_integration_analysis_tools()
        )
        
        # Business Flow Analyst - specialist agent  
        business_flow_analyst = Agent(
            role="Business Flow Analyst",
            goal="Map business process flows and critical application dependencies for migration sequencing",
            backstory="""You are a business process expert with extensive experience in analyzing business 
            workflows and application dependencies. You excel at understanding which applications support 
            critical business processes and how they must be sequenced for migration.""",
            llm=self.llm_model,
            memory=self.shared_memory, 
            knowledge=self.knowledge_base,
            verbose=True,
            collaboration=True if CREWAI_ADVANCED_AVAILABLE else False,
            tools=self._create_business_flow_tools()
        )
        
        return [integration_manager, integration_expert, business_flow_analyst]
    
    def create_tasks(self, agents, asset_inventory: Dict[str, Any], app_server_dependencies: Dict[str, Any]):
        """Create hierarchical tasks for app-app dependency analysis"""
        manager, integration_expert, business_flow_analyst = agents
        
        applications = asset_inventory.get("applications", [])
        hosting_relationships = app_server_dependencies.get("hosting_relationships", {})
        
        # Planning Task - Manager coordinates integration analysis approach
        planning_task = Task(
            description=f"""Plan comprehensive app-to-app integration dependency analysis strategy.
            
            Available assets for analysis:
            - Applications: {len(applications)} identified application assets
            - Hosting context: {len(hosting_relationships)} hosting relationships available
            
            Create an integration analysis plan that:
            1. Assigns integration pattern discovery priorities
            2. Defines dependency mapping methodology for app-to-app relationships
            3. Establishes business flow analysis criteria
            4. Plans collaboration between integration and business flow specialists
            5. Leverages hosting and inventory insights from shared memory
            
            Use your planning capabilities to coordinate comprehensive integration mapping.""",
            expected_output="Comprehensive integration analysis execution plan with pattern discovery strategy and business flow approach",
            agent=manager,
            tools=[]
        )
        
        # Integration Pattern Discovery Task
        integration_discovery_task = Task(
            description=f"""Identify and map application integration patterns and dependencies.
            
            Assets to analyze:
            - Application inventory: {len(applications)} applications
            - Sample applications: {applications[:3] if applications else []}
            - Hosting context: Available from app-server dependency analysis
            
            Integration Analysis Requirements:
            1. Identify API dependencies between applications
            2. Map database sharing and data flow patterns
            3. Discover messaging and event-driven integrations
            4. Identify shared services and middleware dependencies
            5. Map authentication and authorization dependencies
            6. Generate integration dependency matrix
            7. Store integration insights in shared memory for business flow analysis
            
            Collaborate with business flow analyst to share integration discoveries.""",
            expected_output="Comprehensive integration dependency matrix with app-to-app mappings and integration patterns",
            agent=integration_expert,
            context=[planning_task],
            tools=self._create_integration_analysis_tools()
        )
        
        # Business Flow Analysis Task
        business_flow_task = Task(
            description=f"""Map business process flows and critical application dependencies.
            
            Integration context: Use insights from integration expert
            Application inventory: {len(applications)} applications with integration dependencies
            Hosting relationships: Available from previous dependency analysis
            
            Business Flow Analysis Requirements:
            1. Map critical business process flows across applications
            2. Identify single points of failure in business processes
            3. Determine migration sequencing based on business criticality
            4. Assess business continuity risks during migration
            5. Identify opportunities for process optimization
            6. Generate business impact assessment for integration dependencies
            7. Use integration expert insights from shared memory
            
            Collaborate with integration expert to validate business flow mappings.""",
            expected_output="Comprehensive business flow analysis with criticality assessment and migration sequencing recommendations",
            agent=business_flow_analyst,
            context=[integration_discovery_task],
            tools=self._create_business_flow_tools()
        )
        
        return [planning_task, integration_discovery_task, business_flow_task]
    
    def create_crew(self, asset_inventory: Dict[str, Any], app_server_dependencies: Dict[str, Any]):
        """Create hierarchical crew for app-app dependency analysis"""
        agents = self.create_agents()
        tasks = self.create_tasks(agents, asset_inventory, app_server_dependencies)
        
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
            # Ensure manager_llm uses our configured LLM and not gpt-4o-mini
            crew_config.update({
                "manager_llm": self.llm_model,  # Critical: Use our DeepInfra LLM
                "planning": True,
                "planning_llm": self.llm_model,  # Force planning to use our LLM too
                "memory": True,
                "knowledge": self.knowledge_base,
                "share_crew": True,
                "collaboration": True
            })
            
            # Additional environment override to prevent any gpt-4o-mini fallback
            import os
            os.environ["OPENAI_MODEL_NAME"] = str(self.llm_model) if isinstance(self.llm_model, str) else "deepinfra/meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"
        
        logger.info(f"Creating App-App Dependency Crew with {process.name if hasattr(process, 'name') else 'sequential'} process")
        logger.info(f"Using LLM: {self.llm_model if isinstance(self.llm_model, str) else 'Unknown'}")
        return Crew(**crew_config)
    
    def _create_integration_analysis_tools(self):
        """Create tools for integration pattern analysis"""
        # For now, return empty list - tools will be implemented in Task 7
        return []
    
    def _create_business_flow_tools(self):
        """Create tools for business flow analysis"""
        # For now, return empty list - tools will be implemented in Task 7  
        return []

def create_app_app_dependency_crew(crewai_service, asset_inventory: Dict[str, Any], 
                                  app_server_dependencies: Dict[str, Any], shared_memory=None, 
                                  knowledge_base=None) -> Crew:
    """Factory function to create enhanced App-App Dependency Crew"""
    crew_instance = AppAppDependencyCrew(crewai_service, shared_memory, knowledge_base)
    return crew_instance.create_crew(asset_inventory, app_server_dependencies)
