"""
Integration tests for the flows API endpoint
Tests real API calls with authentication and multi-tenant headers
"""

import uuid
from datetime import datetime

import bcrypt
import pytest
from app.models import User
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


# Try to import test utils, skip if not available
try:
    from tests.utils import create_test_client, create_test_engagement, create_test_user
except ImportError:
    # Define minimal test helpers if utils not available
    async def create_test_user(db, email, password):
        user = User(
            email=email,
            password_hash=get_password_hash(password),
            is_active=True,
            status="active",
        )
        db.add(user)
        await db.commit()
        return user

    async def create_test_client(db, name):
        # Minimal implementation
        pass

    async def create_test_engagement(db, client_id, name):
        # Minimal implementation
        pass


@pytest.mark.asyncio
class TestFlowsEndpointIntegration:
    """Test the flows endpoint with real database and API calls"""

    async def test_list_flows_empty_database(
        self, client: AsyncClient, db: AsyncSession, auth_headers: dict
    ):
        """Test listing flows when no flows exist"""
        response = await client.get(
            "/api/v1/flows/?flowType=discovery", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "flows" in data
        assert data["flows"] == []
        assert data["total"] == 0

    async def test_list_flows_with_existing_flows(
        self, client: AsyncClient, db: AsyncSession, auth_headers: dict
    ):
        """Test listing flows with existing flows in database"""
        # Create test flows
        test_flow = CrewAIFlowStateExtensions(
            flow_id=uuid.uuid4(),
            client_account_id=uuid.UUID(auth_headers["X-Client-Account-ID"]),
            engagement_id=uuid.UUID(auth_headers["X-Engagement-ID"]),
            user_id=auth_headers["X-User-ID"],
            flow_type="discovery",
            flow_name="Test Discovery Flow",
            flow_status="running",
            flow_configuration={"test": "config"},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(test_flow)
        await db.commit()

        # Test API call
        response = await client.get(
            "/api/v1/flows/?flowType=discovery", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["flows"]) == 1
        assert data["flows"][0]["flow_type"] == "discovery"
        assert data["flows"][0]["flow_name"] == "Test Discovery Flow"
        assert "created_by" in data["flows"][0]
        assert "metadata" in data["flows"][0]
        assert isinstance(data["flows"][0]["metadata"], dict)

    async def test_list_flows_handles_missing_fields(
        self, client: AsyncClient, db: AsyncSession, auth_headers: dict
    ):
        """Test that listing flows handles database records with missing optional fields"""
        # Create minimal flow
        test_flow = CrewAIFlowStateExtensions(
            flow_id=uuid.uuid4(),
            client_account_id=uuid.UUID(auth_headers["X-Client-Account-ID"]),
            engagement_id=uuid.UUID(auth_headers["X-Engagement-ID"]),
            user_id=auth_headers["X-User-ID"],
            flow_type="assessment",
            flow_status="initialized",
        )
        db.add(test_flow)
        await db.commit()

        # Test API call
        response = await client.get("/api/v1/flows/", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data["flows"]) > 0

        # Check all required fields are present with defaults
        flow = data["flows"][0]
        assert flow["flow_name"] is None
        assert flow["created_by"] is not None  # Should default to user_id
        assert flow["configuration"] == {}
        assert flow["metadata"] == {}
        assert flow["current_phase"] is None
        assert flow["progress_percentage"] == 0.0

    async def test_get_flow_status(
        self, client: AsyncClient, db: AsyncSession, auth_headers: dict
    ):
        """Test getting individual flow status"""
        # Create test flow
        flow_id = uuid.uuid4()
        test_flow = CrewAIFlowStateExtensions(
            flow_id=flow_id,
            client_account_id=uuid.UUID(auth_headers["X-Client-Account-ID"]),
            engagement_id=uuid.UUID(auth_headers["X-Engagement-ID"]),
            user_id=auth_headers["X-User-ID"],
            flow_type="discovery",
            flow_status="running",
            flow_configuration={"source": "test"},
        )
        db.add(test_flow)
        await db.commit()

        # Test API call
        response = await client.get(
            f"/api/v1/flows/{flow_id}/status", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["flow_id"] == str(flow_id)
        assert data["flow_type"] == "discovery"
        assert data["status"] == "running"
        assert "execution_history" in data
        assert "current_state" in data
        assert "performance_metrics" in data

    async def test_list_flows_with_status_filter(
        self, client: AsyncClient, db: AsyncSession, auth_headers: dict
    ):
        """Test filtering flows by status"""
        # Create flows with different statuses
        for status in ["running", "completed", "failed"]:
            test_flow = CrewAIFlowStateExtensions(
                flow_id=uuid.uuid4(),
                client_account_id=uuid.UUID(auth_headers["X-Client-Account-ID"]),
                engagement_id=uuid.UUID(auth_headers["X-Engagement-ID"]),
                user_id=auth_headers["X-User-ID"],
                flow_type="discovery",
                flow_status=status,
            )
            db.add(test_flow)
        await db.commit()

        # Test filtering by status
        response = await client.get(
            "/api/v1/flows/?status=running", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert all(flow["status"] == "running" for flow in data["flows"])

    async def test_flows_endpoint_requires_authentication(self, client: AsyncClient):
        """Test that flows endpoint requires authentication"""
        response = await client.get("/api/v1/flows/")
        assert response.status_code == 401

    async def test_flows_endpoint_requires_tenant_headers(
        self, client: AsyncClient, auth_token: str
    ):
        """Test that flows endpoint requires multi-tenant headers"""
        response = await client.get(
            "/api/v1/flows/", headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 400  # Should fail without tenant headers


@pytest.fixture
async def auth_headers(db: AsyncSession) -> dict:
    """Create authenticated headers with proper UUIDs"""
    # Create test user
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        hashed_password=get_password_hash("testpassword"),
        full_name="Test User",
        is_active=True,
    )
    db.add(user)

    # Create test client and engagement
    client = await create_test_client(db, "Test Client")
    engagement = await create_test_engagement(db, client.id, "Test Engagement")

    await db.commit()

    # Generate auth token (simplified for testing)
    # In real tests, this would use the actual auth flow
    auth_token = "test_token_123"

    return {
        "Authorization": f"Bearer {auth_token}",
        "X-Client-Account-ID": str(client.id),
        "X-Engagement-ID": str(engagement.id),
        "X-User-ID": str(user.id),
    }


@pytest.fixture
async def auth_token() -> str:
    """Get a test auth token"""
    return "test_token_123"
