"""
GCP Platform Adapter for ADCS Implementation

This file maintains backward compatibility by re-exporting all public interfaces
from the modularized gcp_adapter package.

The actual implementation has been modularized into the gcp_adapter/ directory.
"""

# Re-export all public interfaces from the modular implementation
from .gcp_adapter import (GCP_ADAPTER_METADATA, GCPAdapter, GCPCredentials,
                          GCPResourceMetrics)

# Maintain backward compatibility
__all__ = ["GCPAdapter", "GCPCredentials", "GCPResourceMetrics", "GCP_ADAPTER_METADATA"]
