"""
Enhanced Base Adapter with Integrated Performance Monitoring

This module provides an enhanced base adapter class that integrates performance
monitoring, error handling, and optimization capabilities for all platform adapters.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.services.collection_flow.adapters import AdapterMetadata, BaseAdapter, CollectionRequest, CollectionResponse

from .performance_monitor import MetricType, PerformanceMonitor, PerformanceThresholds, monitor_performance
from .retry_handler import AdapterErrorHandler, RetryConfig, RetryHandler


@dataclass
class AdapterConfiguration:
    """Configuration for enhanced adapters"""
    adapter_name: str
    platform: str
    enable_performance_monitoring: bool = True
    enable_error_handling: bool = True
    performance_thresholds: Optional[PerformanceThresholds] = None
    retry_config: Optional[RetryConfig] = None
    max_concurrent_operations: int = 5
    enable_caching: bool = True
    cache_ttl_seconds: int = 300
    enable_metrics_export: bool = True


class EnhancedBaseAdapter(BaseAdapter, ABC):
    """
    Enhanced base adapter with integrated performance monitoring and error handling
    
    This class extends the basic BaseAdapter to provide:
    - Automatic performance monitoring
    - Error handling and retry logic
    - Optimization recommendations
    - Resource usage tracking
    - Adaptive configuration tuning
    """
    
    def __init__(self, config: AdapterConfiguration):
        super().__init__()
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{config.adapter_name}")
        
        # Set instance attributes for performance monitoring
        self._adapter_name = config.adapter_name
        self._platform = config.platform
        
        # Initialize performance monitoring
        if config.enable_performance_monitoring:
            self._performance_monitor = PerformanceMonitor(config.performance_thresholds)
        else:
            self._performance_monitor = None
            
        # Initialize error handling
        if config.enable_error_handling:
            self._error_handler = AdapterErrorHandler(config.retry_config)
        else:
            self._error_handler = None
            
        # Initialize caching
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        
        # Track operations
        self._active_operations = 0
        self._operation_queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        
    @monitor_performance(operation_type="validate_credentials")
    async def validate_credentials(self, credentials: Dict[str, Any]) -> bool:
        """Validate platform credentials with performance monitoring"""
        try:
            return await self._validate_credentials_impl(credentials)
        except Exception:
            await self._record_metric(MetricType.ERROR_RATE, 1.0, "errors", "validate_credentials")
            raise
            
    @monitor_performance(operation_type="test_connectivity")
    async def test_connectivity(self, credentials: Dict[str, Any]) -> bool:
        """Test platform connectivity with performance monitoring"""
        try:
            return await self._test_connectivity_impl(credentials)
        except Exception:
            await self._record_metric(MetricType.ERROR_RATE, 1.0, "errors", "test_connectivity")
            raise
            
    async def collect_data(self, request: CollectionRequest) -> CollectionResponse:
        """
        Collect data with comprehensive error handling and performance monitoring
        """
        if self._error_handler:
            # Use error handler for comprehensive error management
            return await self._error_handler.handle_collection_request(
                self._collect_data_impl,
                (request,),
                {},
                self._adapter_name,
                self._platform
            )
        else:
            # Direct execution without error handling
            return await self._collect_data_with_monitoring(request)
            
    @monitor_performance(operation_type="collect_data")
    async def _collect_data_with_monitoring(self, request: CollectionRequest) -> CollectionResponse:
        """Internal method for data collection with monitoring"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Check cache first
            if self.config.enable_caching:
                cached_response = await self._get_cached_response(request)
                if cached_response:
                    await self._record_metric(MetricType.CACHE_HIT_RATE, 1.0, "ratio", "collect_data")
                    return cached_response
                else:
                    await self._record_metric(MetricType.CACHE_HIT_RATE, 0.0, "ratio", "collect_data")
                    
            # Track concurrent operations
            self._active_operations += 1
            await self._record_metric(
                MetricType.CONCURRENT_OPERATIONS, 
                self._active_operations, 
                "count", 
                "collect_data"
            )
            
            # Execute data collection
            response = await self._collect_data_impl(request)
            
            # Record performance metrics
            end_time = asyncio.get_event_loop().time()
            duration_ms = (end_time - start_time) * 1000
            
            await self._record_metric(MetricType.LATENCY, duration_ms, "ms", "collect_data")
            await self._record_metric(MetricType.THROUGHPUT, 1.0, "ops/sec", "collect_data")
            
            if response.data:
                data_size = len(str(response.data))
                await self._record_metric(MetricType.DATA_VOLUME, data_size, "bytes", "collect_data")
                
            # Cache successful response
            if self.config.enable_caching and response.success:
                await self._cache_response(request, response)
                
            return response
            
        except Exception:
            await self._record_metric(MetricType.ERROR_RATE, 1.0, "errors", "collect_data")
            raise
        finally:
            self._active_operations -= 1
            
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics for this adapter"""
        if not self._performance_monitor:
            return {"performance_monitoring": "disabled"}
            
        # Create performance snapshot
        snapshot = await self._performance_monitor.create_snapshot(
            self._adapter_name, 
            self._platform
        )
        
        # Get optimization recommendations
        recommendations = await self._performance_monitor.generate_optimization_recommendations(
            self._adapter_name,
            self._platform
        )
        
        return {
            "adapter_name": self._adapter_name,
            "platform": self._platform,
            "timestamp": snapshot.timestamp.isoformat(),
            "metrics": {
                metric_type.value: value 
                for metric_type, value in snapshot.metrics.items()
            },
            "resource_usage": snapshot.resource_usage,
            "active_operations": snapshot.active_operations,
            "optimization_recommendations": [
                {
                    "title": rec.title,
                    "level": rec.level.value,
                    "description": rec.description,
                    "expected_improvement": rec.expected_improvement,
                    "priority_score": rec.priority_score
                }
                for rec in recommendations
            ]
        }
        
    async def get_health_status(self) -> Dict[str, Any]:
        """Get adapter health status including error rates and performance"""
        health_data = {
            "adapter_name": self._adapter_name,
            "platform": self._platform,
            "timestamp": datetime.utcnow().isoformat(),
            "active_operations": self._active_operations,
            "cache_enabled": self.config.enable_caching,
            "cache_entries": len(self._cache)
        }
        
        if self._error_handler:
            error_health = self._error_handler.get_health_status()
            health_data.update(error_health)
            
        if self._performance_monitor:
            performance_data = self._performance_monitor.get_performance_dashboard_data()
            health_data["performance_health"] = performance_data
            
        return health_data
        
    async def optimize_configuration(self) -> Dict[str, Any]:
        """Automatically optimize adapter configuration based on performance data"""
        if not self._performance_monitor:
            return {"optimization": "performance_monitoring_disabled"}
            
        # Analyze performance trends
        trends = await self._performance_monitor.analyze_performance_trends(
            self._adapter_name,
            self._platform,
            hours=24
        )
        
        optimization_changes = {}
        
        # Adjust concurrent operations based on performance
        latency_trend = trends.get('trends', {}).get('latency')
        if latency_trend:
            current_latency = latency_trend['current_average']
            if current_latency > 5000:  # High latency
                new_concurrency = max(1, self.config.max_concurrent_operations - 1)
                optimization_changes['max_concurrent_operations'] = new_concurrency
            elif current_latency < 1000:  # Low latency
                new_concurrency = min(10, self.config.max_concurrent_operations + 1)
                optimization_changes['max_concurrent_operations'] = new_concurrency
                
        # Adjust cache TTL based on error rates
        error_rate_trend = trends.get('trends', {}).get('error_rate')
        if error_rate_trend and error_rate_trend['current_average'] > 5.0:
            # High error rate - increase cache TTL to reduce API calls
            new_ttl = min(3600, self.config.cache_ttl_seconds * 2)
            optimization_changes['cache_ttl_seconds'] = new_ttl
            
        # Apply optimization changes
        for key, value in optimization_changes.items():
            setattr(self.config, key, value)
            
        return {
            "optimization_applied": len(optimization_changes) > 0,
            "changes": optimization_changes,
            "performance_trends": trends,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    async def _get_cached_response(self, request: CollectionRequest) -> Optional[CollectionResponse]:
        """Get cached response if available and not expired"""
        cache_key = self._generate_cache_key(request)
        
        if cache_key in self._cache:
            cache_time = self._cache_timestamps.get(cache_key)
            if cache_time:
                age_seconds = (datetime.utcnow() - cache_time).total_seconds()
                if age_seconds < self.config.cache_ttl_seconds:
                    return CollectionResponse(**self._cache[cache_key])
                else:
                    # Expired - remove from cache
                    del self._cache[cache_key]
                    del self._cache_timestamps[cache_key]
                    
        return None
        
    async def _cache_response(self, request: CollectionRequest, response: CollectionResponse):
        """Cache a successful response"""
        cache_key = self._generate_cache_key(request)
        
        # Convert response to cacheable format
        cache_data = {
            'success': response.success,
            'data': response.data,
            'metadata': response.metadata,
            'timestamp': response.timestamp,
            'error_message': response.error_message,
            'error_details': response.error_details
        }
        
        self._cache[cache_key] = cache_data
        self._cache_timestamps[cache_key] = datetime.utcnow()
        
        # Limit cache size
        if len(self._cache) > 100:
            # Remove oldest entries
            oldest_key = min(self._cache_timestamps.keys(), 
                           key=lambda k: self._cache_timestamps[k])
            del self._cache[oldest_key]
            del self._cache_timestamps[oldest_key]
            
    def _generate_cache_key(self, request: CollectionRequest) -> str:
        """Generate cache key for a collection request"""
        # Create deterministic key based on request parameters
        key_parts = [
            request.platform,
            request.resource_types[0] if request.resource_types else "all",
            str(sorted(request.filters.items())) if request.filters else "no_filters",
            str(request.options.get('region', 'default')) if request.options else "no_options"
        ]
        return ":".join(key_parts)
        
    async def _record_metric(
        self, 
        metric_type: MetricType, 
        value: float, 
        unit: str, 
        operation: str
    ):
        """Record a performance metric"""
        if self._performance_monitor:
            await self._performance_monitor.record_metric(
                metric_type,
                value,
                unit,
                self._adapter_name,
                self._platform,
                operation
            )
            
    # Abstract methods that must be implemented by concrete adapters
    @abstractmethod
    async def _validate_credentials_impl(self, credentials: Dict[str, Any]) -> bool:
        """Actual credential validation implementation"""
        pass
        
    @abstractmethod
    async def _test_connectivity_impl(self, credentials: Dict[str, Any]) -> bool:
        """Actual connectivity test implementation"""
        pass
        
    @abstractmethod
    async def _collect_data_impl(self, request: CollectionRequest) -> CollectionResponse:
        """Actual data collection implementation"""
        pass
        
    @abstractmethod
    def get_metadata(self) -> AdapterMetadata:
        """Get adapter metadata"""
        pass