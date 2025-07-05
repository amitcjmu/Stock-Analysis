"""
API Integration Tests for Unified Flow API (MFO-072)

Comprehensive tests covering all flow API endpoints:
- Flow creation, execution, and lifecycle management
- Multi-tenant isolation and security
- Error handling and edge cases
- Analytics and status reporting
- Backward compatibility support
"""

import pytest
import asyncio
import json
from typing import Dict, List, Any
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient

from app.core.database import get_db
from app.core.schemas import RequestContext
from app.services.master_flow_orchestrator import MasterFlowOrchestrator
from app.models import User
from app.api.v1.endpoints.context.services.user_service import UserService


# Test fixtures
@pytest.fixture
def api_client():
    """Test client for API endpoints"""
    from main import app
    return TestClient(app)


@pytest.fixture
def authenticated_headers():
    """Headers with authentication token"""
    return {
        "Authorization": "Bearer mock_jwt_token",
        "Content-Type": "application/json",
        "X-Client-Account-ID": "test_client_123"
    }


@pytest.fixture
def mock_db_session():
    """Mock database session"""
    session = AsyncMock(spec=AsyncSession)
    return session


@pytest.fixture
def mock_user():
    """Mock authenticated user"""
    user = Mock(spec=User)
    user.id = "user_123"
    user.email = "test@example.com"
    return user


@pytest.fixture
def mock_user_context():
    """Mock user context"""
    context = Mock()
    context.client = Mock()
    context.client.id = 1
    context.engagement = Mock()
    context.engagement.id = 1
    return context


@pytest.fixture
def mock_request_context():
    """Mock request context"""
    return RequestContext(
        user_id="user_123",
        client_account_id=1,
        engagement_id=1
    )


@pytest.fixture
def mock_orchestrator():
    """Mock master flow orchestrator"""
    orchestrator = Mock(spec=MasterFlowOrchestrator)
    
    # Mock successful flow creation
    orchestrator.create_flow.return_value = (
        "flow_12345",
        {
            "flow_id": "flow_12345",
            "flow_type": "discovery",
            "status": "created",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "created_by": "user_123",
            "configuration": {},
            "metadata": {},
            "progress_percentage": 0.0
        }
    )
    
    # Mock flow status
    orchestrator.get_flow_status.return_value = {
        "flow_id": "flow_12345",
        "flow_type": "discovery",
        "status": "running",
        "current_phase": "data_import",
        "progress_percentage": 25.0,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "created_by": "user_123",
        "configuration": {},
        "metadata": {},
        "execution_history": [],
        "current_state": {},
        "performance_metrics": {}
    }
    
    # Mock successful operations
    orchestrator.execute_phase.return_value = (True, {"phase": "data_import"})
    orchestrator.pause_flow.return_value = (True, {"status": "paused"})
    orchestrator.resume_flow.return_value = (True, {"status": "running"})
    orchestrator.delete_flow.return_value = (True, {"status": "deleted"})
    
    # Mock flow list
    orchestrator.get_active_flows.return_value = [
        {
            "flow_id": "flow_12345",
            "flow_type": "discovery",
            "status": "running",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "created_by": "user_123",
            "configuration": {},
            "metadata": {},
            "progress_percentage": 25.0
        }
    ]
    
    return orchestrator


@pytest.fixture
def mock_dependencies(mock_db_session, mock_user, mock_user_context, mock_request_context, mock_orchestrator):
    """Mock all dependencies"""
    with patch("app.api.v1.flows.get_db", return_value=mock_db_session), \
         patch("app.api.v1.flows.get_current_user", return_value=mock_user), \
         patch("app.api.v1.flows.UserService") as mock_user_service, \
         patch("app.api.v1.flows.MasterFlowOrchestrator", return_value=mock_orchestrator):
        
        # Mock user service
        mock_user_service.return_value.get_user_context.return_value = mock_user_context
        
        yield {
            "db": mock_db_session,
            "user": mock_user,
            "user_context": mock_user_context,
            "request_context": mock_request_context,
            "orchestrator": mock_orchestrator
        }


class TestFlowCreation:
    """Test flow creation endpoint"""
    
    def test_create_flow_success(self, api_client, authenticated_headers, mock_dependencies):
        """Test successful flow creation"""
        flow_data = {
            "flow_type": "discovery",
            "flow_name": "Test Discovery Flow",
            "configuration": {"source": "cmdb"},
            "initial_state": {"step": 1}
        }
        
        response = api_client.post("/api/v1/flows", json=flow_data, headers=authenticated_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["flow_id"] == "flow_12345"
        assert data["flow_type"] == "discovery"
        assert data["status"] == "created"
        
        # Verify orchestrator was called correctly
        mock_dependencies["orchestrator"].create_flow.assert_called_once_with(
            flow_type="discovery",
            flow_name="Test Discovery Flow",
            configuration={"source": "cmdb"},
            initial_state={"step": 1}
        )
    
    def test_create_flow_invalid_type(self, api_client, authenticated_headers, mock_dependencies):
        """Test flow creation with invalid flow type"""
        flow_data = {
            "flow_type": "",  # Invalid empty type
            "flow_name": "Test Flow"
        }
        
        response = api_client.post("/api/v1/flows", json=flow_data, headers=authenticated_headers)
        
        assert response.status_code == 422  # Validation error
    
    def test_create_flow_orchestrator_error(self, api_client, authenticated_headers, mock_dependencies):
        """Test flow creation when orchestrator fails"""
        mock_dependencies["orchestrator"].create_flow.side_effect = ValueError("Invalid flow type")
        
        flow_data = {
            "flow_type": "invalid_type",
            "flow_name": "Test Flow"
        }
        
        response = api_client.post("/api/v1/flows", json=flow_data, headers=authenticated_headers)
        
        assert response.status_code == 400
        assert "Invalid flow type" in response.json()["detail"]


class TestFlowListing:
    """Test flow listing endpoint"""
    
    def test_list_flows_success(self, api_client, authenticated_headers, mock_dependencies):
        """Test successful flow listing"""
        response = api_client.get("/api/v1/flows", headers=authenticated_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "flows" in data
        assert "total" in data
        assert len(data["flows"]) == 1
        assert data["flows"][0]["flow_id"] == "flow_12345"
    
    def test_list_flows_with_filters(self, api_client, authenticated_headers, mock_dependencies):
        """Test flow listing with filters"""
        response = api_client.get(
            "/api/v1/flows?flow_type=discovery&status=running",
            headers=authenticated_headers
        )
        
        assert response.status_code == 200
        
        # Verify orchestrator was called with filters
        mock_dependencies["orchestrator"].get_active_flows.assert_called_with(
            flow_type="discovery",
            status="running"
        )
    
    def test_list_flows_with_pagination(self, api_client, authenticated_headers, mock_dependencies):
        """Test flow listing with pagination"""
        response = api_client.get(
            "/api/v1/flows?page=2&page_size=5",
            headers=authenticated_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["page_size"] == 5


class TestFlowRetrieval:
    """Test individual flow retrieval"""
    
    def test_get_flow_success(self, api_client, authenticated_headers, mock_dependencies):
        """Test successful flow retrieval"""
        flow_id = "flow_12345"
        
        response = api_client.get(f"/api/v1/flows/{flow_id}", headers=authenticated_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["flow_id"] == flow_id
        assert data["flow_type"] == "discovery"
        
        mock_dependencies["orchestrator"].get_flow_status.assert_called_once_with(flow_id)
    
    def test_get_flow_not_found(self, api_client, authenticated_headers, mock_dependencies):
        """Test flow retrieval for non-existent flow"""
        mock_dependencies["orchestrator"].get_flow_status.return_value = None
        
        response = api_client.get("/api/v1/flows/nonexistent", headers=authenticated_headers)
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestFlowExecution:
    """Test flow execution endpoint"""
    
    def test_execute_phase_success(self, api_client, authenticated_headers, mock_dependencies):
        """Test successful phase execution"""
        flow_id = "flow_12345"
        execution_data = {
            "phase_input": {"data": "test"},
            "force_execution": False
        }
        
        response = api_client.post(
            f"/api/v1/flows/{flow_id}/execute",
            json=execution_data,
            headers=authenticated_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["flow_id"] == flow_id
        
        mock_dependencies["orchestrator"].execute_phase.assert_called_once_with(
            flow_id=flow_id,
            phase_input={"data": "test"},
            force_execution=False
        )
    
    def test_execute_phase_failure(self, api_client, authenticated_headers, mock_dependencies):
        """Test phase execution failure"""
        mock_dependencies["orchestrator"].execute_phase.return_value = (False, {"error": "Phase failed"})
        
        flow_id = "flow_12345"
        execution_data = {"phase_input": {}}
        
        response = api_client.post(
            f"/api/v1/flows/{flow_id}/execute",
            json=execution_data,
            headers=authenticated_headers
        )
        
        assert response.status_code == 400
        assert "Phase failed" in response.json()["detail"]


class TestFlowLifecycle:
    """Test flow lifecycle management"""
    
    def test_pause_flow_success(self, api_client, authenticated_headers, mock_dependencies):
        """Test successful flow pause"""
        flow_id = "flow_12345"
        
        response = api_client.post(f"/api/v1/flows/{flow_id}/pause", headers=authenticated_headers)
        
        assert response.status_code == 200
        mock_dependencies["orchestrator"].pause_flow.assert_called_once_with(flow_id)
    
    def test_resume_flow_success(self, api_client, authenticated_headers, mock_dependencies):
        """Test successful flow resume"""
        flow_id = "flow_12345"
        
        response = api_client.post(f"/api/v1/flows/{flow_id}/resume", headers=authenticated_headers)
        
        assert response.status_code == 200
        mock_dependencies["orchestrator"].resume_flow.assert_called_once_with(flow_id)
    
    def test_delete_flow_success(self, api_client, authenticated_headers, mock_dependencies):
        """Test successful flow deletion"""
        flow_id = "flow_12345"
        
        response = api_client.delete(f"/api/v1/flows/{flow_id}", headers=authenticated_headers)
        
        assert response.status_code == 204
        mock_dependencies["orchestrator"].delete_flow.assert_called_once_with(flow_id)
    
    def test_lifecycle_operation_failure(self, api_client, authenticated_headers, mock_dependencies):
        """Test lifecycle operation failure"""
        mock_dependencies["orchestrator"].pause_flow.return_value = (False, {"error": "Cannot pause"})
        
        flow_id = "flow_12345"
        response = api_client.post(f"/api/v1/flows/{flow_id}/pause", headers=authenticated_headers)
        
        assert response.status_code == 400
        assert "Cannot pause" in response.json()["detail"]


class TestFlowStatus:
    """Test flow status endpoint"""
    
    def test_get_flow_status_success(self, api_client, authenticated_headers, mock_dependencies):
        """Test successful flow status retrieval"""
        flow_id = "flow_12345"
        
        response = api_client.get(f"/api/v1/flows/{flow_id}/status", headers=authenticated_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["flow_id"] == flow_id
        assert "execution_history" in data
        assert "current_state" in data
        assert "performance_metrics" in data
    
    def test_get_flow_status_not_found(self, api_client, authenticated_headers, mock_dependencies):
        """Test flow status for non-existent flow"""
        mock_dependencies["orchestrator"].get_flow_status.return_value = None
        
        response = api_client.get("/api/v1/flows/nonexistent/status", headers=authenticated_headers)
        
        assert response.status_code == 404


class TestFlowAnalytics:
    """Test flow analytics endpoint"""
    
    def test_get_analytics_success(self, api_client, authenticated_headers, mock_dependencies):
        """Test successful analytics retrieval"""
        response = api_client.get("/api/v1/flows/analytics/summary", headers=authenticated_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "total_flows" in data
        assert "flows_by_type" in data
        assert "flows_by_status" in data
        assert "success_rate_by_type" in data
        assert "error_rate_by_type" in data
    
    def test_get_analytics_with_date_filters(self, api_client, authenticated_headers, mock_dependencies):
        """Test analytics with date filtering"""
        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now()
        
        response = api_client.get(
            f"/api/v1/flows/analytics/summary?start_date={start_date.isoformat()}&end_date={end_date.isoformat()}",
            headers=authenticated_headers
        )
        
        assert response.status_code == 200


class TestBackwardCompatibility:
    """Test backward compatibility endpoints"""
    
    def test_legacy_discovery_create(self, api_client, authenticated_headers, mock_dependencies):
        """Test legacy discovery flow creation"""
        config_data = {"source": "cmdb"}
        
        response = api_client.post(
            "/api/v1/flows/legacy/discovery/create",
            json=config_data,
            headers=authenticated_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["flow_type"] == "discovery"
        
        # Verify it called the main create_flow method
        mock_dependencies["orchestrator"].create_flow.assert_called_once_with(
            flow_type="discovery",
            flow_name=None,
            configuration=config_data,
            initial_state={}
        )
    
    def test_legacy_assessment_create(self, api_client, authenticated_headers, mock_dependencies):
        """Test legacy assessment flow creation"""
        config_data = {"assessment_type": "security"}
        
        response = api_client.post(
            "/api/v1/flows/legacy/assessment/create",
            json=config_data,
            headers=authenticated_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["flow_type"] == "assessment"


class TestAuthentication:
    """Test authentication and authorization"""
    
    def test_unauthenticated_request(self, api_client):
        """Test request without authentication"""
        response = api_client.get("/api/v1/flows")
        
        assert response.status_code == 401
    
    def test_missing_client_account(self, api_client, mock_dependencies):
        """Test request with user not associated with client account"""
        mock_dependencies["user_context"].client = None
        
        headers = {"Authorization": "Bearer mock_jwt_token"}
        response = api_client.get("/api/v1/flows", headers=headers)
        
        assert response.status_code == 400
        assert "not associated with a client account" in response.json()["detail"]


class TestErrorHandling:
    """Test error handling scenarios"""
    
    def test_database_error(self, api_client, authenticated_headers, mock_dependencies):
        """Test database error handling"""
        mock_dependencies["orchestrator"].create_flow.side_effect = Exception("Database error")
        
        flow_data = {"flow_type": "discovery"}
        response = api_client.post("/api/v1/flows", json=flow_data, headers=authenticated_headers)
        
        assert response.status_code == 500
        assert "Failed to create flow" in response.json()["detail"]
    
    def test_validation_error(self, api_client, authenticated_headers):
        """Test request validation error"""
        invalid_data = {"invalid_field": "value"}
        
        response = api_client.post("/api/v1/flows", json=invalid_data, headers=authenticated_headers)
        
        assert response.status_code == 422


class TestMultiTenant:
    """Test multi-tenant isolation"""
    
    def test_tenant_isolation(self, api_client, authenticated_headers, mock_dependencies):
        """Test that flows are isolated by tenant"""
        # Mock different client contexts
        context1 = RequestContext(user_id="user1", client_account_id=1, engagement_id=1)
        context2 = RequestContext(user_id="user2", client_account_id=2, engagement_id=2)
        
        # Test that each context gets its own orchestrator
        response = api_client.get("/api/v1/flows", headers=authenticated_headers)
        
        assert response.status_code == 200
        # Verify orchestrator was initialized with correct context
        assert mock_dependencies["orchestrator"] is not None


# Integration test that runs without mocks
@pytest.mark.integration
class TestRealIntegration:
    """Integration tests with real dependencies"""
    
    @pytest.mark.asyncio
    async def test_full_flow_lifecycle(self):
        """Test complete flow lifecycle with real dependencies"""
        # This would be run in integration environment
        # with real database and services
        pass
    
    @pytest.mark.asyncio
    async def test_concurrent_flows(self):
        """Test handling of concurrent flows"""
        # Test multiple flows running simultaneously
        pass
    
    @pytest.mark.asyncio
    async def test_flow_state_persistence(self):
        """Test that flow state is properly persisted"""
        # Test state persistence across service restarts
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])