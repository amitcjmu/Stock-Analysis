"""
Unit tests for ImportProcessorBackgroundRunner unified execution model.

Tests the unified execution model changes (Qodo #6) where all import categories
including cmdb_export go through the processor system.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.core.context import RequestContext
from app.services.data_import.background_execution_service.import_processor_runner import (
    ImportProcessorBackgroundRunner,
    _sanitize_error_message,
)
from app.services.data_import.service_handlers.cmdb_export_processor import (
    CMDBExportProcessor,
)


@pytest.fixture
def mock_background_service():
    """Create a mock BackgroundExecutionService."""
    service = MagicMock()
    service.db = MagicMock()
    service.client_account_id = str(uuid4())
    service.start_background_flow_execution = AsyncMock()
    return service


@pytest.fixture
def mock_context():
    """Create a mock RequestContext."""
    return RequestContext(
        client_account_id=uuid4(),
        engagement_id=uuid4(),
        user_id=str(uuid4()),
        flow_id=str(uuid4()),
    )


@pytest.fixture
def runner(mock_background_service):
    """Create an ImportProcessorBackgroundRunner instance."""
    return ImportProcessorBackgroundRunner(mock_background_service)


class TestUnifiedExecutionModel:
    """Test unified execution model (Qodo #6)."""

    @pytest.mark.asyncio
    async def test_cmdb_export_goes_through_processor_system(
        self, runner, mock_context
    ):
        """CMDB export should go through processor system, not bypass it."""
        master_flow_id = str(uuid4())
        data_import_id = str(uuid4())
        raw_records = [{"name": "test"}]

        with patch(
            "app.services.data_import.background_execution_service.import_processor_runner.get_processor_for_category"
        ) as mock_get_processor:
            mock_processor = MagicMock(spec=CMDBExportProcessor)
            mock_processor.process = AsyncMock(
                return_value={"status": "delegated", "delegate_to_legacy": True}
            )
            mock_get_processor.return_value = mock_processor

            with patch(
                "app.services.data_import.background_execution_service.import_processor_runner.asyncio.create_task"
            ) as mock_create_task:
                mock_task = MagicMock()
                mock_create_task.return_value = mock_task

                await runner.start_background_import_execution(
                    master_flow_id=master_flow_id,
                    data_import_id=data_import_id,
                    raw_records=raw_records,
                    import_category="cmdb_export",
                    processing_config={},
                    context=mock_context,
                )

                # Verify processor was retrieved (not bypassed)
                mock_get_processor.assert_called_once()
                call_args = mock_get_processor.call_args
                assert call_args[0][0] == "cmdb_export"

                # Verify task was created (unified path)
                mock_create_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_app_discovery_goes_through_processor_system(
        self, runner, mock_context
    ):
        """App discovery should go through processor system."""
        master_flow_id = str(uuid4())
        data_import_id = str(uuid4())
        raw_records = [{"application_name": "TestApp"}]

        with patch(
            "app.services.data_import.background_execution_service.import_processor_runner.get_processor_for_category"
        ) as mock_get_processor:
            mock_processor = MagicMock()
            mock_processor.process = AsyncMock(
                return_value={
                    "status": "completed",
                    "validation": {"valid": True},
                    "enrichment": {"assets_enriched": 1},
                }
            )
            mock_get_processor.return_value = mock_processor

            with patch(
                "app.services.data_import.background_execution_service.import_processor_runner.asyncio.create_task"
            ) as mock_create_task:
                mock_task = MagicMock()
                mock_create_task.return_value = mock_task

                await runner.start_background_import_execution(
                    master_flow_id=master_flow_id,
                    data_import_id=data_import_id,
                    raw_records=raw_records,
                    import_category="app_discovery",
                    processing_config={},
                    context=mock_context,
                )

                # Verify processor was retrieved
                mock_get_processor.assert_called_once()
                assert mock_get_processor.call_args[0][0] == "app_discovery"

                # Verify task was created
                mock_create_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_cmdb_processor_delegates_to_legacy(
        self, runner, mock_context, mock_background_service
    ):
        """CMDBProcessor should delegate to legacy executor via delegate_to_legacy flag."""
        master_flow_id = str(uuid4())
        data_import_id = str(uuid4())
        raw_records = [{"name": "test"}]

        with patch(
            "app.services.data_import.background_execution_service.import_processor_runner.get_processor_for_category"
        ) as mock_get_processor:
            mock_processor = MagicMock()
            mock_processor.process = AsyncMock(
                return_value={"status": "delegated", "delegate_to_legacy": True}
            )
            mock_get_processor.return_value = mock_processor

            with patch(
                "app.services.data_import.background_execution_service.import_processor_runner.update_flow_status"
            ) as mock_update_status:
                mock_update_status.return_value = AsyncMock()

                # Execute the task directly (not via asyncio.create_task)
                await runner._run_import_processor_task(
                    master_flow_id=master_flow_id,
                    data_import_id=data_import_id,
                    raw_records=raw_records,
                    import_category="cmdb_export",
                    processing_config={},
                    context=mock_context,
                )

                # Verify legacy executor was called
                mock_background_service.start_background_flow_execution.assert_called_once()
                call_args = (
                    mock_background_service.start_background_flow_execution.call_args
                )
                assert call_args[1]["flow_id"] == master_flow_id
                assert call_args[1]["file_data"] == raw_records

    @pytest.mark.asyncio
    async def test_fallback_on_missing_processor(
        self, runner, mock_context, mock_background_service
    ):
        """Should fallback to legacy executor if processor not found."""
        master_flow_id = str(uuid4())
        data_import_id = str(uuid4())
        raw_records = [{"name": "test"}]

        with patch(
            "app.services.data_import.background_execution_service.import_processor_runner.get_processor_for_category"
        ) as mock_get_processor:
            mock_get_processor.side_effect = KeyError(
                "No processor registered for category 'unknown'"
            )

            await runner.start_background_import_execution(
                master_flow_id=master_flow_id,
                data_import_id=data_import_id,
                raw_records=raw_records,
                import_category="unknown",
                processing_config={},
                context=mock_context,
            )

            # Verify fallback to legacy executor
            mock_background_service.start_background_flow_execution.assert_called_once()


class TestErrorSanitization:
    """Test error message sanitization."""

    def test_sanitizes_validation_error(self):
        """ValidationError should be sanitized to user-friendly message."""
        exc = ValueError("Invalid data format")
        result = _sanitize_error_message(exc, "app_discovery")

        assert "app_discovery" in result
        assert "Invalid data format" in result
        assert "Please verify your data structure" in result

    def test_sanitizes_key_error(self):
        """KeyError should be sanitized to user-friendly message."""
        exc = KeyError("missing_field")
        result = _sanitize_error_message(exc, "cmdb_export")

        assert "cmdb_export" in result
        assert "Missing required field" in result
        assert "missing_field" not in result  # Don't expose internal field names

    def test_sanitizes_database_error(self):
        """Database errors should be sanitized."""
        exc = Exception("database connection failed: timeout")
        result = _sanitize_error_message(exc, "infrastructure")

        assert "infrastructure" in result
        assert (
            "database" in exc.__class__.__name__.lower() or "Database error" in result
        )
        assert "timeout" not in result  # Don't expose internal details

    def test_sanitizes_generic_error(self):
        """Generic errors should return safe message."""
        exc = Exception("Internal server error: secret_key leaked")
        result = _sanitize_error_message(exc, "sensitive_data")

        assert "sensitive_data" in result
        assert "secret_key" not in result  # Don't expose secrets
        assert "leaked" not in result
        assert "Please check your data" in result or "contact support" in result

    def test_sanitizes_normalization_error(self):
        """Normalization errors should be sanitized."""
        exc = ValueError("Failed to normalize record at index 5: invalid format")
        result = _sanitize_error_message(exc, "app_discovery")

        assert "app_discovery" in result
        assert "Data format error" in result or "data format" in result.lower()
        assert "index 5" not in result  # Don't expose internal indices
