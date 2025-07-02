# Assessment Flow - Testing & DevOps Tasks

## Overview
This document tracks all testing, deployment, monitoring, and DevOps tasks for the Assessment Flow implementation.

## Key Implementation Context
- **Docker-first development** for all testing and deployment
- **Remediation-aware testing** to handle mixed v1/v3 API states
- **Multi-tenant testing** with proper client account isolation
- **CrewAI agent testing** with mock and integration test patterns
- **Performance testing** for large application portfolios
- **Database migration validation** for PostgreSQL-only architecture

---

## 🧪 Testing Tasks

### TEST-001: Create Assessment Flow Unit Tests
**Status**: 🔴 Not Started  
**Priority**: P1 - High  
**Effort**: 16 hours  
**Dependencies**: Backend Core (BE-001), API Core (API-001)  
**Sprint**: Testing Week 9-10  

**Description**: Implement comprehensive unit tests for assessment flow components with Docker-based test execution

**Location**: `backend/tests/assessment_flow/`

**Technical Requirements**:
- pytest-based test suite with asyncio support
- Docker container test execution environment
- Mock CrewAI agents for isolated testing
- Multi-tenant test data isolation
- PostgreSQL test database with proper cleanup
- Test coverage for all core components

**Test Structure and Implementation**:
```python
# backend/tests/assessment_flow/test_unified_assessment_flow.py

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.crewai_flows.unified_assessment_flow import UnifiedAssessmentFlow
from app.models.assessment_flow import AssessmentFlowState, AssessmentPhase
from app.core.flow_context import FlowContext
from tests.fixtures.assessment_fixtures import (
    sample_assessment_flow_state,
    mock_crewai_service,
    sample_applications
)

class TestUnifiedAssessmentFlow:
    """Unit tests for UnifiedAssessmentFlow with mock agents"""
    
    @pytest.fixture
    async def flow_context(self, async_db_session: AsyncSession):
        """Create test flow context with proper multi-tenant setup"""
        return FlowContext(
            flow_id="test-flow-123",
            client_account_id=1,
            engagement_id=1,
            user_id="test-user",
            db_session=async_db_session
        )
    
    @pytest.fixture
    async def assessment_flow(self, flow_context, mock_crewai_service):
        """Create assessment flow instance with mocked dependencies"""
        return UnifiedAssessmentFlow(
            crewai_service=mock_crewai_service,
            context=flow_context
        )
    
    @pytest.mark.asyncio
    async def test_initialize_assessment_success(
        self,
        assessment_flow: UnifiedAssessmentFlow,
        sample_applications
    ):
        """Test successful assessment flow initialization"""
        
        # Mock repository methods
        with patch.object(assessment_flow.repository, 'create_assessment_flow') as mock_create:
            mock_create.return_value = "test-flow-123"
            
            # Execute initialization
            result = await assessment_flow.initialize_assessment()
            
            # Assertions
            assert result.flow_id == "test-flow-123"
            assert result.status == "initialized"
            assert result.current_phase == AssessmentPhase.ARCHITECTURE_MINIMUMS
            assert result.progress == 10
            assert len(result.selected_application_ids) > 0
            
            # Verify repository calls
            mock_create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_capture_architecture_minimums_with_defaults(
        self,
        assessment_flow: UnifiedAssessmentFlow,
        sample_assessment_flow_state
    ):
        """Test architecture minimums capture with default standards"""
        
        # Mock engagement standards loading
        with patch.object(assessment_flow, '_load_engagement_standards') as mock_load:
            mock_load.return_value = []
            
            with patch.object(assessment_flow, '_initialize_default_standards') as mock_init:
                mock_init.return_value = [
                    {
                        "requirement_type": "java_versions",
                        "description": "Minimum Java version requirements",
                        "mandatory": True,
                        "supported_versions": {"java": "11+"}
                    }
                ]
                
                # Execute phase
                result = await assessment_flow.capture_architecture_minimums(sample_assessment_flow_state)
                
                # Assertions
                assert result.current_phase == AssessmentPhase.ARCHITECTURE_MINIMUMS
                assert result.status == "paused_for_user_input"
                assert "architecture_minimums" in result.pause_points
                assert len(result.engagement_architecture_standards) == 1
                assert result.progress == 20
    
    @pytest.mark.asyncio
    async def test_analyze_technical_debt_with_components(
        self,
        assessment_flow: UnifiedAssessmentFlow,
        sample_assessment_flow_state,
        mock_crewai_service
    ):
        """Test technical debt analysis with component identification"""
        
        # Setup mock crew result
        mock_crew_result = {
            "components": [
                {
                    "name": "frontend",
                    "type": "ui",
                    "technology_stack": {"react": "16.14.0", "typescript": "4.1.0"},
                    "dependencies": []
                },
                {
                    "name": "backend",
                    "type": "api", 
                    "technology_stack": {"java": "8", "spring": "5.2.0"},
                    "dependencies": ["database"]
                }
            ],
            "tech_debt_analysis": [
                {
                    "category": "version_obsolescence",
                    "severity": "high",
                    "description": "Java 8 is end-of-life",
                    "score": 8.5,
                    "component": "backend"
                }
            ],
            "component_scores": {
                "frontend": 6.0,
                "backend": 8.5
            }
        }
        
        mock_crewai_service.run_crew.return_value = mock_crew_result
        
        # Mock application metadata
        with patch.object(assessment_flow, '_get_application_metadata') as mock_metadata:
            mock_metadata.return_value = {"app_type": "web_application"}
            
            # Execute phase
            result = await assessment_flow.analyze_technical_debt(sample_assessment_flow_state)
            
            # Assertions
            assert result.current_phase == AssessmentPhase.TECH_DEBT_ANALYSIS
            assert result.status == "paused_for_user_input"
            assert len(result.application_components) > 0
            assert len(result.tech_debt_analysis) > 0
            assert result.progress == 50
            
            # Verify crew was called correctly
            mock_crewai_service.run_crew.assert_called_with(
                "component_analysis_crew",
                context=pytest.Any
            )
    
    @pytest.mark.asyncio
    async def test_determine_sixr_strategies_with_validation(
        self,
        assessment_flow: UnifiedAssessmentFlow,
        sample_assessment_flow_state,
        mock_crewai_service
    ):
        """Test 6R strategy determination with compatibility validation"""
        
        # Setup mock crew result
        mock_crew_result = {
            "component_treatments": [
                {
                    "component_name": "frontend",
                    "recommended_strategy": "refactor",
                    "rationale": "React 16 needs modernization",
                    "compatibility_validated": True
                },
                {
                    "component_name": "backend", 
                    "recommended_strategy": "replatform",
                    "rationale": "Java 8 to 11 upgrade with containerization",
                    "compatibility_validated": True
                }
            ],
            "overall_strategy": "refactor",
            "confidence_score": 0.85,
            "rationale": "Moderate modernization with React upgrade",
            "move_group_hints": ["Group with other Java services"]
        }
        
        mock_crewai_service.run_crew.return_value = mock_crew_result
        
        # Mock application name lookup
        with patch.object(assessment_flow, '_get_application_name') as mock_name:
            mock_name.return_value = "Test Application"
            
            # Execute phase
            result = await assessment_flow.determine_component_sixr_strategies(sample_assessment_flow_state)
            
            # Assertions
            assert result.current_phase == AssessmentPhase.COMPONENT_SIXR_STRATEGIES
            assert result.status == "paused_for_user_input"
            assert len(result.sixr_decisions) > 0
            assert result.progress == 75
            
            # Verify decision structure
            app_id = list(result.sixr_decisions.keys())[0]
            decision = result.sixr_decisions[app_id]
            assert decision.overall_strategy == "refactor"
            assert decision.confidence_score == 0.85
            assert len(decision.component_treatments) == 2
    
    @pytest.mark.asyncio
    async def test_resume_from_phase_with_user_input(
        self,
        assessment_flow: UnifiedAssessmentFlow
    ):
        """Test flow resume functionality with user input"""
        
        user_input = {
            "architecture_standards": [
                {
                    "requirement_type": "custom_standard",
                    "description": "Custom requirement",
                    "mandatory": False
                }
            ]
        }
        
        # Mock state loading and saving
        with patch.object(assessment_flow.postgres_store, 'load_flow_state') as mock_load:
            mock_load.return_value = sample_assessment_flow_state
            
            with patch.object(assessment_flow.repository, 'save_user_input') as mock_save:
                with patch.object(assessment_flow, 'analyze_technical_debt') as mock_next_phase:
                    mock_next_phase.return_value = sample_assessment_flow_state
                    
                    # Execute resume
                    result = await assessment_flow.resume_from_phase(
                        AssessmentPhase.ARCHITECTURE_MINIMUMS,
                        user_input
                    )
                    
                    # Assertions
                    assert result is not None
                    mock_save.assert_called_once()
                    mock_next_phase.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_error_handling_during_crew_execution(
        self,
        assessment_flow: UnifiedAssessmentFlow,
        sample_assessment_flow_state,
        mock_crewai_service
    ):
        """Test error handling when CrewAI execution fails"""
        
        # Setup crew to raise exception
        mock_crewai_service.run_crew.side_effect = Exception("Crew execution failed")
        
        # Execute phase and expect exception
        with pytest.raises(Exception) as exc_info:
            await assessment_flow.analyze_technical_debt(sample_assessment_flow_state)
        
        assert "Crew execution failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_multi_tenant_isolation(
        self,
        async_db_session: AsyncSession,
        mock_crewai_service
    ):
        """Test that flows maintain multi-tenant isolation"""
        
        # Create flows for different clients
        context_1 = FlowContext(
            flow_id="flow-client-1",
            client_account_id=1,
            engagement_id=1,
            user_id="user-1",
            db_session=async_db_session
        )
        
        context_2 = FlowContext(
            flow_id="flow-client-2", 
            client_account_id=2,
            engagement_id=2,
            user_id="user-2",
            db_session=async_db_session
        )
        
        flow_1 = UnifiedAssessmentFlow(mock_crewai_service, context_1)
        flow_2 = UnifiedAssessmentFlow(mock_crewai_service, context_2)
        
        # Mock repository isolation
        with patch.object(flow_1.repository, 'get_assessment_flow_state') as mock_1:
            with patch.object(flow_2.repository, 'get_assessment_flow_state') as mock_2:
                mock_1.return_value = None
                mock_2.return_value = None
                
                # Verify different client contexts
                assert flow_1.context.client_account_id == 1
                assert flow_2.context.client_account_id == 2
                assert flow_1.repository.client_account_id == 1
                assert flow_2.repository.client_account_id == 2


# backend/tests/assessment_flow/test_assessment_repository.py

class TestAssessmentFlowRepository:
    """Unit tests for AssessmentFlowRepository with database operations"""
    
    @pytest.mark.asyncio
    async def test_create_assessment_flow(
        self,
        assessment_repository,
        sample_applications
    ):
        """Test assessment flow creation with proper data persistence"""
        
        flow_id = await assessment_repository.create_assessment_flow(
            engagement_id=1,
            selected_application_ids=sample_applications,
            created_by="test@example.com"
        )
        
        assert flow_id is not None
        assert isinstance(flow_id, str)
        
        # Verify flow was created in database
        flow_state = await assessment_repository.get_assessment_flow_state(flow_id)
        assert flow_state is not None
        assert flow_state.engagement_id == 1
        assert flow_state.selected_application_ids == sample_applications
    
    @pytest.mark.asyncio
    async def test_save_and_retrieve_flow_state(
        self,
        assessment_repository,
        sample_assessment_flow_state
    ):
        """Test complete flow state persistence and retrieval"""
        
        # Save flow state
        await assessment_repository.save_flow_state(sample_assessment_flow_state)
        
        # Retrieve and verify
        retrieved_state = await assessment_repository.get_assessment_flow_state(
            sample_assessment_flow_state.flow_id
        )
        
        assert retrieved_state is not None
        assert retrieved_state.flow_id == sample_assessment_flow_state.flow_id
        assert retrieved_state.status == sample_assessment_flow_state.status
        assert retrieved_state.current_phase == sample_assessment_flow_state.current_phase
    
    @pytest.mark.asyncio
    async def test_multi_tenant_data_isolation(
        self,
        async_db_session: AsyncSession
    ):
        """Test that repository enforces multi-tenant data isolation"""
        
        # Create repositories for different clients
        repo_1 = AssessmentFlowRepository(async_db_session, client_account_id=1)
        repo_2 = AssessmentFlowRepository(async_db_session, client_account_id=2)
        
        # Create flow for client 1
        flow_id_1 = await repo_1.create_assessment_flow(
            engagement_id=1,
            selected_application_ids=["app-1"],
            created_by="client1@example.com"
        )
        
        # Try to access from client 2 (should fail/return None)
        flow_state_2 = await repo_2.get_assessment_flow_state(flow_id_1)
        assert flow_state_2 is None
        
        # Client 1 should still have access
        flow_state_1 = await repo_1.get_assessment_flow_state(flow_id_1)
        assert flow_state_1 is not None


# backend/tests/assessment_flow/test_crewai_crews.py

class TestArchitectureStandardsCrew:
    """Unit tests for Architecture Standards CrewAI crew"""
    
    @pytest.mark.asyncio
    async def test_crew_execution_with_mocked_agents(
        self,
        mock_flow_context,
        sample_engagement_context
    ):
        """Test crew execution with mocked agents"""
        
        crew = ArchitectureStandardsCrew(mock_flow_context)
        
        with patch.object(crew.crew, 'kickoff') as mock_kickoff:
            mock_kickoff.return_value = {
                "architecture_standards": [
                    {
                        "requirement_type": "java_versions",
                        "description": "Java version requirements",
                        "mandatory": True
                    }
                ],
                "compliance_analysis": {},
                "architecture_exceptions": [],
                "confidence_score": 0.9
            }
            
            result = await crew.execute({
                "engagement_context": sample_engagement_context,
                "selected_applications": ["app-1", "app-2"]
            })
            
            assert "engagement_standards" in result
            assert "application_compliance" in result
            assert result["crew_confidence"] == 0.9
            mock_kickoff.assert_called_once()
```

**Test Fixtures and Utilities**:
```python
# backend/tests/fixtures/assessment_fixtures.py

import pytest
from datetime import datetime
from app.models.assessment_flow import AssessmentFlowState, AssessmentPhase

@pytest.fixture
def sample_assessment_flow_state():
    """Sample assessment flow state for testing"""
    return AssessmentFlowState(
        flow_id="test-flow-123",
        client_account_id=1,
        engagement_id=1,
        selected_application_ids=["app-1", "app-2"],
        current_phase=AssessmentPhase.ARCHITECTURE_MINIMUMS,
        status="initialized",
        progress=10,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

@pytest.fixture
def mock_crewai_service():
    """Mock CrewAI service for testing"""
    mock = AsyncMock()
    mock.run_crew = AsyncMock()
    return mock

@pytest.fixture
def sample_applications():
    """Sample application IDs for testing"""
    return ["app-1", "app-2", "app-3"]

@pytest.fixture
async def assessment_repository(async_db_session):
    """Assessment repository with test database"""
    from app.repositories.assessment_flow_repository import AssessmentFlowRepository
    return AssessmentFlowRepository(async_db_session, client_account_id=1)
```

**Docker Test Configuration**:
```yaml
# docker-compose.test.yml
version: '3.8'

services:
  test-backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.test
    environment:
      - DATABASE_URL=postgresql://test_user:test_pass@test-db:5432/test_assessment_db
      - PYTEST_ARGS=tests/assessment_flow/
    depends_on:
      - test-db
    volumes:
      - ./backend:/app
    command: ["pytest", "-v", "--cov=app", "tests/assessment_flow/"]
  
  test-db:
    image: postgres:15
    environment:
      - POSTGRES_USER=test_user
      - POSTGRES_PASSWORD=test_pass
      - POSTGRES_DB=test_assessment_db
    ports:
      - "5433:5432"
```

**Acceptance Criteria**:
- [ ] Complete unit test coverage for UnifiedAssessmentFlow
- [ ] Repository layer testing with database operations
- [ ] CrewAI crew testing with mocked agents
- [ ] Multi-tenant isolation validation
- [ ] Error handling and recovery testing
- [ ] Docker-based test execution environment
- [ ] Test data fixtures and utilities
- [ ] Performance benchmarking for large flows

---

### TEST-002: Create Assessment Flow Integration Tests
**Status**: 🔴 Not Started  
**Priority**: P1 - High  
**Effort**: 12 hours  
**Dependencies**: TEST-001, API Core (API-001)  
**Sprint**: Testing Week 9-10  

**Description**: Implement end-to-end integration tests for complete assessment flow execution

**Location**: `backend/tests/integration/assessment_flow/`

**Technical Requirements**:
- Full flow execution from initialization to completion
- Real CrewAI agent integration (not mocked)
- Database state validation throughout flow
- API endpoint integration testing
- Multi-tenant flow isolation validation
- Performance testing with realistic data volumes

**Integration Test Implementation**:
```python
# backend/tests/integration/assessment_flow/test_assessment_flow_integration.py

import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.core.database import get_async_db
from tests.fixtures.integration_fixtures import (
    integration_test_db,
    sample_discovery_data,
    test_client_with_auth
)

class TestAssessmentFlowIntegration:
    """End-to-end integration tests for assessment flow"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_complete_assessment_flow_execution(
        self,
        test_client_with_auth: AsyncClient,
        integration_test_db: AsyncSession,
        sample_discovery_data
    ):
        """Test complete assessment flow from initialization to completion"""
        
        # Step 1: Initialize assessment flow
        init_response = await test_client_with_auth.post(
            "/api/v1/assessment-flow/initialize",
            json={
                "selected_application_ids": ["app-1", "app-2"]
            },
            headers={
                "X-Client-Account-ID": "1",
                "X-Engagement-ID": "1"
            }
        )
        
        assert init_response.status_code == 200
        init_data = init_response.json()
        flow_id = init_data["flow_id"]
        
        # Step 2: Wait for initialization to complete
        await self._wait_for_phase_completion(test_client_with_auth, flow_id, "architecture_minimums")
        
        # Step 3: Provide architecture standards input
        arch_response = await test_client_with_auth.put(
            f"/api/v1/assessment-flow/{flow_id}/architecture-minimums",
            json={
                "engagement_standards": [
                    {
                        "requirement_type": "java_versions",
                        "description": "Minimum Java 11",
                        "mandatory": True,
                        "supported_versions": {"java": "11+"}
                    }
                ],
                "application_overrides": {}
            }
        )
        
        assert arch_response.status_code == 200
        
        # Step 4: Resume flow to tech debt analysis
        resume_response = await test_client_with_auth.post(
            f"/api/v1/assessment-flow/{flow_id}/resume",
            json={
                "user_input": {
                    "standards_approved": True
                }
            }
        )
        
        assert resume_response.status_code == 200
        
        # Step 5: Wait for tech debt analysis completion
        await self._wait_for_phase_completion(test_client_with_auth, flow_id, "tech_debt_analysis")
        
        # Step 6: Verify tech debt analysis results
        tech_debt_response = await test_client_with_auth.get(
            f"/api/v1/assessment-flow/{flow_id}/tech-debt"
        )
        
        assert tech_debt_response.status_code == 200
        tech_debt_data = tech_debt_response.json()
        assert "applications" in tech_debt_data
        assert len(tech_debt_data["applications"]) == 2
        
        # Step 7: Continue through remaining phases
        await self._complete_remaining_phases(test_client_with_auth, flow_id)
        
        # Step 8: Verify final assessment results
        final_response = await test_client_with_auth.get(
            f"/api/v1/assessment-flow/{flow_id}/report"
        )
        
        assert final_response.status_code == 200
        final_data = final_response.json()
        assert final_data["total_apps_assessed"] == 2
        assert final_data["apps_ready_for_planning"] > 0
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_assessment_flow_with_real_crewai_agents(
        self,
        test_client_with_auth: AsyncClient,
        sample_discovery_data
    ):
        """Test assessment flow with actual CrewAI agent execution"""
        
        # This test runs with real agents (not mocked)
        # Requires proper DeepInfra API keys and agent configuration
        
        # Initialize flow
        init_response = await test_client_with_auth.post(
            "/api/v1/assessment-flow/initialize",
            json={
                "selected_application_ids": ["app-1"]
            },
            headers={
                "X-Client-Account-ID": "1",
                "X-Engagement-ID": "1"
            }
        )
        
        flow_id = init_response.json()["flow_id"]
        
        # Provide minimal architecture standards to trigger tech debt analysis
        await test_client_with_auth.put(
            f"/api/v1/assessment-flow/{flow_id}/architecture-minimums",
            json={
                "engagement_standards": [
                    {
                        "requirement_type": "java_versions",
                        "description": "Java 11+ required",
                        "mandatory": True,
                        "supported_versions": {"java": "11+"}
                    }
                ]
            }
        )
        
        # Resume to trigger real agent execution
        await test_client_with_auth.post(
            f"/api/v1/assessment-flow/{flow_id}/resume",
            json={"user_input": {"approved": True}}
        )
        
        # Wait for agent execution (may take several minutes)
        await self._wait_for_phase_completion(
            test_client_with_auth, 
            flow_id, 
            "tech_debt_analysis",
            timeout_minutes=10
        )
        
        # Verify agent results
        results = await test_client_with_auth.get(
            f"/api/v1/assessment-flow/{flow_id}/tech-debt"
        )
        
        results_data = results.json()
        
        # Verify agent-generated data structure
        assert "applications" in results_data
        app_data = results_data["applications"]["app-1"]
        assert "components" in app_data
        assert "overall_score" in app_data
        
        # Verify component identification by agents
        components = app_data["components"]
        assert len(components) > 0
        
        for component in components:
            assert "component_name" in component
            assert "component_type" in component
            assert "tech_debt_score" in component
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_multi_tenant_flow_isolation(
        self,
        test_client_with_auth: AsyncClient
    ):
        """Test that flows maintain proper multi-tenant isolation"""
        
        # Create flows for different client accounts
        flow_1_response = await test_client_with_auth.post(
            "/api/v1/assessment-flow/initialize",
            json={"selected_application_ids": ["app-1"]},
            headers={
                "X-Client-Account-ID": "1",
                "X-Engagement-ID": "1"
            }
        )
        
        flow_2_response = await test_client_with_auth.post(
            "/api/v1/assessment-flow/initialize", 
            json={"selected_application_ids": ["app-2"]},
            headers={
                "X-Client-Account-ID": "2",
                "X-Engagement-ID": "2"
            }
        )
        
        flow_1_id = flow_1_response.json()["flow_id"]
        flow_2_id = flow_2_response.json()["flow_id"]
        
        # Try to access flow 1 with client 2 credentials (should fail)
        isolation_test_response = await test_client_with_auth.get(
            f"/api/v1/assessment-flow/{flow_1_id}/status",
            headers={
                "X-Client-Account-ID": "2",
                "X-Engagement-ID": "2"
            }
        )
        
        assert isolation_test_response.status_code == 404
        
        # Verify client 1 can still access their flow
        access_test_response = await test_client_with_auth.get(
            f"/api/v1/assessment-flow/{flow_1_id}/status",
            headers={
                "X-Client-Account-ID": "1", 
                "X-Engagement-ID": "1"
            }
        )
        
        assert access_test_response.status_code == 200
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_assessment_flow_performance_with_large_dataset(
        self,
        test_client_with_auth: AsyncClient,
        large_application_dataset
    ):
        """Test assessment flow performance with large number of applications"""
        
        # Test with 50+ applications
        large_app_ids = [f"app-{i}" for i in range(50)]
        
        start_time = asyncio.get_event_loop().time()
        
        # Initialize flow with large dataset
        init_response = await test_client_with_auth.post(
            "/api/v1/assessment-flow/initialize",
            json={"selected_application_ids": large_app_ids},
            headers={
                "X-Client-Account-ID": "1",
                "X-Engagement-ID": "1"
            }
        )
        
        assert init_response.status_code == 200
        flow_id = init_response.json()["flow_id"]
        
        # Complete architecture phase quickly
        await test_client_with_auth.put(
            f"/api/v1/assessment-flow/{flow_id}/architecture-minimums",
            json={
                "engagement_standards": [
                    {
                        "requirement_type": "java_versions",
                        "description": "Java 11+",
                        "mandatory": True
                    }
                ]
            }
        )
        
        # Resume and measure tech debt analysis performance
        await test_client_with_auth.post(
            f"/api/v1/assessment-flow/{flow_id}/resume",
            json={"user_input": {"approved": True}}
        )
        
        # Wait for completion with extended timeout
        await self._wait_for_phase_completion(
            test_client_with_auth,
            flow_id, 
            "tech_debt_analysis",
            timeout_minutes=30
        )
        
        end_time = asyncio.get_event_loop().time()
        execution_time = end_time - start_time
        
        # Performance assertions (adjust based on expected performance)
        assert execution_time < 1800  # Should complete within 30 minutes
        
        # Verify all applications were processed
        results = await test_client_with_auth.get(
            f"/api/v1/assessment-flow/{flow_id}/tech-debt"
        )
        
        results_data = results.json()
        assert len(results_data["applications"]) == 50
    
    async def _wait_for_phase_completion(
        self,
        client: AsyncClient,
        flow_id: str,
        expected_phase: str,
        timeout_minutes: int = 5
    ):
        """Helper to wait for phase completion with timeout"""
        
        timeout_seconds = timeout_minutes * 60
        start_time = asyncio.get_event_loop().time()
        
        while True:
            status_response = await client.get(f"/api/v1/assessment-flow/{flow_id}/status")
            status_data = status_response.json()
            
            if (status_data["status"] == "paused_for_user_input" and 
                expected_phase in status_data["pause_points"]):
                break
            
            if asyncio.get_event_loop().time() - start_time > timeout_seconds:
                raise TimeoutError(f"Phase {expected_phase} did not complete within {timeout_minutes} minutes")
            
            await asyncio.sleep(2)
    
    async def _complete_remaining_phases(self, client: AsyncClient, flow_id: str):
        """Helper to complete remaining assessment phases"""
        
        # Complete 6R strategy phase
        await client.post(
            f"/api/v1/assessment-flow/{flow_id}/resume",
            json={"user_input": {"tech_debt_approved": True}}
        )
        
        await self._wait_for_phase_completion(client, flow_id, "component_sixr_strategies")
        
        # Complete app-on-page phase
        await client.post(
            f"/api/v1/assessment-flow/{flow_id}/resume", 
            json={"user_input": {"strategies_approved": True}}
        )
        
        await self._wait_for_phase_completion(client, flow_id, "app_on_page_generation")
        
        # Complete finalization
        await client.post(
            f"/api/v1/assessment-flow/{flow_id}/finalize",
            json={"approved_for_planning": True}
        )
```

**Performance Test Configuration**:
```python
# backend/tests/performance/test_assessment_performance.py

import pytest
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

class TestAssessmentFlowPerformance:
    """Performance tests for assessment flow scalability"""
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_flow_execution(self):
        """Test multiple concurrent assessment flows"""
        
        async def run_flow(flow_index: int):
            # Implementation for running individual flow
            pass
        
        # Run 5 concurrent flows
        start_time = time.time()
        
        tasks = [run_flow(i) for i in range(5)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        
        # Verify all flows completed successfully
        for result in results:
            assert not isinstance(result, Exception)
        
        # Performance assertion (adjust based on requirements)
        assert end_time - start_time < 1200  # All flows within 20 minutes
    
    @pytest.mark.performance
    async def test_memory_usage_during_large_flow(self):
        """Test memory usage with large application datasets"""
        
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Run assessment with 100 applications
        large_app_ids = [f"app-{i}" for i in range(100)]
        
        # Execute flow (implementation)
        # ...
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory usage should not exceed reasonable limits
        assert memory_increase < 500  # Less than 500MB increase
```

**Acceptance Criteria**:
- [ ] Complete end-to-end flow execution testing
- [ ] Real CrewAI agent integration validation
- [ ] Multi-tenant isolation verification
- [ ] Performance testing with large datasets
- [ ] Database state validation throughout flow
- [ ] API endpoint integration validation
- [ ] Concurrent flow execution testing
- [ ] Memory usage and performance benchmarking

---

### TEST-003: Create Frontend Component Tests
**Status**: 🔴 Not Started  
**Priority**: P2 - Medium  
**Effort**: 10 hours  
**Dependencies**: Frontend Core (FE-001, FE-002)  
**Sprint**: Testing Week 9-10  

**Description**: Implement React component tests for assessment flow frontend with React Testing Library

**Location**: `src/__tests__/assessment/`

**Technical Requirements**:
- React Testing Library for component testing
- MSW (Mock Service Worker) for API mocking
- User interaction testing and accessibility validation
- State management testing with custom hooks
- Real-time update simulation and testing
- Responsive design testing

**Frontend Test Implementation**:
```typescript
// src/__tests__/assessment/useAssessmentFlow.test.tsx

import { renderHook, act, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useAssessmentFlow } from '@/hooks/useAssessmentFlow';
import { server } from '../mocks/server';
import { rest } from 'msw';

// Mock data
const mockFlowStatus = {
  flow_id: "test-flow-123",
  status: "paused_for_user_input",
  progress: 20,
  current_phase: "architecture_minimums",
  next_phase: "tech_debt_analysis",
  pause_points: ["architecture_minimums"],
  user_inputs_captured: false
};

describe('useAssessmentFlow', () => {
  let queryClient: QueryClient;
  
  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false }
      }
    });
  });
  
  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
  
  test('should initialize assessment flow successfully', async () => {
    // Mock API responses
    server.use(
      rest.post('/api/v1/assessment-flow/initialize', (req, res, ctx) => {
        return res(ctx.json({
          flow_id: "test-flow-123",
          status: "initialized",
          current_phase: "architecture_minimums",
          next_phase: "architecture_minimums"
        }));
      })
    );
    
    const { result } = renderHook(() => useAssessmentFlow(), { wrapper });
    
    await act(async () => {
      await result.current.initializeFlow(["app-1", "app-2"]);
    });
    
    expect(result.current.state.flowId).toBe("test-flow-123");
    expect(result.current.state.status).toBe("initialized");
    expect(result.current.state.selectedApplicationIds).toEqual(["app-1", "app-2"]);
  });
  
  test('should handle phase navigation correctly', async () => {
    server.use(
      rest.put('/api/v1/assessment-flow/*/navigate-to-phase/*', (req, res, ctx) => {
        return res(ctx.json({ message: "Navigation successful" }));
      })
    );
    
    const { result } = renderHook(() => useAssessmentFlow("test-flow-123"), { wrapper });
    
    await act(async () => {
      await result.current.navigateToPhase('tech_debt_analysis');
    });
    
    expect(result.current.state.currentPhase).toBe('tech_debt_analysis');
  });
  
  test('should update architecture standards', async () => {
    server.use(
      rest.put('/api/v1/assessment-flow/*/architecture-minimums', (req, res, ctx) => {
        return res(ctx.json({ message: "Standards updated" }));
      })
    );
    
    const { result } = renderHook(() => useAssessmentFlow("test-flow-123"), { wrapper });
    
    const standards = [
      {
        requirement_type: "java_versions",
        description: "Java 11+",
        mandatory: true
      }
    ];
    
    await act(async () => {
      await result.current.updateArchitectureStandards(standards, {});
    });
    
    expect(result.current.state.engagementStandards).toEqual(standards);
  });
  
  test('should handle real-time updates', async () => {
    // Mock Server-Sent Events
    const mockEventSource = {
      addEventListener: jest.fn(),
      close: jest.fn(),
      readyState: 1
    };
    
    (global as any).EventSource = jest.fn(() => mockEventSource);
    
    const { result } = renderHook(() => useAssessmentFlow("test-flow-123"), { wrapper });
    
    act(() => {
      result.current.subscribeToUpdates();
    });
    
    // Simulate real-time update
    act(() => {
      const updateHandler = mockEventSource.addEventListener.mock.calls
        .find(call => call[0] === 'message')[1];
      
      updateHandler({
        data: JSON.stringify({
          status: "processing",
          progress: 30,
          message: "Analyzing components..."
        })
      });
    });
    
    expect(result.current.state.status).toBe("processing");
    expect(result.current.state.progress).toBe(30);
    expect(result.current.state.agentUpdates).toHaveLength(1);
  });
  
  test('should handle errors gracefully', async () => {
    server.use(
      rest.post('/api/v1/assessment-flow/initialize', (req, res, ctx) => {
        return res(ctx.status(500), ctx.json({ detail: "Server error" }));
      })
    );
    
    const { result } = renderHook(() => useAssessmentFlow(), { wrapper });
    
    await act(async () => {
      try {
        await result.current.initializeFlow(["app-1"]);
      } catch (error) {
        // Expected error
      }
    });
    
    expect(result.current.state.error).toBeTruthy();
    expect(result.current.state.isLoading).toBe(false);
  });
});

// src/__tests__/assessment/AssessmentFlowLayout.test.tsx

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { useRouter } from 'next/router';
import { AssessmentFlowLayout } from '@/components/assessment/AssessmentFlowLayout';
import { useAssessmentFlow } from '@/hooks/useAssessmentFlow';

// Mock dependencies
jest.mock('next/router');
jest.mock('@/hooks/useAssessmentFlow');

const mockRouter = {
  push: jest.fn(),
  pathname: '/assessment/test-flow-123/architecture'
};

const mockAssessmentFlow = {
  state: {
    flowId: "test-flow-123",
    status: "paused_for_user_input",
    progress: 20,
    currentPhase: "architecture_minimums",
    nextPhase: "tech_debt_analysis",
    selectedApplicationIds: ["app-1", "app-2"],
    appsReadyForPlanning: [],
    error: null,
    agentUpdates: []
  },
  navigateToPhase: jest.fn(),
  canNavigateToPhase: jest.fn(),
  isPhaseComplete: jest.fn(),
  getPhaseProgress: jest.fn()
};

describe('AssessmentFlowLayout', () => {
  beforeEach(() => {
    (useRouter as jest.Mock).mockReturnValue(mockRouter);
    (useAssessmentFlow as jest.Mock).mockReturnValue(mockAssessmentFlow);
  });
  
  test('should render layout with phase navigation', () => {
    render(
      <AssessmentFlowLayout flowId="test-flow-123">
        <div>Test Content</div>
      </AssessmentFlowLayout>
    );
    
    expect(screen.getByText('Assessment Flow')).toBeInTheDocument();
    expect(screen.getByText('2 applications selected')).toBeInTheDocument();
    expect(screen.getByText('Architecture Standards')).toBeInTheDocument();
    expect(screen.getByText('Technical Debt Analysis')).toBeInTheDocument();
    expect(screen.getByText('Test Content')).toBeInTheDocument();
  });
  
  test('should show progress correctly', () => {
    render(
      <AssessmentFlowLayout flowId="test-flow-123">
        <div>Content</div>
      </AssessmentFlowLayout>
    );
    
    expect(screen.getByText('20%')).toBeInTheDocument();
    
    // Progress bar should be visible
    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toBeInTheDocument();
  });
  
  test('should handle phase navigation', async () => {
    mockAssessmentFlow.canNavigateToPhase.mockReturnValue(true);
    
    render(
      <AssessmentFlowLayout flowId="test-flow-123">
        <div>Content</div>
      </AssessmentFlowLayout>
    );
    
    const techDebtPhase = screen.getByText('Technical Debt Analysis');
    fireEvent.click(techDebtPhase);
    
    await waitFor(() => {
      expect(mockAssessmentFlow.navigateToPhase).toHaveBeenCalledWith('tech_debt_analysis');
      expect(mockRouter.push).toHaveBeenCalledWith('/assessment/test-flow-123/tech-debt');
    });
  });
  
  test('should disable navigation for unavailable phases', () => {
    mockAssessmentFlow.canNavigateToPhase.mockImplementation((phase) => 
      phase === 'architecture_minimums'
    );
    
    render(
      <AssessmentFlowLayout flowId="test-flow-123">
        <div>Content</div>
      </AssessmentFlowLayout>
    );
    
    const sixRPhase = screen.getByText('6R Strategy Review');
    expect(sixRPhase.closest('button')).toBeDisabled();
  });
  
  test('should show error state', () => {
    const errorState = {
      ...mockAssessmentFlow,
      state: {
        ...mockAssessmentFlow.state,
        error: "Something went wrong"
      }
    };
    
    (useAssessmentFlow as jest.Mock).mockReturnValue(errorState);
    
    render(
      <AssessmentFlowLayout flowId="test-flow-123">
        <div>Content</div>
      </AssessmentFlowLayout>
    );
    
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
  });
  
  test('should show real-time agent updates', () => {
    const updatesState = {
      ...mockAssessmentFlow,
      state: {
        ...mockAssessmentFlow.state,
        status: "processing",
        agentUpdates: [
          {
            timestamp: new Date(),
            phase: "tech_debt_analysis",
            message: "Analyzing Java components..."
          }
        ]
      }
    };
    
    (useAssessmentFlow as jest.Mock).mockReturnValue(updatesState);
    
    render(
      <AssessmentFlowLayout flowId="test-flow-123">
        <div>Content</div>
      </AssessmentFlowLayout>
    );
    
    expect(screen.getByText('AI Agents Working...')).toBeInTheDocument();
    expect(screen.getByText('Analyzing Java components...')).toBeInTheDocument();
  });
  
  test('should be accessible', async () => {
    const { container } = render(
      <AssessmentFlowLayout flowId="test-flow-123">
        <div>Content</div>
      </AssessmentFlowLayout>
    );
    
    // Check for accessibility
    const navigation = screen.getByRole('navigation');
    expect(navigation).toBeInTheDocument();
    
    const buttons = screen.getAllByRole('button');
    buttons.forEach(button => {
      expect(button).toHaveAttribute('aria-label');
    });
  });
});
```

**Mock Service Worker Configuration**:
```typescript
// src/__tests__/mocks/handlers.ts

import { rest } from 'msw';

export const handlers = [
  // Assessment Flow API handlers
  rest.post('/api/v1/assessment-flow/initialize', (req, res, ctx) => {
    return res(
      ctx.json({
        flow_id: "mock-flow-123",
        status: "initialized",
        current_phase: "architecture_minimums",
        next_phase: "architecture_minimums"
      })
    );
  }),
  
  rest.get('/api/v1/assessment-flow/:flowId/status', (req, res, ctx) => {
    return res(
      ctx.json({
        flow_id: req.params.flowId,
        status: "paused_for_user_input",
        progress: 20,
        current_phase: "architecture_minimums",
        next_phase: "tech_debt_analysis",
        pause_points: ["architecture_minimums"]
      })
    );
  }),
  
  rest.put('/api/v1/assessment-flow/:flowId/architecture-minimums', (req, res, ctx) => {
    return res(
      ctx.json({
        message: "Architecture standards updated successfully"
      })
    );
  }),
  
  rest.post('/api/v1/assessment-flow/:flowId/resume', (req, res, ctx) => {
    return res(
      ctx.json({
        flow_id: req.params.flowId,
        status: "processing",
        current_phase: "tech_debt_analysis"
      })
    );
  })
];

// src/__tests__/mocks/server.ts
import { setupServer } from 'msw/node';
import { handlers } from './handlers';

export const server = setupServer(...handlers);
```

**Acceptance Criteria**:
- [ ] Complete React component test coverage
- [ ] Custom hook testing with state management
- [ ] API integration testing with MSW
- [ ] User interaction and accessibility testing
- [ ] Real-time update simulation
- [ ] Error state handling validation
- [ ] Responsive design testing
- [ ] Navigation and routing testing

---

## 🚀 DevOps and Deployment Tasks

### DEVOPS-001: Create Assessment Flow Docker Configuration
**Status**: 🔴 Not Started  
**Priority**: P1 - High  
**Effort**: 8 hours  
**Dependencies**: Backend Core (BE-001)  
**Sprint**: Testing Week 9-10  

**Description**: Update Docker configuration to support assessment flow development and deployment

**Location**: `docker-compose.yml`, `backend/Dockerfile`

**Technical Requirements**:
- Assessment flow environment variables
- Database migration support for assessment tables
- CrewAI agent configuration and API keys
- Development and production Docker configurations
- Health checks and monitoring integration

**Docker Configuration Updates**:
```yaml
# docker-compose.yml additions

services:
  backend:
    environment:
      # Existing environment variables...
      
      # Assessment Flow Configuration
      - ASSESSMENT_FLOW_ENABLED=true
      - ASSESSMENT_CREW_PARALLELISM=3
      - ASSESSMENT_TIMEOUT_MINUTES=30
      
      # CrewAI Configuration for Assessment
      - CREWAI_ASSESSMENT_AGENTS_ENABLED=true
      - DEEPINFRA_ASSESSMENT_MODEL=meta-llama/Meta-Llama-3.1-70B-Instruct
      
      # Real-time Updates
      - SSE_ENABLED=true
      - SSE_HEARTBEAT_INTERVAL=30
      
      # Performance Configuration
      - ASSESSMENT_MAX_CONCURRENT_FLOWS=5
      - ASSESSMENT_COMPONENT_BATCH_SIZE=10
    
    healthcheck:
      test: ["CMD", "python", "-c", "
        import requests;
        r = requests.get('http://localhost:8000/health');
        assert r.status_code == 200;
        assert 'assessment_flow' in r.json()['services']
        "]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Assessment Flow specific worker (optional for heavy workloads)
  assessment-worker:
    build: ./backend
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - DEEPINFRA_API_KEY=${DEEPINFRA_API_KEY}
      - WORKER_TYPE=assessment_flow
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    command: ["python", "-m", "app.workers.assessment_worker"]
    
  # Redis for task queuing (if using background workers)
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

volumes:
  redis_data:
```

**Development Docker Compose**:
```yaml
# docker-compose.dev.yml

version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.dev
    volumes:
      - ./backend:/app
      - /app/__pycache__
    environment:
      - DEBUG=true
      - ASSESSMENT_FLOW_DEBUG=true
      - CREWAI_LOG_LEVEL=DEBUG
    ports:
      - "8000:8000"
    command: ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--reload", "--log-level", "debug"]

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    volumes:
      - ./frontend:/app
      - /app/node_modules
      - /app/.next
    environment:
      - NODE_ENV=development
      - NEXT_PUBLIC_API_URL=http://localhost:8000
      - NEXT_PUBLIC_ASSESSMENT_SSE_URL=http://localhost:8000
    ports:
      - "3000:3000"
    command: ["npm", "run", "dev"]
```

**Health Check Implementation**:
```python
# backend/app/api/v1/health.py - Update existing health check

@router.get("/health")
async def health_check():
    """Enhanced health check including assessment flow services"""
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "database": "healthy",
            "assessment_flow": "healthy",
            "crewai_agents": "healthy",
            "sse_events": "healthy"
        },
        "version": get_app_version()
    }
    
    try:
        # Check database connection
        await check_database_health()
        
        # Check assessment flow tables
        await check_assessment_tables_health()
        
        # Check CrewAI service availability
        await check_crewai_health()
        
        # Check SSE service
        await check_sse_health()
        
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["error"] = str(e)
        health_status["services"]["assessment_flow"] = "unhealthy"
    
    status_code = 200 if health_status["status"] == "healthy" else 503
    return Response(
        content=json.dumps(health_status),
        status_code=status_code,
        media_type="application/json"
    )

async def check_assessment_tables_health():
    """Check that assessment flow tables are accessible"""
    async with AsyncSessionLocal() as db:
        try:
            await db.execute(text("SELECT 1 FROM assessment_flows LIMIT 1"))
            await db.execute(text("SELECT 1 FROM engagement_architecture_standards LIMIT 1"))
        except Exception as e:
            raise HealthCheckError(f"Assessment tables unhealthy: {str(e)}")

async def check_crewai_health():
    """Check CrewAI service availability"""
    try:
        from app.services.crewai_service import get_crewai_service
        service = get_crewai_service()
        # Lightweight health check - verify configuration
        if not service.is_configured():
            raise HealthCheckError("CrewAI service not properly configured")
    except Exception as e:
        raise HealthCheckError(f"CrewAI service unhealthy: {str(e)}")
```

**Acceptance Criteria**:
- [ ] Updated Docker configuration for assessment flow
- [ ] Environment variable management for development/production
- [ ] Health checks including assessment services
- [ ] Development Docker setup with hot reloading
- [ ] Production-ready configuration with performance optimization
- [ ] Redis integration for background task processing
- [ ] Monitoring and logging configuration

---

### DEVOPS-002: Create Assessment Flow Monitoring and Observability
**Status**: 🔴 Not Started  
**Priority**: P2 - Medium  
**Effort**: 10 hours  
**Dependencies**: DEVOPS-001  
**Sprint**: Testing Week 10  

**Description**: Implement monitoring, logging, and observability for assessment flow operations

**Location**: `backend/app/monitoring/`, `monitoring/`

**Technical Requirements**:
- Assessment flow metrics and performance tracking
- CrewAI agent execution monitoring
- Real-time dashboards for flow progress
- Error tracking and alerting
- Cost monitoring for LLM usage
- Database performance monitoring

**Monitoring Implementation**:
```python
# backend/app/monitoring/assessment_metrics.py

from prometheus_client import Counter, Histogram, Gauge
import time
from functools import wraps

# Assessment Flow Metrics
ASSESSMENT_FLOWS_TOTAL = Counter(
    'assessment_flows_total',
    'Total number of assessment flows initiated',
    ['client_account_id', 'engagement_id']
)

ASSESSMENT_FLOWS_COMPLETED = Counter(
    'assessment_flows_completed_total',
    'Total number of assessment flows completed',
    ['client_account_id', 'status']
)

ASSESSMENT_PHASE_DURATION = Histogram(
    'assessment_phase_duration_seconds',
    'Time spent in each assessment phase',
    ['phase', 'client_account_id'],
    buckets=[10, 30, 60, 300, 600, 1800, 3600]  # 10s to 1hr
)

ASSESSMENT_APPLICATIONS_PROCESSED = Counter(
    'assessment_applications_processed_total',
    'Total number of applications processed',
    ['client_account_id', 'phase']
)

CREWAI_AGENT_EXECUTIONS = Counter(
    'crewai_agent_executions_total',
    'Total CrewAI agent executions',
    ['agent_type', 'status', 'client_account_id']
)

CREWAI_AGENT_DURATION = Histogram(
    'crewai_agent_duration_seconds',
    'CrewAI agent execution duration',
    ['agent_type', 'client_account_id'],
    buckets=[1, 5, 10, 30, 60, 300, 600]  # 1s to 10min
)

ASSESSMENT_FLOW_ERRORS = Counter(
    'assessment_flow_errors_total',
    'Total assessment flow errors',
    ['error_type', 'phase', 'client_account_id']
)

ACTIVE_ASSESSMENT_FLOWS = Gauge(
    'active_assessment_flows',
    'Number of currently active assessment flows',
    ['status', 'client_account_id']
)

LLM_TOKEN_USAGE = Counter(
    'llm_token_usage_total',
    'Total LLM tokens consumed',
    ['model', 'operation_type', 'client_account_id']
)

def track_assessment_phase(phase: str, client_account_id: int):
    """Decorator to track assessment phase metrics"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                ASSESSMENT_PHASE_DURATION.labels(
                    phase=phase,
                    client_account_id=client_account_id
                ).observe(duration)
                
                return result
                
            except Exception as e:
                ASSESSMENT_FLOW_ERRORS.labels(
                    error_type=type(e).__name__,
                    phase=phase,
                    client_account_id=client_account_id
                ).inc()
                raise
        
        return wrapper
    return decorator

def track_crewai_execution(agent_type: str, client_account_id: int):
    """Decorator to track CrewAI agent execution metrics"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                CREWAI_AGENT_EXECUTIONS.labels(
                    agent_type=agent_type,
                    status='success',
                    client_account_id=client_account_id
                ).inc()
                
                CREWAI_AGENT_DURATION.labels(
                    agent_type=agent_type,
                    client_account_id=client_account_id
                ).observe(duration)
                
                return result
                
            except Exception as e:
                CREWAI_AGENT_EXECUTIONS.labels(
                    agent_type=agent_type,
                    status='error',
                    client_account_id=client_account_id
                ).inc()
                raise
        
        return wrapper
    return decorator

class AssessmentFlowMonitor:
    """Centralized monitoring for assessment flows"""
    
    def __init__(self):
        self.active_flows = {}
    
    def flow_started(self, flow_id: str, client_account_id: int, engagement_id: int):
        """Track flow start"""
        ASSESSMENT_FLOWS_TOTAL.labels(
            client_account_id=client_account_id,
            engagement_id=engagement_id
        ).inc()
        
        ACTIVE_ASSESSMENT_FLOWS.labels(
            status='active',
            client_account_id=client_account_id
        ).inc()
        
        self.active_flows[flow_id] = {
            'start_time': time.time(),
            'client_account_id': client_account_id,
            'engagement_id': engagement_id
        }
    
    def flow_completed(self, flow_id: str, status: str):
        """Track flow completion"""
        if flow_id in self.active_flows:
            flow_info = self.active_flows[flow_id]
            
            ASSESSMENT_FLOWS_COMPLETED.labels(
                client_account_id=flow_info['client_account_id'],
                status=status
            ).inc()
            
            ACTIVE_ASSESSMENT_FLOWS.labels(
                status='active',
                client_account_id=flow_info['client_account_id']
            ).dec()
            
            del self.active_flows[flow_id]
    
    def applications_processed(self, count: int, phase: str, client_account_id: int):
        """Track applications processed in phase"""
        ASSESSMENT_APPLICATIONS_PROCESSED.labels(
            client_account_id=client_account_id,
            phase=phase
        ).inc(count)
    
    def llm_usage(self, model: str, tokens: int, operation: str, client_account_id: int):
        """Track LLM token usage"""
        LLM_TOKEN_USAGE.labels(
            model=model,
            operation_type=operation,
            client_account_id=client_account_id
        ).inc(tokens)

# Global monitor instance
assessment_monitor = AssessmentFlowMonitor()
```

**Grafana Dashboard Configuration**:
```json
{
  "dashboard": {
    "title": "Assessment Flow Monitoring",
    "panels": [
      {
        "title": "Active Assessment Flows",
        "type": "stat",
        "targets": [
          {
            "expr": "sum(active_assessment_flows)"
          }
        ]
      },
      {
        "title": "Assessment Flow Completion Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(assessment_flows_completed_total[5m])"
          }
        ]
      },
      {
        "title": "Average Phase Duration",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.50, assessment_phase_duration_seconds_bucket)"
          },
          {
            "expr": "histogram_quantile(0.95, assessment_phase_duration_seconds_bucket)"
          }
        ]
      },
      {
        "title": "CrewAI Agent Performance",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(crewai_agent_executions_total[5m])"
          }
        ]
      },
      {
        "title": "Error Rate by Phase",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(assessment_flow_errors_total[5m])"
          }
        ]
      },
      {
        "title": "LLM Token Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(llm_token_usage_total[5m])"
          }
        ]
      }
    ]
  }
}
```

**Acceptance Criteria**:
- [ ] Comprehensive metrics collection for assessment flows
- [ ] CrewAI agent execution monitoring
- [ ] Grafana dashboards for real-time monitoring
- [ ] Error tracking and alerting configuration
- [ ] LLM cost and usage monitoring
- [ ] Performance optimization recommendations

---

### DEVOPS-003: Create Assessment Flow Database Migration Scripts
**Status**: 🔴 Not Started  
**Priority**: P1 - High  
**Effort**: 6 hours  
**Dependencies**: Database Foundation (DB-001)  
**Sprint**: Testing Week 10  

**Description**: Create production-ready database migration scripts with rollback capabilities

**Location**: `backend/scripts/migrations/`

**Technical Requirements**:
- Alembic migration scripts for all assessment tables
- Data migration for existing engagements
- Rollback procedures and safety checks
- Performance optimization for large datasets
- Multi-environment deployment support

**Migration Scripts**:
```python
# backend/scripts/migrations/assessment_flow_migration.py

"""Production migration script for Assessment Flow"""

import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from alembic import command
from alembic.config import Config
from app.core.database import AsyncSessionLocal
from app.core.database_initialization import initialize_assessment_standards

logger = logging.getLogger(__name__)

class AssessmentFlowMigration:
    """Manages Assessment Flow database migration"""
    
    def __init__(self):
        self.alembic_cfg = Config("alembic.ini")
    
    async def migrate_to_assessment_flow(self):
        """Complete migration to assessment flow schema"""
        
        try:
            logger.info("Starting Assessment Flow migration")
            
            # Step 1: Run Alembic migration
            await self._run_alembic_migration()
            
            # Step 2: Initialize assessment standards for existing engagements
            await self._initialize_existing_engagements()
            
            # Step 3: Verify migration integrity
            await self._verify_migration()
            
            logger.info("Assessment Flow migration completed successfully")
            
        except Exception as e:
            logger.error(f"Migration failed: {str(e)}")
            await self._rollback_migration()
            raise
    
    async def _run_alembic_migration(self):
        """Run Alembic migration for assessment tables"""
        
        try:
            command.upgrade(self.alembic_cfg, "head")
            logger.info("Alembic migration completed")
        except Exception as e:
            logger.error(f"Alembic migration failed: {str(e)}")
            raise
    
    async def _initialize_existing_engagements(self):
        """Initialize assessment standards for existing engagements"""
        
        async with AsyncSessionLocal() as db:
            try:
                # Get all active engagements
                result = await db.execute(
                    text("SELECT id, client_account_id FROM engagements WHERE status = 'active'")
                )
                engagements = result.fetchall()
                
                logger.info(f"Initializing standards for {len(engagements)} engagements")
                
                for engagement in engagements:
                    await initialize_assessment_standards(db, engagement.id)
                    logger.debug(f"Initialized standards for engagement {engagement.id}")
                
                await db.commit()
                logger.info("All engagement standards initialized")
                
            except Exception as e:
                await db.rollback()
                logger.error(f"Failed to initialize engagement standards: {str(e)}")
                raise
    
    async def _verify_migration(self):
        """Verify migration completed successfully"""
        
        async with AsyncSessionLocal() as db:
            try:
                # Check all tables exist
                required_tables = [
                    'assessment_flows',
                    'engagement_architecture_standards',
                    'application_architecture_overrides',
                    'application_components',
                    'tech_debt_analysis',
                    'component_treatments',
                    'sixr_decisions',
                    'assessment_learning_feedback'
                ]
                
                for table in required_tables:
                    result = await db.execute(
                        text(f"SELECT to_regclass('{table}')")
                    )
                    if not result.scalar():
                        raise Exception(f"Table {table} does not exist")
                
                # Check indexes exist
                required_indexes = [
                    'idx_assessment_flows_status',
                    'idx_assessment_flows_client',
                    'idx_eng_arch_standards',
                    'idx_sixr_decisions_app'
                ]
                
                for index in required_indexes:
                    result = await db.execute(
                        text(f"SELECT to_regclass('{index}')")
                    )
                    if not result.scalar():
                        logger.warning(f"Index {index} missing - may affect performance")
                
                # Verify sample data access
                await db.execute(text("SELECT 1 FROM assessment_flows LIMIT 1"))
                await db.execute(text("SELECT 1 FROM engagement_architecture_standards LIMIT 1"))
                
                logger.info("Migration verification completed successfully")
                
            except Exception as e:
                logger.error(f"Migration verification failed: {str(e)}")
                raise
    
    async def _rollback_migration(self):
        """Rollback migration if needed"""
        
        try:
            logger.warning("Starting migration rollback")
            
            # Drop assessment tables (in reverse dependency order)
            async with AsyncSessionLocal() as db:
                rollback_sql = [
                    "DROP TABLE IF EXISTS assessment_learning_feedback CASCADE",
                    "DROP TABLE IF EXISTS sixr_decisions CASCADE", 
                    "DROP TABLE IF EXISTS component_treatments CASCADE",
                    "DROP TABLE IF EXISTS tech_debt_analysis CASCADE",
                    "DROP TABLE IF EXISTS application_components CASCADE",
                    "DROP TABLE IF EXISTS application_architecture_overrides CASCADE",
                    "DROP TABLE IF EXISTS engagement_architecture_standards CASCADE",
                    "DROP TABLE IF EXISTS assessment_flows CASCADE"
                ]
                
                for sql in rollback_sql:
                    await db.execute(text(sql))
                
                await db.commit()
            
            logger.info("Migration rollback completed")
            
        except Exception as e:
            logger.error(f"Rollback failed: {str(e)}")
            raise

async def main():
    """Main migration entry point"""
    
    migration = AssessmentFlowMigration()
    await migration.migrate_to_assessment_flow()

if __name__ == "__main__":
    asyncio.run(main())
```

**Production Deployment Script**:
```bash
#!/bin/bash
# scripts/deploy_assessment_flow.sh

set -e

echo "Starting Assessment Flow deployment..."

# Environment validation
if [[ -z "$DATABASE_URL" ]]; then
    echo "ERROR: DATABASE_URL not set"
    exit 1
fi

if [[ -z "$DEEPINFRA_API_KEY" ]]; then
    echo "ERROR: DEEPINFRA_API_KEY not set"
    exit 1
fi

# Backup database
echo "Creating database backup..."
pg_dump $DATABASE_URL > "backup_$(date +%Y%m%d_%H%M%S).sql"

# Run migration
echo "Running Assessment Flow migration..."
docker exec migration_backend python scripts/migrations/assessment_flow_migration.py

# Verify deployment
echo "Verifying deployment..."
docker exec migration_backend python -c "
from app.core.database_initialization import verify_assessment_tables
import asyncio
from app.core.database import AsyncSessionLocal

async def verify():
    async with AsyncSessionLocal() as db:
        await verify_assessment_tables(db)
        print('Assessment tables verified successfully')

asyncio.run(verify())
"

# Health check
echo "Performing health check..."
curl -f http://localhost:8000/health || {
    echo "Health check failed - rolling back"
    # Implement rollback logic
    exit 1
}

echo "Assessment Flow deployment completed successfully!"
```

**Acceptance Criteria**:
- [ ] Complete Alembic migration scripts
- [ ] Data migration for existing engagements
- [ ] Migration verification and rollback procedures
- [ ] Production deployment scripts with safety checks
- [ ] Database backup and recovery procedures
- [ ] Performance optimization for large datasets

---

## Summary and Next Steps

The Assessment Flow implementation has been broken down into 5 manageable task tracker documents:

1. **Database & Foundation Tasks** (Document 01) - 5 tasks, ~56 hours
2. **Backend & CrewAI Tasks** (Document 02) - 4 tasks, ~64 hours  
3. **API & Integration Tasks** (Document 03) - 7 tasks, ~60 hours
4. **Frontend & UX Tasks** (Document 04) - 7 tasks, ~108 hours
5. **Testing & DevOps Tasks** (Document 05) - 6 tasks, ~62 hours

**Total Estimated Effort**: ~350 hours across 29 detailed tasks

**Implementation Timeline**: 10 weeks with proper task parallelization

**Critical Path Dependencies**:
- Database Foundation → Backend Core → API Core → Frontend Core → Testing
- All tasks maintain multi-tenant architecture and PostgreSQL-only approach
- Real CrewAI agents implementation (not pseudo-agents)
- Integration with existing platform remediation efforts

**Key Success Factors**:
- Following Docker-first development approach
- Maintaining compatibility with current v1 API reality
- Implementing comprehensive testing at each layer
- Ensuring proper multi-tenant data isolation
- Building robust error handling and recovery mechanisms

<function_calls>
<invoke name="TodoWrite">
<parameter name="todos">[{"id": "1", "content": "Create Database & Foundation Task Tracker", "status": "completed", "priority": "high"}, {"id": "2", "content": "Create Backend & CrewAI Task Tracker", "status": "completed", "priority": "high"}, {"id": "3", "content": "Create API & Integration Task Tracker", "status": "completed", "priority": "high"}, {"id": "4", "content": "Create Frontend & UX Task Tracker", "status": "completed", "priority": "high"}, {"id": "5", "content": "Create Testing & DevOps Task Tracker", "status": "completed", "priority": "high"}]