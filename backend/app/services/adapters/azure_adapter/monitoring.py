"""
Azure monitoring and metrics collection operations
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

from .auth import AzureAuthManager
from .exceptions import AZURE_SDK_AVAILABLE

logger = logging.getLogger(__name__)


class AzureMonitoringManager:
    """Manages Azure monitoring and metrics collection"""

    def __init__(self, auth_manager: AzureAuthManager):
        self.auth_manager = auth_manager

    async def test_monitor_connectivity(self) -> bool:
        """Test Azure Monitor API connectivity"""
        if not AZURE_SDK_AVAILABLE:
            return False

        try:
            # List metric definitions (basic monitor access)
            # This requires a resource, so we'll try with the subscription scope
            list(
                self.auth_manager.monitor_client.metric_definitions.list(
                    resource_uri=f"/subscriptions/{self.auth_manager.subscription_id}"
                )
            )
            return True
        except Exception:
            return False

    async def collect_performance_metrics(
        self, collected_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Collect Azure Monitor performance metrics for discovered resources"""
        try:
            metrics_data = {}
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=24)  # Last 24 hours

            # Collect metrics for Virtual Machines
            if "Microsoft.Compute/virtualMachines" in collected_data:
                vm_metrics = await self.collect_vm_metrics(
                    collected_data["Microsoft.Compute/virtualMachines"]["resources"],
                    start_time,
                    end_time,
                )
                metrics_data["VirtualMachines"] = vm_metrics

            # Collect metrics for SQL Databases
            if "Microsoft.Sql/servers/databases" in collected_data:
                sql_metrics = await self.collect_sql_metrics(
                    collected_data["Microsoft.Sql/servers/databases"]["resources"],
                    start_time,
                    end_time,
                )
                metrics_data["SqlDatabases"] = sql_metrics

            # Collect metrics for Web Apps
            if "Microsoft.Web/sites" in collected_data:
                web_metrics = await self.collect_web_app_metrics(
                    collected_data["Microsoft.Web/sites"]["resources"],
                    start_time,
                    end_time,
                )
                metrics_data["WebApps"] = web_metrics

            return metrics_data

        except Exception as e:
            raise Exception(f"Performance metrics collection failed: {str(e)}")

    async def collect_vm_metrics(
        self, vms: List[Dict], start_time: datetime, end_time: datetime
    ) -> List[Dict]:
        """Collect Azure Monitor metrics for Virtual Machines"""
        metrics = []

        for vm in vms:
            resource_id = vm.get("id")
            if not resource_id:
                continue

            try:
                vm_metrics = await self._collect_single_vm_metrics(
                    vm, resource_id, start_time, end_time
                )
                metrics.append(vm_metrics)

            except Exception as e:
                logger.warning(
                    f"Failed to collect metrics for VM {vm.get('name')}: {str(e)}"
                )

        return metrics

    async def _collect_single_vm_metrics(
        self, vm: Dict, resource_id: str, start_time: datetime, end_time: datetime
    ) -> Dict:
        """Collect metrics for a single VM"""
        metric_names = [
            "Percentage CPU",
            "Network In Total",
            "Network Out Total",
            "Disk Read Bytes",
            "Disk Write Bytes",
        ]

        vm_metrics = {
            "resource_id": resource_id,
            "resource_type": "VirtualMachine",
            "resource_name": vm.get("name"),
            "timestamp": datetime.utcnow().isoformat(),
        }

        for metric_name in metric_names:
            try:
                avg_value = await self._get_metric_average(
                    resource_id, metric_name, start_time, end_time
                )
                if avg_value is not None:
                    self._map_vm_metric_value(vm_metrics, metric_name, avg_value)

            except Exception as e:
                logger.warning(
                    f"Failed to collect {metric_name} for VM {vm.get('name')}: {str(e)}"
                )

        return vm_metrics

    async def _get_metric_average(
        self,
        resource_id: str,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
    ) -> float:
        """Get average value for a specific metric"""
        metric_data = self.auth_manager.monitor_client.metrics.list(
            resource_uri=resource_id,
            timespan=f"{start_time.isoformat()}/{end_time.isoformat()}",
            interval="PT1H",  # 1 hour intervals
            metricnames=metric_name,
            aggregation="Average",
        )

        if not metric_data.value:
            return None

        metric_values = []
        for metric in metric_data.value:
            if metric.timeseries:
                for timeseries in metric.timeseries:
                    if timeseries.data:
                        metric_values.extend(
                            [
                                data.average
                                for data in timeseries.data
                                if data.average is not None
                            ]
                        )

        return sum(metric_values) / len(metric_values) if metric_values else None

    def _map_vm_metric_value(
        self, vm_metrics: Dict, metric_name: str, avg_value: float
    ):
        """Map metric names to standard fields"""
        metric_mapping = {
            "Percentage CPU": "cpu_percentage",
            "Network In Total": "network_in",
            "Network Out Total": "network_out",
            "Disk Read Bytes": "disk_read_bytes",
            "Disk Write Bytes": "disk_write_bytes",
        }

        field_name = metric_mapping.get(metric_name)
        if field_name:
            vm_metrics[field_name] = avg_value

    async def collect_sql_metrics(
        self, databases: List[Dict], start_time: datetime, end_time: datetime
    ) -> List[Dict]:
        """Collect Azure Monitor metrics for SQL Databases"""
        metrics = []

        for db in databases:
            resource_id = db.get("id")
            if not resource_id:
                continue

            try:
                # Define metrics to collect for SQL databases
                metric_names = [
                    "cpu_percent",
                    "dtu_consumption_percent",
                    "storage_percent",
                    "connection_successful",
                    "connection_failed",
                ]

                db_metrics = {
                    "resource_id": resource_id,
                    "resource_type": "SqlDatabase",
                    "resource_name": db.get("name"),
                    "timestamp": datetime.utcnow().isoformat(),
                }

                # Collect each metric
                for metric_name in metric_names:
                    try:
                        metric_data = self.auth_manager.monitor_client.metrics.list(
                            resource_uri=resource_id,
                            timespan=f"{start_time.isoformat()}/{end_time.isoformat()}",
                            interval="PT1H",
                            metricnames=metric_name,
                            aggregation="Average",
                        )

                        if metric_data.value:
                            metric_values = []
                            for metric in metric_data.value:
                                if metric.timeseries:
                                    for timeseries in metric.timeseries:
                                        if timeseries.data:
                                            metric_values.extend(
                                                [
                                                    data.average
                                                    for data in timeseries.data
                                                    if data.average is not None
                                                ]
                                            )

                            if metric_values:
                                avg_value = sum(metric_values) / len(metric_values)
                                db_metrics[metric_name] = avg_value

                    except Exception as e:
                        logger.warning(
                            f"Failed to collect {metric_name} for SQL DB {db.get('name')}: {str(e)}"
                        )

                metrics.append(db_metrics)

            except Exception as e:
                logger.warning(
                    f"Failed to collect metrics for SQL DB {db.get('name')}: {str(e)}"
                )

        return metrics

    async def collect_web_app_metrics(
        self, web_apps: List[Dict], start_time: datetime, end_time: datetime
    ) -> List[Dict]:
        """Collect Azure Monitor metrics for Web Apps"""
        metrics = []

        for app in web_apps:
            resource_id = app.get("id")
            if not resource_id:
                continue

            try:
                # Define metrics to collect for web apps
                metric_names = [
                    "CpuTime",
                    "Requests",
                    "BytesReceived",
                    "BytesSent",
                    "Http2xx",
                    "Http4xx",
                    "Http5xx",
                    "ResponseTime",
                ]

                app_metrics = {
                    "resource_id": resource_id,
                    "resource_type": "WebApp",
                    "resource_name": app.get("name"),
                    "timestamp": datetime.utcnow().isoformat(),
                }

                # Collect each metric
                for metric_name in metric_names:
                    try:
                        metric_data = self.auth_manager.monitor_client.metrics.list(
                            resource_uri=resource_id,
                            timespan=f"{start_time.isoformat()}/{end_time.isoformat()}",
                            interval="PT1H",
                            metricnames=metric_name,
                            aggregation=(
                                "Total"
                                if metric_name
                                in [
                                    "Requests",
                                    "Http2xx",
                                    "Http4xx",
                                    "Http5xx",
                                    "BytesReceived",
                                    "BytesSent",
                                ]
                                else "Average"
                            ),
                        )

                        if metric_data.value:
                            metric_values = []
                            for metric in metric_data.value:
                                if metric.timeseries:
                                    for timeseries in metric.timeseries:
                                        if timeseries.data:
                                            metric_values.extend(
                                                [
                                                    (
                                                        data.total
                                                        if metric_name
                                                        in [
                                                            "Requests",
                                                            "Http2xx",
                                                            "Http4xx",
                                                            "Http5xx",
                                                            "BytesReceived",
                                                            "BytesSent",
                                                        ]
                                                        else data.average
                                                    )
                                                    for data in timeseries.data
                                                    if (
                                                        data.total
                                                        if metric_name
                                                        in [
                                                            "Requests",
                                                            "Http2xx",
                                                            "Http4xx",
                                                            "Http5xx",
                                                            "BytesReceived",
                                                            "BytesSent",
                                                        ]
                                                        else data.average
                                                    )
                                                    is not None
                                                ]
                                            )

                            if metric_values:
                                if metric_name in [
                                    "Requests",
                                    "Http2xx",
                                    "Http4xx",
                                    "Http5xx",
                                    "BytesReceived",
                                    "BytesSent",
                                ]:
                                    app_metrics[metric_name.lower()] = sum(
                                        metric_values
                                    )
                                else:
                                    app_metrics[metric_name.lower()] = sum(
                                        metric_values
                                    ) / len(metric_values)

                    except Exception as e:
                        logger.warning(
                            f"Failed to collect {metric_name} for Web App {app.get('name')}: {str(e)}"
                        )

                metrics.append(app_metrics)

            except Exception as e:
                logger.warning(
                    f"Failed to collect metrics for Web App {app.get('name')}: {str(e)}"
                )

        return metrics

    def transform_metrics(self, metrics_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform Azure Monitor metrics to normalized format"""
        normalized_metrics = {}

        for service, service_metrics in metrics_data.items():
            if isinstance(service_metrics, list):
                normalized_metrics[service] = []
                for metric in service_metrics:
                    normalized_metric = {
                        "resource_id": metric.get("resource_id"),
                        "resource_type": metric.get("resource_type"),
                        "resource_name": metric.get("resource_name"),
                        "timestamp": metric.get("timestamp"),
                        "metrics": {},
                    }

                    # Normalize metric names
                    for key, value in metric.items():
                        if (
                            key
                            not in [
                                "resource_id",
                                "resource_type",
                                "resource_name",
                                "timestamp",
                            ]
                            and value is not None
                        ):
                            normalized_metric["metrics"][key] = value

                    normalized_metrics[service].append(normalized_metric)

        return normalized_metrics
