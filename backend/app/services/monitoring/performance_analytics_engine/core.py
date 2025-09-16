"""
Core Performance Analytics Engine

Main engine class that orchestrates all analytics services and provides
the primary interface for performance analytics functionality.
"""

import asyncio
import time
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any, Dict, List

from app.core.logging import get_logger
from app.services.monitoring.auth_performance_monitor import (
    get_auth_performance_monitor,
)
from app.services.monitoring.cache_performance_monitor import (
    get_cache_performance_monitor,
)
from app.services.monitoring.performance_metrics_collector import get_metrics_collector
from app.services.monitoring.system_health_dashboard import get_system_health_dashboard

from .base import (
    BusinessImpactAnalysis,
    OptimizationRecommendation,
    PerformanceBottleneck,
)
from .bottleneck_detection import BottleneckDetectionService
from .business_impact import BusinessImpactService
from .optimization import OptimizationService
from .trend_analysis import TrendAnalysisService
from .utils import ReportingUtils

logger = get_logger(__name__)


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

        # Initialize service components
        self.trend_analyzer = TrendAnalysisService(
            self.trend_history, analysis_window_hours
        )
        self.bottleneck_detector = BottleneckDetectionService()
        self.business_impact_service = BusinessImpactService()
        self.optimization_service = OptimizationService()

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
            await self.trend_analyzer.update_trend_data(
                self.auth_monitor, self.cache_monitor
            )

            # Update bottleneck detection
            bottlenecks = await self.bottleneck_detector.identify_bottlenecks(
                self.auth_monitor, self.cache_monitor, self.dashboard
            )
            for bottleneck in bottlenecks:
                self.bottleneck_history.append(bottleneck)

            # Update recommendations
            recommendations = (
                await self.optimization_service.generate_optimization_recommendations(
                    self.trend_analyzer, self.bottleneck_detector
                )
            )
            for recommendation in recommendations:
                self.recommendation_history.append(recommendation)

            logger.debug("Background performance analysis completed")

        except Exception as e:
            logger.error("Error in background performance analysis: %s", e)

    # Delegate methods to service components
    def analyze_performance_trends(self, hours: int = 24):
        """Analyze performance trends over specified time period"""
        return self.trend_analyzer.analyze_performance_trends(hours)

    async def identify_bottlenecks(self) -> List[PerformanceBottleneck]:
        """Identify current performance bottlenecks"""
        return await self.bottleneck_detector.identify_bottlenecks(
            self.auth_monitor, self.cache_monitor, self.dashboard
        )

    async def generate_optimization_recommendations(
        self,
    ) -> List[OptimizationRecommendation]:
        """Generate optimization recommendations based on current performance data"""
        return await self.optimization_service.generate_optimization_recommendations(
            self.trend_analyzer, self.bottleneck_detector
        )

    def calculate_business_impact(
        self, metric_name: str, performance_change: float
    ) -> BusinessImpactAnalysis:
        """Calculate business impact of performance changes"""
        return self.business_impact_service.calculate_business_impact(
            metric_name, performance_change
        )

    async def generate_performance_report(self, hours: int = 24) -> Dict[str, Any]:
        """Generate comprehensive performance analytics report"""
        # Get all analytics data
        trends = self.analyze_performance_trends(hours)
        bottlenecks = await self.identify_bottlenecks()
        recommendations = await self.generate_optimization_recommendations()

        # Calculate improvement achievements
        improvements = ReportingUtils.calculate_improvement_achievements(
            self.auth_monitor,
            self.cache_monitor,
            self.performance_baselines,
            self.performance_targets,
        )

        # Business impact analysis
        business_impacts = (
            self.business_impact_service.calculate_business_impacts_for_trends(trends)
        )

        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "analysis_period_hours": hours,
            "executive_summary": ReportingUtils.generate_executive_summary(
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

    def get_analytics_health(self) -> Dict[str, Any]:
        """Get analytics engine health status"""
        return ReportingUtils.get_analytics_health_status(
            self.trend_history,
            self.bottleneck_history,
            self.recommendation_history,
            self._last_analysis,
            self._analysis_interval,
        )
