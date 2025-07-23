"""
Azure Platform Adapter for ADCS Implementation

This adapter provides comprehensive Azure resource discovery and data collection
using Azure Resource Graph for resource discovery and Azure Monitor for metrics.
"""

import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set

try:
    from azure.core.exceptions import (ClientAuthenticationError,
                                       HttpResponseError)
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

logger = logging.getLogger(__name__)

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.collection_flow import AutomationTier
from app.services.collection_flow.adapters import (AdapterCapability,
                                                   AdapterMetadata,
                                                   BaseAdapter,
                                                   CollectionRequest,
                                                   CollectionResponse)


@dataclass
class AzureCredentials:
    """Azure credentials configuration"""

    tenant_id: str
    client_id: str
    client_secret: str
    subscription_id: str


@dataclass
class AzureResourceMetrics:
    """Azure resource performance metrics"""

    resource_id: str
    resource_type: str
    cpu_percentage: Optional[float] = None
    memory_percentage: Optional[float] = None
    network_in: Optional[float] = None
    network_out: Optional[float] = None
    disk_read_bytes: Optional[float] = None
    disk_write_bytes: Optional[float] = None
    timestamp: Optional[datetime] = None


class AzureAdapter(BaseAdapter):
    """
    Azure Platform Adapter implementing BaseAdapter interface

    Provides comprehensive Azure resource discovery using:
    - Azure Resource Graph for efficient resource queries
    - Azure Monitor for performance metrics
    - Resource Management APIs for detailed resource information
    - Support for VMs, databases, web apps, storage, and networking resources
    """

    def __init__(self, db: AsyncSession, metadata: AdapterMetadata):
        """Initialize Azure adapter with metadata and session"""
        super().__init__(db, metadata)
        if not AZURE_SDK_AVAILABLE:
            logger.warning(
                "Azure SDK is not installed. Azure adapter functionality will be limited."
            )
        self._credential = None
        self._subscription_id = None
        self._resource_client = None
        self._resource_graph_client = None
        self._monitor_client = None
        self._compute_client = None
        self._sql_client = None
        self._web_client = None
        self._storage_client = None
        self._network_client = None
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

    def _get_azure_credential(
        self, credentials: AzureCredentials
    ) -> ClientSecretCredential:
        """Create Azure credential from provided credentials"""
        return ClientSecretCredential(
            tenant_id=credentials.tenant_id,
            client_id=credentials.client_id,
            client_secret=credentials.client_secret,
        )

    def _init_clients(self, credential: ClientSecretCredential, subscription_id: str):
        """Initialize Azure service clients"""
        self._credential = credential
        self._subscription_id = subscription_id
        self._resource_client = ResourceManagementClient(credential, subscription_id)
        self._resource_graph_client = ResourceGraphClient(credential)
        self._monitor_client = MonitorManagementClient(credential, subscription_id)
        self._compute_client = ComputeManagementClient(credential, subscription_id)
        self._sql_client = SqlManagementClient(credential, subscription_id)
        self._web_client = WebSiteManagementClient(credential, subscription_id)
        self._storage_client = StorageManagementClient(credential, subscription_id)
        self._network_client = NetworkManagementClient(credential, subscription_id)

    async def validate_credentials(self, credentials: Dict[str, Any]) -> bool:
        """
        Validate Azure credentials by attempting to list subscriptions

        Args:
            credentials: Azure credentials dictionary

        Returns:
            True if credentials are valid, False otherwise
        """
        if not AZURE_SDK_AVAILABLE:
            logger.error("Azure SDK is not installed. Cannot validate credentials.")
            return False

        try:
            # Parse credentials
            azure_creds = AzureCredentials(
                tenant_id=credentials.get("tenant_id", ""),
                client_id=credentials.get("client_id", ""),
                client_secret=credentials.get("client_secret", ""),
                subscription_id=credentials.get("subscription_id", ""),
            )

            # Create credential and test with Resource Management
            credential = self._get_azure_credential(azure_creds)
            resource_client = ResourceManagementClient(
                credential, azure_creds.subscription_id
            )

            # Test credentials by getting subscription info
            subscription = resource_client.subscriptions.get(
                azure_creds.subscription_id
            )

            self.logger.info(
                f"Azure credentials validated for subscription: {subscription.display_name}"
            )
            return True

        except ClientAuthenticationError as e:
            self.logger.error(f"Azure authentication failed: {str(e)}")
            return False
        except HttpResponseError as e:
            self.logger.error(f"Azure API error during credential validation: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(
                f"Unexpected error validating Azure credentials: {str(e)}"
            )
            return False

    async def test_connectivity(self, configuration: Dict[str, Any]) -> bool:
        """
        Test connectivity to Azure APIs and verify required permissions

        Args:
            configuration: Azure configuration including credentials

        Returns:
            True if connectivity successful, False otherwise
        """
        try:
            # Extract credentials
            credentials = configuration.get("credentials", {})

            azure_creds = AzureCredentials(
                tenant_id=credentials.get("tenant_id", ""),
                client_id=credentials.get("client_id", ""),
                client_secret=credentials.get("client_secret", ""),
                subscription_id=credentials.get("subscription_id", ""),
            )

            # Create credential and initialize clients
            credential = self._get_azure_credential(azure_creds)
            self._init_clients(credential, azure_creds.subscription_id)

            # Test connectivity to core services
            connectivity_tests = {
                "ResourceManagement": self._test_resource_management_connectivity,
                "ResourceGraph": self._test_resource_graph_connectivity,
                "Monitor": self._test_monitor_connectivity,
                "Compute": self._test_compute_connectivity,
            }

            results = {}
            for service, test_func in connectivity_tests.items():
                try:
                    results[service] = await test_func()
                except Exception as e:
                    self.logger.warning(
                        f"Connectivity test failed for {service}: {str(e)}"
                    )
                    results[service] = False

            # Log results
            successful_tests = sum(1 for result in results.values() if result)
            total_tests = len(results)

            self.logger.info(
                f"Azure connectivity tests: {successful_tests}/{total_tests} successful"
            )

            # Consider connectivity successful if core services work
            core_services = ["ResourceManagement", "ResourceGraph"]
            core_success = all(results.get(service, False) for service in core_services)

            return core_success

        except Exception as e:
            self.logger.error(f"Azure connectivity test failed: {str(e)}")
            return False

    async def _test_resource_management_connectivity(self) -> bool:
        """Test Resource Management API connectivity"""
        try:
            # List resource groups (should work with basic permissions)
            list(self._resource_client.resource_groups.list())
            return True
        except Exception:
            return False

    async def _test_resource_graph_connectivity(self) -> bool:
        """Test Resource Graph API connectivity"""
        try:
            from azure.mgmt.resourcegraph.models import QueryRequest

            # Simple query to test Resource Graph access
            query = QueryRequest(
                subscriptions=[self._subscription_id], query="Resources | take 1"
            )
            self._resource_graph_client.resources(query)
            return True
        except Exception:
            return False

    async def _test_monitor_connectivity(self) -> bool:
        """Test Azure Monitor API connectivity"""
        try:
            # List metric definitions (basic monitor access)
            # This requires a resource, so we'll try with the subscription scope
            list(
                self._monitor_client.metric_definitions.list(
                    resource_uri=f"/subscriptions/{self._subscription_id}"
                )
            )
            return True
        except Exception:
            return False

    async def _test_compute_connectivity(self) -> bool:
        """Test Compute API connectivity"""
        try:
            # List VM sizes in a region (basic compute access)
            list(self._compute_client.virtual_machine_sizes.list("eastus"))
            return True
        except Exception:
            return False

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
                    "suggestion": "Install required packages: pip install azure-mgmt-resource azure-mgmt-compute azure-mgmt-sql",
                },
            )

        start_time = time.time()

        try:
            # Initialize Azure clients
            credentials = request.credentials

            azure_creds = AzureCredentials(
                tenant_id=credentials.get("tenant_id", ""),
                client_id=credentials.get("client_id", ""),
                client_secret=credentials.get("client_secret", ""),
                subscription_id=credentials.get("subscription_id", ""),
            )

            credential = self._get_azure_credential(azure_creds)
            self._init_clients(credential, azure_creds.subscription_id)

            # Collect data using Resource Graph for efficiency
            collected_data = {}
            total_resources = 0

            if not request.target_resources or "all" in request.target_resources:
                # Collect all supported resources
                target_types = self._supported_resource_types
            else:
                # Map request targets to Azure resource types
                target_types = self._map_targets_to_resource_types(
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

    def _map_targets_to_resource_types(self, targets: List[str]) -> Set[str]:
        """Map request targets to Azure resource types"""
        target_mapping = {
            "VirtualMachines": "Microsoft.Compute/virtualMachines",
            "VM": "Microsoft.Compute/virtualMachines",
            "Databases": "Microsoft.Sql/servers/databases",
            "SQL": "Microsoft.Sql/servers/databases",
            "WebApps": "Microsoft.Web/sites",
            "Storage": "Microsoft.Storage/storageAccounts",
            "LoadBalancers": "Microsoft.Network/loadBalancers",
            "AKS": "Microsoft.ContainerService/managedClusters",
            "Redis": "Microsoft.Cache/Redis",
            "CosmosDB": "Microsoft.DocumentDB/databaseAccounts",
            "Networks": "Microsoft.Network/virtualNetworks",
        }

        mapped_types = set()
        for target in targets:
            if target in target_mapping:
                mapped_types.add(target_mapping[target])
            elif target in self._supported_resource_types:
                mapped_types.add(target)

        return mapped_types or self._supported_resource_types

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
                subscriptions=[self._subscription_id], query=query
            )

            response = self._resource_graph_client.resources(query_request)

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
                    enhanced_resource.update(await self._enhance_vm_data(resource))
                elif resource_type == "Microsoft.Sql/servers/databases":
                    enhanced_resource.update(
                        await self._enhance_sql_database_data(resource)
                    )
                elif resource_type == "Microsoft.Web/sites":
                    enhanced_resource.update(await self._enhance_web_app_data(resource))
                elif resource_type == "Microsoft.Storage/storageAccounts":
                    enhanced_resource.update(
                        await self._enhance_storage_account_data(resource)
                    )
                elif resource_type == "Microsoft.Network/loadBalancers":
                    enhanced_resource.update(
                        await self._enhance_load_balancer_data(resource)
                    )

                enhanced_resources.append(enhanced_resource)

            return enhanced_resources

        except Exception as e:
            self.logger.warning(f"Failed to enhance {resource_type} data: {str(e)}")
            return resources  # Return basic data if enhancement fails

    async def _enhance_vm_data(self, vm_resource: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance VM data with detailed compute information"""
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
            self.logger.warning(
                f"Failed to enhance VM data for {vm_resource.get('name')}: {str(e)}"
            )

        return {}

    async def _enhance_sql_database_data(
        self, db_resource: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhance SQL database data with detailed information"""
        try:
            # Parse resource ID to get server and database info
            resource_id = db_resource.get("id", "")
            parts = resource_id.split("/")

            if len(parts) >= 11:
                resource_group = parts[4]
                server_name = parts[8]
                database_name = parts[10]

                # Get detailed database information
                database = self._sql_client.databases.get(
                    resource_group_name=resource_group,
                    server_name=server_name,
                    database_name=database_name,
                )

                return {
                    "sku": {
                        "name": database.sku.name if database.sku else None,
                        "tier": database.sku.tier if database.sku else None,
                        "capacity": database.sku.capacity if database.sku else None,
                    },
                    "status": database.status,
                    "creation_date": (
                        database.creation_date.isoformat()
                        if database.creation_date
                        else None
                    ),
                    "collation": database.collation,
                    "max_size_bytes": database.max_size_bytes,
                    "current_backup_storage_redundancy": database.current_backup_storage_redundancy,
                    "zone_redundant": database.zone_redundant,
                    "read_scale": database.read_scale,
                    "elastic_pool_id": database.elastic_pool_id,
                }

        except Exception as e:
            self.logger.warning(
                f"Failed to enhance SQL database data for {db_resource.get('name')}: {str(e)}"
            )

        return {}

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
                vm_metrics = await self._collect_vm_metrics(
                    collected_data["Microsoft.Compute/virtualMachines"]["resources"],
                    start_time,
                    end_time,
                )
                metrics_data["VirtualMachines"] = vm_metrics

            # Collect metrics for SQL Databases
            if "Microsoft.Sql/servers/databases" in collected_data:
                sql_metrics = await self._collect_sql_metrics(
                    collected_data["Microsoft.Sql/servers/databases"]["resources"],
                    start_time,
                    end_time,
                )
                metrics_data["SqlDatabases"] = sql_metrics

            # Collect metrics for Web Apps
            if "Microsoft.Web/sites" in collected_data:
                web_metrics = await self._collect_web_app_metrics(
                    collected_data["Microsoft.Web/sites"]["resources"],
                    start_time,
                    end_time,
                )
                metrics_data["WebApps"] = web_metrics

            return metrics_data

        except Exception as e:
            raise Exception(f"Performance metrics collection failed: {str(e)}")

    async def _collect_vm_metrics(
        self, vms: List[Dict], start_time: datetime, end_time: datetime
    ) -> List[Dict]:
        """Collect Azure Monitor metrics for Virtual Machines"""
        metrics = []

        for vm in vms:
            resource_id = vm.get("id")
            if not resource_id:
                continue

            try:
                # Define metrics to collect
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

                # Collect each metric
                for metric_name in metric_names:
                    try:
                        metric_data = self._monitor_client.metrics.list(
                            resource_uri=resource_id,
                            timespan=f"{start_time.isoformat()}/{end_time.isoformat()}",
                            interval="PT1H",  # 1 hour intervals
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

                                # Map metric names to standard fields
                                if metric_name == "Percentage CPU":
                                    vm_metrics["cpu_percentage"] = avg_value
                                elif metric_name == "Network In Total":
                                    vm_metrics["network_in"] = avg_value
                                elif metric_name == "Network Out Total":
                                    vm_metrics["network_out"] = avg_value
                                elif metric_name == "Disk Read Bytes":
                                    vm_metrics["disk_read_bytes"] = avg_value
                                elif metric_name == "Disk Write Bytes":
                                    vm_metrics["disk_write_bytes"] = avg_value

                    except Exception as e:
                        self.logger.warning(
                            f"Failed to collect {metric_name} for VM {vm.get('name')}: {str(e)}"
                        )

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
                    has_resources = await self._check_resource_type_has_resources(
                        resource_type
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
                        normalized_asset = self._transform_resource_to_asset(
                            resource_type, resource
                        )
                        if normalized_asset:
                            normalized_data["assets"].append(normalized_asset)

            # Transform performance metrics
            if "metrics" in raw_data:
                normalized_data["performance_metrics"] = self._transform_metrics(
                    raw_data["metrics"]
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
