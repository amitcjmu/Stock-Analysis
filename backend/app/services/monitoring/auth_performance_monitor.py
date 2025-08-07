"""
Auth Performance Monitor

Specialized monitoring system for authentication performance optimization.
Tracks authentication flow performance, login times, session validation,
context switching, and provides real-time analysis of auth operations.

Key Features:
- Login flow performance tracking (200-500ms target from 2-4 seconds)
- Session validation optimization monitoring (cached vs non-cached)
- Context switching performance (100-300ms target from 1-2 seconds)
- Authentication flow bottleneck identification
- Real-time performance alerts and threshold monitoring
- Integration with cache performance monitoring
- Authentication user experience optimization metrics

Performance Targets (from design document):
- Login page load: 200-500ms (from 2-4 seconds) - 80-90% improvement
- Authentication flow: 300-600ms (from 1.5-3 seconds) - 75-85% improvement
- Context switching: 100-300ms (from 1-2 seconds) - 85-90% improvement
"""

import asyncio
import time
import uuid
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from app.core.logging import get_logger
from app.services.monitoring.performance_metrics_collector import (
    get_metrics_collector,
)

logger = get_logger(__name__)


class AuthOperation(str, Enum):
    """Authentication operation types"""

    LOGIN = "login"
    LOGOUT = "logout"
    SESSION_VALIDATION = "session_validation"
    TOKEN_REFRESH = "token_refresh"
    CONTEXT_SWITCH = "context_switch"
    PASSWORD_RESET = "password_reset"
    PROFILE_UPDATE = "profile_update"


class AuthStatus(str, Enum):
    """Authentication operation status"""

    SUCCESS = "success"
    FAILURE = "failure"
    ERROR = "error"
    TIMEOUT = "timeout"
    CACHED = "cached"


class PerformanceThreshold(str, Enum):
    """Performance threshold levels"""

    EXCELLENT = "excellent"  # < 200ms
    GOOD = "good"  # 200-500ms
    ACCEPTABLE = "acceptable"  # 500ms-1s
    SLOW = "slow"  # 1-2s
    CRITICAL = "critical"  # > 2s


@dataclass
class AuthPerformanceEvent:
    """Individual auth performance event record"""

    operation_id: str
    operation_type: AuthOperation
    user_id: Optional[str]
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    status: AuthStatus = AuthStatus.SUCCESS
    cache_hit: bool = False
    context_data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.end_time and not self.duration:
            self.duration = self.end_time - self.start_time

    @property
    def duration_ms(self) -> float:
        """Get duration in milliseconds"""
        return (self.duration or 0) * 1000

    @property
    def performance_grade(self) -> PerformanceThreshold:
        """Calculate performance threshold grade"""
        if not self.duration:
            return PerformanceThreshold.CRITICAL

        duration_ms = self.duration_ms

        if duration_ms < 200:
            return PerformanceThreshold.EXCELLENT
        elif duration_ms < 500:
            return PerformanceThreshold.GOOD
        elif duration_ms < 1000:
            return PerformanceThreshold.ACCEPTABLE
        elif duration_ms < 2000:
            return PerformanceThreshold.SLOW
        else:
            return PerformanceThreshold.CRITICAL


@dataclass
class AuthPerformanceStats:
    """Authentication performance statistics"""

    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    cached_operations: int = 0
    average_duration_ms: float = 0.0
    p50_duration_ms: float = 0.0
    p95_duration_ms: float = 0.0
    p99_duration_ms: float = 0.0
    cache_hit_rate: float = 0.0
    error_rate: float = 0.0
    threshold_distribution: Dict[PerformanceThreshold, int] = field(
        default_factory=dict
    )

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total_operations == 0:
            return 0.0
        return (self.successful_operations / self.total_operations) * 100


class AuthPerformanceMonitor:
    """
    Authentication Performance Monitor

    Provides comprehensive monitoring and analysis of authentication operations
    with focus on performance optimization and user experience improvement.
    """

    # Performance thresholds (in milliseconds)
    THRESHOLDS = {
        AuthOperation.LOGIN: {
            PerformanceThreshold.EXCELLENT: 200,
            PerformanceThreshold.GOOD: 500,
            PerformanceThreshold.ACCEPTABLE: 1000,
            PerformanceThreshold.SLOW: 2000,
        },
        AuthOperation.SESSION_VALIDATION: {
            PerformanceThreshold.EXCELLENT: 50,
            PerformanceThreshold.GOOD: 150,
            PerformanceThreshold.ACCEPTABLE: 300,
            PerformanceThreshold.SLOW: 500,
        },
        AuthOperation.CONTEXT_SWITCH: {
            PerformanceThreshold.EXCELLENT: 100,
            PerformanceThreshold.GOOD: 300,
            PerformanceThreshold.ACCEPTABLE: 500,
            PerformanceThreshold.SLOW: 1000,
        },
        AuthOperation.TOKEN_REFRESH: {
            PerformanceThreshold.EXCELLENT: 100,
            PerformanceThreshold.GOOD: 200,
            PerformanceThreshold.ACCEPTABLE: 500,
            PerformanceThreshold.SLOW: 1000,
        },
    }

    def __init__(self, max_events: int = 10000, analysis_window: int = 3600):
        self.max_events = max_events
        self.analysis_window = analysis_window  # seconds

        # Event storage
        self.events: deque[AuthPerformanceEvent] = deque(maxlen=max_events)
        self.active_operations: Dict[str, AuthPerformanceEvent] = {}

        # Performance tracking
        self.metrics_collector = get_metrics_collector()

        # Statistics cache
        self._stats_cache: Dict[str, Tuple[AuthPerformanceStats, float]] = {}
        self._cache_ttl = 60  # seconds

        # Background analysis
        self._analysis_executor = ThreadPoolExecutor(
            max_workers=2, thread_name_prefix="auth-perf"
        )

        # Alert thresholds
        self.alert_thresholds = {
            "login_p95_ms": 1000,  # Alert if p95 login time > 1000ms
            "session_validation_p95_ms": 500,  # Alert if p95 session validation > 500ms
            "context_switch_p95_ms": 500,  # Alert if p95 context switch > 500ms
            "error_rate_percent": 5.0,  # Alert if error rate > 5%
            "cache_hit_rate_percent": 80.0,  # Alert if cache hit rate < 80%
        }

        logger.info("AuthPerformanceMonitor initialized with max_events=%d", max_events)

    def start_operation(
        self,
        operation_type: AuthOperation,
        user_id: Optional[str] = None,
        context_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Start tracking an authentication operation"""
        operation_id = str(uuid.uuid4())

        event = AuthPerformanceEvent(
            operation_id=operation_id,
            operation_type=operation_type,
            user_id=user_id,
            start_time=time.time(),
            context_data=context_data or {},
            metadata={
                "client_ip": context_data.get("client_ip") if context_data else None,
                "user_agent": context_data.get("user_agent") if context_data else None,
            },
        )

        self.active_operations[operation_id] = event

        logger.debug(
            "Started tracking %s operation: %s", operation_type.value, operation_id
        )
        return operation_id

    def end_operation(
        self,
        operation_id: str,
        status: AuthStatus = AuthStatus.SUCCESS,
        cache_hit: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """End tracking an authentication operation"""
        if operation_id not in self.active_operations:
            logger.warning("Operation %s not found in active operations", operation_id)
            return

        event = self.active_operations.pop(operation_id)
        event.end_time = time.time()
        event.duration = event.end_time - event.start_time
        event.status = status
        event.cache_hit = cache_hit

        if metadata:
            event.metadata.update(metadata)

        # Add to events deque
        self.events.append(event)

        # Record metrics
        self._record_metrics(event)

        # Check performance thresholds
        self._check_performance_thresholds(event)

        logger.debug(
            "Completed %s operation %s in %.2fms (status: %s, cache_hit: %s)",
            event.operation_type.value,
            operation_id,
            event.duration_ms,
            status.value,
            cache_hit,
        )

    def _record_metrics(self, event: AuthPerformanceEvent) -> None:
        """Record event metrics using the metrics collector"""
        duration = event.duration or 0

        if event.operation_type == AuthOperation.LOGIN:
            self.metrics_collector.record_auth_login_duration(
                duration, event.status.value, "password"
            )
        elif event.operation_type == AuthOperation.SESSION_VALIDATION:
            self.metrics_collector.record_session_validation_duration(
                duration, event.status.value, event.cache_hit
            )
        elif event.operation_type == AuthOperation.CONTEXT_SWITCH:
            context_type = event.context_data.get("context_type", "client")
            self.metrics_collector.record_context_switch_duration(
                duration, context_type, event.status.value
            )

    def _check_performance_thresholds(self, event: AuthPerformanceEvent) -> None:
        """Check if event exceeds performance thresholds and log alerts"""
        if not event.duration:
            return

        operation_thresholds = self.THRESHOLDS.get(event.operation_type, {})
        duration_ms = event.duration_ms

        # Check against performance grade thresholds
        if duration_ms > operation_thresholds.get(
            PerformanceThreshold.SLOW, float("inf")
        ):
            logger.warning(
                "SLOW PERFORMANCE ALERT: %s operation %s took %.2fms (user: %s)",
                event.operation_type.value,
                event.operation_id,
                duration_ms,
                event.user_id,
            )
        elif duration_ms > operation_thresholds.get(
            PerformanceThreshold.ACCEPTABLE, float("inf")
        ):
            logger.info(
                "Performance notice: %s operation %s took %.2fms",
                event.operation_type.value,
                event.operation_id,
                duration_ms,
            )

    def get_operation_stats(
        self, operation_type: AuthOperation, window_seconds: Optional[int] = None
    ) -> AuthPerformanceStats:
        """Get performance statistics for specific operation type"""
        window_seconds = window_seconds or self.analysis_window
        cache_key = f"{operation_type.value}_{window_seconds}"

        # Check cache
        if cache_key in self._stats_cache:
            stats, timestamp = self._stats_cache[cache_key]
            if time.time() - timestamp < self._cache_ttl:
                return stats

        # Calculate fresh stats
        cutoff_time = time.time() - window_seconds
        relevant_events = [
            event
            for event in self.events
            if (
                event.operation_type == operation_type
                and event.start_time >= cutoff_time
                and event.duration is not None
            )
        ]

        if not relevant_events:
            return AuthPerformanceStats()

        # Calculate statistics
        durations_ms = [event.duration_ms for event in relevant_events]
        durations_ms.sort()

        stats = AuthPerformanceStats(
            total_operations=len(relevant_events),
            successful_operations=len(
                [e for e in relevant_events if e.status == AuthStatus.SUCCESS]
            ),
            failed_operations=len(
                [
                    e
                    for e in relevant_events
                    if e.status in [AuthStatus.FAILURE, AuthStatus.ERROR]
                ]
            ),
            cached_operations=len([e for e in relevant_events if e.cache_hit]),
            average_duration_ms=sum(durations_ms) / len(durations_ms),
            p50_duration_ms=self._calculate_percentile(durations_ms, 50),
            p95_duration_ms=self._calculate_percentile(durations_ms, 95),
            p99_duration_ms=self._calculate_percentile(durations_ms, 99),
            cache_hit_rate=(
                len([e for e in relevant_events if e.cache_hit]) / len(relevant_events)
            )
            * 100,
            error_rate=(
                len(
                    [
                        e
                        for e in relevant_events
                        if e.status in [AuthStatus.FAILURE, AuthStatus.ERROR]
                    ]
                )
                / len(relevant_events)
            )
            * 100,
        )

        # Calculate threshold distribution
        threshold_counts = defaultdict(int)
        for event in relevant_events:
            threshold_counts[event.performance_grade] += 1
        stats.threshold_distribution = dict(threshold_counts)

        # Cache results
        self._stats_cache[cache_key] = (stats, time.time())

        return stats

    def _calculate_percentile(
        self, sorted_values: List[float], percentile: float
    ) -> float:
        """Calculate percentile from sorted values"""
        if not sorted_values:
            return 0.0

        index = (percentile / 100.0) * (len(sorted_values) - 1)
        lower_index = int(index)
        upper_index = min(lower_index + 1, len(sorted_values) - 1)

        if lower_index == upper_index:
            return sorted_values[lower_index]

        # Linear interpolation
        weight = index - lower_index
        return (
            sorted_values[lower_index] * (1 - weight)
            + sorted_values[upper_index] * weight
        )

    def get_comprehensive_stats(
        self, window_seconds: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get comprehensive authentication performance statistics"""
        window_seconds = window_seconds or self.analysis_window

        stats = {
            "timestamp": datetime.utcnow().isoformat(),
            "analysis_window_seconds": window_seconds,
            "operations": {},
            "overall_summary": {},
            "performance_alerts": [],
        }

        # Get stats for each operation type
        total_operations = 0
        total_successful = 0
        total_cached = 0

        for operation_type in AuthOperation:
            op_stats = self.get_operation_stats(operation_type, window_seconds)
            stats["operations"][operation_type.value] = {
                "total_operations": op_stats.total_operations,
                "success_rate": op_stats.success_rate,
                "error_rate": op_stats.error_rate,
                "cache_hit_rate": op_stats.cache_hit_rate,
                "average_duration_ms": round(op_stats.average_duration_ms, 2),
                "p50_duration_ms": round(op_stats.p50_duration_ms, 2),
                "p95_duration_ms": round(op_stats.p95_duration_ms, 2),
                "p99_duration_ms": round(op_stats.p99_duration_ms, 2),
                "threshold_distribution": {
                    threshold.value: count
                    for threshold, count in op_stats.threshold_distribution.items()
                },
            }

            total_operations += op_stats.total_operations
            total_successful += op_stats.successful_operations
            total_cached += op_stats.cached_operations

        # Overall summary
        stats["overall_summary"] = {
            "total_operations": total_operations,
            "overall_success_rate": (
                (total_successful / total_operations * 100)
                if total_operations > 0
                else 0
            ),
            "overall_cache_hit_rate": (
                (total_cached / total_operations * 100) if total_operations > 0 else 0
            ),
            "active_operations": len(self.active_operations),
        }

        # Performance alerts
        stats["performance_alerts"] = self._generate_performance_alerts(
            stats["operations"]
        )

        return stats

    def _generate_performance_alerts(
        self, operations_stats: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate performance alerts based on thresholds"""
        alerts = []

        # Check login performance
        login_stats = operations_stats.get("login", {})
        if (
            login_stats.get("p95_duration_ms", 0)
            > self.alert_thresholds["login_p95_ms"]
        ):
            alerts.append(
                {
                    "type": "performance_degradation",
                    "operation": "login",
                    "metric": "p95_duration_ms",
                    "value": login_stats["p95_duration_ms"],
                    "threshold": self.alert_thresholds["login_p95_ms"],
                    "severity": "high",
                    "message": f"Login P95 response time ({login_stats['p95_duration_ms']}ms) exceeds threshold",
                }
            )

        # Check session validation performance
        session_stats = operations_stats.get("session_validation", {})
        if (
            session_stats.get("p95_duration_ms", 0)
            > self.alert_thresholds["session_validation_p95_ms"]
        ):
            alerts.append(
                {
                    "type": "performance_degradation",
                    "operation": "session_validation",
                    "metric": "p95_duration_ms",
                    "value": session_stats["p95_duration_ms"],
                    "threshold": self.alert_thresholds["session_validation_p95_ms"],
                    "severity": "medium",
                    "message": (
                        f"Session validation P95 response time "
                        f"({session_stats['p95_duration_ms']}ms) exceeds threshold"
                    ),
                }
            )

        # Check context switching performance
        context_stats = operations_stats.get("context_switch", {})
        if (
            context_stats.get("p95_duration_ms", 0)
            > self.alert_thresholds["context_switch_p95_ms"]
        ):
            alerts.append(
                {
                    "type": "performance_degradation",
                    "operation": "context_switch",
                    "metric": "p95_duration_ms",
                    "value": context_stats["p95_duration_ms"],
                    "threshold": self.alert_thresholds["context_switch_p95_ms"],
                    "severity": "medium",
                    "message": (
                        f"Context switch P95 response time "
                        f"({context_stats['p95_duration_ms']}ms) exceeds threshold"
                    ),
                }
            )

        # Check error rates
        for operation, stats in operations_stats.items():
            if stats.get("error_rate", 0) > self.alert_thresholds["error_rate_percent"]:
                alerts.append(
                    {
                        "type": "high_error_rate",
                        "operation": operation,
                        "metric": "error_rate",
                        "value": stats["error_rate"],
                        "threshold": self.alert_thresholds["error_rate_percent"],
                        "severity": "high",
                        "message": f"{operation} error rate ({stats['error_rate']:.1f}%) exceeds threshold",
                    }
                )

        # Check cache hit rates
        for operation, stats in operations_stats.items():
            if (
                stats.get("cache_hit_rate", 100)
                < self.alert_thresholds["cache_hit_rate_percent"]
            ):
                alerts.append(
                    {
                        "type": "low_cache_performance",
                        "operation": operation,
                        "metric": "cache_hit_rate",
                        "value": stats["cache_hit_rate"],
                        "threshold": self.alert_thresholds["cache_hit_rate_percent"],
                        "severity": "medium",
                        "message": f"{operation} cache hit rate ({stats['cache_hit_rate']:.1f}%) below threshold",
                    }
                )

        return alerts

    def get_performance_trends(
        self, operation_type: AuthOperation, hours: int = 24
    ) -> Dict[str, Any]:
        """Get performance trends over time for an operation type"""
        end_time = time.time()
        start_time = end_time - (hours * 3600)

        # Group events by hour
        hourly_stats = defaultdict(list)

        for event in self.events:
            if (
                event.operation_type == operation_type
                and event.start_time >= start_time
                and event.duration is not None
            ):

                hour_bucket = int((event.start_time - start_time) // 3600)
                hourly_stats[hour_bucket].append(event)

        # Calculate stats for each hour
        trends = {
            "operation_type": operation_type.value,
            "hours_analyzed": hours,
            "hourly_data": [],
        }

        for hour in range(hours):
            hour_events = hourly_stats.get(hour, [])

            if hour_events:
                durations_ms = [event.duration_ms for event in hour_events]
                durations_ms.sort()

                hour_data = {
                    "hour": hour,
                    "timestamp": datetime.fromtimestamp(
                        start_time + hour * 3600
                    ).isoformat(),
                    "total_operations": len(hour_events),
                    "success_rate": (
                        len([e for e in hour_events if e.status == AuthStatus.SUCCESS])
                        / len(hour_events)
                    )
                    * 100,
                    "cache_hit_rate": (
                        len([e for e in hour_events if e.cache_hit]) / len(hour_events)
                    )
                    * 100,
                    "average_duration_ms": sum(durations_ms) / len(durations_ms),
                    "p95_duration_ms": self._calculate_percentile(durations_ms, 95),
                }
            else:
                hour_data = {
                    "hour": hour,
                    "timestamp": datetime.fromtimestamp(
                        start_time + hour * 3600
                    ).isoformat(),
                    "total_operations": 0,
                    "success_rate": 0,
                    "cache_hit_rate": 0,
                    "average_duration_ms": 0,
                    "p95_duration_ms": 0,
                }

            trends["hourly_data"].append(hour_data)

        return trends

    def get_user_performance_analysis(
        self, user_id: str, window_seconds: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get performance analysis for a specific user"""
        window_seconds = window_seconds or self.analysis_window
        cutoff_time = time.time() - window_seconds

        user_events = [
            event
            for event in self.events
            if (
                event.user_id == user_id
                and event.start_time >= cutoff_time
                and event.duration is not None
            )
        ]

        if not user_events:
            return {
                "user_id": user_id,
                "analysis_window_seconds": window_seconds,
                "message": "No performance data available for user",
            }

        # Group by operation type
        operations_analysis = {}
        for operation_type in AuthOperation:
            op_events = [e for e in user_events if e.operation_type == operation_type]

            if op_events:
                durations_ms = [e.duration_ms for e in op_events]
                durations_ms.sort()

                operations_analysis[operation_type.value] = {
                    "total_operations": len(op_events),
                    "success_rate": (
                        len([e for e in op_events if e.status == AuthStatus.SUCCESS])
                        / len(op_events)
                    )
                    * 100,
                    "cache_hit_rate": (
                        len([e for e in op_events if e.cache_hit]) / len(op_events)
                    )
                    * 100,
                    "average_duration_ms": sum(durations_ms) / len(durations_ms),
                    "min_duration_ms": min(durations_ms),
                    "max_duration_ms": max(durations_ms),
                    "p95_duration_ms": self._calculate_percentile(durations_ms, 95),
                }

        return {
            "user_id": user_id,
            "analysis_window_seconds": window_seconds,
            "total_operations": len(user_events),
            "operations_analysis": operations_analysis,
        }

    def cleanup_old_events(self, max_age_hours: int = 24) -> int:
        """Clean up old events and return count of removed events"""
        cutoff_time = time.time() - (max_age_hours * 3600)
        initial_count = len(self.events)

        # Filter out old events
        self.events = deque(
            (event for event in self.events if event.start_time >= cutoff_time),
            maxlen=self.max_events,
        )

        removed_count = initial_count - len(self.events)

        # Clear stats cache to force recalculation
        self._stats_cache.clear()

        if removed_count > 0:
            logger.info("Cleaned up %d old performance events", removed_count)

        return removed_count

    def get_monitor_health(self) -> Dict[str, Any]:
        """Get monitor health status"""
        return {
            "status": "healthy",
            "total_events": len(self.events),
            "active_operations": len(self.active_operations),
            "cache_entries": len(self._stats_cache),
            "memory_usage": {
                "events_capacity": self.max_events,
                "events_used": len(self.events),
                "utilization_percent": len(self.events) / self.max_events * 100,
            },
        }


# Global singleton instance
_auth_performance_monitor = None


def get_auth_performance_monitor() -> AuthPerformanceMonitor:
    """Get singleton auth performance monitor instance"""
    global _auth_performance_monitor
    if _auth_performance_monitor is None:
        _auth_performance_monitor = AuthPerformanceMonitor()
    return _auth_performance_monitor


def track_auth_operation(operation_type: AuthOperation, user_id: Optional[str] = None):
    """Context manager for tracking authentication operations"""

    class AuthOperationTracker:
        def __init__(self, op_type: AuthOperation, uid: Optional[str]):
            self.operation_type = op_type
            self.user_id = uid
            self.operation_id = None
            self.monitor = get_auth_performance_monitor()

        def __enter__(self):
            self.operation_id = self.monitor.start_operation(
                self.operation_type, self.user_id
            )
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            if self.operation_id:
                status = AuthStatus.SUCCESS if exc_type is None else AuthStatus.ERROR
                self.monitor.end_operation(self.operation_id, status)

        async def __aenter__(self):
            self.operation_id = self.monitor.start_operation(
                self.operation_type, self.user_id
            )
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            if self.operation_id:
                status = AuthStatus.SUCCESS if exc_type is None else AuthStatus.ERROR
                self.monitor.end_operation(self.operation_id, status)

    return AuthOperationTracker(operation_type, user_id)


def auth_performance_decorator(operation_type: AuthOperation):
    """Decorator for automatic auth performance tracking"""

    def decorator(func: Callable) -> Callable:
        def sync_wrapper(*args, **kwargs):
            monitor = get_auth_performance_monitor()
            operation_id = monitor.start_operation(operation_type)

            try:
                result = func(*args, **kwargs)
                monitor.end_operation(operation_id, AuthStatus.SUCCESS)
                return result
            except Exception:
                monitor.end_operation(operation_id, AuthStatus.ERROR)
                raise

        async def async_wrapper(*args, **kwargs):
            monitor = get_auth_performance_monitor()
            operation_id = monitor.start_operation(operation_type)

            try:
                result = await func(*args, **kwargs)
                monitor.end_operation(operation_id, AuthStatus.SUCCESS)
                return result
            except Exception:
                monitor.end_operation(operation_id, AuthStatus.ERROR)
                raise

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator
