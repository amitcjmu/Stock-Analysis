"""
Six R Strategy Crew - Main Crew Implementation

This module contains the main SixRStrategyCrew class that orchestrates
component-level 6R strategy determination with validation and wave planning.

The crew determines optimal migration strategies for each component based on
technical characteristics, business constraints, and integration requirements.

Key Responsibilities:
- Determine optimal 6R strategy for each application component
- Validate compatibility between component treatments within applications
- Generate move group hints for Planning Flow wave coordination
- Assess business value, effort, and risk factors for each strategy
- Provide confidence scoring and detailed rationale for decisions

The crew consists of three specialized agents:
1. Component Modernization Strategist - Determines optimal 6R strategy per component
2. Architecture Compatibility Validator - Validates treatment compatibility
3. Migration Wave Planning Advisor - Provides move group hints for Planning Flow
"""

import logging
from typing import TYPE_CHECKING, Any, Dict, List

from app.models.assessment_flow import CrewExecutionError

if TYPE_CHECKING:
    from crewai import Agent, Crew, Task

logger = logging.getLogger(__name__)

# CrewAI imports with fallback
try:
    from crewai import Agent, Crew, Task  # noqa: F401, F811

    CREWAI_AVAILABLE = True
    logger.info("✅ CrewAI imports successful for SixRStrategyCrew")
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
                "component_treatments": [],
                "overall_strategy": "replatform",
            }


class SixRStrategyCrew:
    """
    Determines component-level 6R strategies with validation.

    This crew analyzes application components and determines the optimal migration
    strategy for each component, validates compatibility between strategies, and
    provides move group hints for wave planning.

    Attributes:
        flow_context: Context information for the current flow
        agents: List of specialized agents for strategy determination
        crew: CrewAI crew instance for execution
    """

    def __init__(self, flow_context):
        """
        Initialize Six R Strategy Crew.

        Args:
            flow_context: Flow context containing flow_id and other metadata
        """
        self.flow_context = flow_context
        logger.info(
            f"📋 Initializing Six R Strategy Crew for flow {flow_context.flow_id}"
        )

        if CREWAI_AVAILABLE:
            self.agents = self._create_agents()
            self.crew = self._create_crew()
            logger.info("✅ Six R Strategy Crew initialized with CrewAI agents")
        else:
            logger.warning("CrewAI not available, using fallback mode")
            self.agents = []
            self.crew = None

    def _create_agents(self) -> List[Agent]:
        """
        Create specialized agents for 6R strategy determination.

        Returns:
            List of three configured Agent instances
        """
        from app.services.crewai_flows.crews.sixr_strategy_crew.agents import (
            create_sixr_strategy_agents,
        )

        # Check if tools are available
        try:
            from app.services.crewai_flows.tools.sixr_tools import (  # noqa: F401
                SixRDecisionEngine,
            )

            tools_available = True
        except ImportError:
            logger.warning(
                "Six R strategy tools not yet available, agents will have limited functionality"
            )
            tools_available = False

        return create_sixr_strategy_agents(tools_available=tools_available)

    def _create_crew(self) -> Crew:
        """
        Create crew with 6R strategy tasks.

        Returns:
            Configured Crew instance ready for execution
        """
        from app.services.crewai_flows.crews.sixr_strategy_crew.tasks import (
            create_sixr_strategy_crew_instance,
            create_sixr_strategy_tasks,
        )

        if not CREWAI_AVAILABLE:
            return None

        tasks = create_sixr_strategy_tasks(self.agents)
        return create_sixr_strategy_crew_instance(self.agents, tasks)

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the six R strategy crew.

        This method orchestrates the execution of all three agents to determine
        component-level 6R strategies, validate compatibility, and generate
        move group hints.

        Args:
            context: Execution context containing:
                - application_id: Application identifier
                - components: List of components to analyze
                - tech_debt_analysis: Technical debt analysis data
                - architecture_standards: Architecture standards and patterns
                - business_context: Business constraints and priorities
                - resource_constraints: Resource availability and constraints
                - application_architecture: Application architecture details
                - integration_patterns: Integration patterns and protocols
                - application_dependencies: Application dependency information
                - business_priorities: Business priorities and goals

        Returns:
            Dictionary containing:
                - component_treatments: List of component-level strategy recommendations
                - overall_strategy: Recommended overall 6R strategy
                - confidence_score: Confidence in the recommendation (0-1)
                - rationale: Detailed explanation of the recommendation
                - move_group_hints: Wave planning recommendations
                - compatibility_issues: List of compatibility issues identified
                - crew_confidence: Overall crew confidence in analysis
                - execution_metadata: Metadata about the execution

        Raises:
            CrewExecutionError: If crew execution fails
        """
        try:
            logger.info(
                f"📋 Starting Six R Strategy Crew for application {context.get('application_id')}"
            )

            if not CREWAI_AVAILABLE or not self.crew:
                logger.warning("CrewAI not available, using fallback implementation")
                return await self._execute_fallback(context)

            # Prepare context for crew execution
            crew_context = {
                "components": context.get("components", []),
                "tech_debt_analysis": context.get("tech_debt_analysis", []),
                "architecture_standards": context.get("architecture_standards", []),
                "business_context": context.get("business_context", {}),
                "resource_constraints": context.get("resource_constraints", {}),
                "application_architecture": context.get("application_architecture", {}),
                "integration_patterns": context.get("integration_patterns", {}),
                "application_dependencies": context.get("application_dependencies", {}),
                "business_priorities": context.get("business_priorities", {}),
                "flow_context": self.flow_context,
            }

            # Execute crew
            result = self.crew.kickoff(inputs=crew_context)

            # Process and structure the results
            processed_result = await self._process_crew_results(
                result, context["application_id"]
            )

            logger.info(
                f"✅ Six R Strategy Crew completed for application {context.get('application_id')}"
            )
            return processed_result

        except Exception as e:
            logger.error(f"❌ Six R Strategy Crew execution failed: {str(e)}")
            raise CrewExecutionError(f"Six R strategy determination failed: {str(e)}")

    async def _execute_fallback(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fallback implementation when CrewAI is not available.

        Args:
            context: Execution context

        Returns:
            Fallback strategy results
        """
        from app.services.crewai_flows.crews.sixr_strategy_crew.fallback import (
            execute_fallback,
        )

        return await execute_fallback(context)

    async def _process_crew_results(
        self, result, application_id: str
    ) -> Dict[str, Any]:
        """
        Process and structure crew execution results.

        Args:
            result: Raw crew execution results
            application_id: Application identifier

        Returns:
            Structured result dictionary
        """
        from app.services.crewai_flows.crews.sixr_strategy_crew.fallback import (
            process_crew_results,
        )

        return process_crew_results(result, application_id, self.flow_context.flow_id)


# Export for backward compatibility
__all__ = ["SixRStrategyCrew"]
