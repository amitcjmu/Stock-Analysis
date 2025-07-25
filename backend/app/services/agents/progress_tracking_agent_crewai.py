"""
Progress Tracking Agent - Monitors manual data collection progress
"""

from typing import Any, List

from app.services.agents.base_agent import BaseCrewAIAgent
from app.services.agents.metadata import AgentMetadata
from app.services.llm_config import get_crewai_llm


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
            **kwargs
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
            memory=True,
            verbose=True,
            allow_delegation=False,
        )
