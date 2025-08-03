"""
Grafana Dashboard Configuration

Comprehensive Grafana dashboard configuration for auth performance monitoring.
Provides pre-configured dashboards, panels, and alerting rules for observability
of authentication optimization performance metrics.

Key Features:
- Pre-configured dashboard templates for auth performance monitoring
- Custom panels for authentication flow visualization
- Cache performance monitoring dashboards
- System health overview dashboards
- Performance threshold alerting rules
- Business impact visualization panels
- Automated dashboard provisioning configuration

Dashboard Categories:
1. Executive Overview - High-level performance KPIs and business impact
2. Authentication Performance - Detailed auth flow monitoring
3. Cache Performance - Multi-layer cache monitoring and optimization
4. System Health - Resource utilization and bottleneck identification
5. User Experience - Performance impact on user workflows
6. Troubleshooting - Detailed diagnostics and error analysis
"""

import json
from typing import Any, Dict, List, Optional

# Datetime imports available if needed in future

from app.core.logging import get_logger

logger = get_logger(__name__)


class GrafanaDashboardConfig:
    """
    Grafana Dashboard Configuration Generator

    Generates comprehensive Grafana dashboard configurations for
    authentication performance monitoring and optimization.
    """

    def __init__(self):
        self.datasource_name = "prometheus"
        self.refresh_interval = "30s"
        self.time_range = {"from": "now-1h", "to": "now"}

        # Performance thresholds for alerting
        self.alert_thresholds = {
            "login_p95_ms": 1000,
            "session_validation_p95_ms": 500,
            "context_switch_p95_ms": 500,
            "cache_hit_rate_percent": 80,
            "error_rate_percent": 5,
            "cpu_usage_percent": 80,
            "memory_usage_percent": 85,
        }

        logger.info("GrafanaDashboardConfig initialized")

    def generate_executive_overview_dashboard(self) -> Dict[str, Any]:
        """Generate executive overview dashboard"""
        return {
            "dashboard": {
                "id": None,
                "title": "Auth Performance - Executive Overview",
                "tags": ["auth", "performance", "executive"],
                "timezone": "browser",
                "refresh": self.refresh_interval,
                "time": self.time_range,
                "timepicker": {
                    "refresh_intervals": [
                        "5s",
                        "10s",
                        "30s",
                        "1m",
                        "5m",
                        "15m",
                        "30m",
                        "1h",
                        "2h",
                        "1d",
                    ],
                    "time_options": [
                        "5m",
                        "15m",
                        "1h",
                        "6h",
                        "12h",
                        "24h",
                        "2d",
                        "7d",
                        "30d",
                    ],
                },
                "panels": [
                    self._create_stat_panel(
                        title="Login Performance Target Achievement",
                        query='((2500 - auth_login_duration_seconds{quantile="0.95"} * 1000) / 2500) * 100',
                        unit="percent",
                        pos_x=0,
                        pos_y=0,
                        width=6,
                        height=4,
                        thresholds=[
                            {"color": "red", "value": 0},
                            {"color": "yellow", "value": 70},
                            {"color": "green", "value": 80},
                        ],
                    ),
                    self._create_stat_panel(
                        title="Cache Hit Rate",
                        query="cache_hit_ratio",
                        unit="percent",
                        pos_x=6,
                        pos_y=0,
                        width=6,
                        height=4,
                        thresholds=[
                            {"color": "red", "value": 0},
                            {"color": "yellow", "value": 70},
                            {"color": "green", "value": 80},
                        ],
                    ),
                    self._create_stat_panel(
                        title="Active User Sessions",
                        query="auth_active_sessions",
                        unit="short",
                        pos_x=12,
                        pos_y=0,
                        width=6,
                        height=4,
                    ),
                    self._create_stat_panel(
                        title="System Health Score",
                        query=(
                            "(avg(100 - system_cpu_usage_percent) + "
                            "avg(100 - system_memory_usage_bytes / system_memory_total_bytes * 100) + "
                            "avg(cache_hit_ratio)) / 3"
                        ),
                        unit="percent",
                        pos_x=18,
                        pos_y=0,
                        width=6,
                        height=4,
                        thresholds=[
                            {"color": "red", "value": 0},
                            {"color": "yellow", "value": 70},
                            {"color": "green", "value": 85},
                        ],
                    ),
                    self._create_time_series_panel(
                        title="Authentication Performance Trends",
                        targets=[
                            {
                                "expr": 'auth_login_duration_seconds{quantile="0.95"} * 1000',
                                "legendFormat": "Login P95 (ms)",
                            },
                            {
                                "expr": 'auth_session_validation_duration_seconds{quantile="0.95"} * 1000',
                                "legendFormat": "Session Validation P95 (ms)",
                            },
                            {
                                "expr": 'auth_context_switch_duration_seconds{quantile="0.95"} * 1000',
                                "legendFormat": "Context Switch P95 (ms)",
                            },
                        ],
                        pos_x=0,
                        pos_y=4,
                        width=12,
                        height=8,
                        unit="ms",
                    ),
                    self._create_time_series_panel(
                        title="Business Impact Metrics",
                        targets=[
                            {
                                "expr": 'rate(auth_login_attempts_total{status="success"}[5m]) * 100',
                                "legendFormat": "Successful Logins/min",
                            },
                            {
                                "expr": "rate(auth_login_failures_total[5m]) * 100",
                                "legendFormat": "Failed Logins/min",
                            },
                            {
                                "expr": "cache_hit_ratio",
                                "legendFormat": "Cache Hit Rate %",
                            },
                        ],
                        pos_x=12,
                        pos_y=4,
                        width=12,
                        height=8,
                        unit="short",
                    ),
                ],
            }
        }

    def generate_auth_performance_dashboard(self) -> Dict[str, Any]:
        """Generate detailed authentication performance dashboard"""
        return {
            "dashboard": {
                "id": None,
                "title": "Auth Performance - Detailed Analysis",
                "tags": ["auth", "performance", "detailed"],
                "timezone": "browser",
                "refresh": self.refresh_interval,
                "time": self.time_range,
                "panels": [
                    self._create_time_series_panel(
                        title="Login Performance Distribution",
                        targets=[
                            {
                                "expr": "histogram_quantile(0.50, rate(auth_login_duration_seconds_bucket[5m])) * 1000",
                                "legendFormat": "P50",
                            },
                            {
                                "expr": "histogram_quantile(0.95, rate(auth_login_duration_seconds_bucket[5m])) * 1000",
                                "legendFormat": "P95",
                            },
                            {
                                "expr": "histogram_quantile(0.99, rate(auth_login_duration_seconds_bucket[5m])) * 1000",
                                "legendFormat": "P99",
                            },
                        ],
                        pos_x=0,
                        pos_y=0,
                        width=12,
                        height=8,
                        unit="ms",
                    ),
                    self._create_heatmap_panel(
                        title="Login Response Time Heatmap",
                        query="rate(auth_login_duration_seconds_bucket[5m])",
                        pos_x=12,
                        pos_y=0,
                        width=12,
                        height=8,
                    ),
                    self._create_time_series_panel(
                        title="Authentication Success Rate",
                        targets=[
                            {
                                "expr": (
                                    'rate(auth_login_attempts_total{status="success"}[5m]) / '
                                    "rate(auth_login_attempts_total[5m]) * 100"
                                ),
                                "legendFormat": "Login Success Rate",
                            },
                            {
                                "expr": (
                                    'rate(auth_session_validations_total{status="success"}[5m]) / '
                                    "rate(auth_session_validations_total[5m]) * 100"
                                ),
                                "legendFormat": "Session Validation Success Rate",
                            },
                        ],
                        pos_x=0,
                        pos_y=8,
                        width=12,
                        height=6,
                        unit="percent",
                    ),
                    self._create_time_series_panel(
                        title="Context Switching Performance",
                        targets=[
                            {
                                "expr": (
                                    'auth_context_switch_duration_seconds{quantile="0.95", '
                                    'context_type="client"} * 1000'
                                ),
                                "legendFormat": "Client Context Switch P95",
                            },
                            {
                                "expr": (
                                    'auth_context_switch_duration_seconds{quantile="0.95", '
                                    'context_type="engagement"} * 1000'
                                ),
                                "legendFormat": "Engagement Context Switch P95",
                            },
                        ],
                        pos_x=12,
                        pos_y=8,
                        width=12,
                        height=6,
                        unit="ms",
                    ),
                    self._create_table_panel(
                        title="Authentication Operations Summary",
                        targets=[
                            {
                                "expr": "increase(auth_login_attempts_total[1h])",
                                "legendFormat": "Login Attempts (1h)",
                                "format": "table",
                            },
                            {
                                "expr": "increase(auth_session_validations_total[1h])",
                                "legendFormat": "Session Validations (1h)",
                                "format": "table",
                            },
                        ],
                        pos_x=0,
                        pos_y=14,
                        width=24,
                        height=6,
                    ),
                ],
            }
        }

    def generate_cache_performance_dashboard(self) -> Dict[str, Any]:
        """Generate cache performance monitoring dashboard"""
        return {
            "dashboard": {
                "id": None,
                "title": "Cache Performance - Multi-Layer Analysis",
                "tags": ["cache", "performance", "redis"],
                "timezone": "browser",
                "refresh": self.refresh_interval,
                "time": self.time_range,
                "panels": [
                    self._create_stat_panel(
                        title="Overall Cache Hit Rate",
                        query="cache_hit_ratio",
                        unit="percent",
                        pos_x=0,
                        pos_y=0,
                        width=6,
                        height=4,
                        thresholds=[
                            {"color": "red", "value": 0},
                            {"color": "yellow", "value": 70},
                            {"color": "green", "value": 80},
                        ],
                    ),
                    self._create_stat_panel(
                        title="Redis Hit Rate",
                        query='cache_hit_ratio{cache_type="redis"}',
                        unit="percent",
                        pos_x=6,
                        pos_y=0,
                        width=6,
                        height=4,
                        thresholds=[
                            {"color": "red", "value": 0},
                            {"color": "yellow", "value": 75},
                            {"color": "green", "value": 85},
                        ],
                    ),
                    self._create_stat_panel(
                        title="Memory Cache Hit Rate",
                        query='cache_hit_ratio{cache_type="memory"}',
                        unit="percent",
                        pos_x=12,
                        pos_y=0,
                        width=6,
                        height=4,
                        thresholds=[
                            {"color": "red", "value": 0},
                            {"color": "yellow", "value": 60},
                            {"color": "green", "value": 75},
                        ],
                    ),
                    self._create_stat_panel(
                        title="Cache Operations/sec",
                        query="rate(cache_operations_total[5m])",
                        unit="ops",
                        pos_x=18,
                        pos_y=0,
                        width=6,
                        height=4,
                    ),
                    self._create_time_series_panel(
                        title="Cache Hit/Miss Rates by Layer",
                        targets=[
                            {
                                "expr": 'rate(cache_hits_total{cache_type="redis"}[5m])',
                                "legendFormat": "Redis Hits/sec",
                            },
                            {
                                "expr": 'rate(cache_misses_total{cache_type="redis"}[5m])',
                                "legendFormat": "Redis Misses/sec",
                            },
                            {
                                "expr": 'rate(cache_hits_total{cache_type="memory"}[5m])',
                                "legendFormat": "Memory Hits/sec",
                            },
                            {
                                "expr": 'rate(cache_misses_total{cache_type="memory"}[5m])',
                                "legendFormat": "Memory Misses/sec",
                            },
                        ],
                        pos_x=0,
                        pos_y=4,
                        width=12,
                        height=8,
                        unit="ops",
                    ),
                    self._create_time_series_panel(
                        title="Cache Response Times",
                        targets=[
                            {
                                "expr": (
                                    "histogram_quantile(0.95, rate("
                                    'cache_operation_duration_seconds_bucket{cache_type="redis"}[5m])) * 1000'
                                ),
                                "legendFormat": "Redis P95",
                            },
                            {
                                "expr": (
                                    "histogram_quantile(0.95, rate("
                                    'cache_operation_duration_seconds_bucket{cache_type="memory"}[5m])) * 1000'
                                ),
                                "legendFormat": "Memory P95",
                            },
                            {
                                "expr": (
                                    "histogram_quantile(0.50, rate("
                                    "cache_operation_duration_seconds_bucket[5m])) * 1000"
                                ),
                                "legendFormat": "Overall P50",
                            },
                        ],
                        pos_x=12,
                        pos_y=4,
                        width=12,
                        height=8,
                        unit="ms",
                    ),
                    self._create_time_series_panel(
                        title="Cache Utilization",
                        targets=[
                            {
                                "expr": 'cache_utilization_percent{cache_type="redis"}',
                                "legendFormat": "Redis Utilization %",
                            },
                            {
                                "expr": 'cache_utilization_percent{cache_type="memory"}',
                                "legendFormat": "Memory Cache Utilization %",
                            },
                        ],
                        pos_x=0,
                        pos_y=12,
                        width=12,
                        height=6,
                        unit="percent",
                    ),
                    self._create_time_series_panel(
                        title="Cache Errors and Evictions",
                        targets=[
                            {
                                "expr": "rate(cache_errors_total[5m])",
                                "legendFormat": "Cache Errors/sec",
                            },
                            {
                                "expr": "rate(cache_evictions_total[5m])",
                                "legendFormat": "Cache Evictions/sec",
                            },
                        ],
                        pos_x=12,
                        pos_y=12,
                        width=12,
                        height=6,
                        unit="ops",
                    ),
                ],
            }
        }

    def generate_system_health_dashboard(self) -> Dict[str, Any]:
        """Generate system health monitoring dashboard"""
        return {
            "dashboard": {
                "id": None,
                "title": "System Health - Resource Monitoring",
                "tags": ["system", "health", "resources"],
                "timezone": "browser",
                "refresh": self.refresh_interval,
                "time": self.time_range,
                "panels": [
                    self._create_gauge_panel(
                        title="CPU Usage",
                        query="system_cpu_usage_percent",
                        unit="percent",
                        pos_x=0,
                        pos_y=0,
                        width=6,
                        height=8,
                        min_value=0,
                        max_value=100,
                        thresholds=[
                            {"color": "green", "value": 0},
                            {"color": "yellow", "value": 70},
                            {"color": "red", "value": 85},
                        ],
                    ),
                    self._create_gauge_panel(
                        title="Memory Usage",
                        query="system_memory_usage_bytes / system_memory_total_bytes * 100",
                        unit="percent",
                        pos_x=6,
                        pos_y=0,
                        width=6,
                        height=8,
                        min_value=0,
                        max_value=100,
                        thresholds=[
                            {"color": "green", "value": 0},
                            {"color": "yellow", "value": 75},
                            {"color": "red", "value": 85},
                        ],
                    ),
                    self._create_time_series_panel(
                        title="System Resource Trends",
                        targets=[
                            {
                                "expr": "system_cpu_usage_percent",
                                "legendFormat": "CPU Usage %",
                            },
                            {
                                "expr": "system_memory_usage_bytes / system_memory_total_bytes * 100",
                                "legendFormat": "Memory Usage %",
                            },
                        ],
                        pos_x=12,
                        pos_y=0,
                        width=12,
                        height=8,
                        unit="percent",
                    ),
                    self._create_time_series_panel(
                        title="Network I/O",
                        targets=[
                            {
                                "expr": "rate(system_network_bytes_sent[5m]) * 8 / 1024 / 1024",
                                "legendFormat": "Outbound Mbps",
                            },
                            {
                                "expr": "rate(system_network_bytes_recv[5m]) * 8 / 1024 / 1024",
                                "legendFormat": "Inbound Mbps",
                            },
                        ],
                        pos_x=0,
                        pos_y=8,
                        width=12,
                        height=6,
                        unit="Mbps",
                    ),
                    self._create_time_series_panel(
                        title="Active Connections",
                        targets=[
                            {
                                "expr": 'system_active_connections{type="http"}',
                                "legendFormat": "HTTP Connections",
                            },
                            {
                                "expr": 'system_active_connections{type="database"}',
                                "legendFormat": "Database Connections",
                            },
                        ],
                        pos_x=12,
                        pos_y=8,
                        width=12,
                        height=6,
                        unit="short",
                    ),
                ],
            }
        }

    def generate_user_experience_dashboard(self) -> Dict[str, Any]:
        """Generate user experience impact dashboard"""
        return {
            "dashboard": {
                "id": None,
                "title": "User Experience - Performance Impact",
                "tags": ["user", "experience", "performance"],
                "timezone": "browser",
                "refresh": self.refresh_interval,
                "time": self.time_range,
                "panels": [
                    self._create_stat_panel(
                        title="Login Improvement vs Baseline",
                        query='((2500 - auth_login_duration_seconds{quantile="0.95"} * 1000) / 2500) * 100',
                        unit="percent",
                        pos_x=0,
                        pos_y=0,
                        width=8,
                        height=4,
                        thresholds=[
                            {"color": "red", "value": 0},
                            {"color": "yellow", "value": 75},
                            {"color": "green", "value": 85},
                        ],
                    ),
                    self._create_stat_panel(
                        title="Context Switch Improvement",
                        query='((1500 - auth_context_switch_duration_seconds{quantile="0.95"} * 1000) / 1500) * 100',
                        unit="percent",
                        pos_x=8,
                        pos_y=0,
                        width=8,
                        height=4,
                        thresholds=[
                            {"color": "red", "value": 0},
                            {"color": "yellow", "value": 80},
                            {"color": "green", "value": 90},
                        ],
                    ),
                    self._create_stat_panel(
                        title="User Experience Score",
                        query=(
                            '(min(100, max(0, 100 - auth_login_duration_seconds{quantile="0.95"} * '
                            "1000 / 500 * 100)) + cache_hit_ratio) / 2"
                        ),
                        unit="percent",
                        pos_x=16,
                        pos_y=0,
                        width=8,
                        height=4,
                        thresholds=[
                            {"color": "red", "value": 0},
                            {"color": "yellow", "value": 70},
                            {"color": "green", "value": 85},
                        ],
                    ),
                    self._create_time_series_panel(
                        title="Performance Target Achievement",
                        targets=[
                            {
                                "expr": (
                                    'min(100, max(0, (500 - auth_login_duration_seconds{quantile="0.95"} * '
                                    "1000) / 500 * 100))"
                                ),
                                "legendFormat": "Login Target Achievement %",
                            },
                            {
                                "expr": (
                                    "min(100, max(0, (300 - auth_context_switch_duration_seconds{"
                                    'quantile="0.95"} * 1000) / 300 * 100))'
                                ),
                                "legendFormat": "Context Switch Target Achievement %",
                            },
                            {
                                "expr": "min(100, cache_hit_ratio / 85 * 100)",
                                "legendFormat": "Cache Target Achievement %",
                            },
                        ],
                        pos_x=0,
                        pos_y=4,
                        width=24,
                        height=8,
                        unit="percent",
                    ),
                    self._create_table_panel(
                        title="Performance Bottleneck Analysis",
                        targets=[
                            {
                                "expr": "performance_threshold_breaches_total",
                                "legendFormat": "Threshold Breaches",
                                "format": "table",
                            }
                        ],
                        pos_x=0,
                        pos_y=12,
                        width=24,
                        height=6,
                    ),
                ],
            }
        }

    def generate_alerting_rules(self) -> Dict[str, Any]:
        """Generate Prometheus alerting rules for performance monitoring"""
        return {
            "groups": [
                {
                    "name": "auth_performance_alerts",
                    "rules": [
                        {
                            "alert": "HighLoginResponseTime",
                            "expr": (
                                f"histogram_quantile(0.95, rate(auth_login_duration_seconds_bucket[5m])) * "
                                f"1000 > {self.alert_thresholds['login_p95_ms']}"
                            ),
                            "for": "2m",
                            "labels": {
                                "severity": "warning",
                                "component": "authentication",
                            },
                            "annotations": {
                                "summary": "High login response time detected",
                                "description": (
                                    f"P95 login response time is {{{{ $value }}}}ms, which exceeds "
                                    f"the threshold of {self.alert_thresholds['login_p95_ms']}ms"
                                ),
                            },
                        },
                        {
                            "alert": "LowCacheHitRate",
                            "expr": f"cache_hit_ratio < {self.alert_thresholds['cache_hit_rate_percent']}",
                            "for": "5m",
                            "labels": {"severity": "warning", "component": "cache"},
                            "annotations": {
                                "summary": "Low cache hit rate detected",
                                "description": (
                                    f"Cache hit rate is {{{{ $value }}}}%, which is below "
                                    f"the threshold of {self.alert_thresholds['cache_hit_rate_percent']}%"
                                ),
                            },
                        },
                        {
                            "alert": "HighAuthenticationErrorRate",
                            "expr": (
                                f"rate(auth_login_failures_total[5m]) / rate(auth_login_attempts_total[5m]) * "
                                f"100 > {self.alert_thresholds['error_rate_percent']}"
                            ),
                            "for": "2m",
                            "labels": {
                                "severity": "critical",
                                "component": "authentication",
                            },
                            "annotations": {
                                "summary": "High authentication error rate",
                                "description": (
                                    f"Authentication error rate is {{{{ $value }}}}%, which exceeds "
                                    f"the threshold of {self.alert_thresholds['error_rate_percent']}%"
                                ),
                            },
                        },
                        {
                            "alert": "HighSystemCPU",
                            "expr": f"system_cpu_usage_percent > {self.alert_thresholds['cpu_usage_percent']}",
                            "for": "3m",
                            "labels": {"severity": "warning", "component": "system"},
                            "annotations": {
                                "summary": "High CPU usage detected",
                                "description": (
                                    f"CPU usage is {{{{ $value }}}}%, which exceeds "
                                    f"the threshold of {self.alert_thresholds['cpu_usage_percent']}%"
                                ),
                            },
                        },
                        {
                            "alert": "HighSystemMemory",
                            "expr": f"system_memory_usage_percent > {self.alert_thresholds['memory_usage_percent']}",
                            "for": "3m",
                            "labels": {"severity": "warning", "component": "system"},
                            "annotations": {
                                "summary": "High memory usage detected",
                                "description": (
                                    f"Memory usage is {{{{ $value }}}}%, which exceeds "
                                    f"the threshold of {self.alert_thresholds['memory_usage_percent']}%"
                                ),
                            },
                        },
                    ],
                }
            ]
        }

    def _create_stat_panel(
        self,
        title: str,
        query: str,
        unit: str,
        pos_x: int,
        pos_y: int,
        width: int,
        height: int,
        thresholds: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """Create a stat panel configuration"""
        panel = {
            "title": title,
            "type": "stat",
            "gridPos": {"h": height, "w": width, "x": pos_x, "y": pos_y},
            "targets": [{"expr": query, "refId": "A"}],
            "fieldConfig": {"defaults": {"unit": unit}},
        }

        if thresholds:
            panel["fieldConfig"]["defaults"]["thresholds"] = {"steps": thresholds}

        return panel

    def _create_gauge_panel(
        self,
        title: str,
        query: str,
        unit: str,
        pos_x: int,
        pos_y: int,
        width: int,
        height: int,
        min_value: float = 0,
        max_value: float = 100,
        thresholds: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """Create a gauge panel configuration"""
        panel = {
            "title": title,
            "type": "gauge",
            "gridPos": {"h": height, "w": width, "x": pos_x, "y": pos_y},
            "targets": [{"expr": query, "refId": "A"}],
            "fieldConfig": {
                "defaults": {"unit": unit, "min": min_value, "max": max_value}
            },
        }

        if thresholds:
            panel["fieldConfig"]["defaults"]["thresholds"] = {"steps": thresholds}

        return panel

    def _create_time_series_panel(
        self,
        title: str,
        targets: List[Dict],
        pos_x: int,
        pos_y: int,
        width: int,
        height: int,
        unit: str = "short",
    ) -> Dict[str, Any]:
        """Create a time series panel configuration"""
        return {
            "title": title,
            "type": "timeseries",
            "gridPos": {"h": height, "w": width, "x": pos_x, "y": pos_y},
            "targets": targets,
            "fieldConfig": {"defaults": {"unit": unit}},
        }

    def _create_heatmap_panel(
        self, title: str, query: str, pos_x: int, pos_y: int, width: int, height: int
    ) -> Dict[str, Any]:
        """Create a heatmap panel configuration"""
        return {
            "title": title,
            "type": "heatmap",
            "gridPos": {"h": height, "w": width, "x": pos_x, "y": pos_y},
            "targets": [{"expr": query, "refId": "A", "format": "heatmap"}],
        }

    def _create_table_panel(
        self,
        title: str,
        targets: List[Dict],
        pos_x: int,
        pos_y: int,
        width: int,
        height: int,
    ) -> Dict[str, Any]:
        """Create a table panel configuration"""
        return {
            "title": title,
            "type": "table",
            "gridPos": {"h": height, "w": width, "x": pos_x, "y": pos_y},
            "targets": targets,
        }

    def generate_provisioning_config(self) -> Dict[str, Any]:
        """Generate Grafana provisioning configuration"""
        return {
            "apiVersion": 1,
            "providers": [
                {
                    "name": "auth-performance-dashboards",
                    "orgId": 1,
                    "folder": "Auth Performance",
                    "type": "file",
                    "disableDeletion": False,
                    "updateIntervalSeconds": 10,
                    "allowUiUpdates": True,
                    "options": {
                        "path": "/etc/grafana/provisioning/dashboards/auth-performance"
                    },
                }
            ],
        }

    def export_all_dashboards(self) -> Dict[str, Dict[str, Any]]:
        """Export all dashboard configurations"""
        return {
            "executive_overview": self.generate_executive_overview_dashboard(),
            "auth_performance": self.generate_auth_performance_dashboard(),
            "cache_performance": self.generate_cache_performance_dashboard(),
            "system_health": self.generate_system_health_dashboard(),
            "user_experience": self.generate_user_experience_dashboard(),
            "alerting_rules": self.generate_alerting_rules(),
            "provisioning_config": self.generate_provisioning_config(),
        }

    def save_dashboard_files(self, output_dir: str) -> None:
        """Save all dashboard configurations to files"""
        import os

        os.makedirs(output_dir, exist_ok=True)

        dashboards = self.export_all_dashboards()

        for name, config in dashboards.items():
            filename = f"{name}.json"
            filepath = os.path.join(output_dir, filename)

            with open(filepath, "w") as f:
                json.dump(config, f, indent=2)

            logger.info(f"Saved dashboard configuration: {filepath}")


# Global instance
_grafana_config = None


def get_grafana_dashboard_config() -> GrafanaDashboardConfig:
    """Get singleton Grafana dashboard config instance"""
    global _grafana_config
    if _grafana_config is None:
        _grafana_config = GrafanaDashboardConfig()
    return _grafana_config
