"""
Azure Platform Adapter for ADCS Implementation

This adapter provides comprehensive Azure resource discovery and data collection
using Azure Resource Graph for resource discovery and Azure Monitor for metrics.
"""

# Re-export all public interfaces for backward compatibility
from .adapter import AzureAdapter
from .base import AZURE_ADAPTER_METADATA, AzureCredentials, AzureResourceMetrics

__all__ = [
    "AzureAdapter",
    "AzureCredentials",
    "AzureResourceMetrics",
    "AZURE_ADAPTER_METADATA",
]
