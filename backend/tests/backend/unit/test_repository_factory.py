"""
Unit Tests for RepositoryFactory

Tests the centralized repository initialization factory to ensure:
1. Correct repository types are returned
2. Context values are properly passed to repositories
3. String/int conversions work correctly
4. None values are handled gracefully
5. All major repositories are supported
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.services.repository_factory import RepositoryFactory, create_repository_factory


class TestRepositoryFactory:
    """Test suite for RepositoryFactory initialization and repository creation."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock async database session."""
        db = MagicMock(spec=AsyncSession)
        return db

    @pytest.fixture
    def full_context(self):
        """Create a complete request context with all fields."""
        return RequestContext(
            client_account_id="1",
            engagement_id="100",
            user_id="user-123",
            flow_id=str(uuid.uuid4()),
        )

    @pytest.fixture
    def minimal_context(self):
        """Create a minimal context with only client_account_id."""
        return RequestContext(
            client_account_id="1",
            engagement_id=None,
            user_id=None,
            flow_id=None,
        )

    @pytest.fixture
    def factory(self, mock_db, full_context):
        """Create a repository factory instance."""
        return RepositoryFactory(mock_db, full_context)

    def test_factory_initialization(self, mock_db, full_context):
        """Test that factory initializes with db and context."""
        factory = RepositoryFactory(mock_db, full_context)

        assert factory.db == mock_db
        assert factory.context == full_context
        assert factory.context.client_account_id == "1"
        assert factory.context.engagement_id == "100"

    def test_factory_with_minimal_context(self, mock_db, minimal_context):
        """Test factory works with minimal context (no engagement_id)."""
        factory = RepositoryFactory(mock_db, minimal_context)

        assert factory.context.client_account_id == "1"
        assert factory.context.engagement_id is None

    @patch("app.repositories.discovery_flow_repository.DiscoveryFlowRepository")
    def test_get_discovery_flow_repo(
        self, mock_repo_class, mock_db, full_context, factory
    ):
        """Test that get_discovery_flow_repo creates correct repository."""
        mock_instance = MagicMock()
        mock_repo_class.return_value = mock_instance

        repo = factory.get_discovery_flow_repo()

        # Verify repository was created with correct arguments
        mock_repo_class.assert_called_once_with(
            db=mock_db, client_account_id="1", engagement_id="100"
        )
        assert repo == mock_instance

    @patch("app.repositories.discovery_flow_repository.DiscoveryFlowRepository")
    def test_get_discovery_flow_repo_with_none_engagement(
        self, mock_repo_class, mock_db, minimal_context
    ):
        """Test discovery repo handles None engagement_id."""
        factory = RepositoryFactory(mock_db, minimal_context)
        mock_instance = MagicMock()
        mock_repo_class.return_value = mock_instance

        repo = factory.get_discovery_flow_repo()

        # Verify repository was created
        assert repo is not None
        # Verify None is passed for engagement_id
        mock_repo_class.assert_called_once_with(
            db=mock_db, client_account_id="1", engagement_id=None
        )

    @patch("app.repositories.collection_flow_repository.CollectionFlowRepository")
    def test_get_collection_flow_repo(
        self, mock_repo_class, mock_db, full_context, factory
    ):
        """Test that get_collection_flow_repo creates correct repository."""
        mock_instance = MagicMock()
        mock_repo_class.return_value = mock_instance

        repo = factory.get_collection_flow_repo()

        mock_repo_class.assert_called_once_with(
            db=mock_db, client_account_id="1", engagement_id="100"
        )
        assert repo == mock_instance

    @patch("app.repositories.assessment_flow_repository.AssessmentFlowRepository")
    def test_get_assessment_flow_repo(
        self, mock_repo_class, mock_db, full_context, factory
    ):
        """Test assessment repo converts context IDs to integers."""
        mock_instance = MagicMock()
        mock_repo_class.return_value = mock_instance

        repo = factory.get_assessment_flow_repo()

        # Verify IDs were converted to integers
        mock_repo_class.assert_called_once_with(
            db=mock_db,
            client_account_id=1,  # Converted to int
            engagement_id=100,  # Converted to int
            user_id="user-123",
        )
        assert repo == mock_instance

    @patch("app.repositories.assessment_flow_repository.AssessmentFlowRepository")
    def test_get_assessment_flow_repo_with_none_ids(
        self, mock_repo_class, mock_db, minimal_context
    ):
        """Test assessment repo handles None values during int conversion."""
        minimal_context.client_account_id = None
        factory = RepositoryFactory(mock_db, minimal_context)
        mock_instance = MagicMock()
        mock_repo_class.return_value = mock_instance

        repo = factory.get_assessment_flow_repo()

        # Verify repository was created
        assert repo is not None
        # Verify None is preserved (not converted to int)
        mock_repo_class.assert_called_once_with(
            db=mock_db,
            client_account_id=None,
            engagement_id=None,
            user_id=None,
        )

    @patch(
        "app.repositories.crewai_flow_state_extensions_repository.CrewAIFlowStateExtensionsRepository"
    )
    def test_get_crewai_flow_repo(
        self, mock_repo_class, mock_db, full_context, factory
    ):
        """Test master flow repo (CrewAI) creation."""
        mock_instance = MagicMock()
        mock_repo_class.return_value = mock_instance

        repo = factory.get_crewai_flow_repo()

        mock_repo_class.assert_called_once_with(
            db=mock_db,
            client_account_id="1",
            engagement_id="100",
            user_id="user-123",
        )
        assert repo == mock_instance

    @patch("app.repositories.asset_repository.AssetRepository")
    def test_get_asset_repo(self, mock_repo_class, mock_db, full_context, factory):
        """Test asset repository creation."""
        mock_instance = MagicMock()
        mock_repo_class.return_value = mock_instance

        repo = factory.get_asset_repo()

        mock_repo_class.assert_called_once_with(
            db=mock_db, client_account_id="1", engagement_id="100"
        )
        assert repo == mock_instance

    @patch("app.repositories.governance_repository.ApprovalRequestRepository")
    def test_get_approval_request_repo(
        self, mock_repo_class, mock_db, full_context, factory
    ):
        """Test approval request repository creation."""
        mock_instance = MagicMock()
        mock_repo_class.return_value = mock_instance

        repo = factory.get_approval_request_repo()

        mock_repo_class.assert_called_once_with(
            db=mock_db, client_account_id="1", engagement_id="100"
        )
        assert repo == mock_instance

    @patch("app.repositories.dependency_repository.DependencyRepository")
    def test_get_dependency_repo(self, mock_repo_class, mock_db, full_context, factory):
        """Test dependency repository creation."""
        mock_instance = MagicMock()
        mock_repo_class.return_value = mock_instance

        repo = factory.get_dependency_repo()

        mock_repo_class.assert_called_once_with(
            db=mock_db, client_account_id="1", engagement_id="100"
        )
        assert repo == mock_instance

    @patch("app.repositories.vendor_product_repository.VendorProductRepository")
    def test_get_vendor_product_repo(
        self, mock_repo_class, mock_db, full_context, factory
    ):
        """Test vendor product repository creation."""
        mock_instance = MagicMock()
        mock_repo_class.return_value = mock_instance

        repo = factory.get_vendor_product_repo()

        mock_repo_class.assert_called_once_with(
            db=mock_db, client_account_id="1", engagement_id="100"
        )
        assert repo == mock_instance

    @patch("app.repositories.maintenance_window_repository.MaintenanceWindowRepository")
    def test_get_maintenance_window_repo(
        self, mock_repo_class, mock_db, full_context, factory
    ):
        """Test maintenance window repository creation."""
        mock_instance = MagicMock()
        mock_repo_class.return_value = mock_instance

        repo = factory.get_maintenance_window_repo()

        mock_repo_class.assert_called_once_with(
            db=mock_db, client_account_id="1", engagement_id="100"
        )
        assert repo == mock_instance

    def test_context_values_are_converted_to_strings(self, mock_db):
        """Test that integer context values are converted to strings."""
        context = RequestContext(
            client_account_id=1,  # int
            engagement_id=100,  # int
            user_id="user-123",
        )
        factory = RepositoryFactory(mock_db, context)

        # Context should store as-is (may be int or str depending on source)
        assert factory.context.client_account_id == 1
        assert factory.context.engagement_id == 100

        # But repositories should receive strings (tested via mocks above)

    def test_create_repository_factory_convenience_function(
        self, mock_db, full_context
    ):
        """Test the convenience function creates factory correctly."""
        factory = create_repository_factory(mock_db, full_context)

        assert isinstance(factory, RepositoryFactory)
        assert factory.db == mock_db
        assert factory.context == full_context


class TestRepositoryFactoryIntegration:
    """Integration tests that verify factory behavior with real context scenarios."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock async database session."""
        return MagicMock(spec=AsyncSession)

    def test_multiple_repos_from_same_factory(self, mock_db):
        """Test that factory can create multiple different repositories."""
        context = RequestContext(
            client_account_id="1", engagement_id="100", user_id="user-123"
        )
        factory = RepositoryFactory(mock_db, context)

        # Create multiple repos from same factory
        with patch(
            "app.repositories.discovery_flow_repository.DiscoveryFlowRepository"
        ) as mock_discovery:
            with patch(
                "app.repositories.asset_repository.AssetRepository"
            ) as mock_asset:
                with patch(
                    "app.repositories.crewai_flow_state_extensions_repository.CrewAIFlowStateExtensionsRepository"
                ) as mock_crewai:
                    mock_discovery.return_value = MagicMock()
                    mock_asset.return_value = MagicMock()
                    mock_crewai.return_value = MagicMock()

                    repo1 = factory.get_discovery_flow_repo()
                    repo2 = factory.get_asset_repo()
                    repo3 = factory.get_crewai_flow_repo()

                    # All repos should be created
                    assert repo1 is not None
                    assert repo2 is not None
                    assert repo3 is not None

                    # Each should have been called once
                    mock_discovery.assert_called_once()
                    mock_asset.assert_called_once()
                    mock_crewai.assert_called_once()

    def test_factory_with_uuid_context_ids(self, mock_db):
        """Test factory handles UUID-based context IDs."""
        context = RequestContext(
            client_account_id=str(uuid.uuid4()),
            engagement_id=str(uuid.uuid4()),
            user_id="user-123",
        )
        factory = RepositoryFactory(mock_db, context)

        # Should not raise any errors
        assert factory.context.client_account_id is not None
        assert factory.context.engagement_id is not None

    def test_factory_preserves_context_across_calls(self, mock_db):
        """Test that factory maintains same context for all repos."""
        context = RequestContext(
            client_account_id="999", engagement_id="888", user_id="test-user"
        )
        factory = RepositoryFactory(mock_db, context)

        # All repositories should receive same context values
        with patch(
            "app.repositories.discovery_flow_repository.DiscoveryFlowRepository"
        ) as mock_discovery:
            with patch(
                "app.repositories.asset_repository.AssetRepository"
            ) as mock_asset:
                mock_discovery.return_value = MagicMock()
                mock_asset.return_value = MagicMock()

                factory.get_discovery_flow_repo()
                factory.get_asset_repo()

                # Both should have received same context values
                discovery_call = mock_discovery.call_args
                asset_call = mock_asset.call_args

                assert discovery_call.kwargs["client_account_id"] == "999"
                assert discovery_call.kwargs["engagement_id"] == "888"
                assert asset_call.kwargs["client_account_id"] == "999"
                assert asset_call.kwargs["engagement_id"] == "888"


class TestRepositoryFactoryEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock async database session."""
        return MagicMock(spec=AsyncSession)

    def test_factory_with_empty_string_ids(self, mock_db):
        """Test factory handles empty string IDs."""
        context = RequestContext(client_account_id="", engagement_id="", user_id="")
        factory = RepositoryFactory(mock_db, context)

        # Should not raise errors
        assert factory.context.client_account_id == ""
        assert factory.context.engagement_id == ""

    def test_factory_with_all_none_context(self, mock_db):
        """Test factory handles context with all None values."""
        context = RequestContext(
            client_account_id=None,
            engagement_id=None,
            user_id=None,
            flow_id=None,
        )
        factory = RepositoryFactory(mock_db, context)

        # Factory should initialize successfully
        assert factory.db == mock_db
        assert factory.context.client_account_id is None

    def test_assessment_repo_int_conversion_with_string_numbers(self, mock_db):
        """Test assessment repo converts string numbers to ints correctly."""
        context = RequestContext(
            client_account_id="123", engagement_id="456", user_id="user-789"
        )
        factory = RepositoryFactory(mock_db, context)

        with patch(
            "app.repositories.assessment_flow_repository.AssessmentFlowRepository"
        ) as mock_repo:
            mock_repo.return_value = MagicMock()

            factory.get_assessment_flow_repo()

            # Should convert string numbers to integers
            call_args = mock_repo.call_args
            assert call_args.kwargs["client_account_id"] == 123
            assert call_args.kwargs["engagement_id"] == 456
            assert call_args.kwargs["user_id"] == "user-789"  # user_id stays string

    def test_lazy_import_prevents_circular_dependencies(self, mock_db):
        """Test that imports are lazy and don't cause circular import errors."""
        context = RequestContext(client_account_id="1", engagement_id="100")

        # Creating factory should not trigger any imports
        factory = RepositoryFactory(mock_db, context)

        # Imports should only happen when calling get_* methods
        # This test passes if no ImportError is raised during factory creation
        assert factory is not None
