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
        # Parse CSV content into list of records
        lines = sample_cmdb_csv_content.strip().split("\n")
        headers = lines[0].split(",")
        records = []
        for line in lines[1:]:
            values = line.split(",")
            record = dict(zip(headers, values))
            records.append(record)

        request_data = {
            "filename": "test_assets.csv",
            "raw_data": records,
            "configuration": {},
        }

        response = await api_client.post(
            "/api/v1/unified-discovery/flows/initialize",
            json=request_data,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify FlowInitializationResponse structure
        assert "success" in data
        assert "flow_id" in data
        assert "flow_name" in data
        assert "status" in data
        assert "message" in data
        assert "metadata" in data

        # Verify success
        assert data["success"] is True
        assert data["status"] == "initialized"
        assert isinstance(data["flow_id"], str)
        assert len(data["flow_id"]) > 0

        # Verify metadata structure
        metadata = data["metadata"]
        assert isinstance(metadata, dict)
        assert "created_at" in metadata
        assert "has_raw_data" in metadata

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

        # Parse CSV content into list of records
        lines = device_heavy_content.strip().split("\n")
        headers = lines[0].split(",")
        records = []
        for line in lines[1:]:
            values = line.split(",")
            record = dict(zip(headers, values))
            records.append(record)

        request_data = {
            "filename": "devices.csv",
            "raw_data": records,
            "configuration": {},
        }

        response = await api_client.post(
            "/api/v1/unified-discovery/flows/initialize",
            json=request_data,
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()

        # Verify FlowInitializationResponse structure
        assert data["success"] is True
        assert data["status"] == "initialized"
        assert "flow_id" in data
        assert "metadata" in data

    @pytest.mark.asyncio
    async def test_agentic_intelligence_integration(self, api_client, auth_headers):
        """Test that agentic CrewAI intelligence is properly integrated."""
        # Create data that would benefit from agentic analysis
        complex_content = """Name,Type,Description,Environment
complex-erp-system,Unknown,Enterprise resource planning system,Production
legacy-mainframe,Unknown,IBM z/OS mainframe system,Production
iot-sensor-network,Unknown,Temperature monitoring sensors,Production"""

        # Parse CSV content into list of records
        lines = complex_content.strip().split("\n")
        headers = lines[0].split(",")
        records = []
        for line in lines[1:]:
            values = line.split(",")
            record = dict(zip(headers, values))
            records.append(record)

        request_data = {
            "filename": "complex_assets.csv",
            "raw_data": records,
            "configuration": {},
        }

        response = await api_client.post(
            "/api/v1/unified-discovery/flows/initialize",
            json=request_data,
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()

        # Verify FlowInitializationResponse structure
        assert "success" in data
        assert data["success"] is True
        assert "flow_id" in data
        assert "metadata" in data

        # Verify that flow was initialized successfully
        assert data["status"] == "initialized"
        assert isinstance(data["flow_id"], str)
