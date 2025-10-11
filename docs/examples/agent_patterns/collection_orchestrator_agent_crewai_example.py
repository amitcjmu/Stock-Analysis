"""
Collection Orchestrator Agent - Coordinates automated collection strategy
Manages the entire automated collection phase based on tier determined in platform detection
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

# Import get_crewai_llm if available
try:
    from app.services.llm_config import get_crewai_llm
except ImportError:

    def get_crewai_llm():
        # Return None when CrewAI is not available
        return None


logger = logging.getLogger(__name__)


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
            goal=(
                "Coordinate and optimize automated data collection across all detected platforms "
                "while ensuring quality and completeness"
            ),
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
            **kwargs,
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
            memory=False,  # Per ADR-024: Use TenantMemoryManager
            verbose=True,
            allow_delegation=False,
        )

    async def orchestrate_collection_with_memory(
        self,
        platform: str,
        collection_method: str,
        automation_tier: int,
        crewai_service: Any,
        client_account_id: int,
        engagement_id: int,
        db: AsyncSession,
    ) -> Dict[str, Any]:
        """
        Orchestrate collection strategy with TenantMemoryManager integration (ADR-024).

        This method demonstrates proper memory integration:
        1. Retrieve historical collection strategy patterns
        2. Provide patterns as context for orchestration
        3. Execute collection orchestration with historical insights
        4. Store discovered patterns for future use

        Args:
            platform: Platform identifier (e.g., 'vmware', 'aws', 'azure')
            collection_method: Method of collection (e.g., 'automated', 'manual', 'hybrid')
            automation_tier: Tier level (1=full automation, 2=semi-automated, 3=guided)
            crewai_service: CrewAI service instance
            client_account_id: Client account ID for multi-tenant isolation
            engagement_id: Engagement ID for pattern scoping
            db: Database session

        Returns:
            Dict containing orchestration results with adapter selections and strategy
        """
        try:
            logger.info(
                f"🧠 Starting collection orchestration with TenantMemoryManager "
                f"(client={client_account_id}, engagement={engagement_id}, "
                f"platform={platform}, tier={automation_tier})"
            )

            # Step 1: Initialize TenantMemoryManager
            memory_manager = TenantMemoryManager(
                crewai_service=crewai_service, database_session=db
            )

            # Step 2: Retrieve historical collection strategy patterns
            logger.info("📚 Retrieving historical collection strategy patterns...")
            historical_patterns = await memory_manager.retrieve_similar_patterns(
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                pattern_type="collection_strategy",
                query_context={
                    "platform": platform,
                    "collection_method": collection_method,
                    "automation_tier": automation_tier,
                },
                limit=10,
            )

            logger.info(f"✅ Found {len(historical_patterns)} historical patterns")

            # Step 3: Build orchestration strategy with historical context
            logger.info("🔍 Building collection strategy with historical insights...")

            # Extract insights from historical patterns
            adapter_recommendations = []
            optimization_insights = []

            for pattern in historical_patterns[:5]:  # Top 5 patterns
                pattern_data = pattern.get("pattern_data", {})
                if "adapter_selections" in pattern_data:
                    adapter_recommendations.append(pattern_data["adapter_selections"])
                if "optimization_patterns" in pattern_data:
                    optimization_insights.append(pattern_data["optimization_patterns"])

            # Build orchestration result
            orchestration_result = {
                "platform": platform,
                "collection_method": collection_method,
                "automation_tier": automation_tier,
                "recommended_adapters": adapter_recommendations,
                "optimization_insights": optimization_insights,
                "historical_context": {
                    "patterns_found": len(historical_patterns),
                    "top_adapters": (
                        adapter_recommendations[:3] if adapter_recommendations else []
                    ),
                },
                "execution_strategy": {
                    "parallel_execution": automation_tier == 1,
                    "validation_checkpoints": automation_tier >= 2,
                    "manual_oversight": automation_tier == 3,
                },
            }

            # Step 4: Store discovered patterns
            logger.info("💾 Storing collection orchestration patterns...")

            pattern_data = {
                "name": f"collection_orchestration_{platform}_{engagement_id}",
                "platform": platform,
                "collection_method": collection_method,
                "automation_tier": automation_tier,
                "adapter_selections": (
                    adapter_recommendations[:3] if adapter_recommendations else []
                ),
                "optimization_patterns": (
                    optimization_insights[:3] if optimization_insights else []
                ),
                "execution_strategy": orchestration_result["execution_strategy"],
                "historical_patterns_used": len(historical_patterns),
            }

            pattern_id = await memory_manager.store_learning(
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                scope=LearningScope.ENGAGEMENT,
                pattern_type="collection_strategy",
                pattern_data=pattern_data,
            )

            logger.info(
                f"✅ Stored collection orchestration pattern with ID: {pattern_id}"
            )

            # Enhance result with memory metadata
            orchestration_result["memory_integration"] = {
                "status": "success",
                "pattern_id": pattern_id,
                "historical_patterns_used": len(historical_patterns),
                "framework": "TenantMemoryManager (ADR-024)",
            }

            return orchestration_result

        except Exception as e:
            logger.error(
                f"❌ Collection orchestration with memory failed: {e}", exc_info=True
            )
            # Fallback to basic orchestration result
            logger.warning("⚠️ Falling back to basic orchestration without memory")
            return {
                "platform": platform,
                "collection_method": collection_method,
                "automation_tier": automation_tier,
                "status": "error",
                "error": str(e),
                "execution_strategy": {
                    "parallel_execution": automation_tier == 1,
                    "validation_checkpoints": automation_tier >= 2,
                    "manual_oversight": automation_tier == 3,
                },
            }
