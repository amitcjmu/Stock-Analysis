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

        # For status check, we need a flow_id - using placeholder for now
        flow_id = "test-flow-123"
        response = await api_client.get(
            f"/api/v1/unified-discovery/flow/{flow_id}/status", headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()

        # Verify processing results
        assert "status" in data
        assert "processedAssets" in data
        assert "qualityMetrics" in data
        assert "summary" in data

        # Verify processed assets have enhanced classification
        processed_assets = data["processedAssets"]
        assert len(processed_assets) > 0

        # Check for intelligent asset type classification
        asset_types = [
            asset.get("intelligent_asset_type") for asset in processed_assets
        ]
        assert "Database" in asset_types
        assert "Server" in asset_types

        # Check for 6R readiness assessment
        readiness_values = [
            asset.get("sixr_ready")
            for asset in processed_assets
            if asset.get("sixr_ready")
        ]
        assert len(readiness_values) > 0

        # Check for migration complexity
        complexity_values = [
            asset.get("migration_complexity")
            for asset in processed_assets
            if asset.get("migration_complexity")
        ]
        assert len(complexity_values) > 0

    @pytest.mark.asyncio
    async def test_device_processing_not_applicable(self, api_client, auth_headers):
        """Test that devices are properly marked as not applicable for 6R."""

        # For status check, we need a flow_id - using placeholder for now
        flow_id = "test-flow-456"
        response = await api_client.get(
            f"/api/v1/unified-discovery/flow/{flow_id}/status", headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()
        processed_assets = data["processedAssets"]

        # Devices should be marked as "Not Applicable" for 6R
        for asset in processed_assets:
            if asset.get("intelligent_asset_type") in [
                "Network Device",
                "Storage Device",
            ]:
                assert asset.get("sixr_ready") == "Not Applicable"
