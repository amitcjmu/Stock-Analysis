"""
System Health Dashboard

Real-time monitoring dashboard for comprehensive system health and performance
visualization. Provides unified view of authentication performance, cache efficiency,
system resources, and user experience metrics.

Key Features:
- Real-time performance dashboard with key indicators
- Authentication flow health monitoring
- Cache performance visualization and alerts
- System resource utilization tracking
- User experience optimization metrics
- Performance threshold monitoring and alerting
- Historical trend analysis and reporting
- Integration with all monitoring components

Dashboard Sections:
1. Performance Summary - Overall system health score and key metrics
2. Authentication Health - Login times, session validation, context switching
3. Cache Performance - Hit rates, response times, utilization across cache layers
4. System Resources - CPU, memory, network I/O, active connections
5. User Experience - Performance impact on user workflows
6. Alerts & Recommendations - Active performance issues and optimization suggestions
"""

import asyncio
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List
from concurrent.futures import ThreadPoolExecutor
import psutil
import json

from app.core.logging import get_logger
from app.services.monitoring.performance_metrics_collector import get_metrics_collector
from app.services.monitoring.auth_performance_monitor import (
    get_auth_performance_monitor,
)
from app.services.monitoring.cache_performance_monitor import (
    get_cache_performance_monitor,
)

logger = get_logger(__name__)


class HealthStatus(str, Enum):
    """System health status levels"""

    EXCELLENT = "excellent"  # 90-100% performance
    GOOD = "good"  # 80-89% performance
    WARNING = "warning"  # 70-79% performance
    CRITICAL = "critical"  # < 70% performance
    UNKNOWN = "unknown"  # Unable to determine


class AlertSeverity(str, Enum):
    """Alert severity levels"""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class HealthScore:
    """Health score calculation for system components"""

    component: str
    score: float  # 0-100
    status: HealthStatus
    factors: Dict[str, float] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)

    @classmethod
    def calculate_status(cls, score: float) -> HealthStatus:
        """Calculate health status from score"""
        if score >= 90:
            return HealthStatus.EXCELLENT
        elif score >= 80:
            return HealthStatus.GOOD
        elif score >= 70:
            return HealthStatus.WARNING
        elif score >= 0:
            return HealthStatus.CRITICAL
        else:
            return HealthStatus.UNKNOWN


@dataclass
class SystemAlert:
    """System performance alert"""

    id: str
    severity: AlertSeverity
    component: str
    metric: str
    current_value: float
    threshold: float
    message: str
    timestamp: datetime
    acknowledged: bool = False
    resolved: bool = False


class SystemHealthDashboard:
    """
    System Health Dashboard

    Provides comprehensive real-time monitoring and visualization of system
    health across all performance components.
    """

    def __init__(self, update_interval: int = 30):
        self.update_interval = update_interval  # seconds

        # Component integrations
        self.metrics_collector = get_metrics_collector()
        self.auth_monitor = get_auth_performance_monitor()
        self.cache_monitor = get_cache_performance_monitor()

        # Dashboard state
        self.dashboard_data: Dict[str, Any] = {}
        self.active_alerts: Dict[str, SystemAlert] = {}
        self.alert_history: deque[SystemAlert] = deque(maxlen=1000)

        # Performance targets (from design document)
        self.performance_targets = {
            "login_target_ms": 500,  # Target: 200-500ms
            "auth_flow_target_ms": 600,  # Target: 300-600ms
            "context_switch_target_ms": 300,  # Target: 100-300ms
            "cache_hit_rate_target": 85.0,  # Target: >80%
            "error_rate_target": 2.0,  # Target: <5%
            "cpu_usage_target": 70.0,  # Target: <80%
            "memory_usage_target": 80.0,  # Target: <85%
        }

        # Health score weights
        self.health_score_weights = {
            "auth_performance": 0.35,
            "cache_performance": 0.25,
            "system_resources": 0.20,
            "error_rates": 0.20,
        }

        # Background dashboard updates
        self._dashboard_executor = ThreadPoolExecutor(
            max_workers=2, thread_name_prefix="dashboard"
        )
        self._last_update = time.time()
        self._update_lock = asyncio.Lock()

        logger.info(
            "SystemHealthDashboard initialized with update_interval=%ds",
            update_interval,
        )

        # Start background updates
        self._start_background_updates()

    def _start_background_updates(self) -> None:
        """Start background dashboard updates"""

        def background_updater():
            while True:
                try:
                    if time.time() - self._last_update > self.update_interval:
                        asyncio.create_task(self._update_dashboard_data())
                        self._last_update = time.time()

                    time.sleep(10)  # Check every 10 seconds
                except Exception as e:
                    logger.error("Error in background dashboard updates: %s", e)
                    time.sleep(30)  # Wait longer on error

        self._dashboard_executor.submit(background_updater)

    async def _update_dashboard_data(self) -> None:
        """Update dashboard data from all monitoring components"""
        async with self._update_lock:
            try:
                logger.debug("Updating dashboard data...")

                # Collect data from all components
                auth_stats = self.auth_monitor.get_comprehensive_stats()
                cache_stats = self.cache_monitor.get_comprehensive_stats()
                system_stats = await self._collect_system_stats()
                # metrics_summary = self.metrics_collector.get_performance_summary()  # Available if needed

                # Calculate health scores
                health_scores = self._calculate_health_scores(
                    auth_stats, cache_stats, system_stats
                )

                # Generate alerts
                alerts = self._process_alerts(auth_stats, cache_stats, system_stats)

                # Update dashboard data
                self.dashboard_data = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "overall_health": self._calculate_overall_health(health_scores),
                    "performance_summary": self._create_performance_summary(
                        auth_stats, cache_stats, system_stats
                    ),
                    "auth_health": self._create_auth_health_section(auth_stats),
                    "cache_health": self._create_cache_health_section(cache_stats),
                    "system_health": self._create_system_health_section(system_stats),
                    "user_experience": self._create_user_experience_section(
                        auth_stats, cache_stats
                    ),
                    "alerts": alerts,
                    "recommendations": self._generate_recommendations(
                        health_scores, auth_stats, cache_stats
                    ),
                    "health_scores": {
                        score.component: score.score for score in health_scores
                    },
                }

                logger.debug("Dashboard data updated successfully")

            except Exception as e:
                logger.error("Error updating dashboard data: %s", e)

    async def _collect_system_stats(self) -> Dict[str, Any]:
        """Collect system resource statistics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)

            # Memory usage
            memory = psutil.virtual_memory()

            # Disk I/O
            disk_io = psutil.disk_io_counters()

            # Network I/O
            network_io = psutil.net_io_counters()

            # Process count
            process_count = len(psutil.pids())

            return {
                "cpu": {"usage_percent": cpu_percent, "core_count": psutil.cpu_count()},
                "memory": {
                    "total_bytes": memory.total,
                    "used_bytes": memory.used,
                    "available_bytes": memory.available,
                    "usage_percent": memory.percent,
                },
                "disk_io": {
                    "read_bytes": disk_io.read_bytes if disk_io else 0,
                    "write_bytes": disk_io.write_bytes if disk_io else 0,
                    "read_count": disk_io.read_count if disk_io else 0,
                    "write_count": disk_io.write_count if disk_io else 0,
                },
                "network_io": {
                    "bytes_sent": network_io.bytes_sent if network_io else 0,
                    "bytes_recv": network_io.bytes_recv if network_io else 0,
                    "packets_sent": network_io.packets_sent if network_io else 0,
                    "packets_recv": network_io.packets_recv if network_io else 0,
                },
                "processes": {"count": process_count},
            }
        except Exception as e:
            logger.error("Error collecting system stats: %s", e)
            return {"error": "Failed to collect system statistics"}

    def _calculate_health_scores(
        self,
        auth_stats: Dict[str, Any],
        cache_stats: Dict[str, Any],
        system_stats: Dict[str, Any],
    ) -> List[HealthScore]:
        """Calculate health scores for all system components"""
        health_scores = []

        # Authentication performance health score
        auth_score = self._calculate_auth_health_score(auth_stats)
        health_scores.append(auth_score)

        # Cache performance health score
        cache_score = self._calculate_cache_health_score(cache_stats)
        health_scores.append(cache_score)

        # System resources health score
        system_score = self._calculate_system_health_score(system_stats)
        health_scores.append(system_score)

        return health_scores

    def _calculate_auth_health_score(self, auth_stats: Dict[str, Any]) -> HealthScore:
        """Calculate authentication performance health score"""
        factors = {}
        score = 100.0
        recommendations = []

        # Check login performance
        login_stats = auth_stats.get("operations", {}).get("login", {})
        if login_stats:
            p95_login = login_stats.get("p95_duration_ms", 0)
            target_login = self.performance_targets["login_target_ms"]

            if p95_login > 0:
                login_score = max(0, 100 - (p95_login / target_login - 1) * 50)
                factors["login_performance"] = login_score
                score = min(score, login_score)

                if p95_login > target_login:
                    recommendations.append(
                        f"Login P95 ({p95_login:.0f}ms) exceeds target ({target_login}ms)"
                    )

        # Check session validation performance
        session_stats = auth_stats.get("operations", {}).get("session_validation", {})
        if session_stats:
            p95_session = session_stats.get("p95_duration_ms", 0)
            if p95_session > 200:  # Target < 200ms for session validation
                session_score = max(0, 100 - (p95_session / 200 - 1) * 30)
                factors["session_validation"] = session_score
                score = min(score, session_score)

                if p95_session > 200:
                    recommendations.append(
                        f"Session validation P95 ({p95_session:.0f}ms) exceeds 200ms target"
                    )

        # Check context switching performance
        context_stats = auth_stats.get("operations", {}).get("context_switch", {})
        if context_stats:
            p95_context = context_stats.get("p95_duration_ms", 0)
            target_context = self.performance_targets["context_switch_target_ms"]

            if p95_context > 0:
                context_score = max(0, 100 - (p95_context / target_context - 1) * 40)
                factors["context_switching"] = context_score
                score = min(score, context_score)

                if p95_context > target_context:
                    recommendations.append(
                        f"Context switch P95 ({p95_context:.0f}ms) exceeds target ({target_context}ms)"
                    )

        # Check error rates
        overall_summary = auth_stats.get("overall_summary", {})
        success_rate = overall_summary.get("overall_success_rate", 100)
        if success_rate < 95:  # Target > 95% success rate
            error_score = success_rate
            factors["error_rate"] = error_score
            score = min(score, error_score)
            recommendations.append(
                f"Auth success rate ({success_rate:.1f}%) below 95% target"
            )

        return HealthScore(
            component="auth_performance",
            score=max(0, score),
            status=HealthScore.calculate_status(score),
            factors=factors,
            recommendations=recommendations,
        )

    def _calculate_cache_health_score(self, cache_stats: Dict[str, Any]) -> HealthScore:
        """Calculate cache performance health score"""
        factors = {}
        score = 100.0
        recommendations = []

        # Check overall hit rate
        overall_summary = cache_stats.get("overall_summary", {})
        hit_rate = overall_summary.get("overall_hit_rate", 0)
        target_hit_rate = self.performance_targets["cache_hit_rate_target"]

        if hit_rate > 0:
            hit_rate_score = min(100, (hit_rate / target_hit_rate) * 100)
            factors["hit_rate"] = hit_rate_score
            score = min(score, hit_rate_score)

            if hit_rate < target_hit_rate:
                recommendations.append(
                    f"Cache hit rate ({hit_rate:.1f}%) below target ({target_hit_rate}%)"
                )

        # Check cache layer performance
        redis_stats = cache_stats.get("cache_layers", {}).get("redis", {})
        if redis_stats:
            redis_response_time = redis_stats.get("average_response_time_ms", 0)
            if redis_response_time > 50:  # Target < 50ms for Redis
                redis_score = max(0, 100 - (redis_response_time / 50 - 1) * 30)
                factors["redis_performance"] = redis_score
                score = min(score, redis_score)

                if redis_response_time > 100:
                    recommendations.append(
                        f"Redis response time ({redis_response_time:.1f}ms) exceeds 100ms"
                    )

        # Check error rates
        error_rate = overall_summary.get("overall_error_rate", 0)
        target_error_rate = self.performance_targets["error_rate_target"]

        if error_rate > target_error_rate:
            error_score = max(0, 100 - (error_rate / target_error_rate - 1) * 50)
            factors["error_rate"] = error_score
            score = min(score, error_score)
            recommendations.append(
                f"Cache error rate ({error_rate:.1f}%) exceeds target ({target_error_rate}%)"
            )

        return HealthScore(
            component="cache_performance",
            score=max(0, score),
            status=HealthScore.calculate_status(score),
            factors=factors,
            recommendations=recommendations,
        )

    def _calculate_system_health_score(
        self, system_stats: Dict[str, Any]
    ) -> HealthScore:
        """Calculate system resources health score"""
        factors = {}
        score = 100.0
        recommendations = []

        if "error" in system_stats:
            return HealthScore(
                component="system_resources",
                score=0,
                status=HealthStatus.UNKNOWN,
                recommendations=["Unable to collect system resource data"],
            )

        # Check CPU usage
        cpu_usage = system_stats.get("cpu", {}).get("usage_percent", 0)
        target_cpu = self.performance_targets["cpu_usage_target"]

        if cpu_usage > target_cpu:
            cpu_score = max(0, 100 - (cpu_usage / target_cpu - 1) * 50)
            factors["cpu_usage"] = cpu_score
            score = min(score, cpu_score)
            recommendations.append(
                f"CPU usage ({cpu_usage:.1f}%) exceeds target ({target_cpu}%)"
            )
        else:
            factors["cpu_usage"] = 100

        # Check memory usage
        memory_usage = system_stats.get("memory", {}).get("usage_percent", 0)
        target_memory = self.performance_targets["memory_usage_target"]

        if memory_usage > target_memory:
            memory_score = max(0, 100 - (memory_usage / target_memory - 1) * 50)
            factors["memory_usage"] = memory_score
            score = min(score, memory_score)
            recommendations.append(
                f"Memory usage ({memory_usage:.1f}%) exceeds target ({target_memory}%)"
            )
        else:
            factors["memory_usage"] = 100

        return HealthScore(
            component="system_resources",
            score=max(0, score),
            status=HealthScore.calculate_status(score),
            factors=factors,
            recommendations=recommendations,
        )

    def _calculate_overall_health(
        self, health_scores: List[HealthScore]
    ) -> Dict[str, Any]:
        """Calculate overall system health from component scores"""
        if not health_scores:
            return {
                "score": 0,
                "status": HealthStatus.UNKNOWN.value,
                "message": "No health data available",
            }

        # Calculate weighted average
        weighted_score = 0.0
        total_weight = 0.0

        for health_score in health_scores:
            weight = self.health_score_weights.get(health_score.component, 0.1)
            weighted_score += health_score.score * weight
            total_weight += weight

        overall_score = weighted_score / total_weight if total_weight > 0 else 0
        overall_status = HealthScore.calculate_status(overall_score)

        # Generate overall message
        critical_components = [
            hs.component for hs in health_scores if hs.status == HealthStatus.CRITICAL
        ]
        warning_components = [
            hs.component for hs in health_scores if hs.status == HealthStatus.WARNING
        ]

        if critical_components:
            message = f"Critical issues in: {', '.join(critical_components)}"
        elif warning_components:
            message = f"Performance warnings in: {', '.join(warning_components)}"
        elif overall_status == HealthStatus.EXCELLENT:
            message = "All systems performing excellently"
        elif overall_status == HealthStatus.GOOD:
            message = "All systems performing well"
        else:
            message = "System performance within acceptable ranges"

        return {
            "score": round(overall_score, 1),
            "status": overall_status.value,
            "message": message,
            "component_breakdown": {hs.component: hs.score for hs in health_scores},
        }

    def _create_performance_summary(
        self, auth_stats: Dict, cache_stats: Dict, system_stats: Dict
    ) -> Dict[str, Any]:
        """Create high-level performance summary"""
        return {
            "auth_performance": {
                "login_p95_ms": auth_stats.get("operations", {})
                .get("login", {})
                .get("p95_duration_ms", 0),
                "session_validation_p95_ms": auth_stats.get("operations", {})
                .get("session_validation", {})
                .get("p95_duration_ms", 0),
                "context_switch_p95_ms": auth_stats.get("operations", {})
                .get("context_switch", {})
                .get("p95_duration_ms", 0),
                "success_rate": auth_stats.get("overall_summary", {}).get(
                    "overall_success_rate", 0
                ),
            },
            "cache_performance": {
                "hit_rate": cache_stats.get("overall_summary", {}).get(
                    "overall_hit_rate", 0
                ),
                "redis_response_ms": cache_stats.get("cache_layers", {})
                .get("redis", {})
                .get("average_response_time_ms", 0),
                "error_rate": cache_stats.get("overall_summary", {}).get(
                    "overall_error_rate", 0
                ),
            },
            "system_resources": {
                "cpu_usage": system_stats.get("cpu", {}).get("usage_percent", 0),
                "memory_usage": system_stats.get("memory", {}).get("usage_percent", 0),
                "process_count": system_stats.get("processes", {}).get("count", 0),
            },
        }

    def _create_auth_health_section(self, auth_stats: Dict[str, Any]) -> Dict[str, Any]:
        """Create authentication health section"""
        return {
            "status": "healthy",  # Will be updated based on metrics
            "operations": auth_stats.get("operations", {}),
            "performance_targets": {
                "login_target_ms": self.performance_targets["login_target_ms"],
                "context_switch_target_ms": self.performance_targets[
                    "context_switch_target_ms"
                ],
            },
            "active_operations": auth_stats.get("overall_summary", {}).get(
                "active_operations", 0
            ),
        }

    def _create_cache_health_section(
        self, cache_stats: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create cache health section"""
        return {
            "status": "healthy",  # Will be updated based on metrics
            "overall_summary": cache_stats.get("overall_summary", {}),
            "cache_layers": cache_stats.get("cache_layers", {}),
            "key_patterns": cache_stats.get("key_patterns", {}),
            "utilization": cache_stats.get("utilization", {}),
        }

    def _create_system_health_section(
        self, system_stats: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create system health section"""
        return {
            "status": "healthy" if "error" not in system_stats else "error",
            "resources": system_stats,
            "thresholds": {
                "cpu_target": self.performance_targets["cpu_usage_target"],
                "memory_target": self.performance_targets["memory_usage_target"],
            },
        }

    def _create_user_experience_section(
        self, auth_stats: Dict, cache_stats: Dict
    ) -> Dict[str, Any]:
        """Create user experience metrics section"""
        # Calculate user experience impact scores
        login_p95 = (
            auth_stats.get("operations", {}).get("login", {}).get("p95_duration_ms", 0)
        )
        context_p95 = (
            auth_stats.get("operations", {})
            .get("context_switch", {})
            .get("p95_duration_ms", 0)
        )
        cache_hit_rate = cache_stats.get("overall_summary", {}).get(
            "overall_hit_rate", 0
        )

        # Performance improvement calculations (vs baseline from design doc)
        baseline_login_ms = 3000  # 2-4 second range baseline
        baseline_context_ms = 1500  # 1-2 second range baseline

        login_improvement = (
            ((baseline_login_ms - login_p95) / baseline_login_ms * 100)
            if login_p95 > 0
            else 0
        )
        context_improvement = (
            ((baseline_context_ms - context_p95) / baseline_context_ms * 100)
            if context_p95 > 0
            else 0
        )

        return {
            "performance_improvements": {
                "login_improvement_percent": max(0, login_improvement),
                "context_switch_improvement_percent": max(0, context_improvement),
                "target_improvements": {
                    "login": "80-90%",
                    "auth_flow": "75-85%",
                    "context_switch": "85-90%",
                },
            },
            "user_experience_score": self._calculate_user_experience_score(
                login_p95, context_p95, cache_hit_rate
            ),
            "bottleneck_analysis": self._identify_user_experience_bottlenecks(
                auth_stats, cache_stats
            ),
        }

    def _calculate_user_experience_score(
        self, login_p95: float, context_p95: float, cache_hit_rate: float
    ) -> float:
        """Calculate overall user experience score"""
        login_score = max(0, 100 - (login_p95 / 500 - 1) * 30) if login_p95 > 0 else 100
        context_score = (
            max(0, 100 - (context_p95 / 300 - 1) * 30) if context_p95 > 0 else 100
        )
        cache_score = min(100, cache_hit_rate)

        return login_score * 0.4 + context_score * 0.4 + cache_score * 0.2

    def _identify_user_experience_bottlenecks(
        self, auth_stats: Dict, cache_stats: Dict
    ) -> List[str]:
        """Identify bottlenecks affecting user experience"""
        bottlenecks = []

        # Check auth performance bottlenecks
        login_stats = auth_stats.get("operations", {}).get("login", {})
        if login_stats.get("p95_duration_ms", 0) > 1000:
            bottlenecks.append(
                "Login performance significantly impacts user experience"
            )

        # Check cache performance bottlenecks
        if cache_stats.get("overall_summary", {}).get("overall_hit_rate", 0) < 70:
            bottlenecks.append("Low cache hit rate causes frequent backend calls")

        # Check error rates
        auth_success_rate = auth_stats.get("overall_summary", {}).get(
            "overall_success_rate", 100
        )
        if auth_success_rate < 95:
            bottlenecks.append("Authentication failures disrupt user workflows")

        return bottlenecks

    def _process_alerts(
        self, auth_stats: Dict, cache_stats: Dict, system_stats: Dict
    ) -> List[Dict[str, Any]]:
        """Process and consolidate alerts from all monitoring components"""
        all_alerts = []

        # Get alerts from auth monitor
        auth_alerts = auth_stats.get("performance_alerts", [])
        for alert in auth_alerts:
            all_alerts.append(
                {
                    **alert,
                    "component": "authentication",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

        # Get alerts from cache monitor
        cache_alerts = cache_stats.get("performance_alerts", [])
        for alert in cache_alerts:
            all_alerts.append(
                {
                    **alert,
                    "component": "cache",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

        # Add system resource alerts
        if "error" not in system_stats:
            cpu_usage = system_stats.get("cpu", {}).get("usage_percent", 0)
            if cpu_usage > 90:
                all_alerts.append(
                    {
                        "type": "high_cpu_usage",
                        "severity": "critical" if cpu_usage > 95 else "warning",
                        "component": "system",
                        "metric": "cpu_usage_percent",
                        "value": cpu_usage,
                        "threshold": 90,
                        "message": f"CPU usage ({cpu_usage:.1f}%) is critically high",
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )

            memory_usage = system_stats.get("memory", {}).get("usage_percent", 0)
            if memory_usage > 85:
                all_alerts.append(
                    {
                        "type": "high_memory_usage",
                        "severity": "critical" if memory_usage > 90 else "warning",
                        "component": "system",
                        "metric": "memory_usage_percent",
                        "value": memory_usage,
                        "threshold": 85,
                        "message": f"Memory usage ({memory_usage:.1f}%) is critically high",
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )

        return all_alerts

    def _generate_recommendations(
        self, health_scores: List[HealthScore], auth_stats: Dict, cache_stats: Dict
    ) -> List[Dict[str, Any]]:
        """Generate optimization recommendations"""
        recommendations = []

        # Add recommendations from health scores
        for health_score in health_scores:
            for rec in health_score.recommendations:
                recommendations.append(
                    {
                        "type": "performance_optimization",
                        "component": health_score.component,
                        "priority": (
                            "high"
                            if health_score.status == HealthStatus.CRITICAL
                            else "medium"
                        ),
                        "recommendation": rec,
                        "expected_impact": "Improve system performance and user experience",
                    }
                )

        # Add cache-specific recommendations
        cache_recommendations = (
            self.cache_monitor.get_cache_efficiency_recommendations()
        )
        for rec in cache_recommendations:
            recommendations.append(
                {
                    "type": "cache_optimization",
                    "component": "cache",
                    "priority": rec.get("priority", "medium"),
                    "recommendation": rec.get("recommendation", ""),
                    "expected_impact": rec.get(
                        "potential_impact", "Performance improvement"
                    ),
                }
            )

        return recommendations

    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Get current dashboard data"""
        # Update if data is stale
        if time.time() - self._last_update > self.update_interval:
            await self._update_dashboard_data()

        return self.dashboard_data.copy()

    async def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get real-time metrics snapshot"""
        auth_stats = self.auth_monitor.get_comprehensive_stats(
            window_seconds=300
        )  # Last 5 minutes
        cache_stats = self.cache_monitor.get_comprehensive_stats(window_seconds=300)
        system_stats = await self._collect_system_stats()

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "auth_performance": {
                "active_operations": auth_stats.get("overall_summary", {}).get(
                    "active_operations", 0
                ),
                "recent_login_p95_ms": auth_stats.get("operations", {})
                .get("login", {})
                .get("p95_duration_ms", 0),
                "recent_success_rate": auth_stats.get("overall_summary", {}).get(
                    "overall_success_rate", 0
                ),
            },
            "cache_performance": {
                "current_hit_rate": cache_stats.get("overall_summary", {}).get(
                    "overall_hit_rate", 0
                ),
                "redis_response_ms": cache_stats.get("cache_layers", {})
                .get("redis", {})
                .get("average_response_time_ms", 0),
                "active_operations": cache_stats.get("overall_summary", {}).get(
                    "active_operations", 0
                ),
            },
            "system_resources": {
                "cpu_usage": system_stats.get("cpu", {}).get("usage_percent", 0),
                "memory_usage": system_stats.get("memory", {}).get("usage_percent", 0),
            },
        }

    async def export_dashboard_json(self) -> str:
        """Export dashboard data as JSON"""
        dashboard_data = await self.get_dashboard_data()
        return json.dumps(dashboard_data, indent=2, default=str)

    def get_dashboard_health(self) -> Dict[str, Any]:
        """Get dashboard system health"""
        return {
            "status": "healthy",
            "last_update": datetime.fromtimestamp(self._last_update).isoformat(),
            "update_interval_seconds": self.update_interval,
            "active_alerts": len(self.active_alerts),
            "components_monitored": [
                "auth_performance",
                "cache_performance",
                "system_resources",
            ],
            "data_freshness_seconds": time.time() - self._last_update,
        }


# Global singleton instance
_system_health_dashboard = None


def get_system_health_dashboard() -> SystemHealthDashboard:
    """Get singleton system health dashboard instance"""
    global _system_health_dashboard
    if _system_health_dashboard is None:
        _system_health_dashboard = SystemHealthDashboard()
    return _system_health_dashboard
