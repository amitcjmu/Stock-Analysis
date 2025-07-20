"""
Integration Test Configuration

Pytest configuration and fixtures for ADCS end-to-end integration testing.
Provides shared test infrastructure, database setup, and utility functions.

Generated with CC for ADCS end-to-end integration testing.
"""

import pytest
import asyncio
from uuid import uuid4
from typing import Dict, Any, AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import AsyncSessionLocal, engine
from app.models.base import Base
from app.models import User, ClientAccount, Engagement


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine"""
    # Use in-memory SQLite for fast testing
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    await engine.dispose()


@pytest.fixture(scope="session")
async def test_session_factory(test_engine):
    """Create test session factory"""
    factory = sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    return factory


@pytest.fixture
async def test_session(test_session_factory) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session"""
    async with test_session_factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def test_user(test_session: AsyncSession) -> User:
    """Create test user"""
    user = User(
        id=uuid4(),
        username="integration_test_user",
        email="integration@test.com",
        hashed_password="test_hash",
        is_active=True,
        is_verified=True
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    return user


@pytest.fixture
async def test_client(test_session: AsyncSession) -> ClientAccount:
    """Create test client account"""
    client = ClientAccount(
        id=uuid4(),
        account_name="Integration Test Client",
        industry="Technology",
        company_size="Enterprise",
        headquarters_location="Test City",
        primary_contact_name="Test Contact",
        primary_contact_email="contact@testclient.com",
        business_objectives=["Cost Reduction", "Modernization"],
        target_cloud_providers=["aws", "azure"],
        business_priorities=["cost_reduction", "agility_speed"],
        compliance_requirements=["SOC2", "GDPR"]
    )
    test_session.add(client)
    await test_session.commit()
    await test_session.refresh(client)
    return client


@pytest.fixture
async def test_engagement(
    test_session: AsyncSession,
    test_user: User,
    test_client: ClientAccount
) -> Engagement:
    """Create test engagement"""
    engagement = Engagement(
        id=uuid4(),
        name="Integration Test Engagement",
        description="Test engagement for integration testing",
        client_id=test_client.id,
        created_by=test_user.id,
        status="active",
        scope="full_migration_assessment",
        timeline_months=6,
        budget_range="100k-500k"
    )
    test_session.add(engagement)
    await test_session.commit()
    await test_session.refresh(engagement)
    return engagement


@pytest.fixture
def integration_test_config() -> Dict[str, Any]:
    """Integration test configuration"""
    return {
        "test_timeouts": {
            "workflow_execution": 30,  # seconds
            "validation": 10,
            "synchronization": 5,
            "error_recovery": 15
        },
        "test_data_sizes": {
            "small": 5,
            "medium": 25,
            "large": 100
        },
        "performance_thresholds": {
            "workflow_execution": 30.0,  # seconds
            "validation_speed": 5.0,
            "sync_speed": 2.0,
            "memory_usage": 100 * 1024 * 1024  # 100MB
        },
        "quality_thresholds": {
            "min_confidence": 0.7,
            "min_completeness": 0.8,
            "max_critical_issues": 0
        }
    }


@pytest.fixture
async def populated_engagement(
    test_session: AsyncSession,
    test_engagement: Engagement,
    integration_test_config: Dict[str, Any]
) -> Dict[str, Any]:
    """Create engagement with populated test data"""
    from app.models.asset import Asset
    from app.models.collection_flow import CollectionFlow
    
    # Create collection flow
    collection_flow = CollectionFlow(
        id=uuid4(),
        engagement_id=test_engagement.id,
        user_id=test_engagement.created_by,
        client_id=test_engagement.client_id,
        status="completed",
        current_phase="completed",
        progress_percentage=100.0,
        automation_tier="tier_1",
        confidence_score=0.85,
        metadata={"asset_count": integration_test_config["test_data_sizes"]["small"]}
    )
    test_session.add(collection_flow)
    
    # Create test assets
    assets = []
    asset_count = integration_test_config["test_data_sizes"]["small"]
    
    for i in range(asset_count):
        asset = Asset(
            id=uuid4(),
            engagement_id=test_engagement.id,
            name=f"Test Asset {i+1}",
            type="application" if i % 2 == 0 else "database",
            environment="production" if i % 3 == 0 else "staging",
            business_criticality=3 + (i % 3),
            confidence_score=0.7 + (i % 3) * 0.1,
            technical_fit_score=0.8,
            status="active",
            metadata={"test_asset": True}
        )
        test_session.add(asset)
        assets.append(asset)
    
    await test_session.commit()
    
    # Refresh objects
    await test_session.refresh(collection_flow)
    for asset in assets:
        await test_session.refresh(asset)
    
    return {
        "engagement": test_engagement,
        "collection_flow": collection_flow,
        "assets": assets,
        "asset_count": asset_count
    }


@pytest.mark.asyncio
class BaseIntegrationTest:
    """Base class for integration tests with common utilities"""
    
    async def assert_workflow_completion(
        self,
        workflow_context,
        expected_phases: list = None,
        min_confidence: float = 0.0
    ):
        """Assert workflow completed successfully"""
        assert workflow_context is not None
        assert workflow_context.engagement_id is not None
        
        if expected_phases:
            completed_phases = [
                entry["phase"] for entry in workflow_context.phase_history
                if entry["status"] == "completed"
            ]
            for phase in expected_phases:
                assert phase in completed_phases
        
        if min_confidence > 0:
            confidence = workflow_context.data_quality_metrics.get("overall_confidence", 0.0)
            assert confidence >= min_confidence
    
    async def assert_validation_quality(
        self,
        validation_result,
        max_critical_issues: int = 0,
        min_overall_score: float = 0.7
    ):
        """Assert validation meets quality standards"""
        assert validation_result is not None
        assert validation_result.overall_score >= min_overall_score
        
        critical_issues = [
            issue for issue in validation_result.issues
            if issue.severity.value == "critical"
        ]
        assert len(critical_issues) <= max_critical_issues
    
    async def assert_sync_health(
        self,
        sync_context,
        max_conflicts: int = 0
    ):
        """Assert synchronization is healthy"""
        assert sync_context is not None
        assert len(sync_context.conflicts) <= max_conflicts
        
        # Check that flows are properly tracked
        if sync_context.flows:
            for flow_type, flow_state in sync_context.flows.items():
                assert flow_state.flow_id is not None
                assert flow_state.status is not None
    
    async def measure_performance(self, operation_func, max_duration: float = 30.0):
        """Measure and assert operation performance"""
        import time
        
        start_time = time.time()
        result = await operation_func()
        end_time = time.time()
        
        duration = end_time - start_time
        assert duration <= max_duration, f"Operation took {duration:.2f}s, max allowed: {max_duration}s"
        
        return result, duration


# Performance monitoring utilities
@pytest.fixture
def performance_monitor():
    """Performance monitoring utilities"""
    
    class PerformanceMonitor:
        def __init__(self):
            self.metrics = {}
        
        async def time_operation(self, operation_name: str, operation_func):
            """Time an async operation"""
            import time
            
            start_time = time.time()
            result = await operation_func()
            end_time = time.time()
            
            duration = end_time - start_time
            self.metrics[operation_name] = duration
            
            return result, duration
        
        def get_metrics(self) -> Dict[str, float]:
            """Get collected performance metrics"""
            return self.metrics.copy()
        
        def assert_performance(
            self,
            operation_name: str,
            max_duration: float,
            message: str = None
        ):
            """Assert operation met performance requirements"""
            duration = self.metrics.get(operation_name)
            assert duration is not None, f"No metrics found for operation: {operation_name}"
            
            error_msg = message or f"Operation {operation_name} took {duration:.2f}s, max: {max_duration}s"
            assert duration <= max_duration, error_msg
    
    return PerformanceMonitor()


# Memory monitoring utilities  
@pytest.fixture
def memory_monitor():
    """Memory usage monitoring utilities"""
    
    class MemoryMonitor:
        def __init__(self):
            self.snapshots = {}
        
        def take_snapshot(self, name: str):
            """Take memory usage snapshot"""
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            
            self.snapshots[name] = {
                "rss": memory_info.rss,
                "vms": memory_info.vms,
                "timestamp": asyncio.get_event_loop().time()
            }
        
        def get_memory_diff(self, start_snapshot: str, end_snapshot: str) -> Dict[str, int]:
            """Get memory difference between snapshots"""
            start = self.snapshots.get(start_snapshot)
            end = self.snapshots.get(end_snapshot)
            
            assert start is not None, f"Start snapshot '{start_snapshot}' not found"
            assert end is not None, f"End snapshot '{end_snapshot}' not found"
            
            return {
                "rss_diff": end["rss"] - start["rss"],
                "vms_diff": end["vms"] - start["vms"],
                "duration": end["timestamp"] - start["timestamp"]
            }
        
        def assert_memory_usage(
            self,
            start_snapshot: str,
            end_snapshot: str,
            max_memory_increase: int = 50 * 1024 * 1024  # 50MB
        ):
            """Assert memory usage stayed within bounds"""
            diff = self.get_memory_diff(start_snapshot, end_snapshot)
            
            assert diff["rss_diff"] <= max_memory_increase, (
                f"Memory increased by {diff['rss_diff'] / 1024 / 1024:.1f}MB, "
                f"max allowed: {max_memory_increase / 1024 / 1024:.1f}MB"
            )
    
    return MemoryMonitor()