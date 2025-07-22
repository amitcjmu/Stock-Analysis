"""
Performance Monitoring Integration Example

This example demonstrates how to integrate the performance monitoring system
with platform adapters and use the advanced optimization features.
"""

import asyncio
import logging
from typing import Any, Dict

from app.services.adapters import (
    AdapterConfiguration,
    AdapterManager,
    EnhancedBaseAdapter,
    PerformanceThresholds,
    RetryConfig,
    adapter_manager,
)
from app.services.collection_flow.adapters import AdapterMetadata, CollectionRequest, CollectionResponse


class ExampleEnhancedAWSAdapter(EnhancedBaseAdapter):
    """Example enhanced AWS adapter with performance monitoring"""
    
    def __init__(self, config: AdapterConfiguration):
        super().__init__(config)
        
    async def _validate_credentials_impl(self, credentials: Dict[str, Any]) -> bool:
        """Validate AWS credentials"""
        # Simulate credential validation
        await asyncio.sleep(0.1)
        return credentials.get('access_key') and credentials.get('secret_key')
        
    async def _test_connectivity_impl(self, credentials: Dict[str, Any]) -> bool:
        """Test AWS connectivity"""
        # Simulate connectivity test
        await asyncio.sleep(0.2)
        return True
        
    async def _collect_data_impl(self, request: CollectionRequest) -> CollectionResponse:
        """Collect data from AWS"""
        # Simulate data collection with varying performance
        import random
        
        # Simulate different latencies
        latency = random.uniform(0.5, 2.0)
        await asyncio.sleep(latency)
        
        # Simulate occasional errors
        if random.random() < 0.05:  # 5% error rate
            raise Exception("Simulated AWS API error")
            
        # Return mock data
        return CollectionResponse(
            success=True,
            data={
                "instances": [
                    {"id": "i-123", "type": "t3.micro", "state": "running"},
                    {"id": "i-456", "type": "t3.small", "state": "stopped"}
                ],
                "region": request.options.get("region", "us-east-1")
            },
            metadata={"collection_time": latency, "resource_count": 2}
        )
        
    def get_metadata(self) -> AdapterMetadata:
        """Get adapter metadata"""
        return AdapterMetadata(
            name="Enhanced AWS Adapter",
            version="1.0.0",
            supported_platforms=["aws"],
            supported_resource_types=["ec2", "rds", "lambda"],
            capabilities=["real_time_collection", "batch_collection", "performance_monitoring"]
        )


async def demonstrate_performance_monitoring():
    """Demonstrate the performance monitoring capabilities"""
    
    # Configure performance thresholds
    performance_thresholds = PerformanceThresholds(
        max_latency_ms=3000.0,
        min_throughput_ops_per_sec=0.5,
        max_error_rate_percent=10.0,
        max_memory_usage_mb=256.0,
        max_cpu_usage_percent=70.0,
        max_concurrent_operations=3,
        cache_hit_rate_target=0.7
    )
    
    # Configure retry strategy
    retry_config = RetryConfig(
        max_retries=3,
        base_delay=1.0,
        max_delay=30.0,
        circuit_breaker_enabled=True,
        circuit_breaker_threshold=3
    )
    
    # Create adapter configuration
    config = AdapterConfiguration(
        adapter_name="enhanced_aws_adapter",
        platform="aws",
        enable_performance_monitoring=True,
        enable_error_handling=True,
        performance_thresholds=performance_thresholds,
        retry_config=retry_config,
        max_concurrent_operations=3,
        enable_caching=True,
        cache_ttl_seconds=300
    )
    
    # Register adapter with manager
    await adapter_manager.register_adapter(
        "enhanced_aws_adapter",
        ExampleEnhancedAWSAdapter,
        config
    )
    
    # Start the adapter
    await adapter_manager.start_adapter("enhanced_aws_adapter")
    
    # Start monitoring
    await adapter_manager.start_monitoring()
    
    print("🚀 Performance monitoring demonstration started")
    print("=" * 60)
    
    # Simulate multiple requests to generate performance data
    for i in range(20):
        request = CollectionRequest(
            platform="aws",
            resource_types=["ec2"],
            filters={"region": "us-east-1"},
            options={"region": "us-east-1"}
        )
        
        try:
            response = await adapter_manager.execute_collection_request(request)
            print(f"Request {i+1}: {'✅ Success' if response.success else '❌ Failed'}")
            
        except Exception as e:
            print(f"Request {i+1}: ❌ Exception - {str(e)}")
            
        # Small delay between requests
        await asyncio.sleep(0.1)
        
    print("\n📊 Performance Analysis")
    print("=" * 40)
    
    # Get performance dashboard
    dashboard = await adapter_manager.get_performance_dashboard()
    
    print(f"Total Requests: {dashboard['total_requests']}")
    print(f"Success Rate: {dashboard['overall_success_rate']:.1%}")
    print(f"Active Adapters: {dashboard['active_adapters']}/{dashboard['total_adapters']}")
    
    # Get detailed adapter metrics
    adapter_status = await adapter_manager.get_adapter_status("enhanced_aws_adapter")
    print(f"\nAdapter Success Rate: {adapter_status['success_rate']:.1%}")
    
    # Get performance metrics from the adapter directly
    adapter_instance = adapter_manager._adapter_instances.get("enhanced_aws_adapter")
    if adapter_instance:
        metrics = await adapter_instance.get_performance_metrics()
        
        print("\n🔍 Detailed Performance Metrics:")
        for metric_type, value in metrics.get("metrics", {}).items():
            print(f"  {metric_type}: {value:.2f}")
            
        print("\n💡 Optimization Recommendations:")
        recommendations = metrics.get("optimization_recommendations", [])
        for i, rec in enumerate(recommendations[:3], 1):  # Show top 3
            print(f"  {i}. {rec['title']} ({rec['level']})")
            print(f"     {rec['description']}")
            print(f"     Expected: {rec['expected_improvement']}")
            
    # Demonstrate automatic optimization
    print("\n⚡ Running Automatic Optimization")
    print("=" * 40)
    
    optimization_results = await adapter_manager.optimize_all_adapters()
    
    for adapter_id, result in optimization_results["results"].items():
        if result.get("optimization_applied"):
            print(f"✅ {adapter_id}: Applied {len(result['changes'])} optimizations")
            for param, value in result["changes"].items():
                print(f"   • {param}: {value}")
        else:
            print(f"ℹ️  {adapter_id}: No optimizations needed")
            
    print(f"\nTotal adapters optimized: {optimization_results['adapters_optimized']}")
    print(f"Total configuration changes: {optimization_results['total_changes']}")
    
    # Show health status
    print("\n🏥 Adapter Health Status")
    print("=" * 40)
    
    health_data = await adapter_instance.get_health_status()
    
    print(f"Adapter: {health_data['adapter_name']}")
    print(f"Platform: {health_data['platform']}")
    print(f"Active Operations: {health_data['active_operations']}")
    print(f"Cache Entries: {health_data['cache_entries']}")
    
    if "performance_health" in health_data:
        perf_health = health_data["performance_health"]
        print(f"Health Score: {perf_health['health_status']}")
        print(f"Recent Activity: {perf_health['recent_activity']} metrics")
        
    # Performance trends analysis
    if adapter_instance._performance_monitor:
        trends = await adapter_instance._performance_monitor.analyze_performance_trends(
            "enhanced_aws_adapter",
            "aws",
            hours=1
        )
        
        print("\n📈 Performance Trends (Last Hour)")
        print("=" * 40)
        
        for metric_type, trend_data in trends.get("trends", {}).items():
            direction = trend_data["direction"]
            change = trend_data["change_percent"]
            
            if direction == "increasing":
                emoji = "📈" if metric_type != "error_rate" else "📉"
            elif direction == "decreasing":
                emoji = "📉" if metric_type != "error_rate" else "📈"
            else:
                emoji = "➡️"
                
            print(f"  {emoji} {metric_type}: {direction} ({change:+.1f}%)")
            
    # Stop monitoring
    await adapter_manager.stop_monitoring()
    await adapter_manager.stop_adapter("enhanced_aws_adapter")
    
    print("\n✅ Performance monitoring demonstration completed")


async def demonstrate_advanced_features():
    """Demonstrate advanced performance monitoring features"""
    
    print("\n🚀 Advanced Features Demonstration")
    print("=" * 50)
    
    # Create multiple adapters for comparison
    platforms = ["aws", "azure", "gcp"]
    
    for platform in platforms:
        config = AdapterConfiguration(
            adapter_name=f"enhanced_{platform}_adapter",
            platform=platform,
            enable_performance_monitoring=True,
            enable_error_handling=True,
            max_concurrent_operations=2
        )
        
        await adapter_manager.register_adapter(
            f"enhanced_{platform}_adapter",
            ExampleEnhancedAWSAdapter,  # Using same class for demo
            config
        )
        
        await adapter_manager.start_adapter(f"enhanced_{platform}_adapter")
        
    # Simulate cross-platform workload
    requests = []
    for platform in platforms:
        for i in range(5):
            request = CollectionRequest(
                platform=platform,
                resource_types=["compute"],
                filters={"region": "us-east-1"}
            )
            requests.append((request, platform))
            
    # Execute requests
    for request, platform in requests:
        try:
            response = await adapter_manager.execute_collection_request(request)
            print(f"{platform}: {'✅' if response.success else '❌'}")
        except Exception as e:
            print(f"{platform}: ❌ {str(e)}")
            
    # Get comprehensive dashboard
    dashboard = await adapter_manager.get_performance_dashboard()
    
    print("\n📊 Multi-Platform Performance Summary")
    print("=" * 50)
    print(f"Overall Success Rate: {dashboard['overall_success_rate']:.1%}")
    print(f"Total Requests: {dashboard['total_requests']}")
    
    # Show per-adapter performance
    for adapter_id, details in dashboard["adapter_details"].items():
        if "error" not in details:
            metrics = details.get("metrics", {})
            recommendations = details.get("optimization_recommendations", [])
            
            print(f"\n{adapter_id}:")
            print(f"  Latency: {metrics.get('latency', 0):.1f}ms")
            print(f"  Recommendations: {len(recommendations)}")
            
    # Clean up
    for platform in platforms:
        await adapter_manager.stop_adapter(f"enhanced_{platform}_adapter")


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run demonstrations
    asyncio.run(demonstrate_performance_monitoring())
    asyncio.run(demonstrate_advanced_features())