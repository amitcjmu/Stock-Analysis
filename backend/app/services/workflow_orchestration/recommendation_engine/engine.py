"""
Smart Workflow Recommendation Engine
Team C1 - Task C1.5

Main orchestration engine that coordinates all recommendation components.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.exceptions import FlowError
from app.core.logging import get_logger
from app.services.ai_analysis import ConfidenceScorer, LearningOptimizer

from .analyzers import RecommendationAnalyzers
from .evaluators import RecommendationEvaluator
from .generators.config_recommendations import ConfigRecommendationGenerator
from .generators.performance_recommendations import \
    PerformanceRecommendationGenerator
from .generators.phase_recommendations import PhaseRecommendationGenerator
from .generators.quality_recommendations import QualityRecommendationGenerator
from .generators.tier_recommendations import TierRecommendationGenerator
from .models import LearningPattern, RecommendationPackage
from .optimizers import RecommendationOptimizer

logger = get_logger(__name__)


class SmartWorkflowRecommendationEngine:
    """
    Smart Workflow Recommendation System

    Provides intelligent workflow recommendations with:
    - Historical execution pattern analysis
    - Machine learning-based insights
    - Business context-aware recommendations
    - Adaptive learning from outcomes
    - Multi-dimensional optimization (quality, speed, cost, risk)
    - Environment-specific recommendations
    - Progressive recommendation refinement
    """

    def __init__(self, db: AsyncSession, context: RequestContext):
        """Initialize the Smart Workflow Recommendation Engine"""
        self.db = db
        self.context = context

        # Initialize components
        self.analyzers = RecommendationAnalyzers(db, context)
        self.evaluator = RecommendationEvaluator()
        self.optimizer = RecommendationOptimizer()

        # Initialize generators
        self.tier_generator = TierRecommendationGenerator()
        self.config_generator = ConfigRecommendationGenerator()
        self.phase_generator = PhaseRecommendationGenerator()
        self.quality_generator = QualityRecommendationGenerator()
        self.performance_generator = PerformanceRecommendationGenerator()

        # Initialize AI components
        self.confidence_scoring = ConfidenceScorer()
        self.learning_optimizer = LearningOptimizer()

        # Configuration
        self.min_historical_samples = 5
        self.max_recommendations_per_type = 3
        self.confidence_threshold = 0.6

        logger.info("✅ Smart Workflow Recommendation Engine initialized")

    async def generate_workflow_recommendations(
        self,
        environment_config: Dict[str, Any],
        business_requirements: Optional[Dict[str, Any]] = None,
        historical_context: Optional[List[Dict[str, Any]]] = None,
        optimization_goals: Optional[List[str]] = None,
        constraints: Optional[Dict[str, Any]] = None,
    ) -> RecommendationPackage:
        """
        Generate comprehensive workflow recommendations

        Args:
            environment_config: Target environment configuration
            business_requirements: Business requirements and preferences
            historical_context: Historical execution data for analysis
            optimization_goals: Primary optimization goals (quality, speed, cost, etc.)
            constraints: Implementation constraints (time, budget, resources)

        Returns:
            Complete recommendation package
        """
        try:
            logger.info("🎯 Generating smart workflow recommendations")

            # Step 1: Analyze environment and context
            environment_analysis = await self.analyzers.analyze_environment_context(
                environment_config=environment_config,
                business_requirements=business_requirements or {},
            )

            # Step 2: Process historical data and identify patterns
            historical_patterns = await self.analyzers.analyze_historical_patterns(
                historical_context=historical_context or [],
                environment_analysis=environment_analysis,
            )

            # Store patterns in evaluator for learning
            for pattern in historical_patterns:
                self.evaluator.learned_patterns[pattern.pattern_id] = pattern

            # Step 3: Generate recommendations by type
            recommendations = []

            # Automation tier recommendations
            tier_recommendations = (
                await self.tier_generator.generate_automation_tier_recommendations(
                    environment_analysis=environment_analysis,
                    historical_patterns=historical_patterns,
                    optimization_goals=optimization_goals or ["quality", "performance"],
                )
            )
            recommendations.extend(tier_recommendations)

            # Workflow configuration recommendations
            config_recommendations = (
                await self.config_generator.generate_workflow_config_recommendations(
                    environment_analysis=environment_analysis,
                    historical_patterns=historical_patterns,
                    business_requirements=business_requirements or {},
                )
            )
            recommendations.extend(config_recommendations)

            # Phase optimization recommendations
            phase_recommendations = (
                await self.phase_generator.generate_phase_optimization_recommendations(
                    environment_analysis=environment_analysis,
                    historical_patterns=historical_patterns,
                    constraints=constraints or {},
                )
            )
            recommendations.extend(phase_recommendations)

            # Quality improvement recommendations
            quality_recommendations = await self.quality_generator.generate_quality_improvement_recommendations(
                environment_analysis=environment_analysis,
                historical_patterns=historical_patterns,
            )
            recommendations.extend(quality_recommendations)

            # Performance optimization recommendations
            performance_recommendations = await self.performance_generator.generate_performance_optimization_recommendations(
                environment_analysis=environment_analysis,
                historical_patterns=historical_patterns,
            )
            recommendations.extend(performance_recommendations)

            # Step 4: Rank and prioritize recommendations
            prioritized_recommendations = (
                await self.optimizer.prioritize_recommendations(
                    recommendations=recommendations,
                    optimization_goals=optimization_goals or [],
                    constraints=constraints or {},
                )
            )

            # Step 5: Generate execution order
            execution_order = await self.optimizer.calculate_optimal_execution_order(
                recommendations=prioritized_recommendations
            )

            # Step 6: Calculate overall impact estimates
            estimated_improvement = await self.optimizer.estimate_overall_improvement(
                recommendations=prioritized_recommendations,
                environment_analysis=environment_analysis,
            )

            # Step 7: Generate adaptation notes
            adaptation_notes = await self._generate_adaptation_notes(
                recommendations=prioritized_recommendations,
                environment_analysis=environment_analysis,
                historical_patterns=historical_patterns,
            )

            # Create recommendation package
            package = RecommendationPackage(
                package_id=f"rec-pkg-{uuid.uuid4()}",
                target_environment=environment_config,
                target_requirements=business_requirements or {},
                analysis_timestamp=datetime.utcnow(),
                recommendations=prioritized_recommendations,
                overall_confidence=self._calculate_overall_confidence(
                    prioritized_recommendations
                ),
                recommended_execution_order=execution_order,
                estimated_improvement=estimated_improvement,
                adaptation_notes=adaptation_notes,
                metadata={
                    "optimization_goals": optimization_goals,
                    "constraints": constraints,
                    "patterns_analyzed": len(historical_patterns),
                    "recommendations_generated": len(prioritized_recommendations),
                    "environment_complexity": environment_analysis.get(
                        "complexity", "unknown"
                    ),
                },
            )

            # Store for learning
            self.evaluator.recommendation_history.append(package)

            logger.info(
                f"✅ Generated {len(prioritized_recommendations)} workflow recommendations"
            )
            return package

        except Exception as e:
            logger.error(f"❌ Failed to generate workflow recommendations: {e}")
            raise FlowError(f"Recommendation generation failed: {str(e)}")

    async def evaluate_recommendation_outcome(
        self,
        package_id: str,
        implemented_recommendations: List[str],
        execution_results: Dict[str, Any],
        measured_outcomes: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Evaluate outcomes of implemented recommendations for learning

        Args:
            package_id: ID of the recommendation package
            implemented_recommendations: List of implemented recommendation IDs
            execution_results: Results from workflow execution
            measured_outcomes: Measured performance, quality, and other metrics

        Returns:
            Evaluation results and learning insights
        """
        return await self.evaluator.evaluate_recommendation_outcome(
            package_id=package_id,
            implemented_recommendations=implemented_recommendations,
            execution_results=execution_results,
            measured_outcomes=measured_outcomes,
        )

    async def get_recommendation_insights(
        self,
        environment_type: Optional[str] = None,
        time_range_days: int = 30,
        include_patterns: bool = True,
    ) -> Dict[str, Any]:
        """
        Get insights about recommendation performance and learned patterns

        Args:
            environment_type: Filter by environment type
            time_range_days: Time range for analysis
            include_patterns: Whether to include learned patterns

        Returns:
            Comprehensive recommendation insights
        """
        return await self.evaluator.get_recommendation_insights(
            environment_type=environment_type,
            time_range_days=time_range_days,
            include_patterns=include_patterns,
        )

    async def optimize_recommendation_for_goals(
        self,
        base_environment: Dict[str, Any],
        optimization_targets: Dict[str, float],
        acceptable_tradeoffs: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        Optimize recommendations to meet specific goals

        Args:
            base_environment: Base environment configuration
            optimization_targets: Target metrics (quality, performance, cost)
            acceptable_tradeoffs: Acceptable degradation in other metrics

        Returns:
            Optimized recommendation configuration
        """
        try:
            logger.info("🎯 Optimizing recommendations for specific goals")

            # Generate baseline recommendations
            baseline_package = await self.generate_workflow_recommendations(
                environment_config=base_environment,
                optimization_goals=list(optimization_targets.keys()),
            )

            # Use optimizer to find best combination
            optimization_result = (
                await self.optimizer.optimize_recommendation_for_goals(
                    base_environment=base_environment,
                    optimization_targets=optimization_targets,
                    acceptable_tradeoffs=acceptable_tradeoffs,
                    candidate_recommendations=baseline_package.recommendations,
                )
            )

            return optimization_result

        except Exception as e:
            logger.error(f"❌ Failed to optimize recommendations: {e}")
            raise FlowError(f"Recommendation optimization failed: {str(e)}")

    def _calculate_overall_confidence(self, recommendations: List[Any]) -> float:
        """Calculate overall confidence across all recommendations"""
        if not recommendations:
            return 0.0

        weighted_confidence = sum(
            rec.confidence_score * rec.priority for rec in recommendations
        )
        total_weight = sum(rec.priority for rec in recommendations)

        return weighted_confidence / total_weight if total_weight > 0 else 0.0

    async def _generate_adaptation_notes(
        self,
        recommendations: List[Any],
        environment_analysis: Dict[str, Any],
        historical_patterns: List[LearningPattern],
    ) -> List[str]:
        """Generate adaptation notes for the recommendation package"""

        notes = []

        # Environment-specific notes
        complexity = environment_analysis.get("complexity", {})
        if complexity.get("level") == "enterprise":
            notes.append("Consider phased implementation due to enterprise complexity")

        # Pattern-based notes
        if len(historical_patterns) > 5:
            notes.append(
                "Strong historical patterns available - high confidence in recommendations"
            )
        elif len(historical_patterns) < 3:
            notes.append(
                "Limited historical data - monitor outcomes closely for learning"
            )

        # Recommendation-specific notes
        high_priority_count = len([r for r in recommendations if r.priority >= 8])
        if high_priority_count > 3:
            notes.append(
                "Multiple high-priority recommendations - consider resource allocation"
            )

        # Implementation complexity notes
        high_effort_count = len(
            [r for r in recommendations if r.implementation_effort == "high"]
        )
        if high_effort_count > 2:
            notes.append(
                "Several high-effort recommendations - plan implementation timeline accordingly"
            )

        # Risk notes
        high_risk_recommendations = [
            r for r in recommendations if r.risk_assessment.get("overall_risk", 0) > 0.3
        ]
        if high_risk_recommendations:
            notes.append(
                "Some recommendations carry higher risk - ensure proper testing and rollback plans"
            )

        return notes
