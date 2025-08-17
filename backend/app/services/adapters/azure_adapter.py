"""
Azure Platform Adapter for ADCS Implementation

This adapter provides comprehensive Azure resource discovery and data collection
using Azure Resource Graph for resource discovery and Azure Monitor for metrics.

The adapter is modularized across multiple specialized modules:
- azure_adapter_auth: Authentication and client management
- azure_adapter_compute: Compute resource operations (VMs, Web Apps)
- azure_adapter_storage: Storage resource operations (Storage Accounts)
- azure_adapter_data: Data resource operations (SQL Databases)
- azure_adapter_utils: Utility functions and helper operations
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set

try:
    from azure.core.exceptions import ClientAuthenticationError, HttpResponseError
    from azure.identity import ClientSecretCredential, DefaultAzureCredential
    from azure.mgmt.compute import ComputeManagementClient
    from azure.mgmt.monitor import MonitorManagementClient
    from azure.mgmt.network import NetworkManagementClient
    from azure.mgmt.resource import ResourceManagementClient
    from azure.mgmt.resourcegraph import ResourceGraphClient
    from azure.mgmt.sql import SqlManagementClient
    from azure.mgmt.storage import StorageManagementClient
    from azure.mgmt.web import WebSiteManagementClient

    AZURE_SDK_AVAILABLE = True
except ImportError:
    AZURE_SDK_AVAILABLE = False
    # Create dummy classes for type hints
    ClientSecretCredential = DefaultAzureCredential = None
    ResourceManagementClient = ResourceGraphClient = MonitorManagementClient = None
    ComputeManagementClient = SqlManagementClient = WebSiteManagementClient = None
    StorageManagementClient = NetworkManagementClient = None
    ClientAuthenticationError = HttpResponseError = Exception

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.collection_flow import AutomationTier
from app.services.collection_flow.adapters import (
    AdapterCapability,
    AdapterMetadata,
    BaseAdapter,
    CollectionRequest,
    CollectionResponse,
)

# Import modularized components
from .azure_adapter_auth import AzureAuthenticationManager, AzureCredentials
from .azure_adapter_compute import AzureComputeOperations
from .azure_adapter_storage import AzureStorageOperations
from .azure_adapter_data import AzureDataOperations
from .azure_adapter_utils import AzureUtilities

logger = logging.getLogger(__name__)


class AzureAdapter(BaseAdapter):
    """
    Azure Platform Adapter implementing BaseAdapter interface

    Provides comprehensive Azure resource discovery using:
    - Azure Resource Graph for efficient resource queries
    - Azure Monitor for performance metrics
    - Resource Management APIs for detailed resource information
    - Support for VMs, databases, web apps, storage, and networking resources

    The adapter uses dependency injection with specialized modules:
    - AzureAuthenticationManager: Handles authentication and client management
    - AzureComputeOperations: Manages compute resources (VMs, Web Apps)
    - AzureStorageOperations: Manages storage resources (Storage Accounts)
    - AzureDataOperations: Manages data resources (SQL Databases)
    - AzureUtilities: Provides utility functions and helpers
    """

    def __init__(self, db: AsyncSession, metadata: AdapterMetadata):
        """Initialize Azure adapter with metadata and session"""
        super().__init__(db, metadata)
        if not AZURE_SDK_AVAILABLE:
            logger.warning(
                "Azure SDK is not installed. Azure adapter functionality will be limited."
            )

        # Initialize modular components
        self._auth_manager: Optional[AzureAuthenticationManager] = None
        self._compute_ops: Optional[AzureComputeOperations] = None
        self._storage_ops: Optional[AzureStorageOperations] = None
        self._data_ops: Optional[AzureDataOperations] = None
        self._utilities: Optional[AzureUtilities] = None

        self._supported_resource_types = {
            "Microsoft.Compute/virtualMachines",
            "Microsoft.Sql/servers",
            "Microsoft.Sql/servers/databases",
            "Microsoft.Web/sites",
            "Microsoft.Storage/storageAccounts",
            "Microsoft.Network/loadBalancers",
            "Microsoft.Network/applicationGateways",
            "Microsoft.ContainerService/managedClusters",
            "Microsoft.Cache/Redis",
            "Microsoft.DocumentDB/databaseAccounts",
            "Microsoft.Network/virtualNetworks",
            "Microsoft.Network/networkSecurityGroups",
        }

    def _initialize_modules(
        self, credential: ClientSecretCredential, subscription_id: str
    ) -> None:
        """
        Initialize all modular components with Azure clients

        Args:
            credential: Azure credential for authentication
            subscription_id: Azure subscription ID
        """
        # Initialize authentication manager
        self._auth_manager = AzureAuthenticationManager()
        self._auth_manager.init_clients(credential, subscription_id)

        # Initialize compute operations
        self._compute_ops = AzureComputeOperations(
            compute_client=self._auth_manager.compute_client,
            web_client=self._auth_manager.web_client,
            monitor_client=self._auth_manager.monitor_client,
        )

        # Initialize storage operations
        self._storage_ops = AzureStorageOperations(
            storage_client=self._auth_manager.storage_client
        )

        # Initialize data operations
        self._data_ops = AzureDataOperations(
            sql_client=self._auth_manager.sql_client,
            monitor_client=self._auth_manager.monitor_client,
        )

        # Initialize utilities
        self._utilities = AzureUtilities(
            network_client=self._auth_manager.network_client,
            resource_graph_client=self._auth_manager.resource_graph_client,
            subscription_id=subscription_id,
        )

    def _get_azure_credential(
        self, credentials: AzureCredentials
    ) -> ClientSecretCredential:
        """Create Azure credential from provided credentials"""
        if not self._auth_manager:
            self._auth_manager = AzureAuthenticationManager()
        return self._auth_manager.get_azure_credential(credentials)

    async def validate_credentials(self, credentials: Dict[str, Any]) -> bool:
        """
        Validate Azure credentials by attempting to list subscriptions

        Args:
            credentials: Azure credentials dictionary

        Returns:
            True if credentials are valid, False otherwise
        """
        if not AZURE_SDK_AVAILABLE:
            self.logger.error(
                "Azure SDK is not installed. Cannot validate credentials."
            )
            return False

        if not self._auth_manager:
            self._auth_manager = AzureAuthenticationManager()

        return await self._auth_manager.validate_credentials(credentials)

    async def test_connectivity(self, configuration: Dict[str, Any]) -> bool:
        """
        Test connectivity to Azure APIs and verify required permissions

        Args:
            configuration: Azure configuration including credentials

        Returns:
            True if connectivity successful, False otherwise
        """
        if not self._auth_manager:
            self._auth_manager = AzureAuthenticationManager()

        return await self._auth_manager.test_connectivity(configuration)

    async def collect_data(self, request: CollectionRequest) -> CollectionResponse:
        """
        Collect data from Azure platform

        Args:
            request: Collection request with parameters

        Returns:
            Collection response with collected data or error information
        """
        if not AZURE_SDK_AVAILABLE:
            return CollectionResponse(
                adapter_id=self.metadata.adapter_id,
                success=False,
                error_message="Azure SDK is not installed. Please install azure-mgmt-* packages.",
                collection_metadata={
                    "error": "Azure SDK not available",
                    "suggestion": (
                        "Install required packages: pip install azure-mgmt-resource "
                        "azure-mgmt-compute azure-mgmt-sql"
                    ),
                },
            )

        start_time = time.time()

        try:
            # Initialize Azure clients and modules
            credentials = request.credentials

            azure_creds = AzureCredentials(
                tenant_id=credentials.get("tenant_id", ""),
                client_id=credentials.get("client_id", ""),
                client_secret=credentials.get("client_secret", ""),
                subscription_id=credentials.get("subscription_id", ""),
            )

            credential = self._get_azure_credential(azure_creds)
            self._initialize_modules(credential, azure_creds.subscription_id)

            # Collect data using Resource Graph for efficiency
            collected_data = {}
            total_resources = 0

            if not request.target_resources or "all" in request.target_resources:
                # Collect all supported resources
                target_types = self._supported_resource_types
            else:
                # Map request targets to Azure resource types
                target_types = self._utilities.map_targets_to_resource_types(
                    request.target_resources
                )

            # Use Resource Graph for efficient bulk collection
            resource_data = await self._collect_resources_with_graph(
                target_types, request.configuration
            )

            if resource_data:
                # Process and enhance resource data
                for resource_type, resources in resource_data.items():
                    try:
                        enhanced_resources = await self._enhance_resource_data(
                            resource_type, resources, request.configuration
                        )
                        if enhanced_resources:
                            collected_data[resource_type] = {
                                "resources": enhanced_resources,
                                "service": resource_type,
                                "count": len(enhanced_resources),
                            }
                            total_resources += len(enhanced_resources)

                    except Exception as e:
                        self.logger.error(
                            f"Failed to enhance data for {resource_type}: {str(e)}"
                        )
                        collected_data[resource_type] = {
                            "error": str(e),
                            "resources": [],
                        }

            # Collect performance metrics if requested
            if request.configuration.get("include_metrics", True):
                try:
                    metrics_data = await self._collect_performance_metrics(
                        collected_data
                    )
                    collected_data["metrics"] = metrics_data
                except Exception as e:
                    self.logger.error(
                        f"Failed to collect performance metrics: {str(e)}"
                    )
                    collected_data["metrics"] = {"error": str(e)}

            duration = time.time() - start_time

            self.logger.info(
                f"Azure data collection completed: {total_resources} resources in {duration:.2f}s"
            )

            return CollectionResponse(
                success=True,
                data=collected_data,
                resource_count=total_resources,
                collection_method=request.collection_method,
                duration_seconds=duration,
                metadata={
                    "subscription_id": azure_creds.subscription_id,
                    "resource_types_collected": list(target_types),
                    "adapter_version": self.metadata.version,
                },
            )

        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Azure data collection failed: {str(e)}"
            self.logger.error(error_msg)

            return CollectionResponse(
                success=False,
                error_message=error_msg,
                error_details={"exception_type": type(e).__name__},
                duration_seconds=duration,
                metadata={
                    "subscription_id": (
                        azure_creds.subscription_id
                        if "azure_creds" in locals()
                        else "unknown"
                    )
                },
            )

    async def _collect_resources_with_graph(
        self, resource_types: Set[str], config: Dict[str, Any]
    ) -> Dict[str, List[Dict]]:
        """Use Azure Resource Graph to efficiently collect resource data"""
        try:
            from azure.mgmt.resourcegraph.models import QueryRequest

            resource_data = {}

            # Build Resource Graph query for all resource types
            type_filter = " or ".join([f'type == "{rt}"' for rt in resource_types])
            query = f"""
            Resources
            | where {type_filter}
            | project id, name, type, location, resourceGroup, subscriptionId, tags, properties
            | limit 1000
            """

            # Execute query
            query_request = QueryRequest(
                subscriptions=[self._auth_manager.subscription_id], query=query
            )

            response = self._auth_manager.resource_graph_client.resources(query_request)

            # Group results by resource type
            for resource in response.data:
                resource_type = resource.get("type", "unknown")
                if resource_type not in resource_data:
                    resource_data[resource_type] = []

                # Convert Resource Graph result to standard format
                resource_dict = {
                    "id": resource.get("id"),
                    "name": resource.get("name"),
                    "type": resource.get("type"),
                    "location": resource.get("location"),
                    "resource_group": resource.get("resourceGroup"),
                    "subscription_id": resource.get("subscriptionId"),
                    "tags": resource.get("tags", {}),
                    "properties": resource.get("properties", {}),
                }

                resource_data[resource_type].append(resource_dict)

            self.logger.info(
                f"Resource Graph collected {len(response.data)} resources across {len(resource_data)} types"
            )

            return resource_data

        except Exception as e:
            self.logger.error(f"Resource Graph collection failed: {str(e)}")
            return {}

    async def _enhance_resource_data(
        self, resource_type: str, resources: List[Dict], config: Dict[str, Any]
    ) -> List[Dict]:
        """Enhance basic resource data with detailed information from specific APIs"""
        try:
            enhanced_resources = []

            for resource in resources:
                enhanced_resource = resource.copy()

                # Add detailed information based on resource type
                if resource_type == "Microsoft.Compute/virtualMachines":
                    enhanced_resource.update(
                        await self._compute_ops.enhance_vm_data(resource)
                    )
                elif resource_type == "Microsoft.Sql/servers/databases":
                    enhanced_resource.update(
                        await self._data_ops.enhance_sql_database_data(resource)
                    )
                elif resource_type == "Microsoft.Web/sites":
                    enhanced_resource.update(
                        await self._compute_ops.enhance_web_app_data(resource)
                    )
                elif resource_type == "Microsoft.Storage/storageAccounts":
                    enhanced_resource.update(
                        await self._storage_ops.enhance_storage_account_data(resource)
                    )
                elif resource_type == "Microsoft.Network/loadBalancers":
                    enhanced_resource.update(
                        await self._utilities.enhance_load_balancer_data(resource)
                    )

                enhanced_resources.append(enhanced_resource)

            return enhanced_resources

        except Exception as e:
            self.logger.warning(f"Failed to enhance {resource_type} data: {str(e)}")
            return resources  # Return basic data if enhancement fails

    async def _enhance_web_app_data(
        self, app_resource: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhance web app data with detailed information"""
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
            self.logger.warning(
                f"Failed to enhance web app data for {app_resource.get('name')}: {str(e)}"
            )

        return {}

    async def _enhance_storage_account_data(
        self, storage_resource: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhance storage account data with detailed information"""
        try:
            # Parse resource ID
            resource_id = storage_resource.get("id", "")
            parts = resource_id.split("/")

            if len(parts) >= 9:
                resource_group = parts[4]
                account_name = parts[8]

                # Get detailed storage account information
                storage_account = self._storage_client.storage_accounts.get_properties(
                    resource_group_name=resource_group, account_name=account_name
                )

                return {
                    "sku": {
                        "name": (
                            storage_account.sku.name if storage_account.sku else None
                        ),
                        "tier": (
                            storage_account.sku.tier if storage_account.sku else None
                        ),
                    },
                    "kind": storage_account.kind,
                    "provisioning_state": storage_account.provisioning_state,
                    "primary_location": storage_account.primary_location,
                    "status_of_primary": storage_account.status_of_primary,
                    "secondary_location": storage_account.secondary_location,
                    "status_of_secondary": storage_account.status_of_secondary,
                    "creation_time": (
                        storage_account.creation_time.isoformat()
                        if storage_account.creation_time
                        else None
                    ),
                    "primary_endpoints": (
                        {
                            "blob": (
                                storage_account.primary_endpoints.blob
                                if storage_account.primary_endpoints
                                else None
                            ),
                            "file": (
                                storage_account.primary_endpoints.file
                                if storage_account.primary_endpoints
                                else None
                            ),
                            "queue": (
                                storage_account.primary_endpoints.queue
                                if storage_account.primary_endpoints
                                else None
                            ),
                            "table": (
                                storage_account.primary_endpoints.table
                                if storage_account.primary_endpoints
                                else None
                            ),
                        }
                        if storage_account.primary_endpoints
                        else {}
                    ),
                    "access_tier": storage_account.access_tier,
                    "enable_https_traffic_only": storage_account.enable_https_traffic_only,
                    "network_rule_set": (
                        {
                            "default_action": (
                                storage_account.network_rule_set.default_action
                                if storage_account.network_rule_set
                                else None
                            ),
                        }
                        if storage_account.network_rule_set
                        else {}
                    ),
                    "encryption": (
                        {
                            "key_source": (
                                storage_account.encryption.key_source
                                if storage_account.encryption
                                else None
                            ),
                        }
                        if storage_account.encryption
                        else {}
                    ),
                }

        except Exception as e:
            self.logger.warning(
                f"Failed to enhance storage account data for {storage_resource.get('name')}: {str(e)}"
            )

        return {}

    async def _enhance_load_balancer_data(
        self, lb_resource: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhance load balancer data with detailed information"""
        try:
            # Parse resource ID
            resource_id = lb_resource.get("id", "")
            parts = resource_id.split("/")

            if len(parts) >= 9:
                resource_group = parts[4]
                lb_name = parts[8]

                # Get detailed load balancer information
                load_balancer = self._network_client.load_balancers.get(
                    resource_group_name=resource_group, load_balancer_name=lb_name
                )

                return {
                    "sku": {
                        "name": load_balancer.sku.name if load_balancer.sku else None,
                        "tier": load_balancer.sku.tier if load_balancer.sku else None,
                    },
                    "provisioning_state": load_balancer.provisioning_state,
                    "frontend_ip_configurations": (
                        [
                            {
                                "name": fic.name,
                                "private_ip_address": fic.private_ip_address,
                                "private_ip_allocation_method": fic.private_ip_allocation_method,
                                "subnet_id": fic.subnet.id if fic.subnet else None,
                                "public_ip_address_id": (
                                    fic.public_ip_address.id
                                    if fic.public_ip_address
                                    else None
                                ),
                            }
                            for fic in load_balancer.frontend_ip_configurations
                        ]
                        if load_balancer.frontend_ip_configurations
                        else []
                    ),
                    "backend_address_pools": (
                        [
                            {
                                "name": bap.name,
                                "backend_addresses_count": (
                                    len(bap.backend_addresses)
                                    if bap.backend_addresses
                                    else 0
                                ),
                            }
                            for bap in load_balancer.backend_address_pools
                        ]
                        if load_balancer.backend_address_pools
                        else []
                    ),
                    "load_balancing_rules": (
                        [
                            {
                                "name": lbr.name,
                                "protocol": lbr.protocol,
                                "frontend_port": lbr.frontend_port,
                                "backend_port": lbr.backend_port,
                                "enable_floating_ip": lbr.enable_floating_ip,
                            }
                            for lbr in load_balancer.load_balancing_rules
                        ]
                        if load_balancer.load_balancing_rules
                        else []
                    ),
                    "inbound_nat_rules": (
                        [
                            {
                                "name": inr.name,
                                "protocol": inr.protocol,
                                "frontend_port": inr.frontend_port,
                                "backend_port": inr.backend_port,
                            }
                            for inr in load_balancer.inbound_nat_rules
                        ]
                        if load_balancer.inbound_nat_rules
                        else []
                    ),
                }

        except Exception as e:
            self.logger.warning(
                f"Failed to enhance load balancer data for {lb_resource.get('name')}: {str(e)}"
            )

        return {}

    def _get_vm_power_state(self, instance_view) -> Optional[str]:
        """Extract VM power state from instance view"""
        if instance_view and instance_view.statuses:
            for status in instance_view.statuses:
                if status.code and status.code.startswith("PowerState/"):
                    return status.code.replace("PowerState/", "")
        return None

    async def _collect_performance_metrics(
        self, collected_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Collect Azure Monitor performance metrics for discovered resources"""
        try:
            metrics_data = {}
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=24)  # Last 24 hours

            # Collect metrics for Virtual Machines
            if "Microsoft.Compute/virtualMachines" in collected_data:
                vm_metrics = await self._compute_ops.collect_vm_metrics(
                    collected_data["Microsoft.Compute/virtualMachines"]["resources"],
                    start_time,
                    end_time,
                )
                metrics_data["VirtualMachines"] = vm_metrics

            # Collect metrics for SQL Databases
            if "Microsoft.Sql/servers/databases" in collected_data:
                sql_metrics = await self._data_ops.collect_sql_metrics(
                    collected_data["Microsoft.Sql/servers/databases"]["resources"],
                    start_time,
                    end_time,
                )
                metrics_data["SqlDatabases"] = sql_metrics

            # Collect metrics for Web Apps
            if "Microsoft.Web/sites" in collected_data:
                web_metrics = await self._compute_ops.collect_web_app_metrics(
                    collected_data["Microsoft.Web/sites"]["resources"],
                    start_time,
                    end_time,
                )
                metrics_data["WebApps"] = web_metrics

            return metrics_data

        except Exception as e:
            raise Exception(f"Performance metrics collection failed: {str(e)}")

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

    def _extract_metric_values(self, metric_data) -> List[float]:
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

    def _map_metric_to_field(self, metric_name: str, avg_value: float, vm_metrics: Dict) -> None:
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

    async def _collect_single_vm_metric(
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

            metric_values = self._extract_metric_values(metric_data)
            if metric_values:
                return sum(metric_values) / len(metric_values)
        except Exception as e:
            self.logger.warning(f"Failed to collect {metric_name}: {str(e)}")
        return None

    async def _collect_vm_metrics(
        self, vms: List[Dict], start_time: datetime, end_time: datetime
    ) -> List[Dict]:
        """Collect Azure Monitor metrics for Virtual Machines"""
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
                    avg_value = await self._collect_single_vm_metric(
                        resource_id, metric_name, start_time, end_time
                    )
                    if avg_value is not None:
                        self._map_metric_to_field(metric_name, avg_value, vm_metrics)

                metrics.append(vm_metrics)

            except Exception as e:
                self.logger.warning(
                    f"Failed to collect metrics for VM {vm.get('name')}: {str(e)}"
                )

        return metrics

    async def _collect_sql_metrics(
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
                        metric_data = self._monitor_client.metrics.list(
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
                        self.logger.warning(
                            f"Failed to collect {metric_name} for SQL DB {db.get('name')}: {str(e)}"
                        )

                metrics.append(db_metrics)

            except Exception as e:
                self.logger.warning(
                    f"Failed to collect metrics for SQL DB {db.get('name')}: {str(e)}"
                )

        return metrics

    async def _collect_web_app_metrics(
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
                        self.logger.warning(
                            f"Failed to collect {metric_name} for Web App {app.get('name')}: {str(e)}"
                        )

                metrics.append(app_metrics)

            except Exception as e:
                self.logger.warning(
                    f"Failed to collect metrics for Web App {app.get('name')}: {str(e)}"
                )

        return metrics

    async def get_available_resources(self, configuration: Dict[str, Any]) -> List[str]:
        """
        Get list of available Azure resources for collection

        Args:
            configuration: Azure configuration including credentials

        Returns:
            List of available resource type identifiers
        """
        try:
            # Test connectivity first
            if not await self.test_connectivity(configuration):
                return []

            # Use Resource Graph to quickly check for resource types
            available_types = []

            for resource_type in self._supported_resource_types:
                try:
                    has_resources = (
                        await self._utilities.check_resource_type_has_resources(
                            resource_type
                        )
                    )
                    if has_resources:
                        available_types.append(resource_type)

                except Exception as e:
                    self.logger.warning(
                        f"Failed to check resources for {resource_type}: {str(e)}"
                    )

            return available_types

        except Exception as e:
            self.logger.error(f"Failed to get available Azure resources: {str(e)}")
            return []

    async def _check_resource_type_has_resources(self, resource_type: str) -> bool:
        """Quick check if a resource type has any resources using Resource Graph"""
        try:
            from azure.mgmt.resourcegraph.models import QueryRequest

            query = f"""
            Resources
            | where type == "{resource_type}"
            | take 1
            | project id
            """

            query_request = QueryRequest(
                subscriptions=[self._subscription_id], query=query
            )

            response = self._resource_graph_client.resources(query_request)
            return len(response.data) > 0

        except Exception:
            return False

    def transform_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform raw Azure data to normalized format for Discovery Flow

        Args:
            raw_data: Raw Azure data from collection

        Returns:
            Normalized data structure compatible with Discovery Flow
        """
        try:
            normalized_data = {
                "platform": "Azure",
                "platform_version": "1.0",
                "collection_timestamp": datetime.utcnow().isoformat(),
                "assets": [],
                "dependencies": [],
                "performance_metrics": {},
                "configuration": {},
                "metadata": raw_data.get("metadata", {}),
            }

            # Transform each resource type's resources to normalized assets
            for resource_type, type_data in raw_data.items():
                if resource_type == "metadata" or "error" in type_data:
                    continue

                if "resources" in type_data:
                    for resource in type_data["resources"]:
                        normalized_asset = self._utilities.transform_resource_to_asset(
                            resource_type, resource
                        )
                        if normalized_asset:
                            normalized_data["assets"].append(normalized_asset)

            # Transform performance metrics
            if "metrics" in raw_data:
                normalized_data["performance_metrics"] = (
                    self._utilities.transform_metrics(raw_data["metrics"])
                )

            self.logger.info(
                f"Transformed {len(normalized_data['assets'])} Azure assets to normalized format"
            )

            return normalized_data

        except Exception as e:
            self.logger.error(f"Failed to transform Azure data: {str(e)}")
            return {
                "platform": "Azure",
                "error": f"Data transformation failed: {str(e)}",
                "assets": [],
                "dependencies": [],
                "performance_metrics": {},
                "configuration": {},
            }

    def _transform_resource_to_asset(
        self, resource_type: str, resource: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Transform Azure resource to normalized asset format"""
        try:
            # Common asset structure
            asset = {
                "platform": "Azure",
                "platform_service": resource_type,
                "asset_type": self._get_asset_type(resource_type),
                "unique_id": resource.get("id"),
                "name": resource.get("name"),
                "environment": "cloud",
                "region": resource.get("location"),
                "resource_group": resource.get("resource_group"),
                "subscription_id": resource.get("subscription_id"),
                "tags": resource.get("tags", {}),
                "discovery_method": "automated",
                "discovery_timestamp": datetime.utcnow().isoformat(),
                "raw_data": resource,
            }

            # Resource-type-specific transformations
            if resource_type == "Microsoft.Compute/virtualMachines":
                asset.update(
                    {
                        "compute_type": "virtual_machine",
                        "instance_type": resource.get("vm_size"),
                        "state": resource.get(
                            "power_state", resource.get("provisioning_state")
                        ),
                        "operating_system": resource.get("os_type"),
                        "computer_name": resource.get("computer_name"),
                        "network_interfaces": resource.get("network_interfaces", []),
                        "zones": resource.get("zones", []),
                    }
                )

            elif resource_type == "Microsoft.Sql/servers/databases":
                asset.update(
                    {
                        "database_type": "sql_server",
                        "database_sku": resource.get("sku", {}),
                        "database_status": resource.get("status"),
                        "max_size_bytes": resource.get("max_size_bytes"),
                        "collation": resource.get("collation"),
                        "zone_redundant": resource.get("zone_redundant"),
                    }
                )

            elif resource_type == "Microsoft.Web/sites":
                asset.update(
                    {
                        "compute_type": "web_application",
                        "app_kind": resource.get("kind"),
                        "app_state": resource.get("state"),
                        "host_names": resource.get("host_names", []),
                        "default_host_name": resource.get("default_host_name"),
                        "https_only": resource.get("https_only"),
                        "site_config": resource.get("site_config", {}),
                    }
                )

            elif resource_type == "Microsoft.Storage/storageAccounts":
                asset.update(
                    {
                        "storage_type": "object_storage",
                        "storage_sku": resource.get("sku", {}),
                        "storage_kind": resource.get("kind"),
                        "access_tier": resource.get("access_tier"),
                        "primary_location": resource.get("primary_location"),
                        "secondary_location": resource.get("secondary_location"),
                        "https_only": resource.get("enable_https_traffic_only"),
                    }
                )

            elif resource_type == "Microsoft.Network/loadBalancers":
                asset.update(
                    {
                        "network_type": "load_balancer",
                        "load_balancer_sku": resource.get("sku", {}),
                        "frontend_ip_configurations": resource.get(
                            "frontend_ip_configurations", []
                        ),
                        "backend_address_pools": resource.get(
                            "backend_address_pools", []
                        ),
                        "load_balancing_rules": resource.get(
                            "load_balancing_rules", []
                        ),
                    }
                )

            return asset

        except Exception as e:
            self.logger.warning(
                f"Failed to transform {resource_type} resource to asset: {str(e)}"
            )
            return None

    def _get_asset_type(self, resource_type: str) -> str:
        """Get normalized asset type for Azure resource"""
        type_map = {
            "Microsoft.Compute/virtualMachines": "server",
            "Microsoft.Sql/servers": "database_server",
            "Microsoft.Sql/servers/databases": "database",
            "Microsoft.Web/sites": "application",
            "Microsoft.Storage/storageAccounts": "storage",
            "Microsoft.Network/loadBalancers": "load_balancer",
            "Microsoft.Network/applicationGateways": "application_gateway",
            "Microsoft.ContainerService/managedClusters": "kubernetes_cluster",
            "Microsoft.Cache/Redis": "cache",
            "Microsoft.DocumentDB/databaseAccounts": "nosql_database",
            "Microsoft.Network/virtualNetworks": "network",
            "Microsoft.Network/networkSecurityGroups": "security_group",
        }
        return type_map.get(resource_type, "infrastructure")

    def _transform_metrics(self, metrics_data: Dict[str, Any]) -> Dict[str, Any]:
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


# Azure Adapter metadata for registration
AZURE_ADAPTER_METADATA = AdapterMetadata(
    name="azure_adapter",
    version="1.0.0",
    adapter_type="cloud_platform",
    automation_tier=AutomationTier.TIER_1,
    supported_platforms=["Azure"],
    capabilities=[
        AdapterCapability.SERVER_DISCOVERY,
        AdapterCapability.APPLICATION_DISCOVERY,
        AdapterCapability.DATABASE_DISCOVERY,
        AdapterCapability.NETWORK_DISCOVERY,
        AdapterCapability.DEPENDENCY_MAPPING,
        AdapterCapability.PERFORMANCE_METRICS,
        AdapterCapability.CONFIGURATION_EXPORT,
        AdapterCapability.CREDENTIAL_VALIDATION,
    ],
    required_credentials=["tenant_id", "client_id", "client_secret", "subscription_id"],
    configuration_schema={
        "type": "object",
        "required": ["credentials"],
        "properties": {
            "credentials": {
                "type": "object",
                "required": [
                    "tenant_id",
                    "client_id",
                    "client_secret",
                    "subscription_id",
                ],
                "properties": {
                    "tenant_id": {"type": "string"},
                    "client_id": {"type": "string"},
                    "client_secret": {"type": "string"},
                    "subscription_id": {"type": "string"},
                },
            },
            "include_metrics": {"type": "boolean", "default": True},
            "resource_groups": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Specific resource groups to collect from (optional)",
            },
        },
    },
    description="Comprehensive Azure platform adapter with Resource Graph and Monitor integration",
    author="ADCS Team B1",
    documentation_url="https://docs.microsoft.com/en-us/azure/developer/python/",
)
