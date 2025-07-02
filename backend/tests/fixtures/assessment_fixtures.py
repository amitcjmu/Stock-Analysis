"""
Assessment Flow Test Fixtures

Provides test fixtures and utilities for assessment flow testing.
"""

import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from typing import Dict, List, Any

try:
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.core.database import AsyncSessionLocal
    from app.core.flow_context import FlowContext
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    AsyncSession = object
    AsyncSessionLocal = None
    FlowContext = object


@pytest.fixture
async def async_db_session():
    """Create async database session for testing"""
    if not SQLALCHEMY_AVAILABLE:
        pytest.skip("SQLAlchemy not available")
    
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.rollback()


@pytest.fixture
def sample_assessment_flow_state():
    """Sample assessment flow state for testing"""
    return {
        "flow_id": "test-flow-123",
        "client_account_id": 1,
        "engagement_id": 1,
        "selected_application_ids": ["app-1", "app-2"],
        "current_phase": "architecture_minimums",
        "next_phase": "tech_debt_analysis",
        "status": "initialized",
        "progress": 10,
        "pause_points": [],
        "user_inputs_captured": False,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "engagement_architecture_standards": [],
        "application_architecture_overrides": {},
        "application_components": {},
        "tech_debt_analysis": {},
        "sixr_decisions": {},
        "assessment_results": {},
        "apps_ready_for_planning": []
    }


@pytest.fixture
def mock_crewai_service():
    """Mock CrewAI service for testing"""
    mock = AsyncMock()
    mock.run_crew = AsyncMock()
    mock.is_configured = MagicMock(return_value=True)
    return mock


@pytest.fixture
def sample_applications():
    """Sample application IDs for testing"""
    return ["app-1", "app-2", "app-3"]


@pytest.fixture
def sample_engagement_context():
    """Sample engagement context data"""
    return {
        "engagement_id": 1,
        "client_account_id": 1,
        "engagement_name": "Test Migration Project",
        "engagement_type": "cloud_migration",
        "target_cloud": "aws",
        "compliance_requirements": ["SOX", "PCI"],
        "business_drivers": ["cost_optimization", "modernization"],
        "timeline_constraints": {
            "project_start": "2025-01-01",
            "go_live_target": "2025-12-31"
        }
    }


@pytest.fixture
def sample_architecture_standards():
    """Sample architecture standards"""
    return [
        {
            "requirement_type": "java_versions",
            "description": "Minimum Java version requirements",
            "mandatory": True,
            "supported_versions": {"java": "11+"},
            "rationale": "Java 8 end of life support",
            "exceptions_allowed": False
        },
        {
            "requirement_type": "database_platforms",
            "description": "Approved database platforms",
            "mandatory": True,
            "supported_versions": {
                "postgresql": "12+",
                "mysql": "8.0+",
                "oracle": "19c+"
            },
            "rationale": "Cloud compatibility and support",
            "exceptions_allowed": True
        },
        {
            "requirement_type": "container_support",
            "description": "Application containerization requirements",
            "mandatory": False,
            "supported_versions": {"docker": "20.10+"},
            "rationale": "Modernization and scalability",
            "exceptions_allowed": True
        }
    ]


@pytest.fixture
def sample_application_metadata():
    """Sample application metadata for testing"""
    return {
        "app-1": {
            "application_name": "Frontend Portal",
            "technology_stack": {
                "frontend": "React 16.14.0",
                "backend": "Node.js 14.18.0",
                "database": "PostgreSQL 11"
            },
            "criticality": "high",
            "user_base": 5000,
            "data_sensitivity": "medium"
        },
        "app-2": {
            "application_name": "Backend API",
            "technology_stack": {
                "runtime": "Java 8",
                "framework": "Spring 5.2.0",
                "database": "Oracle 12c"
            },
            "criticality": "critical",
            "user_base": 10000,
            "data_sensitivity": "high"
        },
        "app-3": {
            "application_name": "Analytics Service",
            "technology_stack": {
                "runtime": "Python 3.8",
                "framework": "Django 3.2",
                "database": "MySQL 5.7"
            },
            "criticality": "medium",
            "user_base": 500,
            "data_sensitivity": "low"
        }
    }


@pytest.fixture
def sample_component_analysis_result():
    """Sample component analysis result from CrewAI"""
    return {
        "components": [
            {
                "name": "frontend",
                "type": "ui",
                "technology_stack": {"react": "16.14.0", "typescript": "4.1.0"},
                "dependencies": ["backend_api"],
                "component_size": "large",
                "complexity_score": 6.5
            },
            {
                "name": "backend_api",
                "type": "api",
                "technology_stack": {"java": "8", "spring": "5.2.0"},
                "dependencies": ["database", "auth_service"],
                "component_size": "large",
                "complexity_score": 8.5
            },
            {
                "name": "database",
                "type": "data",
                "technology_stack": {"oracle": "12c"},
                "dependencies": [],
                "component_size": "medium",
                "complexity_score": 7.0
            }
        ],
        "tech_debt_analysis": [
            {
                "category": "version_obsolescence",
                "severity": "high",
                "description": "Java 8 is end-of-life",
                "score": 8.5,
                "component": "backend_api",
                "recommendations": ["Upgrade to Java 11 or 17"]
            },
            {
                "category": "framework_outdated",
                "severity": "medium",
                "description": "React 16 is several versions behind",
                "score": 6.0,
                "component": "frontend",
                "recommendations": ["Upgrade to React 18"]
            }
        ],
        "component_scores": {
            "frontend": 6.0,
            "backend_api": 8.5,
            "database": 7.0
        },
        "overall_tech_debt_score": 7.2
    }


@pytest.fixture
def sample_sixr_strategy_result():
    """Sample 6R strategy analysis result"""
    return {
        "component_treatments": [
            {
                "component_name": "frontend",
                "recommended_strategy": "refactor",
                "rationale": "React upgrade and modernization needed",
                "compatibility_validated": True,
                "effort_estimate": "medium",
                "risk_level": "low"
            },
            {
                "component_name": "backend_api",
                "recommended_strategy": "replatform",
                "rationale": "Java upgrade with containerization",
                "compatibility_validated": True,
                "effort_estimate": "high",
                "risk_level": "medium"
            },
            {
                "component_name": "database",
                "recommended_strategy": "rehost",
                "rationale": "Lift and shift to cloud with minor updates",
                "compatibility_validated": True,
                "effort_estimate": "low",
                "risk_level": "low"
            }
        ],
        "overall_strategy": "refactor",
        "confidence_score": 0.85,
        "rationale": "Moderate modernization with strategic upgrades",
        "move_group_hints": ["Group with other Java microservices"],
        "estimated_effort_weeks": 16,
        "estimated_cost_range": "$150k-$200k"
    }


@pytest.fixture 
async def flow_context(async_db_session: AsyncSession):
    """Create test flow context with proper multi-tenant setup"""
    if not SQLALCHEMY_AVAILABLE:
        pytest.skip("SQLAlchemy not available")
    
    return FlowContext(
        flow_id="test-flow-123",
        client_account_id=1,
        engagement_id=1,
        user_id="test-user",
        db_session=async_db_session
    )


@pytest.fixture
def mock_flow_context():
    """Mock flow context for testing without database"""
    mock = MagicMock()
    mock.flow_id = "test-flow-123"
    mock.client_account_id = 1
    mock.engagement_id = 1
    mock.user_id = "test-user"
    return mock


@pytest.fixture
def sample_assessment_results():
    """Sample complete assessment results"""
    return {
        "total_apps_assessed": 2,
        "apps_ready_for_planning": 2,
        "overall_assessment_score": 7.5,
        "assessment_summary": {
            "apps_by_strategy": {
                "refactor": 1,
                "replatform": 1,
                "rehost": 0,
                "retain": 0,
                "retire": 0,
                "repurchase": 0
            },
            "risk_distribution": {
                "low": 1,
                "medium": 1,
                "high": 0,
                "critical": 0
            },
            "effort_distribution": {
                "low": 0,
                "medium": 1,
                "high": 1
            }
        },
        "applications": {
            "app-1": {
                "application_name": "Frontend Portal",
                "recommended_strategy": "refactor",
                "confidence_score": 0.85,
                "overall_score": 6.0,
                "components": [
                    {
                        "component_name": "frontend",
                        "tech_debt_score": 6.0,
                        "recommended_treatment": "refactor"
                    }
                ]
            },
            "app-2": {
                "application_name": "Backend API", 
                "recommended_strategy": "replatform",
                "confidence_score": 0.80,
                "overall_score": 8.5,
                "components": [
                    {
                        "component_name": "backend_api",
                        "tech_debt_score": 8.5,
                        "recommended_treatment": "replatform"
                    }
                ]
            }
        }
    }


@pytest.fixture
def large_application_dataset():
    """Large application dataset for performance testing"""
    apps = {}
    for i in range(50):
        apps[f"app-{i}"] = {
            "application_name": f"Application {i}",
            "technology_stack": {
                "runtime": "Java 8" if i % 2 == 0 else "Python 3.8",
                "database": "PostgreSQL 11"
            },
            "criticality": ["low", "medium", "high"][i % 3],
            "user_base": (i + 1) * 100
        }
    return apps


class MockPostgresStore:
    """Mock PostgreSQL store for testing"""
    
    def __init__(self):
        self.stored_data = {}
    
    async def save_flow_state(self, flow_id: str, state: Dict[str, Any]):
        """Mock save flow state"""
        self.stored_data[flow_id] = state
    
    async def load_flow_state(self, flow_id: str) -> Dict[str, Any]:
        """Mock load flow state"""
        return self.stored_data.get(flow_id)
    
    async def delete_flow_state(self, flow_id: str):
        """Mock delete flow state"""
        if flow_id in self.stored_data:
            del self.stored_data[flow_id]


@pytest.fixture
def mock_postgres_store():
    """Mock PostgreSQL store fixture"""
    return MockPostgresStore()


class MockAssessmentRepository:
    """Mock assessment repository for testing"""
    
    def __init__(self, client_account_id: int):
        self.client_account_id = client_account_id
        self.flows = {}
        self.user_inputs = {}
    
    async def create_assessment_flow(self, engagement_id: int, selected_application_ids: List[str], created_by: str) -> str:
        """Mock create assessment flow"""
        flow_id = f"test-flow-{uuid4()}"
        self.flows[flow_id] = {
            "flow_id": flow_id,
            "engagement_id": engagement_id,
            "selected_application_ids": selected_application_ids,
            "created_by": created_by,
            "client_account_id": self.client_account_id
        }
        return flow_id
    
    async def get_assessment_flow_state(self, flow_id: str):
        """Mock get assessment flow state"""
        return self.flows.get(flow_id)
    
    async def save_flow_state(self, flow_state):
        """Mock save flow state"""
        self.flows[flow_state.flow_id] = flow_state
    
    async def save_user_input(self, flow_id: str, phase: str, user_input: Dict[str, Any]):
        """Mock save user input"""
        if flow_id not in self.user_inputs:
            self.user_inputs[flow_id] = {}
        self.user_inputs[flow_id][phase] = user_input


@pytest.fixture
def mock_assessment_repository():
    """Mock assessment repository fixture"""
    return MockAssessmentRepository(client_account_id=1)


# Test utilities
def create_test_event_loop():
    """Create event loop for async testing"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError("Event loop is closed")
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop


def assert_flow_state_valid(flow_state, expected_phase: str = None):
    """Assert that flow state is valid"""
    assert flow_state is not None
    assert "flow_id" in flow_state
    assert "status" in flow_state
    assert "current_phase" in flow_state
    assert "progress" in flow_state
    
    if expected_phase:
        assert flow_state["current_phase"] == expected_phase


def assert_multi_tenant_isolation(repository, flow_id: str, client_account_id: int):
    """Assert multi-tenant isolation is maintained"""
    assert repository.client_account_id == client_account_id
    flow_state = repository.flows.get(flow_id)
    if flow_state:
        assert flow_state["client_account_id"] == client_account_id