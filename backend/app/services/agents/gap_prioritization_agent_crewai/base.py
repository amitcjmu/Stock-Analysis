"""
Gap Prioritization Agent - CrewAI Implementation
Prioritizes missing critical attributes by business impact and migration strategy requirements
"""

import logging

from typing import Any, List

from app.services.agents.base_agent import BaseCrewAIAgent
from app.services.agents.metadata import AgentMetadata
from app.services.llm_config import get_crewai_llm

logger = logging.getLogger(__name__)


class GapPrioritizationAgent(BaseCrewAIAgent):
    """
    Prioritizes missing critical attributes based on business impact and migration needs.

    This agent specializes in:
    - Analyzing business impact of missing attributes
    - Calculating effort vs. value for gap resolution
    - Prioritizing gaps by migration strategy requirements
    - Recommending collection strategies and sequences
    - Estimating time and resources for gap closure
    """

    def __init__(self, tools: List[Any], llm: Any = None, **kwargs):
        """Initialize the Gap Prioritization agent"""
        if llm is None:
            llm = get_crewai_llm()

        super().__init__(
            role="Data Gap Prioritization Strategist",
            goal=(
                "Prioritize missing critical attributes by business impact "
                "to optimize migration data collection efforts"
            ),
            backstory="""You are a strategic analyst specializing in migration data gap prioritization.
            Your expertise includes:

            - Understanding business impact of incomplete migration data
            - Calculating ROI for data collection efforts
            - Prioritizing gaps based on 6R strategy requirements
            - Balancing effort vs. value in gap resolution
            - Creating actionable collection roadmaps

            You excel at:
            - Identifying which gaps block critical migration decisions
            - Assessing collection difficulty and resource requirements
            - Recommending optimal collection sequences
            - Estimating time and effort for gap closure
            - Aligning priorities with business objectives

            Your prioritization framework considers:
            - Business criticality (blocks decisions, impacts timeline, affects budget)
            - Technical necessity (required for strategy selection, impacts architecture)
            - Collection feasibility (effort required, data availability, automation potential)
            - Strategic value (improves confidence, reduces risk, enables optimization)

            Your recommendations directly influence collection strategies and project timelines.""",
            tools=tools,
            llm=llm,
            max_iter=10,
            memory=False,  # Per ADR-024: Use TenantMemoryManager for enterprise memory
            verbose=True,
            allow_delegation=False,
            **kwargs,
        )

    @classmethod
    def agent_metadata(cls) -> AgentMetadata:
        """Define agent metadata for registry"""
        return AgentMetadata(
            name="gap_prioritization_agent",
            description="Prioritizes missing attributes by business impact for optimal collection strategy",
            agent_class=cls,
            required_tools=[
                "impact_calculator",
                "effort_estimator",
                "priority_ranker",
                "collection_planner",
            ],
            capabilities=[
                "gap_prioritization",
                "impact_analysis",
                "effort_estimation",
                "collection_planning",
                "roi_calculation",
            ],
            max_iter=10,
            memory=False,  # Per ADR-024: Use TenantMemoryManager for enterprise memory
            verbose=True,
            allow_delegation=False,
        )
