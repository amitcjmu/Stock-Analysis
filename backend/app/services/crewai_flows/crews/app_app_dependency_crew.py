"""
App-App Dependency Crew - Integration Dependency Analysis Phase
Enhanced implementation with CrewAI best practices:
- Hierarchical management with Integration Manager
- Application-to-application dependency mapping
- Cross-crew collaboration with hosting and inventory insights
- Shared memory integration for dependency patterns
"""

import logging
from typing import Any, Dict, Optional

from crewai import Agent, Crew, Process, Task

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
            self.llm_model = getattr(crewai_service, "llm", None)

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
                    "model": "text-embedding-3-small",
                },
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
                    "model": "text-embedding-3-small",
                },
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
            planning=True if CREWAI_ADVANCED_AVAILABLE else False,
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
            tools=self._create_integration_analysis_tools(),
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
            tools=self._create_business_flow_tools(),
        )

        return [integration_manager, integration_expert, business_flow_analyst]

    def create_tasks(
        self,
        agents,
        asset_inventory: Dict[str, Any],
        app_server_dependencies: Dict[str, Any],
    ):
        """Create hierarchical tasks for app-app dependency analysis"""
        manager, integration_expert, business_flow_analyst = agents

        applications = asset_inventory.get("applications", [])
        hosting_relationships = app_server_dependencies.get("hosting_relationships", {})

        # Format applications list for agents
        app_summary = []
        for app in applications[:30]:  # Limit for context
            if isinstance(app, dict):
                app_summary.append(
                    {
                        "id": app.get("id", "unknown"),
                        "name": app.get("name", app.get("asset_name", "Unknown")),
                        "type": app.get("type", "application"),
                    }
                )

        # Planning Task - Manager coordinates integration analysis approach
        planning_task = Task(
            description=f"""Plan comprehensive app-to-app integration dependency analysis strategy.

            CRITICAL: You must analyze ONLY the {len(applications)} REAL applications provided.
            DO NOT invent any fictional services or applications.

            Available REAL assets for analysis:
            - Applications: {len(applications)} actual application assets
            - Sample applications: {app_summary}
            - Hosting context: {len(hosting_relationships)} hosting relationships available

            Create an integration analysis plan that:
            1. Focuses on discovering dependencies between REAL applications only
            2. Uses application names and types to infer likely integrations
            3. Establishes criteria for identifying app-to-app dependencies
            4. Plans systematic analysis of the provided application list
            5. Ensures NO fictional services are created

            Remember: ONLY analyze relationships between the applications in the provided list!""",
            expected_output="Integration analysis plan focusing on real application dependencies only",
            agent=manager,
            tools=[],
        )

        # Integration Pattern Discovery Task
        integration_discovery_task = Task(
            description=f"""Identify and map application integration patterns and dependencies.

            CRITICAL INSTRUCTIONS:
            - ONLY analyze the {len(applications)} REAL applications provided
            - DO NOT create any fictional services or applications
            - Base dependencies on application names and types
            - Output must be structured JSON

            REAL Applications to analyze (showing {len(app_summary)} samples):
            {app_summary}

            Analysis Requirements:
            1. Look for naming patterns suggesting integration (e.g., "API", "Service", "Gateway")
            2. Identify frontend/backend relationships based on names
            3. Find database relationships (apps with "DB" or "Database" in related apps)
            4. Map authentication dependencies (apps with "Auth" or "Login")
            5. Discover API integrations (apps with "API" or "Service")

            Required JSON output format:
            {{"app_dependencies": [
                {{
                    "source_id": "actual_app_id",
                    "source_name": "actual_app_name",
                    "target_id": "actual_app_id",
                    "target_name": "actual_app_name",
                    "dependency_type": "api|data|auth|messaging|shared_service",
                    "confidence_score": 0.0-1.0,
                    "is_app_to_app": true,
                    "integration_pattern": "REST API|Database|Auth|Message Queue|etc",
                    "description": "Brief description"
                }}
            ]}}

            Remember: Every dependency MUST reference real application IDs from the provided list!""",
            expected_output="Valid JSON object with app_dependencies array containing real app-to-app mappings",
            agent=integration_expert,
            context=[planning_task],
            tools=self._create_integration_analysis_tools(),
        )

        # Business Flow Analysis Task
        business_flow_task = Task(
            description=f"""Map business process flows and critical application dependencies.

            CRITICAL INSTRUCTIONS:
            - Use ONLY the integration dependencies discovered by the integration expert
            - DO NOT create new applications or services
            - Focus on business impact of REAL dependencies only

            Context:
            - {len(applications)} REAL applications analyzed
            - Integration dependencies from previous task
            - Must validate all references against actual application IDs

            Analysis Requirements:
            1. Group applications by business function based on names
            2. Identify critical paths through connected applications
            3. Determine migration sequence based on dependencies
            4. Assess risk levels for each dependency
            5. Provide migration recommendations

            Required JSON output format:
            {{"business_analysis": {{
                "critical_paths": [
                    {{
                        "path_name": "Critical Business Flow",
                        "applications": ["app_id_1", "app_id_2"],
                        "criticality": "high|medium|low",
                        "description": "Why this path is critical"
                    }}
                ],
                "migration_groups": [
                    {{
                        "group_name": "Group 1",
                        "application_ids": ["app_id_1", "app_id_2"],
                        "sequence": 1,
                        "dependencies": ["Description of dependencies"],
                        "risk_level": "high|medium|low"
                    }}
                ],
                "recommendations": ["Specific migration recommendations based on real dependencies"]
            }}}}

            All application IDs must be from the original {len(applications)} applications!""",
            expected_output="Valid JSON object with business_analysis containing critical paths and migration groups",
            agent=business_flow_analyst,
            context=[integration_discovery_task],
            tools=self._create_business_flow_tools(),
        )

        return [planning_task, integration_discovery_task, business_flow_task]

    def create_crew(
        self, asset_inventory: Dict[str, Any], app_server_dependencies: Dict[str, Any]
    ):
        """Create hierarchical crew for app-app dependency analysis"""
        agents = self.create_agents()
        tasks = self.create_tasks(agents, asset_inventory, app_server_dependencies)

        # Use hierarchical process if advanced features available
        process = (
            Process.hierarchical if CREWAI_ADVANCED_AVAILABLE else Process.sequential
        )

        crew_config = {
            "agents": agents,
            "tasks": tasks,
            "process": process,
            "verbose": True,
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
            f"Creating App-App Dependency Crew with "
            f"{process.name if hasattr(process, 'name') else 'sequential'} process"
        )
        logger.info(
            f"Using LLM: {self.llm_model if isinstance(self.llm_model, str) else 'Unknown'}"
        )
        return Crew(**crew_config)

    def _create_integration_analysis_tools(self):
        """Create tools for integration pattern analysis"""
        # For now, return empty list - tools will be implemented in Task 7
        return []

    def _create_business_flow_tools(self):
        """Create tools for business flow analysis"""
        # For now, return empty list - tools will be implemented in Task 7
        return []


def create_app_app_dependency_crew(
    crewai_service,
    asset_inventory: Dict[str, Any],
    app_server_dependencies: Dict[str, Any],
    shared_memory=None,
    knowledge_base=None,
) -> Crew:
    """Factory function to create enhanced App-App Dependency Crew"""
    crew_instance = AppAppDependencyCrew(crewai_service, shared_memory, knowledge_base)
    return crew_instance.create_crew(asset_inventory, app_server_dependencies)
