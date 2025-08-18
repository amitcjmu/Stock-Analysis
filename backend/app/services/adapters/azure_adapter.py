"""
Azure Platform Adapter for ADCS Implementation

This adapter provides comprehensive Azure resource discovery and data collection
using Azure Resource Graph for resource discovery and Azure Monitor for metrics.

This file maintains backward compatibility by re-exporting all public interfaces
from the modularized azure_adapter package.
"""

# Re-export all public interfaces for backward compatibility
from .azure_adapter import (
    AzureAdapter,
    AzureCredentials,
    AzureResourceMetrics,
    AZURE_ADAPTER_METADATA,
)

# Maintain backward compatibility with direct imports
__all__ = [
    "AzureAdapter",
    "AzureCredentials",
    "AzureResourceMetrics",
    "AZURE_ADAPTER_METADATA",
]

# For compatibility with existing code that might access these directly
import logging

logger = logging.getLogger(__name__)

# Note: The actual implementation has been modularized into the azure_adapter/ directory
# This file exists only for backward compatibility
