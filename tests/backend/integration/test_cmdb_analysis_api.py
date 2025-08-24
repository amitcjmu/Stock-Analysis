"""
CMDB Analysis API Integration Tests.

Tests the CMDB analysis API endpoints with agentic workflows.
"""

import pytest


class TestCMDBAnalysisAPI:
    """Test CMDB analysis API endpoints with agentic workflows."""

    @pytest.mark.asyncio
    async def test_analyze_cmdb_endpoint(
        self, api_client, sample_cmdb_csv_content, auth_headers
    ):
        """Test CMDB analysis endpoint with sample data."""
        request_data = {
            "filename": "test_assets.csv",
            "content": sample_cmdb_csv_content,
            "fileType": "csv",
        }

        response = await api_client.post(
            "/api/v1/unified-discovery/flow/initialize",
            json=request_data,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "status" in data
        assert "dataQuality" in data
        assert "coverage" in data
        assert "missingFields" in data
        assert "readyForImport" in data

        # Verify data quality structure
        quality = data["dataQuality"]
        assert "score" in quality
        assert "issues" in quality
        assert "recommendations" in quality
        assert isinstance(quality["score"], int)
        assert 0 <= quality["score"] <= 100

        # Verify coverage includes device types
        coverage = data["coverage"]
        assert "applications" in coverage
        assert "servers" in coverage
        assert "databases" in coverage
        # Note: dependencies might be 0 in this test data

        # Verify agentic analysis results
        assert isinstance(data["missingFields"], list)
        assert isinstance(data["readyForImport"], bool)

    @pytest.mark.asyncio
    async def test_cmdb_analysis_with_device_classification(
        self, api_client, auth_headers
    ):
        """Test that device classification works correctly in API."""
        device_heavy_content = """Asset_Name,CI_Type,Environment
core-switch-main,Switch,Production
san-storage-01,Storage,Production
firewall-perimeter,Firewall,Production
ups-datacenter,UPS,Production
vmware-host-01,Virtualization,Production"""

        request_data = {
            "filename": "devices.csv",
            "content": device_heavy_content,
            "fileType": "csv",
        }

        response = await api_client.post(
            "/api/v1/unified-discovery/flow/initialize",
            json=request_data,
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()

        # Should recognize device-heavy dataset
        assert data["status"] == "success"
        # Device-heavy datasets might have different readiness criteria
        assert "readyForImport" in data

    @pytest.mark.asyncio
    async def test_agentic_intelligence_integration(self, api_client, auth_headers):
        """Test that agentic CrewAI intelligence is properly integrated."""
        # Create data that would benefit from agentic analysis
        complex_content = """Name,Type,Description,Environment
complex-erp-system,Unknown,Enterprise resource planning system,Production
legacy-mainframe,Unknown,IBM z/OS mainframe system,Production
iot-sensor-network,Unknown,Temperature monitoring sensors,Production"""

        request_data = {
            "filename": "complex_assets.csv",
            "content": complex_content,
            "fileType": "csv",
        }

        response = await api_client.post(
            "/api/v1/unified-discovery/flow/initialize",
            json=request_data,
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()

        # Agentic analysis should provide intelligent insights
        assert "dataQuality" in data
        assert "recommendations" in data["dataQuality"]

        # Should have suggestions for unknown asset types
        recommendations = data["dataQuality"]["recommendations"]
        assert len(recommendations) > 0
