"""
GCP Adapter Module - Modularized components for GCP platform integration

This module provides comprehensive GCP resource discovery and data collection
using Cloud Asset Inventory for resource discovery and Cloud Monitoring for metrics.
"""

# Re-export all public interfaces for backward compatibility
from .adapter import GCPAdapter
from .metadata import GCP_ADAPTER_METADATA
from .models import GCPCredentials, GCPResourceMetrics

__all__ = [
    'GCPAdapter',
    'GCPCredentials',
    'GCPResourceMetrics',
    'GCP_ADAPTER_METADATA'
]