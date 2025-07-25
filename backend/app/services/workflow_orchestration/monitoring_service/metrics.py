"""
Metrics Collection and Analysis Module
Team C1 - Task C1.6

Handles metrics collection, aggregation, analysis, and trending.
"""

import statistics
from collections import deque
from dataclasses import asdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.core.logging import get_logger

from .models import MetricPoint, PerformanceMetrics
from .types import MetricType

logger = get_logger(__name__)


class MetricsCollector:
    """Collects and manages workflow metrics"""

    def __init__(self):
        self.metric_buffer: deque = deque(maxlen=10000)  # Rolling metrics buffer
        self.performance_metrics: Dict[str, PerformanceMetrics] = {}

        # Configuration
        self.monitoring_interval_ms = 5000  # 5 seconds
        self.metrics_retention_hours = 72  # 3 days

    async def initialize_performance_metrics(self, workflow_id: str):
        """Initialize performance metrics for a workflow"""
        metrics = PerformanceMetrics(
            workflow_id=workflow_id,
            execution_time_ms=None,
            throughput=0.0,
            resource_utilization={},
            queue_metrics={},
            error_rate=0.0,
            success_rate=1.0,
            quality_scores={},
            efficiency_score=1.0,
            sla_compliance={},
        )
        self.performance_metrics[workflow_id] = metrics

    async def collect_workflow_metrics(self, workflow_id: str):
        """Collect metrics for a specific workflow"""
        # Would implement real metrics collection
        metric = MetricPoint(
            timestamp=datetime.utcnow(),
            metric_name="workflow_status",
            metric_type=MetricType.OPERATIONAL,
            value="running",
            unit=None,
            tags={"workflow_id": workflow_id},
            context={},
        )
        self.metric_buffer.append(metric)

    async def get_performance_metrics(
        self,
        workflow_id: str,
        time_range_minutes: int = 60,
        metric_types: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Get performance metrics for a workflow

        Args:
            workflow_id: ID of the workflow
            time_range_minutes: Time range for metrics
            metric_types: Specific metric types to include

        Returns:
            Comprehensive performance metrics
        """
        try:
            logger.info(f"📈 Getting performance metrics for workflow: {workflow_id}")

            # Get current performance metrics
            perf_metrics = self.performance_metrics.get(workflow_id)
            if not perf_metrics:
                await self.initialize_performance_metrics(workflow_id)
                perf_metrics = self.performance_metrics.get(workflow_id)

            # Get historical metrics from buffer
            cutoff_time = datetime.utcnow() - timedelta(minutes=time_range_minutes)
            historical_metrics = [
                metric
                for metric in self.metric_buffer
                if metric.timestamp >= cutoff_time
                and metric.tags.get("workflow_id") == workflow_id
            ]

            # Filter by metric types if specified
            if metric_types:
                historical_metrics = [
                    metric
                    for metric in historical_metrics
                    if metric.metric_type.value in metric_types
                ]

            # Calculate aggregated metrics
            aggregated_metrics = await self._aggregate_historical_metrics(
                historical_metrics=historical_metrics,
                time_range_minutes=time_range_minutes,
            )

            # Get real-time metrics
            real_time_metrics = await self._collect_real_time_metrics(workflow_id)

            # Combine all metrics
            metrics_data = {
                "workflow_id": workflow_id,
                "time_range_minutes": time_range_minutes,
                "current_metrics": asdict(perf_metrics) if perf_metrics else {},
                "real_time_metrics": real_time_metrics,
                "aggregated_metrics": aggregated_metrics,
                "metric_trends": await self._calculate_metric_trends(
                    historical_metrics
                ),
                "performance_summary": await self._generate_performance_summary(
                    workflow_id=workflow_id,
                    current_metrics=perf_metrics,
                    historical_metrics=historical_metrics,
                ),
            }

            return metrics_data

        except Exception as e:
            logger.error(f"❌ Failed to get performance metrics: {e}")
            raise

    async def update_performance_metrics(self):
        """Update performance metrics for all workflows"""
        # Would implement real performance metrics updates
        pass

    async def cleanup_old_metrics(self):
        """Clean up old metrics from buffer"""
        cutoff_time = datetime.utcnow() - timedelta(hours=self.metrics_retention_hours)
        while self.metric_buffer and self.metric_buffer[0].timestamp < cutoff_time:
            self.metric_buffer.popleft()

    async def _aggregate_historical_metrics(
        self, historical_metrics: List[MetricPoint], time_range_minutes: int
    ) -> Dict[str, Any]:
        """Aggregate historical metrics"""
        if not historical_metrics:
            return {"average_value": 0.0, "max_value": 0.0, "min_value": 0.0}

        # Group metrics by type and name
        grouped_metrics = {}
        for metric in historical_metrics:
            key = f"{metric.metric_type.value}_{metric.metric_name}"
            if key not in grouped_metrics:
                grouped_metrics[key] = []

            # Only aggregate numeric values
            if isinstance(metric.value, (int, float)):
                grouped_metrics[key].append(metric.value)

        # Calculate aggregations
        aggregated = {}
        for key, values in grouped_metrics.items():
            if values:
                aggregated[key] = {
                    "count": len(values),
                    "average": statistics.mean(values),
                    "median": statistics.median(values),
                    "min": min(values),
                    "max": max(values),
                    "std_dev": statistics.stdev(values) if len(values) > 1 else 0.0,
                }

        return aggregated

    async def _collect_real_time_metrics(self, workflow_id: str) -> Dict[str, Any]:
        """Collect real-time metrics"""
        # Simplified real-time metrics collection
        return {
            "cpu_usage": 0.3,
            "memory_usage": 0.4,
            "network_io": 0.1,
            "disk_io": 0.2,
            "active_connections": 10,
        }

    async def _calculate_metric_trends(
        self, metrics: List[MetricPoint]
    ) -> Dict[str, Any]:
        """Calculate metric trends"""
        if len(metrics) < 2:
            return {"trend": "stable", "change_rate": 0.0}

        # Group numeric metrics by name
        metric_groups = {}
        for metric in metrics:
            if isinstance(metric.value, (int, float)):
                if metric.metric_name not in metric_groups:
                    metric_groups[metric.metric_name] = []
                metric_groups[metric.metric_name].append(
                    (metric.timestamp, metric.value)
                )

        trends = {}
        for metric_name, values in metric_groups.items():
            if len(values) >= 2:
                # Sort by timestamp
                values.sort(key=lambda x: x[0])

                # Calculate simple trend (comparing first and last values)
                first_value = values[0][1]
                last_value = values[-1][1]

                if first_value != 0:
                    change_rate = (last_value - first_value) / first_value
                else:
                    change_rate = 0.0

                if abs(change_rate) < 0.05:  # 5% threshold
                    trend = "stable"
                elif change_rate > 0:
                    trend = "increasing"
                else:
                    trend = "decreasing"

                trends[metric_name] = {
                    "trend": trend,
                    "change_rate": change_rate,
                    "direction": (
                        "up"
                        if change_rate > 0
                        else "down"
                        if change_rate < 0
                        else "stable"
                    ),
                }

        return trends

    async def _generate_performance_summary(
        self,
        workflow_id: str,
        current_metrics: Optional[PerformanceMetrics],
        historical_metrics: List[MetricPoint],
    ) -> Dict[str, Any]:
        """Generate performance summary"""
        summary = {
            "overall_performance": "good",
            "efficiency": 0.85,
            "recommendations": [],
        }

        if current_metrics:
            # Add current metrics analysis
            if current_metrics.error_rate > 0.1:
                summary["overall_performance"] = "poor"
                summary["recommendations"].append(
                    "High error rate detected - investigate failure causes"
                )

            if current_metrics.efficiency_score < 0.7:
                summary["recommendations"].append(
                    "Low efficiency score - consider workflow optimization"
                )

            if current_metrics.success_rate < 0.9:
                summary["recommendations"].append(
                    "Low success rate - review workflow reliability"
                )

        # Add historical analysis
        if len(historical_metrics) > 10:
            summary["data_points"] = len(historical_metrics)
            summary["monitoring_coverage"] = "good"
        else:
            summary["monitoring_coverage"] = "limited"
            summary["recommendations"].append("Increase monitoring data collection")

        return summary
