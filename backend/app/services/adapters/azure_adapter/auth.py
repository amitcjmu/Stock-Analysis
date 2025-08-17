"""
Azure authentication and credential management
"""

import logging
from typing import Any, Dict

from .base import AzureCredentials
from .exceptions import (
    AZURE_SDK_AVAILABLE,
    AzureSDKNotAvailableError,
    ClientAuthenticationError,
    HttpResponseError,
)

if AZURE_SDK_AVAILABLE:
    from azure.identity import ClientSecretCredential, DefaultAzureCredential
    from azure.mgmt.compute import ComputeManagementClient
    from azure.mgmt.monitor import MonitorManagementClient
    from azure.mgmt.network import NetworkManagementClient
    from azure.mgmt.resource import ResourceManagementClient
    from azure.mgmt.resourcegraph import ResourceGraphClient
    from azure.mgmt.sql import SqlManagementClient
    from azure.mgmt.storage import StorageManagementClient
    from azure.mgmt.web import WebSiteManagementClient
else:
    # Create dummy classes for type hints
    ClientSecretCredential = DefaultAzureCredential = None
    ResourceManagementClient = ResourceGraphClient = MonitorManagementClient = None
    ComputeManagementClient = SqlManagementClient = WebSiteManagementClient = None
    StorageManagementClient = NetworkManagementClient = None

logger = logging.getLogger(__name__)


class AzureAuthManager:
    """Manages Azure authentication and service client initialization"""

    def __init__(self):
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

    def get_azure_credential(
        self, credentials: AzureCredentials
    ) -> ClientSecretCredential:
        """Create Azure credential from provided credentials"""
        if not AZURE_SDK_AVAILABLE:
            raise AzureSDKNotAvailableError()

        return ClientSecretCredential(
            tenant_id=credentials.tenant_id,
            client_id=credentials.client_id,
            client_secret=credentials.client_secret,
        )

    def init_clients(self, credential: ClientSecretCredential, subscription_id: str):
        """Initialize Azure service clients"""
        if not AZURE_SDK_AVAILABLE:
            raise AzureSDKNotAvailableError()

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

    @property
    def resource_client(self):
        """Get Resource Management client"""
        return self._resource_client

    @property
    def resource_graph_client(self):
        """Get Resource Graph client"""
        return self._resource_graph_client

    @property
    def monitor_client(self):
        """Get Monitor client"""
        return self._monitor_client

    @property
    def compute_client(self):
        """Get Compute client"""
        return self._compute_client

    @property
    def sql_client(self):
        """Get SQL client"""
        return self._sql_client

    @property
    def web_client(self):
        """Get Web client"""
        return self._web_client

    @property
    def storage_client(self):
        """Get Storage client"""
        return self._storage_client

    @property
    def network_client(self):
        """Get Network client"""
        return self._network_client

    @property
    def subscription_id(self):
        """Get current subscription ID"""
        return self._subscription_id
