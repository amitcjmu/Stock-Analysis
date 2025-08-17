"""
Azure Authentication Module for ADCS Implementation

This module handles Azure authentication, credential validation, and client initialization
for the Azure adapter. Provides centralized authentication management with comprehensive
connectivity testing across Azure services.
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict

try:
    from azure.core.exceptions import ClientAuthenticationError, HttpResponseError
    from azure.identity import ClientSecretCredential
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
    ClientSecretCredential = None
    ResourceManagementClient = ResourceGraphClient = MonitorManagementClient = None
    ComputeManagementClient = SqlManagementClient = WebSiteManagementClient = None
    StorageManagementClient = NetworkManagementClient = None
    ClientAuthenticationError = HttpResponseError = Exception

logger = logging.getLogger(__name__)


@dataclass
class AzureCredentials:
    """Azure credentials configuration"""

    tenant_id: str
    client_id: str
    client_secret: str
    subscription_id: str


class AzureAuthenticationManager:
    """
    Azure Authentication Manager for ADCS Implementation

    Handles Azure credential validation, client initialization, and connectivity testing
    across all Azure services required by the adapter.
    """

    def __init__(self):
        """Initialize Azure authentication manager"""
        if not AZURE_SDK_AVAILABLE:
            logger.warning(
                "Azure SDK is not installed. Azure adapter functionality will be limited."
            )
        self._credential: ClientSecretCredential = None
        self._subscription_id: str = None
        self._resource_client: ResourceManagementClient = None
        self._resource_graph_client: ResourceGraphClient = None
        self._monitor_client: MonitorManagementClient = None
        self._compute_client: ComputeManagementClient = None
        self._sql_client: SqlManagementClient = None
        self._web_client: WebSiteManagementClient = None
        self._storage_client: StorageManagementClient = None
        self._network_client: NetworkManagementClient = None

    def get_azure_credential(
        self, credentials: AzureCredentials
    ) -> ClientSecretCredential:
        """
        Create Azure credential from provided credentials

        Args:
            credentials: Azure credentials configuration

        Returns:
            ClientSecretCredential instance for Azure authentication
        """
        return ClientSecretCredential(
            tenant_id=credentials.tenant_id,
            client_id=credentials.client_id,
            client_secret=credentials.client_secret,
        )

    def init_clients(
        self, credential: ClientSecretCredential, subscription_id: str
    ) -> None:
        """
        Initialize Azure service clients with credentials

        Args:
            credential: Azure credential for authentication
            subscription_id: Azure subscription ID
        """
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
            credential = self.get_azure_credential(azure_creds)
            resource_client = ResourceManagementClient(
                credential, azure_creds.subscription_id
            )

            # Test credentials by getting subscription info
            subscription = resource_client.subscriptions.get(
                azure_creds.subscription_id
            )

            logger.info(
                f"Azure credentials validated for subscription: {subscription.display_name}"
            )
            return True

        except ClientAuthenticationError as e:
            logger.error(f"Azure authentication failed: {str(e)}")
            return False
        except HttpResponseError as e:
            logger.error(f"Azure API error during credential validation: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error validating Azure credentials: {str(e)}")
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
            credential = self.get_azure_credential(azure_creds)
            self.init_clients(credential, azure_creds.subscription_id)

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
                    logger.warning(f"Connectivity test failed for {service}: {str(e)}")
                    results[service] = False

            # Log results
            successful_tests = sum(1 for result in results.values() if result)
            total_tests = len(results)

            logger.info(
                f"Azure connectivity tests: {successful_tests}/{total_tests} successful"
            )

            # Consider connectivity successful if core services work
            core_services = ["ResourceManagement", "ResourceGraph"]
            core_success = all(results.get(service, False) for service in core_services)

            return core_success

        except Exception as e:
            logger.error(f"Azure connectivity test failed: {str(e)}")
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

    @property
    def credential(self) -> ClientSecretCredential:
        """Get current Azure credential"""
        return self._credential

    @property
    def subscription_id(self) -> str:
        """Get current subscription ID"""
        return self._subscription_id

    @property
    def resource_client(self) -> ResourceManagementClient:
        """Get Resource Management client"""
        return self._resource_client

    @property
    def resource_graph_client(self) -> ResourceGraphClient:
        """Get Resource Graph client"""
        return self._resource_graph_client

    @property
    def monitor_client(self) -> MonitorManagementClient:
        """Get Monitor client"""
        return self._monitor_client

    @property
    def compute_client(self) -> ComputeManagementClient:
        """Get Compute client"""
        return self._compute_client

    @property
    def sql_client(self) -> SqlManagementClient:
        """Get SQL client"""
        return self._sql_client

    @property
    def web_client(self) -> WebSiteManagementClient:
        """Get Web client"""
        return self._web_client

    @property
    def storage_client(self) -> StorageManagementClient:
        """Get Storage client"""
        return self._storage_client

    @property
    def network_client(self) -> NetworkManagementClient:
        """Get Network client"""
        return self._network_client
