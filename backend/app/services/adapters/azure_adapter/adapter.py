"""
Azure Adapter Main Module

Main Azure adapter class that orchestrates all modular components.
"""

import logging
import time
from typing import Any, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.collection_flow.adapters import (
    BaseAdapter,
    CollectionRequest,
    CollectionResponse,
)

from .auth import AzureAuthManager
from .base import AZURE_ADAPTER_METADATA, SUPPORTED_RESOURCE_TYPES, AzureCredentials
from .compute import AzureComputeManager
from .discovery import AzureResourceCollector
from .exceptions import AZURE_SDK_AVAILABLE
from .monitoring import AzureMonitoringManager
from .network import AzureNetworkManager
from .storage import AzureStorageManager
from .transformer import AzureDataTransformer
from .utils import map_targets_to_resource_types

logger = logging.getLogger(__name__)


class AzureAdapter(BaseAdapter):
    """
    Azure Platform Adapter implementing BaseAdapter interface

    Provides comprehensive Azure resource discovery using:
    - Azure Resource Graph for efficient resource queries
    - Azure Monitor for performance metrics
    - Resource Management APIs for detailed resource information
    - Support for VMs, databases, web apps, storage, and networking resources
    """

    def __init__(self, db: AsyncSession, metadata=AZURE_ADAPTER_METADATA):
        """Initialize Azure adapter with metadata and session"""
        super().__init__(db, metadata)
        if not AZURE_SDK_AVAILABLE:
            logger.warning(
                "Azure SDK is not installed. Azure adapter functionality will be limited."
            )

        # Initialize component managers
        self._auth_manager = AzureAuthManager()
        self._resource_collector = AzureResourceCollector(self._auth_manager)
        self._compute_manager = AzureComputeManager(self._auth_manager)
        self._storage_manager = AzureStorageManager(self._auth_manager)
        self._network_manager = AzureNetworkManager(self._auth_manager)
        self._monitoring_manager = AzureMonitoringManager(self._auth_manager)
        self._data_transformer = AzureDataTransformer()

    async def validate_credentials(self, credentials: Dict[str, Any]) -> bool:
        """
        Validate Azure credentials by attempting to list subscriptions

        Args:
            credentials: Azure credentials dictionary

        Returns:
            True if credentials are valid, False otherwise
        """
        return await self._auth_manager.validate_credentials(credentials)

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
            credential = self._auth_manager.get_azure_credential(azure_creds)
            self._auth_manager.init_clients(credential, azure_creds.subscription_id)

            # Test connectivity to core services
            connectivity_tests = {
                "ResourceManagement": self._resource_collector.test_resource_management_connectivity,
                "ResourceGraph": self._resource_collector.test_resource_graph_connectivity,
                "Monitor": self._monitoring_manager.test_monitor_connectivity,
                "Compute": self._compute_manager.test_compute_connectivity,
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
            # Initialize Azure clients
            credentials = request.credentials

            azure_creds = AzureCredentials(
                tenant_id=credentials.get("tenant_id", ""),
                client_id=credentials.get("client_id", ""),
                client_secret=credentials.get("client_secret", ""),
                subscription_id=credentials.get("subscription_id", ""),
            )

            credential = self._auth_manager.get_azure_credential(azure_creds)
            self._auth_manager.init_clients(credential, azure_creds.subscription_id)

            # Collect data using Resource Graph for efficiency
            collected_data = {}
            total_resources = 0

            if not request.target_resources or "all" in request.target_resources:
                # Collect all supported resources
                target_types = SUPPORTED_RESOURCE_TYPES
            else:
                # Map request targets to Azure resource types
                target_types = map_targets_to_resource_types(request.target_resources)

            # Use Resource Graph for efficient bulk collection
            resource_data = await self._resource_collector.collect_resources_with_graph(
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
                    metrics_data = (
                        await self._monitoring_manager.collect_performance_metrics(
                            collected_data
                        )
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
                        await self._compute_manager.enhance_vm_data(resource)
                    )
                elif resource_type == "Microsoft.Sql/servers/databases":
                    enhanced_resource.update(
                        await self._compute_manager.enhance_sql_database_data(resource)
                    )
                elif resource_type == "Microsoft.Web/sites":
                    enhanced_resource.update(
                        await self._compute_manager.enhance_web_app_data(resource)
                    )
                elif resource_type == "Microsoft.Storage/storageAccounts":
                    enhanced_resource.update(
                        await self._storage_manager.enhance_storage_account_data(
                            resource
                        )
                    )
                elif resource_type == "Microsoft.Network/loadBalancers":
                    enhanced_resource.update(
                        await self._network_manager.enhance_load_balancer_data(resource)
                    )

                enhanced_resources.append(enhanced_resource)

            return enhanced_resources

        except Exception as e:
            self.logger.warning(f"Failed to enhance {resource_type} data: {str(e)}")
            return resources  # Return basic data if enhancement fails

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
            available_types = await self._resource_collector.get_available_resources(
                SUPPORTED_RESOURCE_TYPES
            )

            return available_types

        except Exception as e:
            self.logger.error(f"Failed to get available Azure resources: {str(e)}")
            return []

    def transform_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform raw Azure data to normalized format for Discovery Flow

        Args:
            raw_data: Raw Azure data from collection

        Returns:
            Normalized data structure compatible with Discovery Flow
        """
        return self._data_transformer.transform_data(raw_data)
