"""
Azure storage services operations (blob storage, file operations, etc.)
"""

import logging
from typing import Any, Dict

from .auth import AzureAuthManager
from .utils import parse_azure_resource_id

logger = logging.getLogger(__name__)


class AzureStorageManager:
    """Manages Azure storage resource operations"""

    def __init__(self, auth_manager: AzureAuthManager):
        self.auth_manager = auth_manager

    async def enhance_storage_account_data(
        self, storage_resource: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhance storage account data with detailed information"""
        try:
            # Parse resource ID
            parsed = parse_azure_resource_id(storage_resource.get("id", ""))

            if not parsed.get("resource_group") or not parsed.get("resource_name"):
                logger.warning(
                    f"Could not parse storage account resource ID: {storage_resource.get('id')}"
                )
                return {}

            resource_group = parsed["resource_group"]
            account_name = parsed["resource_name"]

            # Get detailed storage account information
            storage_account = (
                self.auth_manager.storage_client.storage_accounts.get_properties(
                    resource_group_name=resource_group, account_name=account_name
                )
            )

            return {
                "sku": {
                    "name": (storage_account.sku.name if storage_account.sku else None),
                    "tier": (storage_account.sku.tier if storage_account.sku else None),
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
