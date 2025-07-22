"""
Performance Monitoring and Optimization for ADCS Platform Adapters

This module provides comprehensive performance monitoring, metrics collection,
optimization recommendations, and adaptive tuning for all platform adapters.
"""

import asyncio
import json
import logging
import statistics
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TypeVar

T = TypeVar('T')


class MetricType(str, Enum):
    """Types of performance metrics"""
    LATENCY = "latency"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    RESOURCE_USAGE = "resource_usage"
    CACHE_HIT_RATE = "cache_hit_rate"
    API_QUOTA_USAGE = "api_quota_usage"
    CONCURRENT_OPERATIONS = "concurrent_operations"
    DATA_VOLUME = "data_volume"


class OptimizationLevel(str, Enum):
    """Optimization recommendation levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class PerformanceMetric:
    """Individual performance metric"""
    timestamp: datetime
    metric_type: MetricType
    value: float
    unit: str
    adapter_name: str
    platform: str
    operation: str
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceSnapshot:
    """Snapshot of adapter performance at a point in time"""
    timestamp: datetime
    adapter_name: str
    platform: str
    metrics: Dict[MetricType, float]
    resource_usage: Dict[str, float]
    active_operations: int
    queue_size: int
    error_count: int
    success_count: int


@dataclass
class OptimizationRecommendation:
    """Performance optimization recommendation"""
    recommendation_id: str
    level: OptimizationLevel
    title: str
    description: str
    expected_improvement: str
    implementation_complexity: str
    adapter_name: str
    platform: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    estimated_effort_hours: float = 0.0
    priority_score: float = 0.0


@dataclass
class PerformanceThresholds:
    """Performance thresholds for alerting and optimization"""
    max_latency_ms: float = 5000.0
    min_throughput_ops_per_sec: float = 1.0
    max_error_rate_percent: float = 5.0
    max_memory_usage_mb: float = 512.0
    max_cpu_usage_percent: float = 80.0
    max_concurrent_operations: int = 10
    max_queue_size: int = 100
    cache_hit_rate_target: float = 0.8


class PerformanceProfiler:
    """Profiles adapter performance and collects detailed metrics"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.PerformanceProfiler")
        self._active_operations: Dict[str, Dict[str, Any]] = {}
        self._operation_history: deque = deque(maxlen=1000)
        
    async def profile_operation(
        self,
        operation_id: str,
        adapter_name: str,
        platform: str,
        operation_type: str,
        func: Callable[..., T],
        *args,
        **kwargs
    ) -> T:
        """
        Profile a single adapter operation
        
        Args:
            operation_id: Unique identifier for this operation
            adapter_name: Name of the adapter
            platform: Platform being accessed
            operation_type: Type of operation (e.g., 'collect_data', 'validate_credentials')
            func: Function to profile
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result with performance data collected
        """
        start_time = time.time()
        start_memory = self._get_memory_usage()
        
        # Record operation start
        operation_context = {
            'operation_id': operation_id,
            'adapter_name': adapter_name,
            'platform': platform,
            'operation_type': operation_type,
            'start_time': start_time,
            'start_memory': start_memory,
            'args_count': len(args),
            'kwargs_keys': list(kwargs.keys())
        }
        
        self._active_operations[operation_id] = operation_context
        
        try:
            # Execute function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
                
            # Record success metrics
            end_time = time.time()
            end_memory = self._get_memory_usage()
            
            operation_metrics = {
                'operation_id': operation_id,
                'adapter_name': adapter_name,
                'platform': platform,
                'operation_type': operation_type,
                'duration_ms': (end_time - start_time) * 1000,
                'memory_delta_mb': end_memory - start_memory,
                'success': True,
                'timestamp': datetime.utcnow(),
                'result_size': self._estimate_result_size(result)
            }
            
            self._operation_history.append(operation_metrics)
            
            return result
            
        except Exception as e:
            # Record error metrics
            end_time = time.time()
            end_memory = self._get_memory_usage()
            
            operation_metrics = {
                'operation_id': operation_id,
                'adapter_name': adapter_name,
                'platform': platform,
                'operation_type': operation_type,
                'duration_ms': (end_time - start_time) * 1000,
                'memory_delta_mb': end_memory - start_memory,
                'success': False,
                'error_type': type(e).__name__,
                'error_message': str(e),
                'timestamp': datetime.utcnow()
            }
            
            self._operation_history.append(operation_metrics)
            raise
            
        finally:
            # Clean up active operation tracking
            if operation_id in self._active_operations:
                del self._active_operations[operation_id]
                
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            return 0.0
            
    def _estimate_result_size(self, result: Any) -> int:
        """Estimate the size of a result object"""
        try:
            if hasattr(result, 'data') and isinstance(result.data, (list, dict)):
                return len(json.dumps(result.data))
            elif isinstance(result, (list, dict)):
                return len(json.dumps(result))
            else:
                return len(str(result))
        except Exception:
            return 0
            
    def get_operation_stats(
        self,
        adapter_name: Optional[str] = None,
        platform: Optional[str] = None,
        operation_type: Optional[str] = None,
        hours: int = 24
    ) -> Dict[str, Any]:
        """Get operation statistics with optional filtering"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Filter operations
        filtered_ops = [
            op for op in self._operation_history
            if op['timestamp'] >= cutoff_time
        ]
        
        if adapter_name:
            filtered_ops = [op for op in filtered_ops if op['adapter_name'] == adapter_name]
        if platform:
            filtered_ops = [op for op in filtered_ops if op['platform'] == platform]
        if operation_type:
            filtered_ops = [op for op in filtered_ops if op['operation_type'] == operation_type]
            
        if not filtered_ops:
            return {'total_operations': 0}
            
        # Calculate statistics
        durations = [op['duration_ms'] for op in filtered_ops]
        successes = [op for op in filtered_ops if op['success']]
        failures = [op for op in filtered_ops if not op['success']]
        
        stats = {
            'total_operations': len(filtered_ops),
            'successful_operations': len(successes),
            'failed_operations': len(failures),
            'success_rate': len(successes) / len(filtered_ops) if filtered_ops else 0,
            'average_duration_ms': statistics.mean(durations) if durations else 0,
            'median_duration_ms': statistics.median(durations) if durations else 0,
            'p95_duration_ms': self._calculate_percentile(durations, 0.95) if durations else 0,
            'p99_duration_ms': self._calculate_percentile(durations, 0.99) if durations else 0,
            'min_duration_ms': min(durations) if durations else 0,
            'max_duration_ms': max(durations) if durations else 0,
        }
        
        # Add memory statistics if available
        memory_deltas = [op.get('memory_delta_mb', 0) for op in filtered_ops]
        if memory_deltas:
            stats.update({
                'average_memory_delta_mb': statistics.mean(memory_deltas),
                'max_memory_delta_mb': max(memory_deltas),
                'min_memory_delta_mb': min(memory_deltas)
            })
            
        return stats
        
    def _calculate_percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile of a list of values"""
        if not values:
            return 0.0
        sorted_values = sorted(values)
        index = int(percentile * (len(sorted_values) - 1))
        return sorted_values[index]


class PerformanceMonitor:
    """Main performance monitoring system for adapters"""
    
    def __init__(self, thresholds: Optional[PerformanceThresholds] = None):
        self.thresholds = thresholds or PerformanceThresholds()
        self.logger = logging.getLogger(f"{__name__}.PerformanceMonitor")
        self.profiler = PerformanceProfiler()
        
        # Metrics storage
        self._metrics: deque = deque(maxlen=10000)
        self._snapshots: deque = deque(maxlen=1000)
        self._recommendations: List[OptimizationRecommendation] = []
        
        # Real-time tracking
        self._adapter_states: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self._performance_trends: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        
    async def record_metric(
        self,
        metric_type: MetricType,
        value: float,
        unit: str,
        adapter_name: str,
        platform: str,
        operation: str,
        context: Optional[Dict[str, Any]] = None
    ):
        """Record a performance metric"""
        metric = PerformanceMetric(
            timestamp=datetime.utcnow(),
            metric_type=metric_type,
            value=value,
            unit=unit,
            adapter_name=adapter_name,
            platform=platform,
            operation=operation,
            context=context or {}
        )
        
        self._metrics.append(metric)
        
        # Update real-time trends
        trend_key = f"{adapter_name}:{platform}:{metric_type.value}"
        self._performance_trends[trend_key].append({
            'timestamp': metric.timestamp,
            'value': value
        })
        
        # Check for threshold violations
        await self._check_thresholds(metric)
        
    async def create_snapshot(self, adapter_name: str, platform: str) -> PerformanceSnapshot:
        """Create a performance snapshot for an adapter"""
        current_time = datetime.utcnow()
        
        # Get recent metrics for this adapter
        recent_metrics = [
            m for m in self._metrics
            if m.adapter_name == adapter_name 
            and m.platform == platform
            and m.timestamp >= current_time - timedelta(minutes=5)
        ]
        
        # Calculate aggregated metrics
        metrics_by_type = defaultdict(list)
        for metric in recent_metrics:
            metrics_by_type[metric.metric_type].append(metric.value)
            
        aggregated_metrics = {}
        for metric_type, values in metrics_by_type.items():
            if values:
                aggregated_metrics[metric_type] = statistics.mean(values)
                
        # Get adapter state
        adapter_key = f"{adapter_name}:{platform}"
        state = self._adapter_states.get(adapter_key, {})
        
        snapshot = PerformanceSnapshot(
            timestamp=current_time,
            adapter_name=adapter_name,
            platform=platform,
            metrics=aggregated_metrics,
            resource_usage=state.get('resource_usage', {}),
            active_operations=state.get('active_operations', 0),
            queue_size=state.get('queue_size', 0),
            error_count=state.get('error_count', 0),
            success_count=state.get('success_count', 0)
        )
        
        self._snapshots.append(snapshot)
        return snapshot
        
    async def _check_thresholds(self, metric: PerformanceMetric):
        """Check if metric violates performance thresholds"""
        violations = []
        
        if metric.metric_type == MetricType.LATENCY and metric.value > self.thresholds.max_latency_ms:
            violations.append(f"High latency: {metric.value:.1f}ms exceeds threshold {self.thresholds.max_latency_ms}ms")
            
        elif metric.metric_type == MetricType.ERROR_RATE and metric.value > self.thresholds.max_error_rate_percent:
            violations.append(f"High error rate: {metric.value:.1f}% exceeds threshold {self.thresholds.max_error_rate_percent}%")
            
        elif metric.metric_type == MetricType.THROUGHPUT and metric.value < self.thresholds.min_throughput_ops_per_sec:
            violations.append(f"Low throughput: {metric.value:.1f} ops/sec below threshold {self.thresholds.min_throughput_ops_per_sec}")
            
        if violations:
            self.logger.warning(
                f"Performance threshold violations for {metric.adapter_name}:{metric.platform} - {', '.join(violations)}"
            )
            
    async def analyze_performance_trends(
        self,
        adapter_name: str,
        platform: str,
        hours: int = 24
    ) -> Dict[str, Any]:
        """Analyze performance trends for an adapter"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Get metrics for the specified time period
        relevant_metrics = [
            m for m in self._metrics
            if m.adapter_name == adapter_name
            and m.platform == platform
            and m.timestamp >= cutoff_time
        ]
        
        if not relevant_metrics:
            return {'status': 'insufficient_data'}
            
        # Group metrics by type
        metrics_by_type = defaultdict(list)
        for metric in relevant_metrics:
            metrics_by_type[metric.metric_type].append({
                'timestamp': metric.timestamp,
                'value': metric.value
            })
            
        # Analyze trends for each metric type
        trends = {}
        for metric_type, values in metrics_by_type.items():
            if len(values) < 2:
                continue
                
            # Calculate trend direction
            recent_values = [v['value'] for v in values[-10:]]  # Last 10 values
            early_values = [v['value'] for v in values[:10]]   # First 10 values
            
            if len(recent_values) >= 2 and len(early_values) >= 2:
                recent_avg = statistics.mean(recent_values)
                early_avg = statistics.mean(early_values)
                
                if recent_avg > early_avg * 1.1:  # 10% increase
                    trend_direction = 'increasing'
                elif recent_avg < early_avg * 0.9:  # 10% decrease
                    trend_direction = 'decreasing'
                else:
                    trend_direction = 'stable'
                    
                trends[metric_type.value] = {
                    'direction': trend_direction,
                    'current_average': recent_avg,
                    'baseline_average': early_avg,
                    'change_percent': ((recent_avg - early_avg) / early_avg * 100) if early_avg > 0 else 0,
                    'data_points': len(values)
                }
                
        return {
            'adapter_name': adapter_name,
            'platform': platform,
            'analysis_period_hours': hours,
            'trends': trends,
            'total_data_points': len(relevant_metrics)
        }
        
    async def generate_optimization_recommendations(
        self,
        adapter_name: str,
        platform: str
    ) -> List[OptimizationRecommendation]:
        """Generate optimization recommendations based on performance analysis"""
        recommendations = []
        
        # Get recent performance data
        trends = await self.analyze_performance_trends(adapter_name, platform, hours=24)
        operation_stats = self.profiler.get_operation_stats(adapter_name, platform, hours=24)
        
        if trends.get('status') == 'insufficient_data':
            return recommendations
            
        # Analyze latency issues
        latency_trend = trends.get('trends', {}).get('latency')
        if latency_trend and latency_trend['current_average'] > self.thresholds.max_latency_ms:
            recommendations.append(OptimizationRecommendation(
                recommendation_id=f"latency_opt_{adapter_name}_{platform}_{int(time.time())}",
                level=OptimizationLevel.HIGH,
                title="Reduce API Call Latency",
                description=f"Average latency is {latency_trend['current_average']:.1f}ms, exceeding threshold. Consider implementing request batching, connection pooling, or caching.",
                expected_improvement="20-40% latency reduction",
                implementation_complexity="Medium",
                adapter_name=adapter_name,
                platform=platform,
                parameters={
                    'current_latency_ms': latency_trend['current_average'],
                    'threshold_ms': self.thresholds.max_latency_ms,
                    'suggested_batch_size': 50,
                    'suggested_connection_pool_size': 5
                },
                estimated_effort_hours=4.0,
                priority_score=0.8
            ))
            
        # Analyze error rate issues
        error_rate_trend = trends.get('trends', {}).get('error_rate')
        if error_rate_trend and error_rate_trend['current_average'] > self.thresholds.max_error_rate_percent:
            recommendations.append(OptimizationRecommendation(
                recommendation_id=f"error_rate_opt_{adapter_name}_{platform}_{int(time.time())}",
                level=OptimizationLevel.CRITICAL,
                title="Improve Error Handling",
                description=f"Error rate is {error_rate_trend['current_average']:.1f}%, above acceptable threshold. Review retry strategies and error classification.",
                expected_improvement="50-70% error reduction",
                implementation_complexity="Low",
                adapter_name=adapter_name,
                platform=platform,
                parameters={
                    'current_error_rate': error_rate_trend['current_average'],
                    'threshold_rate': self.thresholds.max_error_rate_percent,
                    'suggested_retry_attempts': 3,
                    'suggested_backoff_strategy': 'exponential'
                },
                estimated_effort_hours=2.0,
                priority_score=0.9
            ))
            
        # Analyze throughput issues
        throughput_trend = trends.get('trends', {}).get('throughput')
        if throughput_trend and throughput_trend['current_average'] < self.thresholds.min_throughput_ops_per_sec:
            recommendations.append(OptimizationRecommendation(
                recommendation_id=f"throughput_opt_{adapter_name}_{platform}_{int(time.time())}",
                level=OptimizationLevel.MEDIUM,
                title="Increase Operation Throughput",
                description=f"Throughput is {throughput_trend['current_average']:.1f} ops/sec, below target. Consider parallel processing or async optimizations.",
                expected_improvement="2-3x throughput increase",
                implementation_complexity="High",
                adapter_name=adapter_name,
                platform=platform,
                parameters={
                    'current_throughput': throughput_trend['current_average'],
                    'target_throughput': self.thresholds.min_throughput_ops_per_sec,
                    'suggested_concurrency': 5,
                    'suggested_async_pattern': 'gather'
                },
                estimated_effort_hours=6.0,
                priority_score=0.7
            ))
            
        # Analyze operation-specific issues
        if operation_stats.get('p95_duration_ms', 0) > operation_stats.get('average_duration_ms', 0) * 2:
            recommendations.append(OptimizationRecommendation(
                recommendation_id=f"p95_latency_opt_{adapter_name}_{platform}_{int(time.time())}",
                level=OptimizationLevel.MEDIUM,
                title="Address P95 Latency Outliers",
                description="P95 latency is significantly higher than average, indicating inconsistent performance. Investigate timeout handling and resource contention.",
                expected_improvement="30-50% P95 latency reduction",
                implementation_complexity="Medium",
                adapter_name=adapter_name,
                platform=platform,
                parameters={
                    'average_duration_ms': operation_stats.get('average_duration_ms', 0),
                    'p95_duration_ms': operation_stats.get('p95_duration_ms', 0),
                    'suggested_timeout_ms': operation_stats.get('average_duration_ms', 0) * 3
                },
                estimated_effort_hours=3.0,
                priority_score=0.6
            ))
            
        # Store recommendations
        self._recommendations.extend(recommendations)
        
        return recommendations
        
    def get_performance_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive performance dashboard data"""
        current_time = datetime.utcnow()
        
        # Get adapter summary
        adapters_summary = defaultdict(lambda: {
            'total_operations': 0,
            'avg_latency_ms': 0,
            'error_rate': 0,
            'last_activity': None
        })
        
        # Analyze recent metrics (last hour)
        recent_metrics = [
            m for m in self._metrics
            if m.timestamp >= current_time - timedelta(hours=1)
        ]
        
        for metric in recent_metrics:
            adapter_key = f"{metric.adapter_name}:{metric.platform}"
            summary = adapters_summary[adapter_key]
            
            if metric.metric_type == MetricType.LATENCY:
                if summary['total_operations'] == 0:
                    summary['avg_latency_ms'] = metric.value
                else:
                    summary['avg_latency_ms'] = (summary['avg_latency_ms'] + metric.value) / 2
                    
            elif metric.metric_type == MetricType.ERROR_RATE:
                summary['error_rate'] = metric.value
                
            summary['total_operations'] += 1
            summary['last_activity'] = metric.timestamp
            
        # Get top recommendations
        top_recommendations = sorted(
            self._recommendations,
            key=lambda r: r.priority_score,
            reverse=True
        )[:5]
        
        # Calculate overall health score
        health_issues = 0
        total_adapters = len(adapters_summary)
        
        for summary in adapters_summary.values():
            if summary['avg_latency_ms'] > self.thresholds.max_latency_ms:
                health_issues += 1
            if summary['error_rate'] > self.thresholds.max_error_rate_percent:
                health_issues += 1
                
        health_score = max(0, 100 - (health_issues / max(total_adapters, 1)) * 100) if total_adapters > 0 else 100
        
        return {
            'timestamp': current_time.isoformat(),
            'health_score': health_score,
            'total_adapters': total_adapters,
            'total_metrics': len(self._metrics),
            'adapters_summary': dict(adapters_summary),
            'top_recommendations': [
                {
                    'title': r.title,
                    'level': r.level.value,
                    'adapter': f"{r.adapter_name}:{r.platform}",
                    'expected_improvement': r.expected_improvement,
                    'priority_score': r.priority_score
                }
                for r in top_recommendations
            ],
            'recent_activity': len(recent_metrics),
            'active_recommendations': len(self._recommendations)
        }
        
    def export_performance_report(
        self,
        adapter_name: Optional[str] = None,
        platform: Optional[str] = None,
        hours: int = 24
    ) -> Dict[str, Any]:
        """Export comprehensive performance report"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Filter data
        filtered_metrics = [
            m for m in self._metrics
            if m.timestamp >= cutoff_time
        ]
        
        if adapter_name:
            filtered_metrics = [m for m in filtered_metrics if m.adapter_name == adapter_name]
        if platform:
            filtered_metrics = [m for m in filtered_metrics if m.platform == platform]
            
        # Generate report
        report = {
            'report_metadata': {
                'generated_at': datetime.utcnow().isoformat(),
                'time_period_hours': hours,
                'adapter_filter': adapter_name,
                'platform_filter': platform,
                'total_metrics': len(filtered_metrics)
            },
            'summary_statistics': self._calculate_summary_stats(filtered_metrics),
            'performance_trends': {},
            'optimization_opportunities': [],
            'threshold_violations': [],
            'recommendations': []
        }
        
        # Get unique adapter/platform combinations
        adapter_platforms = set()
        for metric in filtered_metrics:
            adapter_platforms.add((metric.adapter_name, metric.platform))
            
        # Analyze each adapter/platform combination
        for adapter, platform in adapter_platforms:
            trends = asyncio.run(self.analyze_performance_trends(adapter, platform, hours))
            recommendations = asyncio.run(self.generate_optimization_recommendations(adapter, platform))
            
            report['performance_trends'][f"{adapter}:{platform}"] = trends
            report['recommendations'].extend([
                {
                    'adapter': adapter,
                    'platform': platform,
                    'title': r.title,
                    'level': r.level.value,
                    'description': r.description,
                    'expected_improvement': r.expected_improvement,
                    'estimated_effort_hours': r.estimated_effort_hours,
                    'priority_score': r.priority_score
                }
                for r in recommendations
            ])
            
        return report
        
    def _calculate_summary_stats(self, metrics: List[PerformanceMetric]) -> Dict[str, Any]:
        """Calculate summary statistics for metrics"""
        if not metrics:
            return {}
            
        stats_by_type = defaultdict(list)
        for metric in metrics:
            stats_by_type[metric.metric_type.value].append(metric.value)
            
        summary = {}
        for metric_type, values in stats_by_type.items():
            if values:
                summary[metric_type] = {
                    'count': len(values),
                    'average': statistics.mean(values),
                    'median': statistics.median(values),
                    'min': min(values),
                    'max': max(values),
                    'std_dev': statistics.stdev(values) if len(values) > 1 else 0
                }
                
        return summary


# Decorator for automatic performance monitoring
def monitor_performance(
    operation_type: str = "unknown",
    record_metrics: bool = True
):
    """
    Decorator to automatically monitor adapter operation performance
    
    Args:
        operation_type: Type of operation being monitored
        record_metrics: Whether to record detailed metrics
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Get adapter instance and performance monitor
            adapter_instance = args[0] if args else None
            
            if not (adapter_instance and hasattr(adapter_instance, '_performance_monitor')):
                # No performance monitor available, execute normally
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
                    
            monitor = adapter_instance._performance_monitor
            adapter_name = getattr(adapter_instance, '_adapter_name', 'unknown')
            platform = getattr(adapter_instance, '_platform', 'unknown')
            
            # Generate operation ID
            operation_id = f"{adapter_name}_{platform}_{operation_type}_{int(time.time() * 1000)}"
            
            # Profile the operation
            return await monitor.profiler.profile_operation(
                operation_id,
                adapter_name,
                platform,
                operation_type,
                func,
                *args,
                **kwargs
            )
            
        return wrapper
    return decorator