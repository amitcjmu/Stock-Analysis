"""
Integration tests for decommission flow endpoints.

Tests all 5 decommission flow management endpoints:
- POST /api/v1/decommission-flow/initialize
- GET /api/v1/decommission-flow/{flow_id}/status
- POST /api/v1/decommission-flow/{flow_id}/resume
- POST /api/v1/decommission-flow/{flow_id}/pause
- POST /api/v1/decommission-flow/{flow_id}/cancel

Reference: Issue #935
Pattern: backend/tests/integration/test_assessment_flow_endpoints.py
"""

import pytest
from uuid import uuid4
from httpx import AsyncClient


class TestDecommissionFlowEndpoints:
    """Integration tests for decommission flow management endpoints."""

    @pytest.fixture
    def auth_headers(self):
        """Mock authentication headers for testing."""
        return {
            "Authorization": "Bearer test_token",
            "X-Client-Account-ID": str(uuid4()),
            "X-Engagement-ID": str(uuid4()),
        }

    @pytest.fixture
    def decommission_request_body(self):
        """Sample request body for decommission flow creation."""
        return {
            "selected_system_ids": [str(uuid4()), str(uuid4())],
            "flow_name": "Test Decommission Flow",
            "decommission_strategy": {
                "priority": "cost_savings",
                "execution_mode": "phased",
                "rollback_enabled": True,
            },
        }

    @pytest.mark.asyncio
    async def test_initialize_decommission_flow_success(
        self, async_client: AsyncClient, auth_headers, decommission_request_body
    ):
        """
        Test successful decommission flow initialization.

        GIVEN a valid decommission request
        WHEN POST /api/v1/decommission-flow/initialize is called
        THEN a new flow is created with status "initialized"
        """
        response = await async_client.post(
            "/api/v1/decommission-flow/initialize",
            headers=auth_headers,
            json=decommission_request_body,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "flow_id" in data
        assert "status" in data
        assert "current_phase" in data
        assert "selected_systems" in data

        # Verify initial state
        assert data["status"] == "initialized"
        assert data["current_phase"] == "decommission_planning"
        assert len(data["selected_systems"]) == 2

    @pytest.mark.asyncio
    async def test_initialize_decommission_flow_requires_auth(
        self, async_client: AsyncClient, decommission_request_body
    ):
        """
        Test that initialization requires authentication.

        GIVEN no authentication headers
        WHEN POST /api/v1/decommission-flow/initialize is called
        THEN a 401/403 error is returned
        """
        response = await async_client.post(
            "/api/v1/decommission-flow/initialize",
            json=decommission_request_body,
        )

        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_initialize_decommission_flow_validates_system_ids(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test validation of system IDs.

        GIVEN an empty system_ids list
        WHEN POST /api/v1/decommission-flow/initialize is called
        THEN a 400 validation error is returned
        """
        invalid_body = {
            "selected_system_ids": [],
            "flow_name": "Invalid Flow",
        }

        response = await async_client.post(
            "/api/v1/decommission-flow/initialize",
            headers=auth_headers,
            json=invalid_body,
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_get_decommission_flow_status_success(
        self, async_client: AsyncClient, auth_headers, decommission_request_body
    ):
        """
        Test successful status retrieval.

        GIVEN an existing decommission flow
        WHEN GET /api/v1/decommission-flow/{flow_id}/status is called
        THEN detailed status information is returned
        """
        # First create a flow
        create_response = await async_client.post(
            "/api/v1/decommission-flow/initialize",
            headers=auth_headers,
            json=decommission_request_body,
        )
        flow_id = create_response.json()["flow_id"]

        # Then get its status
        response = await async_client.get(
            f"/api/v1/decommission-flow/{flow_id}/status",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify status response structure
        assert data["flow_id"] == flow_id
        assert "master_flow_id" in data
        assert "status" in data
        assert "current_phase" in data
        assert "phase_progress" in data
        assert "metrics" in data

        # Verify phase_progress structure (ADR-027 phase names)
        assert "decommission_planning" in data["phase_progress"]
        assert "data_migration" in data["phase_progress"]
        assert "system_shutdown" in data["phase_progress"]

    @pytest.mark.asyncio
    async def test_get_decommission_flow_status_not_found(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test status retrieval for non-existent flow.

        GIVEN a non-existent flow_id
        WHEN GET /api/v1/decommission-flow/{flow_id}/status is called
        THEN a 404 error is returned
        """
        fake_flow_id = str(uuid4())

        response = await async_client.get(
            f"/api/v1/decommission-flow/{fake_flow_id}/status",
            headers=auth_headers,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_pause_decommission_flow_success(
        self, async_client: AsyncClient, auth_headers, decommission_request_body
    ):
        """
        Test successful flow pause.

        GIVEN a running decommission flow
        WHEN POST /api/v1/decommission-flow/{flow_id}/pause is called
        THEN the flow is paused successfully
        """
        # Create a flow
        create_response = await async_client.post(
            "/api/v1/decommission-flow/initialize",
            headers=auth_headers,
            json=decommission_request_body,
        )
        flow_id = create_response.json()["flow_id"]

        # Pause the flow
        response = await async_client.post(
            f"/api/v1/decommission-flow/{flow_id}/pause",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["flow_id"] == flow_id
        assert "status" in data
        assert "message" in data

    @pytest.mark.asyncio
    async def test_resume_decommission_flow_success(
        self, async_client: AsyncClient, auth_headers, decommission_request_body
    ):
        """
        Test successful flow resume.

        GIVEN a paused decommission flow
        WHEN POST /api/v1/decommission-flow/{flow_id}/resume is called
        THEN the flow resumes successfully
        """
        # Create and pause a flow
        create_response = await async_client.post(
            "/api/v1/decommission-flow/initialize",
            headers=auth_headers,
            json=decommission_request_body,
        )
        flow_id = create_response.json()["flow_id"]

        await async_client.post(
            f"/api/v1/decommission-flow/{flow_id}/pause",
            headers=auth_headers,
        )

        # Resume the flow
        resume_body = {"phase": None, "user_input": {}}
        response = await async_client.post(
            f"/api/v1/decommission-flow/{flow_id}/resume",
            headers=auth_headers,
            json=resume_body,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["flow_id"] == flow_id
        assert "status" in data
        assert "current_phase" in data

    @pytest.mark.asyncio
    async def test_cancel_decommission_flow_success(
        self, async_client: AsyncClient, auth_headers, decommission_request_body
    ):
        """
        Test successful flow cancellation.

        GIVEN a running decommission flow
        WHEN POST /api/v1/decommission-flow/{flow_id}/cancel is called
        THEN the flow is cancelled successfully
        """
        # Create a flow
        create_response = await async_client.post(
            "/api/v1/decommission-flow/initialize",
            headers=auth_headers,
            json=decommission_request_body,
        )
        flow_id = create_response.json()["flow_id"]

        # Cancel the flow
        response = await async_client.post(
            f"/api/v1/decommission-flow/{flow_id}/cancel",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["flow_id"] == flow_id
        assert "status" in data
        assert "message" in data

    @pytest.mark.asyncio
    async def test_multi_tenant_isolation(
        self, async_client: AsyncClient, decommission_request_body
    ):
        """
        Test multi-tenant data isolation.

        GIVEN flows created by different tenants
        WHEN a tenant tries to access another tenant's flow
        THEN access is denied (404 not found)
        """
        # Create flow as tenant 1
        tenant1_headers = {
            "Authorization": "Bearer test_token",
            "X-Client-Account-ID": str(uuid4()),
            "X-Engagement-ID": str(uuid4()),
        }

        create_response = await async_client.post(
            "/api/v1/decommission-flow/initialize",
            headers=tenant1_headers,
            json=decommission_request_body,
        )
        flow_id = create_response.json()["flow_id"]

        # Try to access as tenant 2
        tenant2_headers = {
            "Authorization": "Bearer test_token",
            "X-Client-Account-ID": str(uuid4()),  # Different tenant
            "X-Engagement-ID": str(uuid4()),
        }

        response = await async_client.get(
            f"/api/v1/decommission-flow/{flow_id}/status",
            headers=tenant2_headers,
        )

        # Should not be able to access another tenant's flow
        assert response.status_code == 404
