"""
Metrics collection and management for Service Health Manager

Handles service metrics collection, analysis, and alerting.
"""

import statistics
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Any, Dict, List

from app.core.logging import get_logger

from .base import HealthCheckResult, HealthMetrics, ServiceHealth, ServiceType

logger = get_logger(__name__)


class MetricsManager:
    """Manages metrics collection and analysis for service health monitoring"""

    def __init__(self):
        self.service_metrics: Dict[ServiceType, HealthMetrics] = {}
        self.response_times: Dict[ServiceType, deque] = defaultdict(
            lambda: deque(maxlen=1000)
        )
        self.health_history: Dict[ServiceType, deque] = defaultdict(
            lambda: deque(maxlen=500)
        )
        self.alert_history: Dict[ServiceType, List] = defaultdict(list)

    def initialize_metrics(self, service_type: ServiceType) -> None:
        """Initialize metrics for a service"""
        if service_type not in self.service_metrics:
            self.service_metrics[service_type] = HealthMetrics(
                service_type=service_type
            )

    async def update_service_metrics(self, result: HealthCheckResult, config) -> None:
        """Update service metrics based on health check result"""
        service_type = result.service_type
        metrics = self.service_metrics[service_type]

        # Update basic metrics
        metrics.response_time_ms = result.response_time_ms

        # Add to response time history
        self.response_times[service_type].append(result.response_time_ms)

        # Add to health history
        self.health_history[service_type].append(
            {
                "timestamp": result.timestamp,
                "is_healthy": result.is_healthy,
                "response_time_ms": result.response_time_ms,
                "error_message": result.error_message,
            }
        )

        if result.is_healthy:
            metrics.consecutive_failures = 0
            metrics.consecutive_successes += 1
            metrics.last_success = result.timestamp
            metrics.is_available = True
        else:
            metrics.consecutive_failures += 1
            metrics.consecutive_successes = 0
            metrics.last_failure = result.timestamp
            metrics.error_count += 1

            # Update availability based on failure threshold
            if metrics.consecutive_failures >= config.failure_threshold:
                metrics.is_available = False

        # Calculate success rate from recent history
        recent_checks = list(self.health_history[service_type])[
            -100:
        ]  # Last 100 checks
        if recent_checks:
            successful_checks = sum(1 for check in recent_checks if check["is_healthy"])
            metrics.success_rate = (successful_checks / len(recent_checks)) * 100

    async def check_alerts(self, service_type: ServiceType, config) -> None:
        """Check if alerts should be triggered for a service"""
        metrics = self.service_metrics[service_type]

        # Check for consecutive failures
        if metrics.consecutive_failures >= config.failure_threshold:
            await self._trigger_alert(
                service_type,
                "consecutive_failures",
                f"Service has {metrics.consecutive_failures} consecutive failures",
                severity="high",
            )

        # Check for high response time
        if metrics.response_time_ms > getattr(
            config, "response_time_critical_ms", 5000
        ):
            await self._trigger_alert(
                service_type,
                "high_response_time",
                f"Response time {metrics.response_time_ms}ms exceeds critical threshold",
                severity="medium",
            )

        # Check for low success rate
        if metrics.success_rate < 80:
            await self._trigger_alert(
                service_type,
                "low_success_rate",
                f"Success rate {metrics.success_rate}% below acceptable threshold",
                severity="medium",
            )

    async def _trigger_alert(
        self, service_type: ServiceType, alert_type: str, message: str, severity: str
    ) -> None:
        """Trigger an alert for a service"""
        alert = {
            "timestamp": datetime.utcnow(),
            "service_type": service_type.value,
            "alert_type": alert_type,
            "message": message,
            "severity": severity,
        }

        self.alert_history[service_type].append(alert)

        # Log the alert
        if severity == "high":
            logger.warning(f"HIGH SEVERITY ALERT for {service_type}: {message}")
        else:
            logger.info(f"ALERT for {service_type}: {message}")

    def get_service_health_status(self, service_type: ServiceType) -> ServiceHealth:
        """Get current health status for a service"""
        metrics = self.service_metrics.get(service_type)
        if not metrics:
            return ServiceHealth.UNKNOWN

        if not metrics.is_available:
            return ServiceHealth.CRITICAL

        if metrics.consecutive_failures > 0 or metrics.success_rate < 95:
            return ServiceHealth.DEGRADED

        return ServiceHealth.HEALTHY

    def get_service_metrics(self, service_type: ServiceType) -> HealthMetrics:
        """Get metrics for a specific service"""
        return self.service_metrics.get(
            service_type, HealthMetrics(service_type=service_type)
        )

    async def get_all_metrics(self) -> Dict[ServiceType, HealthMetrics]:
        """Get metrics for all monitored services"""
        return self.service_metrics.copy()

    async def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary across all services"""
        summary = {
            "total_services": len(self.service_metrics),
            "healthy_services": 0,
            "degraded_services": 0,
            "critical_services": 0,
            "average_response_time": 0.0,
            "overall_success_rate": 0.0,
            "recent_alerts": [],
        }

        if not self.service_metrics:
            return summary

        total_response_time = 0.0
        total_success_rate = 0.0

        for service_type, metrics in self.service_metrics.items():
            health_status = self.get_service_health_status(service_type)

            if health_status == ServiceHealth.HEALTHY:
                summary["healthy_services"] += 1
            elif health_status == ServiceHealth.DEGRADED:
                summary["degraded_services"] += 1
            elif health_status == ServiceHealth.CRITICAL:
                summary["critical_services"] += 1

            total_response_time += metrics.response_time_ms
            total_success_rate += metrics.success_rate

        summary["average_response_time"] = total_response_time / len(
            self.service_metrics
        )
        summary["overall_success_rate"] = total_success_rate / len(self.service_metrics)

        # Collect recent alerts from all services
        recent_alerts = []
        cutoff_time = datetime.utcnow() - timedelta(hours=24)

        for service_alerts in self.alert_history.values():
            recent_alerts.extend(
                [alert for alert in service_alerts if alert["timestamp"] > cutoff_time]
            )

        # Sort by timestamp and take most recent
        recent_alerts.sort(key=lambda x: x["timestamp"], reverse=True)
        summary["recent_alerts"] = recent_alerts[:10]

        return summary

    def get_response_time_percentiles(
        self, service_type: ServiceType
    ) -> Dict[str, float]:
        """Calculate response time percentiles for a service"""
        response_times = list(self.response_times[service_type])
        if not response_times:
            return {}

        return {
            "p50": statistics.median(response_times),
            "p95": (
                statistics.quantiles(response_times, n=20)[18]
                if len(response_times) > 20
                else max(response_times)
            ),
            "p99": (
                statistics.quantiles(response_times, n=100)[98]
                if len(response_times) > 100
                else max(response_times)
            ),
            "avg": statistics.mean(response_times),
            "min": min(response_times),
            "max": max(response_times),
        }
