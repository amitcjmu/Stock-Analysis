"""
Technical Debt Crew - 6R Strategy Preparation Phase
Enhanced implementation with CrewAI best practices:
- Hierarchical management with Technical Debt Manager
- 6R strategy analysis (Rehost, Replatform, Refactor, Rearchitect, Retire, Retain)
- Cross-crew collaboration with dependency and inventory insights
- Shared memory integration for migration patterns
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

class TechnicalDebtCrew:
    """Enhanced Technical Debt Crew for 6R strategy preparation"""
    
    def __init__(self, crewai_service, shared_memory=None, knowledge_base=None):
        self.crewai_service = crewai_service
        
        # Get proper LLM configuration from our LLM config service
        try:
            from app.services.llm_config import get_crewai_llm
            self.llm = get_crewai_llm()
            logger.info("✅ Technical Debt Crew using configured DeepInfra LLM")
        except Exception as e:
            logger.warning(f"Failed to get configured LLM, using fallback: {e}")
            self.llm = getattr(crewai_service, 'llm', None)
        
        # Setup shared memory and knowledge base
        self.shared_memory = shared_memory or self._setup_shared_memory()
        self.knowledge_base = knowledge_base or self._setup_knowledge_base()
        
        logger.info("✅ Technical Debt Crew initialized with 6R strategy analysis")
    
    def _setup_shared_memory(self) -> Optional[LongTermMemory]:
        """Setup shared memory for technical debt and migration pattern insights"""
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
        """Setup knowledge base for 6R strategy patterns"""
        if not CREWAI_ADVANCED_AVAILABLE:
            logger.warning("Knowledge base not available - using fallback")
            return None
        
        try:
            return Knowledge(
                sources=[
                    "backend/app/knowledge_bases/migration_strategy_patterns.json"
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
        """Create agents with hierarchical management for technical debt analysis"""
        
        # Manager Agent for technical debt coordination
        tech_debt_manager = Agent(
            role="Technical Debt Manager",
            goal="Coordinate comprehensive technical debt analysis and 6R migration strategy preparation",
            backstory="""You are a senior enterprise architect with expertise in technical debt analysis 
            and cloud migration strategies. You excel at coordinating complex migration assessments and 
            ensuring comprehensive 6R strategy preparation across diverse technology portfolios.""",
            llm=self.llm,
            memory=None,  # DISABLED: Causing APIStatusError loops
            knowledge=None,  # DISABLED: Causing API errors
            verbose=True,
            allow_delegation=True,
            max_delegation=1,  # REDUCED: From 3 to 1 to prevent loops
            max_execution_time=300,  # ADD: 5 minute timeout
            max_retry=1,  # REDUCED: Prevent retry loops
            planning=False  # DISABLED: Causing API errors
        )
        
        # Legacy Systems Analyst - specialist agent
        legacy_analyst = Agent(
            role="Legacy Systems Analyst", 
            goal="Identify legacy systems and assess technical debt for migration planning",
            backstory="""You are an expert in legacy system analysis with deep knowledge of enterprise 
            technology portfolios. You excel at identifying technical debt, legacy dependencies, and 
            modernization opportunities that impact migration strategy decisions.""",
            llm=self.llm,
            memory=self.shared_memory,
            knowledge=self.knowledge_base,
            verbose=True,
            collaboration=True if CREWAI_ADVANCED_AVAILABLE else False,
            tools=self._create_legacy_analysis_tools()
        )
        
        # Modernization Expert - specialist agent  
        modernization_expert = Agent(
            role="Modernization Expert",
            goal="Assess modernization opportunities and recommend 6R strategies for each asset",
            backstory="""You are a cloud modernization expert with extensive experience in 6R migration 
            strategies. You excel at evaluating technical assets and recommending optimal migration 
            approaches (Rehost, Replatform, Refactor, Rearchitect, Retire, Retain).""",
            llm=self.llm,
            memory=self.shared_memory, 
            knowledge=self.knowledge_base,
            verbose=True,
            collaboration=True if CREWAI_ADVANCED_AVAILABLE else False,
            tools=self._create_modernization_tools()
        )
        
        # Risk Assessment Specialist - specialist agent
        risk_specialist = Agent(
            role="Risk Assessment Specialist",
            goal="Assess migration risks and complexity factors for 6R strategy validation",
            backstory="""You are a migration risk specialist with expertise in assessing technical and 
            business risks associated with cloud migration. You excel at identifying risk factors and 
            validating migration strategies to ensure successful outcomes.""",
            llm=self.llm,
            memory=self.shared_memory,
            knowledge=self.knowledge_base,
            verbose=True,
            collaboration=True if CREWAI_ADVANCED_AVAILABLE else False,
            tools=self._create_risk_assessment_tools()
        )
        
        return [tech_debt_manager, legacy_analyst, modernization_expert, risk_specialist]
    
    def create_tasks(self, agents, asset_inventory: Dict[str, Any], dependencies: Dict[str, Any]):
        """Create hierarchical tasks for technical debt and 6R strategy analysis"""
        manager, legacy_analyst, modernization_expert, risk_specialist = agents
        
        all_assets = []
        for asset_type in ["servers", "applications", "devices"]:
            all_assets.extend(asset_inventory.get(asset_type, []))
        
        app_server_deps = dependencies.get("app_server_dependencies", {})
        app_app_deps = dependencies.get("app_app_dependencies", {})
        
        # Planning Task - Manager coordinates technical debt analysis approach
        planning_task = Task(
            description=f"""Plan comprehensive technical debt analysis and 6R strategy preparation.
            
            Available assets for analysis:
            - Total assets: {len(all_assets)} assets across servers, applications, and devices
            - App-server dependencies: {len(app_server_deps)} hosting relationships
            - App-app dependencies: {len(app_app_deps)} integration relationships
            
            Create a technical debt analysis plan that:
            1. Assigns legacy analysis priorities based on dependencies
            2. Defines 6R strategy assessment methodology
            3. Establishes risk assessment criteria
            4. Plans collaboration between legacy, modernization, and risk specialists
            5. Leverages dependency and inventory insights from shared memory
            
            Use your planning capabilities to coordinate comprehensive migration strategy preparation.""",
            expected_output="Comprehensive technical debt analysis plan with 6R strategy approach and risk assessment methodology",
            agent=manager,
            tools=[]
        )
        
        # Legacy Systems Analysis Task
        legacy_analysis_task = Task(
            description=f"""Identify legacy systems and assess technical debt for migration planning.
            
            Assets to analyze:
            - Total assets: {len(all_assets)} assets
            - Dependency context: App-server and app-app relationships available
            - Sample assets: {all_assets[:3] if all_assets else []}
            
            Legacy Analysis Requirements:
            1. Identify legacy technologies and end-of-life systems
            2. Assess technical debt across infrastructure and applications
            3. Evaluate technology stack modernization needs
            4. Identify security and compliance gaps
            5. Assess skill availability for current technologies
            6. Generate legacy assessment report with modernization priorities
            7. Store legacy insights in shared memory for modernization expert
            
            Collaborate with modernization expert to share legacy discoveries.""",
            expected_output="Comprehensive legacy systems assessment with technical debt analysis and modernization priorities",
            agent=legacy_analyst,
            context=[planning_task],
            tools=self._create_legacy_analysis_tools()
        )
        
        # 6R Strategy Assessment Task
        modernization_task = Task(
            description=f"""Assess modernization opportunities and recommend 6R strategies.
            
            Legacy context: Use insights from legacy analyst
            Asset inventory: {len(all_assets)} assets requiring strategy decisions
            Dependency relationships: App-server and app-app dependencies available
            
            6R Strategy Assessment Requirements:
            1. Evaluate each asset for optimal 6R strategy:
               - Rehost: Lift-and-shift to cloud
               - Replatform: Minimal cloud optimization
               - Refactor: Significant code changes
               - Rearchitect: Major architectural changes
               - Retire: Decommission unnecessary assets
               - Retain: Keep in current environment
            2. Consider dependency constraints in strategy selection
            3. Assess business value vs. effort for each strategy
            4. Generate 6R recommendations with justification
            5. Use legacy analyst insights from shared memory
            
            Collaborate with risk specialist to validate strategy recommendations.""",
            expected_output="Comprehensive 6R strategy recommendations with business justification and dependency considerations",
            agent=modernization_expert,
            context=[legacy_analysis_task],
            tools=self._create_modernization_tools()
        )
        
        # Risk Assessment Task
        risk_assessment_task = Task(
            description=f"""Assess migration risks and complexity factors for 6R strategy validation.
            
            6R strategies: Use recommendations from modernization expert
            Legacy context: Technical debt and modernization insights available
            Dependencies: App-server and app-app relationship constraints
            
            Risk Assessment Requirements:
            1. Assess technical risks for each 6R strategy
            2. Evaluate business continuity risks during migration
            3. Identify dependency-related migration risks
            4. Assess resource and skill requirements
            5. Validate 6R strategy feasibility and timeline
            6. Generate risk mitigation recommendations
            7. Use modernization expert insights from shared memory
            
            Collaborate with all specialists to validate comprehensive risk assessment.""",
            expected_output="Comprehensive risk assessment with 6R strategy validation and mitigation recommendations",
            agent=risk_specialist,
            context=[modernization_task],
            tools=self._create_risk_assessment_tools()
        )
        
        return [planning_task, legacy_analysis_task, modernization_task, risk_assessment_task]
    
    def create_crew(self, asset_inventory: Dict[str, Any], dependencies: Dict[str, Any]):
        """Create hierarchical crew for technical debt and 6R strategy analysis"""
        agents = self.create_agents()
        tasks = self.create_tasks(agents, asset_inventory, dependencies)
        
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
                "manager_llm": self.llm,  # Critical: Use our DeepInfra LLM
                "planning": False,
                "planning_llm": self.llm,  # Force planning to use our LLM too
                "memory": False,
                "knowledge": None,
                "share_crew": False,  # DISABLED: Causing complexity
                "collaboration": False  # DISABLED: Causing complexity
            })
            
            # Additional environment override to prevent any gpt-4o-mini fallback
            import os
            os.environ["OPENAI_MODEL_NAME"] = str(self.llm.model) if hasattr(self.llm, 'model') else "deepinfra/meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"
        
        logger.info(f"Creating Technical Debt Crew with {process.name if hasattr(process, 'name') else 'sequential'} process")
        logger.info(f"Using LLM: {self.llm.model if hasattr(self.llm, 'model') else 'Unknown'}")
        return Crew(**crew_config)
    
    def _create_legacy_analysis_tools(self):
        """Create tools for legacy systems analysis"""
        # For now, return empty list - tools will be implemented in Task 7
        return []
    
    def _create_modernization_tools(self):
        """Create tools for modernization assessment"""
        # For now, return empty list - tools will be implemented in Task 7
        return []
    
    def _create_risk_assessment_tools(self):
        """Create tools for risk assessment"""
        # For now, return empty list - tools will be implemented in Task 7  
        return []

def create_technical_debt_crew(crewai_service, asset_inventory: Dict[str, Any], 
                              dependencies: Dict[str, Any], shared_memory=None, 
                              knowledge_base=None) -> Crew:
    """Factory function to create enhanced Technical Debt Crew"""
    crew_instance = TechnicalDebtCrew(crewai_service, shared_memory, knowledge_base)
    return crew_instance.create_crew(asset_inventory, dependencies)
