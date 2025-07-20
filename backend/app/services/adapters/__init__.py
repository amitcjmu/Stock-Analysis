"""
Platform Adapters for ADCS Implementation

This module provides concrete implementations of platform-specific data collection
adapters for AWS, Azure, GCP, and on-premises environments.
"""

from .aws_adapter import AWSAdapter
from .azure_adapter import AzureAdapter
from .gcp_adapter import GCPAdapter
from .onpremises_adapter import OnPremisesAdapter
from .orchestrator import AdapterOrchestrator
from .retry_handler import (
    RetryHandler, 
    AdapterErrorHandler,
    retry_adapter_operation,
    ErrorType,
    ErrorSeverity,
    RetryStrategy
)
from .performance_monitor import (
    PerformanceMonitor,
    PerformanceProfiler,
    monitor_performance,
    MetricType,
    OptimizationLevel,
    PerformanceThresholds
)
from .enhanced_base_adapter import (
    EnhancedBaseAdapter,
    AdapterConfiguration
)
from .adapter_manager import (
    AdapterManager,
    AdapterStatus,
    adapter_manager
)

__all__ = [
    "AWSAdapter",
    "AzureAdapter", 
    "GCPAdapter",
    "OnPremisesAdapter",
    "AdapterOrchestrator",
    "RetryHandler",
    "AdapterErrorHandler",
    "retry_adapter_operation",
    "ErrorType",
    "ErrorSeverity", 
    "RetryStrategy",
    "PerformanceMonitor",
    "PerformanceProfiler",
    "monitor_performance",
    "MetricType",
    "OptimizationLevel",
    "PerformanceThresholds",
    "EnhancedBaseAdapter",
    "AdapterConfiguration",
    "AdapterManager",
    "AdapterStatus",
    "adapter_manager",
]