"""
AWS Platform Adapter for ADCS Implementation

This adapter provides comprehensive AWS resource discovery and data collection
using CloudWatch for metrics and AWS Config for configuration data.
"""

from .base import AWS_ADAPTER_METADATA, AWSCredentials, AWSResourceMetrics
from .main import AWSAdapter

__all__ = [
    "AWSAdapter",
    "AWSCredentials", 
    "AWSResourceMetrics",
    "AWS_ADAPTER_METADATA"
]