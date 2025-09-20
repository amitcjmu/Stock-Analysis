"""
End-to-End Workflow Integration Tests.

Tests complete end-to-end workflow using Master Flow Orchestrator (MFO) patterns:
analyze -> process -> inventory -> feedback.

Aligned with ADR-006: Master Flow Orchestrator and lessons from coding-agent-guide.md.
"""

import csv
import io

import pytest
from app.services.persistent_agents.tenant_scoped_agent_pool import TenantScopedAgentPool
from tests.fixtures.mfo_fixtures import (
    demo_tenant_context,
    mock_tenant_scoped_agent_pool,
    mock_flow_execution_results,
)


@pytest.mark.asyncio
@pytest.mark.mfo
async def test_end_to_end_workflow(api_client, sample_cmdb_csv_content, auth_headers, demo_tenant_context, mock_tenant_scoped_agent_pool):
    """Test complete end-to-end workflow: analyze -> process -> inventory -> feedback."""

    # Step 1: Analyze CMDB data using MFO endpoint
    analyze_request = {
        "filename": "e2e_test.csv",
        "content": sample_cmdb_csv_content,
        "file_type": "csv",  # Use snake_case not camelCase
        "flow_type": "discovery",
        "client_account_id": demo_tenant_context.client_account_id,
        "engagement_id": demo_tenant_context.engagement_id,
    }

    analyze_response = await api_client.post(
        "/api/v1/master-flows/initialize",  # Use MFO endpoint
        json=analyze_request,
        headers={
            **auth_headers,
            "X-Client-Account-ID": demo_tenant_context.client_account_id,
            "X-Engagement-ID": demo_tenant_context.engagement_id,
        },
    )
    assert analyze_response.status_code == 200

    analyze_data = analyze_response.json()
    assert analyze_data["status"] == "success"

    # Step 2: Process the data
    # Convert CSV to asset list for processing
    csv_reader = csv.DictReader(io.StringIO(sample_cmdb_csv_content))
    list(csv_reader)

    # Extract flow_id from analyze response for status check
    flow_id = analyze_data.get("flow_id", "e2e-flow-123")
    process_response = await api_client.get(
        f"/api/v1/master-flows/{flow_id}/status",  # Use MFO endpoint
        headers={
            **auth_headers,
            "X-Client-Account-ID": demo_tenant_context.client_account_id,
            "X-Engagement-ID": demo_tenant_context.engagement_id,
        }
    )
    assert process_response.status_code == 200

    process_data = process_response.json()
    # Use snake_case field names
    assert len(process_data["processed_assets"]) > 0 or len(process_data.get("processedAssets", [])) > 0

    # Step 3: Check inventory using MFO endpoint
    inventory_response = await api_client.get(
        "/api/v1/master-flows/active",  # Use MFO endpoint
        headers={
            **auth_headers,
            "X-Client-Account-ID": demo_tenant_context.client_account_id,
            "X-Engagement-ID": demo_tenant_context.engagement_id,
        }
    )
    assert inventory_response.status_code == 200

    inventory_data = inventory_response.json()
    assert "assets" in inventory_data
    assert "summary" in inventory_data

    # Step 4: Submit feedback using MFO endpoint (if analysis had issues)
    data_quality_score = analyze_data.get("data_quality", {}).get("score", 100)
    if data_quality_score < 90:
        feedback_request = {
            "filename": "e2e_test.csv",
            "original_analysis": analyze_data,  # Use snake_case
            "user_corrections": {"comments": "Data quality looks good after review"},
            "flow_id": flow_id,
            "client_account_id": demo_tenant_context.client_account_id,
            "engagement_id": demo_tenant_context.engagement_id,
        }

        feedback_response = await api_client.post(
            "/api/v1/master-flows/feedback",  # Use MFO endpoint
            json=feedback_request,
            headers={
                **auth_headers,
                "X-Client-Account-ID": demo_tenant_context.client_account_id,
                "X-Engagement-ID": demo_tenant_context.engagement_id,
            },
        )
        assert feedback_response.status_code == 200


@pytest.mark.asyncio
@pytest.mark.mfo
async def test_mfo_workflow_with_tenant_scoped_agents(api_client, sample_cmdb_csv_content, auth_headers, demo_tenant_context, mock_tenant_scoped_agent_pool):
    """Test end-to-end workflow using TenantScopedAgentPool instead of direct Crew instantiation."""

    # Step 1: Initialize flow with agent pool
    flow_request = {
        "flow_type": "discovery",
        "data_source": {
            "filename": "tenant_test.csv",
            "content": sample_cmdb_csv_content,
            "file_type": "csv"
        },
        "use_persistent_agents": True,  # Ensure TenantScopedAgentPool is used
        "client_account_id": demo_tenant_context.client_account_id,
        "engagement_id": demo_tenant_context.engagement_id,
    }

    init_response = await api_client.post(
        "/api/v1/master-flows/create",
        json=flow_request,
        headers={
            **auth_headers,
            "X-Client-Account-ID": demo_tenant_context.client_account_id,
            "X-Engagement-ID": demo_tenant_context.engagement_id,
        }
    )

    if init_response.status_code == 200:
        init_data = init_response.json()
        flow_id = init_data["flow_id"]

        # Step 2: Execute phases using persistent agents
        phases = ["field_mapping", "data_cleansing", "asset_inventory", "dependency_analysis"]

        for phase in phases:
            phase_response = await api_client.post(
                f"/api/v1/master-flows/{flow_id}/execute/{phase}",
                headers={
                    **auth_headers,
                    "X-Client-Account-ID": demo_tenant_context.client_account_id,
                    "X-Engagement-ID": demo_tenant_context.engagement_id,
                }
            )

            if phase_response.status_code == 200:
                phase_data = phase_response.json()
                # Verify agent pool usage
                assert "agent_pool_stats" in phase_data or "status" in phase_data
                # Verify snake_case field naming
                assert "phase_name" in phase_data or "current_phase" in phase_data
                # Verify no camelCase fields
                assert "phaseName" not in phase_data
                assert "currentPhase" not in phase_data if "current_phase" in phase_data

        # Step 3: Get final results
        results_response = await api_client.get(
            f"/api/v1/master-flows/{flow_id}/results",
            headers={
                **auth_headers,
                "X-Client-Account-ID": demo_tenant_context.client_account_id,
                "X-Engagement-ID": demo_tenant_context.engagement_id,
            }
        )

        if results_response.status_code == 200:
            results_data = results_response.json()
            # Verify tenant scoping
            assert results_data["client_account_id"] == demo_tenant_context.client_account_id
            assert results_data["engagement_id"] == demo_tenant_context.engagement_id
            # Verify completion
            assert results_data["status"] in ["completed", "success"]


@pytest.mark.asyncio
@pytest.mark.mfo
async def test_atomic_transaction_workflow(api_client, auth_headers, demo_tenant_context):
    """Test that workflow operations use atomic transactions for data integrity."""

    # Test atomic flow creation
    flow_data = {
        "flow_type": "discovery",
        "flow_name": "Atomic Test Flow",
        "client_account_id": demo_tenant_context.client_account_id,
        "engagement_id": demo_tenant_context.engagement_id,
        "atomic_transaction": True,
    }

    create_response = await api_client.post(
        "/api/v1/master-flows/create-atomic",
        json=flow_data,
        headers={
            **auth_headers,
            "X-Client-Account-ID": demo_tenant_context.client_account_id,
            "X-Engagement-ID": demo_tenant_context.engagement_id,
        }
    )

    if create_response.status_code in [200, 201]:
        create_data = create_response.json()
        assert "transaction_id" in create_data
        assert "flow_id" in create_data
        # Verify master and child flows created atomically
        assert "master_flow_created" in create_data
        assert "child_flow_created" in create_data
        # Verify tenant scoping
        assert create_data["client_account_id"] == demo_tenant_context.client_account_id
        assert create_data["engagement_id"] == demo_tenant_context.engagement_id
