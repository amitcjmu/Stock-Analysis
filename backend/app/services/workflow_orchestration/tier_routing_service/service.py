"""
Tier Routing Service Main Module
Team C1 - Task C1.3

Main service class that orchestrates tier routing operations.
"""

from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.exceptions import FlowError
from app.core.logging import get_logger
from app.services.ai_analysis import BusinessContextAnalyzer, ConfidenceScorer

# Import Phase 1 & 2 components
from app.services.collection_flow import TierDetectionService

# Import modular components
from .enums import AutomationTier, EnvironmentComplexity, RoutingStrategy
from .environment_analyzer import EnvironmentAnalyzer
from .models import RoutingDecision, TierAnalysis
from .quality_optimizer import QualityOptimizer
from .routing_engine import RoutingEngine
from .tier_analyzer import TierAnalyzer

logger = get_logger(__name__)


class TierRoutingService:
    """
    Tier Detection and Routing Service

    Provides intelligent tier detection and routing logic with:
    - Advanced environment analysis and complexity assessment
    - Quality-based tier recommendations
    - Adaptive routing strategies
    - Fallback and alternative path planning
    - Integration with existing TierDetectionService
    """

    def __init__(self, db: AsyncSession, context: RequestContext):
        """Initialize the Tier Routing Service"""
        self.db = db
        self.context = context

        # Initialize base tier detection service
        self.tier_detection = TierDetectionService(db, context)

        # Initialize AI analysis services
        self.business_analyzer = BusinessContextAnalyzer()
        self.confidence_scoring = ConfidenceScorer()

        # Initialize modular components
        self.tier_analyzer = TierAnalyzer()
        self.environment_analyzer = EnvironmentAnalyzer()
        self.routing_engine = RoutingEngine()
        self.quality_optimizer = QualityOptimizer()

        # Routing configuration
        self.default_strategy = RoutingStrategy.BALANCED

        logger.info("Tier Routing Service initialized")

    async def analyze_and_route(
        self,
        environment_config: Dict[str, Any],
        client_requirements: Optional[Dict[str, Any]] = None,
        routing_strategy: Optional[str] = None,
        quality_requirements: Optional[Dict[str, float]] = None,
    ) -> Tuple[TierAnalysis, RoutingDecision]:
        """
        Perform comprehensive tier analysis and routing decision

        Args:
            environment_config: Environment configuration and platform details
            client_requirements: Client-specific requirements and preferences
            routing_strategy: Strategy for tier selection (aggressive, balanced, conservative, adaptive)
            quality_requirements: Minimum quality requirements per aspect

        Returns:
            Tuple of (TierAnalysis, RoutingDecision)
        """
        try:
            logger.info("Starting tier analysis and routing")

            # Step 1: Perform base tier detection
            base_tier_result = await self.tier_detection.analyze_environment_tier(
                environment_config=environment_config,
                automation_tier="tier_2",  # Use tier_2 as baseline for analysis
            )

            # Step 2: Analyze environment complexity
            complexity_analysis = (
                await self.environment_analyzer.analyze_environment_complexity(
                    environment_config=environment_config,
                    base_analysis=base_tier_result,
                )
            )

            # Step 3: Assess platform coverage and compatibility
            platform_analysis = (
                await self.environment_analyzer.analyze_platform_coverage(
                    environment_config=environment_config,
                    complexity=complexity_analysis,
                )
            )

            # Step 4: Perform comprehensive tier analysis
            tier_analysis = (
                await self.tier_analyzer.perform_comprehensive_tier_analysis(
                    environment_config=environment_config,
                    client_requirements=client_requirements or {},
                    base_analysis=base_tier_result,
                    complexity=complexity_analysis,
                    platform_analysis=platform_analysis,
                    quality_requirements=quality_requirements or {},
                )
            )

            # Step 5: Make routing decision
            routing_decision = await self.routing_engine.make_routing_decision(
                tier_analysis=tier_analysis,
                routing_strategy=RoutingStrategy(
                    routing_strategy or self.default_strategy.value
                ),
                client_requirements=client_requirements or {},
                environment_config=environment_config,
            )

            logger.info(
                f"Tier analysis completed: {tier_analysis.recommended_tier.value} "
                f"(confidence: {tier_analysis.confidence_score:.2f})"
            )

            return tier_analysis, routing_decision

        except Exception as e:
            logger.error(f"Tier analysis and routing failed: {e}")
            raise FlowError(f"Tier analysis failed: {str(e)}")

    async def validate_tier_selection(
        self,
        selected_tier: str,
        environment_config: Dict[str, Any],
        minimum_confidence: float = 0.7,
    ) -> Dict[str, Any]:
        """
        Validate a manually selected tier against environment analysis

        Args:
            selected_tier: Manually selected automation tier
            environment_config: Environment configuration
            minimum_confidence: Minimum confidence required for validation

        Returns:
            Validation result with recommendations
        """
        try:
            # Perform analysis for the selected tier
            tier_analysis, routing_decision = await self.analyze_and_route(
                environment_config=environment_config, routing_strategy="balanced"
            )

            selected_automation_tier = AutomationTier(selected_tier)

            # Check if selected tier matches recommendation
            tier_match = selected_automation_tier == tier_analysis.recommended_tier

            # Find confidence for selected tier in alternatives
            selected_confidence = tier_analysis.confidence_score
            if not tier_match:
                for alt_tier, alt_confidence in tier_analysis.alternative_tiers:
                    if alt_tier == selected_automation_tier:
                        selected_confidence = alt_confidence
                        break
                else:
                    selected_confidence = 0.5  # Low confidence if not in alternatives

            # Validation result
            is_valid = selected_confidence >= minimum_confidence

            # Generate warnings and recommendations
            warnings = []
            recommendations = []

            if not is_valid:
                warnings.append(
                    f"Selected tier {selected_tier} has low confidence ({selected_confidence:.2f})"
                )
                recommendations.append(
                    f"Consider using recommended tier: {tier_analysis.recommended_tier.value}"
                )

            if not tier_match and tier_analysis.confidence_score > 0.8:
                warnings.append(
                    "Selected tier differs from high-confidence recommendation"
                )
                recommendations.append(
                    f"Recommended tier {tier_analysis.recommended_tier.value} has {tier_analysis.confidence_score:.2f} confidence"
                )

            # Risk assessment for selected tier
            risk_factors = await self._assess_tier_selection_risks(
                selected_tier=selected_automation_tier,
                tier_analysis=tier_analysis,
                environment_config=environment_config,
            )

            return {
                "selected_tier": selected_tier,
                "is_valid": is_valid,
                "confidence_score": selected_confidence,
                "recommended_tier": tier_analysis.recommended_tier.value,
                "recommendation_confidence": tier_analysis.confidence_score,
                "tier_match": tier_match,
                "warnings": warnings,
                "recommendations": recommendations,
                "risk_assessment": risk_factors,
                "environment_complexity": tier_analysis.environment_complexity.value,
                "platform_coverage": tier_analysis.platform_coverage,
                "quality_prediction": tier_analysis.quality_prediction,
                "execution_time_estimate": tier_analysis.execution_time_estimate,
            }

        except Exception as e:
            logger.error(f"Tier validation failed: {e}")
            raise FlowError(f"Tier validation failed: {str(e)}")

    async def optimize_routing_for_quality(
        self,
        target_quality: float,
        environment_config: Dict[str, Any],
        time_constraints: Optional[Dict[str, int]] = None,
    ) -> Dict[str, Any]:
        """
        Optimize routing to meet specific quality targets

        Args:
            target_quality: Target overall quality score (0.0 to 1.0)
            environment_config: Environment configuration
            time_constraints: Maximum execution time constraints

        Returns:
            Optimized routing configuration
        """
        return await self.quality_optimizer.optimize_routing_for_quality(
            tier_analyzer=self.tier_analyzer,
            routing_engine=self.routing_engine,
            target_quality=target_quality,
            environment_config=environment_config,
            time_constraints=time_constraints,
        )

    async def get_adaptive_routing_insights(
        self,
        historical_executions: List[Dict[str, Any]],
        environment_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate adaptive routing insights based on historical execution data

        Args:
            historical_executions: Historical workflow execution data
            environment_config: Current environment configuration

        Returns:
            Adaptive routing insights and recommendations
        """
        return await self.quality_optimizer.get_adaptive_routing_insights(
            historical_executions=historical_executions,
            environment_config=environment_config,
        )

    # Private helper method
    async def _assess_tier_selection_risks(
        self,
        selected_tier: AutomationTier,
        tier_analysis: TierAnalysis,
        environment_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Assess risks for tier selection"""
        risk_level = "low"
        risk_factors = []

        # Check for complexity mismatch
        if (
            selected_tier == AutomationTier.TIER_1
            and tier_analysis.environment_complexity
            in [EnvironmentComplexity.COMPLEX, EnvironmentComplexity.ENTERPRISE]
        ):
            risk_level = "high"
            risk_factors.append("High automation tier selected for complex environment")

        # Check for platform count
        if len(environment_config.get("platforms", [])) > 5:
            if risk_level == "low":
                risk_level = "medium"
            risk_factors.append(
                "Large number of platforms increases execution complexity"
            )

        # Check for custom configurations
        if environment_config.get("custom_configurations"):
            if risk_level == "low":
                risk_level = "medium"
            risk_factors.append("Custom configurations may require manual intervention")

        return {"risk_level": risk_level, "risk_factors": risk_factors}
