"""
Security Tests for Multi-Tenant Isolation

Tests to ensure that clients cannot access each other's data.
This is a CRITICAL security requirement.
"""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.database import AsyncSessionLocal
from app.repositories.crewai_flow_state_extensions_repository import (
    CrewAIFlowStateExtensionsRepository,
)
from app.repositories.discovery_flow_repository import DiscoveryFlowRepository


@pytest.fixture
async def db_session():
    """Create a test database session"""
    async with AsyncSessionLocal() as session:
        yield session


@pytest.fixture
def client1_context():
    """Context for Client 1"""
    return RequestContext(
        client_account_id=str(uuid.uuid4()),
        engagement_id=str(uuid.uuid4()),
        user_id=str(uuid.uuid4()),
    )


@pytest.fixture
def client2_context():
    """Context for Client 2"""
    return RequestContext(
        client_account_id=str(uuid.uuid4()),
        engagement_id=str(uuid.uuid4()),
        user_id=str(uuid.uuid4()),
    )


class TestTenantIsolation:
    """Test suite for multi-tenant isolation"""

    async def test_context_required_for_repository(self, db_session: AsyncSession):
        """Test that repositories require client context"""
        # Should raise ValueError when no client_account_id provided
        with pytest.raises(ValueError, match="SECURITY.*Client account ID is required"):
            DiscoveryFlowRepository(
                db=db_session, client_account_id=None, engagement_id=None
            )

    async def test_discovery_flow_isolation(
        self,
        db_session: AsyncSession,
        client1_context: RequestContext,
        client2_context: RequestContext,
    ):
        """Test that discovery flows are isolated between clients"""
        # Create repositories for each client
        client1_repo = DiscoveryFlowRepository(
            db=db_session,
            client_account_id=client1_context.client_account_id,
            engagement_id=client1_context.engagement_id,
        )

        client2_repo = DiscoveryFlowRepository(
            db=db_session,
            client_account_id=client2_context.client_account_id,
            engagement_id=client2_context.engagement_id,
        )

        # Create a flow for Client 1
        flow1_id = str(uuid.uuid4())
        await client1_repo.create_discovery_flow(
            flow_id=flow1_id, flow_type="primary", description="Client 1 Discovery Flow"
        )

        # Create a flow for Client 2
        flow2_id = str(uuid.uuid4())
        await client2_repo.create_discovery_flow(
            flow_id=flow2_id, flow_type="primary", description="Client 2 Discovery Flow"
        )

        # Client 1 should only see their own flow
        client1_flows = await client1_repo.get_active_flows()
        assert len(client1_flows) == 1
        assert client1_flows[0].flow_id == uuid.UUID(flow1_id)

        # Client 2 should only see their own flow
        client2_flows = await client2_repo.get_active_flows()
        assert len(client2_flows) == 1
        assert client2_flows[0].flow_id == uuid.UUID(flow2_id)

        # Client 1 should NOT be able to access Client 2's flow
        client2_flow_from_client1 = await client1_repo.get_by_flow_id(flow2_id)
        assert client2_flow_from_client1 is None

        # Client 2 should NOT be able to access Client 1's flow
        client1_flow_from_client2 = await client2_repo.get_by_flow_id(flow1_id)
        assert client1_flow_from_client2 is None

    async def test_master_flow_isolation(
        self,
        db_session: AsyncSession,
        client1_context: RequestContext,
        client2_context: RequestContext,
    ):
        """Test that master flows are isolated between clients"""
        # Create repositories for each client
        client1_repo = CrewAIFlowStateExtensionsRepository(
            db=db_session,
            client_account_id=client1_context.client_account_id,
            engagement_id=client1_context.engagement_id,
        )

        client2_repo = CrewAIFlowStateExtensionsRepository(
            db=db_session,
            client_account_id=client2_context.client_account_id,
            engagement_id=client2_context.engagement_id,
        )

        # Create master flows
        flow1_id = str(uuid.uuid4())
        await client1_repo.create_master_flow(
            flow_id=flow1_id, flow_type="discovery", flow_name="Client 1 Master Flow"
        )

        flow2_id = str(uuid.uuid4())
        await client2_repo.create_master_flow(
            flow_id=flow2_id, flow_type="discovery", flow_name="Client 2 Master Flow"
        )

        # Each client should only see their own flows
        client1_active = await client1_repo.get_active_flows()
        assert all(
            f.client_account_id == uuid.UUID(client1_context.client_account_id)
            for f in client1_active
        )

        client2_active = await client2_repo.get_active_flows()
        assert all(
            f.client_account_id == uuid.UUID(client2_context.client_account_id)
            for f in client2_active
        )

        # Cross-client access should fail
        assert await client1_repo.get_by_flow_id(flow2_id) is None
        assert await client2_repo.get_by_flow_id(flow1_id) is None

    async def test_global_query_security(
        self,
        db_session: AsyncSession,
        client1_context: RequestContext,
        client2_context: RequestContext,
    ):
        """Test that global query methods are secured"""
        client1_repo = DiscoveryFlowRepository(
            db=db_session,
            client_account_id=client1_context.client_account_id,
            engagement_id=client1_context.engagement_id,
        )

        client2_repo = DiscoveryFlowRepository(
            db=db_session,
            client_account_id=client2_context.client_account_id,
            engagement_id=client2_context.engagement_id,
        )

        # Create a flow for Client 1
        flow1_id = str(uuid.uuid4())
        await client1_repo.create_discovery_flow(
            flow_id=flow1_id, flow_type="primary", description="Client 1 Flow"
        )

        # Client 2 trying to use global query should fail
        result = await client2_repo.flow_queries.get_by_flow_id_global(flow1_id)
        assert result is None  # Should be denied due to security check

    async def test_context_enforcement_in_queries(self, db_session: AsyncSession):
        """Test that all query methods enforce context"""
        # Try to create repository without context - should fail
        with pytest.raises(ValueError, match="SECURITY"):
            DiscoveryFlowRepository(
                db=db_session, client_account_id=None, engagement_id=None
            )

    async def test_repository_prevents_context_injection(
        self,
        db_session: AsyncSession,
        client1_context: RequestContext,
        client2_context: RequestContext,
    ):
        """Test that repositories prevent context injection attacks"""
        # Create a flow for Client 1
        client1_repo = DiscoveryFlowRepository(
            db=db_session,
            client_account_id=client1_context.client_account_id,
            engagement_id=client1_context.engagement_id,
        )

        flow_id = str(uuid.uuid4())
        await client1_repo.create_discovery_flow(flow_id=flow_id, flow_type="primary")

        # Try to update with Client 2's context - should fail
        client2_repo = DiscoveryFlowRepository(
            db=db_session,
            client_account_id=client2_context.client_account_id,
            engagement_id=client2_context.engagement_id,
        )

        # Attempt to update Client 1's flow from Client 2's repo
        result = await client2_repo.update_phase_completion(
            flow_id=flow_id, phase="data_import", data={"malicious": "update"}
        )

        assert result is None  # Update should fail due to tenant mismatch


class TestAPISecurityEnforcement:
    """Test security enforcement at API layer"""

    async def test_api_requires_context_headers(self):
        """Test that API endpoints require context headers"""
        from fastapi import Request

        from app.api.security_dependencies import SecurityError, get_verified_context

        # Mock request without headers
        request = Request(
            {
                "type": "http",
                "headers": [],
                "method": "GET",
                "url": {"path": "/api/v1/flows"},
            },
            receive=None,
            send=None,
        )

        # Should raise SecurityError
        with pytest.raises(SecurityError, match="Client account context is required"):
            get_verified_context(request)

    async def test_api_validates_uuid_format(self):
        """Test that API validates UUID format in context"""
        from fastapi import Request

        from app.api.security_dependencies import SecurityError, get_verified_context

        # Mock request with invalid UUID
        headers = [
            (b"x-client-account-id", b"not-a-uuid"),
            (b"x-engagement-id", b"also-not-a-uuid"),
        ]

        request = Request(
            {
                "type": "http",
                "headers": headers,
                "method": "GET",
                "url": {"path": "/api/v1/flows"},
            },
            receive=None,
            send=None,
        )

        # Should raise SecurityError for invalid UUID
        with pytest.raises(SecurityError, match="Invalid context format"):
            get_verified_context(request)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
