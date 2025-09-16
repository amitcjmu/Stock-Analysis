"""
Panel Configuration Builders for Grafana Dashboards

Provides panel configuration builders for all supported Grafana panel types.
Contains methods for creating stat, gauge, time series, heatmap, and table panels.
"""

from typing import Any, Dict, List, Optional


class PanelConfigBuilder:
    """
    Builder class for Grafana panel configurations

    Provides methods to create different types of panels with consistent configuration.
    Supports stat, gauge, time series, heatmap, and table panel types.
    """

    @staticmethod
    def create_stat_panel(
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

    @staticmethod
    def create_gauge_panel(
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

    @staticmethod
    def create_time_series_panel(
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

    @staticmethod
    def create_heatmap_panel(
        title: str, query: str, pos_x: int, pos_y: int, width: int, height: int
    ) -> Dict[str, Any]:
        """Create a heatmap panel configuration"""
        return {
            "title": title,
            "type": "heatmap",
            "gridPos": {"h": height, "w": width, "x": pos_x, "y": pos_y},
            "targets": [{"expr": query, "refId": "A", "format": "heatmap"}],
        }

    @staticmethod
    def create_table_panel(
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
