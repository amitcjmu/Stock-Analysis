"""
Discovery Flow v2 API Endpoints Testing
Tests the new v2 API architecture with CrewAI Flow ID as single source of truth.
"""

import pytest
from fastapi.testclient import TestClient

# API testing fixtures
@pytest.fixture
def api_client():
    """Test client for API endpoints"""
    from backend.main import app
    return TestClient(app)

@pytest.fixture
def authenticated_headers():
    """Headers with multi-tenant context"""
    return {
        "Content-Type": "application/json",
        "X-Client-Account-Id": "11111111-1111-1111-1111-111111111111",
        "X-Engagement-Id": "22222222-2222-2222-2222-222222222222"
    }

@pytest.fixture
def mock_discovery_data():
    """Mock data for Discovery Flow v2 testing"""
    return {
        "flow_id": "test-flow-v2-001",
        "raw_data": [
            {
                "asset_name": "web-server-01",
                "hostname": "web-server-01",
                "ip_address": "192.168.1.10",
                "os_type": "Linux",
                "application": "Web Application",
                "environment": "Production"
            },
            {
                "asset_name": "db-server-01",
                "hostname": "db-server-01", 
                "ip_address": "192.168.1.20",
                "os_type": "Windows",
                "application": "Database Server",
                "environment": "Production"
            }
        ],
        "metadata": {
            "source": "api_test",
            "import_type": "cmdb",
            "total_assets": 2
        }
    }

@pytest.fixture
def mock_phase_data():
    """Mock phase completion data"""
    return {
        "phase": "inventory",
        "phase_data": {
            "assets": [
                {
                    "asset_name": "web-server-01",
                    "asset_type": "server",
                    "confidence": 0.95
                }
            ],
            "total_discovered": 1,
            "quality_score": 0.9
        },
        "crew_status": {
            "crew_id": "asset_intelligence_crew",
            "status": "completed",
            "execution_time": 45.2
        },
        "agent_insights": [
            {
                "agent": "Asset Intelligence Agent",
                "insight": "High confidence asset classification",
                "confidence": 0.95
            }
        ]
    }

class TestDiscoveryFlowV2Endpoints:
    """Test suite for Discovery Flow v2 API endpoints"""
    
    def test_health_endpoint(self, api_client):
        """Test v2 health endpoint (no context required)"""
        # Act
        response = api_client.get("/api/v2/discovery-flows/health")
        
        # Assert
        assert response.status_code == 200, "Health endpoint should be accessible"
        
        response_data = response.json()
        assert response_data["status"] == "healthy"
        assert response_data["service"] == "discovery-flows-v2"
        assert response_data["api_version"] == "v2"
        assert "features" in response_data
        assert "crewai_flow_id_as_single_source_of_truth" in response_data["features"]
        
    def test_create_discovery_flow(
        self,
        api_client,
        authenticated_headers,
        mock_discovery_data
    ):
        """Test creating a new discovery flow with CrewAI Flow ID"""
        # Act
        response = api_client.post(
            "/api/v2/discovery-flows/flows",
            headers=authenticated_headers,
            json=mock_discovery_data
        )
        
        # Assert
        assert response.status_code == 201, "Flow creation should succeed"
        
        response_data = response.json()
        assert response_data["flow_id"] == mock_discovery_data["flow_id"]
        assert response_data["status"] == "active"
        assert response_data["current_phase"] == "data_import"
        assert response_data["progress_percentage"] == 0.0
        assert len(response_data["raw_data"]) == 2
        
        # Verify multi-tenant context
        assert response_data["client_account_id"] == "11111111-1111-1111-1111-111111111111"
        assert response_data["engagement_id"] == "22222222-2222-2222-2222-222222222222"
        
    def test_get_discovery_flow_by_id(
        self,
        api_client,
        authenticated_headers,
        mock_discovery_data
    ):
        """Test retrieving discovery flow by CrewAI Flow ID"""
        # Arrange - Create flow first
        create_response = api_client.post(
            "/api/v2/discovery-flows/flows",
            headers=authenticated_headers,
            json=mock_discovery_data
        )
        assert create_response.status_code == 201
        
        flow_id = mock_discovery_data["flow_id"]
        
        # Act
        response = api_client.get(
            f"/api/v2/discovery-flows/flows/{flow_id}",
            headers=authenticated_headers
        )
        
        # Assert
        assert response.status_code == 200, "Flow retrieval should succeed"
        
        response_data = response.json()
        assert response_data["flow_id"] == flow_id
        assert response_data["status"] == "active"
        
    def test_get_discovery_flows_list(
        self,
        api_client,
        authenticated_headers,
        mock_discovery_data
    ):
        """Test listing discovery flows"""
        # Arrange - Create a flow first
        api_client.post(
            "/api/v2/discovery-flows/flows",
            headers=authenticated_headers,
            json=mock_discovery_data
        )
        
        # Act
        response = api_client.get(
            "/api/v2/discovery-flows/flows",
            headers=authenticated_headers
        )
        
        # Assert
        assert response.status_code == 200, "Flow listing should succeed"
        
        response_data = response.json()
        assert isinstance(response_data, list), "Should return a list of flows"
        assert len(response_data) > 0, "Should find at least one flow"
        
        # Verify first flow structure
        flow = response_data[0]
        assert "flow_id" in flow
        assert "status" in flow
        assert "current_phase" in flow
        assert "progress_percentage" in flow
        
    def test_update_phase_completion(
        self,
        api_client,
        authenticated_headers,
        mock_discovery_data,
        mock_phase_data
    ):
        """Test updating phase completion"""
        # Arrange - Create flow first
        create_response = api_client.post(
            "/api/v2/discovery-flows/flows",
            headers=authenticated_headers,
            json=mock_discovery_data
        )
        assert create_response.status_code == 201
        
        flow_id = mock_discovery_data["flow_id"]
        
        # Act
        response = api_client.put(
            f"/api/v2/discovery-flows/flows/{flow_id}/phase",
            headers=authenticated_headers,
            json=mock_phase_data
        )
        
        # Assert
        assert response.status_code == 200, "Phase update should succeed"
        
        response_data = response.json()
        assert response_data["flow_id"] == flow_id
        assert response_data["phase_completion"]["inventory"] == True
        assert response_data["progress_percentage"] > 0
        
    def test_complete_discovery_flow(
        self,
        api_client,
        authenticated_headers,
        mock_discovery_data
    ):
        """Test completing a discovery flow"""
        # Arrange - Create flow first
        create_response = api_client.post(
            "/api/v2/discovery-flows/flows",
            headers=authenticated_headers,
            json=mock_discovery_data
        )
        assert create_response.status_code == 201
        
        flow_id = mock_discovery_data["flow_id"]
        
        # Act
        response = api_client.post(
            f"/api/v2/discovery-flows/flows/{flow_id}/complete",
            headers=authenticated_headers
        )
        
        # Assert
        assert response.status_code == 200, "Flow completion should succeed"
        
        response_data = response.json()
        assert response_data["flow_id"] == flow_id
        assert response_data["status"] == "completed"
        assert response_data["assessment_ready"] == True
        
    def test_get_flow_summary(
        self,
        api_client,
        authenticated_headers,
        mock_discovery_data
    ):
        """Test getting flow summary"""
        # Arrange - Create flow first
        create_response = api_client.post(
            "/api/v2/discovery-flows/flows",
            headers=authenticated_headers,
            json=mock_discovery_data
        )
        assert create_response.status_code == 201
        
        flow_id = mock_discovery_data["flow_id"]
        
        # Act
        response = api_client.get(
            f"/api/v2/discovery-flows/flows/{flow_id}/summary",
            headers=authenticated_headers
        )
        
        # Assert
        assert response.status_code == 200, "Flow summary should succeed"
        
        response_data = response.json()
        assert response_data["flow_id"] == flow_id
        assert "progress_percentage" in response_data
        assert "phase_completion" in response_data
        assert "completed_phases" in response_data
        assert "total_phases" in response_data
        
    def test_get_flow_assets(
        self,
        api_client,
        authenticated_headers,
        mock_discovery_data,
        mock_phase_data
    ):
        """Test getting flow assets"""
        # Arrange - Create flow and add assets
        create_response = api_client.post(
            "/api/v2/discovery-flows/flows",
            headers=authenticated_headers,
            json=mock_discovery_data
        )
        assert create_response.status_code == 201
        
        flow_id = mock_discovery_data["flow_id"]
        
        # Update with inventory phase to create assets
        api_client.put(
            f"/api/v2/discovery-flows/flows/{flow_id}/phase",
            headers=authenticated_headers,
            json=mock_phase_data
        )
        
        # Act
        response = api_client.get(
            f"/api/v2/discovery-flows/flows/{flow_id}/assets",
            headers=authenticated_headers
        )
        
        # Assert
        assert response.status_code == 200, "Flow assets retrieval should succeed"
        
        response_data = response.json()
        assert isinstance(response_data, list), "Should return list of assets"
        
    def test_crewai_integration_endpoints(
        self,
        api_client,
        authenticated_headers
    ):
        """Test CrewAI integration endpoints"""
        # Arrange
        crewai_request = {
            "crewai_flow_id": "crewai-flow-123",
            "crewai_state": {
                "flow_status": "running",
                "current_task": "data_analysis",
                "agents": ["asset_intelligence", "cmdb_analyst"]
            },
            "raw_data": [
                {"asset_name": "test-server", "type": "server"}
            ],
            "metadata": {
                "source": "crewai_integration_test"
            }
        }
        
        # Act
        response = api_client.post(
            "/api/v2/discovery-flows/crewai/create-flow",
            headers=authenticated_headers,
            json=crewai_request
        )
        
        # Assert
        assert response.status_code == 201, "CrewAI flow creation should succeed"
        
        response_data = response.json()
        assert "flow_id" in response_data
        assert response_data["status"] == "active"
        
    def test_error_handling(
        self,
        api_client,
        authenticated_headers
    ):
        """Test error handling for invalid requests"""
        # Test invalid flow ID
        response = api_client.get(
            "/api/v2/discovery-flows/flows/invalid-flow-id",
            headers=authenticated_headers
        )
        assert response.status_code == 404
        
        # Test missing required fields
        response = api_client.post(
            "/api/v2/discovery-flows/flows",
            headers=authenticated_headers,
            json={"invalid": "data"}
        )
        assert response.status_code == 422  # Validation error
        
    def test_multi_tenant_isolation(
        self,
        api_client,
        mock_discovery_data
    ):
        """Test multi-tenant data isolation"""
        # Create flow with one tenant
        headers_tenant1 = {
            "Content-Type": "application/json",
            "X-Client-Account-Id": "11111111-1111-1111-1111-111111111111",
            "X-Engagement-Id": "22222222-2222-2222-2222-222222222222"
        }
        
        response1 = api_client.post(
            "/api/v2/discovery-flows/flows",
            headers=headers_tenant1,
            json=mock_discovery_data
        )
        assert response1.status_code == 201
        
        # Try to access with different tenant
        headers_tenant2 = {
            "Content-Type": "application/json",
            "X-Client-Account-Id": "99999999-9999-9999-9999-999999999999",
            "X-Engagement-Id": "88888888-8888-8888-8888-888888888888"
        }
        
        response2 = api_client.get(
            f"/api/v2/discovery-flows/flows/{mock_discovery_data['flow_id']}",
            headers=headers_tenant2
        )
        assert response2.status_code == 404, "Should not find flow from different tenant"

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 