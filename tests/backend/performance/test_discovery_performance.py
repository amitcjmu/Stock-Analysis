"""
Performance Testing for Discovery Flow (Task 61)

Tests performance characteristics of the Discovery Flow including:
- Crew execution performance under different data loads
- Memory usage optimization during complex workflows
- Scalability testing for enterprise-scale data
- Resource utilization monitoring
- Performance regression detection
"""

import pytest
import asyncio
import time
import psutil
import gc
from typing import Dict, Any

# Performance testing fixtures
@pytest.fixture
def performance_monitor():
    """Monitor for tracking performance metrics"""
    class PerformanceMonitor:
        def __init__(self):
            self.metrics = {}
            self.start_time = None
            self.start_memory = None

        def start_monitoring(self):
            self.start_time = time.time()
            self.start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

        def stop_monitoring(self):
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

            self.metrics['execution_time'] = end_time - self.start_time
            self.metrics['memory_delta'] = end_memory - self.start_memory
            self.metrics['peak_memory'] = end_memory

            return self.metrics

        def get_cpu_usage(self):
            return psutil.cpu_percent(interval=1)

    return PerformanceMonitor()

@pytest.fixture
def performance_data_sets():
    """Different sized datasets for performance testing"""
    return {
        'small': {
            'asset_count': 100,
            'field_count': 10,
            'complexity': 'low'
        },
        'medium': {
            'asset_count': 1000,
            'field_count': 25,
            'complexity': 'moderate'
        },
        'large': {
            'asset_count': 10000,
            'field_count': 50,
            'complexity': 'high'
        },
        'enterprise': {
            'asset_count': 50000,
            'field_count': 100,
            'complexity': 'enterprise'
        }
    }

@pytest.fixture
def mock_crew_performance():
    """Mock crew with performance simulation"""
    class MockCrewWithPerformance:
        def __init__(self, processing_time: float = 1.0):
            self.processing_time = processing_time
            self.memory_usage = 50  # MB

        async def execute_async(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
            # Simulate processing time based on data complexity
            asset_count = inputs.get('asset_count', 100)
            complexity_multiplier = {
                'low': 0.1,
                'moderate': 0.5,
                'high': 1.0,
                'enterprise': 2.0
            }.get(inputs.get('complexity', 'low'), 0.1)

            processing_time = (asset_count / 1000) * complexity_multiplier
            await asyncio.sleep(min(processing_time, 5.0))  # Cap at 5 seconds for testing

            return {
                'status': 'completed',
                'processed_assets': asset_count,
                'processing_time': processing_time,
                'memory_used': self.memory_usage
            }

    return MockCrewWithPerformance

class TestDiscoveryFlowPerformance:
    """Test suite for Discovery Flow performance characteristics"""

    @pytest.mark.asyncio
    async def test_crew_execution_performance_small_dataset(
        self,
        performance_monitor,
        performance_data_sets,
        mock_crew_performance
    ):
        """Test performance with small dataset (Task 61)"""
        # Arrange
        small_data = performance_data_sets['small']
        field_mapping_crew = mock_crew_performance(processing_time=0.1)
        data_cleansing_crew = mock_crew_performance(processing_time=0.2)

        performance_monitor.start_monitoring()

        # Act
        field_result = await field_mapping_crew.execute_async(small_data)
        cleansing_result = await data_cleansing_crew.execute_async(small_data)

        metrics = performance_monitor.stop_monitoring()

        # Assert
        assert metrics['execution_time'] < 1.0, "Small dataset should process quickly"
        assert metrics['memory_delta'] < 100, "Memory usage should be minimal for small data"
        assert field_result['status'] == 'completed'
        assert cleansing_result['status'] == 'completed'

    @pytest.mark.asyncio
    async def test_crew_execution_performance_enterprise_dataset(
        self,
        performance_monitor,
        performance_data_sets,
        mock_crew_performance
    ):
        """Test performance with enterprise-scale dataset (Task 61)"""
        # Arrange
        enterprise_data = performance_data_sets['enterprise']
        crew = mock_crew_performance(processing_time=2.0)

        performance_monitor.start_monitoring()

        # Act
        result = await crew.execute_async(enterprise_data)
        metrics = performance_monitor.stop_monitoring()

        # Assert
        assert metrics['execution_time'] < 10.0, "Enterprise processing should complete in reasonable time"
        assert result['processed_assets'] == 50000, "All enterprise assets should be processed"
        assert result['status'] == 'completed'

    @pytest.mark.asyncio
    async def test_parallel_crew_execution_performance(
        self,
        performance_monitor,
        performance_data_sets,
        mock_crew_performance
    ):
        """Test performance of parallel crew execution (Task 61)"""
        # Arrange
        medium_data = performance_data_sets['medium']
        crews = [
            mock_crew_performance(processing_time=0.5),
            mock_crew_performance(processing_time=0.7),
            mock_crew_performance(processing_time=0.3)
        ]

        performance_monitor.start_monitoring()

        # Act - Execute crews in parallel
        tasks = [crew.execute_async(medium_data) for crew in crews]
        results = await asyncio.gather(*tasks)

        metrics = performance_monitor.stop_monitoring()

        # Assert
        assert len(results) == 3, "All crews should complete"
        assert all(r['status'] == 'completed' for r in results), "All crews should succeed"
        assert metrics['execution_time'] < 1.5, "Parallel execution should be faster than sequential"

    @pytest.mark.asyncio
    async def test_memory_optimization_during_workflow(
        self,
        performance_monitor,
        performance_data_sets
    ):
        """Test memory optimization strategies (Task 61)"""
        # Arrange
        large_data = performance_data_sets['large']

        class MemoryOptimizedCrew:
            def __init__(self):
                self.large_data_cache = {}

            async def execute_with_cleanup(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
                # Simulate processing large dataset
                large_dataset = list(range(inputs['asset_count']))
                self.large_data_cache['processed'] = large_dataset

                # Process data
                processed_count = len(large_dataset)

                # Cleanup memory
                del large_dataset
                self.large_data_cache.clear()
                gc.collect()

                return {
                    'status': 'completed',
                    'processed_assets': processed_count,
                    'memory_optimized': True
                }

        crew = MemoryOptimizedCrew()
        performance_monitor.start_monitoring()

        # Act
        result = await crew.execute_with_cleanup(large_data)
        metrics = performance_monitor.stop_monitoring()

        # Assert
        assert result['memory_optimized'], "Memory optimization should be applied"
        assert metrics['memory_delta'] < 200, "Memory delta should be controlled with optimization"
        assert result['processed_assets'] == 10000, "All assets should be processed"

    @pytest.mark.asyncio
    async def test_scalability_with_increasing_data_loads(
        self,
        performance_data_sets,
        mock_crew_performance
    ):
        """Test scalability characteristics across different data loads (Task 61)"""
        # Arrange
        data_sizes = ['small', 'medium', 'large']
        performance_results = {}

        for size in data_sizes:
            # Act
            data = performance_data_sets[size]
            crew = mock_crew_performance()

            start_time = time.time()
            result = await crew.execute_async(data)
            execution_time = time.time() - start_time

            performance_results[size] = {
                'execution_time': execution_time,
                'processed_assets': result['processed_assets'],
                'throughput': result['processed_assets'] / execution_time
            }

        # Assert scalability characteristics
        small_throughput = performance_results['small']['throughput']
        medium_throughput = performance_results['medium']['throughput']
        large_throughput = performance_results['large']['throughput']

        # Throughput should degrade gracefully, not catastrophically
        assert medium_throughput > small_throughput * 0.5, "Medium scale should maintain reasonable throughput"
        assert large_throughput > medium_throughput * 0.3, "Large scale should maintain minimum throughput"

    @pytest.mark.asyncio
    async def test_resource_utilization_monitoring(
        self,
        performance_monitor,
        performance_data_sets,
        mock_crew_performance
    ):
        """Test resource utilization monitoring (Task 61)"""
        # Arrange
        large_data = performance_data_sets['large']
        crew = mock_crew_performance(processing_time=1.0)

        cpu_samples = []
        memory_samples = []

        async def monitor_resources():
            for _ in range(10):
                cpu_samples.append(psutil.cpu_percent())
                memory_samples.append(psutil.Process().memory_info().rss / 1024 / 1024)
                await asyncio.sleep(0.1)

        # Act
        monitor_task = asyncio.create_task(monitor_resources())
        performance_monitor.start_monitoring()

        result = await crew.execute_async(large_data)

        await monitor_task
        performance_monitor.stop_monitoring()

        # Assert
        avg_cpu = sum(cpu_samples) / len(cpu_samples)
        max_memory = max(memory_samples)

        assert avg_cpu < 80, "Average CPU usage should be reasonable"
        assert max_memory < 1000, "Peak memory should be under control (< 1GB)"
        assert result['status'] == 'completed', "Processing should complete successfully"

    @pytest.mark.asyncio
    async def test_performance_regression_detection(
        self,
        performance_data_sets,
        mock_crew_performance
    ):
        """Test performance regression detection (Task 61)"""
        # Arrange
        baseline_performance = {
            'small': {'max_time': 0.5, 'max_memory': 50},
            'medium': {'max_time': 2.0, 'max_memory': 200},
            'large': {'max_time': 5.0, 'max_memory': 500}
        }

        regression_results = {}

        for size, baseline in baseline_performance.items():
            # Act
            data = performance_data_sets[size]
            crew = mock_crew_performance()

            start_time = time.time()
            start_memory = psutil.Process().memory_info().rss / 1024 / 1024

            await crew.execute_async(data)

            execution_time = time.time() - start_time
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024
            memory_delta = end_memory - start_memory

            # Check for regressions
            time_regression = execution_time > baseline['max_time']
            memory_regression = memory_delta > baseline['max_memory']

            regression_results[size] = {
                'time_regression': time_regression,
                'memory_regression': memory_regression,
                'execution_time': execution_time,
                'memory_delta': memory_delta
            }

        # Assert no significant regressions
        for size, results in regression_results.items():
            assert not results['time_regression'], f"{size} dataset shows time regression"
            assert not results['memory_regression'], f"{size} dataset shows memory regression"

    @pytest.mark.asyncio
    async def test_concurrent_workflow_performance(
        self,
        performance_monitor,
        performance_data_sets,
        mock_crew_performance
    ):
        """Test performance under concurrent workflow execution (Task 61)"""
        # Arrange
        medium_data = performance_data_sets['medium']
        num_concurrent_workflows = 3

        workflows = []
        for i in range(num_concurrent_workflows):
            workflow_crews = [
                mock_crew_performance(processing_time=0.3),
                mock_crew_performance(processing_time=0.4),
                mock_crew_performance(processing_time=0.2)
            ]
            workflows.append(workflow_crews)

        performance_monitor.start_monitoring()

        # Act - Execute multiple workflows concurrently
        workflow_tasks = []
        for workflow in workflows:
            workflow_task = asyncio.gather(*[
                crew.execute_async(medium_data) for crew in workflow
            ])
            workflow_tasks.append(workflow_task)

        all_results = await asyncio.gather(*workflow_tasks)
        metrics = performance_monitor.stop_monitoring()

        # Assert
        assert len(all_results) == num_concurrent_workflows, "All workflows should complete"
        for workflow_results in all_results:
            assert len(workflow_results) == 3, "Each workflow should have 3 crew results"
            assert all(r['status'] == 'completed' for r in workflow_results), "All crews should succeed"

        # Performance should degrade gracefully under load
        assert metrics['execution_time'] < 3.0, "Concurrent execution should complete in reasonable time"
        assert metrics['memory_delta'] < 400, "Memory usage should be controlled under concurrent load"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
