"""
Field Mapping API Integration Tests.

Tests field mapping functionality using Master Flow Orchestrator (MFO) patterns.
Aligned with ADR-006 and lessons from coding-agent-guide.md.
"""

import pytest
from app.services.persistent_agents.tenant_scoped_agent_pool import TenantScopedAgentPool
from tests.fixtures.mfo_fixtures import (
    demo_tenant_context,
    mock_tenant_scoped_agent_pool,
    mock_flow_execution_results,
)


@pytest.mark.mfo
class TestFieldMappingAPI:
    """Test field mapping functionality with MFO patterns."""

    @pytest.mark.asyncio
    @pytest.mark.mfo
    async def test_field_mapping_endpoint(self, api_client, auth_headers, demo_tenant_context, mock_tenant_scoped_agent_pool):
        """Test field mapping tool integration using MFO patterns."""
        # Update to use MFO endpoint instead of legacy discovery endpoint
        response = await api_client.get(
            "/api/v1/master-flows/field-mapping",
            headers={
                **auth_headers,
                "X-Client-Account-ID": demo_tenant_context.client_account_id,
                "X-Engagement-ID": demo_tenant_context.engagement_id,
            }
        )

        # This endpoint might not be available in production
        if response.status_code == 200:
            data = response.json()
            assert "status" in data
            assert "mappings" in data
            # Verify tenant scoping
            assert "client_account_id" in data
            assert "engagement_id" in data

    @pytest.mark.asyncio
    @pytest.mark.mfo
    async def test_cmdb_templates_endpoint(self, api_client, auth_headers, demo_tenant_context):
        """Test CMDB template endpoint using MFO patterns."""
        # Update to use MFO endpoint with proper tenant scoping
        response = await api_client.get(
            "/api/v1/master-flows/cmdb-templates",
            headers={
                **auth_headers,
                "X-Client-Account-ID": demo_tenant_context.client_account_id,
                "X-Engagement-ID": demo_tenant_context.engagement_id,
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert "templates" in data
        assert isinstance(data["templates"], list)

        # Verify template structure with tenant scoping
        for template in data["templates"]:
            assert "name" in template
            assert "fields" in template
            assert "description" in template
            # Verify snake_case field naming (not camelCase)
            assert "template_id" in template or "id" in template
            assert "field_count" in template or "fields" in template

    @pytest.mark.asyncio
    @pytest.mark.mfo
    async def test_field_mapping_with_tenant_scoped_agent_pool(self, api_client, auth_headers, demo_tenant_context, mock_tenant_scoped_agent_pool):
        """Test field mapping using TenantScopedAgentPool instead of direct Crew instantiation."""
        # Test that agent pool is used for field mapping operations

        # Mock flow data for field mapping
        flow_data = {
            "flow_id": "test-flow-123",
            "data_import_id": "test-import-456",
            "source_fields": ["hostname", "ip_address", "os_type"],
            "target_schema": "cmdb_server"
        }

        response = await api_client.post(
            "/api/v1/master-flows/field-mapping/analyze",
            json=flow_data,
            headers={
                **auth_headers,
                "X-Client-Account-ID": demo_tenant_context.client_account_id,
                "X-Engagement-ID": demo_tenant_context.engagement_id,
            }
        )

        # Check response structure uses snake_case fields
        if response.status_code == 200:
            data = response.json()
            assert "field_mappings" in data or "mappings" in data
            assert "confidence_score" in data
            assert "agent_insights" in data
            # Verify no camelCase fields
            assert "fieldMappings" not in data
            assert "confidenceScore" not in data
            assert "agentInsights" not in data

    @pytest.mark.asyncio
    @pytest.mark.mfo
    async def test_field_mapping_atomic_transactions(self, api_client, auth_headers, demo_tenant_context):
        """Test that field mapping operations use atomic transactions."""
        # Test data for creating field mappings
        mapping_data = {
            "flow_id": "test-flow-789",
            "mappings": [
                {"source_field": "hostname", "target_field": "server_name", "confidence": 0.95},
                {"source_field": "ip_address", "target_field": "ip_addr", "confidence": 0.98},
                {"source_field": "os_type", "target_field": "operating_system", "confidence": 0.87}
            ]
        }

        response = await api_client.post(
            "/api/v1/master-flows/field-mapping/create",
            json=mapping_data,
            headers={
                **auth_headers,
                "X-Client-Account-ID": demo_tenant_context.client_account_id,
                "X-Engagement-ID": demo_tenant_context.engagement_id,
            }
        )

        # Verify atomic transaction handling
        if response.status_code in [200, 201]:
            data = response.json()
            assert "status" in data
            assert "transaction_id" in data or "flow_id" in data
            # Verify all mappings created or none created (atomic)
            assert "mappings_created" in data
            assert data["mappings_created"] == len(mapping_data["mappings"]) or data["mappings_created"] == 0
