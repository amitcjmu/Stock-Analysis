"""
Temporal Core Module

This module contains core temporal data structures and functionality for
representing points in time and temporal trends.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class TemporalPoint:
    """Represents a point in time with associated data"""

    def __init__(
        self, timestamp: datetime, value: Any, metadata: Dict[str, Any] = None
    ):
        self.timestamp = timestamp
        self.value = value
        self.metadata = metadata or {}

    def age_in_days(self) -> int:
        """Calculate age in days from current time"""
        return (datetime.utcnow() - self.timestamp).days

    def age_in_months(self) -> int:
        """Calculate age in months from current time"""
        return self.age_in_days() // 30

    def age_in_years(self) -> float:
        """Calculate age in years from current time"""
        return self.age_in_days() / 365.25


class TemporalTrend:
    """Represents a trend over time with direction and strength"""

    def __init__(self, data_points: List[TemporalPoint]):
        self.data_points = sorted(data_points, key=lambda x: x.timestamp)
        self.trend_direction = self._calculate_trend_direction()
        self.trend_strength = self._calculate_trend_strength()
        self.volatility = self._calculate_volatility()

    def _calculate_trend_direction(self) -> str:
        """Calculate overall trend direction"""
        if len(self.data_points) < 2:
            return "unknown"

        first_value = self.data_points[0].value
        last_value = self.data_points[-1].value

        try:
            if isinstance(first_value, (int, float)) and isinstance(
                last_value, (int, float)
            ):
                if last_value > first_value * 1.1:
                    return "increasing"
                elif last_value < first_value * 0.9:
                    return "decreasing"
                else:
                    return "stable"
        except (TypeError, ValueError):
            pass

        return "unknown"

    def _calculate_trend_strength(self) -> float:
        """Calculate strength of the trend (0.0 to 1.0)"""
        if len(self.data_points) < 2:
            return 0.0

        try:
            first_value = float(self.data_points[0].value)
            last_value = float(self.data_points[-1].value)
            change_ratio = abs(last_value - first_value) / (
                first_value if first_value != 0 else 1
            )
            return min(1.0, change_ratio)
        except (TypeError, ValueError, ZeroDivisionError):
            return 0.0

    def _calculate_volatility(self) -> float:
        """Calculate volatility/variance in the data"""
        if len(self.data_points) < 3:
            return 0.0

        try:
            values = [float(point.value) for point in self.data_points]
            mean_value = sum(values) / len(values)
            variance = sum((x - mean_value) ** 2 for x in values) / len(values)
            return min(1.0, variance / (mean_value**2) if mean_value != 0 else 0)
        except (TypeError, ValueError, ZeroDivisionError):
            return 0.0
