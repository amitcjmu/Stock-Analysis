"""
Base test class for Discovery Flow testing.

This module provides a base test class with common setup, utilities, and
helpers for testing the Discovery flow implementation.
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, Optional
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

# Import test fixtures
from tests.fixtures.discovery_flow_fixtures import (
    TEST_CLIENT_ACCOUNT_ID,
    TEST_ENGAGEMENT_ID,
    TEST_USER_ID,
    get_mock_file_content,
)

# Base URL for API endpoints
API_BASE_URL = "/api/v1"


class BaseDiscoveryFlowTest:
    """Base test class for Discovery flow testing."""

    @pytest.fixture(autouse=True)
    async def setup_base(self, db_session: AsyncSession, test_client: TestClient):
        """Set up base test environment."""
        self.db = db_session
        self.client = test_client
        self.base_headers = {
            "X-Client-Account-ID": str(TEST_CLIENT_ACCOUNT_ID),
            "X-Engagement-ID": str(TEST_ENGAGEMENT_ID),
            "X-User-ID": str(TEST_USER_ID),
            "Content-Type": "application/json",
        }

        # Mock services
        self.mock_llm = AsyncMock()
        self.mock_crewai = AsyncMock()
        self.mock_storage = AsyncMock()

        # Set up test data
        await self._setup_test_data()

        yield

        # Cleanup
        await self._cleanup_test_data()

    async def _setup_test_data(self):
        """Set up initial test data in database."""
        # This would typically create test users, client accounts, etc.
        # For now, we'll keep it simple
        pass

    async def _cleanup_test_data(self):
        """Clean up test data from database."""
        # Clean up any test data created
        pass

    def get_auth_headers(self, user_id: Optional[str] = None) -> Dict[str, str]:
        """Get authentication headers for API requests."""
        headers = self.base_headers.copy()
        if user_id:
            headers["X-User-ID"] = user_id
        # In a real test, this might include JWT tokens
        headers["Authorization"] = "Bearer test-token"
        return headers

    async def create_discovery_flow(self) -> Dict[str, Any]:
        """Create a new discovery flow via API."""
        response = self.client.post(
            f"{API_BASE_URL}/unified-discovery/flow/initialize",
            headers=self.get_auth_headers(),
            json={"name": "Test Discovery Flow"},
        )
        assert response.status_code == 200
        return response.json()

    async def upload_file(
        self, flow_id: str, file_content: bytes, filename: str = "test.csv"
    ) -> Dict[str, Any]:
        """Upload a file to the discovery flow."""
        files = {"file": (filename, file_content, "text/csv")}
        response = self.client.post(
            f"{API_BASE_URL}/data-import/store-import",
            headers={
                "X-Client-Account-ID": str(TEST_CLIENT_ACCOUNT_ID),
                "X-Engagement-ID": str(TEST_ENGAGEMENT_ID),
                "X-User-ID": str(TEST_USER_ID),
                "Authorization": "Bearer test-token",
            },
            files=files,
            data={"flow_id": flow_id},
        )
        assert response.status_code in [200, 201]
        return response.json()

    async def get_flow_status(self, flow_id: str) -> Dict[str, Any]:
        """Get the current status of a discovery flow."""
        response = self.client.get(
            f"{API_BASE_URL}/unified-discovery/flow/status/{flow_id}",
            headers=self.get_auth_headers(),
        )
        assert response.status_code == 200
        return response.json()

    async def wait_for_phase(
        self, flow_id: str, phase: str, timeout: int = 30
    ) -> Dict[str, Any]:
        """Wait for a flow to reach a specific phase."""
        start_time = datetime.utcnow()
        while (datetime.utcnow() - start_time).seconds < timeout:
            status = await self.get_flow_status(flow_id)
            if status.get("current_phase") == phase or phase in status.get(
                "phases_completed", []
            ):
                return status
            await asyncio.sleep(1)
        raise TimeoutError(f"Flow did not reach phase {phase} within {timeout} seconds")

    async def stream_sse_events(
        self, flow_id: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream SSE events for a flow."""
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "GET",
                f"http://localhost:8000{API_BASE_URL}/unified-discovery/flow/events/{flow_id}",
                headers=self.get_auth_headers(),
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]  # Remove "data: " prefix
                        if data:
                            yield json.loads(data)

    def assert_agent_decision(self, decision: Dict[str, Any], expected_agent: str):
        """Assert that an agent decision matches expected format."""
        assert "agent" in decision
        assert "decision" in decision
        assert "confidence" in decision
        assert "timestamp" in decision
        assert decision["agent"] == expected_agent
        assert 0 <= decision["confidence"] <= 1

    def assert_flow_state(self, flow_state: Dict[str, Any], expected_status: str):
        """Assert that a flow state matches expected format."""
        assert "flow_id" in flow_state
        assert "status" in flow_state
        assert "current_phase" in flow_state
        assert "phases_completed" in flow_state
        assert flow_state["status"] == expected_status

    async def mock_agent_response(self, agent_name: str, response_data: Dict[str, Any]):
        """Mock a CrewAI agent response."""
        self.mock_crewai.execute.return_value = response_data

    async def simulate_agent_delay(self, delay_seconds: float = 1.0):
        """Simulate agent processing delay."""
        await asyncio.sleep(delay_seconds)

    def create_mock_sse_event(self, event_type: str, data: Dict[str, Any]) -> str:
        """Create a mock SSE event string."""
        return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"

    async def verify_phase_completion(self, flow_id: str, phase: str):
        """Verify that a phase has been completed successfully."""
        status = await self.get_flow_status(flow_id)
        assert phase in status.get("phases_completed", [])

        # Check for phase-specific data
        if phase == "data_import":
            assert "data_import_id" in status
        elif phase == "field_mapping":
            assert "field_mapping_id" in status
        elif phase == "asset_inventory":
            assert "assets_created" in status
        elif phase == "dependency_analysis":
            assert "dependencies_found" in status

    def generate_test_csv(self, num_rows: int = 10) -> bytes:
        """Generate test CSV data with specified number of rows."""
        csv_content = (
            "server_name,ip_address,operating_system,cpu_cores,memory_gb,environment\n"
        )
        for i in range(num_rows):
            csv_content += f"TEST-SERVER-{i:03d},10.0.{i // 256}.{i % 256},"
            csv_content += f"Ubuntu 20.04,{4 + (i % 4) * 4},{16 + (i % 4) * 16},"
            csv_content += f"{'Production' if i % 2 == 0 else 'Development'}\n"
        return csv_content.encode("utf-8")

    async def assert_error_response(self, response, expected_error: str):
        """Assert that a response contains expected error."""
        assert response.status_code >= 400
        error_data = response.json()
        assert "error" in error_data or "detail" in error_data
        error_message = error_data.get("error") or error_data.get("detail")
        assert expected_error in str(error_message).lower()

    @pytest.fixture
    async def mock_deepinfra_llm(self):
        """Mock DeepInfra LLM service."""
        with patch("app.services.deepinfra_llm.DeepInfraLLM") as mock:
            instance = mock.return_value
            instance.agenerate.return_value = AsyncMock(
                return_value=Mock(generations=[[Mock(text="Mocked LLM response")]])
            )
            yield instance

    @pytest.fixture
    async def mock_storage_service(self):
        """Mock storage service for file operations."""
        with patch("app.services.data_import.storage_manager.StorageManager") as mock:
            instance = mock.return_value
            instance.store_file = AsyncMock(return_value="mock-file-id")
            instance.get_file = AsyncMock(return_value=get_mock_file_content())
            yield instance

    @pytest.fixture
    async def mock_crewai_flow(self):
        """Mock CrewAI flow execution."""
        with patch(
            "app.services.crewai_flows.unified_discovery_flow.UnifiedDiscoveryFlow"
        ) as mock:
            instance = mock.return_value
            instance.kickoff = AsyncMock(return_value={"status": "completed"})
            yield instance


class TestHelpers:
    """Additional test helper functions."""

    @staticmethod
    def create_test_user(user_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a test user object."""
        return {
            "user_id": user_id or str(uuid.uuid4()),
            "email": "test@example.com",
            "role": "user",
            "client_account_id": TEST_CLIENT_ACCOUNT_ID,
            "engagement_id": TEST_ENGAGEMENT_ID,
        }

    @staticmethod
    def create_test_file(filename: str, content: str) -> Dict[str, Any]:
        """Create a test file object."""
        return {
            "filename": filename,
            "content": content,
            "size": len(content),
            "mime_type": (
                "text/csv" if filename.endswith(".csv") else "application/json"
            ),
        }

    @staticmethod
    async def poll_until_condition(
        condition_func: callable, timeout: int = 30, poll_interval: float = 0.5
    ) -> Any:
        """Poll until a condition is met or timeout."""
        start_time = datetime.utcnow()
        while (datetime.utcnow() - start_time).seconds < timeout:
            result = await condition_func()
            if result:
                return result
            await asyncio.sleep(poll_interval)
        raise TimeoutError("Condition not met within timeout period")


# Pytest markers for different test categories
def slow_test(func):
    """Mark test as slow (takes > 5 seconds)."""
    return pytest.mark.slow(func)


def integration_test(func):
    """Mark test as integration test."""
    return pytest.mark.integration(func)


def unit_test(func):
    """Mark test as unit test."""
    return pytest.mark.unit(func)


def requires_llm(func):
    """Mark test as requiring LLM service."""
    return pytest.mark.requires_llm(func)


def requires_db(func):
    """Mark test as requiring database."""
    return pytest.mark.requires_db(func)
