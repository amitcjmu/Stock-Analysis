"""
CrewAI Flow End-to-End Validation Script
Tests the complete CrewAI Flow system in Docker environment.
"""

import pytest
import requests
import time
from datetime import datetime


class TestCrewAIFlowValidation:
    """End-to-end validation tests for CrewAI Flow system."""
    
    BASE_URL = "http://localhost:8000"
    
    @pytest.fixture(scope="class")
    def api_client(self):
        """API client for testing."""
        return requests.Session()
    
    @pytest.fixture
    def sample_cmdb_data(self):
        """Sample CMDB data for testing."""
        return {
            "file_data": [
                {
                    "name": "web-server-prod-01",
                    "type": "server",
                    "environment": "production",
                    "cpu_cores": 8,
                    "memory_gb": 32,
                    "os": "Ubuntu 20.04"
                },
                {
                    "name": "customer-database",
                    "type": "database",
                    "environment": "production",
                    "engine": "PostgreSQL",
                    "version": "13.5"
                },
                {
                    "name": "order-processing-app",
                    "type": "application",
                    "environment": "production",
                    "language": "Java",
                    "framework": "Spring Boot"
                }
            ],
            "metadata": {
                "source": "validation_test",
                "timestamp": datetime.utcnow().isoformat(),
                "client_account_id": "test-client-validation",
                "engagement_id": "test-engagement-validation"
            }
        }
    
    def test_service_health_check(self, api_client):
        """Test that the CrewAI Flow service is healthy."""
        response = api_client.get(f"{self.BASE_URL}/api/v1/discovery/flow/health")
        
        assert response.status_code == 200
        health_data = response.json()
        
        assert health_data["service_name"] == "CrewAI Flow Service"
        assert "status" in health_data
        assert "features" in health_data
        assert "timestamp" in health_data
        
        # Verify key features are available
        features = health_data["features"]
        assert features["fallback_execution"] is True
        assert features["state_persistence"] is True
    
    def test_discovery_workflow_initiation(self, api_client, sample_cmdb_data):
        """Test initiating a discovery workflow."""
        response = api_client.post(
            f"{self.BASE_URL}/api/v1/discovery/analyze",
            json=sample_cmdb_data,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # Verify response structure
        assert "session_id" in result
        assert "status" in result
        assert "current_phase" in result
        assert result["status"] in ["running", "completed", "error"]
        
        return result["session_id"]
    
    def test_workflow_state_retrieval(self, api_client, sample_cmdb_data):
        """Test retrieving workflow state."""
        # First initiate a workflow
        session_id = self.test_discovery_workflow_initiation(api_client, sample_cmdb_data)
        
        # Then retrieve its state
        response = api_client.get(f"{self.BASE_URL}/api/v1/discovery/flow/state/{session_id}")
        
        assert response.status_code == 200
        state = response.json()
        
        # Verify state structure
        assert state["session_id"] == session_id
        assert "status" in state
        assert "current_phase" in state
        assert "phases_completed" in state
        assert "results" in state
        
        # Verify legacy compatibility
        assert "data_validation" in state
        assert "field_mapping" in state
        assert "asset_classification" in state
    
    def test_active_flows_monitoring(self, api_client):
        """Test active flows monitoring endpoint."""
        response = api_client.get(f"{self.BASE_URL}/api/v1/discovery/flow/active")
        
        assert response.status_code == 200
        summary = response.json()
        
        assert "total_active_flows" in summary
        assert "active_sessions" in summary
        assert "flows_by_status" in summary
        assert "service_available" in summary
        assert "timestamp" in summary
    
    def test_workflow_error_handling(self, api_client):
        """Test workflow error handling with invalid data."""
        invalid_data = {
            "file_data": None,
            "metadata": {}
        }
        
        response = api_client.post(
            f"{self.BASE_URL}/api/v1/discovery/analyze",
            json=invalid_data,
            headers={"Content-Type": "application/json"}
        )
        
        # Should handle error gracefully
        assert response.status_code in [200, 400, 422]
        
        if response.status_code == 200:
            result = response.json()
            assert result["status"] == "error"
            assert "message" in result
    
    def test_concurrent_workflows(self, api_client, sample_cmdb_data):
        """Test handling multiple concurrent workflows."""
        session_ids = []
        
        # Start multiple workflows concurrently
        for i in range(3):
            test_data = sample_cmdb_data.copy()
            test_data["metadata"]["source"] = f"concurrent_test_{i}"
            
            response = api_client.post(
                f"{self.BASE_URL}/api/v1/discovery/analyze",
                json=test_data,
                headers={"Content-Type": "application/json"}
            )
            
            assert response.status_code == 200
            result = response.json()
            session_ids.append(result["session_id"])
        
        # Verify all workflows are tracked
        response = api_client.get(f"{self.BASE_URL}/api/v1/discovery/flow/active")
        assert response.status_code == 200
        
        summary = response.json()
        assert summary["total_active_flows"] >= 3
        
        # Verify each session can be retrieved
        for session_id in session_ids:
            response = api_client.get(f"{self.BASE_URL}/api/v1/discovery/flow/state/{session_id}")
            assert response.status_code == 200
    
    def test_fallback_execution_mode(self, api_client, sample_cmdb_data):
        """Test that fallback execution works when CrewAI Flow is unavailable."""
        # This test verifies the system works in degraded mode
        response = api_client.post(
            f"{self.BASE_URL}/api/v1/discovery/analyze",
            json=sample_cmdb_data,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # Should complete successfully even in fallback mode
        assert result["status"] in ["running", "completed"]
        
        # Verify state can be retrieved
        session_id = result["session_id"]
        response = api_client.get(f"{self.BASE_URL}/api/v1/discovery/flow/state/{session_id}")
        assert response.status_code == 200
        
        state = response.json()
        assert "results" in state
        
        # In fallback mode, should have basic validation results
        if "data_validation" in state and state["data_validation"]["status"] == "completed":
            validation_results = state["data_validation"]["results"]
            assert "total_records" in validation_results
            assert "method" in validation_results
            assert validation_results["method"] == "fallback_validation"
    
    def test_performance_with_large_dataset(self, api_client):
        """Test performance with larger datasets."""
        # Create a larger dataset
        large_dataset = []
        for i in range(100):
            large_dataset.append({
                "name": f"asset-{i:03d}",
                "type": "server" if i % 3 == 0 else "application" if i % 3 == 1 else "database",
                "environment": "production" if i % 2 == 0 else "staging",
                "department": "IT" if i % 4 == 0 else "Sales"
            })
        
        large_data = {
            "file_data": large_dataset,
            "metadata": {
                "source": "performance_test",
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        start_time = time.time()
        response = api_client.post(
            f"{self.BASE_URL}/api/v1/discovery/analyze",
            json=large_data,
            headers={"Content-Type": "application/json"}
        )
        end_time = time.time()
        
        assert response.status_code == 200
        result = response.json()
        
        # Should complete within reasonable time (< 30 seconds for 100 records)
        assert (end_time - start_time) < 30.0
        assert result["status"] in ["running", "completed"]
    
    def test_data_validation_accuracy(self, api_client, sample_cmdb_data):
        """Test data validation accuracy."""
        response = api_client.post(
            f"{self.BASE_URL}/api/v1/discovery/analyze",
            json=sample_cmdb_data,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        result = response.json()
        session_id = result["session_id"]
        
        # Wait a moment for processing
        time.sleep(2)
        
        # Get final state
        response = api_client.get(f"{self.BASE_URL}/api/v1/discovery/flow/state/{session_id}")
        assert response.status_code == 200
        
        state = response.json()
        
        # Verify data validation results
        if "data_validation" in state and state["data_validation"]["status"] == "completed":
            validation = state["data_validation"]["results"]
            assert validation["total_records"] == 3
            assert validation["valid_records"] >= 0
            assert validation["validation_rate"] >= 0.0
    
    def test_field_mapping_intelligence(self, api_client, sample_cmdb_data):
        """Test field mapping intelligence."""
        response = api_client.post(
            f"{self.BASE_URL}/api/v1/discovery/analyze",
            json=sample_cmdb_data,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        result = response.json()
        session_id = result["session_id"]
        
        # Wait for processing
        time.sleep(3)
        
        # Get state
        response = api_client.get(f"{self.BASE_URL}/api/v1/discovery/flow/state/{session_id}")
        assert response.status_code == 200
        
        state = response.json()
        
        # Verify field mapping results
        if "field_mapping" in state and state["field_mapping"]["status"] == "completed":
            mapping = state["field_mapping"]["results"]
            assert "field_mappings" in mapping
            assert "total_fields" in mapping
            assert mapping["total_fields"] > 0
    
    def test_asset_classification_results(self, api_client, sample_cmdb_data):
        """Test asset classification results."""
        response = api_client.post(
            f"{self.BASE_URL}/api/v1/discovery/analyze",
            json=sample_cmdb_data,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        result = response.json()
        session_id = result["session_id"]
        
        # Wait for processing
        time.sleep(5)
        
        # Get state
        response = api_client.get(f"{self.BASE_URL}/api/v1/discovery/flow/state/{session_id}")
        assert response.status_code == 200
        
        state = response.json()
        
        # Verify asset classification results
        if "asset_classification" in state and state["asset_classification"]["status"] == "completed":
            classification = state["asset_classification"]["results"]
            assert "classified_assets" in classification
            assert "total_assets" in classification
            assert classification["total_assets"] == 3
            
            # Verify each asset has required fields
            for asset in classification["classified_assets"]:
                assert "id" in asset
                assert "asset_type" in asset
                assert "migration_strategy" in asset
                assert "confidence" in asset


class TestDockerIntegration:
    """Test Docker container integration."""
    
    def test_container_health(self):
        """Test that the backend container is healthy."""
        try:
            response = requests.get("http://localhost:8000/health", timeout=10)
            assert response.status_code == 200
            
            health = response.json()
            assert health["status"] == "healthy"
        except requests.exceptions.RequestException:
            pytest.skip("Backend container not available")
    
    def test_database_connectivity(self):
        """Test database connectivity through the API."""
        try:
            response = requests.get("http://localhost:8000/api/v1/discovery/flow/health", timeout=10)
            assert response.status_code == 200
            
            health = response.json()
            # Should not fail due to database issues
            assert "status" in health
        except requests.exceptions.RequestException:
            pytest.skip("Backend container not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"]) 