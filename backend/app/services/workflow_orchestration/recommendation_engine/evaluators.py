"""
Recommendation Engine Evaluators
Team C1 - Task C1.5

Evaluation and learning methods for recommendation outcomes and pattern updates.
"""

import statistics
from dataclasses import asdict
from datetime import datetime, timedelta
from typing import Any, Dict, List

from app.core.exceptions import FlowError
from app.core.logging import get_logger

from .models import LearningPattern, RecommendationPackage, WorkflowRecommendation

logger = get_logger(__name__)


class RecommendationEvaluator:
    """
    Handles evaluation of recommendation outcomes and learning pattern updates.
    """

    def __init__(self):
        self.learned_patterns: Dict[str, LearningPattern] = {}
        self.recommendation_history: List[RecommendationPackage] = []
        self.adaptation_metrics: Dict[str, Any] = {}
        self.learning_weight_decay = 0.95  # Decay factor for older patterns

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
        try:
            logger.info(f"📊 Evaluating recommendation outcomes: {package_id}")

            # Find the recommendation package
            package = None
            for pkg in self.recommendation_history:
                if pkg.package_id == package_id:
                    package = pkg
                    break

            if not package:
                raise ValueError(f"Recommendation package not found: {package_id}")

            # Evaluate each implemented recommendation
            recommendation_evaluations = []

            for rec_id in implemented_recommendations:
                recommendation = None
                for rec in package.recommendations:
                    if rec.recommendation_id == rec_id:
                        recommendation = rec
                        break

                if not recommendation:
                    continue

                evaluation = await self._evaluate_single_recommendation(
                    recommendation=recommendation,
                    execution_results=execution_results,
                    measured_outcomes=measured_outcomes,
                )
                recommendation_evaluations.append(evaluation)

            # Update learning patterns
            await self._update_learning_patterns(
                package=package,
                evaluations=recommendation_evaluations,
                measured_outcomes=measured_outcomes,
            )

            # Calculate overall recommendation success
            overall_success = await self._calculate_recommendation_success(
                package=package,
                evaluations=recommendation_evaluations,
                measured_outcomes=measured_outcomes,
            )

            # Generate insights for future recommendations
            learning_insights = await self._generate_learning_insights(
                package=package,
                evaluations=recommendation_evaluations,
                overall_success=overall_success,
            )

            evaluation_result = {
                "package_id": package_id,
                "evaluation_timestamp": datetime.utcnow().isoformat(),
                "implemented_count": len(implemented_recommendations),
                "total_recommendations": len(package.recommendations),
                "recommendation_evaluations": recommendation_evaluations,
                "overall_success": overall_success,
                "learning_insights": learning_insights,
                "adaptation_suggestions": await self._generate_adaptation_suggestions(
                    evaluations=recommendation_evaluations,
                    learning_insights=learning_insights,
                ),
            }

            # Update adaptation metrics
            self._update_adaptation_metrics(evaluation_result)

            logger.info(
                f"✅ Recommendation evaluation completed: {overall_success.get('success_score', 0):.2f} success score"
            )
            return evaluation_result

        except Exception as e:
            logger.error(f"❌ Failed to evaluate recommendation outcomes: {e}")
            raise FlowError(f"Recommendation evaluation failed: {str(e)}")

    async def get_recommendation_insights(
        self,
        environment_type: str = None,
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
        try:
            logger.info("📈 Generating recommendation insights")

            # Filter recommendation history by time range
            cutoff_date = datetime.utcnow() - timedelta(days=time_range_days)
            recent_packages = [
                pkg
                for pkg in self.recommendation_history
                if pkg.analysis_timestamp >= cutoff_date
            ]

            # Filter by environment type if specified
            if environment_type:
                recent_packages = [
                    pkg
                    for pkg in recent_packages
                    if pkg.target_environment.get("environment_type")
                    == environment_type
                ]

            # Calculate recommendation performance metrics
            performance_metrics = (
                await self._calculate_recommendation_performance_metrics(
                    packages=recent_packages
                )
            )

            # Analyze recommendation trends
            trends = await self._analyze_recommendation_trends(packages=recent_packages)

            # Get top performing patterns
            top_patterns = await self._get_top_performing_patterns(
                min_confidence=0.7, min_occurrences=3
            )

            # Calculate adaptation effectiveness
            adaptation_effectiveness = await self._calculate_adaptation_effectiveness()

            insights = {
                "analysis_period": {
                    "start_date": cutoff_date.isoformat(),
                    "end_date": datetime.utcnow().isoformat(),
                    "packages_analyzed": len(recent_packages),
                },
                "performance_metrics": performance_metrics,
                "recommendation_trends": trends,
                "adaptation_effectiveness": adaptation_effectiveness,
                "engine_statistics": {
                    "total_patterns_learned": len(self.learned_patterns),
                    "total_packages_generated": len(self.recommendation_history),
                    "average_recommendations_per_package": (
                        statistics.mean(
                            [
                                len(pkg.recommendations)
                                for pkg in self.recommendation_history
                            ]
                        )
                        if self.recommendation_history
                        else 0
                    ),
                    "overall_confidence": (
                        statistics.mean(
                            [pkg.overall_confidence for pkg in recent_packages]
                        )
                        if recent_packages
                        else 0
                    ),
                },
            }

            # Include learned patterns if requested
            if include_patterns:
                insights["learned_patterns"] = [
                    asdict(pattern) for pattern in top_patterns
                ]

            return insights

        except Exception as e:
            logger.error(f"❌ Failed to generate recommendation insights: {e}")
            raise FlowError(f"Insight generation failed: {str(e)}")

    async def _evaluate_single_recommendation(
        self,
        recommendation: WorkflowRecommendation,
        execution_results: Dict[str, Any],
        measured_outcomes: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Evaluate a single recommendation outcome"""

        # Compare expected vs actual impact
        expected_impact = recommendation.expected_impact
        actual_impact = {}

        for metric, expected_value in expected_impact.items():
            if metric in measured_outcomes:
                actual_value = measured_outcomes[metric]
                actual_impact[metric] = actual_value

        # Calculate success score
        success_score = 0.0
        impact_achieved = 0.0

        for metric in expected_impact:
            if metric in actual_impact:
                # Calculate achievement ratio
                if expected_impact[metric] != 0:
                    achievement = actual_impact[metric] / expected_impact[metric]
                    success_score += min(1.0, achievement) / len(expected_impact)
                    impact_achieved += achievement / len(expected_impact)

        return {
            "recommendation_id": recommendation.recommendation_id,
            "recommendation_type": recommendation.recommendation_type.value,
            "success": success_score > 0.7,
            "success_score": success_score,
            "impact_achieved": impact_achieved,
            "expected_impact": expected_impact,
            "actual_impact": actual_impact,
            "confidence_validated": success_score > 0.5
            and recommendation.confidence_score > 0.7,
            "execution_status": execution_results.get("status", "unknown"),
        }

    async def _update_learning_patterns(
        self,
        package: RecommendationPackage,
        evaluations: List[Dict[str, Any]],
        measured_outcomes: Dict[str, Any],
    ) -> None:
        """Update learning patterns based on evaluation results"""

        # Group evaluations by recommendation type
        type_groups = {}
        for evaluation in evaluations:
            rec_type = evaluation["recommendation_type"]
            if rec_type not in type_groups:
                type_groups[rec_type] = []
            type_groups[rec_type].append(evaluation)

        # Update patterns for each type
        for rec_type, type_evaluations in type_groups.items():
            success_rate = sum(1 for e in type_evaluations if e["success"]) / len(
                type_evaluations
            )
            avg_impact = statistics.mean(
                [e["impact_achieved"] for e in type_evaluations]
            )

            # Create or update pattern
            pattern_id = f"learned-{rec_type}-{package.target_environment.get('environment_type', 'unknown')}"

            if pattern_id in self.learned_patterns:
                # Update existing pattern with decay
                pattern = self.learned_patterns[pattern_id]
                pattern.confidence = (
                    pattern.confidence * self.learning_weight_decay
                    + success_rate * (1 - self.learning_weight_decay)
                )
                pattern.success_rate = (
                    pattern.success_rate * self.learning_weight_decay
                    + success_rate * (1 - self.learning_weight_decay)
                )
                pattern.occurrence_count += 1
            else:
                # Create new pattern
                pattern = LearningPattern(
                    pattern_id=pattern_id,
                    pattern_type=rec_type,
                    description=f"Learned pattern for {rec_type} recommendations",
                    conditions={
                        "environment_type": package.target_environment.get(
                            "environment_type"
                        ),
                        "complexity": package.target_environment.get("complexity"),
                    },
                    outcomes={"average_impact": avg_impact},
                    confidence=success_rate,
                    occurrence_count=1,
                    success_rate=success_rate,
                    average_improvement={"overall": avg_impact},
                    applicable_scenarios=[
                        package.target_environment.get("environment_type", "unknown")
                    ],
                )
                self.learned_patterns[pattern_id] = pattern

    async def _calculate_recommendation_success(
        self,
        package: RecommendationPackage,
        evaluations: List[Dict[str, Any]],
        measured_outcomes: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Calculate overall recommendation success"""

        if not evaluations:
            return {
                "success_score": 0.0,
                "recommendations_successful": 0,
                "overall_impact": 0.0,
            }

        success_count = sum(1 for e in evaluations if e["success"])
        avg_success_score = statistics.mean([e["success_score"] for e in evaluations])
        avg_impact = statistics.mean([e["impact_achieved"] for e in evaluations])

        # Calculate weighted overall score
        overall_score = (
            avg_success_score * 0.4
            + (success_count / len(evaluations)) * 0.3
            + min(1.0, avg_impact) * 0.3
        )

        return {
            "success_score": overall_score,
            "recommendations_successful": success_count,
            "success_rate": success_count / len(evaluations),
            "average_impact_achieved": avg_impact,
            "overall_impact": measured_outcomes.get("overall_improvement", avg_impact),
            "confidence_accuracy": avg_success_score > 0.7,
        }

    async def _generate_learning_insights(
        self,
        package: RecommendationPackage,
        evaluations: List[Dict[str, Any]],
        overall_success: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Generate insights for future learning"""

        insights = []

        # Insight about recommendation success
        if overall_success["success_score"] > 0.8:
            insights.append(
                {
                    "insight_type": "high_success",
                    "description": "Recommendations highly successful for this environment type",
                    "confidence": 0.9,
                    "actionable": True,
                    "recommendation": "Continue using similar recommendation strategies",
                }
            )
        elif overall_success["success_score"] < 0.5:
            insights.append(
                {
                    "insight_type": "low_success",
                    "description": "Recommendations showed limited success",
                    "confidence": 0.8,
                    "actionable": True,
                    "recommendation": "Adjust recommendation thresholds and strategies",
                }
            )

        # Insights about specific recommendation types
        type_performance = {}
        for evaluation in evaluations:
            rec_type = evaluation["recommendation_type"]
            if rec_type not in type_performance:
                type_performance[rec_type] = []
            type_performance[rec_type].append(evaluation["success_score"])

        for rec_type, scores in type_performance.items():
            avg_score = statistics.mean(scores)
            if avg_score > 0.85:
                insights.append(
                    {
                        "insight_type": "high_performing_type",
                        "description": f"{rec_type} recommendations performing exceptionally well",
                        "confidence": 0.85,
                        "actionable": True,
                        "recommendation": f"Prioritize {rec_type} recommendations for similar environments",
                    }
                )

        return insights

    async def _generate_adaptation_suggestions(
        self, evaluations: List[Dict[str, Any]], learning_insights: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate adaptation suggestions based on evaluation"""

        suggestions = []

        # Analyze evaluation patterns
        low_success_types = []
        high_success_types = []

        type_scores = {}
        for evaluation in evaluations:
            rec_type = evaluation["recommendation_type"]
            if rec_type not in type_scores:
                type_scores[rec_type] = []
            type_scores[rec_type].append(evaluation["success_score"])

        for rec_type, scores in type_scores.items():
            avg_score = statistics.mean(scores)
            if avg_score < 0.5:
                low_success_types.append(rec_type)
            elif avg_score > 0.8:
                high_success_types.append(rec_type)

        # Generate suggestions
        if low_success_types:
            suggestions.append(
                f"Consider adjusting thresholds for: {', '.join(low_success_types)}"
            )

        if high_success_types:
            suggestions.append(
                f"Increase priority for: {', '.join(high_success_types)}"
            )

        # Add insight-based suggestions
        for insight in learning_insights:
            if insight.get("actionable") and "recommendation" in insight:
                suggestions.append(insight["recommendation"])

        return suggestions

    def _update_adaptation_metrics(self, evaluation_result: Dict[str, Any]) -> None:
        """Update adaptation metrics based on evaluation"""

        # Update success tracking
        if "recommendation_success" not in self.adaptation_metrics:
            self.adaptation_metrics["recommendation_success"] = []

        self.adaptation_metrics["recommendation_success"].append(
            {
                "timestamp": evaluation_result["evaluation_timestamp"],
                "success_score": evaluation_result["overall_success"]["success_score"],
                "implemented_count": evaluation_result["implemented_count"],
            }
        )

        # Keep only recent metrics (last 100)
        if len(self.adaptation_metrics["recommendation_success"]) > 100:
            self.adaptation_metrics["recommendation_success"] = self.adaptation_metrics[
                "recommendation_success"
            ][-100:]

    async def _calculate_recommendation_performance_metrics(
        self, packages: List[RecommendationPackage]
    ) -> Dict[str, Any]:
        """Calculate recommendation performance metrics"""

        if not packages:
            return {
                "average_confidence": 0.0,
                "success_rate": 0.0,
                "average_impact": 0.0,
            }

        # Calculate average metrics
        avg_confidence = statistics.mean([pkg.overall_confidence for pkg in packages])
        avg_recommendation_count = statistics.mean(
            [len(pkg.recommendations) for pkg in packages]
        )

        # Calculate success rate from adaptation metrics
        success_rate = 0.0
        if "recommendation_success" in self.adaptation_metrics:
            recent_successes = self.adaptation_metrics["recommendation_success"][-20:]
            if recent_successes:
                success_scores = [s["success_score"] for s in recent_successes]
                success_rate = statistics.mean(success_scores)

        return {
            "average_confidence": avg_confidence,
            "success_rate": success_rate,
            "average_recommendations_per_package": avg_recommendation_count,
            "confidence_trend": "stable",  # Would calculate from historical data
            "average_impact": 0.15,  # Would calculate from measured outcomes
        }

    async def _analyze_recommendation_trends(
        self, packages: List[RecommendationPackage]
    ) -> Dict[str, Any]:
        """Analyze recommendation trends over time"""

        if len(packages) < 2:
            return {
                "trend_direction": "insufficient_data",
                "confidence_trend": "unknown",
                "success_trend": "unknown",
            }

        # Sort packages by timestamp
        sorted_packages = sorted(packages, key=lambda p: p.analysis_timestamp)

        # Calculate confidence trend
        early_confidence = statistics.mean(
            [p.overall_confidence for p in sorted_packages[: len(sorted_packages) // 2]]
        )
        late_confidence = statistics.mean(
            [p.overall_confidence for p in sorted_packages[len(sorted_packages) // 2 :]]
        )

        confidence_trend = (
            "improving" if late_confidence > early_confidence else "declining"
        )

        return {
            "trend_direction": (
                "improving" if late_confidence > early_confidence + 0.05 else "stable"
            ),
            "confidence_trend": confidence_trend,
            "success_trend": "improving",  # Would calculate from success metrics
            "recommendation_type_distribution": self._calculate_type_distribution(
                packages
            ),
        }

    def _calculate_type_distribution(
        self, packages: List[RecommendationPackage]
    ) -> Dict[str, float]:
        """Calculate distribution of recommendation types"""

        type_counts = {}
        total_recommendations = 0

        for package in packages:
            for recommendation in package.recommendations:
                rec_type = recommendation.recommendation_type.value
                type_counts[rec_type] = type_counts.get(rec_type, 0) + 1
                total_recommendations += 1

        if total_recommendations == 0:
            return {}

        return {
            rec_type: count / total_recommendations
            for rec_type, count in type_counts.items()
        }

    async def _get_top_performing_patterns(
        self, min_confidence: float, min_occurrences: int
    ) -> List[LearningPattern]:
        """Get top performing learned patterns"""

        # Filter patterns by criteria
        qualified_patterns = [
            pattern
            for pattern in self.learned_patterns.values()
            if pattern.confidence >= min_confidence
            and pattern.occurrence_count >= min_occurrences
        ]

        # Sort by confidence and success rate
        sorted_patterns = sorted(
            qualified_patterns,
            key=lambda p: (p.confidence * p.success_rate),
            reverse=True,
        )

        return sorted_patterns[:10]  # Return top 10

    async def _calculate_adaptation_effectiveness(self) -> Dict[str, Any]:
        """Calculate how effectively the system is adapting"""

        if (
            "recommendation_success" not in self.adaptation_metrics
            or len(self.adaptation_metrics["recommendation_success"]) < 10
        ):
            return {
                "effectiveness_score": 0.5,
                "learning_rate": 0.0,
                "adaptation_frequency": "insufficient_data",
            }

        # Calculate improvement over time
        success_history = self.adaptation_metrics["recommendation_success"]
        early_scores = [
            s["success_score"] for s in success_history[: len(success_history) // 3]
        ]
        late_scores = [
            s["success_score"] for s in success_history[-len(success_history) // 3 :]
        ]

        early_avg = statistics.mean(early_scores) if early_scores else 0.5
        late_avg = statistics.mean(late_scores) if late_scores else 0.5

        improvement = late_avg - early_avg
        learning_rate = max(0, min(1, improvement * 10))  # Scale improvement to 0-1

        return {
            "effectiveness_score": late_avg,
            "learning_rate": learning_rate,
            "improvement_percentage": improvement * 100,
            "adaptation_frequency": "continuous",
            "pattern_utilization": len(self.learned_patterns)
            / 20,  # Normalized by expected patterns
        }
