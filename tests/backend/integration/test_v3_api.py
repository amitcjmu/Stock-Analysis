"""
Integration tests for v3 API
"""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.workflow_state import WorkflowState


@pytest.fixture
async def async_client():
    """Create async HTTP client for testing"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def auth_headers():
    """Mock authentication headers"""
    return {"Authorization": "Bearer test-token", "Content-Type": "application/json"}


@pytest.fixture
def sample_flow_data():
    """Sample flow creation data"""
    return {
        "name": "Test Flow",
        "client_account_id": "test-client-123",
        "engagement_id": "test-engagement-456",
        "description": "Integration test flow",
        "configuration": {
            "auto_progression": True,
            "notification_settings": {"email_updates": True},
        },
    }


@pytest.fixture
async def mock_db_session():
    """Mock database session"""
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.add = AsyncMock()
    session.refresh = AsyncMock()
    return session


class TestV3DiscoveryFlowAPI:
    """Test v3 discovery flow endpoints"""

    @pytest.mark.asyncio
    async def test_create_flow(
        self, async_client: AsyncClient, auth_headers, sample_flow_data
    ):
        """Test creating a new flow"""
        with patch(
            "app.services.crewai_flows.unified_discovery_flow.UnifiedDiscoveryFlow"
        ) as mock_flow_class:
            mock_flow_instance = AsyncMock()
            mock_flow_instance.initialize.return_value = {
                "flow_id": "test-flow-123",
                "status": "initializing",
                "phases": {"initialization": True, "attribute_mapping": False},
            }
            mock_flow_class.return_value = mock_flow_instance

            response = await async_client.post(
                "/api/v3/discovery-flow/flows",
                json=sample_flow_data,
                headers=auth_headers,
            )

            assert response.status_code == 201
            data = response.json()
            assert "flow_id" in data
            assert data["status"] == "initializing"
            assert "phases" in data

    @pytest.mark.asyncio
    async def test_get_flow_status(self, async_client: AsyncClient, auth_headers):
        """Test retrieving flow status"""
        flow_id = str(uuid.uuid4())

        with patch(
            "app.repositories.discovery_v2_repository.DiscoveryV2Repository"
        ) as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_flow_by_id.return_value = WorkflowState(
                id=flow_id,
                flow_id=flow_id,
                status="attribute_mapping",
                client_account_id="test-client-123",
                current_phase="attribute_mapping",
                phases_completed=["initialization"],
                metadata_={"progress": 45},
            )
            mock_repo_class.return_value = mock_repo

            response = await async_client.get(
                f"/api/v3/discovery-flow/flows/{flow_id}", headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert data["flow_id"] == flow_id
            assert data["status"] == "attribute_mapping"
            assert data["current_phase"] == "attribute_mapping"

    @pytest.mark.asyncio
    async def test_update_flow_phase(self, async_client: AsyncClient, auth_headers):
        """Test updating flow phase"""
        flow_id = str(uuid.uuid4())

        with patch(
            "app.repositories.discovery_v2_repository.DiscoveryV2Repository"
        ) as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.update_flow_phase.return_value = True
            mock_repo_class.return_value = mock_repo

            response = await async_client.patch(
                f"/api/v3/discovery-flow/flows/{flow_id}/phase",
                json={
                    "phase": "data_cleansing",
                    "status": "in_progress",
                    "metadata": {"user_initiated": True},
                },
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "message" in data

    @pytest.mark.asyncio
    async def test_list_flows(self, async_client: AsyncClient, auth_headers):
        """Test listing flows for client"""
        with patch(
            "app.repositories.discovery_v2_repository.DiscoveryV2Repository"
        ) as mock_repo_class:
            mock_repo = AsyncMock()
            mock_flows = [
                WorkflowState(
                    id=str(uuid.uuid4()),
                    flow_id=str(uuid.uuid4()),
                    status="completed",
                    client_account_id="test-client-123",
                    current_phase="completed",
                    phases_completed=[
                        "initialization",
                        "attribute_mapping",
                        "data_cleansing",
                    ],
                ),
                WorkflowState(
                    id=str(uuid.uuid4()),
                    flow_id=str(uuid.uuid4()),
                    status="attribute_mapping",
                    client_account_id="test-client-123",
                    current_phase="attribute_mapping",
                    phases_completed=["initialization"],
                ),
            ]
            mock_repo.get_flows_by_client.return_value = mock_flows
            mock_repo_class.return_value = mock_repo

            response = await async_client.get(
                "/api/v3/discovery-flow/flows",
                headers=auth_headers,
                params={"client_account_id": "test-client-123"},
            )

            assert response.status_code == 200
            data = response.json()
            assert "flows" in data
            assert len(data["flows"]) == 2
            assert data["flows"][0]["status"] in ["completed", "attribute_mapping"]

    @pytest.mark.asyncio
    async def test_delete_flow(self, async_client: AsyncClient, auth_headers):
        """Test deleting a flow"""
        flow_id = str(uuid.uuid4())

        with patch(
            "app.repositories.discovery_v2_repository.DiscoveryV2Repository"
        ) as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.delete_flow.return_value = True
            mock_repo_class.return_value = mock_repo

            response = await async_client.delete(
                f"/api/v3/discovery-flow/flows/{flow_id}", headers=auth_headers
            )

            assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_flow_lifecycle(
        self, async_client: AsyncClient, auth_headers, sample_flow_data
    ):
        """Test complete flow lifecycle"""
        flow_id = str(uuid.uuid4())

        # Mock the flow creation and progression
        with patch(
            "app.services.crewai_flows.unified_discovery_flow.UnifiedDiscoveryFlow"
        ) as mock_flow_class:
            with patch(
                "app.repositories.discovery_v2_repository.DiscoveryV2Repository"
            ) as mock_repo_class:
                mock_flow_instance = AsyncMock()
                mock_repo = AsyncMock()

                # 1. Create flow
                mock_flow_instance.initialize.return_value = {
                    "flow_id": flow_id,
                    "status": "initializing",
                    "current_phase": "initialization",
                }
                mock_flow_class.return_value = mock_flow_instance

                create_response = await async_client.post(
                    "/api/v3/discovery-flow/flows",
                    json=sample_flow_data,
                    headers=auth_headers,
                )

                assert create_response.status_code == 201

                # 2. Progress to attribute_mapping
                mock_repo.update_flow_phase.return_value = True
                mock_repo_class.return_value = mock_repo

                progress_response = await async_client.patch(
                    f"/api/v3/discovery-flow/flows/{flow_id}/phase",
                    json={"phase": "attribute_mapping", "status": "in_progress"},
                    headers=auth_headers,
                )

                assert progress_response.status_code == 200

                # 3. Complete to data_cleansing
                complete_response = await async_client.patch(
                    f"/api/v3/discovery-flow/flows/{flow_id}/phase",
                    json={"phase": "data_cleansing", "status": "completed"},
                    headers=auth_headers,
                )

                assert complete_response.status_code == 200

                # 4. Verify final state
                mock_repo.get_flow_by_id.return_value = WorkflowState(
                    id=flow_id,
                    flow_id=flow_id,
                    status="completed",
                    client_account_id="test-client-123",
                    current_phase="data_cleansing",
                    phases_completed=[
                        "initialization",
                        "attribute_mapping",
                        "data_cleansing",
                    ],
                )

                final_response = await async_client.get(
                    f"/api/v3/discovery-flow/flows/{flow_id}", headers=auth_headers
                )

                assert final_response.status_code == 200
                final_data = final_response.json()
                assert final_data["status"] == "completed"
                assert "data_cleansing" in final_data.get("phases_completed", [])

    @pytest.mark.asyncio
    async def test_error_handling_invalid_flow_id(
        self, async_client: AsyncClient, auth_headers
    ):
        """Test error handling for invalid flow ID"""
        invalid_flow_id = "invalid-flow-id"

        with patch(
            "app.repositories.discovery_v2_repository.DiscoveryV2Repository"
        ) as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_flow_by_id.return_value = None
            mock_repo_class.return_value = mock_repo

            response = await async_client.get(
                f"/api/v3/discovery-flow/flows/{invalid_flow_id}", headers=auth_headers
            )

            assert response.status_code == 404
            data = response.json()
            assert "error" in data
            assert "not found" in data["error"].lower()

    @pytest.mark.asyncio
    async def test_authentication_required(self, async_client: AsyncClient):
        """Test that authentication is required"""
        response = await async_client.get("/api/v3/discovery-flow/flows")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_multi_tenant_isolation(
        self, async_client: AsyncClient, auth_headers
    ):
        """Test multi-tenant isolation"""
        with patch(
            "app.repositories.discovery_v2_repository.DiscoveryV2Repository"
        ) as mock_repo_class:
            mock_repo = AsyncMock()

            # Client A's flows
            client_a_flows = [
                WorkflowState(
                    id=str(uuid.uuid4()),
                    flow_id=str(uuid.uuid4()),
                    status="active",
                    client_account_id="client-a",
                    current_phase="attribute_mapping",
                )
            ]

            # Client B's flows
            client_b_flows = [
                WorkflowState(
                    id=str(uuid.uuid4()),
                    flow_id=str(uuid.uuid4()),
                    status="active",
                    client_account_id="client-b",
                    current_phase="data_cleansing",
                )
            ]

            # Mock repository to return client-specific flows
            def mock_get_flows_by_client(client_id):
                if client_id == "client-a":
                    return client_a_flows
                elif client_id == "client-b":
                    return client_b_flows
                return []

            mock_repo.get_flows_by_client.side_effect = mock_get_flows_by_client
            mock_repo_class.return_value = mock_repo

            # Test Client A can only see their flows
            response_a = await async_client.get(
                "/api/v3/discovery-flow/flows",
                headers=auth_headers,
                params={"client_account_id": "client-a"},
            )

            assert response_a.status_code == 200
            data_a = response_a.json()
            assert len(data_a["flows"]) == 1
            assert data_a["flows"][0]["client_account_id"] == "client-a"

            # Test Client B can only see their flows
            response_b = await async_client.get(
                "/api/v3/discovery-flow/flows",
                headers=auth_headers,
                params={"client_account_id": "client-b"},
            )

            assert response_b.status_code == 200
            data_b = response_b.json()
            assert len(data_b["flows"]) == 1
            assert data_b["flows"][0]["client_account_id"] == "client-b"

    @pytest.mark.asyncio
    async def test_flow_state_persistence(
        self, async_client: AsyncClient, auth_headers, sample_flow_data
    ):
        """Test flow state persistence across operations"""
        flow_id = str(uuid.uuid4())

        with patch(
            "app.repositories.discovery_v2_repository.DiscoveryV2Repository"
        ) as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo

            # Create initial state
            initial_state = WorkflowState(
                id=flow_id,
                flow_id=flow_id,
                status="initialization",
                client_account_id="test-client-123",
                current_phase="initialization",
                phases_completed=[],
                metadata_={"created_at": "2024-01-01T00:00:00Z"},
            )

            # Update state after phase progression
            updated_state = WorkflowState(
                id=flow_id,
                flow_id=flow_id,
                status="attribute_mapping",
                client_account_id="test-client-123",
                current_phase="attribute_mapping",
                phases_completed=["initialization"],
                metadata_={
                    "created_at": "2024-01-01T00:00:00Z",
                    "last_updated": "2024-01-01T01:00:00Z",
                    "progress_percentage": 25,
                },
            )

            # Mock repository calls
            mock_repo.get_flow_by_id.side_effect = [initial_state, updated_state]
            mock_repo.update_flow_phase.return_value = True

            # Test initial state retrieval
            response1 = await async_client.get(
                f"/api/v3/discovery-flow/flows/{flow_id}", headers=auth_headers
            )

            assert response1.status_code == 200
            data1 = response1.json()
            assert data1["status"] == "initialization"
            assert data1["current_phase"] == "initialization"
            assert len(data1.get("phases_completed", [])) == 0

            # Update phase
            await async_client.patch(
                f"/api/v3/discovery-flow/flows/{flow_id}/phase",
                json={
                    "phase": "attribute_mapping",
                    "status": "in_progress",
                    "metadata": {"progress_percentage": 25},
                },
                headers=auth_headers,
            )

            # Test updated state retrieval
            response2 = await async_client.get(
                f"/api/v3/discovery-flow/flows/{flow_id}", headers=auth_headers
            )

            assert response2.status_code == 200
            data2 = response2.json()
            assert data2["status"] == "attribute_mapping"
            assert data2["current_phase"] == "attribute_mapping"
            assert "initialization" in data2.get("phases_completed", [])

    @pytest.mark.asyncio
    async def test_concurrent_flow_operations(
        self, async_client: AsyncClient, auth_headers
    ):
        """Test concurrent flow operations don't interfere"""
        flow_id = str(uuid.uuid4())

        with patch(
            "app.repositories.discovery_v2_repository.DiscoveryV2Repository"
        ) as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo

            # Mock concurrent update detection
            mock_repo.update_flow_phase.side_effect = [
                True,
                False,
            ]  # Second update fails due to concurrency

            # Simulate concurrent updates
            update_data = {"phase": "data_cleansing", "status": "in_progress"}

            # First update should succeed
            response1 = await async_client.patch(
                f"/api/v3/discovery-flow/flows/{flow_id}/phase",
                json=update_data,
                headers=auth_headers,
            )

            assert response1.status_code == 200

            # Second concurrent update should handle conflict gracefully
            response2 = await async_client.patch(
                f"/api/v3/discovery-flow/flows/{flow_id}/phase",
                json=update_data,
                headers=auth_headers,
            )

            # Should either succeed or return conflict status
            assert response2.status_code in [200, 409]
