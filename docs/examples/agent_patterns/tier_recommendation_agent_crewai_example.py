"""
Tier Recommendation Agent - Automation tier recommendation
Recommends optimal automation tier based on platform capabilities and requirements
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


class TierRecommendationAgent(BaseCrewAIAgent):
    """
    Recommends appropriate automation tier using CrewAI patterns.

    Capabilities:
    - Complexity assessment
    - Automation feasibility analysis
    - Risk evaluation
    - Tier matching
    - Recommendation justification
    """

    def __init__(self, tools: List[Any], llm: Any = None, **kwargs):
        """Initialize with proper CrewAI configuration"""
        if llm is None:
            llm = get_crewai_llm()

        super().__init__(
            role="Automation Tier Recommendation Specialist",
            goal="Recommend the optimal automation tier that balances efficiency, risk, and complexity",
            backstory="""You are an expert in migration automation strategy with
            comprehensive understanding of different automation approaches. You excel at:
            - Assessing migration complexity and requirements
            - Evaluating automation feasibility and risks
            - Understanding platform-specific automation capabilities
            - Balancing speed with safety in migrations
            - Recommending appropriate human oversight levels
            - Justifying tier selections with clear rationale

            Your recommendations ensure migrations use the right level of automation
            for optimal outcomes while managing risk appropriately. You understand
            the three tiers:
            - Tier 1: Full automation with minimal oversight
            - Tier 2: Semi-automated with checkpoint validations
            - Tier 3: Guided manual with automation assistance""",
            tools=tools,
            llm=llm,
            **kwargs,
        )

    @classmethod
    def agent_metadata(cls) -> AgentMetadata:
        """Define agent metadata for registry"""
        return AgentMetadata(
            name="tier_recommendation_agent",
            description="Recommends optimal automation tier for migration execution",
            agent_class=cls,
            required_tools=[
                "ComplexityAnalyzer",
                "AutomationFeasibilityChecker",
                "RiskAssessmentTool",
                "TierMatchingEngine",
                "RecommendationJustifier",
            ],
            capabilities=[
                "complexity_assessment",
                "automation_feasibility",
                "risk_evaluation",
                "tier_recommendation",
                "justification_generation",
            ],
            max_iter=8,
            memory=False,  # Per ADR-024: Use TenantMemoryManager for enterprise memory
            verbose=True,
            allow_delegation=False,
        )

    async def recommend_tier_with_memory(
        self,
        asset_complexity: str,
        data_quality: float,
        platform: str,
        crewai_service: Any,
        client_account_id: int,
        engagement_id: int,
        db: AsyncSession,
    ) -> Dict[str, Any]:
        """
        Recommend automation tier with TenantMemoryManager integration (ADR-024).

        This method demonstrates proper memory integration:
        1. Retrieve historical tier recommendation patterns
        2. Provide patterns as context for tier selection
        3. Execute tier recommendation with historical insights
        4. Store discovered patterns for future use

        Args:
            asset_complexity: Complexity level (e.g., 'simple', 'moderate', 'complex')
            data_quality: Data quality score (0.0 to 1.0)
            platform: Platform identifier (e.g., 'vmware', 'aws', 'azure')
            crewai_service: CrewAI service instance
            client_account_id: Client account ID for multi-tenant isolation
            engagement_id: Engagement ID for pattern scoping
            db: Database session

        Returns:
            Dict containing tier recommendation with justification and confidence
        """
        try:
            logger.info(
                f"🧠 Starting tier recommendation with TenantMemoryManager "
                f"(client={client_account_id}, engagement={engagement_id}, "
                f"complexity={asset_complexity}, quality={data_quality:.2f})"
            )

            # Step 1: Initialize TenantMemoryManager
            memory_manager = TenantMemoryManager(
                crewai_service=crewai_service, database_session=db
            )

            # Step 2: Retrieve historical tier recommendation patterns
            logger.info("📚 Retrieving historical tier recommendation patterns...")
            historical_patterns = await memory_manager.retrieve_similar_patterns(
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                pattern_type="tier_recommendation",
                query_context={
                    "asset_complexity": asset_complexity,
                    "data_quality": data_quality,
                    "platform": platform,
                },
                limit=10,
            )

            logger.info(f"✅ Found {len(historical_patterns)} historical patterns")

            # Step 3: Build tier recommendation with historical context
            logger.info("🔍 Building tier recommendation with historical insights...")

            # Extract insights from historical patterns
            tier_recommendations = []
            justifications = []

            for pattern in historical_patterns[:5]:  # Top 5 patterns
                pattern_data = pattern.get("pattern_data", {})
                if "recommended_tier" in pattern_data:
                    tier_recommendations.append(pattern_data["recommended_tier"])
                if "justification" in pattern_data:
                    justifications.append(pattern_data["justification"])

            # Determine recommended tier based on complexity and data quality
            if asset_complexity == "simple" and data_quality >= 0.8:
                recommended_tier = 1  # Full automation
                confidence = 0.9
                justification = (
                    "High data quality with simple assets supports full automation"
                )
            elif asset_complexity == "complex" or data_quality < 0.5:
                recommended_tier = 3  # Guided manual
                confidence = 0.85
                justification = (
                    "Complex assets or low data quality require manual oversight"
                )
            else:
                recommended_tier = 2  # Semi-automated
                confidence = 0.8
                justification = (
                    "Moderate complexity and data quality suit semi-automated approach"
                )

            # Adjust based on historical patterns if available
            if tier_recommendations:
                most_common_tier = max(
                    set(tier_recommendations), key=tier_recommendations.count
                )
                logger.info(f"Historical patterns suggest tier {most_common_tier}")

            # Build recommendation result
            recommendation_result = {
                "recommended_tier": recommended_tier,
                "confidence": confidence,
                "justification": justification,
                "asset_complexity": asset_complexity,
                "data_quality": data_quality,
                "platform": platform,
                "historical_context": {
                    "patterns_found": len(historical_patterns),
                    "historical_tiers": (
                        tier_recommendations[:3] if tier_recommendations else []
                    ),
                },
                "tier_characteristics": {
                    1: "Full automation with minimal oversight",
                    2: "Semi-automated with checkpoint validations",
                    3: "Guided manual with automation assistance",
                }[recommended_tier],
            }

            # Step 4: Store discovered patterns
            logger.info("💾 Storing tier recommendation patterns...")

            pattern_data = {
                "name": f"tier_recommendation_{platform}_{engagement_id}",
                "recommended_tier": recommended_tier,
                "asset_complexity": asset_complexity,
                "data_quality": data_quality,
                "platform": platform,
                "confidence": confidence,
                "justification": justification,
                "historical_patterns_used": len(historical_patterns),
            }

            pattern_id = await memory_manager.store_learning(
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                scope=LearningScope.ENGAGEMENT,
                pattern_type="tier_recommendation",
                pattern_data=pattern_data,
            )

            logger.info(f"✅ Stored tier recommendation pattern with ID: {pattern_id}")

            # Enhance result with memory metadata
            recommendation_result["memory_integration"] = {
                "status": "success",
                "pattern_id": pattern_id,
                "historical_patterns_used": len(historical_patterns),
                "framework": "TenantMemoryManager (ADR-024)",
            }

            return recommendation_result

        except Exception as e:
            logger.error(
                f"❌ Tier recommendation with memory failed: {e}", exc_info=True
            )
            # Fallback to basic recommendation
            logger.warning("⚠️ Falling back to basic recommendation without memory")

            # Simple fallback logic
            if asset_complexity == "simple" and data_quality >= 0.8:
                tier = 1
            elif asset_complexity == "complex" or data_quality < 0.5:
                tier = 3
            else:
                tier = 2

            return {
                "recommended_tier": tier,
                "confidence": 0.7,
                "justification": "Fallback recommendation based on basic rules",
                "asset_complexity": asset_complexity,
                "data_quality": data_quality,
                "platform": platform,
                "status": "error",
                "error": str(e),
            }
