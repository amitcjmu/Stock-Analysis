"""
Base classes and constants for AWS adapter
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.services.collection_flow.adapters import AdapterMetadata, AdapterCapability
from app.models.collection_flow import AutomationTier


@dataclass
class AWSCredentials:
    """AWS credentials configuration"""
    access_key_id: str
    secret_access_key: str
    session_token: Optional[str] = None
    region: str = "us-east-1"
    
    
@dataclass
class AWSResourceMetrics:
    """AWS resource performance metrics"""
    resource_id: str
    resource_type: str
    cpu_utilization: Optional[float] = None
    memory_utilization: Optional[float] = None
    network_in: Optional[float] = None
    network_out: Optional[float] = None
    disk_read_ops: Optional[float] = None
    disk_write_ops: Optional[float] = None
    timestamp: Optional[datetime] = None


# AWS Adapter metadata for registration
AWS_ADAPTER_METADATA = AdapterMetadata(
    name="aws_adapter",
    version="1.0.0",
    adapter_type="cloud_platform",
    automation_tier=AutomationTier.TIER_1,
    supported_platforms=["AWS"],
    capabilities=[
        AdapterCapability.SERVER_DISCOVERY,
        AdapterCapability.APPLICATION_DISCOVERY,
        AdapterCapability.DATABASE_DISCOVERY,
        AdapterCapability.NETWORK_DISCOVERY,
        AdapterCapability.DEPENDENCY_MAPPING,
        AdapterCapability.PERFORMANCE_METRICS,
        AdapterCapability.CONFIGURATION_EXPORT,
        AdapterCapability.CREDENTIAL_VALIDATION
    ],
    required_credentials=[
        "access_key_id",
        "secret_access_key"
    ],
    configuration_schema={
        "type": "object",
        "required": ["credentials", "region"],
        "properties": {
            "credentials": {
                "type": "object",
                "required": ["access_key_id", "secret_access_key"],
                "properties": {
                    "access_key_id": {"type": "string"},
                    "secret_access_key": {"type": "string"},
                    "session_token": {"type": "string"},
                    "region": {"type": "string", "default": "us-east-1"}
                }
            },
            "region": {"type": "string", "default": "us-east-1"},
            "include_metrics": {"type": "boolean", "default": True},
            "include_config": {"type": "boolean", "default": True},
            "collect_all_regions": {"type": "boolean", "default": False}
        }
    },
    description="Comprehensive AWS platform adapter with CloudWatch and Config integration",
    author="ADCS Team B1",
    documentation_url="https://docs.aws.amazon.com/sdk-for-python/"
)