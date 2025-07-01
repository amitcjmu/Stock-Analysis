# Remediation Plan: Phase 4 - Optimization & Testing (Weeks 7-8)

## Overview

Phase 4 focuses on performance optimization, comprehensive testing, monitoring enhancement, and production readiness. This final phase ensures the remediated codebase meets enterprise-grade quality standards and operational requirements.

## Week 7: Performance Optimization and Comprehensive Testing

### Day 31-32: Performance Optimization

#### Current Performance Issues
```python
# Identified performance bottlenecks from current implementation:
# 1. Large monolithic files (1790+ lines) causing slow loading
# 2. Inefficient database queries without proper indexing
# 3. Memory leaks from improper WebSocket connection management
# 4. Synchronous operations blocking async workflows
```

#### Remediation Steps

**Step 1: Database Query Optimization**
```sql
-- backend/sql/performance_indexes.sql - Add performance indexes
-- Optimize workflow_states queries
CREATE INDEX CONCURRENTLY idx_workflow_states_client_flow 
ON workflow_states (client_account_id, flow_id);

CREATE INDEX CONCURRENTLY idx_workflow_states_status_created 
ON workflow_states (status, created_at) 
WHERE status IN ('running', 'pending');

-- Optimize agent_insights queries  
CREATE INDEX CONCURRENTLY idx_agent_insights_flow_timestamp
ON agent_insights (flow_id, created_at DESC);

-- Optimize learning patterns for similarity searches
CREATE INDEX CONCURRENTLY idx_learning_patterns_client_type
ON learned_patterns (client_account_id, pattern_type);

-- Add partial index for active flows only
CREATE INDEX CONCURRENTLY idx_active_flows
ON workflow_states (client_account_id, flow_id)
WHERE status IN ('running', 'pending', 'paused');

-- Optimize LLM usage tracking
CREATE INDEX CONCURRENTLY idx_llm_usage_client_date
ON llm_usage_records (client_account_id, date_trunc('day', timestamp));

-- Add composite index for cost aggregations
CREATE INDEX CONCURRENTLY idx_llm_usage_model_agent
ON llm_usage_records (model_name, agent_name, timestamp);
```

**Step 2: Query Optimization in Services**
```python
# backend/app/repositories/optimized_repositories.py - Optimized database access
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload, joinedload
from typing import List, Optional, Dict, Any

class OptimizedFlowRepository(BaseRepository[WorkflowState]):
    """Optimized repository for flow operations"""
    
    async def get_active_flows(self, limit: int = 100) -> List[WorkflowState]:
        """Get active flows with optimized query"""
        context = get_current_context()
        
        # Use partial index for active flows
        stmt = (
            select(WorkflowState)
            .where(
                and_(
                    WorkflowState.client_account_id == context.client_account_id,
                    WorkflowState.status.in_(['running', 'pending', 'paused'])
                )
            )
            .order_by(WorkflowState.updated_at.desc())
            .limit(limit)
        )
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_flow_with_insights(self, flow_id: str) -> Optional[WorkflowState]:
        """Get flow with related insights in single query"""
        context = get_current_context()
        
        stmt = (
            select(WorkflowState)
            .options(selectinload(WorkflowState.agent_insights))
            .where(
                and_(
                    WorkflowState.flow_id == flow_id,
                    WorkflowState.client_account_id == context.client_account_id
                )
            )
        )
        
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_flow_statistics(self) -> Dict[str, Any]:
        """Get flow statistics with single aggregation query"""
        context = get_current_context()
        
        # Single query for all statistics
        stmt = (
            select(
                func.count(WorkflowState.id).label('total_flows'),
                func.count(
                    func.nullif(WorkflowState.status != 'completed', True)
                ).label('completed_flows'),
                func.count(
                    func.nullif(WorkflowState.status != 'running', True)
                ).label('running_flows'),
                func.avg(
                    func.extract('epoch', WorkflowState.updated_at - WorkflowState.created_at)
                ).label('avg_duration_seconds')
            )
            .where(WorkflowState.client_account_id == context.client_account_id)
        )
        
        result = await self.db.execute(stmt)
        stats = result.first()
        
        return {
            'total_flows': stats.total_flows or 0,
            'completed_flows': stats.completed_flows or 0,
            'running_flows': stats.running_flows or 0,
            'completion_rate': (stats.completed_flows / stats.total_flows * 100) if stats.total_flows else 0,
            'avg_duration_minutes': (stats.avg_duration_seconds / 60) if stats.avg_duration_seconds else 0
        }

class OptimizedLearningRepository(BaseRepository[LearningPattern]):
    """Optimized repository for learning patterns"""
    
    async def find_similar_patterns_optimized(self, pattern_text: str, 
                                            pattern_type: str = None,
                                            limit: int = 10) -> List[LearningPattern]:
        """Find similar patterns using optimized vector search"""
        context = get_current_context()
        
        # Use parameterized query for better performance
        base_query = """
        SELECT *, (pattern_vector <=> %s) as distance
        FROM learned_patterns 
        WHERE client_account_id = %s
        """
        
        params = [pattern_text, context.client_account_id]
        
        if pattern_type:
            base_query += " AND pattern_type = %s"
            params.append(pattern_type)
        
        base_query += " ORDER BY distance LIMIT %s"
        params.append(limit)
        
        result = await self.db.execute(text(base_query), params)
        return [LearningPattern(**row._asdict()) for row in result.fetchall()]
    
    async def batch_store_patterns(self, patterns: List[Dict[str, Any]]) -> bool:
        """Store multiple patterns in single transaction"""
        context = get_current_context()
        
        try:
            # Prepare bulk insert data
            pattern_records = []
            for pattern_data in patterns:
                pattern_records.append(LearningPattern(
                    client_account_id=context.client_account_id,
                    pattern_type=pattern_data['type'],
                    pattern_data=pattern_data['data'],
                    pattern_text=pattern_data['text'],
                    confidence_score=pattern_data.get('confidence', 0.8)
                ))
            
            # Bulk insert
            self.db.add_all(pattern_records)
            await self.db.commit()
            
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to batch store patterns: {e}")
            return False
```

**Step 3: Async Operations Optimization**
```python
# backend/app/services/optimized_flow_service.py - Optimized async operations
import asyncio
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor

class OptimizedFlowService:
    """Flow service with performance optimizations"""
    
    def __init__(self, context: RequestContext):
        self.context = context
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.batch_size = 50
    
    async def process_bulk_data(self, data_batches: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process multiple data batches concurrently"""
        
        # Create tasks for concurrent processing
        tasks = []
        for batch in data_batches:
            task = asyncio.create_task(self._process_single_batch(batch))
            tasks.append(task)
        
        # Process with controlled concurrency
        semaphore = asyncio.Semaphore(5)  # Limit concurrent operations
        
        async def bounded_process(task):
            async with semaphore:
                return await task
        
        # Execute all tasks with concurrency control
        results = await asyncio.gather(
            *[bounded_process(task) for task in tasks],
            return_exceptions=True
        )
        
        # Aggregate results
        successful_results = []
        errors = []
        
        for result in results:
            if isinstance(result, Exception):
                errors.append(str(result))
            else:
                successful_results.append(result)
        
        return {
            'successful_batches': len(successful_results),
            'failed_batches': len(errors),
            'total_batches': len(data_batches),
            'results': successful_results,
            'errors': errors
        }
    
    async def _process_single_batch(self, batch: Dict[str, Any]) -> Dict[str, Any]:
        """Process single batch with optimizations"""
        
        # Use connection pooling for database operations
        async with AsyncSessionLocal() as session:
            # Process batch data
            processed_records = []
            
            # Batch database operations
            for record in batch.get('records', []):
                # Apply transformations
                processed_record = await self._transform_record(record)
                processed_records.append(processed_record)
            
            # Bulk insert processed records
            if processed_records:
                session.add_all(processed_records)
                await session.commit()
        
        return {
            'batch_id': batch.get('id'),
            'records_processed': len(processed_records),
            'status': 'completed'
        }
    
    async def _transform_record(self, record: Dict[str, Any]) -> Any:
        """Transform individual record (CPU-intensive operations in thread pool)"""
        
        # Offload CPU-intensive work to thread pool
        loop = asyncio.get_event_loop()
        
        transformed = await loop.run_in_executor(
            self.executor,
            self._cpu_intensive_transform,
            record
        )
        
        return transformed
    
    def _cpu_intensive_transform(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """CPU-intensive transformation in separate thread"""
        # Simulate complex transformation
        # This runs in thread pool to avoid blocking event loop
        
        transformed = {
            'id': record.get('id'),
            'processed_data': self._complex_calculation(record),
            'metadata': self._extract_metadata(record)
        }
        
        return transformed
```

**Step 4: Memory and Resource Optimization**
```python
# backend/app/core/resource_manager.py - Resource management
import psutil
import gc
from typing import Dict, Any
import weakref

class ResourceManager:
    """Manages application resources and memory usage"""
    
    def __init__(self):
        self.connection_cache = weakref.WeakValueDictionary()
        self.memory_threshold = 0.8  # 80% memory usage threshold
        self.cleanup_interval = 300  # 5 minutes
    
    async def monitor_memory_usage(self) -> Dict[str, Any]:
        """Monitor current memory usage"""
        memory = psutil.virtual_memory()
        process = psutil.Process()
        
        memory_info = {
            'system_memory_percent': memory.percent,
            'system_memory_available_gb': memory.available / (1024**3),
            'process_memory_mb': process.memory_info().rss / (1024**2),
            'process_memory_percent': process.memory_percent(),
            'open_file_descriptors': process.num_fds(),
            'thread_count': process.num_threads()
        }
        
        # Trigger cleanup if memory usage is high
        if memory.percent > self.memory_threshold * 100:
            await self._cleanup_memory()
        
        return memory_info
    
    async def _cleanup_memory(self):
        """Perform memory cleanup"""
        logger.info("High memory usage detected, performing cleanup")
        
        # Force garbage collection
        collected = gc.collect()
        logger.info(f"Garbage collection freed {collected} objects")
        
        # Clear connection caches
        self.connection_cache.clear()
        
        # Clear any application-specific caches
        await self._clear_application_caches()
    
    async def _clear_application_caches(self):
        """Clear application-specific caches"""
        # Clear learning pattern cache
        from app.services.learning.learning_engine import LearningEngine
        learning_engine = LearningEngine()
        learning_engine.patterns_cache.clear()
        
        # Clear agent registry cache if needed
        from app.agents import agent_registry
        agent_registry._tool_instances.clear()
        
        logger.info("Application caches cleared")
    
    def get_resource_limits(self) -> Dict[str, Any]:
        """Get recommended resource limits for the application"""
        memory = psutil.virtual_memory()
        cpu_count = psutil.cpu_count()
        
        return {
            'max_workers': min(cpu_count * 2, 16),
            'max_connections': min(memory.total // (1024**3) * 100, 1000),
            'max_memory_mb': memory.total // (1024**2) * 0.7,  # 70% of system memory
            'max_file_descriptors': 1024
        }

# Global resource manager
resource_manager = ResourceManager()
```

### Day 33-34: Comprehensive Testing Infrastructure

#### Current Testing Issues
```python
# Inadequate test coverage and structure:
# - Debug scripts instead of proper tests
# - No integration tests for complex workflows
# - Missing performance benchmarks
# - No load testing for concurrent operations
```

#### Remediation Steps

**Step 1: Advanced Test Infrastructure**
```python
# backend/tests/fixtures/advanced_fixtures.py - Advanced test fixtures
import pytest
import asyncio
from typing import Dict, Any, List
from unittest.mock import AsyncMock, MagicMock
from app.core.database import AsyncSessionLocal

@pytest.fixture
async def flow_factory():
    """Factory for creating test flows"""
    created_flows = []
    
    class FlowFactory:
        async def create(self, flow_data: Dict[str, Any] = None):
            from app.services.discovery_flow_service import DiscoveryFlowService
            from app.core.context import get_current_context
            
            default_data = {
                'name': 'Test Flow',
                'description': 'Test flow for unit testing',
                'data': {
                    'assets': [
                        {'id': 1, 'name': 'Test Asset', 'type': 'application'},
                        {'id': 2, 'name': 'Test Database', 'type': 'database'}
                    ]
                }
            }
            
            if flow_data:
                default_data.update(flow_data)
            
            context = get_current_context()
            service = DiscoveryFlowService(context)
            flow = await service.create_flow(default_data)
            created_flows.append(flow)
            return flow
        
        async def create_completed_flow(self):
            flow = await self.create()
            flow.state.status = "completed"
            flow.state.progress = 100
            await flow._persist_state()
            return flow
        
        async def create_failed_flow(self):
            flow = await self.create()
            flow.state.status = "failed"
            flow.state.error_message = "Test failure"
            await flow._persist_state()
            return flow
    
    yield FlowFactory()
    
    # Cleanup created flows
    async with AsyncSessionLocal() as session:
        for flow in created_flows:
            await session.delete(flow)
        await session.commit()

@pytest.fixture
def mock_llm_responses():
    """Mock LLM responses for testing"""
    
    mock_responses = {
        'data_validation': {
            'validation_status': 'passed',
            'issues_found': [],
            'security_score': 95,
            'recommendations': ['Data quality is excellent']
        },
        'application_discovery': {
            'applications': [
                {
                    'name': 'Web Application',
                    'type': 'web_app',
                    'technology_stack': ['Java', 'Spring', 'MySQL'],
                    'dependencies': ['Database Service']
                }
            ],
            'dependency_map': {
                'Web Application': ['Database Service']
            }
        },
        'field_mapping': {
            'mappings': [
                {
                    'source_field': 'customer_name',
                    'target_field': 'client_name',
                    'confidence': 0.95,
                    'transformation': None
                }
            ],
            'mapping_confidence': 0.93
        }
    }
    
    return mock_responses

@pytest.fixture
async def performance_monitor():
    """Monitor for performance testing"""
    import time
    import psutil
    
    class PerformanceMonitor:
        def __init__(self):
            self.start_time = None
            self.start_memory = None
            self.metrics = {}
        
        def start(self):
            self.start_time = time.time()
            self.start_memory = psutil.virtual_memory().used
        
        def stop(self, operation_name: str):
            end_time = time.time()
            end_memory = psutil.virtual_memory().used
            
            self.metrics[operation_name] = {
                'duration_seconds': end_time - self.start_time,
                'memory_delta_mb': (end_memory - self.start_memory) / (1024**2),
                'timestamp': end_time
            }
        
        def get_metrics(self):
            return self.metrics
        
        def assert_performance(self, operation_name: str, 
                             max_duration: float = None, 
                             max_memory_mb: float = None):
            metrics = self.metrics.get(operation_name)
            assert metrics, f"No metrics found for operation: {operation_name}"
            
            if max_duration:
                assert metrics['duration_seconds'] <= max_duration, \
                    f"Operation took {metrics['duration_seconds']:.2f}s, expected <={max_duration}s"
            
            if max_memory_mb:
                assert metrics['memory_delta_mb'] <= max_memory_mb, \
                    f"Operation used {metrics['memory_delta_mb']:.2f}MB, expected <={max_memory_mb}MB"
    
    return PerformanceMonitor()
```

**Step 2: Integration Test Suite**
```python
# backend/tests/integration/test_complete_workflows.py - Integration tests
import pytest
import asyncio
from unittest.mock import patch, AsyncMock

@pytest.mark.integration
class TestCompleteWorkflows:
    """Integration tests for complete workflow execution"""
    
    async def test_complete_discovery_workflow(self, flow_factory, mock_llm_responses, test_context):
        """Test complete discovery workflow from start to finish"""
        
        # Mock LLM calls to avoid external dependencies
        with patch('app.agents.data_validation.DataImportValidationAgent.execute') as mock_validation, \
             patch('app.agents.application_discovery.ApplicationDiscoveryAgent.execute') as mock_discovery:
            
            mock_validation.return_value = mock_llm_responses['data_validation']
            mock_discovery.return_value = mock_llm_responses['application_discovery']
            
            # Create and execute flow
            flow = await flow_factory.create({
                'name': 'Integration Test Flow',
                'data': {
                    'customers': [
                        {'id': 1, 'name': 'John Doe', 'email': 'john@example.com'},
                        {'id': 2, 'name': 'Jane Smith', 'email': 'jane@example.com'}
                    ]
                }
            })
            
            # Execute flow phases
            result1 = flow.initialize_discovery()
            assert result1 == "initialized"
            
            result2 = flow.validate_data("initialized")
            assert result2 == "validated"
            
            result3 = flow.discover_applications("validated")
            assert result3 == "discovered"
            
            # Verify state progression
            assert flow.state.status == "running"
            assert flow.state.current_phase == "application_discovery"
            assert flow.state.progress == 60
            
            # Verify results stored
            assert flow.state.validation_results is not None
            assert flow.state.discovery_results is not None
    
    async def test_flow_error_handling_and_recovery(self, flow_factory, test_context):
        """Test flow error handling and recovery mechanisms"""
        
        # Mock agent failure
        with patch('app.agents.data_validation.DataImportValidationAgent.execute') as mock_agent:
            mock_agent.side_effect = Exception("Simulated agent failure")
            
            flow = await flow_factory.create()
            
            # Execute flow with failure
            result = flow.validate_data("initialized")
            
            # Verify error handling
            assert result == "validation_failed"
            assert flow.state.status == "failed"
            assert "Data validation failed" in flow.state.error_message
    
    async def test_concurrent_flow_execution(self, flow_factory, test_context):
        """Test multiple flows executing concurrently"""
        
        with patch('app.agents.data_validation.DataImportValidationAgent.execute') as mock_validation:
            mock_validation.return_value = {'validation_status': 'passed'}
            
            # Create multiple flows
            flows = []
            for i in range(5):
                flow = await flow_factory.create({
                    'name': f'Concurrent Flow {i}',
                    'data': {'test_data': f'data_{i}'}
                })
                flows.append(flow)
            
            # Execute all flows concurrently
            async def execute_flow(flow):
                flow.initialize_discovery()
                return flow.validate_data("initialized")
            
            results = await asyncio.gather(
                *[execute_flow(flow) for flow in flows],
                return_exceptions=True
            )
            
            # Verify all flows executed successfully
            for result in results:
                assert not isinstance(result, Exception)
                assert result == "validated"
            
            # Verify flow isolation (each flow has unique state)
            flow_ids = [flow.state.flow_id for flow in flows]
            assert len(set(flow_ids)) == 5  # All unique
    
    async def test_learning_system_integration(self, flow_factory, test_context):
        """Test learning system integration with flows"""
        from app.services.learning.learning_engine import LearningEngine
        
        learning_engine = LearningEngine()
        
        # Create flow with initial mapping
        flow = await flow_factory.create()
        
        original_mapping = {
            'field_mappings': [
                {'source': 'cust_name', 'target': 'customer_name', 'confidence': 0.7}
            ]
        }
        
        # Simulate user correction
        corrected_mapping = {
            'field_mappings': [
                {'source': 'cust_name', 'target': 'client_full_name', 'confidence': 0.95}
            ]
        }
        
        # Learn from correction
        context = {'flow_id': flow.state.flow_id, 'data_type': 'customer'}
        success = await learning_engine.learn_from_correction(
            original_mapping, corrected_mapping, context
        )
        assert success is True
        
        # Test recommendation retrieval
        recommendations = await learning_engine.get_recommendations(context)
        assert len(recommendations) > 0
        assert recommendations[0]['type'] == 'correction_recommendation'
```

**Step 3: Load and Performance Testing**
```python
# backend/tests/performance/test_load_testing.py - Load testing
import pytest
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

@pytest.mark.performance
class TestLoadTesting:
    """Load testing for system performance under stress"""
    
    async def test_api_endpoint_load(self, client, test_context):
        """Test API endpoints under high load"""
        
        async def make_request():
            response = await client.post("/api/v1/discovery/flows", json={
                'name': 'Load Test Flow',
                'description': 'Testing under load'
            })
            return response.status_code
        
        # Execute 100 concurrent requests
        start_time = time.time()
        
        tasks = [make_request() for _ in range(100)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Analyze results
        successful_requests = sum(1 for r in results if r == 200)
        failed_requests = len(results) - successful_requests
        
        # Performance assertions
        assert total_time < 10.0, f"100 requests took {total_time:.2f}s, expected <10s"
        assert successful_requests >= 95, f"Only {successful_requests}/100 requests succeeded"
        assert failed_requests <= 5, f"{failed_requests} requests failed, expected <=5"
        
        # Calculate throughput
        throughput = len(results) / total_time
        assert throughput >= 10, f"Throughput {throughput:.1f} req/s, expected >=10 req/s"
    
    async def test_websocket_connection_load(self, performance_monitor):
        """Test WebSocket system under connection load"""
        from app.websocket.manager import ConnectionManager
        
        manager = ConnectionManager()
        
        performance_monitor.start()
        
        # Simulate 200 concurrent connections
        connection_ids = []
        for i in range(200):
            connection_id = f"load-test-{i}"
            # Mock connection metadata
            manager.connection_metadata[connection_id] = {
                'tenant_id': 'load-test-tenant',
                'user_id': f'user-{i}',
                'subscriptions': set()
            }
            connection_ids.append(connection_id)
        
        # Subscribe all connections to a flow
        flow_id = "load-test-flow"
        for connection_id in connection_ids:
            await manager.subscribe_to_flow(connection_id, flow_id)
        
        performance_monitor.stop('connection_setup')
        
        # Test broadcast performance
        performance_monitor.start()
        
        # Broadcast 50 messages
        for i in range(50):
            message = {
                'type': 'load_test',
                'message_id': i,
                'data': f'Load test message {i}'
            }
            await manager.broadcast_to_flow(flow_id, message)
        
        performance_monitor.stop('broadcast_messages')
        
        # Performance assertions
        performance_monitor.assert_performance('connection_setup', max_duration=5.0)
        performance_monitor.assert_performance('broadcast_messages', max_duration=2.0)
        
        # Cleanup
        for connection_id in connection_ids:
            await manager.disconnect(connection_id)
    
    async def test_database_load(self, db_session, test_context, performance_monitor):
        """Test database operations under load"""
        from app.repositories.optimized_repositories import OptimizedFlowRepository
        
        repo = OptimizedFlowRepository(db_session, WorkflowState)
        
        performance_monitor.start()
        
        # Create many flow records concurrently
        async def create_flow_record(index):
            from app.models.workflow_state import WorkflowState
            
            flow = WorkflowState(
                flow_id=f"load-test-flow-{index}",
                client_account_id=test_context.client_account_id,
                status="running",
                state_data={'test': f'data_{index}'}
            )
            db_session.add(flow)
            return flow
        
        # Create 500 records
        tasks = [create_flow_record(i) for i in range(500)]
        flows = await asyncio.gather(*tasks)
        
        await db_session.commit()
        
        performance_monitor.stop('bulk_insert')
        
        # Test bulk query performance
        performance_monitor.start()
        
        active_flows = await repo.get_active_flows(limit=100)
        
        performance_monitor.stop('bulk_query')
        
        # Performance assertions
        performance_monitor.assert_performance('bulk_insert', max_duration=5.0)
        performance_monitor.assert_performance('bulk_query', max_duration=1.0)
        
        assert len(active_flows) <= 100
        assert all(flow.status == "running" for flow in active_flows)
    
    async def test_learning_system_load(self, test_context, performance_monitor):
        """Test learning system under pattern load"""
        from app.services.learning.learning_engine import LearningEngine
        
        learning_engine = LearningEngine()
        
        performance_monitor.start()
        
        # Create many learning patterns concurrently
        async def create_pattern(index):
            original = {'field': f'field_{index}', 'value': f'original_{index}'}
            corrected = {'field': f'field_{index}', 'value': f'corrected_{index}'}
            context = {'type': f'pattern_type_{index % 10}', 'index': index}
            
            return await learning_engine.learn_from_correction(original, corrected, context)
        
        # Create 200 patterns
        tasks = [create_pattern(i) for i in range(200)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        performance_monitor.stop('pattern_creation')
        
        # Test recommendation performance with many patterns
        performance_monitor.start()
        
        recommendations = await learning_engine.get_recommendations({
            'type': 'pattern_type_1'
        })
        
        performance_monitor.stop('recommendation_retrieval')
        
        # Performance assertions
        performance_monitor.assert_performance('pattern_creation', max_duration=15.0)
        performance_monitor.assert_performance('recommendation_retrieval', max_duration=3.0)
        
        successful_patterns = sum(1 for r in results if r is True)
        assert successful_patterns >= 190, f"Only {successful_patterns}/200 patterns created"
        assert len(recommendations) > 0
```

## Week 8: Monitoring Enhancement and Production Readiness

### Day 35-36: Enhanced Monitoring and Observability

#### Current Monitoring Issues
```python
# Limited monitoring capabilities:
# - Basic health endpoints only
# - No distributed tracing
# - Manual log analysis
# - Missing performance metrics
```

#### Remediation Steps

**Step 1: Comprehensive Metrics System**
```python
# backend/app/monitoring/metrics.py - Comprehensive metrics collection
from prometheus_client import Counter, Histogram, Gauge, Summary, CollectorRegistry
from typing import Dict, Any, Optional
import time
import functools

# Create custom registry for application metrics
registry = CollectorRegistry()

# Define application metrics
flow_operations = Counter(
    'flow_operations_total',
    'Total number of flow operations',
    ['operation', 'status', 'tenant_id'],
    registry=registry
)

flow_duration = Histogram(
    'flow_duration_seconds',
    'Duration of flow operations',
    ['operation', 'tenant_id'],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0],
    registry=registry
)

agent_executions = Counter(
    'agent_executions_total',
    'Total number of agent executions',
    ['agent_name', 'status', 'tenant_id'],
    registry=registry
)

agent_duration = Histogram(
    'agent_execution_duration_seconds',
    'Duration of agent executions',
    ['agent_name', 'tenant_id'],
    registry=registry
)

websocket_connections = Gauge(
    'websocket_connections_active',
    'Number of active WebSocket connections',
    ['tenant_id'],
    registry=registry
)

llm_requests = Counter(
    'llm_requests_total',
    'Total number of LLM requests',
    ['model', 'agent', 'tenant_id'],
    registry=registry
)

llm_tokens = Counter(
    'llm_tokens_total',
    'Total number of LLM tokens consumed',
    ['model', 'type', 'tenant_id'],  # type: input/output
    registry=registry
)

llm_cost = Counter(
    'llm_cost_dollars_total',
    'Total LLM cost in dollars',
    ['model', 'tenant_id'],
    registry=registry
)

database_operations = Counter(
    'database_operations_total',
    'Total number of database operations',
    ['operation', 'table', 'status'],
    registry=registry
)

database_duration = Histogram(
    'database_operation_duration_seconds',
    'Duration of database operations',
    ['operation', 'table'],
    registry=registry
)

learning_patterns = Gauge(
    'learning_patterns_count',
    'Number of learned patterns',
    ['pattern_type', 'tenant_id'],
    registry=registry
)

class MetricsCollector:
    """Centralized metrics collection service"""
    
    def __init__(self):
        self.start_times = {}
    
    def record_flow_operation(self, operation: str, status: str, 
                            tenant_id: str, duration: Optional[float] = None):
        """Record flow operation metrics"""
        flow_operations.labels(
            operation=operation,
            status=status, 
            tenant_id=tenant_id
        ).inc()
        
        if duration is not None:
            flow_duration.labels(
                operation=operation,
                tenant_id=tenant_id
            ).observe(duration)
    
    def record_agent_execution(self, agent_name: str, status: str,
                             tenant_id: str, duration: Optional[float] = None):
        """Record agent execution metrics"""
        agent_executions.labels(
            agent_name=agent_name,
            status=status,
            tenant_id=tenant_id
        ).inc()
        
        if duration is not None:
            agent_duration.labels(
                agent_name=agent_name,
                tenant_id=tenant_id
            ).observe(duration)
    
    def record_llm_usage(self, model: str, agent: str, tenant_id: str,
                        input_tokens: int, output_tokens: int, cost: float):
        """Record LLM usage metrics"""
        llm_requests.labels(
            model=model,
            agent=agent,
            tenant_id=tenant_id
        ).inc()
        
        llm_tokens.labels(
            model=model,
            type='input',
            tenant_id=tenant_id
        ).inc(input_tokens)
        
        llm_tokens.labels(
            model=model,
            type='output', 
            tenant_id=tenant_id
        ).inc(output_tokens)
        
        llm_cost.labels(
            model=model,
            tenant_id=tenant_id
        ).inc(cost)
    
    def update_websocket_connections(self, tenant_id: str, count: int):
        """Update WebSocket connection count"""
        websocket_connections.labels(tenant_id=tenant_id).set(count)
    
    def start_timer(self, operation_id: str) -> str:
        """Start timing an operation"""
        timer_id = f"{operation_id}_{int(time.time() * 1000)}"
        self.start_times[timer_id] = time.time()
        return timer_id
    
    def end_timer(self, timer_id: str) -> float:
        """End timing and return duration"""
        if timer_id in self.start_times:
            duration = time.time() - self.start_times[timer_id]
            del self.start_times[timer_id]
            return duration
        return 0.0

# Global metrics collector
metrics = MetricsCollector()

def monitor_performance(operation: str):
    """Decorator to monitor function performance"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            from app.core.context import get_current_context
            
            context = get_current_context()
            tenant_id = str(context.client_account_id) if context else 'unknown'
            
            timer_id = metrics.start_timer(f"{operation}_{func.__name__}")
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                
                duration = metrics.end_timer(timer_id)
                metrics.record_flow_operation(operation, 'success', tenant_id, duration)
                
                return result
                
            except Exception as e:
                duration = metrics.end_timer(timer_id)
                metrics.record_flow_operation(operation, 'error', tenant_id, duration)
                raise
        
        return wrapper
    return decorator
```

**Step 2: Distributed Tracing Implementation**
```python
# backend/app/monitoring/tracing.py - OpenTelemetry distributed tracing
from opentelemetry import trace, context
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
import functools

# Configure tracing
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

# Configure Jaeger exporter
jaeger_exporter = JaegerExporter(
    agent_host_name="localhost",
    agent_port=6831,
)

span_processor = BatchSpanProcessor(jaeger_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

class TracingManager:
    """Manages distributed tracing across the application"""
    
    def __init__(self):
        self.tracer = trace.get_tracer("ai-migration-platform")
    
    def setup_instrumentation(self, app):
        """Setup automatic instrumentation"""
        # Instrument FastAPI
        FastAPIInstrumentor.instrument_app(app)
        
        # Instrument SQLAlchemy
        SQLAlchemyInstrumentor().instrument()
        
        # Instrument HTTP requests
        RequestsInstrumentor().instrument()
    
    def create_span(self, name: str, attributes: dict = None):
        """Create a new span"""
        span = self.tracer.start_span(name)
        
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, str(value))
        
        return span
    
    def add_span_event(self, span, name: str, attributes: dict = None):
        """Add event to current span"""
        span.add_event(name, attributes or {})

def trace_operation(operation_name: str, **span_attributes):
    """Decorator to trace function execution"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            tracing_manager = TracingManager()
            
            # Add context attributes
            from app.core.context import get_current_context
            context_info = get_current_context()
            
            attributes = {
                'operation': operation_name,
                'function': func.__name__,
                **span_attributes
            }
            
            if context_info:
                attributes.update({
                    'tenant_id': str(context_info.client_account_id),
                    'user_id': str(context_info.user_id) if context_info.user_id else None
                })
            
            with tracing_manager.create_span(operation_name, attributes) as span:
                try:
                    tracing_manager.add_span_event(span, f"{operation_name}.start")
                    
                    result = await func(*args, **kwargs)
                    
                    tracing_manager.add_span_event(span, f"{operation_name}.success")
                    span.set_attribute("operation.status", "success")
                    
                    return result
                    
                except Exception as e:
                    tracing_manager.add_span_event(
                        span, 
                        f"{operation_name}.error",
                        {"error.message": str(e), "error.type": type(e).__name__}
                    )
                    span.set_attribute("operation.status", "error")
                    span.set_attribute("error.message", str(e))
                    raise
        
        return wrapper
    return decorator

# Global tracing manager
tracing_manager = TracingManager()
```

**Step 3: Advanced Logging System**
```python
# backend/app/monitoring/logging.py - Structured logging with correlation
import logging
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from contextvars import ContextVar

# Correlation ID for request tracing
correlation_id: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)

class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record):
        from app.core.context import get_current_context
        
        # Get context information
        context = get_current_context()
        corr_id = correlation_id.get()
        
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'correlation_id': corr_id,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add context information if available
        if context:
            log_entry.update({
                'tenant_id': str(context.client_account_id),
                'user_id': str(context.user_id) if context.user_id else None,
                'engagement_id': str(context.engagement_id) if context.engagement_id else None
            })
        
        # Add extra fields from record
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
        
        # Add exception information if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry)

class ContextualLogger:
    """Logger with automatic context injection"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        
        # Configure structured formatter
        handler = logging.StreamHandler()
        handler.setFormatter(StructuredFormatter())
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def _log_with_context(self, level: int, message: str, extra_fields: Dict[str, Any] = None):
        """Log with automatic context injection"""
        if extra_fields:
            # Create log record with extra fields
            extra = {'extra_fields': extra_fields}
            self.logger.log(level, message, extra=extra)
        else:
            self.logger.log(level, message)
    
    def info(self, message: str, **kwargs):
        self._log_with_context(logging.INFO, message, kwargs)
    
    def warning(self, message: str, **kwargs):
        self._log_with_context(logging.WARNING, message, kwargs)
    
    def error(self, message: str, **kwargs):
        self._log_with_context(logging.ERROR, message, kwargs)
    
    def debug(self, message: str, **kwargs):
        self._log_with_context(logging.DEBUG, message, kwargs)
    
    def flow_event(self, flow_id: str, event: str, **kwargs):
        """Log flow-specific events"""
        self.info(f"Flow {event}", flow_id=flow_id, event_type=event, **kwargs)
    
    def agent_event(self, agent_name: str, event: str, **kwargs):
        """Log agent-specific events"""
        self.info(f"Agent {event}", agent_name=agent_name, event_type=event, **kwargs)
    
    def performance_log(self, operation: str, duration: float, **kwargs):
        """Log performance metrics"""
        self.info(f"Performance: {operation}", 
                 operation=operation, 
                 duration_seconds=duration, 
                 performance_log=True,
                 **kwargs)

def get_logger(name: str) -> ContextualLogger:
    """Get contextual logger instance"""
    return ContextualLogger(name)

def set_correlation_id(corr_id: str = None) -> str:
    """Set correlation ID for request tracing"""
    if not corr_id:
        corr_id = str(uuid.uuid4())
    
    correlation_id.set(corr_id)
    return corr_id

def get_correlation_id() -> Optional[str]:
    """Get current correlation ID"""
    return correlation_id.get()
```

### Day 37-38: Production Deployment Preparation

#### Current Deployment Issues
```python
# Missing production-ready deployment configuration:
# - No health checks for all services
# - Missing resource limits
# - No proper secrets management
# - Limited environment configuration
```

#### Remediation Steps

**Step 1: Production Docker Configuration**
```yaml
# docker-compose.prod.yml - Production-ready Docker configuration
version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg16
    container_name: migration_postgres_prod
    environment:
      POSTGRES_DB: ${DATABASE_NAME}
      POSTGRES_USER: ${DATABASE_USER}
      POSTGRES_PASSWORD: ${DATABASE_PASSWORD}
    volumes:
      - postgres_data_prod:/var/lib/postgresql/data
      - ./backend/sql/init_prod.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 1G
          cpus: '0.5'
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DATABASE_USER} -d ${DATABASE_NAME}"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: migration_redis_prod
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    ports:
      - "6379:6379"
    volumes:
      - redis_data_prod:/data
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
        reservations:
          memory: 256M
          cpus: '0.25'
    healthcheck:
      test: ["CMD", "redis-cli", "--no-auth-warning", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
      target: production
    container_name: migration_backend_prod
    environment:
      - DATABASE_URL=postgresql://${DATABASE_USER}:${DATABASE_PASSWORD}@postgres:5432/${DATABASE_NAME}
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379
      - ENVIRONMENT=production
      - SECRET_KEY=${SECRET_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - DEEPINFRA_API_KEY=${DEEPINFRA_API_KEY}
      - ALLOWED_ORIGINS=${ALLOWED_ORIGINS}
      - JAEGER_AGENT_HOST=jaeger
      - PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '2.0'
        reservations:
          memory: 1G
          cpus: '1.0'
      replicas: 2
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
      target: production
    container_name: migration_frontend_prod
    environment:
      - NEXT_PUBLIC_API_URL=${API_URL}
      - NEXT_PUBLIC_WS_URL=${WS_URL}
    ports:
      - "3000:3000"
    depends_on:
      - backend
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '1.0'
        reservations:
          memory: 512M
          cpus: '0.5'
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  # Monitoring services
  prometheus:
    image: prom/prometheus:latest
    container_name: migration_prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--web.enable-lifecycle'
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    container_name: migration_grafana
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/var/lib/grafana/dashboards
    restart: unless-stopped

  jaeger:
    image: jaegertracing/all-in-one:latest
    container_name: migration_jaeger
    ports:
      - "16686:16686"
      - "14268:14268"
    environment:
      - COLLECTOR_OTLP_ENABLED=true
    restart: unless-stopped

volumes:
  postgres_data_prod:
  redis_data_prod:
  prometheus_data:
  grafana_data:

networks:
  default:
    driver: bridge
```

**Step 2: Production Dockerfile Optimization**
```dockerfile
# backend/Dockerfile.prod - Multi-stage production build
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash app

# Development stage
FROM base as development
WORKDIR /app
COPY requirements/dev.txt .
RUN pip install -r dev.txt
USER app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production stage
FROM base as production

# Install production dependencies only
WORKDIR /app
COPY requirements/prod.txt .
RUN pip install --no-cache-dir -r prod.txt

# Copy application code
COPY --chown=app:app . .

# Switch to non-root user
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application with gunicorn
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

**Step 3: Health Check and Monitoring Endpoints**
```python
# backend/app/api/v1/health.py - Comprehensive health checks
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import text
from typing import Dict, Any
import asyncio
import time
from app.core.database import AsyncSessionLocal
from app.monitoring.metrics import metrics

router = APIRouter()

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "ai-migration-platform"
    }

@router.get("/health/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """Detailed health check with dependency status"""
    
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "ai-migration-platform",
        "checks": {}
    }
    
    # Check database connectivity
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        health_status["checks"]["database"] = {"status": "healthy", "response_time_ms": 0}
    except Exception as e:
        health_status["checks"]["database"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "unhealthy"
    
    # Check Redis connectivity
    try:
        import redis.asyncio as redis
        from app.core.config import settings
        
        redis_client = redis.from_url(settings.REDIS_URL)
        await redis_client.ping()
        await redis_client.close()
        health_status["checks"]["redis"] = {"status": "healthy"}
    except Exception as e:
        health_status["checks"]["redis"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "unhealthy"
    
    # Check LLM API connectivity (optional check)
    try:
        # Simple test to verify LLM APIs are accessible
        # This is a lightweight check, not a full API call
        health_status["checks"]["llm_apis"] = {"status": "healthy", "note": "API keys configured"}
    except Exception as e:
        health_status["checks"]["llm_apis"] = {"status": "degraded", "error": str(e)}
    
    return health_status

@router.get("/health/readiness")
async def readiness_check() -> Dict[str, Any]:
    """Kubernetes readiness probe endpoint"""
    
    # Check critical dependencies for readiness
    checks = []
    
    # Database readiness
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT COUNT(*) FROM information_schema.tables"))
            table_count = result.scalar()
            checks.append({"name": "database", "ready": table_count > 0})
    except Exception:
        checks.append({"name": "database", "ready": False})
    
    # Redis readiness
    try:
        import redis.asyncio as redis
        from app.core.config import settings
        
        redis_client = redis.from_url(settings.REDIS_URL)
        await redis_client.ping()
        await redis_client.close()
        checks.append({"name": "redis", "ready": True})
    except Exception:
        checks.append({"name": "redis", "ready": False})
    
    all_ready = all(check["ready"] for check in checks)
    
    return {
        "ready": all_ready,
        "checks": checks,
        "timestamp": time.time()
    }

@router.get("/health/liveness")
async def liveness_check() -> Dict[str, Any]:
    """Kubernetes liveness probe endpoint"""
    
    # Simple liveness check - if we can respond, we're alive
    return {
        "alive": True,
        "timestamp": time.time(),
        "uptime_seconds": time.time() - startup_time
    }

# Track startup time
startup_time = time.time()

@router.get("/metrics")
async def metrics_endpoint():
    """Prometheus metrics endpoint"""
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from app.monitoring.metrics import registry
    
    return Response(
        generate_latest(registry),
        media_type=CONTENT_TYPE_LATEST
    )
```

**Step 4: Environment Configuration Management**
```python
# backend/app/core/production_config.py - Production configuration
from pydantic_settings import BaseSettings
from typing import List, Optional
import secrets

class ProductionSettings(BaseSettings):
    """Production-specific configuration"""
    
    # Application
    PROJECT_NAME: str = "AI Migration Platform"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "production"
    DEBUG: bool = False
    
    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALLOWED_HOSTS: List[str] = ["*"]  # Restrict in production
    ALLOWED_ORIGINS: List[str] = []  # Set specific origins
    
    # Database
    DATABASE_URL: str
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 30
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600
    
    # Redis
    REDIS_URL: str
    REDIS_POOL_SIZE: int = 10
    
    # LLM APIs
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    DEEPINFRA_API_KEY: Optional[str] = None
    LLM_REQUEST_TIMEOUT: int = 60
    LLM_MAX_RETRIES: int = 3
    
    # Monitoring
    ENABLE_METRICS: bool = True
    ENABLE_TRACING: bool = True
    JAEGER_AGENT_HOST: str = "localhost"
    JAEGER_AGENT_PORT: int = 6831
    
    # Performance
    MAX_CONCURRENT_FLOWS: int = 100
    MAX_WEBSOCKET_CONNECTIONS: int = 1000
    REQUEST_TIMEOUT: int = 300
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # Feature Flags
    ENABLE_LEARNING_SYSTEM: bool = True
    ENABLE_COST_TRACKING: bool = True
    ENABLE_REAL_TIME_UPDATES: bool = True
    
    class Config:
        env_file = ".env.production"
        case_sensitive = True

class ConfigManager:
    """Manages configuration across environments"""
    
    def __init__(self):
        self._settings = None
    
    def get_settings(self) -> ProductionSettings:
        if self._settings is None:
            self._settings = ProductionSettings()
        return self._settings
    
    def validate_production_config(self) -> Dict[str, Any]:
        """Validate production configuration"""
        settings = self.get_settings()
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Required settings validation
        required_settings = [
            "DATABASE_URL",
            "REDIS_URL", 
            "SECRET_KEY"
        ]
        
        for setting in required_settings:
            if not getattr(settings, setting, None):
                validation_results["errors"].append(f"Missing required setting: {setting}")
                validation_results["valid"] = False
        
        # Security validation
        if settings.DEBUG:
            validation_results["warnings"].append("DEBUG mode enabled in production")
        
        if not settings.ALLOWED_ORIGINS:
            validation_results["warnings"].append("ALLOWED_ORIGINS not restricted")
        
        if len(settings.SECRET_KEY) < 32:
            validation_results["errors"].append("SECRET_KEY too short (minimum 32 characters)")
            validation_results["valid"] = False
        
        # LLM API validation
        llm_keys = [settings.OPENAI_API_KEY, settings.ANTHROPIC_API_KEY, settings.DEEPINFRA_API_KEY]
        if not any(llm_keys):
            validation_results["warnings"].append("No LLM API keys configured")
        
        return validation_results

# Global config manager
config_manager = ConfigManager()
```

## Phase 4 Deliverables

### Performance Optimizations
1. **Database Optimization**: Proper indexing, query optimization, connection pooling
2. **Async Operations**: Concurrent processing, resource management, memory optimization
3. **Caching Strategy**: Multi-level caching for improved response times
4. **Resource Management**: Memory monitoring, cleanup procedures, resource limits

### Testing Infrastructure
1. **Comprehensive Test Suite**: Unit, integration, performance, and load tests
2. **Test Coverage**: >90% code coverage across all modules
3. **Performance Benchmarks**: Documented performance requirements and validation
4. **Load Testing**: Validated system performance under stress

### Monitoring and Observability
1. **Metrics Collection**: Comprehensive Prometheus metrics for all operations
2. **Distributed Tracing**: OpenTelemetry tracing across all services
3. **Structured Logging**: JSON-formatted logs with correlation IDs
4. **Health Checks**: Detailed health, readiness, and liveness endpoints

### Production Readiness
1. **Docker Optimization**: Multi-stage builds, resource limits, health checks
2. **Configuration Management**: Environment-specific configurations with validation
3. **Security Hardening**: Proper secrets management, restricted access, security headers
4. **Deployment Automation**: Production-ready Docker Compose with monitoring stack

### Quality Gates
- [ ] All performance benchmarks met (API <200ms, flow processing <45s for 10K assets)
- [ ] Test coverage >90% with all tests passing
- [ ] No critical security vulnerabilities
- [ ] All monitoring systems functional and providing actionable insights
- [ ] Production deployment validated in staging environment
- [ ] Zero-downtime deployment capability verified

## Risk Mitigation

### Performance Monitoring
- Continuous monitoring of key performance indicators
- Automated alerts for performance degradation
- Regular performance testing and optimization cycles

### Deployment Safety
- Blue-green deployment strategy for zero-downtime updates
- Automated rollback procedures for failed deployments
- Comprehensive staging environment testing

### Operational Excellence
- Runbook documentation for common operational scenarios
- Incident response procedures with defined escalation paths
- Regular disaster recovery testing

This completes Phase 4 optimization and testing, ensuring the remediated codebase meets enterprise-grade performance, reliability, and operational requirements while maintaining all existing functionality.