"""
Base Configuration Classes for Grafana Dashboards

Provides core configuration classes and utilities for Grafana dashboard generation.
Contains threshold definitions, base dashboard properties, and common utilities.
"""

from typing import Any, Dict, List, Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


class GrafanaDashboardBase:
    """
    Base configuration class for Grafana dashboards

    Provides common configuration and utilities for all dashboard types.
    Contains shared properties, thresholds, and helper methods.
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

        logger.info("GrafanaDashboardBase initialized")

    def get_base_dashboard_config(self, title: str, tags: List[str]) -> Dict[str, Any]:
        """Get base dashboard configuration"""
        return {
            "id": None,
            "title": title,
            "tags": tags,
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
        }

    def get_threshold_config(self, metric_name: str) -> Optional[float]:
        """Get threshold value for a specific metric"""
        return self.alert_thresholds.get(metric_name)

    def get_common_colors(self) -> Dict[str, str]:
        """Get common color scheme for dashboards"""
        return {
            "green": "#56A64B",
            "yellow": "#F2CC0C",
            "red": "#E02F44",
            "blue": "#1F60C4",
            "orange": "#FF9830",
        }
