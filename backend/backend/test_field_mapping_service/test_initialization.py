"""
Unit Tests for FieldMappingService Initialization

Tests the FieldMappingService initialization and basic setup.
"""

import uuid
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.services.field_mapping_service import FieldMappingService


class TestFieldMappingServiceInitialization:
    """Test FieldMappingService initialization and basic setup"""

    @pytest.fixture
    def mock_session(self):
        """Create mock database session"""
        session = AsyncMock(spec=AsyncSession)
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        return session

    @pytest.fixture
    def sample_context(self):
        """Create sample request context"""
        return RequestContext(
            client_account_id=uuid.uuid4(),
            engagement_id=uuid.uuid4(),
            user_email="test@example.com",
            current_flow_id=str(uuid.uuid4()),
        )

    @pytest.fixture
    def field_mapping_service(self, mock_session, sample_context):
        """Create FieldMappingService instance"""
        return FieldMappingService(
            db_session=mock_session,
            context=sample_context,
        )

    async def test_initialization_with_valid_parameters(
        self, field_mapping_service, sample_context
    ):
        """Test service initializes correctly with valid parameters"""
        assert field_mapping_service.context == sample_context
        assert field_mapping_service.db_session is not None
        assert (
            field_mapping_service.client_account_id == sample_context.client_account_id
        )
        assert field_mapping_service.engagement_id == sample_context.engagement_id

    async def test_initialization_creates_required_components(
        self, field_mapping_service
    ):
        """Test that initialization creates all required internal components"""
        # The service should have internal components initialized
        assert hasattr(field_mapping_service, "context")
        assert hasattr(field_mapping_service, "db_session")
        assert hasattr(field_mapping_service, "client_account_id")
        assert hasattr(field_mapping_service, "engagement_id")

    async def test_service_health_check_with_valid_setup(self, field_mapping_service):
        """Test service health check returns positive with valid setup"""
        health_status = await field_mapping_service.health_check()

        assert health_status is not None
        assert "status" in health_status
        # Health check should pass with valid setup
        assert health_status["status"] in ["healthy", "ready"]
