"""
On-Premises Platform Adapter for ADCS Implementation

This module maintains backward compatibility by re-exporting all interfaces
from the modularized onpremises_adapter package.

The implementation has been refactored into separate modules:
- models.py: Data models (OnPremisesCredentials, DiscoveredHost)
- network_scanner.py: Network scanning functionality
- service_discovery.py: Service detection and identification
- protocol_collectors.py: Protocol-specific collectors (SNMP, SSH, WMI)
- topology.py: Network topology discovery
- data_transformer.py: Data transformation logic
- adapter.py: Main adapter class
"""

# Re-export all public interfaces for backward compatibility
from .onpremises_adapter import ONPREMISES_ADAPTER_METADATA, DiscoveredHost, OnPremisesAdapter, OnPremisesCredentials

__all__ = [
    "OnPremisesAdapter",
    "OnPremisesCredentials", 
    "DiscoveredHost",
    "ONPREMISES_ADAPTER_METADATA"
]