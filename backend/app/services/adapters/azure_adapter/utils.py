"""
Utility functions and helpers for Azure adapter
"""

import logging
from typing import Dict, List, Optional, Set

from .base import SUPPORTED_RESOURCE_TYPES, TARGET_MAPPING

logger = logging.getLogger(__name__)


def map_targets_to_resource_types(targets: List[str]) -> Set[str]:
    """Map request targets to Azure resource types"""
    mapped_types = set()
    for target in targets:
        if target in TARGET_MAPPING:
            mapped_types.add(TARGET_MAPPING[target])
        elif target in SUPPORTED_RESOURCE_TYPES:
            mapped_types.add(target)

    return mapped_types or SUPPORTED_RESOURCE_TYPES


def parse_azure_resource_id(resource_id: str) -> Dict[str, Optional[str]]:
    """
    Parse Azure resource ID into components

    Args:
        resource_id: Azure resource ID

    Returns:
        Dictionary with parsed components
    """
    if not resource_id:
        return {}

    parts = resource_id.split("/")

    # Standard Azure resource ID format:
    # /subscriptions/{subscription}/resourceGroups/{resourceGroup}/providers/{provider}/{type}/{name}
    parsed = {
        "subscription_id": None,
        "resource_group": None,
        "provider": None,
        "resource_type": None,
        "resource_name": None,
        "parent_resource": None,
    }

    try:
        if len(parts) >= 5 and parts[1] == "subscriptions":
            parsed["subscription_id"] = parts[2]

        if len(parts) >= 9 and parts[3] == "resourceGroups":
            parsed["resource_group"] = parts[4]

        if len(parts) >= 7 and parts[5] == "providers":
            parsed["provider"] = parts[6]

        if len(parts) >= 9:
            parsed["resource_type"] = f"{parts[6]}/{parts[7]}"
            parsed["resource_name"] = parts[8]

        # Handle nested resources (e.g., SQL databases)
        if len(parts) >= 11:
            parsed["resource_type"] = f"{parts[6]}/{parts[7]}/{parts[9]}"
            parsed["parent_resource"] = parts[8]
            parsed["resource_name"] = parts[10]

    except (IndexError, ValueError) as e:
        logger.warning(f"Failed to parse Azure resource ID {resource_id}: {e}")

    return parsed


def get_vm_power_state(instance_view) -> Optional[str]:
    """Extract VM power state from instance view"""
    if instance_view and instance_view.statuses:
        for status in instance_view.statuses:
            if status.code and status.code.startswith("PowerState/"):
                return status.code.replace("PowerState/", "")
    return None


def normalize_asset_type(resource_type: str) -> str:
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
