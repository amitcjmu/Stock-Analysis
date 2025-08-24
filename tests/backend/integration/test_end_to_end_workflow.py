"""
End-to-End Workflow Integration Tests.

Tests complete end-to-end workflow: analyze -> process -> inventory -> feedback.
"""

import csv
import io

import pytest


@pytest.mark.asyncio
async def test_end_to_end_workflow(api_client, sample_cmdb_csv_content, auth_headers):
    """Test complete end-to-end workflow: analyze -> process -> inventory -> feedback."""

    # Step 1: Analyze CMDB data
    analyze_request = {
        "filename": "e2e_test.csv",
        "content": sample_cmdb_csv_content,
        "fileType": "csv",
    }

    analyze_response = await api_client.post(
        "/api/v1/unified-discovery/flow/initialize",
        json=analyze_request,
        headers=auth_headers,
    )
    assert analyze_response.status_code == 200

    analyze_data = analyze_response.json()
    assert analyze_data["status"] == "success"

    # Step 2: Process the data
    # Convert CSV to asset list for processing
    csv_reader = csv.DictReader(io.StringIO(sample_cmdb_csv_content))
    list(csv_reader)

    # For status check, we need a flow_id - using placeholder for now
    flow_id = "e2e-flow-123"
    process_response = await api_client.get(
        f"/api/v1/unified-discovery/flow/{flow_id}/status", headers=auth_headers
    )
    assert process_response.status_code == 200

    process_data = process_response.json()
    assert len(process_data["processedAssets"]) > 0

    # Step 3: Check inventory
    inventory_response = await api_client.get(
        "/api/v1/unified-discovery/flows/active", headers=auth_headers
    )
    assert inventory_response.status_code == 200

    inventory_data = inventory_response.json()
    assert "assets" in inventory_data
    assert "summary" in inventory_data

    # Step 4: Submit feedback (if analysis had issues)
    if analyze_data["dataQuality"]["score"] < 90:
        feedback_request = {
            "filename": "e2e_test.csv",
            "originalAnalysis": analyze_data,
            "userCorrections": {"comments": "Data quality looks good after review"},
        }

        feedback_response = await api_client.post(
            "/api/v1/discovery/cmdb-feedback",
            json=feedback_request,
            headers=auth_headers,
        )
        assert feedback_response.status_code == 200
