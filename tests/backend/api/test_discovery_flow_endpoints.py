"""
End-to-End API Testing for Discovery Flow (Task 63)

Tests complete API workflows including:
- Full Discovery Flow API execution end-to-end
- API response validation and data consistency
- Authentication and authorization flows
- Multi-tenant API isolation and security
- Real-time WebSocket communication testing
"""

import pytest
import asyncio
import json
from typing import Dict, List, Any
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, Mock, patch
import websockets
from datetime import datetime, timedelta

# API testing fixtures
@pytest.fixture
def api_client():
    """Test client for API endpoints"""
    from backend.app.main import app
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
def mock_discovery_data():
    """Mock data for Discovery Flow testing"""
    return {
        "engagement_id": "eng_123",
        "client_account_id": "client_456", 
        "data_source": "cmdb_import",
        "assets": [
            {
                "asset_id": "asset_001",
                "hostname": "web-server-01",
                "ip_address": "192.168.1.10",
                "os_type": "Linux",
                "application": "Web Application",
                "environment": "Production"
            },
            {
                "asset_id": "asset_002", 
                "hostname": "db-server-01",
                "ip_address": "192.168.1.20",
                "os_type": "Windows",
                "application": "Database Server",
                "environment": "Production"
            }
        ],
        "configuration": {
            "enable_field_mapping": True,
            "enable_data_cleansing": True,
            "enable_dependency_analysis": True,
            "parallel_execution": True
        }
    }

@pytest.fixture
def mock_websocket_server():
    """Mock WebSocket server for real-time testing"""
    class MockWebSocketServer:
        def __init__(self):
            self.connected_clients = []
            self.messages_sent = []
            
        async def connect(self, websocket):
            self.connected_clients.append(websocket)
            
        async def disconnect(self, websocket):
            if websocket in self.connected_clients:
                self.connected_clients.remove(websocket)
                
        async def send_progress_update(self, progress_data: Dict[str, Any]):
            message = {
                "type": "progress_update",
                "data": progress_data,
                "timestamp": datetime.now().isoformat()
            }
            
            for client in self.connected_clients:
                await client.send(json.dumps(message))
                self.messages_sent.append(message)
                
    return MockWebSocketServer()

class TestDiscoveryFlowAPIEndpoints:
    """Test suite for Discovery Flow API endpoints"""
    
    def test_discovery_flow_initialization_endpoint(
        self,
        api_client,
        authenticated_headers,
        mock_discovery_data
    ):
        """Test Discovery Flow initialization API endpoint (Task 63)"""
        # Act
        response = api_client.post(
            "/api/v1/flows/",
            headers=authenticated_headers,
            json={**mock_discovery_data, "flow_type": "discovery"}
        )
        
        # Assert
        assert response.status_code == 200, "Initialization should succeed"
        
        response_data = response.json()
        assert "flow_id" in response_data, "Should return flow ID"
        assert "status" in response_data, "Should return status"
        assert response_data["status"] == "initialized", "Status should be initialized"
        assert "estimated_duration" in response_data, "Should provide time estimate"
        
        # Verify response structure
        assert "crew_sequence" in response_data, "Should include crew execution sequence"
        assert len(response_data["crew_sequence"]) > 0, "Should have planned crew executions"
        
    def test_field_mapping_crew_execution_endpoint(
        self,
        api_client,
        authenticated_headers
    ):
        """Test Field Mapping Crew execution API endpoint (Task 63)"""
        # Arrange
        field_mapping_request = {
            "flow_id": "flow_123",
            "crew_type": "field_mapping",
            "input_data": {
                "source_fields": ["hostname", "ip_addr", "os_version"],
                "target_schema": "migration_schema_v1",
                "confidence_threshold": 0.8
            }
        }
        
        # Act
        response = api_client.post(
            "/api/v1/flows/crews/field-mapping/execute",
            headers=authenticated_headers,
            json=field_mapping_request
        )
        
        # Assert
        assert response.status_code == 200, "Field mapping execution should succeed"
        
        response_data = response.json()
        assert response_data["status"] == "completed", "Crew should complete successfully"
        assert "field_mappings" in response_data, "Should return field mappings"
        assert "confidence_scores" in response_data, "Should include confidence scores"
        assert "execution_time" in response_data, "Should track execution time"
        
        # Verify field mapping structure
        field_mappings = response_data["field_mappings"]
        assert isinstance(field_mappings, list), "Field mappings should be a list"
        if field_mappings:
            mapping = field_mappings[0]
            assert "source_field" in mapping, "Should include source field"
            assert "target_field" in mapping, "Should include target field"
            assert "confidence" in mapping, "Should include confidence score"
            
    def test_data_cleansing_crew_execution_endpoint(
        self,
        api_client,
        authenticated_headers
    ):
        """Test Data Cleansing Crew execution API endpoint (Task 63)"""
        # Arrange
        cleansing_request = {
            "flow_id": "flow_123",
            "crew_type": "data_cleansing", 
            "input_data": {
                "raw_assets": [
                    {"hostname": "WEB-01", "ip": "192.168.1.10", "status": "Active"},
                    {"hostname": "db-01", "ip": "192.168.1.20", "status": "active"}
                ],
                "cleansing_rules": {
                    "normalize_hostnames": True,
                    "validate_ip_addresses": True,
                    "standardize_status_values": True
                }
            }
        }
        
        # Act
        response = api_client.post(
            "/api/v1/flows/crews/data-cleansing/execute",
            headers=authenticated_headers,
            json=cleansing_request
        )
        
        # Assert
        assert response.status_code == 200, "Data cleansing should succeed"
        
        response_data = response.json()
        assert response_data["status"] == "completed", "Cleansing should complete"
        assert "cleansed_assets" in response_data, "Should return cleansed data"
        assert "quality_metrics" in response_data, "Should include quality metrics"
        assert "issues_resolved" in response_data, "Should track resolved issues"
        
    def test_complete_discovery_flow_execution_endpoint(
        self,
        api_client,
        authenticated_headers,
        mock_discovery_data
    ):
        """Test complete Discovery Flow execution API endpoint (Task 63)"""
        # Act
        response = api_client.post(
            "/api/v1/flows/execute",
            headers=authenticated_headers,
            json={**mock_discovery_data, "flow_type": "discovery"}
        )
        
        # Assert
        assert response.status_code == 200, "Complete flow should execute successfully"
        
        response_data = response.json()
        assert response_data["status"] in ["in_progress", "completed"], "Should have valid status"
        assert "flow_id" in response_data, "Should return flow ID"
        assert "crew_results" in response_data, "Should include crew results"
        
        # Verify crew execution results
        crew_results = response_data["crew_results"]
        expected_crews = [
            "field_mapping", "data_cleansing", "inventory_building",
            "app_server_dependencies", "app_app_dependencies", "technical_debt"
        ]
        
        for crew_name in expected_crews:
            assert crew_name in crew_results, f"Should include {crew_name} results"
            crew_result = crew_results[crew_name]
            assert "status" in crew_result, f"{crew_name} should have status"
            assert "execution_time" in crew_result, f"{crew_name} should track execution time"
            
    def test_flow_status_monitoring_endpoint(
        self,
        api_client,
        authenticated_headers
    ):
        """Test flow status monitoring API endpoint (Task 63)"""
        # Arrange
        flow_id = "flow_123"
        
        # Act
        response = api_client.get(
            f"/api/v1/flows/{flow_id}/status",
            headers=authenticated_headers
        )
        
        # Assert
        assert response.status_code == 200, "Status endpoint should respond"
        
        response_data = response.json()
        assert "flow_id" in response_data, "Should include flow ID"
        assert "overall_status" in response_data, "Should include overall status"
        assert "progress_percentage" in response_data, "Should include progress"
        assert "crew_statuses" in response_data, "Should include crew statuses"
        assert "estimated_completion" in response_data, "Should estimate completion time"
        
        # Verify crew status structure
        crew_statuses = response_data["crew_statuses"]
        assert isinstance(crew_statuses, dict), "Crew statuses should be dictionary"
        
    def test_flow_results_retrieval_endpoint(
        self,
        api_client,
        authenticated_headers
    ):
        """Test flow results retrieval API endpoint (Task 63)"""
        # Arrange
        flow_id = "flow_123"
        
        # Act
        response = api_client.get(
            f"/api/v1/flows/{flow_id}/results",
            headers=authenticated_headers
        )
        
        # Assert
        assert response.status_code == 200, "Results endpoint should respond"
        
        response_data = response.json()
        assert "flow_id" in response_data, "Should include flow ID"
        assert "final_status" in response_data, "Should include final status"
        assert "crew_results" in response_data, "Should include all crew results"
        assert "summary_metrics" in response_data, "Should include summary metrics"
        assert "recommendations" in response_data, "Should include recommendations"
        
        # Verify summary metrics
        summary_metrics = response_data["summary_metrics"]
        assert "total_assets_processed" in summary_metrics, "Should count processed assets"
        assert "field_mappings_created" in summary_metrics, "Should count field mappings"
        assert "data_quality_score" in summary_metrics, "Should include quality score"
        
    def test_multi_tenant_api_isolation(
        self,
        api_client
    ):
        """Test multi-tenant API isolation (Task 63)"""
        # Arrange
        client_1_headers = {
            "Authorization": "Bearer client_1_token",
            "Content-Type": "application/json",
            "X-Client-Account-ID": "client_001"
        }
        
        client_2_headers = {
            "Authorization": "Bearer client_2_token",
            "Content-Type": "application/json",
            "X-Client-Account-ID": "client_002"
        }
        
        # Create flow for client 1
        client_1_data = {
            "engagement_id": "eng_client_1",
            "client_account_id": "client_001",
            "assets": [{"hostname": "client1-server"}]
        }
        
        # Act
        response_1 = api_client.post(
            "/api/v1/flows/",
            headers=client_1_headers,
            json={**client_1_data, "flow_type": "discovery"}
        )
        
        flow_id_1 = response_1.json()["flow_id"]
        
        # Client 2 tries to access client 1's flow
        response_2 = api_client.get(
            f"/api/v1/flows/{flow_id_1}/status",
            headers=client_2_headers
        )
        
        # Assert
        assert response_1.status_code == 200, "Client 1 should create flow successfully"
        assert response_2.status_code == 403, "Client 2 should be denied access to client 1's flow"
        
    def test_api_authentication_and_authorization(
        self,
        api_client,
        mock_discovery_data
    ):
        """Test API authentication and authorization (Task 63)"""
        # Test without authentication
        response_no_auth = api_client.post(
            "/api/v1/flows/",
            json={**mock_discovery_data, "flow_type": "discovery"}
        )
        
        # Test with invalid token
        invalid_headers = {
            "Authorization": "Bearer invalid_token",
            "Content-Type": "application/json"
        }
        
        response_invalid_auth = api_client.post(
            "/api/v1/flows/", 
            headers=invalid_headers,
            json={**mock_discovery_data, "flow_type": "discovery"}
        )
        
        # Test with valid token but insufficient permissions
        limited_headers = {
            "Authorization": "Bearer limited_token",
            "Content-Type": "application/json",
            "X-User-Role": "viewer"  # Read-only role
        }
        
        response_limited_auth = api_client.post(
            "/api/v1/flows/",
            headers=limited_headers,
            json={**mock_discovery_data, "flow_type": "discovery"}
        )
        
        # Assert
        assert response_no_auth.status_code == 401, "Should require authentication"
        assert response_invalid_auth.status_code == 401, "Should reject invalid tokens"
        assert response_limited_auth.status_code == 403, "Should enforce role permissions"
        
    @pytest.mark.asyncio
    async def test_websocket_real_time_updates(
        self,
        mock_websocket_server
    ):
        """Test WebSocket real-time progress updates (Task 63)"""
        # Arrange
        class MockWebSocket:
            def __init__(self):
                self.received_messages = []
                
            async def send(self, message):
                self.received_messages.append(json.loads(message))
                
        mock_client = MockWebSocket()
        await mock_websocket_server.connect(mock_client)
        
        # Act - Send progress updates
        progress_updates = [
            {
                "flow_id": "flow_123",
                "crew_name": "field_mapping",
                "status": "in_progress",
                "progress_percentage": 25
            },
            {
                "flow_id": "flow_123", 
                "crew_name": "field_mapping",
                "status": "completed",
                "progress_percentage": 100
            }
        ]
        
        for update in progress_updates:
            await mock_websocket_server.send_progress_update(update)
            
        # Assert
        assert len(mock_client.received_messages) == 2, "Should receive all progress updates"
        
        first_message = mock_client.received_messages[0]
        assert first_message["type"] == "progress_update", "Should be progress update type"
        assert first_message["data"]["status"] == "in_progress", "Should include status"
        assert first_message["data"]["progress_percentage"] == 25, "Should include progress"
        
        second_message = mock_client.received_messages[1]
        assert second_message["data"]["status"] == "completed", "Should show completion"
        
    def test_api_error_handling_and_responses(
        self,
        api_client,
        authenticated_headers
    ):
        """Test API error handling and response formats (Task 63)"""
        # Test invalid request data
        invalid_data = {
            "invalid_field": "invalid_value"
            # Missing required fields
        }
        
        response_invalid = api_client.post(
            "/api/v1/discovery/flow/initialize",
            headers=authenticated_headers,
            json=invalid_data
        )
        
        # Test non-existent flow ID
        response_not_found = api_client.get(
            "/api/v1/discovery/flow/non_existent_flow/status",
            headers=authenticated_headers
        )
        
        # Assert error responses
        assert response_invalid.status_code == 422, "Should return validation error"
        assert response_not_found.status_code == 404, "Should return not found error"
        
        # Verify error response structure
        invalid_error = response_invalid.json()
        assert "detail" in invalid_error, "Should include error details"
        assert "error_type" in invalid_error, "Should include error type"
        
        not_found_error = response_not_found.json()
        assert "message" in not_found_error, "Should include error message"
        
    def test_api_performance_and_timeouts(
        self,
        api_client,
        authenticated_headers,
        mock_discovery_data
    ):
        """Test API performance characteristics and timeout handling (Task 63)"""
        # Arrange
        large_dataset = mock_discovery_data.copy()
        large_dataset["assets"] = [
            {
                "asset_id": f"asset_{i:03d}",
                "hostname": f"server-{i:03d}",
                "ip_address": f"192.168.1.{i % 255 + 1}",
                "os_type": "Linux" if i % 2 == 0 else "Windows"
            }
            for i in range(100)  # 100 assets for performance testing
        ]
        
        # Act
        start_time = datetime.now()
        response = api_client.post(
            "/api/v1/flows/",
            headers=authenticated_headers,
            json={**large_dataset, "flow_type": "discovery"},
            timeout=30  # 30 second timeout
        )
        end_time = datetime.now()
        
        execution_time = (end_time - start_time).total_seconds()
        
        # Assert
        assert response.status_code == 200, "Large dataset should be handled successfully"
        assert execution_time < 30, "Should complete within timeout period"
        
        response_data = response.json()
        assert "performance_metrics" in response_data, "Should include performance metrics"
        
    def test_api_data_consistency_and_validation(
        self,
        api_client,
        authenticated_headers,
        mock_discovery_data
    ):
        """Test API data consistency and validation (Task 63)"""
        # Initialize flow
        init_response = api_client.post(
            "/api/v1/flows/",
            headers=authenticated_headers,
            json={**mock_discovery_data, "flow_type": "discovery"}
        )
        
        flow_id = init_response.json()["flow_id"]
        
        # Execute flow
        execute_response = api_client.post(
            "/api/v1/flows/execute",
            headers=authenticated_headers,
            json={"flow_id": flow_id, "flow_type": "discovery"}
        )
        
        # Get results
        results_response = api_client.get(
            f"/api/v1/flows/{flow_id}/results",
            headers=authenticated_headers
        )
        
        # Assert data consistency
        assert init_response.status_code == 200, "Initialization should succeed"
        assert execute_response.status_code == 200, "Execution should succeed"
        assert results_response.status_code == 200, "Results retrieval should succeed"
        
        # Verify data consistency across endpoints
        init_data = init_response.json()
        results_data = results_response.json()
        
        assert init_data["flow_id"] == results_data["flow_id"], "Flow ID should be consistent"
        assert len(mock_discovery_data["assets"]) <= results_data["summary_metrics"]["total_assets_processed"], "Asset count should be consistent"

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 