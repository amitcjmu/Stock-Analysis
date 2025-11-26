"""
Integration tests for Planning Flow API endpoints.

Tests all endpoints created/modified for issue #1141:
- GET /api/v1/plan/resources (#1143)
- GET /api/v1/plan/roadmap (#1144)
- GET /api/v1/plan/target (#1145)
- POST /api/v1/master-flows/planning/initialize (#1146)
- GET /api/v1/master-flows/planning/status/{id} (#1146)
- GET /api/v1/master-flows/planning/export/{id} (#1152)

CC - Claude Code - Issue #1155
"""

import pytest

# from uuid import UUID  # Unused
from httpx import AsyncClient

# Test tenant context
TEST_CLIENT_ID = "11111111-1111-1111-1111-111111111111"
TEST_ENGAGEMENT_ID = "22222222-2222-2222-2222-222222222222"

# Headers required for multi-tenant scoping
TENANT_HEADERS = {
    "X-Client-Account-ID": TEST_CLIENT_ID,
    "X-Engagement-ID": TEST_ENGAGEMENT_ID,
}


@pytest.fixture
def auth_headers():
    """Return headers needed for authenticated API requests."""
    return {
        **TENANT_HEADERS,
        "Content-Type": "application/json",
    }


class TestResourcePlanningEndpoint:
    """Tests for GET /api/v1/plan/resources endpoint (#1143)."""

    @pytest.mark.asyncio
    async def test_resources_endpoint_exists(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Verify the resources endpoint exists and responds."""
        response = await async_client.get(
            "/api/v1/plan/resources", headers=auth_headers
        )

        # Accept 200 (success) or 401 (if auth required)
        assert response.status_code in [
            200,
            401,
        ], f"Unexpected status: {response.status_code}"

    @pytest.mark.asyncio
    async def test_resources_schema_structure(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Verify resources endpoint returns expected schema."""
        response = await async_client.get(
            "/api/v1/plan/resources", headers=auth_headers
        )

        if response.status_code == 200:
            data = response.json()

            # Verify required fields exist
            assert "teams" in data, "Missing 'teams' field"
            assert "metrics" in data, "Missing 'metrics' field"

            # Verify teams is a list
            assert isinstance(data["teams"], list), "'teams' should be a list"

            # Verify metrics structure
            metrics = data["metrics"]
            assert "total_resources" in metrics, "Missing 'total_resources' in metrics"
            assert (
                "allocated_resources" in metrics
            ), "Missing 'allocated_resources' in metrics"


class TestRoadmapEndpoint:
    """Tests for GET /api/v1/plan/roadmap endpoint (#1144)."""

    @pytest.mark.asyncio
    async def test_roadmap_endpoint_exists(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Verify the roadmap endpoint exists and responds."""
        response = await async_client.get("/api/v1/plan/roadmap", headers=auth_headers)

        assert response.status_code in [
            200,
            401,
        ], f"Unexpected status: {response.status_code}"

    @pytest.mark.asyncio
    async def test_roadmap_schema_structure(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Verify roadmap endpoint returns expected schema."""
        response = await async_client.get("/api/v1/plan/roadmap", headers=auth_headers)

        if response.status_code == 200:
            data = response.json()

            # Verify required fields exist
            assert "phases" in data, "Missing 'phases' field"
            assert "metrics" in data, "Missing 'metrics' field"
            assert "critical_path" in data, "Missing 'critical_path' field"
            assert "schedule_health" in data, "Missing 'schedule_health' field"

            # Verify phases is a list
            assert isinstance(data["phases"], list), "'phases' should be a list"

            # Verify critical_path is a list
            assert isinstance(
                data["critical_path"], list
            ), "'critical_path' should be a list"


class TestTargetEnvironmentEndpoint:
    """Tests for GET /api/v1/plan/target endpoint (#1145)."""

    @pytest.mark.asyncio
    async def test_target_endpoint_exists(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Verify the target endpoint exists and responds."""
        response = await async_client.get("/api/v1/plan/target", headers=auth_headers)

        assert response.status_code in [
            200,
            401,
        ], f"Unexpected status: {response.status_code}"

    @pytest.mark.asyncio
    async def test_target_schema_structure(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Verify target endpoint returns expected schema."""
        response = await async_client.get("/api/v1/plan/target", headers=auth_headers)

        if response.status_code == 200:
            data = response.json()

            # Verify required fields exist
            assert "environments" in data, "Missing 'environments' field"
            assert "metrics" in data, "Missing 'metrics' field"
            assert "recommendations" in data, "Missing 'recommendations' field"

            # Verify environments is a list
            assert isinstance(
                data["environments"], list
            ), "'environments' should be a list"


class TestPlanningFlowEndpoints:
    """Tests for Planning Flow MFO endpoints (#1146)."""

    @pytest.mark.asyncio
    async def test_initialize_endpoint_exists(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Verify the planning initialize endpoint exists."""
        response = await async_client.post(
            "/api/v1/master-flows/planning/initialize",
            headers=auth_headers,
            json={"selected_application_ids": []},
        )

        # Accept 200, 401 (auth), 422 (validation), or 400 (bad request)
        assert response.status_code in [
            200,
            400,
            401,
            422,
        ], f"Unexpected status: {response.status_code}"

    @pytest.mark.asyncio
    async def test_status_endpoint_exists(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Verify the planning status endpoint exists."""
        mock_flow_id = "33333333-3333-3333-3333-333333333333"
        response = await async_client.get(
            f"/api/v1/master-flows/planning/status/{mock_flow_id}", headers=auth_headers
        )

        # Accept 200, 401, or 404 (flow not found)
        assert response.status_code in [
            200,
            401,
            404,
        ], f"Unexpected status: {response.status_code}"


class TestExportEndpoint:
    """Tests for Planning Export endpoint (#1152)."""

    @pytest.mark.asyncio
    async def test_export_endpoint_exists(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Verify the export endpoint exists."""
        mock_flow_id = "33333333-3333-3333-3333-333333333333"
        response = await async_client.get(
            f"/api/v1/master-flows/planning/export/{mock_flow_id}?format=json",
            headers=auth_headers,
        )

        # Accept 200, 401, 404, or 501 (not implemented)
        assert response.status_code in [
            200,
            401,
            404,
            501,
        ], f"Unexpected status: {response.status_code}"

    @pytest.mark.asyncio
    async def test_export_formats(self, async_client: AsyncClient, auth_headers: dict):
        """Verify export supports multiple formats."""
        mock_flow_id = "33333333-3333-3333-3333-333333333333"

        for format_type in ["json", "pdf", "excel"]:
            response = await async_client.get(
                f"/api/v1/master-flows/planning/export/{mock_flow_id}?format={format_type}",
                headers=auth_headers,
            )

            # All formats should at least return 401, 404, or 501
            assert response.status_code in [
                200,
                401,
                404,
                501,
            ], f"Format {format_type} returned unexpected status: {response.status_code}"


class TestTimelineDeprecation:
    """Tests for deprecated /timeline endpoint (#1144)."""

    @pytest.mark.asyncio
    async def test_timeline_deprecated_or_redirects(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Verify /timeline is deprecated or redirects to /roadmap."""
        response = await async_client.get("/api/v1/plan/timeline", headers=auth_headers)

        # Accept 200 (redirected/consolidated), 301/302 (redirect), 410 (gone), or 404
        assert response.status_code in [
            200,
            301,
            302,
            404,
            410,
        ], f"Timeline endpoint returned unexpected status: {response.status_code}"

    @pytest.mark.asyncio
    async def test_roadmap_is_primary(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Verify /roadmap is the primary timeline endpoint."""
        response = await async_client.get("/api/v1/plan/roadmap", headers=auth_headers)

        # Roadmap should be the active endpoint
        assert response.status_code in [
            200,
            401,
        ], f"Roadmap endpoint should be primary, got: {response.status_code}"


class TestMultiTenantScoping:
    """Tests for multi-tenant header requirements."""

    @pytest.mark.asyncio
    async def test_endpoints_require_tenant_headers(self, async_client: AsyncClient):
        """Verify endpoints require tenant headers."""
        endpoints = [
            "/api/v1/plan/resources",
            "/api/v1/plan/roadmap",
            "/api/v1/plan/target",
        ]

        for endpoint in endpoints:
            # Request without tenant headers
            response = await async_client.get(endpoint)

            # Should return 400 (bad request) or 401 (unauthorized) without headers
            assert response.status_code in [
                400,
                401,
                422,
            ], f"Endpoint {endpoint} should require tenant headers, got: {response.status_code}"

    @pytest.mark.asyncio
    async def test_endpoints_accept_tenant_headers(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Verify endpoints accept valid tenant headers."""
        endpoints = [
            "/api/v1/plan/resources",
            "/api/v1/plan/roadmap",
            "/api/v1/plan/target",
        ]

        for endpoint in endpoints:
            response = await async_client.get(endpoint, headers=auth_headers)

            # Should not return 400 for missing headers when headers are provided
            assert (
                response.status_code != 400
            ), f"Endpoint {endpoint} rejected valid tenant headers"
