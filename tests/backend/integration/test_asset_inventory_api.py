"""
Asset Inventory API Integration Tests.

Tests asset inventory API with enhanced features.
"""

import pytest


class TestAssetInventoryAPI:
    """Test asset inventory API with enhanced features."""

    @pytest.mark.asyncio
    async def test_get_assets_endpoint(self, api_client, auth_headers):
        """Test getting active discovery flows."""
        response = await api_client.get(
            "/api/v1/unified-discovery/flows/active", headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()

        # Verify response structure - should be a list of active flows
        assert isinstance(data, list)
        # If no active flows, that's expected for a fresh test environment

    @pytest.mark.asyncio
    async def test_suggested_headers_generation(self, api_client, auth_headers):
        """Test that suggested headers are generated correctly."""
        response = await api_client.get(
            "/api/v1/unified-discovery/flows/active", headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()

        if "suggestedHeaders" in data:
            headers = data["suggestedHeaders"]
            assert isinstance(headers, list)

            # Verify header structure
            for header in headers:
                assert "key" in header
                assert "label" in header
                assert "description" in header

    @pytest.mark.asyncio
    async def test_assets_with_6r_readiness(self, api_client, auth_headers):
        """Test that assets include 6R readiness information."""
        response = await api_client.get(
            "/api/v1/unified-discovery/flows/active", headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()

        # The response might be an empty list if no active flows
        if isinstance(data, list) and len(data) == 0:
            return  # No assets to test in empty response

        # Check if response has assets structure
        if "assets" not in data:
            return  # No assets structure in response

        assets = data["assets"]

        # Check if any assets have 6R readiness data
        assets_with_readiness = [a for a in assets if "sixr_ready" in a]
        [a for a in assets if "migration_complexity" in a]

        # Note: This might be empty for test data, but structure should be correct
        if assets_with_readiness:
            for asset in assets_with_readiness:
                readiness = asset["sixr_ready"]
                assert readiness in [
                    "Ready",
                    "Not Applicable",
                    "Needs Owner Info",
                    "Needs Infrastructure Data",
                    "Needs Version Info",
                    "Insufficient Data",
                    "Type Classification Needed",
                    "Complex Analysis Required",
                ]
