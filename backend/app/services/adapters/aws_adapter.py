"""
AWS Platform Adapter for ADCS Implementation

This adapter provides comprehensive AWS resource discovery and data collection
using CloudWatch for metrics and AWS Config for configuration data.

This file maintains backward compatibility by re-exporting all public interfaces
from the modularized aws_adapter package.
"""

# Re-export all public interfaces for backward compatibility
from .aws_adapter.base import (AWS_ADAPTER_METADATA, AWSCredentials,
                               AWSResourceMetrics)
from .aws_adapter.main import AWSAdapter

# Maintain backward compatibility with direct imports
__all__ = ["AWSAdapter", "AWSCredentials", "AWSResourceMetrics", "AWS_ADAPTER_METADATA"]

# For compatibility with existing code that might access these directly
import logging

logger = logging.getLogger(__name__)

# Note: The actual implementation has been modularized into the aws_adapter/ directory
# This file exists only for backward compatibility
