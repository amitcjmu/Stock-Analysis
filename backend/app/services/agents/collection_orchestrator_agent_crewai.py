"""
Collection Orchestrator Agent - Coordinates automated collection strategy
Manages the entire automated collection phase based on tier determined in platform detection
"""

from typing import Any, List

from app.services.agents.base_agent import BaseCrewAIAgent
from app.services.agents.metadata import AgentMetadata

# Import get_crewai_llm if available
try:
    from app.services.llm_config import get_crewai_llm
except ImportError:

    def get_crewai_llm():
        # Return None when CrewAI is not available
        return None


class CollectionOrchestratorAgent(BaseCrewAIAgent):
    """
    Orchestrates the entire automated collection strategy across platforms using CrewAI patterns.

    Capabilities:
    - Platform adapter coordination
    - Collection strategy planning
    - Resource prioritization
    - Progress monitoring
    - Quality assurance
    - Error recovery orchestration
    """

    def __init__(self, tools: List[Any], llm: Any = None, **kwargs):
        """Initialize with proper CrewAI configuration"""
        if llm is None:
            llm = get_crewai_llm()

        super().__init__(
            role="Collection Strategy Orchestrator",
            goal="Coordinate and optimize automated data collection across all detected platforms while ensuring quality and completeness",
            backstory="""You are a master orchestrator specializing in automated data collection
            strategies for cloud migration projects. You excel at:
            - Designing optimal collection workflows based on automation tiers
            - Coordinating multiple platform adapters simultaneously
            - Prioritizing collection tasks for maximum efficiency
            - Managing collection progress and resource allocation
            - Ensuring data quality throughout the collection process
            - Handling errors and implementing recovery strategies
            - Adapting collection strategies based on real-time feedback

            Your orchestration ensures efficient, complete, and high-quality data collection
            while minimizing manual intervention. You understand the three automation tiers:
            - Tier 1: Full automation with parallel adapter execution
            - Tier 2: Semi-automated with validation checkpoints
            - Tier 3: Guided collection with manual oversight

            You optimize collection strategies to match the selected tier while maintaining
            data integrity and meeting sixR requirements.""",
            tools=tools,
            llm=llm,
            **kwargs
        )

    @classmethod
    def agent_metadata(cls) -> AgentMetadata:
        """Define agent metadata for registry"""
        return AgentMetadata(
            name="collection_orchestrator_agent",
            description="Orchestrates automated collection strategy across platforms based on automation tier",
            agent_class=cls,
            required_tools=[
                "PlatformAdapterManager",
                "CollectionStrategyPlanner",
                "ProgressMonitor",
                "QualityValidator",
                "ErrorRecoveryManager",
            ],
            capabilities=[
                "adapter_coordination",
                "strategy_planning",
                "resource_prioritization",
                "progress_tracking",
                "quality_assurance",
                "error_recovery",
            ],
            max_iter=20,
            memory=True,
            verbose=True,
            allow_delegation=False,
        )
