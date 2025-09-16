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

# Import all base types and enums
from .base import (
    BottleneckType,
    BusinessImpactAnalysis,
    ImpactLevel,
    OptimizationRecommendation,
    PerformanceBottleneck,
    PerformanceTrend,
    TrendDirection,
)

# Import main engine class
from .core import PerformanceAnalyticsEngine

# Import service components (for advanced usage)
from .bottleneck_detection import BottleneckDetectionService
from .business_impact import BusinessImpactService
from .optimization import OptimizationService
from .trend_analysis import TrendAnalysisService
from .utils import ReportingUtils

# Global singleton instance
_performance_analytics_engine = None


def get_performance_analytics_engine() -> PerformanceAnalyticsEngine:
    """Get singleton performance analytics engine instance"""
    global _performance_analytics_engine
    if _performance_analytics_engine is None:
        _performance_analytics_engine = PerformanceAnalyticsEngine()
    return _performance_analytics_engine


# Public API exports - maintains backward compatibility
__all__ = [
    # Main engine
    "PerformanceAnalyticsEngine",
    "get_performance_analytics_engine",
    # Base types and enums
    "TrendDirection",
    "BottleneckType",
    "ImpactLevel",
    "PerformanceTrend",
    "PerformanceBottleneck",
    "OptimizationRecommendation",
    "BusinessImpactAnalysis",
    # Service components (for advanced usage)
    "TrendAnalysisService",
    "BottleneckDetectionService",
    "OptimizationService",
    "BusinessImpactService",
    "ReportingUtils",
]
