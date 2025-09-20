"""
Test UUID type consistency across repositories.
"""

import uuid
import pytest
from unittest.mock import AsyncMock, Mock

from app.core.utils.uuid_helpers import ensure_uuid, ensure_uuid_str, UUIDMixin
from app.repositories.crewai_flow_state_extensions_repository import (
    CrewAIFlowStateExtensionsRepository,
)


class TestUUIDHelpers:
    """Test UUID helper utilities."""

    def test_ensure_uuid_with_string(self):
        """Test UUID conversion from string."""
        test_uuid_str = "11111111-1111-1111-1111-111111111111"
        result = ensure_uuid(test_uuid_str)
        assert isinstance(result, uuid.UUID)
        assert str(result) == test_uuid_str

    def test_ensure_uuid_with_uuid(self):
        """Test UUID passthrough."""
        test_uuid = uuid.uuid4()
        result = ensure_uuid(test_uuid)
        assert result == test_uuid

    def test_ensure_uuid_with_none(self):
        """Test UUID handling of None."""
        result = ensure_uuid(None)
        assert result is None

    def test_ensure_uuid_with_invalid_string(self):
        """Test UUID handling of invalid string."""
        result = ensure_uuid("invalid-uuid")
        assert result is None

    def test_ensure_uuid_str_conversion(self):
        """Test UUID to string conversion."""
        test_uuid = uuid.uuid4()
        result = ensure_uuid_str(test_uuid)
        assert isinstance(result, str)
        assert result == str(test_uuid)


class TestRepositoryTypeConsistency:
    """Test repository type consistency."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return AsyncMock()

    def test_crewai_repository_accepts_string_ids(self, mock_db):
        """Test that CrewAI repository accepts string IDs."""
        client_id = "11111111-1111-1111-1111-111111111111"
        engagement_id = "22222222-2222-2222-2222-222222222222"

        # Should not raise exception
        repo = CrewAIFlowStateExtensionsRepository(
            db=mock_db,
            client_account_id=client_id,
            engagement_id=engagement_id
        )

        # Verify internal storage is consistent
        assert isinstance(repo.client_account_id, str)
        assert isinstance(repo.engagement_id, str)

    def test_crewai_repository_accepts_uuid_ids(self, mock_db):
        """Test that CrewAI repository accepts UUID IDs."""
        client_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
        engagement_id = uuid.UUID("22222222-2222-2222-2222-222222222222")

        # Should not raise exception
        repo = CrewAIFlowStateExtensionsRepository(
            db=mock_db,
            client_account_id=client_id,
            engagement_id=engagement_id
        )

        # Verify internal storage is consistent
        assert isinstance(repo.client_account_id, str)
        assert isinstance(repo.engagement_id, str)


class MockRepository(UUIDMixin):
    """Mock repository for testing UUIDMixin."""

    def __init__(self, client_account_id, engagement_id):
        self.client_account_id, self.engagement_id = self._parse_tenant_ids(
            client_account_id, engagement_id
        )


class TestUUIDMixin:
    """Test UUIDMixin functionality."""

    def test_parse_tenant_ids_with_strings(self):
        """Test tenant ID parsing with strings."""
        repo = MockRepository(
            "11111111-1111-1111-1111-111111111111",
            "22222222-2222-2222-2222-222222222222"
        )

        assert isinstance(repo.client_account_id, uuid.UUID)
        assert isinstance(repo.engagement_id, uuid.UUID)

    def test_parse_tenant_ids_with_uuids(self):
        """Test tenant ID parsing with UUIDs."""
        client_uuid = uuid.uuid4()
        engagement_uuid = uuid.uuid4()

        repo = MockRepository(client_uuid, engagement_uuid)

        assert repo.client_account_id == client_uuid
        assert repo.engagement_id == engagement_uuid

    def test_parse_tenant_ids_with_none(self):
        """Test tenant ID parsing with None values uses fallbacks."""
        repo = MockRepository(None, None)

        assert isinstance(repo.client_account_id, uuid.UUID)
        assert isinstance(repo.engagement_id, uuid.UUID)
        # Should use demo fallback values
        assert str(repo.client_account_id) == "11111111-1111-1111-1111-111111111111"
        assert str(repo.engagement_id) == "22222222-2222-2222-2222-222222222222"

    def test_ensure_uuid_method(self):
        """Test _ensure_uuid method raises on invalid input."""
        repo = MockRepository("11111111-1111-1111-1111-111111111111", None)

        # Valid UUID should work
        valid_uuid = repo._ensure_uuid("11111111-1111-1111-1111-111111111111")
        assert isinstance(valid_uuid, uuid.UUID)

        # Invalid UUID should raise
        with pytest.raises(ValueError):
            repo._ensure_uuid("invalid-uuid")