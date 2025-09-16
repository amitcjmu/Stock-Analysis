"""
Optimization module for Performance Analytics Engine

Generates optimization recommendations based on performance trends and bottlenecks.
"""

import uuid
from typing import List

from .base import (
    ImpactLevel,
    OptimizationRecommendation,
    PerformanceBottleneck,
    PerformanceTrend,
    TrendDirection,
)


class OptimizationService:
    """Service for generating optimization recommendations"""

    def __init__(self):
        pass

    async def generate_optimization_recommendations(
        self, trends_analyzer, bottleneck_detector
    ) -> List[OptimizationRecommendation]:
        """Generate optimization recommendations based on current performance data"""
        recommendations = []

        # Get performance trends
        trends = trends_analyzer.analyze_performance_trends(hours=24)

        # Get current bottlenecks
        bottlenecks = await bottleneck_detector.identify_bottlenecks()

        # Generate recommendations based on trends
        for metric_name, trend in trends.items():
            if (
                trend.direction == TrendDirection.DEGRADING
                and trend.confidence_score > 60
            ):
                recommendations.extend(
                    self._generate_trend_recommendations(metric_name, trend)
                )

        # Generate recommendations based on bottlenecks
        for bottleneck in bottlenecks:
            recommendations.extend(
                self._generate_bottleneck_recommendations(bottleneck)
            )

        # Generate proactive recommendations
        recommendations.extend(self._generate_proactive_recommendations())

        return recommendations

    def _generate_trend_recommendations(
        self, metric_name: str, trend: PerformanceTrend
    ) -> List[OptimizationRecommendation]:
        """Generate recommendations based on performance trends"""
        recommendations = []

        if (
            metric_name == "login_p95_ms"
            and trend.direction == TrendDirection.DEGRADING
        ):
            rec = OptimizationRecommendation(
                id=f"login_trend_opt_{uuid.uuid4()}",
                title="Optimize Login Performance",
                description=f"Login performance has degraded by {trend.change_percentage:.1f}% over the last 24 hours",
                priority="high",
                impact_level=ImpactLevel.HIGH,
                estimated_improvement_percent=30,
                implementation_effort="medium",
                cost_estimate="low",
                timeline_days=7,
                success_probability=85,
                dependencies=["database_optimization", "cache_tuning"],
                risks=["Temporary performance impact during implementation"],
            )
            recommendations.append(rec)

        elif (
            metric_name == "cache_hit_rate"
            and trend.direction == TrendDirection.DEGRADING
        ):
            rec = OptimizationRecommendation(
                id=f"cache_trend_opt_{uuid.uuid4()}",
                title="Improve Cache Efficiency",
                description=(
                    f"Cache hit rate has declined by {abs(trend.change_percentage):.1f}% "
                    f"over the last 24 hours"
                ),
                priority="medium",
                impact_level=ImpactLevel.MEDIUM,
                estimated_improvement_percent=20,
                implementation_effort="low",
                cost_estimate="low",
                timeline_days=3,
                success_probability=90,
                dependencies=["cache_configuration"],
                risks=["Minimal risk"],
            )
            recommendations.append(rec)

        return recommendations

    def _generate_bottleneck_recommendations(
        self, bottleneck: PerformanceBottleneck
    ) -> List[OptimizationRecommendation]:
        """Generate recommendations based on identified bottlenecks"""
        recommendations = []

        # Convert bottleneck recommendations to structured format
        for i, recommendation_text in enumerate(bottleneck.recommendations):
            rec = OptimizationRecommendation(
                id=f"bottleneck_rec_{bottleneck.id}_{i}",
                title=f"Address {bottleneck.component.title()} Bottleneck",
                description=recommendation_text,
                priority=(
                    "high"
                    if bottleneck.impact_level == ImpactLevel.CRITICAL
                    else "medium"
                ),
                impact_level=bottleneck.impact_level,
                estimated_improvement_percent=bottleneck.estimated_improvement.get(
                    "response_time_reduction_percent", 15
                ),
                implementation_effort="medium",
                cost_estimate="low",
                timeline_days=5,
                success_probability=bottleneck.confidence_score,
                dependencies=[],
                risks=["Performance impact during implementation"],
            )
            recommendations.append(rec)

        return recommendations

    def _generate_proactive_recommendations(self) -> List[OptimizationRecommendation]:
        """Generate proactive optimization recommendations"""
        recommendations = []

        # Recommend Redis optimization
        rec = OptimizationRecommendation(
            id=f"proactive_redis_{uuid.uuid4()}",
            title="Proactive Redis Optimization",
            description="Implement advanced Redis optimization techniques for better cache performance",
            priority="medium",
            impact_level=ImpactLevel.MEDIUM,
            estimated_improvement_percent=15,
            implementation_effort="medium",
            cost_estimate="low",
            timeline_days=10,
            success_probability=75,
            dependencies=["redis_configuration"],
            risks=["Minimal risk to existing functionality"],
        )
        recommendations.append(rec)

        # Recommend monitoring enhancement
        rec = OptimizationRecommendation(
            id=f"proactive_monitoring_{uuid.uuid4()}",
            title="Enhanced Performance Monitoring",
            description="Implement additional performance monitoring for deeper insights",
            priority="low",
            impact_level=ImpactLevel.LOW,
            estimated_improvement_percent=5,
            implementation_effort="high",
            cost_estimate="medium",
            timeline_days=14,
            success_probability=80,
            dependencies=["monitoring_infrastructure"],
            risks=["Additional system overhead"],
        )
        recommendations.append(rec)

        return recommendations
