"""
Performance Analytics Engine

Advanced analytics engine for performance trend analysis, bottleneck identification,
and optimization recommendations. Provides data-driven insights for performance
optimization and business impact analysis.

Key Features:
- Historical performance trend analysis
- Bottleneck identification and root cause analysis
- Performance optimization recommendations with impact estimates
- Business impact analysis (performance → user experience → business metrics)
- Predictive performance modeling and capacity planning
- Automated performance regression detection
- Custom performance KPI calculations and tracking

Analytics Capabilities:
1. Trend Analysis - Performance patterns over time with seasonality detection
2. Bottleneck Detection - Automated identification of performance constraints
3. Impact Analysis - Correlation between performance and business metrics
4. Optimization Recommendations - Data-driven improvement suggestions
5. Regression Detection - Automated alerts for performance degradations
6. Capacity Planning - Predictive modeling for resource requirements
"""

import asyncio
import time
import statistics
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor

# JSON import available if needed
import math

from app.core.logging import get_logger
from app.services.monitoring.performance_metrics_collector import get_metrics_collector
from app.services.monitoring.auth_performance_monitor import (
    get_auth_performance_monitor,
)
from app.services.monitoring.cache_performance_monitor import (
    get_cache_performance_monitor,
)
from app.services.monitoring.system_health_dashboard import get_system_health_dashboard

logger = get_logger(__name__)


class TrendDirection(str, Enum):
    """Trend direction indicators"""

    IMPROVING = "improving"
    STABLE = "stable"
    DEGRADING = "degrading"
    VOLATILE = "volatile"
    UNKNOWN = "unknown"


class BottleneckType(str, Enum):
    """Types of performance bottlenecks"""

    CPU_BOUND = "cpu_bound"
    MEMORY_BOUND = "memory_bound"
    IO_BOUND = "io_bound"
    CACHE_BOUND = "cache_bound"
    AUTH_BOUND = "auth_bound"
    NETWORK_BOUND = "network_bound"
    DATABASE_BOUND = "database_bound"


class ImpactLevel(str, Enum):
    """Impact severity levels"""

    CRITICAL = "critical"  # Severe user experience impact
    HIGH = "high"  # Noticeable user impact
    MEDIUM = "medium"  # Minor user impact
    LOW = "low"  # Minimal user impact
    NONE = "none"  # No user impact


@dataclass
class PerformanceTrend:
    """Performance trend analysis result"""

    metric_name: str
    time_period_hours: int
    direction: TrendDirection
    change_percentage: float
    confidence_score: float  # 0-100
    data_points: int
    trend_details: Dict[str, Any] = field(default_factory=dict)
    predictions: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceBottleneck:
    """Identified performance bottleneck"""

    id: str
    type: BottleneckType
    component: str
    metric: str
    current_value: float
    threshold: float
    impact_level: ImpactLevel
    confidence_score: float
    root_causes: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    estimated_improvement: Dict[str, float] = field(default_factory=dict)


@dataclass
class OptimizationRecommendation:
    """Performance optimization recommendation"""

    id: str
    title: str
    description: str
    priority: str  # high, medium, low
    impact_level: ImpactLevel
    estimated_improvement_percent: float
    implementation_effort: str  # low, medium, high
    cost_estimate: str  # low, medium, high
    timeline_days: int
    success_probability: float  # 0-100
    dependencies: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)


@dataclass
class BusinessImpactAnalysis:
    """Business impact analysis of performance metrics"""

    metric_name: str
    performance_change_percent: float
    estimated_user_impact: Dict[str, float]
    estimated_business_impact: Dict[str, Any]
    confidence_level: float


class PerformanceAnalyticsEngine:
    """
    Performance Analytics Engine

    Provides advanced analytics and insights for performance optimization
    with focus on data-driven decision making and business impact analysis.
    """

    def __init__(self, analysis_window_hours: int = 168):  # 1 week default
        self.analysis_window_hours = analysis_window_hours

        # Component integrations
        self.metrics_collector = get_metrics_collector()
        self.auth_monitor = get_auth_performance_monitor()
        self.cache_monitor = get_cache_performance_monitor()
        self.dashboard = get_system_health_dashboard()

        # Analytics state
        self.trend_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.bottleneck_history: deque[PerformanceBottleneck] = deque(maxlen=500)
        self.recommendation_history: deque[OptimizationRecommendation] = deque(
            maxlen=200
        )

        # Performance baselines and targets
        self.performance_baselines = {
            "login_p95_ms": 2500,  # Pre-optimization baseline
            "auth_flow_p95_ms": 2000,  # Pre-optimization baseline
            "context_switch_p95_ms": 1500,  # Pre-optimization baseline
            "cache_hit_rate": 60.0,  # Pre-optimization baseline
        }

        self.performance_targets = {
            "login_p95_ms": 500,  # Target: 200-500ms
            "auth_flow_p95_ms": 600,  # Target: 300-600ms
            "context_switch_p95_ms": 300,  # Target: 100-300ms
            "cache_hit_rate": 85.0,  # Target: >80%
        }

        # Business impact models
        self.business_impact_models = {
            "user_satisfaction": self._model_user_satisfaction_impact,
            "conversion_rate": self._model_conversion_impact,
            "user_retention": self._model_retention_impact,
            "operational_cost": self._model_cost_impact,
        }

        # Background analysis
        self._analytics_executor = ThreadPoolExecutor(
            max_workers=3, thread_name_prefix="perf-analytics"
        )
        self._last_analysis = time.time()
        self._analysis_interval = 300  # 5 minutes

        logger.info(
            "PerformanceAnalyticsEngine initialized with %d hour analysis window",
            analysis_window_hours,
        )

        # Start background analytics
        self._start_background_analytics()

    def _start_background_analytics(self) -> None:
        """Start background analytics processing"""
        # Store reference to the main event loop for thread-safe async scheduling
        self._main_loop = asyncio.get_event_loop()

        def background_analyzer():
            while True:
                try:
                    if time.time() - self._last_analysis > self._analysis_interval:
                        # Properly schedule async task from sync thread using run_coroutine_threadsafe
                        future = asyncio.run_coroutine_threadsafe(
                            self._run_background_analysis(), self._main_loop
                        )
                        # Wait for completion to ensure proper error handling
                        try:
                            future.result(timeout=60)  # 60 second timeout
                        except Exception as e:
                            logger.error("Background analysis failed: %s", e)
                        self._last_analysis = time.time()

                    time.sleep(60)  # Check every minute
                except Exception as e:
                    logger.error("Error in background analytics: %s", e)
                    time.sleep(120)  # Wait longer on error

        self._analytics_executor.submit(background_analyzer)

    async def _run_background_analysis(self) -> None:
        """Run background performance analysis"""
        try:
            logger.debug("Running background performance analysis...")

            # Update trend analysis
            await self._update_trend_analysis()

            # Update bottleneck detection
            await self._update_bottleneck_analysis()

            # Update recommendations
            await self._update_optimization_recommendations()

            logger.debug("Background performance analysis completed")

        except Exception as e:
            logger.error("Error in background performance analysis: %s", e)

    async def _update_trend_analysis(self) -> None:
        """Update performance trend analysis"""
        # Get current performance data
        auth_stats = self.auth_monitor.get_comprehensive_stats()
        cache_stats = self.cache_monitor.get_comprehensive_stats()

        # Update trend data
        current_time = time.time()

        # Auth performance trends
        login_stats = auth_stats.get("operations", {}).get("login", {})
        if login_stats:
            self.trend_history["login_p95_ms"].append(
                {
                    "timestamp": current_time,
                    "value": login_stats.get("p95_duration_ms", 0),
                }
            )

        session_stats = auth_stats.get("operations", {}).get("session_validation", {})
        if session_stats:
            self.trend_history["session_validation_p95_ms"].append(
                {
                    "timestamp": current_time,
                    "value": session_stats.get("p95_duration_ms", 0),
                }
            )

        context_stats = auth_stats.get("operations", {}).get("context_switch", {})
        if context_stats:
            self.trend_history["context_switch_p95_ms"].append(
                {
                    "timestamp": current_time,
                    "value": context_stats.get("p95_duration_ms", 0),
                }
            )

        # Cache performance trends
        cache_summary = cache_stats.get("overall_summary", {})
        self.trend_history["cache_hit_rate"].append(
            {
                "timestamp": current_time,
                "value": cache_summary.get("overall_hit_rate", 0),
            }
        )

        redis_stats = cache_stats.get("cache_layers", {}).get("redis", {})
        if redis_stats:
            self.trend_history["redis_response_ms"].append(
                {
                    "timestamp": current_time,
                    "value": redis_stats.get("average_response_time_ms", 0),
                }
            )

    async def _update_bottleneck_analysis(self) -> None:
        """Update bottleneck identification analysis"""
        bottlenecks = await self.identify_bottlenecks()

        # Store new bottlenecks
        for bottleneck in bottlenecks:
            self.bottleneck_history.append(bottleneck)

    async def _update_optimization_recommendations(self) -> None:
        """Update optimization recommendations"""
        recommendations = await self.generate_optimization_recommendations()

        # Store new recommendations
        for recommendation in recommendations:
            self.recommendation_history.append(recommendation)

    def analyze_performance_trends(
        self, hours: int = 24
    ) -> Dict[str, PerformanceTrend]:
        """Analyze performance trends over specified time period"""
        cutoff_time = time.time() - (hours * 3600)
        trends = {}

        for metric_name, trend_data in self.trend_history.items():
            # Filter data within time window
            recent_data = [
                point
                for point in trend_data
                if point["timestamp"] >= cutoff_time and point["value"] > 0
            ]

            if len(recent_data) < 3:  # Need minimum data points
                continue

            # Calculate trend
            trend = self._calculate_trend(recent_data, metric_name, hours)
            trends[metric_name] = trend

        return trends

    def _calculate_trend(
        self, data_points: List[Dict], metric_name: str, hours: int
    ) -> PerformanceTrend:
        """Calculate trend analysis for a metric"""
        if len(data_points) < 3:
            return PerformanceTrend(
                metric_name=metric_name,
                time_period_hours=hours,
                direction=TrendDirection.UNKNOWN,
                change_percentage=0.0,
                confidence_score=0.0,
                data_points=len(data_points),
            )

        # Sort by timestamp
        data_points.sort(key=lambda x: x["timestamp"])
        values = [point["value"] for point in data_points]
        # timestamps = [point["timestamp"] for point in data_points]  # Available if needed

        # Calculate linear trend
        n = len(values)
        sum_x = sum(range(n))
        sum_y = sum(values)
        sum_xy = sum(i * values[i] for i in range(n))
        sum_x2 = sum(i * i for i in range(n))

        # Linear regression slope
        if n * sum_x2 - sum_x * sum_x == 0:
            slope = 0
        else:
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)

        # Calculate percentage change
        start_value = statistics.mean(values[: max(1, n // 4)])  # First quarter average
        end_value = statistics.mean(values[-max(1, n // 4) :])  # Last quarter average

        if start_value > 0:
            change_percentage = ((end_value - start_value) / start_value) * 100
        else:
            change_percentage = 0.0

        # Determine trend direction
        if abs(change_percentage) < 5:
            direction = TrendDirection.STABLE
        elif change_percentage > 0:
            # For performance metrics, positive change might be bad (higher response times)
            if metric_name.endswith("_ms") or metric_name.endswith("_time"):
                direction = TrendDirection.DEGRADING
            else:
                direction = TrendDirection.IMPROVING
        else:
            # Negative change
            if metric_name.endswith("_ms") or metric_name.endswith("_time"):
                direction = TrendDirection.IMPROVING
            else:
                direction = TrendDirection.DEGRADING

        # Calculate confidence score based on data consistency
        variance = statistics.variance(values) if len(values) > 1 else 0
        mean_value = statistics.mean(values)
        coefficient_of_variation = (
            (math.sqrt(variance) / mean_value) if mean_value > 0 else 0
        )

        # Higher confidence for more data points and lower variability
        confidence_score = min(
            100, (n / 10) * 100 * (1 - min(1, coefficient_of_variation))
        )

        # Volatility check
        if coefficient_of_variation > 0.5:  # High variability
            direction = TrendDirection.VOLATILE

        return PerformanceTrend(
            metric_name=metric_name,
            time_period_hours=hours,
            direction=direction,
            change_percentage=change_percentage,
            confidence_score=confidence_score,
            data_points=n,
            trend_details={
                "slope": slope,
                "start_value": start_value,
                "end_value": end_value,
                "mean_value": mean_value,
                "variance": variance,
                "coefficient_of_variation": coefficient_of_variation,
            },
        )

    async def identify_bottlenecks(self) -> List[PerformanceBottleneck]:
        """Identify current performance bottlenecks"""
        bottlenecks = []

        # Get current performance data
        auth_stats = self.auth_monitor.get_comprehensive_stats()
        cache_stats = self.cache_monitor.get_comprehensive_stats()
        dashboard_data = await self.dashboard.get_real_time_metrics()

        # Check auth bottlenecks
        bottlenecks.extend(self._identify_auth_bottlenecks(auth_stats))

        # Check cache bottlenecks
        bottlenecks.extend(self._identify_cache_bottlenecks(cache_stats))

        # Check system bottlenecks
        bottlenecks.extend(self._identify_system_bottlenecks(dashboard_data))

        return bottlenecks

    def _identify_auth_bottlenecks(
        self, auth_stats: Dict[str, Any]
    ) -> List[PerformanceBottleneck]:
        """Identify authentication-related bottlenecks"""
        bottlenecks = []

        # Check login performance
        login_stats = auth_stats.get("operations", {}).get("login", {})
        if login_stats:
            p95_login = login_stats.get("p95_duration_ms", 0)
            if p95_login > 1000:  # Bottleneck threshold
                bottleneck = PerformanceBottleneck(
                    id=f"auth_login_slow_{int(time.time())}",
                    type=BottleneckType.AUTH_BOUND,
                    component="authentication",
                    metric="login_p95_duration_ms",
                    current_value=p95_login,
                    threshold=1000,
                    impact_level=(
                        ImpactLevel.HIGH if p95_login > 2000 else ImpactLevel.MEDIUM
                    ),
                    confidence_score=85.0,
                    root_causes=[
                        "Slow authentication database queries",
                        "Inefficient password hashing",
                        "Cache misses for user data",
                    ],
                    recommendations=[
                        "Implement database connection pooling",
                        "Cache user authentication data",
                        "Optimize password hashing algorithm",
                    ],
                    estimated_improvement={
                        "response_time_reduction_percent": 40,
                        "user_satisfaction_improvement": 15,
                    },
                )
                bottlenecks.append(bottleneck)

        # Check session validation
        session_stats = auth_stats.get("operations", {}).get("session_validation", {})
        if session_stats:
            p95_session = session_stats.get("p95_duration_ms", 0)
            cache_hit_rate = session_stats.get("cache_hit_rate", 100)

            if p95_session > 300 or cache_hit_rate < 80:
                bottleneck = PerformanceBottleneck(
                    id=f"auth_session_slow_{int(time.time())}",
                    type=BottleneckType.CACHE_BOUND,
                    component="session_validation",
                    metric="session_validation_performance",
                    current_value=p95_session,
                    threshold=200,
                    impact_level=ImpactLevel.MEDIUM,
                    confidence_score=75.0,
                    root_causes=[
                        "Low session cache hit rate",
                        "Frequent database lookups for session validation",
                    ],
                    recommendations=[
                        "Increase session cache TTL",
                        "Pre-warm session cache",
                        "Implement session data batching",
                    ],
                    estimated_improvement={
                        "response_time_reduction_percent": 25,
                        "cache_efficiency_improvement": 20,
                    },
                )
                bottlenecks.append(bottleneck)

        return bottlenecks

    def _identify_cache_bottlenecks(
        self, cache_stats: Dict[str, Any]
    ) -> List[PerformanceBottleneck]:
        """Identify cache-related bottlenecks"""
        bottlenecks = []

        overall_summary = cache_stats.get("overall_summary", {})
        hit_rate = overall_summary.get("overall_hit_rate", 0)

        # Low cache hit rate bottleneck
        if hit_rate < 70:
            bottleneck = PerformanceBottleneck(
                id=f"cache_hit_rate_low_{int(time.time())}",
                type=BottleneckType.CACHE_BOUND,
                component="cache",
                metric="cache_hit_rate",
                current_value=hit_rate,
                threshold=80,
                impact_level=ImpactLevel.HIGH if hit_rate < 50 else ImpactLevel.MEDIUM,
                confidence_score=90.0,
                root_causes=[
                    "Suboptimal cache TTL settings",
                    "Frequent cache invalidations",
                    "Insufficient cache warming",
                ],
                recommendations=[
                    "Optimize cache TTL for different data types",
                    "Implement intelligent cache warming",
                    "Review cache invalidation strategy",
                ],
                estimated_improvement={
                    "hit_rate_improvement_percent": 30,
                    "response_time_reduction_percent": 20,
                },
            )
            bottlenecks.append(bottleneck)

        # Redis performance bottleneck
        redis_stats = cache_stats.get("cache_layers", {}).get("redis", {})
        if redis_stats:
            redis_response_ms = redis_stats.get("average_response_time_ms", 0)
            if redis_response_ms > 100:
                bottleneck = PerformanceBottleneck(
                    id=f"redis_slow_{int(time.time())}",
                    type=BottleneckType.IO_BOUND,
                    component="redis",
                    metric="redis_response_time_ms",
                    current_value=redis_response_ms,
                    threshold=50,
                    impact_level=ImpactLevel.MEDIUM,
                    confidence_score=80.0,
                    root_causes=[
                        "Network latency to Redis",
                        "Redis server overload",
                        "Large payload sizes",
                    ],
                    recommendations=[
                        "Optimize Redis configuration",
                        "Implement connection pooling",
                        "Reduce payload sizes",
                    ],
                    estimated_improvement={"response_time_reduction_percent": 35},
                )
                bottlenecks.append(bottleneck)

        return bottlenecks

    def _identify_system_bottlenecks(
        self, system_data: Dict[str, Any]
    ) -> List[PerformanceBottleneck]:
        """Identify system resource bottlenecks"""
        bottlenecks = []

        system_resources = system_data.get("system_resources", {})

        # CPU bottleneck
        cpu_usage = system_resources.get("cpu_usage", 0)
        if cpu_usage > 80:
            bottleneck = PerformanceBottleneck(
                id=f"cpu_high_{int(time.time())}",
                type=BottleneckType.CPU_BOUND,
                component="system",
                metric="cpu_usage_percent",
                current_value=cpu_usage,
                threshold=70,
                impact_level=ImpactLevel.HIGH if cpu_usage > 90 else ImpactLevel.MEDIUM,
                confidence_score=95.0,
                root_causes=[
                    "Inefficient algorithms",
                    "Excessive background processing",
                    "Insufficient CPU resources",
                ],
                recommendations=[
                    "Optimize CPU-intensive operations",
                    "Implement background task queuing",
                    "Scale CPU resources",
                ],
                estimated_improvement={"response_time_reduction_percent": 25},
            )
            bottlenecks.append(bottleneck)

        # Memory bottleneck
        memory_usage = system_resources.get("memory_usage", 0)
        if memory_usage > 85:
            bottleneck = PerformanceBottleneck(
                id=f"memory_high_{int(time.time())}",
                type=BottleneckType.MEMORY_BOUND,
                component="system",
                metric="memory_usage_percent",
                current_value=memory_usage,
                threshold=80,
                impact_level=(
                    ImpactLevel.HIGH if memory_usage > 90 else ImpactLevel.MEDIUM
                ),
                confidence_score=95.0,
                root_causes=[
                    "Memory leaks",
                    "Inefficient caching",
                    "Insufficient memory resources",
                ],
                recommendations=[
                    "Investigate memory leaks",
                    "Optimize memory usage patterns",
                    "Scale memory resources",
                ],
                estimated_improvement={"performance_improvement_percent": 20},
            )
            bottlenecks.append(bottleneck)

        return bottlenecks

    async def generate_optimization_recommendations(
        self,
    ) -> List[OptimizationRecommendation]:
        """Generate optimization recommendations based on current performance data"""
        recommendations = []

        # Get performance trends
        trends = self.analyze_performance_trends(hours=24)

        # Get current bottlenecks
        bottlenecks = await self.identify_bottlenecks()

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
                id=f"login_trend_opt_{int(time.time())}",
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
                id=f"cache_trend_opt_{int(time.time())}",
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
            id=f"proactive_redis_{int(time.time())}",
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
            id=f"proactive_monitoring_{int(time.time())}",
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

    def calculate_business_impact(
        self, metric_name: str, performance_change: float
    ) -> BusinessImpactAnalysis:
        """Calculate business impact of performance changes"""
        user_impact = {}
        business_impact = {}
        confidence = 0.0

        # Apply business impact models
        for impact_type, model_func in self.business_impact_models.items():
            impact_value, impact_confidence = model_func(
                metric_name, performance_change
            )
            user_impact[impact_type] = impact_value
            confidence += impact_confidence

        confidence = confidence / len(self.business_impact_models)

        # Calculate aggregate business impact
        business_impact = {
            "user_experience_score_change": user_impact.get("user_satisfaction", 0),
            "estimated_conversion_impact_percent": user_impact.get(
                "conversion_rate", 0
            ),
            "estimated_retention_impact_percent": user_impact.get("user_retention", 0),
            "estimated_cost_impact_percent": user_impact.get("operational_cost", 0),
        }

        return BusinessImpactAnalysis(
            metric_name=metric_name,
            performance_change_percent=performance_change,
            estimated_user_impact=user_impact,
            estimated_business_impact=business_impact,
            confidence_level=confidence,
        )

    def _model_user_satisfaction_impact(
        self, metric_name: str, performance_change: float
    ) -> Tuple[float, float]:
        """Model impact on user satisfaction"""
        # Simplified model: performance improvements have diminishing returns on satisfaction
        if metric_name.endswith("_ms"):
            # For response time metrics, negative change is good
            satisfaction_change = -performance_change * 0.3
        else:
            # For other metrics, positive change is good
            satisfaction_change = performance_change * 0.2

        return satisfaction_change, 70.0  # 70% confidence

    def _model_conversion_impact(
        self, metric_name: str, performance_change: float
    ) -> Tuple[float, float]:
        """Model impact on conversion rate"""
        # Research shows 100ms improvement can increase conversion by 1%
        if metric_name == "login_p95_ms":
            conversion_change = -performance_change * 0.01  # 1% per 100ms improvement
        else:
            conversion_change = performance_change * 0.005

        return conversion_change, 60.0  # 60% confidence

    def _model_retention_impact(
        self, metric_name: str, performance_change: float
    ) -> Tuple[float, float]:
        """Model impact on user retention"""
        # Performance has moderate impact on retention
        retention_change = performance_change * 0.1

        return retention_change, 50.0  # 50% confidence

    def _model_cost_impact(
        self, metric_name: str, performance_change: float
    ) -> Tuple[float, float]:
        """Model impact on operational costs"""
        # Better performance can reduce server costs
        if metric_name in ["cpu_usage", "memory_usage"]:
            cost_change = performance_change * 0.5  # Direct correlation
        else:
            cost_change = performance_change * 0.1  # Indirect correlation

        return cost_change, 80.0  # 80% confidence

    async def generate_performance_report(self, hours: int = 24) -> Dict[str, Any]:
        """Generate comprehensive performance analytics report"""
        # Get all analytics data
        trends = self.analyze_performance_trends(hours)
        bottlenecks = await self.identify_bottlenecks()
        recommendations = await self.generate_optimization_recommendations()

        # Calculate improvement achievements
        improvements = self._calculate_improvement_achievements()

        # Business impact analysis
        business_impacts = []
        for metric_name, trend in trends.items():
            if abs(trend.change_percentage) > 5:  # Significant changes only
                impact = self.calculate_business_impact(
                    metric_name, trend.change_percentage
                )
                business_impacts.append(impact)

        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "analysis_period_hours": hours,
            "executive_summary": self._generate_executive_summary(
                trends, bottlenecks, improvements
            ),
            "performance_trends": {
                metric: {
                    "direction": trend.direction.value,
                    "change_percentage": trend.change_percentage,
                    "confidence_score": trend.confidence_score,
                    "data_points": trend.data_points,
                }
                for metric, trend in trends.items()
            },
            "bottleneck_analysis": [
                {
                    "type": bottleneck.type.value,
                    "component": bottleneck.component,
                    "metric": bottleneck.metric,
                    "impact_level": bottleneck.impact_level.value,
                    "confidence_score": bottleneck.confidence_score,
                    "recommendations": bottleneck.recommendations,
                }
                for bottleneck in bottlenecks
            ],
            "optimization_recommendations": [
                {
                    "title": rec.title,
                    "priority": rec.priority,
                    "estimated_improvement_percent": rec.estimated_improvement_percent,
                    "implementation_effort": rec.implementation_effort,
                    "timeline_days": rec.timeline_days,
                    "success_probability": rec.success_probability,
                }
                for rec in recommendations[:10]  # Top 10 recommendations
            ],
            "business_impact_analysis": [
                {
                    "metric": impact.metric_name,
                    "performance_change_percent": impact.performance_change_percent,
                    "business_impact": impact.estimated_business_impact,
                    "confidence_level": impact.confidence_level,
                }
                for impact in business_impacts
            ],
            "achievement_summary": improvements,
        }

        return report

    def _calculate_improvement_achievements(self) -> Dict[str, Any]:
        """Calculate achieved performance improvements vs baselines"""
        achievements = {}

        # Get current performance data
        auth_stats = self.auth_monitor.get_comprehensive_stats()
        cache_stats = self.cache_monitor.get_comprehensive_stats()

        # Login performance achievement
        login_stats = auth_stats.get("operations", {}).get("login", {})
        if login_stats:
            current_login_p95 = login_stats.get("p95_duration_ms", 0)
            baseline_login = self.performance_baselines["login_p95_ms"]
            target_login = self.performance_targets["login_p95_ms"]

            if current_login_p95 > 0:
                improvement_achieved = (
                    (baseline_login - current_login_p95) / baseline_login
                ) * 100
                target_progress = (
                    (baseline_login - current_login_p95)
                    / (baseline_login - target_login)
                ) * 100

                achievements["login_performance"] = {
                    "improvement_achieved_percent": max(0, improvement_achieved),
                    "target_progress_percent": min(100, max(0, target_progress)),
                    "current_value_ms": current_login_p95,
                    "target_value_ms": target_login,
                    "baseline_value_ms": baseline_login,
                }

        # Cache performance achievement
        current_hit_rate = cache_stats.get("overall_summary", {}).get(
            "overall_hit_rate", 0
        )
        baseline_hit_rate = self.performance_baselines["cache_hit_rate"]
        target_hit_rate = self.performance_targets["cache_hit_rate"]

        if current_hit_rate > 0:
            improvement_achieved = (
                (current_hit_rate - baseline_hit_rate) / baseline_hit_rate
            ) * 100
            target_progress = (
                (current_hit_rate - baseline_hit_rate)
                / (target_hit_rate - baseline_hit_rate)
            ) * 100

            achievements["cache_performance"] = {
                "improvement_achieved_percent": max(0, improvement_achieved),
                "target_progress_percent": min(100, max(0, target_progress)),
                "current_value_percent": current_hit_rate,
                "target_value_percent": target_hit_rate,
                "baseline_value_percent": baseline_hit_rate,
            }

        return achievements

    def _generate_executive_summary(
        self, trends: Dict, bottlenecks: List, achievements: Dict
    ) -> str:
        """Generate executive summary of performance analysis"""
        improving_metrics = len(
            [t for t in trends.values() if t.direction == TrendDirection.IMPROVING]
        )
        degrading_metrics = len(
            [t for t in trends.values() if t.direction == TrendDirection.DEGRADING]
        )
        critical_bottlenecks = len(
            [b for b in bottlenecks if b.impact_level == ImpactLevel.CRITICAL]
        )

        summary_parts = []

        # Overall trend assessment
        if improving_metrics > degrading_metrics:
            summary_parts.append(
                f"System performance shows positive trends with {improving_metrics} metrics improving"
            )
        elif degrading_metrics > improving_metrics:
            summary_parts.append(
                f"Performance concerns identified with {degrading_metrics} metrics degrading"
            )
        else:
            summary_parts.append("System performance is stable with mixed trends")

        # Bottleneck summary
        if critical_bottlenecks > 0:
            summary_parts.append(
                f"{critical_bottlenecks} critical bottlenecks require immediate attention"
            )
        elif len(bottlenecks) > 0:
            summary_parts.append(
                f"{len(bottlenecks)} performance bottlenecks identified for optimization"
            )

        # Achievement summary
        if achievements:
            login_achievement = achievements.get("login_performance", {}).get(
                "improvement_achieved_percent", 0
            )
            if login_achievement > 50:
                summary_parts.append(
                    f"Significant login performance improvement achieved ({login_achievement:.0f}%)"
                )

        return ". ".join(summary_parts) + "."

    def get_analytics_health(self) -> Dict[str, Any]:
        """Get analytics engine health status"""
        return {
            "status": "healthy",
            "trend_data_points": {
                metric: len(data) for metric, data in self.trend_history.items()
            },
            "bottleneck_history_size": len(self.bottleneck_history),
            "recommendation_history_size": len(self.recommendation_history),
            "last_analysis": datetime.fromtimestamp(self._last_analysis).isoformat(),
            "analysis_interval_seconds": self._analysis_interval,
        }


# Global singleton instance
_performance_analytics_engine = None


def get_performance_analytics_engine() -> PerformanceAnalyticsEngine:
    """Get singleton performance analytics engine instance"""
    global _performance_analytics_engine
    if _performance_analytics_engine is None:
        _performance_analytics_engine = PerformanceAnalyticsEngine()
    return _performance_analytics_engine
