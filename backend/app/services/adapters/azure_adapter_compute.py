"""
Azure Compute Operations Module for ADCS Implementation

This module handles Azure compute resource operations including Virtual Machines
and Web Apps. Provides detailed resource enhancement and performance metrics
collection for compute workloads.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from azure.mgmt.compute import ComputeManagementClient
    from azure.mgmt.monitor import MonitorManagementClient
    from azure.mgmt.web import WebSiteManagementClient

    AZURE_SDK_AVAILABLE = True
except ImportError:
    AZURE_SDK_AVAILABLE = False
    ComputeManagementClient = MonitorManagementClient = WebSiteManagementClient = None

logger = logging.getLogger(__name__)


class AzureComputeOperations:
    """
    Azure Compute Operations for ADCS Implementation

    Handles Virtual Machine and Web App resource enhancement, metrics collection,
    and detailed compute resource information gathering.
    """

    def __init__(
        self,
        compute_client: ComputeManagementClient,
        web_client: WebSiteManagementClient,
        monitor_client: MonitorManagementClient,
    ):
        """
        Initialize Azure compute operations

        Args:
            compute_client: Azure Compute Management client
            web_client: Azure Web Site Management client
            monitor_client: Azure Monitor Management client
        """
        self._compute_client = compute_client
        self._web_client = web_client
        self._monitor_client = monitor_client

    async def enhance_vm_data(self, vm_resource: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance VM data with detailed compute information

        Args:
            vm_resource: Basic VM resource data from Resource Graph

        Returns:
            Enhanced VM data with detailed compute properties
        """
        try:
            # Parse resource ID to get resource group and VM name
            resource_id = vm_resource.get("id", "")
            parts = resource_id.split("/")

            if len(parts) >= 9:
                resource_group = parts[4]
                vm_name = parts[8]

                # Get detailed VM information
                vm = self._compute_client.virtual_machines.get(
                    resource_group_name=resource_group,
                    vm_name=vm_name,
                    expand="instanceView",
                )

                return {
                    "vm_size": (
                        vm.hardware_profile.vm_size if vm.hardware_profile else None
                    ),
                    "os_type": (
                        vm.storage_profile.os_disk.os_type
                        if vm.storage_profile and vm.storage_profile.os_disk
                        else None
                    ),
                    "os_disk_size": (
                        vm.storage_profile.os_disk.disk_size_gb
                        if vm.storage_profile and vm.storage_profile.os_disk
                        else None
                    ),
                    "data_disks_count": (
                        len(vm.storage_profile.data_disks)
                        if vm.storage_profile and vm.storage_profile.data_disks
                        else 0
                    ),
                    "network_interfaces": (
                        [nic.id for nic in vm.network_profile.network_interfaces]
                        if vm.network_profile and vm.network_profile.network_interfaces
                        else []
                    ),
                    "provisioning_state": vm.provisioning_state,
                    "power_state": (
                        self._get_vm_power_state(vm.instance_view)
                        if vm.instance_view
                        else None
                    ),
                    "computer_name": (
                        vm.os_profile.computer_name if vm.os_profile else None
                    ),
                    "admin_username": (
                        vm.os_profile.admin_username if vm.os_profile else None
                    ),
                    "zones": vm.zones,
                    "availability_set": (
                        vm.availability_set.id if vm.availability_set else None
                    ),
                }

        except Exception as e:
            logger.warning(
                f"Failed to enhance VM data for {vm_resource.get('name')}: {str(e)}"
            )

        return {}

    async def enhance_web_app_data(
        self, app_resource: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enhance web app data with detailed information

        Args:
            app_resource: Basic web app resource data from Resource Graph

        Returns:
            Enhanced web app data with detailed application properties
        """
        try:
            # Parse resource ID
            resource_id = app_resource.get("id", "")
            parts = resource_id.split("/")

            if len(parts) >= 9:
                resource_group = parts[4]
                app_name = parts[8]

                # Get detailed web app information
                web_app = self._web_client.web_apps.get(
                    resource_group_name=resource_group, name=app_name
                )

                return {
                    "kind": web_app.kind,
                    "state": web_app.state,
                    "host_names": web_app.host_names,
                    "enabled": web_app.enabled,
                    "availability_state": web_app.availability_state,
                    "server_farm_id": web_app.server_farm_id,
                    "default_host_name": web_app.default_host_name,
                    "https_only": web_app.https_only,
                    "site_config": (
                        {
                            "app_settings": (
                                getattr(web_app.site_config, "app_settings", None)
                                if web_app.site_config
                                else None
                            ),
                            "connection_strings": (
                                getattr(web_app.site_config, "connection_strings", None)
                                if web_app.site_config
                                else None
                            ),
                            "default_documents": (
                                getattr(web_app.site_config, "default_documents", None)
                                if web_app.site_config
                                else None
                            ),
                            "net_framework_version": (
                                getattr(
                                    web_app.site_config, "net_framework_version", None
                                )
                                if web_app.site_config
                                else None
                            ),
                            "php_version": (
                                getattr(web_app.site_config, "php_version", None)
                                if web_app.site_config
                                else None
                            ),
                            "python_version": (
                                getattr(web_app.site_config, "python_version", None)
                                if web_app.site_config
                                else None
                            ),
                            "node_version": (
                                getattr(web_app.site_config, "node_version", None)
                                if web_app.site_config
                                else None
                            ),
                            "java_version": (
                                getattr(web_app.site_config, "java_version", None)
                                if web_app.site_config
                                else None
                            ),
                        }
                        if web_app.site_config
                        else {}
                    ),
                }

        except Exception as e:
            logger.warning(
                f"Failed to enhance web app data for {app_resource.get('name')}: {str(e)}"
            )

        return {}

    def _get_vm_metric_names(self) -> List[str]:
        """Get list of VM metrics to collect"""
        return [
            "Percentage CPU",
            "Network In Total",
            "Network Out Total",
            "Disk Read Bytes",
            "Disk Write Bytes",
        ]

    def _create_vm_base_metrics(self, vm: Dict) -> Dict:
        """Create base metrics structure for VM"""
        return {
            "resource_id": vm.get("id"),
            "resource_type": "VirtualMachine",
            "resource_name": vm.get("name"),
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _extract_metric_values_from_response(self, metric_data) -> List[float]:
        """Extract metric values from Azure Monitor response"""
        metric_values = []
        if metric_data.value:
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
        return metric_values

    def _map_vm_metric_to_field(self, metric_name: str, avg_value: float, vm_metrics: Dict) -> None:
        """Map Azure metric name to standard field"""
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

    async def _collect_single_vm_metric_value(
        self, resource_id: str, metric_name: str, start_time: datetime, end_time: datetime
    ) -> Optional[float]:
        """Collect a single metric for a VM"""
        try:
            metric_data = self._monitor_client.metrics.list(
                resource_uri=resource_id,
                timespan=f"{start_time.isoformat()}/{end_time.isoformat()}",
                interval="PT1H",  # 1 hour intervals
                metricnames=metric_name,
                aggregation="Average",
            )

            metric_values = self._extract_metric_values_from_response(metric_data)
            if metric_values:
                return sum(metric_values) / len(metric_values)
        except Exception as e:
            logger.warning(f"Failed to collect {metric_name}: {str(e)}")
        return None

    async def collect_vm_metrics(
        self, vms: List[Dict], start_time: datetime, end_time: datetime
    ) -> List[Dict]:
        """
        Collect Azure Monitor metrics for Virtual Machines

        Args:
            vms: List of VM resource dictionaries
            start_time: Start time for metrics collection
            end_time: End time for metrics collection

        Returns:
            List of VM performance metrics
        """
        metrics = []
        metric_names = self._get_vm_metric_names()

        for vm in vms:
            resource_id = vm.get("id")
            if not resource_id:
                continue

            try:
                vm_metrics = self._create_vm_base_metrics(vm)

                # Collect each metric
                for metric_name in metric_names:
                    avg_value = await self._collect_single_vm_metric_value(
                        resource_id, metric_name, start_time, end_time
                    )
                    if avg_value is not None:
                        self._map_vm_metric_to_field(metric_name, avg_value, vm_metrics)

                metrics.append(vm_metrics)

            except Exception as e:
                logger.warning(
                    f"Failed to collect metrics for VM {vm.get('name')}: {str(e)}"
                )

        return metrics

    async def collect_web_app_metrics(
        self, web_apps: List[Dict], start_time: datetime, end_time: datetime
    ) -> List[Dict]:
        """
        Collect Azure Monitor metrics for Web Apps

        Args:
            web_apps: List of web app resource dictionaries
            start_time: Start time for metrics collection
            end_time: End time for metrics collection

        Returns:
            List of web app performance metrics
        """
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
                        metric_data = self._monitor_client.metrics.list(
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

    def _get_vm_power_state(self, instance_view) -> Optional[str]:
        """
        Extract VM power state from instance view

        Args:
            instance_view: VM instance view from Azure API

        Returns:
            VM power state string or None
        """
        if instance_view and instance_view.statuses:
            for status in instance_view.statuses:
                if status.code and status.code.startswith("PowerState/"):
                    return status.code.replace("PowerState/", "")
        return None
