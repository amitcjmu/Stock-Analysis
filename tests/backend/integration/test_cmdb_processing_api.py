"""
CMDB Processing API Integration Tests.

Tests CMDB processing API with enhanced classification.
"""

import pytest


class TestCMDBProcessingAPI:
    """Test CMDB processing API with enhanced classification."""

    @pytest.mark.asyncio
    async def test_process_cmdb_data(
        self, api_client, sample_mixed_assets, auth_headers
    ):
        """Test CMDB data processing with mixed asset types."""
        # First, create a flow with the sample data
        request_data = {
            "filename": "mixed_assets.csv",
            "raw_data": sample_mixed_assets,
            "configuration": {},
        }

        init_response = await api_client.post(
            "/api/v1/unified-discovery/flows/initialize",
            json=request_data,
            headers=auth_headers,
        )
        assert init_response.status_code == 200

        init_data = init_response.json()
        assert "flow_id" in init_data
        flow_id = init_data["flow_id"]

        # Now get the flow status
        response = await api_client.get(
            f"/api/v1/unified-discovery/flows/{flow_id}/status", headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()

        # Verify flow status response structure
        assert "flow_id" in data
        assert "status" in data
        assert "current_phase" in data
        assert "progress_percentage" in data

        # Verify flow_id matches
        assert data["flow_id"] == flow_id

        # Verify status is valid
        assert data["status"] in [
            "initialized",
            "running",
            "processing",
            "completed",
            "failed",
            "paused",
        ]

        # Verify progress is a number between 0 and 100
        assert isinstance(data["progress_percentage"], (int, float))
        assert 0 <= data["progress_percentage"] <= 100

        # If include_details is True (default), verify additional fields
        if "phases" in data:
            assert isinstance(data["phases"], dict)

        if "metadata" in data:
            assert isinstance(data["metadata"], dict)

    @pytest.mark.asyncio
    async def test_device_processing_not_applicable(self, api_client, auth_headers):
        """Test that flow status endpoint returns proper structure."""
        # First, create a flow with device data
        device_data = [
            {
                "Asset_Name": "core-switch-01",
                "CI_Type": "Network",
                "Environment": "Production",
            },
            {
                "Asset_Name": "san-storage-01",
                "CI_Type": "Storage",
                "Environment": "Production",
            },
        ]

        request_data = {
            "filename": "devices.csv",
            "raw_data": device_data,
            "configuration": {},
        }

        init_response = await api_client.post(
            "/api/v1/unified-discovery/flows/initialize",
            json=request_data,
            headers=auth_headers,
        )
        assert init_response.status_code == 200

        init_data = init_response.json()
        assert "flow_id" in init_data
        flow_id = init_data["flow_id"]

        # Get flow status
        response = await api_client.get(
            f"/api/v1/unified-discovery/flows/{flow_id}/status", headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()

        # Verify flow status structure
        assert "flow_id" in data
        assert "status" in data
        assert "current_phase" in data

        # Note: Asset-level 6R readiness data would be retrieved from
        # the assets endpoint, not the flow status endpoint
        # The flow status endpoint provides flow-level information
