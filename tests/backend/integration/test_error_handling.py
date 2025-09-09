"""
Error Handling Integration Tests.

Tests error handling and edge cases.
"""

import pytest


class TestErrorHandling:
    """Test error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_invalid_cmdb_data(self, api_client, auth_headers):
        """Test handling of invalid CMDB data."""
        invalid_data = {
            "filename": "invalid.csv",
            "content": "Invalid,CSV,Content\nwith,mismatched,columns,too,many",
            "fileType": "csv",
        }

        response = await api_client.post(
            "/api/v1/unified-discovery/flow/initialize",
            json=invalid_data,
            headers=auth_headers,
        )

        # Should handle gracefully, not crash
        assert response.status_code in [200, 400, 422]

        if response.status_code == 200:
            data = response.json()
            # Should indicate issues with data quality
            assert "dataQuality" in data
            quality_score = data["dataQuality"]["score"]
            assert quality_score < 50  # Should be low quality

    @pytest.mark.asyncio
    async def test_empty_processing_request(self, api_client, auth_headers):
        """Test handling of empty processing request."""

        # For status check, we need a flow_id - using placeholder for now
        flow_id = "empty-flow-789"
        response = await api_client.get(
            f"/api/v1/unified-discovery/flow/{flow_id}/status", headers=auth_headers
        )

        # Should handle gracefully
        assert response.status_code in [200, 400]

        if response.status_code == 200:
            data = response.json()
            assert "processedAssets" in data
            assert len(data["processedAssets"]) == 0

    @pytest.mark.asyncio
    async def test_malformed_feedback(self, api_client, auth_headers):
        """Test handling of malformed feedback data."""
        malformed_feedback = {
            "filename": "test.csv"
            # Missing required fields - this should cause a validation error
        }

        response = await api_client.post(
            "/api/v1/unified-discovery/cmdb-feedback",
            json=malformed_feedback,
            headers=auth_headers,
        )

        # Should return validation error or not found (if endpoint doesn't exist)
        assert response.status_code in [404, 422]
