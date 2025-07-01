"""
Performance tests for V3 API and consolidated database
Tests response times, throughput, and resource usage
"""

import pytest
import pytest_asyncio
import asyncio
import time
import statistics
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any
import httpx
import psutil
import json

from app.core.database import AsyncSessionLocal
from app.models.client_account import ClientAccount, Engagement, User
from app.services.v3.asset_service import V3AssetService
from sqlalchemy import text
import uuid

# Configure pytest to use asyncio
pytestmark = pytest.mark.asyncio


class PerformanceMetrics:
    """Helper class to track performance metrics"""
    
    def __init__(self):
        self.response_times: List[float] = []
        self.errors: List[str] = []
        self.start_time = time.time()
        self.end_time = None
    
    def add_response_time(self, duration: float):
        """Add a response time measurement"""
        self.response_times.append(duration)
    
    def add_error(self, error: str):
        """Add an error"""
        self.errors.append(error)
    
    def finish(self):
        """Mark the test as finished"""
        self.end_time = time.time()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary statistics"""
        if not self.response_times:
            return {"error": "No response times recorded"}
        
        return {
            "total_requests": len(self.response_times),
            "successful_requests": len(self.response_times),
            "failed_requests": len(self.errors),
            "total_duration": self.end_time - self.start_time if self.end_time else time.time() - self.start_time,
            "min_response_time": min(self.response_times),
            "max_response_time": max(self.response_times),
            "avg_response_time": statistics.mean(self.response_times),
            "median_response_time": statistics.median(self.response_times),
            "p95_response_time": statistics.quantiles(self.response_times, n=20)[18] if len(self.response_times) > 20 else max(self.response_times),
            "p99_response_time": statistics.quantiles(self.response_times, n=100)[98] if len(self.response_times) > 100 else max(self.response_times),
            "requests_per_second": len(self.response_times) / (self.end_time - self.start_time) if self.end_time else 0
        }


class TestAPIPerformance:
    """Performance tests for V3 API endpoints"""
    
    @pytest_asyncio.fixture
    def api_client(self):
        """Create HTTP client for API tests"""
        return httpx.AsyncClient(
            base_url="http://localhost:8000",
            timeout=30.0
        )
    
    @pytest_asyncio.fixture
    def auth_headers(self):
        """Create authenticated headers"""
        return {
            "Authorization": "Bearer test-token",
            "Content-Type": "application/json",
            "X-Client-Account-ID": "550e8400-e29b-41d4-a716-446655440000",
            "X-Engagement-ID": "660e8400-e29b-41d4-a716-446655440000"
        }
    
    async def test_data_import_upload_performance(self, api_client, auth_headers):
        """Test performance of file upload endpoint"""
        metrics = PerformanceMetrics()
        
        # Generate CSV content of various sizes
        test_sizes = [
            (100, "small"),      # 100 rows
            (1000, "medium"),    # 1,000 rows
            (10000, "large"),    # 10,000 rows
            (50000, "xlarge")    # 50,000 rows
        ]
        
        for row_count, size_name in test_sizes:
            # Generate CSV content
            csv_lines = ["hostname,ip,os,cpu,memory,storage"]
            for i in range(row_count):
                csv_lines.append(f"server-{i:05d},10.0.{i//256}.{i%256},Ubuntu,8,16384,512000")
            
            csv_content = "\n".join(csv_lines)
            file_size_mb = len(csv_content) / (1024 * 1024)
            
            # Measure upload time
            start_time = time.time()
            
            try:
                response = await api_client.post(
                    "/api/v3/data-import/imports/upload",
                    files={"file": (f"test_{size_name}.csv", csv_content, "text/csv")},
                    headers=auth_headers
                )
                
                duration = time.time() - start_time
                
                if response.status_code == 201:
                    metrics.add_response_time(duration)
                    throughput_mbps = (file_size_mb / duration) * 8
                    
                    print(f"\n📊 {size_name.upper()} file upload ({row_count} rows):")
                    print(f"   - File size: {file_size_mb:.2f} MB")
                    print(f"   - Upload time: {duration:.2f}s")
                    print(f"   - Throughput: {throughput_mbps:.2f} Mbps")
                else:
                    metrics.add_error(f"Upload failed: {response.status_code}")
                    
            except Exception as e:
                metrics.add_error(str(e))
        
        metrics.finish()
        summary = metrics.get_summary()
        
        # Performance assertions
        assert summary["avg_response_time"] < 10.0, "Average upload time should be < 10s"
        assert summary["failed_requests"] == 0, "All uploads should succeed"
    
    async def test_discovery_flow_creation_performance(self, api_client, auth_headers):
        """Test performance of discovery flow creation with varying data sizes"""
        metrics = PerformanceMetrics()
        
        test_sizes = [10, 50, 100, 500, 1000]
        
        for size in test_sizes:
            # Generate test data
            test_data = []
            for i in range(size):
                test_data.append({
                    "asset_name": f"server-{i:04d}",
                    "asset_type": "server",
                    "ip_address": f"10.0.{i//256}.{i%256}",
                    "cpu_cores": 8,
                    "memory_gb": 16,
                    "storage_gb": 500
                })
            
            start_time = time.time()
            
            try:
                response = await api_client.post(
                    "/api/v3/discovery-flow/flows",
                    json={
                        "name": f"Performance Test - {size} records",
                        "raw_data": test_data,
                        "execution_mode": "database"
                    },
                    headers=auth_headers
                )
                
                duration = time.time() - start_time
                
                if response.status_code == 201:
                    metrics.add_response_time(duration)
                    records_per_second = size / duration
                    
                    print(f"\n🚀 Flow creation with {size} records:")
                    print(f"   - Creation time: {duration:.2f}s")
                    print(f"   - Rate: {records_per_second:.0f} records/s")
                else:
                    metrics.add_error(f"Flow creation failed: {response.status_code}")
                    
            except Exception as e:
                metrics.add_error(str(e))
        
        metrics.finish()
        summary = metrics.get_summary()
        
        # Performance assertions
        assert summary["p95_response_time"] < 5.0, "95th percentile should be < 5s"
        assert summary["failed_requests"] == 0, "All flow creations should succeed"
    
    async def test_concurrent_api_requests(self, api_client, auth_headers):
        """Test API performance under concurrent load"""
        metrics = PerformanceMetrics()
        
        async def make_request(request_id: int):
            """Make a single API request"""
            start_time = time.time()
            
            try:
                response = await api_client.get(
                    "/api/v3/discovery-flow/health",
                    headers=auth_headers
                )
                
                duration = time.time() - start_time
                
                if response.status_code == 200:
                    metrics.add_response_time(duration)
                else:
                    metrics.add_error(f"Request {request_id} failed: {response.status_code}")
                    
            except Exception as e:
                metrics.add_error(f"Request {request_id} error: {str(e)}")
        
        # Test with different concurrency levels
        concurrency_levels = [1, 10, 50, 100]
        
        for concurrency in concurrency_levels:
            print(f"\n🔄 Testing with {concurrency} concurrent requests...")
            
            tasks = []
            for i in range(concurrency):
                tasks.append(make_request(i))
            
            start_time = time.time()
            await asyncio.gather(*tasks)
            duration = time.time() - start_time
            
            print(f"   - Total time: {duration:.2f}s")
            print(f"   - Requests/second: {concurrency / duration:.0f}")
        
        metrics.finish()
        summary = metrics.get_summary()
        
        # Performance assertions
        assert summary["avg_response_time"] < 1.0, "Average response time should be < 1s"
        assert summary["failed_requests"] / summary["total_requests"] < 0.01, "Error rate should be < 1%"


class TestDatabasePerformance:
    """Performance tests for database operations"""
    
    async def test_bulk_insert_performance(self):
        """Test performance of bulk insert operations"""
        async with AsyncSessionLocal() as db:
            # Create test context
            client_id = str(uuid.uuid4())
            engagement_id = str(uuid.uuid4())
            
            asset_service = V3AssetService(db, client_id, engagement_id)
            
            metrics = PerformanceMetrics()
            
            # Test different batch sizes
            batch_sizes = [100, 500, 1000, 5000]
            
            for batch_size in batch_sizes:
                # Generate test data
                assets_data = []
                for i in range(batch_size):
                    assets_data.append({
                        "asset_name": f"perf-test-{i:05d}",
                        "asset_type": "server",
                        "ip_address": f"192.168.{i//256}.{i%256}",
                        "cpu_cores": 8,
                        "memory_gb": 32,
                        "storage_gb": 1000
                    })
                
                # Measure insert time
                start_time = time.time()
                
                try:
                    created_assets = await asset_service.bulk_create_assets(assets_data)
                    duration = time.time() - start_time
                    
                    metrics.add_response_time(duration)
                    inserts_per_second = batch_size / duration
                    
                    print(f"\n💾 Bulk insert {batch_size} assets:")
                    print(f"   - Insert time: {duration:.2f}s")
                    print(f"   - Rate: {inserts_per_second:.0f} inserts/s")
                    
                    # Clean up
                    for asset in created_assets:
                        await db.delete(asset)
                    await db.commit()
                    
                except Exception as e:
                    metrics.add_error(str(e))
            
            metrics.finish()
            summary = metrics.get_summary()
            
            # Performance assertions
            assert summary["avg_response_time"] < 10.0, "Average bulk insert should be < 10s"
            assert summary["failed_requests"] == 0, "All bulk inserts should succeed"
    
    async def test_query_performance_with_indexes(self):
        """Test query performance with multi-tenant indexes"""
        async with AsyncSessionLocal() as db:
            # Setup test data
            client1_id = str(uuid.uuid4())
            client2_id = str(uuid.uuid4())
            engagement_id = str(uuid.uuid4())
            
            # Create assets for multiple clients
            for client_id in [client1_id, client2_id]:
                asset_service = V3AssetService(db, client_id, engagement_id)
                
                assets_data = []
                for i in range(1000):
                    assets_data.append({
                        "asset_name": f"client-{client_id[:8]}-asset-{i:04d}",
                        "asset_type": ["server", "application", "database"][i % 3],
                        "environment": ["production", "staging", "development"][i % 3]
                    })
                
                await asset_service.bulk_create_assets(assets_data)
            
            # Test query performance
            metrics = PerformanceMetrics()
            
            # Test different query types
            query_tests = [
                ("Simple filter", {"asset_type": "server"}),
                ("Multiple filters", {"asset_type": "server", "environment": "production"}),
                ("Text search", {"asset_name__contains": "asset-05"}),
            ]
            
            for test_name, filters in query_tests:
                asset_service = V3AssetService(db, client1_id, engagement_id)
                
                start_time = time.time()
                
                try:
                    results = await asset_service.search_assets(
                        filters=filters,
                        limit=100
                    )
                    
                    duration = time.time() - start_time
                    metrics.add_response_time(duration)
                    
                    print(f"\n🔍 Query: {test_name}")
                    print(f"   - Results: {len(results)}")
                    print(f"   - Query time: {duration*1000:.2f}ms")
                    
                except Exception as e:
                    metrics.add_error(str(e))
            
            metrics.finish()
            summary = metrics.get_summary()
            
            # Performance assertions
            assert summary["avg_response_time"] < 0.1, "Average query time should be < 100ms"
            assert summary["p95_response_time"] < 0.2, "95th percentile should be < 200ms"
    
    async def test_connection_pool_performance(self):
        """Test database connection pool performance under load"""
        metrics = PerformanceMetrics()
        
        async def db_operation(op_id: int):
            """Simulate a database operation"""
            start_time = time.time()
            
            try:
                async with AsyncSessionLocal() as db:
                    # Simple query to test connection
                    result = await db.execute(text("SELECT 1"))
                    result.scalar()
                    
                    # Simulate some work
                    await asyncio.sleep(0.01)
                
                duration = time.time() - start_time
                metrics.add_response_time(duration)
                
            except Exception as e:
                metrics.add_error(f"Operation {op_id} error: {str(e)}")
        
        # Test with increasing concurrent connections
        concurrency_levels = [10, 50, 100, 200]
        
        for concurrency in concurrency_levels:
            print(f"\n🔌 Testing {concurrency} concurrent DB connections...")
            
            tasks = []
            for i in range(concurrency):
                tasks.append(db_operation(i))
            
            start_time = time.time()
            await asyncio.gather(*tasks)
            duration = time.time() - start_time
            
            ops_per_second = concurrency / duration
            print(f"   - Total time: {duration:.2f}s")
            print(f"   - Operations/second: {ops_per_second:.0f}")
        
        metrics.finish()
        summary = metrics.get_summary()
        
        # Performance assertions
        assert summary["avg_response_time"] < 0.5, "Average operation time should be < 500ms"
        assert summary["failed_requests"] / summary["total_requests"] < 0.01, "Error rate should be < 1%"


class TestMemoryUsage:
    """Test memory usage and potential leaks"""
    
    async def test_large_data_processing_memory(self):
        """Test memory usage when processing large datasets"""
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        print(f"\n💾 Initial memory usage: {initial_memory:.2f} MB")
        
        async with AsyncSessionLocal() as db:
            asset_service = V3AssetService(
                db,
                str(uuid.uuid4()),
                str(uuid.uuid4())
            )
            
            # Process data in batches
            batch_count = 10
            batch_size = 1000
            
            for batch in range(batch_count):
                # Generate batch data
                assets_data = []
                for i in range(batch_size):
                    assets_data.append({
                        "asset_name": f"batch-{batch}-asset-{i:04d}",
                        "asset_type": "server",
                        "metadata": {
                            "batch": batch,
                            "index": i,
                            "data": "x" * 1000  # 1KB of data per asset
                        }
                    })
                
                # Create and immediately delete to test memory cleanup
                created = await asset_service.bulk_create_assets(assets_data)
                
                # Delete assets
                for asset in created:
                    await db.delete(asset)
                await db.commit()
                
                # Check memory after each batch
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_increase = current_memory - initial_memory
                
                print(f"   Batch {batch + 1}: Memory +{memory_increase:.2f} MB")
        
        # Final memory check
        final_memory = process.memory_info().rss / 1024 / 1024
        total_increase = final_memory - initial_memory
        
        print(f"\n💾 Final memory usage: {final_memory:.2f} MB")
        print(f"   Total increase: {total_increase:.2f} MB")
        
        # Memory leak assertion
        assert total_increase < 100, f"Memory increased by {total_increase:.2f} MB, possible leak"


# Performance test runner
async def run_performance_tests():
    """Run all performance tests and generate report"""
    print("\n" + "="*60)
    print("🏃 RUNNING V3 API PERFORMANCE TESTS")
    print("="*60)
    
    # API Performance Tests
    print("\n📡 API Performance Tests")
    api_tests = TestAPIPerformance()
    
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        headers = {
            "Authorization": "Bearer test-token",
            "Content-Type": "application/json",
            "X-Client-Account-ID": str(uuid.uuid4()),
            "X-Engagement-ID": str(uuid.uuid4())
        }
        
        await api_tests.test_data_import_upload_performance(client, headers)
        await api_tests.test_discovery_flow_creation_performance(client, headers)
        await api_tests.test_concurrent_api_requests(client, headers)
    
    # Database Performance Tests
    print("\n🗄️ Database Performance Tests")
    db_tests = TestDatabasePerformance()
    
    await db_tests.test_bulk_insert_performance()
    await db_tests.test_query_performance_with_indexes()
    await db_tests.test_connection_pool_performance()
    
    # Memory Usage Tests
    print("\n🧠 Memory Usage Tests")
    memory_tests = TestMemoryUsage()
    
    await memory_tests.test_large_data_processing_memory()
    
    print("\n" + "="*60)
    print("✅ ALL PERFORMANCE TESTS COMPLETED")
    print("="*60)


if __name__ == "__main__":
    import uuid
    from sqlalchemy import text
    
    asyncio.run(run_performance_tests())