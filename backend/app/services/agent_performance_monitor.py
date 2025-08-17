"""
Agent Performance Monitor with Learning Integration
Monitors agent performance, identifies bottlenecks, and provides optimization recommendations
based on performance patterns and learning data.
"""

import asyncio
import logging
import statistics
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from app.services.agent_learning_system import LearningContext, agent_learning_system
from app.services.enhanced_agent_memory import enhanced_agent_memory
from app.services.performance.response_optimizer import response_optimizer

logger = logging.getLogger(__name__)


@dataclass
class PerformanceEvent:
    """Individual performance event record"""

    event_id: str
    agent_id: str
    operation_type: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None
    memory_usage: Optional[float] = None
    cache_hit: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceMetrics:
    """Aggregated performance metrics"""

    operation_type: str
    total_operations: int
    successful_operations: int
    avg_duration: float
    min_duration: float
    max_duration: float
    p95_duration: float
    error_rate: float
    cache_hit_rate: float
    throughput_per_minute: float
    memory_efficiency: float


class AgentPerformanceMonitor:
    """
    Comprehensive agent performance monitoring with learning integration
    """

    def __init__(self, max_events: int = 10000, analysis_window_hours: int = 24):
        self.max_events = max_events
        self.analysis_window = timedelta(hours=analysis_window_hours)

        # Event storage - using deque for efficient memory management
        self.performance_events: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=max_events)
        )
        self.active_operations: Dict[str, PerformanceEvent] = {}

        # Performance baselines and thresholds
        self.performance_baselines = {
            "field_mapping": {"target_duration": 30.0, "target_success_rate": 0.95},
            "data_cleansing": {"target_duration": 45.0, "target_success_rate": 0.90},
            "asset_inventory": {"target_duration": 60.0, "target_success_rate": 0.92},
            "dependency_analysis": {
                "target_duration": 90.0,
                "target_success_rate": 0.88,
            },
            "tech_debt_analysis": {
                "target_duration": 120.0,
                "target_success_rate": 0.85,
            },
        }

        # Performance trends tracking
        self.performance_trends: Dict[str, List[Tuple[datetime, float]]] = defaultdict(
            list
        )

        # Optimization recommendations cache
        self.optimization_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl = timedelta(hours=1)

        logger.info("🔍 Agent Performance Monitor initialized")

    def start_operation(
        self,
        agent_id: str,
        operation_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Start monitoring an operation"""
        event_id = f"{agent_id}_{operation_type}_{int(time.time() * 1000)}"

        event = PerformanceEvent(
            event_id=event_id,
            agent_id=agent_id,
            operation_type=operation_type,
            start_time=datetime.utcnow(),
            metadata=metadata or {},
        )

        self.active_operations[event_id] = event
        logger.debug(f"Started monitoring operation {event_id}")

        return event_id

    def end_operation(
        self,
        event_id: str,
        success: bool = True,
        error_message: Optional[str] = None,
        cache_hit: bool = False,
        memory_usage: Optional[float] = None,
    ) -> Optional[PerformanceEvent]:
        """End monitoring an operation"""
        if event_id not in self.active_operations:
            logger.warning(f"Operation {event_id} not found in active operations")
            return None

        event = self.active_operations.pop(event_id)
        event.end_time = datetime.utcnow()
        event.duration = (event.end_time - event.start_time).total_seconds()
        event.success = success
        event.error_message = error_message
        event.cache_hit = cache_hit
        event.memory_usage = memory_usage

        # Store in event history
        self.performance_events[event.operation_type].append(event)

        # Update performance trends
        self.performance_trends[event.operation_type].append(
            (event.end_time, event.duration)
        )

        # Keep trends within analysis window
        cutoff_time = datetime.utcnow() - self.analysis_window
        self.performance_trends[event.operation_type] = [
            (ts, dur)
            for ts, dur in self.performance_trends[event.operation_type]
            if ts > cutoff_time
        ]

        logger.debug(f"Completed operation {event_id} in {event.duration:.2f}s")

        # Trigger real-time analysis for critical performance issues
        asyncio.create_task(self._analyze_real_time_performance(event))

        return event

    async def _analyze_real_time_performance(self, event: PerformanceEvent):
        """Analyze performance in real-time and trigger alerts if needed"""
        try:
            baseline = self.performance_baselines.get(event.operation_type, {})
            target_duration = baseline.get("target_duration", 60.0)

            # Check for performance degradation
            if event.duration and event.duration > target_duration * 2:
                logger.warning(
                    f"🚨 Performance alert: {event.operation_type} took {event.duration:.2f}s "
                    f"(target: {target_duration}s)"
                )

                # Store performance issue in memory for learning
                await enhanced_agent_memory.store_memory(
                    {
                        "type": "performance_issue",
                        "operation_type": event.operation_type,
                        "duration": event.duration,
                        "target_duration": target_duration,
                        "severity": (
                            "high" if event.duration > target_duration * 3 else "medium"
                        ),
                        "context": event.metadata,
                    },
                    memory_type="performance_alert",
                    context=LearningContext(),
                    metadata={"alert_level": "high", "requires_investigation": True},
                )

        except Exception as e:
            logger.error(f"Failed to analyze real-time performance: {e}")

    def get_performance_metrics(
        self,
        operation_type: Optional[str] = None,
        time_window: Optional[timedelta] = None,
    ) -> Dict[str, PerformanceMetrics]:
        """Get aggregated performance metrics"""
        time_window = time_window or self.analysis_window
        cutoff_time = datetime.utcnow() - time_window

        metrics = {}

        # Determine which operation types to analyze
        if operation_type:
            operation_types = [operation_type]
        else:
            operation_types = list(self.performance_events.keys())

        for op_type in operation_types:
            events = [
                event
                for event in self.performance_events[op_type]
                if event.end_time and event.end_time > cutoff_time
            ]

            if not events:
                continue

            # Calculate metrics
            durations = [e.duration for e in events if e.duration is not None]
            successful_events = [e for e in events if e.success]
            cache_hits = [e for e in events if e.cache_hit]

            if durations:
                metrics[op_type] = PerformanceMetrics(
                    operation_type=op_type,
                    total_operations=len(events),
                    successful_operations=len(successful_events),
                    avg_duration=statistics.mean(durations),
                    min_duration=min(durations),
                    max_duration=max(durations),
                    p95_duration=(
                        statistics.quantiles(durations, n=20)[18]
                        if len(durations) > 1
                        else durations[0]
                    ),
                    error_rate=(len(events) - len(successful_events)) / len(events),
                    cache_hit_rate=len(cache_hits) / len(events),
                    throughput_per_minute=len(events)
                    / (time_window.total_seconds() / 60),
                    memory_efficiency=self._calculate_memory_efficiency(events),
                )

        return metrics

    def _calculate_memory_efficiency(self, events: List[PerformanceEvent]) -> float:
        """Calculate memory efficiency score"""
        try:
            memory_usages = [
                e.memory_usage for e in events if e.memory_usage is not None
            ]
            if not memory_usages:
                return 1.0  # Default to perfect if no data

            # Simple efficiency calculation based on memory usage consistency
            avg_memory = statistics.mean(memory_usages)
            memory_variance = (
                statistics.variance(memory_usages) if len(memory_usages) > 1 else 0
            )

            # Lower variance indicates better memory efficiency
            efficiency = max(0.0, 1.0 - (memory_variance / (avg_memory**2)))
            return min(1.0, efficiency)

        except Exception:
            return 1.0

    async def analyze_performance_trends(
        self, operation_type: str, context: Optional[LearningContext] = None
    ) -> Dict[str, Any]:
        """Analyze performance trends and identify patterns"""
        try:
            trends = self.performance_trends.get(operation_type, [])
            if len(trends) < 10:  # Need minimum data for trend analysis
                return {"status": "insufficient_data", "data_points": len(trends)}

            # Extract time series data
            [ts for ts, _ in trends]
            durations = [dur for _, dur in trends]

            # Calculate trend metrics
            recent_avg = statistics.mean(durations[-10:])  # Last 10 operations
            historical_avg = (
                statistics.mean(durations[:-10]) if len(durations) > 10 else recent_avg
            )

            trend_direction = (
                "improving" if recent_avg < historical_avg else "degrading"
            )
            trend_magnitude = (
                abs(recent_avg - historical_avg) / historical_avg
                if historical_avg > 0
                else 0
            )

            # Detect performance patterns
            patterns = await self._detect_performance_patterns(operation_type, trends)

            # Generate recommendations
            recommendations = await self._generate_performance_recommendations(
                operation_type, trends, patterns, context
            )

            analysis_result = {
                "operation_type": operation_type,
                "trend_direction": trend_direction,
                "trend_magnitude": trend_magnitude,
                "recent_avg_duration": recent_avg,
                "historical_avg_duration": historical_avg,
                "data_points": len(trends),
                "patterns_detected": patterns,
                "recommendations": recommendations,
                "analysis_timestamp": datetime.utcnow().isoformat(),
            }

            # Store analysis in memory for future reference
            if context:
                await enhanced_agent_memory.store_memory(
                    analysis_result,
                    memory_type="performance_analysis",
                    context=context,
                    metadata={"analysis_type": "trend_analysis"},
                )

            return analysis_result

        except Exception as e:
            logger.error(f"Failed to analyze performance trends: {e}")
            return {"error": str(e)}

    async def _detect_performance_patterns(
        self, operation_type: str, trends: List[Tuple[datetime, float]]
    ) -> List[Dict[str, Any]]:
        """Detect patterns in performance data"""
        patterns = []

        try:
            if len(trends) < 20:
                return patterns

            durations = [dur for _, dur in trends]

            # Detect outliers
            q1 = statistics.quantiles(durations, n=4)[0]
            q3 = statistics.quantiles(durations, n=4)[2]
            iqr = q3 - q1
            outlier_threshold = q3 + 1.5 * iqr

            outliers = [i for i, dur in enumerate(durations) if dur > outlier_threshold]
            if len(outliers) > len(durations) * 0.1:  # More than 10% outliers
                patterns.append(
                    {
                        "type": "frequent_outliers",
                        "description": (
                            f"High frequency of performance outliers detected "
                            f"({len(outliers)} out of {len(durations)})"
                        ),
                        "severity": "medium",
                    }
                )

            # Detect degradation patterns
            recent_chunk = durations[-10:]
            earlier_chunk = (
                durations[-20:-10] if len(durations) >= 20 else durations[:-10]
            )

            if statistics.mean(recent_chunk) > statistics.mean(earlier_chunk) * 1.2:
                patterns.append(
                    {
                        "type": "performance_degradation",
                        "description": "Recent performance is 20% slower than previous period",
                        "severity": "high",
                    }
                )

            # Detect improvement patterns
            if statistics.mean(recent_chunk) < statistics.mean(earlier_chunk) * 0.8:
                patterns.append(
                    {
                        "type": "performance_improvement",
                        "description": "Recent performance is 20% faster than previous period",
                        "severity": "positive",
                    }
                )

            # Detect consistency patterns
            recent_variance = (
                statistics.variance(recent_chunk) if len(recent_chunk) > 1 else 0
            )
            if recent_variance < statistics.variance(durations) * 0.5:
                patterns.append(
                    {
                        "type": "improved_consistency",
                        "description": "Performance consistency has improved significantly",
                        "severity": "positive",
                    }
                )

            return patterns

        except Exception as e:
            logger.error(f"Failed to detect performance patterns: {e}")
            return []

    async def _generate_performance_recommendations(
        self,
        operation_type: str,
        trends: List[Tuple[datetime, float]],
        patterns: List[Dict[str, Any]],
        context: Optional[LearningContext],
    ) -> List[str]:
        """Generate performance optimization recommendations"""
        recommendations = []

        try:
            # Get baseline expectations
            baseline = self.performance_baselines.get(operation_type, {})
            target_duration = baseline.get("target_duration", 60.0)

            # Analyze current performance vs baseline
            recent_durations = [dur for _, dur in trends[-10:]]
            avg_recent = statistics.mean(recent_durations) if recent_durations else 0

            if avg_recent > target_duration * 1.5:
                recommendations.append(
                    f"Consider enabling response caching - current avg ({avg_recent:.1f}s) significantly exceeds target ({target_duration}s)"
                )

            if avg_recent > target_duration * 1.2:
                recommendations.append(
                    "Review agent configuration - consider reducing max_iter or enabling parallel processing"
                )

            # Pattern-based recommendations
            for pattern in patterns:
                if pattern["type"] == "frequent_outliers":
                    recommendations.append(
                        "Investigate outlier causes - consider implementing timeout controls"
                    )
                elif pattern["type"] == "performance_degradation":
                    recommendations.append(
                        "Performance degradation detected - review recent configuration changes"
                    )
                elif pattern["type"] == "improved_consistency":
                    recommendations.append(
                        "Performance consistency improved - current optimization strategies are effective"
                    )

            # Memory-based recommendations
            if context:
                # Check for similar optimization experiences
                past_optimizations = await enhanced_agent_memory.retrieve_memories(
                    {"type": "optimization_applied", "operation_type": operation_type},
                    context=context,
                    limit=5,
                )

                if past_optimizations:
                    successful_optimizations = [
                        opt
                        for opt in past_optimizations
                        if opt.content.get("success", False)
                    ]

                    for opt in successful_optimizations:
                        optimization_type = opt.content.get("optimization_type", "")
                        improvement = opt.content.get("improvement_factor", 1.0)

                        if improvement > 1.2:  # 20% improvement
                            recommendations.append(
                                f"Consider re-applying {optimization_type} - previously achieved {improvement:.1f}x improvement"
                            )

            # Cache-based recommendations
            cache_stats = response_optimizer.get_performance_summary()
            cache_hit_rate = cache_stats.get("cache_hit_rate", 0)

            if cache_hit_rate < 0.3:
                recommendations.append(
                    "Enable more aggressive caching - current cache hit rate is low"
                )

            return recommendations[:5]  # Limit to top 5 recommendations

        except Exception as e:
            logger.error(f"Failed to generate recommendations: {e}")
            return ["Unable to generate recommendations due to analysis error"]

    async def optimize_based_on_performance(
        self, operation_type: str, context: Optional[LearningContext] = None
    ) -> Dict[str, Any]:
        """Apply optimizations based on performance analysis"""
        try:
            # Check optimization cache
            cache_key = (
                f"{operation_type}_{context.context_hash if context else 'global'}"
            )
            if cache_key in self.optimization_cache:
                cached_result = self.optimization_cache[cache_key]
                if datetime.utcnow() - cached_result["timestamp"] < self.cache_ttl:
                    return cached_result

            # Analyze current performance
            metrics = self.get_performance_metrics(operation_type)
            current_metrics = metrics.get(operation_type)

            if not current_metrics:
                return {"status": "no_data", "optimizations_applied": []}

            optimization_result = {
                "operation_type": operation_type,
                "optimizations_applied": [],
                "expected_improvements": {},
                "baseline_metrics": {
                    "avg_duration": current_metrics.avg_duration,
                    "error_rate": current_metrics.error_rate,
                    "cache_hit_rate": current_metrics.cache_hit_rate,
                },
            }

            # Apply cache optimizations
            if current_metrics.cache_hit_rate < 0.5:
                # Increase cache TTL
                response_optimizer.cache.ttl_seconds = min(
                    7200, response_optimizer.cache.ttl_seconds * 1.5
                )
                optimization_result["optimizations_applied"].append(
                    "increased_cache_ttl"
                )
                optimization_result["expected_improvements"]["cache_hit_rate"] = 0.2

            # Apply memory optimizations
            if (
                current_metrics.avg_duration
                > self.performance_baselines.get(operation_type, {}).get(
                    "target_duration", 60
                )
                * 1.5
            ):
                # Trigger memory cleanup
                memory_cleanup = (
                    await enhanced_agent_memory.optimize_memory_performance()
                )
                optimization_result["optimizations_applied"].append(
                    "memory_optimization"
                )
                optimization_result["expected_improvements"][
                    "avg_duration"
                ] = -0.3  # 30% improvement expected
                optimization_result["memory_cleanup_results"] = memory_cleanup

            # Learn from optimization patterns
            if context:
                await agent_learning_system.learn_from_performance_metrics(
                    operation_type,
                    {
                        "baseline_duration": current_metrics.avg_duration,
                        "current_duration": current_metrics.avg_duration,
                        "error_rate": current_metrics.error_rate,
                        "cache_hit_rate": current_metrics.cache_hit_rate,
                    },
                    optimization_result["optimizations_applied"],
                    context,
                )

            # Cache optimization result
            optimization_result["timestamp"] = datetime.utcnow()
            self.optimization_cache[cache_key] = optimization_result

            return optimization_result

        except Exception as e:
            logger.error(f"Failed to optimize based on performance: {e}")
            return {"error": str(e), "optimizations_applied": []}

    def get_comprehensive_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        try:
            # Get metrics for all operation types
            all_metrics = self.get_performance_metrics()

            # Calculate overall health score
            health_scores = []
            for op_type, metrics in all_metrics.items():
                baseline = self.performance_baselines.get(op_type, {})
                target_duration = baseline.get("target_duration", 60.0)
                target_success_rate = baseline.get("target_success_rate", 0.9)

                duration_score = (
                    min(1.0, target_duration / metrics.avg_duration)
                    if metrics.avg_duration > 0
                    else 1.0
                )
                success_score = (
                    (1 - metrics.error_rate) / target_success_rate
                    if target_success_rate > 0
                    else 1.0
                )

                health_score = (duration_score + success_score) / 2
                health_scores.append(health_score)

            overall_health = statistics.mean(health_scores) if health_scores else 0.0

            # Generate health grade
            if overall_health >= 0.9:
                health_grade = "A"
            elif overall_health >= 0.8:
                health_grade = "B"
            elif overall_health >= 0.7:
                health_grade = "C"
            elif overall_health >= 0.6:
                health_grade = "D"
            else:
                health_grade = "F"

            report = {
                "overall_health_score": overall_health,
                "health_grade": health_grade,
                "operation_metrics": {
                    op: {
                        "avg_duration": m.avg_duration,
                        "error_rate": m.error_rate,
                        "cache_hit_rate": m.cache_hit_rate,
                        "throughput_per_minute": m.throughput_per_minute,
                    }
                    for op, m in all_metrics.items()
                },
                "active_operations": len(self.active_operations),
                "total_operations_monitored": sum(
                    len(events) for events in self.performance_events.values()
                ),
                "monitoring_window_hours": self.analysis_window.total_seconds() / 3600,
                "generated_at": datetime.utcnow().isoformat(),
            }

            return report

        except Exception as e:
            logger.error(f"Failed to generate comprehensive report: {e}")
            return {"error": str(e)}


# Global performance monitor instance
agent_performance_monitor = AgentPerformanceMonitor()


# Decorator for automatic performance monitoring
def monitor_performance(operation_type: str):
    """Decorator to automatically monitor agent operation performance"""

    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            agent_id = kwargs.get("agent_id", f"agent_{func.__name__}")
            event_id = agent_performance_monitor.start_operation(
                agent_id, operation_type
            )

            try:
                result = await func(*args, **kwargs)
                agent_performance_monitor.end_operation(event_id, success=True)
                return result
            except Exception as e:
                agent_performance_monitor.end_operation(
                    event_id, success=False, error_message=str(e)
                )
                raise

        def sync_wrapper(*args, **kwargs):
            agent_id = kwargs.get("agent_id", f"agent_{func.__name__}")
            event_id = agent_performance_monitor.start_operation(
                agent_id, operation_type
            )

            try:
                result = func(*args, **kwargs)
                agent_performance_monitor.end_operation(event_id, success=True)
                return result
            except Exception as e:
                agent_performance_monitor.end_operation(
                    event_id, success=False, error_message=str(e)
                )
                raise

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator
