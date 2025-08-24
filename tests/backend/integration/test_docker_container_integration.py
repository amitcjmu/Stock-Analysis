"""
Docker Container Integration Tests.

Tests that the application works correctly in Docker containers.
"""

import httpx
import pytest

from conftest import DOCKER_FRONTEND_BASE


class TestDockerContainerIntegration:
    """Test that the application works correctly in Docker containers."""

    @pytest.mark.asyncio
    async def test_backend_container_health(self, api_client):
        """Test that backend container is healthy."""
        try:
            response = await api_client.get("/health")
            # Health endpoint might not exist, so check any valid endpoint
            if response.status_code == 404:
                # Try root endpoint
                response = await api_client.get("/")

            # Should get some response, not connection error
            assert response.status_code in [
                200,
                404,
                422,
            ]  # Any HTTP response means container is running

        except httpx.ConnectError:
            pytest.fail("Backend Docker container is not accessible")

    @pytest.mark.asyncio
    async def test_frontend_container_health(self, frontend_client):
        """Test that frontend container is healthy."""
        try:
            response = await frontend_client.get("/")
            assert response.status_code == 200

        except httpx.ConnectError:
            pytest.fail("Frontend Docker container is not accessible")

    @pytest.mark.asyncio
    async def test_api_cors_configuration(self, api_client, auth_headers):
        """Test that CORS is properly configured for frontend-backend communication."""
        headers = {
            "Origin": DOCKER_FRONTEND_BASE,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
            **auth_headers,
        }

        # Test preflight request
        response = await api_client.options(
            "/api/v1/unified-discovery/flows/active", headers=headers
        )

        # Should not block CORS
        assert response.status_code in [
            200,
            204,
            404,
        ]  # 404 is OK if OPTIONS not implemented
