"""
Platform Adapters for ADCS Implementation

This module provides concrete implementations of platform-specific data collection
adapters for AWS, Azure, GCP, and on-premises environments.
"""

from .adapter_manager import AdapterManager, AdapterStatus, adapter_manager
from .aws_adapter import AWSAdapter
from .azure_adapter import AzureAdapter
from .enhanced_base_adapter import AdapterConfiguration, EnhancedBaseAdapter
from .gcp_adapter import GCPAdapter
from .onpremises_adapter import OnPremisesAdapter
from .orchestrator import AdapterOrchestrator
from .performance_monitor import (
    MetricType,
    OptimizationLevel,
    PerformanceMonitor,
    PerformanceProfiler,
    PerformanceThresholds,
    monitor_performance,
)
from .retry_handler import (
    AdapterErrorHandler,
    ErrorSeverity,
    ErrorType,
    RetryHandler,
    RetryStrategy,
    retry_adapter_operation,
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