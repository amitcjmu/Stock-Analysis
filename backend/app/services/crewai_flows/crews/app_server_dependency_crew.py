"""
App-Server Dependency Crew - Hosting Relationship Mapping Phase
Enhanced implementation with CrewAI best practices:
- Hierarchical management with Dependency Manager
- Hosting relationship analysis between applications and servers
- Cross-crew collaboration with inventory insights
- Shared memory integration for dependency patterns
"""

import logging
from typing import Any, Dict, Optional

from crewai import Crew, Process

from app.services.crewai_flows.config.crew_factory import (
    create_agent,
    create_crew,
    create_task,
)

from .crew_config import get_optimized_agent_config

# Import advanced CrewAI features with fallbacks
try:
    from crewai.knowledge.knowledge import Knowledge
    from crewai.memory import LongTermMemory

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


class AppServerDependencyCrew:
    """Enhanced App-Server Dependency Crew for hosting relationship mapping"""

    def __init__(self, crewai_service, shared_memory=None, knowledge_base=None):
        self.crewai_service = crewai_service

        # Get proper LLM configuration from our LLM config service
        try:
            from app.services.llm_config import get_crewai_llm

            self.llm_model = get_crewai_llm()
            logger.info("✅ App-Server Dependency Crew using configured DeepInfra LLM")
        except Exception as e:
            logger.warning(f"Failed to get configured LLM, using fallback: {e}")
            self.llm_model = getattr(crewai_service, "llm", None)

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
                    "model": "text-embedding-3-small",
                },
            )
        except Exception as e:
            logger.warning(f"Failed to setup shared memory: {e}")
            return None

    def _setup_knowledge_base(self) -> Optional[Knowledge]:
        """Setup knowledge base for dependency analysis patterns"""
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
                    "model": "text-embedding-3-small",
                },
            )
        except Exception as e:
            logger.warning(f"Failed to setup knowledge base: {e}")
            return None

    def create_agents(self):
        """Create agents with hierarchical management for dependency analysis"""

        # Manager Agent for dependency coordination
        manager_config = get_optimized_agent_config(allow_delegation=True)
        dependency_manager = create_agent(
            role="Dependency Analysis Manager",
            goal="Coordinate comprehensive app-server hosting relationship mapping for migration planning",
            backstory="""You are a systems architect with expertise in enterprise application hosting
            and dependency mapping. You excel at coordinating dependency analysis across complex
            enterprise environments and ensuring comprehensive hosting relationship discovery.""",
            llm=self.llm_model,
            memory=self.shared_memory,
            knowledge=self.knowledge_base,
            verbose=True,
            planning=True if CREWAI_ADVANCED_AVAILABLE else False,
            **manager_config,
        )

        # Hosting Relationship Expert - specialist agent (no delegation)
        specialist_config = get_optimized_agent_config(allow_delegation=False)
        hosting_expert = create_agent(
            role="Hosting Relationship Expert",
            goal="Identify and map application-to-server hosting relationships with migration impact analysis",
            backstory="""You are an expert in application hosting with deep knowledge of enterprise
            infrastructure dependencies. You excel at identifying which applications run on which
            servers and understanding the hosting implications for migration planning.""",
            llm=self.llm_model,
            memory=self.shared_memory,
            knowledge=self.knowledge_base,
            verbose=True,
            collaboration=True if CREWAI_ADVANCED_AVAILABLE else False,
            tools=self._create_hosting_analysis_tools(),
            **specialist_config,
        )

        # Migration Impact Analyst - specialist agent (no delegation)
        migration_impact_analyst = create_agent(
            role="Migration Impact Analyst",
            goal="Assess migration complexity and risk based on app-server dependencies",
            backstory="""You are a migration specialist with extensive experience in assessing the
            impact of hosting relationships on migration projects. You excel at identifying migration
            risks, complexity factors, and sequencing requirements based on dependencies.""",
            llm=self.llm_model,
            memory=self.shared_memory,
            knowledge=self.knowledge_base,
            verbose=True,
            collaboration=True if CREWAI_ADVANCED_AVAILABLE else False,
            tools=self._create_impact_analysis_tools(),
            **specialist_config,
        )

        return [dependency_manager, hosting_expert, migration_impact_analyst]

    def create_tasks(self, agents, asset_inventory: Dict[str, Any]):
        """Create hierarchical tasks for app-server dependency analysis"""
        manager, hosting_expert, migration_impact_analyst = agents

        servers = asset_inventory.get("servers", [])
        applications = asset_inventory.get("applications", [])

        # Planning Task - Manager coordinates dependency analysis approach
        planning_task = create_task(
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
            expected_output=(
                "Comprehensive dependency analysis execution plan with hosting discovery "
                "strategy and impact assessment approach"
            ),
            agent=manager,
            tools=[],
        )

        # Hosting Relationship Discovery Task
        hosting_discovery_task = create_task(
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
            tools=self._create_hosting_analysis_tools(),
        )

        # Migration Impact Assessment Task
        impact_assessment_task = create_task(
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
            tools=self._create_impact_analysis_tools(),
        )

        return [planning_task, hosting_discovery_task, impact_assessment_task]

    def create_crew(self, asset_inventory: Dict[str, Any]):
        """Create hierarchical crew for app-server dependency analysis"""
        agents = self.create_agents()
        tasks = self.create_tasks(agents, asset_inventory)

        # Use hierarchical process if advanced features available
        process = (
            Process.hierarchical if CREWAI_ADVANCED_AVAILABLE else Process.sequential
        )

        crew_config = {
            "agents": agents,
            "tasks": tasks,
            "process": process,
            "verbose": True,
            "max_iterations": 10,  # Limit total crew iterations
            "step_callback": lambda step: logger.info(f"Crew step {step}"),
        }

        # Add advanced features if available
        if CREWAI_ADVANCED_AVAILABLE:
            # Ensure manager_llm uses our configured LLM and not gpt-4o-mini
            crew_config.update(
                {
                    "manager_llm": self.llm_model,  # Critical: Use our DeepInfra LLM
                    "planning": True,
                    "planning_llm": self.llm_model,  # Force planning to use our LLM too
                    "memory": True,
                    "knowledge": self.knowledge_base,
                    "share_crew": True,
                    "collaboration": True,
                }
            )

            # Additional environment override to prevent any gpt-4o-mini fallback
            import os

            os.environ["OPENAI_MODEL_NAME"] = (
                str(self.llm_model)
                if isinstance(self.llm_model, str)
                else "deepinfra/meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"
            )

        logger.info(
            f"Creating App-Server Dependency Crew with "
            f"{process.name if hasattr(process, 'name') else 'sequential'} process"
        )
        logger.info(
            f"Using LLM: {self.llm_model if isinstance(self.llm_model, str) else 'Unknown'}"
        )
        return create_crew(**crew_config)

    def _create_hosting_analysis_tools(self):
        """Create tools for hosting relationship analysis"""
        # For now, return empty list - tools will be implemented in Task 7
        return []

    def _create_impact_analysis_tools(self):
        """Create tools for migration impact analysis"""
        # For now, return empty list - tools will be implemented in Task 7
        return []


def create_app_server_dependency_crew(
    crewai_service, asset_inventory: Dict[str, Any], shared_memory=None
) -> Crew:
    """
    Create enhanced App-Server Dependency Crew with inventory intelligence
    Uses asset inventory insights from shared memory to map hosting relationships
    """

    # Access inventory insights from shared memory
    if shared_memory:
        logger.info(
            "🧠 App-Server Dependency Crew accessing asset inventory insights from shared memory"
        )

    try:
        # Dependency Manager - Enhanced with inventory context
        dependency_manager = create_agent(
            role="Dependency Manager",
            goal="Orchestrate comprehensive app-to-server dependency mapping using asset inventory intelligence",
            backstory="""Senior infrastructure architect with 15+ years managing enterprise hosting relationships.
            Expert in leveraging asset inventory intelligence to optimize dependency mapping and hosting analysis.
            Capable of coordinating multiple specialists to achieve comprehensive hosting relationship mapping.""",
            llm=crewai_service.llm,
            manager=True,
            delegation=True,
            max_delegation=2,
            memory=shared_memory,  # Access inventory insights
            planning=True,
            verbose=True,
            step_callback=lambda step: logger.info(f"Dependency Manager: {step}"),
        )

        # Hosting Relationship Expert - Enhanced with inventory intelligence
        hosting_expert = create_agent(
            role="Hosting Relationship Expert",
            goal="Map application-to-server hosting relationships using inventory intelligence",
            backstory="""Expert in hosting relationship analysis with deep knowledge of application deployment patterns.
            Specializes in using asset inventory intelligence to identify hosting relationships and resource mappings.
            Skilled in cross-referencing application and server data to determine hosting dependencies.""",
            llm=crewai_service.llm,
            memory=shared_memory,  # Access shared insights
            collaboration=True,
            verbose=True,
            tools=[
                _create_hosting_analysis_tool(asset_inventory),
                _create_topology_mapping_tool(),
                _create_relationship_validation_tool(),
            ],
        )

        # Migration Impact Analyst - Enhanced with hosting context
        migration_analyst = create_agent(
            role="Migration Impact Analyst",
            goal="Analyze migration complexity using hosting relationship context",
            backstory="""Specialist in migration impact assessment with expertise in hosting dependency analysis.
            Expert in evaluating migration complexity based on hosting relationships and resource dependencies.
            Capable of generating actionable migration recommendations based on hosting topology.""",
            llm=crewai_service.llm,
            memory=shared_memory,  # Access hosting context
            collaboration=True,
            verbose=True,
            tools=[
                _create_migration_complexity_tool(asset_inventory),
                _create_capacity_analysis_tool(),
                _create_impact_assessment_tool(),
            ],
        )

        # Enhanced planning task that leverages inventory intelligence
        planning_task = create_task(
            description=f"""
            Plan comprehensive app-server dependency mapping using asset inventory intelligence.

            INVENTORY INTELLIGENCE CONTEXT:
            - Servers available: {len(asset_inventory.get('servers', []))}
            - Applications available: {len(asset_inventory.get('applications', []))}
            - Devices available: {len(asset_inventory.get('devices', []))}
            - Cross-domain classification completed

            PLANNING REQUIREMENTS:
            1. Review asset inventory for hosting relationship candidates
            2. Identify applications requiring server hosting
            3. Map server capacity and hosting capabilities
            4. Plan hosting relationship discovery approach
            5. Coordinate hosting analysis and migration impact assessment
            6. Set success criteria for dependency mapping

            DELIVERABLE: Comprehensive dependency mapping plan with hosting relationship strategy
            """,
            expected_output="App-server dependency mapping plan with hosting relationship discovery strategy",
            agent=dependency_manager,
            context=[],
            tools=[],
        )

        # Inventory-aware hosting analysis task
        hosting_analysis_task = create_task(
            description=f"""
            Execute comprehensive hosting relationship mapping using asset inventory intelligence.

            ASSET INVENTORY INSIGHTS:
            - Server assets: {asset_inventory.get('servers', [])}
            - Application assets: {asset_inventory.get('applications', [])}
            - Classification metadata: {asset_inventory.get('classification_metadata', {})}

            HOSTING ANALYSIS REQUIREMENTS:
            1. Map applications to their hosting servers using inventory data
            2. Identify hosting patterns and resource utilization
            3. Analyze server capacity and application resource requirements
            4. Validate hosting relationships through cross-reference analysis
            5. Generate hosting topology with resource mappings
            6. Store hosting insights in shared memory for app-app dependency crew

            COLLABORATION: Work with migration analyst to assess hosting complexity and migration impact.
            """,
            expected_output=(
                "Comprehensive hosting relationship mapping with resource utilization "
                "and topology insights"
            ),
            agent=hosting_expert,
            context=[planning_task],
            collaboration=[migration_analyst],
            tools=[
                _create_hosting_analysis_tool(asset_inventory),
                _create_topology_mapping_tool(),
            ],
        )

        # Inventory-aware migration impact task
        migration_impact_task = create_task(
            description="""
            Analyze migration complexity and impact using hosting relationship intelligence.

            HOSTING CONTEXT USAGE:
            - Use hosting relationships identified by hosting expert
            - Analyze migration complexity based on hosting dependencies
            - Assess resource requirements and capacity constraints
            - Evaluate migration risks and effort estimates

            MIGRATION IMPACT TARGETS:
            1. Application migration complexity scoring
            2. Server migration impact assessment
            3. Resource dependency analysis
            4. Migration sequencing recommendations
            5. Risk assessment for hosting changes
            6. Effort estimation for migration planning

            MEMORY STORAGE: Store migration insights in shared memory for technical debt crew.
            """,
            expected_output="Migration impact assessment with complexity scoring and risk analysis",
            agent=migration_analyst,
            context=[hosting_analysis_task],
            collaboration=[hosting_expert],
            tools=[
                _create_migration_complexity_tool(asset_inventory),
                _create_capacity_analysis_tool(),
            ],
        )

        # Create crew with hierarchical process and shared memory
        crew = create_crew(
            agents=[dependency_manager, hosting_expert, migration_analyst],
            tasks=[planning_task, hosting_analysis_task, migration_impact_task],
            process=Process.hierarchical,
            manager_llm=crewai_service.llm,
            planning=True,
            planning_llm=getattr(crewai_service, "planning_llm", crewai_service.llm),
            memory=True,
            verbose=True,
            share_crew=True,  # Enable cross-crew collaboration
        )

        logger.info(
            "✅ Enhanced App-Server Dependency Crew created with inventory intelligence"
        )
        return crew

    except Exception as e:
        logger.error(f"Failed to create enhanced App-Server Dependency Crew: {e}")
        # Fallback to basic crew
        return _create_fallback_app_server_dependency_crew(
            crewai_service, asset_inventory
        )


def _create_hosting_analysis_tool(asset_inventory: Dict[str, Any]):
    """Create tool for hosting relationship analysis"""

    # Placeholder for hosting analysis tool - will be implemented in Task 7
    class HostingAnalysisTool:
        def analyze_hosting_relationships(self, data):
            return (
                f"Hosting analysis for {len(asset_inventory.get('servers', []))} servers "
                f"and {len(asset_inventory.get('applications', []))} applications"
            )

    return HostingAnalysisTool()


def _create_topology_mapping_tool():
    """Create tool for topology mapping"""

    # Placeholder for topology mapping tool - will be implemented in Task 7
    class TopologyMappingTool:
        def map_topology(self, data):
            return "Topology mapping analysis"

    return TopologyMappingTool()


def _create_relationship_validation_tool():
    """Create tool for relationship validation"""

    # Placeholder for relationship validation tool - will be implemented in Task 7
    class RelationshipValidationTool:
        def validate_relationships(self, data):
            return "Relationship validation analysis"

    return RelationshipValidationTool()


def _create_migration_complexity_tool(asset_inventory: Dict[str, Any]):
    """Create tool for migration complexity analysis"""

    # Placeholder for migration complexity tool - will be implemented in Task 7
    class MigrationComplexityTool:
        def analyze_complexity(self, data):
            return f"Migration complexity analysis for {len(asset_inventory.get('servers', []))} servers"

    return MigrationComplexityTool()


def _create_capacity_analysis_tool():
    """Create tool for capacity analysis"""

    # Placeholder for capacity analysis tool - will be implemented in Task 7
    class CapacityAnalysisTool:
        def analyze_capacity(self, data):
            return "Capacity analysis"

    return CapacityAnalysisTool()


def _create_impact_assessment_tool():
    """Create tool for impact assessment"""

    # Placeholder for impact assessment tool - will be implemented in Task 7
    class ImpactAssessmentTool:
        def assess_impact(self, data):
            return "Impact assessment analysis"

    return ImpactAssessmentTool()


def _create_fallback_app_server_dependency_crew(
    crewai_service, asset_inventory: Dict[str, Any]
) -> Crew:
    """Create fallback crew when enhanced features fail"""
    logger.info("Creating fallback App-Server Dependency Crew")

    # Basic crew with minimal functionality
    crew_instance = AppServerDependencyCrew(crewai_service)
    return crew_instance.create_crew(asset_inventory)
