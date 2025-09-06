"""
Gap Analysis AI Agent - Persistent Multi-Tenant Architecture
ADCS AI Analysis & Intelligence Service

This agent uses persistent CrewAI agents per tenant context to intelligently analyze
data gaps in collected assets and provide targeted recommendations for gap resolution.

Implements ADR-015: Persistent Multi-Tenant Agent Architecture
Built by: CC (AI Analysis & Intelligence)
"""

import logging
from typing import Any, Dict, List

try:
    from crewai import Agent, Task

    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    # Create dummy classes for type hints
    Agent = Task = object

# Import TenantScopedAgentPool separately - it should always be available
from app.services.persistent_agents.tenant_scoped_agent_pool import (
    TenantScopedAgentPool,
)

from .gap_analysis_constants import (
    create_error_result,
    get_gap_analysis_metadata,
)
from .gap_analysis_tasks import (
    create_gap_analysis_task,
    create_business_impact_task,
    create_quality_validation_task,
    validate_gap_analysis_output,
)

logger = logging.getLogger(__name__)


class GapAnalysisAgent:
    """
    AI-powered gap analysis service using persistent multi-tenant agents.

    Analyzes collected data to identify missing critical attributes
    for 6R migration strategy recommendations using TenantScopedAgentPool.

    Implements ADR-015: No per-execution agent creation, uses persistent agents.
    """

    def __init__(self, client_account_id: str, engagement_id: str):
        """Initialize gap analysis service with tenant context"""
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
        self.name = "gap_analysis_service"

        if not CREWAI_AVAILABLE:
            raise RuntimeError(
                "CrewAI is required for gap analysis but is not available"
            )

    async def get_persistent_agents(self) -> Dict[str, Agent]:
        """Get persistent agents from TenantScopedAgentPool"""
        if not CREWAI_AVAILABLE:
            raise RuntimeError(
                "CrewAI is required for gap analysis but is not available"
            )

        # Get or create persistent agents for this tenant
        gap_specialist = await TenantScopedAgentPool.get_or_create_agent(
            client_id=self.client_account_id,
            engagement_id=self.engagement_id,
            agent_type="gap_analysis_specialist",
        )

        business_assessor = await TenantScopedAgentPool.get_or_create_agent(
            client_id=self.client_account_id,
            engagement_id=self.engagement_id,
            agent_type="business_impact_assessor",
        )

        quality_validator = await TenantScopedAgentPool.get_or_create_agent(
            client_id=self.client_account_id,
            engagement_id=self.engagement_id,
            agent_type="quality_validator",
        )

        return {
            "gap_specialist": gap_specialist,
            "business_assessor": business_assessor,
            "quality_validator": quality_validator,
        }

    def create_tasks(
        self, inputs: Dict[str, Any], agents: Dict[str, Agent]
    ) -> List[Task]:
        """Create gap analysis tasks"""
        collection_flow_id = inputs.get("collection_flow_id")
        automation_tier = inputs.get("automation_tier", "tier_2")
        business_context = inputs.get("business_context", {})

        tasks = []

        # Task 1: Primary Gap Analysis
        gap_analysis_task = create_gap_analysis_task(
            inputs=inputs,
            agent=agents["gap_specialist"],
            collection_flow_id=collection_flow_id,
            automation_tier=automation_tier,
        )
        tasks.append(gap_analysis_task)

        # Task 2: Business Impact Assessment
        business_impact_task = create_business_impact_task(
            inputs=inputs,
            agent=agents["business_assessor"],
            business_context=business_context,
        )
        tasks.append(business_impact_task)

        # Task 3: Quality Validation
        quality_validation_task = create_quality_validation_task(
            inputs=inputs, agent=agents["quality_validator"]
        )
        tasks.append(quality_validation_task)

        return tasks

    def process_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Process and structure gap analysis results"""
        try:
            # Combine results from all tasks
            combined_results = {
                "service_name": self.name,
                "status": "completed",
                "gap_analysis": {
                    "summary": {
                        "total_framework_attributes": 22,
                        "analysis_completed": True,
                        "tenant_context": f"{self.client_account_id}/{self.engagement_id}",
                    }
                },
                "metadata": get_gap_analysis_metadata(
                    self.client_account_id, self.engagement_id
                ),
                "task_results": results,
            }

            # Validate and process results if available
            if results and validate_gap_analysis_output(results.get("task_0", {})):
                # Extract key metrics from the main analysis task
                main_analysis = results.get("task_0", {})

                combined_results["gap_analysis"]["summary"].update(
                    {
                        "attributes_collected": main_analysis.get(
                            "gap_analysis_summary", {}
                        ).get("attributes_collected", 0),
                        "coverage_percentage": main_analysis.get(
                            "gap_analysis_summary", {}
                        ).get("overall_coverage_percentage", 0),
                        "critical_gaps_count": main_analysis.get(
                            "gap_analysis_summary", {}
                        ).get("critical_gaps_count", 0),
                    }
                )

                # Include detailed analysis
                combined_results["gap_analysis"]["detailed_analysis"] = main_analysis

            logger.info(
                f"Gap analysis completed successfully for tenant {self.client_account_id}/{self.engagement_id}"
            )
            return combined_results

        except Exception as e:
            logger.error(f"Failed to process gap analysis results: {e}")
            return create_error_result(
                service_name=self.name,
                error_code="RESULT_PROCESSING_FAILED",
                error_message=str(e),
                client_account_id=self.client_account_id,
                engagement_id=self.engagement_id,
            )

    async def analyze_data_gaps(
        self,
        collected_data: List[Dict[str, Any]],
        existing_gaps: List[Dict[str, Any]] = None,
        sixr_requirements: Dict[str, Any] = None,
        automation_tier: str = "tier_2",
    ) -> Dict[str, Any]:
        """
        Perform comprehensive gap analysis using persistent agents.

        Args:
            collected_data: List of collected asset data dictionaries
            existing_gaps: List of previously identified gaps
            sixr_requirements: 6R migration requirements context
            automation_tier: Automation tier level (tier_1 to tier_4)

        Returns:
            Comprehensive gap analysis results
        """
        try:
            if not CREWAI_AVAILABLE:
                raise RuntimeError(
                    "CrewAI is not available - gap analysis cannot proceed. "
                    "No mock fallbacks permitted per ADR-015."
                )

            # Get persistent agents for this tenant
            logger.info(
                f"Getting persistent agents for tenant {self.client_account_id}/{self.engagement_id}"
            )
            agents = await self.get_persistent_agents()

            # Prepare analysis inputs
            analysis_inputs = {
                "collected_data": collected_data,
                "existing_gaps": existing_gaps,
                "sixr_requirements": sixr_requirements,
                "automation_tier": automation_tier,
            }

            # Create tasks using persistent agents
            tasks = self.create_tasks(analysis_inputs, agents)

            # Execute gap analysis using persistent agents
            logger.info(
                f"Starting gap analysis for {len(collected_data)} assets using persistent agents"
            )

            # Execute tasks directly with agents
            results = {}
            for i, task in enumerate(tasks):
                try:
                    # Execute individual task with its assigned agent
                    task_result = await task.agent.execute_async(task)
                    results[f"task_{i}"] = task_result
                except Exception as e:
                    logger.error(f"Task {i} execution failed: {e}")
                    results[f"task_{i}"] = {"error": str(e)}

            logger.info("Gap analysis completed using persistent agents")
            return self.process_results(results)

        except Exception as e:
            logger.error(f"Failed to perform gap analysis: {e}")
            return create_error_result(
                service_name=self.name,
                error_code="GAP_ANALYSIS_FAILED",
                error_message=str(e),
                client_account_id=self.client_account_id,
                engagement_id=self.engagement_id,
            )


async def analyze_collection_gaps(
    collected_data: List[Dict[str, Any]],
    client_account_id: str,
    engagement_id: str,
    collection_flow_id: str = None,
    automation_tier: str = "tier_2",
    business_context: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """
    Standalone function for collection gap analysis using persistent agents.

    Args:
        collected_data: List of collected asset data
        client_account_id: Tenant client account ID
        engagement_id: Engagement identifier
        collection_flow_id: Collection flow ID for context
        automation_tier: Automation tier level
        business_context: Additional business context for analysis

    Returns:
        Comprehensive gap analysis results using persistent agents
    """
    try:
        # Initialize gap analysis agent with tenant context
        gap_agent = GapAnalysisAgent(
            client_account_id=client_account_id, engagement_id=engagement_id
        )

        # Execute gap analysis using persistent agents
        logger.info(
            f"Starting gap analysis for collection flow: {collection_flow_id} "
            f"(tenant: {client_account_id}/{engagement_id})"
        )

        results = await gap_agent.analyze_data_gaps(
            collected_data=collected_data,
            existing_gaps=[],
            sixr_requirements=business_context or {},
            automation_tier=automation_tier,
        )

        logger.info(f"Gap analysis completed for collection flow: {collection_flow_id}")
        return results

    except Exception as e:
        logger.error(f"Failed to perform gap analysis: {e}")
        return create_error_result(
            service_name="gap_analysis_service",
            error_code="GAP_ANALYSIS_INIT_FAILED",
            error_message=str(e),
            client_account_id=client_account_id,
            engagement_id=engagement_id,
        )
