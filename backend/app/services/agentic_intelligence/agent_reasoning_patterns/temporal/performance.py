"""
Performance Trend Pattern Module

This module implements temporal reasoning patterns for performance trend analysis,
analyzing performance metrics over time to identify trends and predict issues.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..base import BaseReasoningPattern, ReasoningEvidence, EvidenceType
from .temporal_core import TemporalPoint, TemporalTrend

logger = logging.getLogger(__name__)


class PerformanceTrendPattern(BaseReasoningPattern):
    """
    Temporal reasoning pattern for performance trend analysis.
    Analyzes performance metrics over time to identify trends and predict issues.
    """

    def __init__(self):
        super().__init__(
            "performance_trend",
            "Performance Trend Analysis",
            "Analyzes performance trends over time to identify issues and opportunities",
        )

    def analyze_performance_trends(
        self, asset_data: Dict[str, Any], historical_data: List[Dict[str, Any]] = None
    ) -> List[ReasoningEvidence]:
        """
        Analyze performance trends for an asset.

        Args:
            asset_data: Current asset data
            historical_data: Historical performance data points

        Returns:
            List of evidence pieces from trend analysis
        """
        evidence_pieces = []

        if not historical_data:
            # Use current metrics as baseline
            return self._analyze_current_performance(asset_data)

        # Analyze CPU utilization trends
        cpu_trend = self._extract_metric_trend(
            historical_data, "cpu_utilization_percent"
        )
        if cpu_trend:
            cpu_evidence = self._analyze_cpu_trend(cpu_trend)
            evidence_pieces.extend(cpu_evidence)

        # Analyze memory utilization trends
        memory_trend = self._extract_metric_trend(
            historical_data, "memory_utilization_percent"
        )
        if memory_trend:
            memory_evidence = self._analyze_memory_trend(memory_trend)
            evidence_pieces.extend(memory_evidence)

        # Analyze response time trends
        response_trend = self._extract_metric_trend(historical_data, "response_time_ms")
        if response_trend:
            response_evidence = self._analyze_response_time_trend(response_trend)
            evidence_pieces.extend(response_evidence)

        return evidence_pieces

    def _extract_metric_trend(
        self, historical_data: List[Dict[str, Any]], metric_name: str
    ) -> Optional[TemporalTrend]:
        """Extract temporal trend for a specific metric"""
        data_points = []

        for data_point in historical_data:
            timestamp_str = data_point.get("timestamp")
            metric_value = data_point.get(metric_name)

            if timestamp_str and metric_value is not None:
                try:
                    timestamp = datetime.fromisoformat(
                        timestamp_str.replace("Z", "+00:00")
                    )
                    data_points.append(TemporalPoint(timestamp, metric_value))
                except (ValueError, TypeError):
                    continue

        return TemporalTrend(data_points) if len(data_points) >= 2 else None

    def _analyze_cpu_trend(self, cpu_trend: TemporalTrend) -> List[ReasoningEvidence]:
        """Analyze CPU utilization trend"""
        evidence_pieces = []

        if cpu_trend.trend_direction == "increasing" and cpu_trend.trend_strength > 0.3:
            confidence = min(0.9, 0.6 + cpu_trend.trend_strength)
            evidence_pieces.append(
                ReasoningEvidence(
                    evidence_type=EvidenceType.PERFORMANCE_METRICS,
                    field_name="cpu_trend",
                    field_value="increasing",
                    confidence=confidence,
                    reasoning=(
                        f"CPU utilization shows increasing trend "
                        f"(strength: {cpu_trend.trend_strength:.2f}), "
                        f"indicating growing load or performance degradation"
                    ),
                    supporting_patterns=[self.pattern_id],
                )
            )

        if cpu_trend.volatility > 0.5:
            evidence_pieces.append(
                ReasoningEvidence(
                    evidence_type=EvidenceType.PERFORMANCE_METRICS,
                    field_name="cpu_volatility",
                    field_value=cpu_trend.volatility,
                    confidence=0.7,
                    reasoning=f"High CPU volatility ({cpu_trend.volatility:.2f}) indicates unstable performance",
                    supporting_patterns=[self.pattern_id],
                )
            )

        return evidence_pieces

    def _analyze_memory_trend(
        self, memory_trend: TemporalTrend
    ) -> List[ReasoningEvidence]:
        """Analyze memory utilization trend"""
        if (
            memory_trend.trend_direction == "increasing"
            and memory_trend.trend_strength > 0.2
        ):
            return [
                ReasoningEvidence(
                    evidence_type=EvidenceType.PERFORMANCE_METRICS,
                    field_name="memory_trend",
                    field_value="increasing",
                    confidence=min(0.9, 0.6 + memory_trend.trend_strength),
                    reasoning=f"Memory increasing trend (strength: {memory_trend.trend_strength:.2f})",
                    supporting_patterns=[self.pattern_id],
                )
            ]
        return []

    def _analyze_response_time_trend(
        self, response_trend: TemporalTrend
    ) -> List[ReasoningEvidence]:
        """Analyze response time trend"""
        if (
            response_trend.trend_direction == "increasing"
            and response_trend.trend_strength > 0.2
        ):
            return [
                ReasoningEvidence(
                    evidence_type=EvidenceType.PERFORMANCE_METRICS,
                    field_name="response_time_trend",
                    field_value="degrading",
                    confidence=min(0.9, 0.6 + response_trend.trend_strength),
                    reasoning=f"Response time degrading trend (strength: {response_trend.trend_strength:.2f})",
                    supporting_patterns=[self.pattern_id],
                )
            ]
        return []

    def _analyze_current_performance(
        self, asset_data: Dict[str, Any]
    ) -> List[ReasoningEvidence]:
        """Analyze current performance metrics when no historical data is available"""
        evidence_pieces = []
        cpu_util = asset_data.get("cpu_utilization_percent")
        if cpu_util and cpu_util >= 80:
            evidence_pieces.append(
                ReasoningEvidence(
                    evidence_type=EvidenceType.PERFORMANCE_METRICS,
                    field_name="current_cpu_high",
                    field_value=cpu_util,
                    confidence=0.8,
                    reasoning=f"Current CPU utilization ({cpu_util}%) is high",
                    supporting_patterns=[self.pattern_id],
                )
            )
        return evidence_pieces
