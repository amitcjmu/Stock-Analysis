"""
Azure resource discovery and collection using Resource Graph
"""

import logging
from typing import Any, Dict, List, Set

from .auth import AzureAuthManager
from .exceptions import AZURE_SDK_AVAILABLE


if AZURE_SDK_AVAILABLE:
    from azure.mgmt.resourcegraph.models import QueryRequest

logger = logging.getLogger(__name__)


class AzureResourceCollector:
    """Manages Azure resource discovery and collection"""

    def __init__(self, auth_manager: AzureAuthManager):
        self.auth_manager = auth_manager

    async def test_resource_management_connectivity(self) -> bool:
        """Test Resource Management API connectivity"""
        try:
            # List resource groups (should work with basic permissions)
            list(self.auth_manager.resource_client.resource_groups.list())
            return True
        except Exception:
            return False

    async def test_resource_graph_connectivity(self) -> bool:
        """Test Resource Graph API connectivity"""
        if not AZURE_SDK_AVAILABLE:
            return False

        try:
            # Simple query to test Resource Graph access
            query = QueryRequest(
                subscriptions=[self.auth_manager.subscription_id],
                query="Resources | take 1",
            )
            self.auth_manager.resource_graph_client.resources(query)
            return True
        except Exception:
            return False

    async def collect_resources_with_graph(
        self, resource_types: Set[str], config: Dict[str, Any]
    ) -> Dict[str, List[Dict]]:
        """Use Azure Resource Graph to efficiently collect resource data"""
        if not AZURE_SDK_AVAILABLE:
            logger.error("Azure SDK not available for resource collection")
            return {}

        try:
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
                subscriptions=[self.auth_manager.subscription_id], query=query
            )

            response = self.auth_manager.resource_graph_client.resources(query_request)

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

            logger.info(
                f"Resource Graph collected {len(response.data)} resources across {len(resource_data)} types"
            )

            return resource_data

        except Exception as e:
            logger.error(f"Resource Graph collection failed: {str(e)}")
            return {}

    async def get_available_resources(
        self, supported_resource_types: Set[str]
    ) -> List[str]:
        """
        Get list of available Azure resources for collection

        Args:
            supported_resource_types: Set of supported resource types to check

        Returns:
            List of available resource type identifiers
        """
        try:
            available_types = []

            for resource_type in supported_resource_types:
                try:
                    has_resources = await self.check_resource_type_has_resources(
                        resource_type
                    )
                    if has_resources:
                        available_types.append(resource_type)

                except Exception as e:
                    logger.warning(
                        f"Failed to check resources for {resource_type}: {str(e)}"
                    )

            return available_types

        except Exception as e:
            logger.error(f"Failed to get available Azure resources: {str(e)}")
            return []

    async def check_resource_type_has_resources(self, resource_type: str) -> bool:
        """Quick check if a resource type has any resources using Resource Graph"""
        if not AZURE_SDK_AVAILABLE:
            return False

        try:
            query = f"""
            Resources
            | where type == "{resource_type}"
            | take 1
            | project id
            """

            query_request = QueryRequest(
                subscriptions=[self.auth_manager.subscription_id], query=query
            )

            response = self.auth_manager.resource_graph_client.resources(query_request)
            return len(response.data) > 0

        except Exception:
            return False
