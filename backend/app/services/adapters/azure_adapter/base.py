"""
Base classes and constants for Azure adapter
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Set

from app.models.collection_flow import AutomationTier
from app.services.collection_flow.adapters import AdapterCapability, AdapterMetadata


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


# Supported Azure resource types
SUPPORTED_RESOURCE_TYPES: Set[str] = {
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

# Target mapping for user-friendly resource type names
TARGET_MAPPING = {
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
