"""
Azure Utilities Module for ADCS Implementation

This module provides utility functions and helper operations for the Azure adapter
including resource type mapping, data transformation, load balancer operations,
and various helper functions for Azure resource management.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

try:
    from azure.mgmt.network import NetworkManagementClient
    from azure.mgmt.resourcegraph import ResourceGraphClient

    AZURE_SDK_AVAILABLE = True
except ImportError:
    AZURE_SDK_AVAILABLE = False
    NetworkManagementClient = ResourceGraphClient = None

logger = logging.getLogger(__name__)


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


class AzureUtilities:
    """
    Azure Utilities for ADCS Implementation

    Provides utility functions, helper operations, and network resource
    management for the Azure adapter including load balancer operations
    and data transformation utilities.
    """

    def __init__(
        self,
        network_client: NetworkManagementClient,
        resource_graph_client: ResourceGraphClient,
        subscription_id: str,
    ):
        """
        Initialize Azure utilities

        Args:
            network_client: Azure Network Management client
            resource_graph_client: Azure Resource Graph client
            subscription_id: Azure subscription ID
        """
        self._network_client = network_client
        self._resource_graph_client = resource_graph_client
        self._subscription_id = subscription_id

    def map_targets_to_resource_types(self, targets: List[str]) -> Set[str]:
        """
        Map request targets to Azure resource types

        Args:
            targets: List of target resource types from request

        Returns:
            Set of Azure resource type strings
        """
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

        # Default supported resource types
        supported_resource_types = {
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

        mapped_types = set()
        for target in targets:
            if target in target_mapping:
                mapped_types.add(target_mapping[target])
            elif target in supported_resource_types:
                mapped_types.add(target)

        return mapped_types or supported_resource_types

    async def enhance_load_balancer_data(
        self, lb_resource: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enhance load balancer data with detailed information

        Args:
            lb_resource: Basic load balancer resource data from Resource Graph

        Returns:
            Enhanced load balancer data with detailed network properties
        """
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
            logger.warning(
                f"Failed to enhance load balancer data for {lb_resource.get('name')}: {str(e)}"
            )

        return {}

    async def check_resource_type_has_resources(self, resource_type: str) -> bool:
        """
        Quick check if a resource type has any resources using Resource Graph

        Args:
            resource_type: Azure resource type to check

        Returns:
            True if resource type has resources, False otherwise
        """
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

    def transform_resource_to_asset(
        self, resource_type: str, resource: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Transform Azure resource to normalized asset format

        Args:
            resource_type: Azure resource type
            resource: Resource data dictionary

        Returns:
            Normalized asset dictionary or None if transformation fails
        """
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
            logger.warning(
                f"Failed to transform {resource_type} resource to asset: {str(e)}"
            )
            return None

    def _get_asset_type(self, resource_type: str) -> str:
        """
        Get normalized asset type for Azure resource

        Args:
            resource_type: Azure resource type

        Returns:
            Normalized asset type string
        """
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

    def transform_metrics(self, metrics_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform Azure Monitor metrics to normalized format

        Args:
            metrics_data: Raw metrics data from Azure Monitor

        Returns:
            Normalized metrics data
        """
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
