"""
Grafana Dashboard Configuration Module

Modularized Grafana dashboard configuration for auth performance monitoring.
Provides pre-configured dashboards, panels, and alerting rules for observability
of authentication optimization performance metrics.

This module maintains full backward compatibility with the original monolithic
grafana_dashboard_config.py file while providing a cleaner, modular structure.

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

Usage:
    # Original API (maintained for backward compatibility)
    from app.services.monitoring.grafana_dashboard_config import (
        GrafanaDashboardConfig,
        get_grafana_dashboard_config
    )

    # New modular API (recommended for new code)
    from app.services.monitoring.grafana_dashboard_config import (
        GrafanaDashboardBuilder,
        get_grafana_dashboard_builder,
        DashboardTemplates,
        PanelConfigBuilder,
        MetricQueryBuilder
    )
"""

# Import all components for internal use
from .base import GrafanaDashboardBase
from .builder import GrafanaDashboardBuilder, get_grafana_dashboard_builder
from .panels import PanelConfigBuilder
from .queries import MetricQueryBuilder
from .templates import DashboardTemplates


class GrafanaDashboardConfig(GrafanaDashboardBuilder):
    """
    Backward compatibility class that preserves the original API

    This class maintains 100% backward compatibility with the original
    GrafanaDashboardConfig class while using the new modular implementation.
    All original methods are preserved and work identically.
    """

    def __init__(self):
        super().__init__()

    # Preserve original method names and signatures for backward compatibility
    def _create_stat_panel(
        self,
        title: str,
        query: str,
        unit: str,
        pos_x: int,
        pos_y: int,
        width: int,
        height: int,
        thresholds=None,
    ):
        """Create a stat panel configuration (backward compatibility)"""
        return self.templates.panel_builder.create_stat_panel(
            title, query, unit, pos_x, pos_y, width, height, thresholds
        )

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
        thresholds=None,
    ):
        """Create a gauge panel configuration (backward compatibility)"""
        return self.templates.panel_builder.create_gauge_panel(
            title,
            query,
            unit,
            pos_x,
            pos_y,
            width,
            height,
            min_value,
            max_value,
            thresholds,
        )

    def _create_time_series_panel(
        self,
        title: str,
        targets,
        pos_x: int,
        pos_y: int,
        width: int,
        height: int,
        unit: str = "short",
    ):
        """Create a time series panel configuration (backward compatibility)"""
        return self.templates.panel_builder.create_time_series_panel(
            title, targets, pos_x, pos_y, width, height, unit
        )

    def _create_heatmap_panel(
        self, title: str, query: str, pos_x: int, pos_y: int, width: int, height: int
    ):
        """Create a heatmap panel configuration (backward compatibility)"""
        return self.templates.panel_builder.create_heatmap_panel(
            title, query, pos_x, pos_y, width, height
        )

    def _create_table_panel(
        self,
        title: str,
        targets,
        pos_x: int,
        pos_y: int,
        width: int,
        height: int,
    ):
        """Create a table panel configuration (backward compatibility)"""
        return self.templates.panel_builder.create_table_panel(
            title, targets, pos_x, pos_y, width, height
        )

    # Delegate template methods to the templates instance
    def generate_executive_overview_dashboard(self):
        """Generate executive overview dashboard (backward compatibility)"""
        return self.templates.generate_executive_overview_dashboard()

    def generate_auth_performance_dashboard(self):
        """Generate detailed authentication performance dashboard (backward compatibility)"""
        return self.templates.generate_auth_performance_dashboard()

    def generate_cache_performance_dashboard(self):
        """Generate cache performance monitoring dashboard (backward compatibility)"""
        return self.templates.generate_cache_performance_dashboard()

    def generate_system_health_dashboard(self):
        """Generate system health monitoring dashboard (backward compatibility)"""
        return self.templates.generate_system_health_dashboard()

    def generate_user_experience_dashboard(self):
        """Generate user experience impact dashboard (backward compatibility)"""
        return self.templates.generate_user_experience_dashboard()


# Global instance for backward compatibility
_grafana_config = None


def get_grafana_dashboard_config() -> GrafanaDashboardConfig:
    """Get singleton Grafana dashboard config instance (backward compatibility)"""
    global _grafana_config
    if _grafana_config is None:
        _grafana_config = GrafanaDashboardConfig()
    return _grafana_config


# Export all classes and functions for both backward compatibility and new usage
__all__ = [
    # Backward compatibility (original API)
    "GrafanaDashboardConfig",
    "get_grafana_dashboard_config",
    # New modular API
    "GrafanaDashboardBuilder",
    "get_grafana_dashboard_builder",
    "DashboardTemplates",
    "PanelConfigBuilder",
    "MetricQueryBuilder",
    "GrafanaDashboardBase",
]
