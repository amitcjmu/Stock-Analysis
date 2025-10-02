"""
Architecture Standards Crew - Main Crew Class

This module contains the main ArchitectureStandardsCrew class that orchestrates
the architecture standards analysis workflow.

The crew captures and evaluates architecture requirements with user collaboration,
creating true CrewAI agents for intelligent decision making around engagement-level
architecture standards.

Key Responsibilities:
- Capture comprehensive architecture standards based on industry best practices
- Analyze application technology stacks against supported versions
- Evaluate architecture exceptions based on business constraints
- Generate compliance reports and upgrade recommendations
- Support RBAC-aware standards validation

The crew workflow:
1. Initialize with flow context
2. Create specialized agents
3. Define and execute tasks
4. Process and structure results
5. Return comprehensive analysis

References:
- Original file: architecture_standards_crew.py (lines 61-78, 452-660)
- Pattern source: component_analysis_crew/crew.py
"""

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict

from app.models.assessment_flow import CrewExecutionError
from app.services.crewai_flows.crews.architecture_standards_crew.agents import (
    create_architecture_standards_agents,
)
from app.services.crewai_flows.crews.architecture_standards_crew.fallback import (
    execute_fallback_architecture_standards,
)
from app.services.crewai_flows.crews.architecture_standards_crew.tasks import (
    create_architecture_standards_crew_instance,
    create_architecture_standards_tasks,
)

if TYPE_CHECKING:
    from crewai import Agent, Crew, Task

# CrewAI availability check
try:
    from crewai import Agent, Crew, Task  # noqa: F401, F811

    CREWAI_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("✅ CrewAI imports successful for ArchitectureStandardsCrew")
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"CrewAI not available: {e}")
    CREWAI_AVAILABLE = False


class ArchitectureStandardsCrew:
    """
    Captures and evaluates architecture requirements with user collaboration.

    This crew creates specialized CrewAI agents for intelligent decision making
    around engagement-level architecture standards. It analyzes technology stacks,
    evaluates compliance, and recommends upgrade paths.

    Attributes:
        flow_context: Flow context containing flow_id and other metadata
        agents: List of specialized Agent instances
        crew: CrewAI Crew instance for orchestration

    Methods:
        execute: Execute the architecture standards analysis workflow
        _process_crew_results: Process and structure crew execution results
    """

    def __init__(self, flow_context):
        """
        Initialize the Architecture Standards Crew.

        Args:
            flow_context: Flow context object containing flow_id and metadata
        """
        self.flow_context = flow_context
        logger.info(
            f"🏗️ Initializing Architecture Standards Crew for flow {flow_context.flow_id}"
        )

        if CREWAI_AVAILABLE:
            try:
                # Create specialized agents
                self.agents = create_architecture_standards_agents()

                # Create tasks
                self.tasks = create_architecture_standards_tasks(self.agents)

                # Create crew instance
                self.crew = create_architecture_standards_crew_instance(
                    self.agents, self.tasks
                )

                logger.info(
                    "✅ Architecture Standards Crew initialized with CrewAI agents"
                )
            except Exception as e:
                logger.error(f"Failed to initialize crew components: {e}")
                logger.warning("Falling back to degraded mode")
                self.agents = []
                self.tasks = []
                self.crew = None
        else:
            logger.warning("CrewAI not available, using fallback mode")
            self.agents = []
            self.tasks = []
            self.crew = None

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the architecture standards crew workflow.

        This method orchestrates the complete architecture standards analysis,
        including capturing standards, analyzing application stacks, and
        evaluating exceptions.

        Args:
            context: Execution context containing:
                - engagement_context: Engagement-level context
                - selected_applications: List of application IDs to analyze
                - application_metadata: Metadata for each application
                - existing_standards: Previously defined standards
                - business_constraints: Known business constraints
                - risk_tolerance: Risk tolerance level (low/medium/high)

        Returns:
            Dictionary containing:
                - engagement_standards: Captured architecture standards
                - application_compliance: Compliance analysis per application
                - exceptions: Identified architecture exceptions
                - upgrade_recommendations: Recommended upgrade paths
                - technical_debt_scores: Technical debt scores per application
                - crew_confidence: Confidence score (0-1)
                - recommendations: Implementation recommendations
                - execution_metadata: Execution metadata (timestamps, flow_id, etc.)

        Raises:
            CrewExecutionError: If the crew execution fails
        """
        try:
            logger.info("🏗️ Starting Architecture Standards Crew execution")

            if not CREWAI_AVAILABLE or not self.crew:
                logger.warning("CrewAI not available, using fallback implementation")
                return await execute_fallback_architecture_standards(context)

            # Prepare context for crew execution
            crew_context = {
                "engagement_context": context.get("engagement_context", {}),
                "selected_applications": context.get("selected_applications", []),
                "application_metadata": context.get("application_metadata", {}),
                "existing_standards": context.get("existing_standards", []),
                "business_constraints": context.get("business_constraints", {}),
                "risk_tolerance": context.get("risk_tolerance", "medium"),
                "flow_context": self.flow_context,
            }

            # Execute crew
            logger.info("Executing CrewAI workflow with prepared context")
            result = self.crew.kickoff(inputs=crew_context)

            # Process and structure the results
            processed_result = await self._process_crew_results(result)

            logger.info(
                "✅ Architecture Standards Crew execution completed successfully"
            )
            return processed_result

        except Exception as e:
            logger.error(
                f"❌ Architecture Standards Crew execution failed: {str(e)}",
                exc_info=True,
            )
            raise CrewExecutionError(
                f"Architecture standards analysis failed: {str(e)}"
            )

    async def _process_crew_results(self, result) -> Dict[str, Any]:
        """
        Process and structure crew execution results.

        This method extracts and structures the raw crew results into a
        consistent format for downstream consumption.

        Args:
            result: Raw result from crew.kickoff()

        Returns:
            Structured dictionary with processed results
        """
        try:
            logger.info("Processing Architecture Standards Crew results")

            # Extract standards from crew results
            standards = result.get("engagement_standards", [])
            if isinstance(standards, str):
                # Parse if returned as string (some CrewAI versions do this)
                logger.warning(
                    "Standards returned as string, initializing as empty list"
                )
                standards = []

            # Structure compliance analysis
            compliance = result.get("application_compliance", {})
            if not isinstance(compliance, dict):
                logger.warning("Compliance data not in expected format")
                compliance = {}

            # Extract exceptions
            exceptions = result.get("architecture_exceptions", [])
            if not isinstance(exceptions, list):
                exceptions = []

            # Calculate overall metrics
            confidence_scores = []
            tech_debt_scores = {}

            for app_id, app_compliance in compliance.items():
                if isinstance(app_compliance, dict):
                    score = app_compliance.get("overall_score", 0.0)
                    confidence_scores.append(score / 100.0)  # Convert to 0-1 scale
                    tech_debt_scores[app_id] = (
                        100.0 - score
                    ) / 10.0  # Convert to 0-10 debt scale

            # Calculate overall confidence
            overall_confidence = (
                sum(confidence_scores) / len(confidence_scores)
                if confidence_scores
                else 0.7  # Default confidence if no scores
            )

            processed_result = {
                "engagement_standards": standards,
                "application_compliance": compliance,
                "exceptions": exceptions,
                "upgrade_recommendations": result.get("upgrade_paths", {}),
                "technical_debt_scores": tech_debt_scores,
                "crew_confidence": min(
                    overall_confidence, 0.95
                ),  # Cap at 95% max confidence
                "recommendations": result.get("implementation_guidance", []),
                "execution_metadata": {
                    "crew_type": "architecture_standards",
                    "execution_time": datetime.utcnow().isoformat(),
                    "flow_id": self.flow_context.flow_id,
                    "agent_count": len(self.agents),
                    "task_count": len(self.tasks),
                },
            }

            logger.info(
                f"Processed results: {len(standards)} standards, "
                f"{len(compliance)} applications, "
                f"{len(exceptions)} exceptions"
            )

            return processed_result

        except Exception as e:
            logger.error(
                f"Error processing crew results: {e}",
                exc_info=True,
            )
            # Return basic structure to prevent flow failure
            return {
                "engagement_standards": [],
                "application_compliance": {},
                "exceptions": [],
                "upgrade_recommendations": {},
                "technical_debt_scores": {},
                "crew_confidence": 0.5,  # Low confidence for error case
                "recommendations": [],
                "processing_error": str(e),
                "execution_metadata": {
                    "crew_type": "architecture_standards",
                    "execution_time": datetime.utcnow().isoformat(),
                    "flow_id": self.flow_context.flow_id,
                    "error": True,
                },
            }


# Export main crew class
__all__ = ["ArchitectureStandardsCrew"]
