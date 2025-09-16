"""
Metrics export functionality for performance metrics collection.

This module provides capabilities for exporting metrics in various formats,
primarily focusing on Prometheus format for integration with monitoring
and observability systems.
"""

from typing import Dict, Any
from datetime import datetime

from .aggregators import Counter, Gauge, Histogram


class PrometheusExporter:
    """Exports metrics in Prometheus format"""

    @staticmethod
    def export_metrics(
        counters: Dict[str, Counter],
        gauges: Dict[str, Gauge],
        histograms: Dict[str, Histogram],
    ) -> str:
        """Export all metrics in Prometheus format"""
        lines = []

        # Export counters
        for counter in counters.values():
            lines.append(f"# HELP {counter.name} {counter.description}")
            lines.append(f"# TYPE {counter.name} counter")
            for sample in counter.get_samples():
                label_str = ""
                if sample.labels:
                    label_pairs = [f'{k}="{v}"' for k, v in sample.labels.items()]
                    label_str = "{" + ",".join(label_pairs) + "}"
                lines.append(
                    f"{counter.name}{label_str} {sample.value} {int(sample.timestamp * 1000)}"
                )

        # Export gauges
        for gauge in gauges.values():
            lines.append(f"# HELP {gauge.name} {gauge.description}")
            lines.append(f"# TYPE {gauge.name} gauge")
            for sample in gauge.get_samples():
                label_str = ""
                if sample.labels:
                    label_pairs = [f'{k}="{v}"' for k, v in sample.labels.items()]
                    label_str = "{" + ",".join(label_pairs) + "}"
                lines.append(
                    f"{gauge.name}{label_str} {sample.value} {int(sample.timestamp * 1000)}"
                )

        # Export histograms
        for histogram in histograms.values():
            lines.append(f"# HELP {histogram.name} {histogram.description}")
            lines.append(f"# TYPE {histogram.name} histogram")
            for sample in histogram.get_samples():
                metric_name = sample.labels.pop("__name__", histogram.name)
                label_str = ""
                if sample.labels:
                    label_pairs = [f'{k}="{v}"' for k, v in sample.labels.items()]
                    label_str = "{" + ",".join(label_pairs) + "}"
                lines.append(
                    f"{metric_name}{label_str} {sample.value} {int(sample.timestamp * 1000)}"
                )

        return "\n".join(lines)


class PerformanceSummaryExporter:
    """Exports performance summary data"""

    @staticmethod
    def export_performance_summary(
        counters: Dict[str, Counter],
        gauges: Dict[str, Gauge],
        histograms: Dict[str, Histogram],
    ) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        summary = {
            "timestamp": datetime.utcnow().isoformat(),
            "metrics_count": {
                "counters": len(counters),
                "gauges": len(gauges),
                "histograms": len(histograms),
            },
            "auth_performance": {},
            "cache_performance": {},
            "system_performance": {},
        }

        # Authentication performance summary
        login_histogram = histograms.get("auth_login_duration_seconds")
        if login_histogram:
            summary["auth_performance"]["login"] = {
                "average_duration_ms": login_histogram.get_average() * 1000,
                "p95_duration_ms": login_histogram.get_percentile(95) * 1000,
                "p99_duration_ms": login_histogram.get_percentile(99) * 1000,
                "total_attempts": login_histogram.get_count(),
            }

        session_histogram = histograms.get("auth_session_validation_duration_seconds")
        if session_histogram:
            summary["auth_performance"]["session_validation"] = {
                "average_duration_ms": session_histogram.get_average() * 1000,
                "p95_duration_ms": session_histogram.get_percentile(95) * 1000,
                "total_validations": session_histogram.get_count(),
            }

        context_histogram = histograms.get("auth_context_switch_duration_seconds")
        if context_histogram:
            summary["auth_performance"]["context_switching"] = {
                "average_duration_ms": context_histogram.get_average() * 1000,
                "p95_duration_ms": context_histogram.get_percentile(95) * 1000,
                "total_switches": context_histogram.get_count(),
            }

        # Cache performance summary
        cache_ops_histogram = histograms.get("cache_operation_duration_seconds")
        if cache_ops_histogram:
            summary["cache_performance"]["operations"] = {
                "average_duration_ms": cache_ops_histogram.get_average() * 1000,
                "p95_duration_ms": cache_ops_histogram.get_percentile(95) * 1000,
                "total_operations": cache_ops_histogram.get_count(),
            }

        hit_ratio_gauge = gauges.get("cache_hit_ratio")
        if hit_ratio_gauge:
            summary["cache_performance"]["hit_ratio"] = hit_ratio_gauge.get_value()

        # System performance summary
        active_sessions_gauge = gauges.get("auth_active_sessions")
        if active_sessions_gauge:
            summary["system_performance"][
                "active_sessions"
            ] = active_sessions_gauge.get_value()

        cpu_gauge = gauges.get("system_cpu_usage_percent")
        if cpu_gauge:
            summary["system_performance"]["cpu_usage"] = cpu_gauge.get_value()

        return summary
