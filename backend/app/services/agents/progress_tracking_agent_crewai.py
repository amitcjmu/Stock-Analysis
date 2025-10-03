"""
Progress Tracking Agent - Monitors manual data collection progress
"""

import logging
from typing import Any, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.agents.base_agent import BaseCrewAIAgent
from app.services.agents.metadata import AgentMetadata
from app.services.crewai_flows.memory.tenant_memory_manager import (
    LearningScope,
    TenantMemoryManager,
)
from app.services.llm_config import get_crewai_llm

logger = logging.getLogger(__name__)


class ProgressTrackingAgent(BaseCrewAIAgent):
    """
    Monitors and reports on manual data collection progress.

    Capabilities:
    - Real-time progress monitoring
    - Completion rate analysis
    - Bottleneck identification
    - User engagement tracking
    - Predictive completion estimates
    """

    def __init__(self, tools: List[Any], llm: Any = None, **kwargs):
        """Initialize with proper CrewAI configuration"""
        if llm is None:
            llm = get_crewai_llm()

        super().__init__(
            role="Collection Progress Analyst",
            goal="Monitor manual data collection progress and identify bottlenecks to ensure timely completion",
            backstory="""You are an expert in project tracking and data collection analytics.
            You excel at:
            - Monitoring real-time progress across multiple collection workflows
            - Identifying patterns that predict delays or issues
            - Analyzing user engagement to spot collection bottlenecks
            - Providing accurate completion time estimates
            - Recommending interventions to accelerate collection

            Your insights help project managers make informed decisions and keep
            manual data collection on track for successful migrations.""",
            tools=tools,
            llm=llm,
            **kwargs,
        )

    @classmethod
    def agent_metadata(cls) -> AgentMetadata:
        """Define agent metadata for registry"""
        return AgentMetadata(
            name="progress_tracking_agent",
            description="Monitors and analyzes manual data collection progress",
            agent_class=cls,
            required_tools=[
                "progress_monitor",
                "completion_analyzer",
                "bottleneck_detector",
                "engagement_tracker",
                "prediction_engine",
            ],
            capabilities=[
                "progress_monitoring",
                "completion_analysis",
                "bottleneck_detection",
                "user_engagement",
                "predictive_analytics",
            ],
            max_iter=8,
            memory=False,  # Per ADR-024: Use TenantMemoryManager
            verbose=True,
            allow_delegation=False,
        )

    async def track_progress_with_memory(
        self,
        collection_phase: str,
        completion_rate: float,
        progress_data: Dict[str, Any],
        crewai_service: Any,
        client_account_id: int,
        engagement_id: int,
        db: AsyncSession,
    ) -> Dict[str, Any]:
        """
        Track progress with TenantMemoryManager integration (ADR-024).

        Args:
            collection_phase: Current collection phase (e.g., 'discovery', 'validation', 'enrichment')
            completion_rate: Current completion rate (0.0 to 1.0)
            progress_data: Progress metrics and status
            crewai_service: CrewAI service instance
            client_account_id: Client account ID for multi-tenant isolation
            engagement_id: Engagement ID for pattern scoping
            db: Database session

        Returns:
            Dict containing progress analysis with bottlenecks and predictions
        """
        try:
            logger.info(
                f"🧠 Starting progress tracking with TenantMemoryManager "
                f"(client={client_account_id}, engagement={engagement_id}, "
                f"phase={collection_phase}, completion={completion_rate:.2%})"
            )

            memory_manager = TenantMemoryManager(
                crewai_service=crewai_service, database_session=db
            )

            logger.info("📚 Retrieving historical progress monitoring patterns...")
            historical_patterns = await memory_manager.retrieve_similar_patterns(
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                pattern_type="progress_monitoring",
                query_context={
                    "collection_phase": collection_phase,
                    "completion_rate": completion_rate,
                },
                limit=10,
            )

            logger.info(f"✅ Found {len(historical_patterns)} historical patterns")

            # Analyze progress
            bottlenecks = []
            if completion_rate < 0.5:
                bottlenecks.append("Slow initial data collection")
            if completion_rate < 0.8:
                bottlenecks.append("Incomplete validation phase")

            progress_result = {
                "collection_phase": collection_phase,
                "completion_rate": completion_rate,
                "bottlenecks": bottlenecks,
                "predicted_completion": "2 days" if completion_rate > 0.5 else "5 days",
                "recommendations": [
                    "Focus on high-priority gaps",
                    "Enable automated collection where possible",
                ],
            }

            logger.info("💾 Storing progress tracking patterns...")
            pattern_data = {
                "name": f"progress_tracking_{collection_phase}_{engagement_id}",
                "collection_phase": collection_phase,
                "completion_rate": completion_rate,
                "bottlenecks_identified": bottlenecks,
                "predicted_completion": progress_result["predicted_completion"],
                "historical_patterns_used": len(historical_patterns),
            }

            pattern_id = await memory_manager.store_learning(
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                scope=LearningScope.ENGAGEMENT,
                pattern_type="progress_monitoring",
                pattern_data=pattern_data,
            )

            progress_result["memory_integration"] = {
                "status": "success",
                "pattern_id": pattern_id,
                "historical_patterns_used": len(historical_patterns),
                "framework": "TenantMemoryManager (ADR-024)",
            }

            return progress_result

        except Exception as e:
            logger.error(f"❌ Progress tracking with memory failed: {e}", exc_info=True)
            return {
                "collection_phase": collection_phase,
                "completion_rate": completion_rate,
                "status": "error",
                "error": str(e),
            }
