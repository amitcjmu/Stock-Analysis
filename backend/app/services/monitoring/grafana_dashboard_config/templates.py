"""
Dashboard Templates for Grafana Configuration

Provides complete dashboard templates for different monitoring scenarios.
Contains pre-configured dashboard layouts and panel arrangements.
"""

from typing import Any, Dict, List

from .base import GrafanaDashboardBase
from .panels import PanelConfigBuilder
from .queries import MetricQueryBuilder


class DashboardTemplates(GrafanaDashboardBase):
    """
    Dashboard template generator for Grafana configurations

    Provides complete dashboard templates with pre-configured panels
    for different monitoring scenarios including executive, detailed,
    cache, system health, and user experience dashboards.
    """

    def __init__(self):
        super().__init__()
        self.panel_builder = PanelConfigBuilder()
        self.query_builder = MetricQueryBuilder()

    def generate_executive_overview_dashboard(self) -> Dict[str, Any]:
        """Generate executive overview dashboard"""
        base_config = self.get_base_dashboard_config(
            "Auth Performance - Executive Overview",
            ["auth", "performance", "executive"],
        )

        auth_queries = self.query_builder.get_auth_performance_queries()
        business_queries = self.query_builder.get_business_impact_queries()
        target_queries = self.query_builder.get_performance_targets_queries()

        panels = [
            self.panel_builder.create_stat_panel(
                title="Login Performance Target Achievement",
                query=business_queries["login_improvement"]["expr"],
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
            self.panel_builder.create_stat_panel(
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
            self.panel_builder.create_stat_panel(
                title="Active User Sessions",
                query=business_queries["active_sessions"]["expr"],
                unit="short",
                pos_x=12,
                pos_y=0,
                width=6,
                height=4,
            ),
            self.panel_builder.create_stat_panel(
                title="System Health Score",
                query=target_queries["system_health_score"]["expr"],
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
            self.panel_builder.create_time_series_panel(
                title="Authentication Performance Trends",
                targets=[
                    auth_queries["login_p95"],
                    auth_queries["session_validation_p95"],
                    auth_queries["context_switch_p95"],
                ],
                pos_x=0,
                pos_y=4,
                width=12,
                height=8,
                unit="ms",
            ),
            self.panel_builder.create_time_series_panel(
                title="Business Impact Metrics",
                targets=[
                    business_queries["successful_logins"],
                    business_queries["failed_logins"],
                    {"expr": "cache_hit_ratio", "legendFormat": "Cache Hit Rate %"},
                ],
                pos_x=12,
                pos_y=4,
                width=12,
                height=8,
                unit="short",
            ),
        ]

        return {"dashboard": {**base_config, "panels": panels}}

    def generate_auth_performance_dashboard(self) -> Dict[str, Any]:
        """Generate detailed authentication performance dashboard"""
        base_config = self.get_base_dashboard_config(
            "Auth Performance - Detailed Analysis", ["auth", "performance", "detailed"]
        )

        auth_queries = self.query_builder.get_auth_performance_queries()

        panels = [
            self.panel_builder.create_time_series_panel(
                title="Login Performance Distribution",
                targets=[
                    auth_queries["login_p50"],
                    auth_queries["login_p95"],
                    auth_queries["login_p99"],
                ],
                pos_x=0,
                pos_y=0,
                width=12,
                height=8,
                unit="ms",
            ),
            self.panel_builder.create_heatmap_panel(
                title="Login Response Time Heatmap",
                query="rate(auth_login_duration_seconds_bucket[5m])",
                pos_x=12,
                pos_y=0,
                width=12,
                height=8,
            ),
            self.panel_builder.create_time_series_panel(
                title="Authentication Success Rate",
                targets=[
                    auth_queries["success_rate"],
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
            self.panel_builder.create_time_series_panel(
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
            self.panel_builder.create_table_panel(
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
        ]

        return {"dashboard": {**base_config, "panels": panels}}

    def generate_cache_performance_dashboard(self) -> Dict[str, Any]:
        """Generate cache performance monitoring dashboard"""
        base_config = self.get_base_dashboard_config(
            "Cache Performance - Multi-Layer Analysis",
            ["cache", "performance", "redis"],
        )

        cache_queries = self.query_builder.get_cache_performance_queries()

        panels = [
            self.panel_builder.create_stat_panel(
                title="Overall Cache Hit Rate",
                query=cache_queries["overall_hit_rate"]["expr"],
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
            self.panel_builder.create_stat_panel(
                title="Redis Hit Rate",
                query=cache_queries["redis_hit_rate"]["expr"],
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
            self.panel_builder.create_stat_panel(
                title="Memory Cache Hit Rate",
                query=cache_queries["memory_hit_rate"]["expr"],
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
            self.panel_builder.create_stat_panel(
                title="Cache Operations/sec",
                query="rate(cache_operations_total[5m])",
                unit="ops",
                pos_x=18,
                pos_y=0,
                width=6,
                height=4,
            ),
            self.panel_builder.create_time_series_panel(
                title="Cache Hit/Miss Rates by Layer",
                targets=[
                    cache_queries["redis_hits"],
                    cache_queries["redis_misses"],
                    cache_queries["memory_hits"],
                    cache_queries["memory_misses"],
                ],
                pos_x=0,
                pos_y=4,
                width=12,
                height=8,
                unit="ops",
            ),
            self.panel_builder.create_time_series_panel(
                title="Cache Response Times",
                targets=[
                    cache_queries["redis_response_time"],
                    cache_queries["memory_response_time"],
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
        ]

        return {"dashboard": {**base_config, "panels": panels}}

    def generate_system_health_dashboard(self) -> Dict[str, Any]:
        """Generate system health monitoring dashboard"""
        base_config = self.get_base_dashboard_config(
            "System Health - Resource Monitoring", ["system", "health", "resources"]
        )

        system_queries = self.query_builder.get_system_health_queries()

        panels = [
            self.panel_builder.create_gauge_panel(
                title="CPU Usage",
                query=system_queries["cpu_usage"]["expr"],
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
            self.panel_builder.create_gauge_panel(
                title="Memory Usage",
                query=system_queries["memory_usage"]["expr"],
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
            self.panel_builder.create_time_series_panel(
                title="System Resource Trends",
                targets=[
                    system_queries["cpu_usage"],
                    system_queries["memory_usage"],
                ],
                pos_x=12,
                pos_y=0,
                width=12,
                height=8,
                unit="percent",
            ),
        ]

        return {"dashboard": {**base_config, "panels": panels}}

    def generate_user_experience_dashboard(self) -> Dict[str, Any]:
        """Generate user experience impact dashboard"""
        base_config = self.get_base_dashboard_config(
            "User Experience - Performance Impact",
            ["user", "experience", "performance"],
        )

        business_queries = self.query_builder.get_business_impact_queries()
        target_queries = self.query_builder.get_performance_targets_queries()

        panels = [
            self.panel_builder.create_stat_panel(
                title="Login Improvement vs Baseline",
                query=business_queries["login_improvement"]["expr"],
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
            self.panel_builder.create_stat_panel(
                title="Context Switch Improvement",
                query=business_queries["context_switch_improvement"]["expr"],
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
            self.panel_builder.create_time_series_panel(
                title="Performance Target Achievement",
                targets=[
                    target_queries["login_target"],
                    target_queries["context_switch_target"],
                    target_queries["cache_target"],
                ],
                pos_x=0,
                pos_y=4,
                width=24,
                height=8,
                unit="percent",
            ),
        ]

        return {"dashboard": {**base_config, "panels": panels}}
