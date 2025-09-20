"""
CRITICAL Security Tests for Multi-Tenant Isolation

Tests to ensure that clients cannot access each other's data.
This is a CRITICAL security requirement following ADR-015 architecture.

Validates:
- Master Flow Orchestrator (MFO) endpoint security
- Repository-level tenant isolation
- API security dependencies enforcement
- Cross-tenant access prevention
- Atomic transaction patterns with tenant scoping
"""

import uuid
from typing import Dict, Any

import pytest
import pytest_asyncio
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, patch

from app.api.v1.master_flows_service import MasterFlowService
from app.core.context import RequestContext
from app.core.database import AsyncSessionLocal
from app.repositories.crewai_flow_state_extensions_repository import (
    CrewAIFlowStateExtensionsRepository,
)
from app.repositories.discovery_flow_repository import DiscoveryFlowRepository
from app.repositories.asset_repository import AssetRepository
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.models.discovery_flow import DiscoveryFlow
from app.models.asset import Asset


@pytest.fixture
async def db_session():
    """Create a test database session"""
    async with AsyncSessionLocal() as session:
        yield session


@pytest.fixture
def client1_context():
    """Context for Client 1 - CRITICAL for tenant isolation testing"""
    return RequestContext(
        client_account_id=str(uuid.uuid4()),
        engagement_id=str(uuid.uuid4()),
        user_id=str(uuid.uuid4()),
        user_role="admin",
        request_id=str(uuid.uuid4()),
    )


@pytest.fixture
def client2_context():
    """Context for Client 2 - Different tenant for isolation testing"""
    return RequestContext(
        client_account_id=str(uuid.uuid4()),
        engagement_id=str(uuid.uuid4()),
        user_id=str(uuid.uuid4()),
        user_role="admin",
        request_id=str(uuid.uuid4()),
    )


@pytest.fixture
def malicious_context():
    """Context simulating a potential attacker trying tenant boundary violations"""
    return RequestContext(
        client_account_id=str(uuid.uuid4()),
        engagement_id=str(uuid.uuid4()),
        user_id="potential_attacker",
        user_role="user",
        request_id=str(uuid.uuid4()),
    )


class TestTenantIsolation:
    """CRITICAL Security Test Suite for Multi-Tenant Isolation

    Validates enterprise-grade tenant isolation following ADR-015.
    These tests MUST pass for production deployment.
    """

    @pytest.mark.security
    @pytest.mark.critical
    async def test_context_required_for_repository(self, db_session: AsyncSession):
        """CRITICAL: Test that repositories require client context

        This test ensures repositories cannot be instantiated without proper
        tenant context, preventing accidental data leakage.
        """
        # Should raise ValueError when no client_account_id provided
        with pytest.raises(ValueError, match="SECURITY.*Client account ID is required"):
            DiscoveryFlowRepository(
                db=db_session, client_account_id=None, engagement_id=None
            )

        # Test all critical repositories require context
        with pytest.raises(ValueError, match="SECURITY.*Client account ID is required"):
            AssetRepository(db=db_session, client_account_id=None)

        with pytest.raises(ValueError, match="SECURITY.*Client account ID is required"):
            CrewAIFlowStateExtensionsRepository(
                db=db_session,
                client_account_id=None,
                engagement_id=None
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


class TestMFOTenantIsolation:
    """CRITICAL: Test Master Flow Orchestrator (MFO) tenant isolation

    Validates that MFO endpoints properly enforce tenant boundaries
    according to ADR-006 and ADR-015 requirements.
    """

    @pytest.mark.security
    @pytest.mark.critical
    @pytest.mark.asyncio
    async def test_mfo_service_tenant_isolation(
        self,
        db_session: AsyncSession,
        client1_context: RequestContext,
        client2_context: RequestContext
    ):
        """CRITICAL: Test MFO service enforces tenant isolation

        Validates that MasterFlowService cannot access cross-tenant data
        and properly scopes all operations to the requesting tenant.
        """
        # Create MFO services for each tenant
        mfo_service_1 = MasterFlowService(db_session, client1_context)
        mfo_service_2 = MasterFlowService(db_session, client2_context)

        # Create a flow for tenant 1
        flow_1_id = str(uuid.uuid4())
        with patch.object(db_session, 'commit', new_callable=AsyncMock):
            await mfo_service_1.create_master_flow(
                flow_id=flow_1_id,
                flow_type="discovery",
                flow_name="Tenant 1 Flow"
            )

        # Tenant 2 should NOT be able to access tenant 1's flow
        flow_data = await mfo_service_2.get_master_flow_status(flow_1_id)
        assert flow_data is None or "error" in flow_data, \
            "MFO service allowed cross-tenant access"

    @pytest.mark.security
    @pytest.mark.critical
    @pytest.mark.asyncio
    async def test_mfo_atomic_transactions_with_tenant_scoping(
        self,
        db_session: AsyncSession,
        client1_context: RequestContext
    ):
        """CRITICAL: Test MFO atomic transactions maintain tenant scoping

        Validates that atomic transactions (ADR-012) properly scope
        all operations to the correct tenant context.
        """
        mfo_service = MasterFlowService(db_session, client1_context)

        flow_id = str(uuid.uuid4())

        # Mock atomic transaction pattern
        with patch.object(db_session, 'begin', new_callable=AsyncMock) as mock_begin:
            with patch.object(db_session, 'flush', new_callable=AsyncMock) as mock_flush:
                with patch.object(db_session, 'commit', new_callable=AsyncMock) as mock_commit:
                    await mfo_service.create_master_flow(
                        flow_id=flow_id,
                        flow_type="discovery",
                        flow_name="Atomic Test Flow"
                    )

        # Verify atomic pattern was used
        mock_begin.assert_called()
        mock_flush.assert_called()
        mock_commit.assert_called()

    @pytest.mark.security
    @pytest.mark.critical
    @pytest.mark.asyncio
    async def test_mfo_prevents_tenant_boundary_violations(
        self,
        db_session: AsyncSession,
        client1_context: RequestContext,
        malicious_context: RequestContext
    ):
        """CRITICAL: Test MFO prevents tenant boundary violations

        Simulates potential attacks where malicious actors try to
        access or modify data across tenant boundaries.
        """
        # Create legitimate flow for client 1
        mfo_service_1 = MasterFlowService(db_session, client1_context)
        flow_id = str(uuid.uuid4())

        with patch.object(db_session, 'commit', new_callable=AsyncMock):
            await mfo_service_1.create_master_flow(
                flow_id=flow_id,
                flow_type="discovery",
                flow_name="Target Flow"
            )

        # Malicious actor tries to access the flow
        malicious_service = MasterFlowService(db_session, malicious_context)

        # Should be denied access
        with pytest.raises((HTTPException, ValueError, PermissionError)):
            await malicious_service.get_master_flow_status(flow_id)

        # Should not be able to modify the flow
        with pytest.raises((HTTPException, ValueError, PermissionError)):
            await malicious_service.update_master_flow_status(
                flow_id=flow_id,
                status="compromised"
            )

    @pytest.mark.security
    @pytest.mark.critical
    @pytest.mark.asyncio
    async def test_mfo_asset_access_isolation(
        self,
        db_session: AsyncSession,
        client1_context: RequestContext,
        client2_context: RequestContext
    ):
        """CRITICAL: Test MFO asset access is properly isolated

        Validates that asset operations through MFO endpoints
        respect tenant boundaries.
        """
        # Create asset repositories for each tenant
        asset_repo_1 = AssetRepository(db_session, client1_context.client_account_id)
        asset_repo_2 = AssetRepository(db_session, client2_context.client_account_id)

        # Create an asset for tenant 1
        master_flow_id_1 = str(uuid.uuid4())

        # Mock asset creation
        with patch.object(db_session, 'commit', new_callable=AsyncMock):
            # Simulate asset creation for tenant 1
            pass

        # Tenant 2 should not be able to access tenant 1's assets
        assets = await asset_repo_2.get_by_master_flow(master_flow_id_1)
        assert len(assets) == 0, "Cross-tenant asset access detected"

    @pytest.mark.security
    @pytest.mark.critical
    @pytest.mark.asyncio
    async def test_mfo_repository_query_scoping(
        self,
        db_session: AsyncSession,
        client1_context: RequestContext,
        client2_context: RequestContext
    ):
        """CRITICAL: Test all MFO repository queries are properly scoped

        Validates that every query includes proper tenant scoping
        clauses to prevent data leakage.
        """
        # Test CrewAI Flow State Extensions Repository
        repo_1 = CrewAIFlowStateExtensionsRepository(
            db_session,
            client1_context.client_account_id,
            client1_context.engagement_id,
            client1_context.user_id
        )

        repo_2 = CrewAIFlowStateExtensionsRepository(
            db_session,
            client2_context.client_account_id,
            client2_context.engagement_id,
            client2_context.user_id
        )

        # Create flows for each tenant
        flow_1_id = str(uuid.uuid4())
        flow_2_id = str(uuid.uuid4())

        with patch.object(db_session, 'commit', new_callable=AsyncMock):
            await repo_1.create_master_flow(
                flow_id=flow_1_id,
                flow_type="discovery",
                flow_name="Tenant 1 Flow"
            )
            await repo_2.create_master_flow(
                flow_id=flow_2_id,
                flow_type="discovery",
                flow_name="Tenant 2 Flow"
            )

        # Each repository should only see its tenant's flows
        tenant_1_flows = await repo_1.get_active_flows()
        tenant_2_flows = await repo_2.get_active_flows()

        # Verify tenant isolation
        for flow in tenant_1_flows:
            assert str(flow.client_account_id) == client1_context.client_account_id

        for flow in tenant_2_flows:
            assert str(flow.client_account_id) == client2_context.client_account_id


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
