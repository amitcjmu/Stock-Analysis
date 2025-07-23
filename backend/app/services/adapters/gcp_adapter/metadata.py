"""
GCP Adapter Metadata

Contains the adapter metadata configuration for registration.
"""

from app.models.collection_flow import AutomationTier
from app.services.collection_flow.adapters import AdapterCapability, AdapterMetadata

# GCP Adapter metadata for registration
GCP_ADAPTER_METADATA = AdapterMetadata(
    name="gcp_adapter",
    version="1.0.0",
    adapter_type="cloud_platform",
    automation_tier=AutomationTier.TIER_1,
    supported_platforms=["GCP"],
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
    required_credentials=["project_id", "service_account_key"],
    configuration_schema={
        "type": "object",
        "required": ["credentials"],
        "properties": {
            "credentials": {
                "type": "object",
                "required": ["project_id", "service_account_key"],
                "properties": {
                    "project_id": {"type": "string"},
                    "service_account_key": {"type": "object"},
                },
            },
            "include_metrics": {"type": "boolean", "default": True},
            "regions": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Specific regions to collect from (optional)",
            },
        },
    },
    description="Comprehensive GCP platform adapter with Asset Inventory and Monitoring integration",
    author="ADCS Team B1",
    documentation_url="https://cloud.google.com/python/docs/reference",
)
