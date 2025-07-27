"""
GCP Metrics Collection

Handles performance metrics collection using Cloud Monitoring.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

from .auth import GCPAuthManager
from .constants import COMPUTE_METRICS, FUNCTION_METRICS, SQL_METRICS
from .dependencies import monitoring_v3


class GCPMetricsCollector:
    """Collects performance metrics using Cloud Monitoring"""

    def __init__(self, auth_manager: GCPAuthManager):
        self.auth_manager = auth_manager
        self.logger = logging.getLogger(__name__)

    async def collect_performance_metrics(
        self, collected_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Collect Cloud Monitoring performance metrics for discovered resources"""
        try:
            metrics_data = {}
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=24)  # Last 24 hours

            # Collect metrics for Compute Instances
            if "compute.googleapis.com/Instance" in collected_data:
                compute_metrics = await self.collect_compute_metrics(
                    collected_data["compute.googleapis.com/Instance"]["resources"],
                    start_time,
                    end_time,
                )
                metrics_data["ComputeInstances"] = compute_metrics

            # Collect metrics for Cloud SQL Instances
            if "sqladmin.googleapis.com/Instance" in collected_data:
                sql_metrics = await self.collect_sql_metrics(
                    collected_data["sqladmin.googleapis.com/Instance"]["resources"],
                    start_time,
                    end_time,
                )
                metrics_data["SqlInstances"] = sql_metrics

            # Collect metrics for Cloud Functions
            if "cloudfunctions.googleapis.com/CloudFunction" in collected_data:
                function_metrics = await self.collect_function_metrics(
                    collected_data["cloudfunctions.googleapis.com/CloudFunction"][
                        "resources"
                    ],
                    start_time,
                    end_time,
                )
                metrics_data["CloudFunctions"] = function_metrics

            return metrics_data

        except Exception as e:
            raise Exception(f"Performance metrics collection failed: {str(e)}")

    async def collect_compute_metrics(
        self, instances: List[Dict], start_time: datetime, end_time: datetime
    ) -> List[Dict]:
        """Collect Cloud Monitoring metrics for Compute Engine instances"""
        metrics = []

        for instance in instances:
            asset_name = instance.get("name", "")
            if "/instances/" not in asset_name:
                continue

            # Extract instance details
            parts = asset_name.split("/")
            if len(parts) >= 6:
                parts[2]
                zone = parts[4]
                instance_name = parts[6]

                try:
                    instance_metrics = {
                        "resource_id": asset_name,
                        "resource_type": "ComputeInstance",
                        "resource_name": instance_name,
                        "zone": zone,
                        "timestamp": datetime.utcnow().isoformat(),
                    }

                    # Collect each metric
                    for metric_type in COMPUTE_METRICS:
                        try:
                            # Build time series request
                            interval = monitoring_v3.TimeInterval(
                                {
                                    "end_time": {"seconds": int(end_time.timestamp())},
                                    "start_time": {
                                        "seconds": int(start_time.timestamp())
                                    },
                                }
                            )

                            request = monitoring_v3.ListTimeSeriesRequest(
                                name=f"projects/{self.auth_manager.project_id}",
                                filter=f'metric.type="{metric_type}" AND resource.labels.instance_id="{instance_name}" AND resource.labels.zone="{zone}"',
                                interval=interval,
                                view=monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
                            )

                            results = (
                                self.auth_manager.monitoring_client.list_time_series(
                                    request=request
                                )
                            )

                            # Process results
                            values = []
                            for result in results:
                                for point in result.points:
                                    if point.value.double_value is not None:
                                        values.append(point.value.double_value)
                                    elif point.value.int64_value is not None:
                                        values.append(float(point.value.int64_value))

                            if values:
                                avg_value = sum(values) / len(values)

                                # Map metric types to standard fields
                                if "cpu/utilization" in metric_type:
                                    instance_metrics["cpu_utilization"] = (
                                        avg_value * 100
                                    )  # Convert to percentage
                                elif "network/received_bytes_count" in metric_type:
                                    instance_metrics["network_received_bytes"] = (
                                        avg_value
                                    )
                                elif "network/sent_bytes_count" in metric_type:
                                    instance_metrics["network_sent_bytes"] = avg_value
                                elif "disk/read_bytes_count" in metric_type:
                                    instance_metrics["disk_read_bytes"] = avg_value
                                elif "disk/write_bytes_count" in metric_type:
                                    instance_metrics["disk_write_bytes"] = avg_value

                        except Exception as e:
                            self.logger.warning(
                                f"Failed to collect {metric_type} for instance {instance_name}: {str(e)}"
                            )

                    metrics.append(instance_metrics)

                except Exception as e:
                    self.logger.warning(
                        f"Failed to collect metrics for instance {instance_name}: {str(e)}"
                    )

        return metrics

    async def collect_sql_metrics(
        self, instances: List[Dict], start_time: datetime, end_time: datetime
    ) -> List[Dict]:
        """Collect Cloud Monitoring metrics for Cloud SQL instances"""
        metrics = []

        for instance in instances:
            asset_name = instance.get("name", "")
            if "/instances/" not in asset_name:
                continue

            instance_name = asset_name.split("/")[-1]

            try:
                sql_metrics = {
                    "resource_id": asset_name,
                    "resource_type": "SqlInstance",
                    "resource_name": instance_name,
                    "timestamp": datetime.utcnow().isoformat(),
                }

                # Collect each metric
                for metric_type in SQL_METRICS:
                    try:
                        # Build time series request
                        interval = monitoring_v3.TimeInterval(
                            {
                                "end_time": {"seconds": int(end_time.timestamp())},
                                "start_time": {"seconds": int(start_time.timestamp())},
                            }
                        )

                        request = monitoring_v3.ListTimeSeriesRequest(
                            name=f"projects/{self.auth_manager.project_id}",
                            filter=f'metric.type="{metric_type}" AND resource.labels.database_id="{self.auth_manager.project_id}:{instance_name}"',
                            interval=interval,
                            view=monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
                        )

                        results = self.auth_manager.monitoring_client.list_time_series(
                            request=request
                        )

                        # Process results
                        values = []
                        for result in results:
                            for point in result.points:
                                if point.value.double_value is not None:
                                    values.append(point.value.double_value)
                                elif point.value.int64_value is not None:
                                    values.append(float(point.value.int64_value))

                        if values:
                            avg_value = sum(values) / len(values)

                            # Map metric types to standard fields
                            if "cpu/utilization" in metric_type:
                                sql_metrics["cpu_utilization"] = avg_value * 100
                            elif "memory/utilization" in metric_type:
                                sql_metrics["memory_utilization"] = avg_value * 100
                            elif "disk/utilization" in metric_type:
                                sql_metrics["disk_utilization"] = avg_value * 100
                            elif "network/received_bytes_count" in metric_type:
                                sql_metrics["network_received_bytes"] = avg_value
                            elif "network/sent_bytes_count" in metric_type:
                                sql_metrics["network_sent_bytes"] = avg_value

                    except Exception as e:
                        self.logger.warning(
                            f"Failed to collect {metric_type} for SQL instance {instance_name}: {str(e)}"
                        )

                metrics.append(sql_metrics)

            except Exception as e:
                self.logger.warning(
                    f"Failed to collect metrics for SQL instance {instance_name}: {str(e)}"
                )

        return metrics

    async def collect_function_metrics(
        self, functions: List[Dict], start_time: datetime, end_time: datetime
    ) -> List[Dict]:
        """Collect Cloud Monitoring metrics for Cloud Functions"""
        metrics = []

        for function in functions:
            asset_name = function.get("name", "")
            if "/functions/" not in asset_name:
                continue

            function_name = asset_name.split("/")[-1]

            try:
                function_metrics = {
                    "resource_id": asset_name,
                    "resource_type": "CloudFunction",
                    "resource_name": function_name,
                    "timestamp": datetime.utcnow().isoformat(),
                }

                # Collect each metric
                for metric_type in FUNCTION_METRICS:
                    try:
                        # Build time series request
                        interval = monitoring_v3.TimeInterval(
                            {
                                "end_time": {"seconds": int(end_time.timestamp())},
                                "start_time": {"seconds": int(start_time.timestamp())},
                            }
                        )

                        request = monitoring_v3.ListTimeSeriesRequest(
                            name=f"projects/{self.auth_manager.project_id}",
                            filter=f'metric.type="{metric_type}" AND resource.labels.function_name="{function_name}"',
                            interval=interval,
                            view=monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
                        )

                        results = self.auth_manager.monitoring_client.list_time_series(
                            request=request
                        )

                        # Process results
                        values = []
                        for result in results:
                            for point in result.points:
                                if point.value.double_value is not None:
                                    values.append(point.value.double_value)
                                elif point.value.int64_value is not None:
                                    values.append(float(point.value.int64_value))

                        if values:
                            if "executions" in metric_type:
                                function_metrics["executions"] = sum(values)
                            else:
                                avg_value = sum(values) / len(values)

                                if "execution_times" in metric_type:
                                    function_metrics["average_execution_time_ms"] = (
                                        avg_value / 1000000
                                    )  # Convert from nanoseconds to milliseconds
                                elif "user_memory_bytes" in metric_type:
                                    function_metrics["memory_usage_bytes"] = avg_value
                                elif "network_egress" in metric_type:
                                    function_metrics["network_egress_bytes"] = avg_value

                    except Exception as e:
                        self.logger.warning(
                            f"Failed to collect {metric_type} for function {function_name}: {str(e)}"
                        )

                metrics.append(function_metrics)

            except Exception as e:
                self.logger.warning(
                    f"Failed to collect metrics for function {function_name}: {str(e)}"
                )

        return metrics
