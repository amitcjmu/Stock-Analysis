"""
Test Repository No-Commit Operations for Service Registry Pattern

Validates that repositories properly support commit=False parameter
for use with the Service Registry pattern where orchestrators own transactions.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.context_aware_repository import ContextAwareRepository


# Mock secure_setattr to actually set attributes in tests
def mock_secure_setattr(obj, name, value):
    setattr(obj, name, value)


class MockModel:
    """Mock model for testing"""

    # Class-level attributes to simulate SQLAlchemy model
    client_account_id = None
    engagement_id = None
    id = None

    def __init__(self, **kwargs):
        self.id = kwargs.get("id", str(uuid.uuid4()))
        self.client_account_id = kwargs.get("client_account_id")
        self.engagement_id = kwargs.get("engagement_id")
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __setattr__(self, name, value):
        # Allow setting any attribute
        self.__dict__[name] = value


class TestRepositoryNoCommitOperations:
    """Test repository operations with commit=False parameter"""

    @pytest.fixture
    def mock_session(self):
        """Create mock database session"""
        session = AsyncMock(spec=AsyncSession)
        session.add = MagicMock()
        session.delete = AsyncMock()  # Must be AsyncMock for await
        session.commit = AsyncMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        return session

    @pytest.fixture
    def repository(self, mock_session):
        """Create repository instance"""
        return ContextAwareRepository(
            db=mock_session,
            model_class=MockModel,
            client_account_id=str(uuid.uuid4()),
            engagement_id=str(uuid.uuid4()),
        )

    @pytest.mark.asyncio
    @patch("app.core.security.cache_encryption.secure_setattr", mock_secure_setattr)
    async def test_create_with_commit_false(self, repository, mock_session):
        """Test create with commit=False only flushes"""
        # Create with commit=False
        data = {"name": "test_asset", "type": "server"}
        instance = await repository.create(commit=False, **data)

        # Should add to session
        mock_session.add.assert_called_once()

        # Should flush but NOT commit
        mock_session.flush.assert_called_once()
        mock_session.commit.assert_not_called()

        # Should refresh to get DB-generated values
        mock_session.refresh.assert_called_once()

        # Instance should have context applied
        assert instance.client_account_id == repository.client_account_id
        assert instance.engagement_id == repository.engagement_id

    @pytest.mark.asyncio
    @patch("app.core.security.cache_encryption.secure_setattr", mock_secure_setattr)
    async def test_create_with_commit_true(self, repository, mock_session):
        """Test create with commit=True (legacy behavior)"""
        # Create with commit=True (default)
        data = {"name": "test_asset", "type": "server"}
        await repository.create(commit=True, **data)

        # Should add to session
        mock_session.add.assert_called_once()

        # Should commit (legacy behavior)
        mock_session.commit.assert_called_once()
        mock_session.flush.assert_not_called()

        # Should refresh after commit
        mock_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.core.security.cache_encryption.secure_setattr", mock_secure_setattr)
    async def test_create_no_commit_helper(self, repository, mock_session):
        """Test create_no_commit helper method"""
        data = {"name": "test_asset", "type": "server"}
        await repository.create_no_commit(**data)

        # Should flush but NOT commit
        mock_session.flush.assert_called_once()
        mock_session.commit.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.core.security.cache_encryption.secure_setattr", mock_secure_setattr)
    async def test_update_with_commit_false(self, repository, mock_session):
        """Test update with commit=False only flushes"""
        # Mock get_by_id to return an instance
        mock_instance = MockModel(
            id="test-id",
            name="old_name",
            client_account_id=repository.client_account_id,
        )

        with patch.object(repository, "get_by_id", return_value=mock_instance):
            # Update with commit=False
            updated = await repository.update("test-id", commit=False, name="new_name")

            # Should flush but NOT commit
            mock_session.flush.assert_called_once()
            mock_session.commit.assert_not_called()

            # Should refresh to get DB-updated values
            mock_session.refresh.assert_called_once()

            # Instance should be updated
            assert updated.name == "new_name"

    @pytest.mark.asyncio
    @patch("app.core.security.cache_encryption.secure_setattr", mock_secure_setattr)
    async def test_update_with_commit_true(self, repository, mock_session):
        """Test update with commit=True (legacy behavior)"""
        # Mock get_by_id to return an instance
        mock_instance = MockModel(
            id="test-id",
            name="old_name",
            client_account_id=repository.client_account_id,
        )

        with patch.object(repository, "get_by_id", return_value=mock_instance):
            # Update with commit=True (default)
            await repository.update("test-id", commit=True, name="new_name")

            # Should commit (legacy behavior)
            mock_session.commit.assert_called_once()
            mock_session.flush.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.core.security.cache_encryption.secure_setattr", mock_secure_setattr)
    async def test_update_no_commit_helper(self, repository, mock_session):
        """Test update_no_commit helper method"""
        mock_instance = MockModel(id="test-id", name="old_name")

        with patch.object(repository, "get_by_id", return_value=mock_instance):
            await repository.update_no_commit("test-id", name="new_name")

            # Should flush but NOT commit
            mock_session.flush.assert_called_once()
            mock_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_with_commit_false(self, repository, mock_session):
        """Test delete with commit=False only flushes"""
        # Mock get_by_id to return an instance
        mock_instance = MockModel(id="test-id")

        with patch.object(repository, "get_by_id", return_value=mock_instance):
            # Delete with commit=False
            result = await repository.delete("test-id", commit=False)

            assert result is True

            # Should delete from session
            mock_session.delete.assert_called_once_with(mock_instance)

            # Should flush but NOT commit
            mock_session.flush.assert_called_once()
            mock_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_with_commit_true(self, repository, mock_session):
        """Test delete with commit=True (legacy behavior)"""
        # Mock get_by_id to return an instance
        mock_instance = MockModel(id="test-id")

        with patch.object(repository, "get_by_id", return_value=mock_instance):
            # Delete with commit=True (default)
            result = await repository.delete("test-id", commit=True)

            assert result is True

            # Should delete from session
            mock_session.delete.assert_called_once_with(mock_instance)

            # Should commit (legacy behavior)
            mock_session.commit.assert_called_once()
            mock_session.flush.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_no_commit_helper(self, repository, mock_session):
        """Test delete_no_commit helper method"""
        mock_instance = MockModel(id="test-id")

        with patch.object(repository, "get_by_id", return_value=mock_instance):
            result = await repository.delete_no_commit("test-id")

            assert result is True

            # Should flush but NOT commit
            mock_session.flush.assert_called_once()
            mock_session.commit.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.core.security.cache_encryption.secure_setattr", mock_secure_setattr)
    async def test_orchestrator_transaction_pattern(self, mock_session):
        """Test the full orchestrator transaction pattern"""
        # This demonstrates how an orchestrator would use the repository
        repository = ContextAwareRepository(
            db=mock_session,
            model_class=MockModel,
            client_account_id=str(uuid.uuid4()),
            engagement_id=str(uuid.uuid4()),
        )

        # Orchestrator begins transaction
        mock_session.begin = AsyncMock()
        mock_session.rollback = AsyncMock()

        try:
            # Multiple operations without commits
            asset1 = await repository.create(commit=False, name="asset1")
            asset2 = await repository.create(commit=False, name="asset2")

            # Update first asset
            with patch.object(repository, "get_by_id", return_value=asset1):
                await repository.update(asset1.id, commit=False, status="active")

            # Delete second asset
            with patch.object(repository, "get_by_id", return_value=asset2):
                await repository.delete(asset2.id, commit=False)

            # Orchestrator commits once at the end
            await mock_session.commit()

        except Exception:
            # Orchestrator handles rollback
            await mock_session.rollback()
            raise

        # Verify pattern: multiple flushes, single commit
        assert mock_session.flush.call_count == 4  # 2 creates + 1 update + 1 delete
        assert mock_session.commit.call_count == 1  # Only orchestrator commits
        mock_session.rollback.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.core.security.cache_encryption.secure_setattr", mock_secure_setattr)
    async def test_no_commit_operations_preserve_transaction_integrity(
        self, repository, mock_session
    ):
        """Test that no-commit operations preserve transaction integrity"""
        # Create multiple entities in same transaction
        asset1 = await repository.create_no_commit(name="asset1", type="server")
        asset2 = await repository.create_no_commit(name="asset2", type="application")
        asset3 = await repository.create_no_commit(name="asset3", type="database")

        # All should be flushed but not committed
        assert mock_session.flush.call_count == 3
        assert mock_session.commit.call_count == 0

        # All should have context applied
        for asset in [asset1, asset2, asset3]:
            assert asset.client_account_id == repository.client_account_id
            assert asset.engagement_id == repository.engagement_id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
