"""
Component Analysis Crew - Main Crew Class

This module contains the main ComponentAnalysisCrew class that orchestrates
component identification, technical debt analysis, and dependency mapping.

The crew provides enterprise-grade component analysis with graceful degradation
when CrewAI is not available.
"""

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict

from app.models.assessment_flow import (
    ComponentType,
    CrewExecutionError,
    TechDebtSeverity,
)
from app.services.crewai_flows.crews.component_analysis_crew.agents import (
    create_component_analysis_agents,
)
from app.services.crewai_flows.crews.component_analysis_crew.fallback import (
    execute_fallback_analysis,
)
from app.services.crewai_flows.crews.component_analysis_crew.tasks import (
    create_component_analysis_crew_instance,
    create_component_analysis_tasks,
)

if TYPE_CHECKING:
    from crewai import Agent, Crew, Task

logger = logging.getLogger(__name__)

# CrewAI imports with fallback
try:
    from crewai import Agent, Crew, Task  # noqa: F401, F811

    CREWAI_AVAILABLE = True
    logger.info("✅ CrewAI imports successful for ComponentAnalysisCrew")
except ImportError as e:
    logger.warning(f"CrewAI not available: {e}")
    CREWAI_AVAILABLE = False

    # Fallback classes
    class Agent:  # type: ignore[no-redef]
        def __init__(self, **kwargs):
            self.role = kwargs.get("role", "")
            self.goal = kwargs.get("goal", "")
            self.backstory = kwargs.get("backstory", "")

    class Task:  # type: ignore[no-redef]
        def __init__(self, **kwargs):
            self.description = kwargs.get("description", "")
            self.expected_output = kwargs.get("expected_output", "")

    class Crew:  # type: ignore[no-redef]
        def __init__(self, **kwargs):
            self.agents = kwargs.get("agents", [])
            self.tasks = kwargs.get("tasks", [])

        def kickoff(self, inputs=None):
            return {
                "status": "fallback_mode",
                "components": [],
                "tech_debt_analysis": [],
            }


class ComponentAnalysisCrew:
    """
    Identifies components and analyzes technical debt based on discovered metadata.

    This crew goes beyond traditional 3-tier architecture to identify modern component
    patterns and provides detailed technical debt analysis for migration decision making.

    Key Responsibilities:
    - Identify components beyond traditional frontend/middleware/backend patterns
    - Analyze technical debt from Discovery flow metadata
    - Map dependencies and coupling patterns between components
    - Assess migration complexity and modernization opportunities
    - Generate component-level insights for 6R strategy determination
    """

    def __init__(self, flow_context):
        """
        Initialize the Component Analysis Crew.

        Args:
            flow_context: Flow context containing flow_id and other metadata
        """
        self.flow_context = flow_context
        logger.info(
            f"🔍 Initializing Component Analysis Crew for flow {flow_context.flow_id}"
        )

        if CREWAI_AVAILABLE:
            # Check if tools are available
            try:
                from app.services.crewai_flows.tools.component_tools import (  # noqa: F401
                    ComponentDiscoveryTool,
                )

                tools_available = True
            except ImportError:
                logger.warning(
                    "Component analysis tools not yet available, agents will have limited functionality"
                )
                tools_available = False

            self.agents = create_component_analysis_agents(
                tools_available=tools_available
            )
            tasks = create_component_analysis_tasks(self.agents)
            self.crew = create_component_analysis_crew_instance(self.agents, tasks)
            logger.info("✅ Component Analysis Crew initialized with CrewAI agents")
        else:
            logger.warning("CrewAI not available, using fallback mode")
            self.agents = []
            self.crew = None

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the component analysis crew.

        Args:
            context: Execution context containing application metadata and discovery data

        Returns:
            Dictionary containing component analysis results
        """
        try:
            logger.info(
                f"🔍 Starting Component Analysis Crew for application {context.get('application_id')}"
            )

            if not CREWAI_AVAILABLE or not self.crew:
                logger.warning("CrewAI not available, using fallback implementation")
                return await execute_fallback_analysis(context)

            # Prepare context for crew execution
            crew_context = {
                "application_metadata": context.get("application_metadata", {}),
                "discovery_data": context.get("discovery_data", {}),
                "architecture_context": context.get("architecture_standards", []),
                "architecture_standards": context.get("architecture_standards", []),
                "technology_lifecycle": context.get("technology_lifecycle", {}),
                "security_requirements": context.get("security_requirements", {}),
                "architecture_patterns": context.get("architecture_patterns", {}),
                "network_topology": context.get("network_topology", {}),
                "flow_context": self.flow_context,
            }

            # Execute crew
            result = self.crew.kickoff(inputs=crew_context)

            # Process and structure the results
            processed_result = await self._process_crew_results(
                result, context["application_id"]
            )

            logger.info(
                f"✅ Component Analysis Crew completed for application {context.get('application_id')}"
            )
            return processed_result

        except Exception as e:
            logger.error(f"❌ Component Analysis Crew execution failed: {str(e)}")
            raise CrewExecutionError(f"Component analysis failed: {str(e)}")

    async def _process_crew_results(
        self, result, application_id: str
    ) -> Dict[str, Any]:
        """
        Process and structure crew execution results.

        Args:
            result: Raw crew execution results
            application_id: ID of the analyzed application

        Returns:
            Structured results dictionary
        """
        try:
            # Extract components from crew results
            components_data = result.get("component_inventory", [])

            # Structure components for flow state
            structured_components = []
            for component in components_data:
                structured_components.append(
                    {
                        "name": component.get("name", "unknown"),
                        "type": component.get("type", ComponentType.CUSTOM.value),
                        "technology_stack": component.get("technology_stack", {}),
                        "responsibilities": component.get("responsibilities", []),
                        "complexity_score": component.get("complexity_score", 5.0),
                        "business_value_score": component.get(
                            "business_value_score", 5.0
                        ),
                        "dependencies": component.get("dependencies", []),
                    }
                )

            # Extract and structure technical debt analysis
            tech_debt_data = result.get("tech_debt_analysis", [])
            structured_tech_debt = []
            component_scores = {}

            for debt_item in tech_debt_data:
                structured_tech_debt.append(
                    {
                        "category": debt_item.get("category", "unknown"),
                        "subcategory": debt_item.get("subcategory", ""),
                        "title": debt_item.get("title", ""),
                        "description": debt_item.get("description", ""),
                        "severity": debt_item.get(
                            "severity", TechDebtSeverity.MEDIUM.value
                        ),
                        "tech_debt_score": debt_item.get("tech_debt_score", 5.0),
                        "component": debt_item.get("component", ""),
                        "remediation_effort_hours": debt_item.get(
                            "remediation_effort_hours", 0
                        ),
                        "impact_on_migration": debt_item.get(
                            "impact_on_migration", "medium"
                        ),
                        "detected_by_agent": "component_analysis_crew",
                        "agent_confidence": debt_item.get("confidence", 0.8),
                    }
                )

                # Track component-level scores
                component_name = debt_item.get("component")
                if component_name:
                    component_scores[component_name] = debt_item.get(
                        "tech_debt_score", 5.0
                    )

            # Calculate average scores for components without explicit scores
            for component in structured_components:
                if component["name"] not in component_scores:
                    component_scores[component["name"]] = component.get(
                        "complexity_score", 5.0
                    )

            return {
                "components": structured_components,
                "tech_debt_analysis": structured_tech_debt,
                "component_scores": component_scores,
                "dependency_map": result.get("dependency_map", {}),
                "migration_groups": result.get("migration_grouping", []),
                "crew_confidence": result.get("confidence_score", 0.8),
                "analysis_insights": result.get("analysis_insights", []),
                "execution_metadata": {
                    "crew_type": "component_analysis",
                    "application_id": application_id,
                    "execution_time": datetime.utcnow().isoformat(),
                    "flow_id": self.flow_context.flow_id,
                },
            }

        except Exception as e:
            logger.error(f"Error processing crew results: {e}")
            # Return basic structure to prevent flow failure
            return {
                "components": [],
                "tech_debt_analysis": [],
                "component_scores": {},
                "dependency_map": {},
                "migration_groups": [],
                "crew_confidence": 0.5,
                "analysis_insights": [],
                "processing_error": str(e),
            }


# Export for backward compatibility
__all__ = ["ComponentAnalysisCrew"]
