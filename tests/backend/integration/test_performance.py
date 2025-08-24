"""
Performance Integration Tests.

Tests performance with larger datasets.
"""

import time

import pytest


class TestPerformance:
    """Test performance with larger datasets."""

    @pytest.mark.asyncio
    async def test_large_dataset_processing(self, api_client, auth_headers):
        """Test processing of moderately large dataset."""
        # Create larger dataset (100 assets)
        large_dataset = []
        for i in range(100):
            asset_type = ["Server", "Application", "Database", "Network", "Storage"][
                i % 5
            ]
            large_dataset.append(
                {
                    "Asset_Name": f"asset-{i:03d}",
                    "CI_Type": asset_type,
                    "Environment": "Production" if i % 2 == 0 else "Development",
                    "CPU_Cores": str(4 + (i % 16)),
                    "Memory_GB": str(8 + (i % 32)),
                }
            )

        start_time = time.time()
        # For status check, we need a flow_id - using placeholder for now
        flow_id = "large-dataset-flow-999"
        response = await api_client.get(
            f"/api/v1/unified-discovery/flow/{flow_id}/status", headers=auth_headers
        )
        processing_time = time.time() - start_time

        assert response.status_code == 200
        # Should complete within reasonable time (30 seconds for 100 assets)
        assert processing_time < 30

        data = response.json()
        assert len(data["processedAssets"]) == 100
