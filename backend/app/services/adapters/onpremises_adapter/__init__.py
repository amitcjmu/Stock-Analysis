"""
On-Premises Platform Adapter Package

This package provides modular components for on-premises infrastructure discovery.
"""

from .adapter import OnPremisesAdapter
from .models import OnPremisesCredentials, DiscoveredHost

# Re-export metadata for backward compatibility
from app.services.collection_flow.adapters import AdapterMetadata, AdapterCapability
from app.models.collection_flow import AutomationTier

# On-premises Adapter metadata for registration
ONPREMISES_ADAPTER_METADATA = AdapterMetadata(
    name="onpremises_adapter",
    version="1.0.0",
    adapter_type="on_premises",
    automation_tier=AutomationTier.TIER_2,
    supported_platforms=["OnPremises"],
    capabilities=[
        AdapterCapability.SERVER_DISCOVERY,
        AdapterCapability.NETWORK_DISCOVERY,
        AdapterCapability.DEPENDENCY_MAPPING,
        AdapterCapability.CREDENTIAL_VALIDATION
    ],
    required_credentials=[
        "network_ranges"
    ],
    configuration_schema={
        "type": "object",
        "required": ["credentials"],
        "properties": {
            "credentials": {
                "type": "object",
                "required": ["network_ranges"],
                "properties": {
                    "network_ranges": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "CIDR network ranges to scan (e.g., ['192.168.1.0/24'])"
                    },
                    "ssh_username": {"type": "string"},
                    "ssh_password": {"type": "string"},
                    "ssh_private_key": {"type": "string"},
                    "ssh_port": {"type": "integer", "default": 22},
                    "snmp_community": {"type": "string", "default": "public"},
                    "snmp_version": {"type": "string", "default": "2c"},
                    "snmp_username": {"type": "string"},
                    "snmp_auth_protocol": {"type": "string"},
                    "snmp_auth_key": {"type": "string"},
                    "snmp_priv_protocol": {"type": "string"},
                    "snmp_priv_key": {"type": "string"},
                    "wmi_username": {"type": "string"},
                    "wmi_password": {"type": "string"},
                    "wmi_domain": {"type": "string"},
                    "timeout": {"type": "integer", "default": 10},
                    "max_concurrent_scans": {"type": "integer", "default": 50}
                }
            },
            "include_port_scanning": {"type": "boolean", "default": True},
            "include_detailed_info": {"type": "boolean", "default": True},
            "include_topology": {"type": "boolean", "default": False},
            "max_hosts_per_network": {"type": "integer", "default": 1000},
            "custom_ports": {
                "type": "array",
                "items": {"type": "integer"},
                "description": "Additional ports to scan"
            }
        }
    },
    description="Comprehensive on-premises infrastructure adapter with network scanning, SNMP, SSH, and WMI support",
    author="ADCS Team B1",
    documentation_url="https://docs.python.org/3/library/socket.html"
)

__all__ = [
    "OnPremisesAdapter",
    "OnPremisesCredentials",
    "DiscoveredHost",
    "ONPREMISES_ADAPTER_METADATA"
]