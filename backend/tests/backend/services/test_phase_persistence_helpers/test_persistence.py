"""
Tests for persistence functions.

Tests the data persistence helpers for phase completion and error handling.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.discovery_flow import DiscoveryFlow
from app.services.discovery.phase_persistence_helpers import (
    persist_error_with_classification,
    persist_if_changed,
)


class TestPersistIfChanged:
    """Test the persist_if_changed utility function."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def sample_flow(self):
        """Create a sample discovery flow."""
        flow = DiscoveryFlow(
            id=uuid4(),
            flow_id=uuid4(),
            client_account_id=uuid4(),
            engagement_id=uuid4(),
            user_id="test_user",
            flow_name="Test Flow",
            data_import_completed=False,
            field_mapping_completed=False,
        )
        flow.update_progress = MagicMock()
        return flow

    @pytest.mark.asyncio
    async def test_changes_persisted(self, mock_db, sample_flow):
        """Test that flag changes are persisted."""
        changes_made = await persist_if_changed(
            db=mock_db,
            flow=sample_flow,
            data_import_completed=True,
            field_mapping_completed=True,
        )

        assert changes_made
        assert sample_flow.data_import_completed is True
        assert sample_flow.field_mapping_completed is True
        sample_flow.update_progress.assert_called_once()
        mock_db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_changes_needed(self, mock_db, sample_flow):
        """Test behavior when no changes are needed."""
        changes_made = await persist_if_changed(
            db=mock_db,
            flow=sample_flow,
            data_import_completed=False,  # Same as current
            field_mapping_completed=False,  # Same as current
        )

        assert not changes_made
        sample_flow.update_progress.assert_not_called()
        mock_db.flush.assert_not_called()

    @pytest.mark.asyncio
    async def test_unknown_field_warning(self, mock_db, sample_flow):
        """Test that unknown fields generate warnings but don't fail."""
        changes_made = await persist_if_changed(
            db=mock_db, flow=sample_flow, unknown_field=True
        )

        assert not changes_made  # No valid changes
        assert not hasattr(sample_flow, "unknown_field")


class TestPersistErrorWithClassification:
    """Test the error persistence with classification."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def sample_flow(self):
        """Create a sample discovery flow."""
        return DiscoveryFlow(
            id=uuid4(),
            flow_id=uuid4(),
            client_account_id=uuid4(),
            engagement_id=uuid4(),
            user_id="test_user",
            flow_name="Test Flow",
        )

    @pytest.mark.asyncio
    async def test_transient_error_classification(self, mock_db, sample_flow):
        """Test classification of transient errors."""
        error = Exception("Connection timeout occurred")

        await persist_error_with_classification(
            db=mock_db,
            flow=sample_flow,
            error=error,
            phase="data_import",
            error_code="IMPORT_TIMEOUT",
        )

        assert sample_flow.error_message == "Connection timeout occurred"
        assert sample_flow.error_phase == "data_import"
        assert sample_flow.error_details["error_code"] == "IMPORT_TIMEOUT"
        assert sample_flow.error_details["error_type"] == "transient_io"
        assert sample_flow.error_details["is_retryable"] is True

    @pytest.mark.asyncio
    async def test_validation_error_classification(self, mock_db, sample_flow):
        """Test classification of validation errors."""
        error = Exception("Invalid field mapping configuration")

        await persist_error_with_classification(
            db=mock_db,
            flow=sample_flow,
            error=error,
            phase="field_mapping",
            error_code="MAPPING_VALIDATION_FAILED",
        )

        assert sample_flow.error_details["error_type"] == "validation"
        assert sample_flow.error_details["is_retryable"] is False

    @pytest.mark.asyncio
    async def test_permission_error_classification(self, mock_db, sample_flow):
        """Test classification of permission errors."""
        error = Exception("Permission denied accessing resource")

        await persist_error_with_classification(
            db=mock_db,
            flow=sample_flow,
            error=error,
            phase="asset_inventory",
            error_code="ACCESS_DENIED",
        )

        assert sample_flow.error_details["error_type"] == "permission"
        assert sample_flow.error_details["is_retryable"] is False

    @pytest.mark.asyncio
    async def test_error_message_truncation(self, mock_db, sample_flow):
        """Test that long error messages are truncated."""
        long_error = Exception("x" * 2000)  # Very long error message

        await persist_error_with_classification(
            db=mock_db,
            flow=sample_flow,
            error=long_error,
            phase="data_import",
            error_code="LONG_ERROR",
        )

        assert len(sample_flow.error_message) == 1000  # Truncated to 1000 chars
        mock_db.flush.assert_called_once()
