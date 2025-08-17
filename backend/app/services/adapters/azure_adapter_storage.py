"""
Azure Storage Operations Module for ADCS Implementation

This module handles Azure storage resource operations including Storage Accounts.
Provides detailed resource enhancement and storage-specific information gathering
for Azure storage services.
"""

import logging
from typing import Any, Dict

try:
    from azure.mgmt.storage import StorageManagementClient

    AZURE_SDK_AVAILABLE = True
except ImportError:
    AZURE_SDK_AVAILABLE = False
    StorageManagementClient = None

logger = logging.getLogger(__name__)


class AzureStorageOperations:
    """
    Azure Storage Operations for ADCS Implementation

    Handles Storage Account resource enhancement and detailed storage
    information gathering for comprehensive storage asset discovery.
    """

    def __init__(self, storage_client: StorageManagementClient):
        """
        Initialize Azure storage operations

        Args:
            storage_client: Azure Storage Management client
        """
        self._storage_client = storage_client

    async def enhance_storage_account_data(
        self, storage_resource: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enhance storage account data with detailed information

        Args:
            storage_resource: Basic storage account resource data from Resource Graph

        Returns:
            Enhanced storage account data with detailed storage properties
        """
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
            logger.warning(
                f"Failed to enhance storage account data for {storage_resource.get('name')}: {str(e)}"
            )

        return {}
