"""
Dashboard Builder and Export Logic

Provides the main dashboard builder class and export functionality.
Contains alerting rule generation and dashboard provisioning configuration.
"""

import json
import os
from typing import Any, Dict

from app.core.logging import get_logger

from .base import GrafanaDashboardBase
from .templates import DashboardTemplates

logger = get_logger(__name__)


class GrafanaDashboardBuilder(GrafanaDashboardBase):
    """
    Main dashboard builder class for Grafana configurations

    Provides complete dashboard generation, alerting rules, and export functionality.
    Combines all dashboard types and provides unified configuration management.
    """

    def __init__(self):
        super().__init__()
        self.templates = DashboardTemplates()

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
            "executive_overview": self.templates.generate_executive_overview_dashboard(),
            "auth_performance": self.templates.generate_auth_performance_dashboard(),
            "cache_performance": self.templates.generate_cache_performance_dashboard(),
            "system_health": self.templates.generate_system_health_dashboard(),
            "user_experience": self.templates.generate_user_experience_dashboard(),
            "alerting_rules": self.generate_alerting_rules(),
            "provisioning_config": self.generate_provisioning_config(),
        }

    def save_dashboard_files(self, output_dir: str) -> None:
        """Save all dashboard configurations to files"""
        os.makedirs(output_dir, exist_ok=True)

        dashboards = self.export_all_dashboards()

        for name, config in dashboards.items():
            filename = f"{name}.json"
            filepath = os.path.join(output_dir, filename)

            with open(filepath, "w") as f:
                json.dump(config, f, indent=2)

            logger.info(f"Saved dashboard configuration: {filepath}")


# Global instance
_grafana_builder = None


def get_grafana_dashboard_builder() -> GrafanaDashboardBuilder:
    """Get singleton Grafana dashboard builder instance"""
    global _grafana_builder
    if _grafana_builder is None:
        _grafana_builder = GrafanaDashboardBuilder()
    return _grafana_builder
