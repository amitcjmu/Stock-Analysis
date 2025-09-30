"""
Unit Tests for Import Storage Handler Service

Tests the key methods in the service handler without database operations,
transaction management, or tenant isolation complexity.

Coverage:
- ImportStorageHandler class methods
- get_latest_import_data
- get_import_data
- get_import_status
- cancel_import
- retry_failed_import
- handle_import (main orchestration method)
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.data_import.import_storage_handler import ImportStorageHandler
from app.core.context import RequestContext
from app.schemas.data_import_schemas import StoreImportRequest


@pytest.fixture
def mock_db_session():
    """Mock database session"""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def mock_context():
    """Mock RequestContext"""
    return RequestContext(
        client_account_id="11111111-1111-1111-1111-111111111111",
        engagement_id="22222222-2222-2222-2222-222222222222",
        user_id="33333333-3333-3333-3333-333333333333",
    )


@pytest.fixture
def sample_store_request():
    """Sample StoreImportRequest data"""
    return StoreImportRequest(
        file_data=[
            {"hostname": "server1", "ip": "192.168.1.1", "type": "server"},
            {"hostname": "server2", "ip": "192.168.1.2", "type": "database"},
        ],
        metadata={
            "filename": "test_data.csv",
            "file_size": 1024,
            "mime_type": "text/csv",
        },
        upload_context={
            "intended_type": "cmdb",
            "validation_status": "validated",
        },
    )


@pytest.fixture
def sample_import_data():
    """Sample import data response"""
    return {
        "success": True,
        "data": [{"hostname": "server1", "ip": "192.168.1.1"}],
        "import_metadata": {
            "import_id": "44444444-4444-4444-4444-444444444444",
            "filename": "test_data.csv",
            "import_type": "cmdb",
            "record_count": 1,
        },
    }


@pytest.fixture
def sample_import_status():
    """Sample import status data"""
    return {
        "import_id": "44444444-4444-4444-4444-444444444444",
        "status": "completed",
        "filename": "test_data.csv",
        "import_type": "cmdb",
        "record_count": 10,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:05:00Z",
        "master_flow_id": "55555555-5555-5555-5555-555555555555",
    }


class TestImportStorageHandler:
    """Test ImportStorageHandler class"""

    def test_initialization(self, mock_db_session):
        """Test handler initialization"""
        client_account_id = "11111111-1111-1111-1111-111111111111"
        handler = ImportStorageHandler(mock_db_session, client_account_id)

        assert handler.db == mock_db_session
        assert handler.client_account_id == client_account_id
        assert handler.response_builder is not None

    @pytest.mark.asyncio
    async def test_get_latest_import_data_success(self, mock_db_session, mock_context, sample_import_data):
        """Test successful retrieval of latest import data"""
        handler = ImportStorageHandler(mock_db_session, mock_context.client_account_id)

        with patch("app.services.data_import.import_storage_handler.ImportStorageManager") as mock_storage_manager_class:
            mock_storage_manager = AsyncMock()
            mock_storage_manager.get_import_data.return_value = sample_import_data
            mock_storage_manager_class.return_value = mock_storage_manager

            with patch.object(handler.db, "execute") as mock_execute:
                # Mock the database query result
                mock_result = Mock()
                mock_result.scalar_one_or_none.return_value = Mock(id="44444444-4444-4444-4444-444444444444")
                mock_execute.return_value = mock_result

                result = await handler.get_latest_import_data(mock_context)

                assert result == sample_import_data
                mock_storage_manager.get_import_data.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_latest_import_data_no_imports(self, mock_db_session, mock_context):
        """Test handling when no imports exist"""
        handler = ImportStorageHandler(mock_db_session, mock_context.client_account_id)

        with patch.object(handler.db, "execute") as mock_execute:
            # Mock empty query result
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = None
            mock_execute.return_value = mock_result

            result = await handler.get_latest_import_data(mock_context)

            assert result is None

    @pytest.mark.asyncio
    async def test_get_latest_import_data_error(self, mock_db_session, mock_context):
        """Test error handling in get_latest_import_data"""
        handler = ImportStorageHandler(mock_db_session, mock_context.client_account_id)

        with patch.object(handler.db, "execute") as mock_execute:
            mock_execute.side_effect = Exception("Database error")

            result = await handler.get_latest_import_data(mock_context)

            assert result is None

    @pytest.mark.asyncio
    async def test_get_import_data_success(self, mock_db_session, sample_import_data):
        """Test successful retrieval of import data by ID"""
        handler = ImportStorageHandler(mock_db_session, "11111111-1111-1111-1111-111111111111")
        import_id = "44444444-4444-4444-4444-444444444444"

        with patch("app.services.data_import.import_storage_handler.ImportStorageManager") as mock_storage_manager_class:
            mock_storage_manager = AsyncMock()
            mock_storage_manager.get_import_data.return_value = sample_import_data
            mock_storage_manager_class.return_value = mock_storage_manager

            result = await handler.get_import_data(import_id)

            assert result == sample_import_data
            mock_storage_manager.get_import_data.assert_called_once_with(import_id)

    @pytest.mark.asyncio
    async def test_get_import_data_not_found(self, mock_db_session):
        """Test handling when import data is not found"""
        handler = ImportStorageHandler(mock_db_session, "11111111-1111-1111-1111-111111111111")
        import_id = "44444444-4444-4444-4444-444444444444"

        with patch("app.services.data_import.import_storage_handler.ImportStorageManager") as mock_storage_manager_class:
            mock_storage_manager = AsyncMock()
            mock_storage_manager.get_import_data.return_value = None
            mock_storage_manager_class.return_value = mock_storage_manager

            result = await handler.get_import_data(import_id)

            assert result is None

    @pytest.mark.asyncio
    async def test_get_import_status_success(self, mock_db_session, sample_import_status):
        """Test successful retrieval of import status"""
        handler = ImportStorageHandler(mock_db_session, "11111111-1111-1111-1111-111111111111")
        import_id = "44444444-4444-4444-4444-444444444444"

        with patch.object(handler.db, "execute") as mock_execute:
            # Mock the database query result
            mock_result = Mock()
            mock_data_import = Mock()
            mock_data_import.id = import_id
            mock_data_import.status = sample_import_status["status"]
            mock_data_import.filename = sample_import_status["filename"]
            mock_data_import.import_type = sample_import_status["import_type"]
            mock_data_import.total_records = sample_import_status["record_count"]
            mock_data_import.created_at = Mock()
            mock_data_import.created_at.isoformat.return_value = sample_import_status["created_at"]
            mock_data_import.updated_at = Mock()
            mock_data_import.updated_at.isoformat.return_value = sample_import_status["updated_at"]
            mock_data_import.master_flow_id = sample_import_status["master_flow_id"]
            mock_result.scalar_one_or_none.return_value = mock_data_import
            mock_execute.return_value = mock_result

            result = await handler.get_import_status(import_id)

            assert result["import_id"] == import_id
            assert result["status"] == sample_import_status["status"]
            assert result["filename"] == sample_import_status["filename"]

    @pytest.mark.asyncio
    async def test_get_import_status_not_found(self, mock_db_session):
        """Test handling when import status is not found"""
        handler = ImportStorageHandler(mock_db_session, "11111111-1111-1111-1111-111111111111")
        import_id = "44444444-4444-4444-4444-444444444444"

        with patch.object(handler.db, "execute") as mock_execute:
            # Mock empty query result
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = None
            mock_execute.return_value = mock_result

            result = await handler.get_import_status(import_id)

            assert result is None

    @pytest.mark.asyncio
    async def test_cancel_import_success(self, mock_db_session, mock_context):
        """Test successful import cancellation"""
        handler = ImportStorageHandler(mock_db_session, mock_context.client_account_id)
        import_id = "44444444-4444-4444-4444-444444444444"

        with patch.object(handler.db, "execute") as mock_execute:
            # Mock the database query result
            mock_result = Mock()
            mock_data_import = Mock()
            mock_data_import.id = import_id
            mock_data_import.status = "processing"
            mock_result.scalar_one_or_none.return_value = mock_data_import
            mock_execute.return_value = mock_result

            result = await handler.cancel_import(import_id, mock_context)

            assert result is True
            assert mock_data_import.status == "cancelled"
            mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_cancel_import_not_found(self, mock_db_session, mock_context):
        """Test handling when import is not found for cancellation"""
        handler = ImportStorageHandler(mock_db_session, mock_context.client_account_id)
        import_id = "44444444-4444-4444-4444-444444444444"

        with patch.object(handler.db, "execute") as mock_execute:
            # Mock empty query result
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = None
            mock_execute.return_value = mock_result

            result = await handler.cancel_import(import_id, mock_context)

            assert result is False

    @pytest.mark.asyncio
    async def test_cancel_import_error(self, mock_db_session, mock_context):
        """Test error handling in cancel_import"""
        handler = ImportStorageHandler(mock_db_session, mock_context.client_account_id)
        import_id = "44444444-4444-4444-4444-444444444444"

        with patch.object(handler.db, "execute") as mock_execute:
            mock_execute.side_effect = Exception("Database error")

            result = await handler.cancel_import(import_id, mock_context)

            assert result is False
            mock_db_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_retry_failed_import_success(self, mock_db_session, mock_context):
        """Test successful retry of failed import"""
        handler = ImportStorageHandler(mock_db_session, mock_context.client_account_id)
        import_id = "44444444-4444-4444-4444-444444444444"

        with patch.object(handler.db, "execute") as mock_execute:
            # Mock the database query result
            mock_result = Mock()
            mock_data_import = Mock()
            mock_data_import.id = import_id
            mock_data_import.status = "failed"
            mock_result.scalar_one_or_none.return_value = mock_data_import
            mock_execute.return_value = mock_result

            result = await handler.retry_failed_import(import_id, mock_context)

            assert result["success"] is True
            assert f"Import {import_id} retry initiated successfully" in result["message"]
            assert mock_data_import.status == "processing"
            mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_retry_failed_import_not_failed_status(self, mock_db_session, mock_context):
        """Test handling when import is not in failed status"""
        handler = ImportStorageHandler(mock_db_session, mock_context.client_account_id)
        import_id = "44444444-4444-4444-4444-444444444444"

        with patch.object(handler.db, "execute") as mock_execute:
            # Mock the database query result
            mock_result = Mock()
            mock_data_import = Mock()
            mock_data_import.id = import_id
            mock_data_import.status = "completed"  # Not failed
            mock_result.scalar_one_or_none.return_value = mock_data_import
            mock_execute.return_value = mock_result

            result = await handler.retry_failed_import(import_id, mock_context)

            assert result["success"] is False
            assert f"Import {import_id} is not in failed status" in result["message"]

    @pytest.mark.asyncio
    async def test_retry_failed_import_not_found(self, mock_db_session, mock_context):
        """Test handling when import is not found for retry"""
        handler = ImportStorageHandler(mock_db_session, mock_context.client_account_id)
        import_id = "44444444-4444-4444-4444-444444444444"

        with patch.object(handler.db, "execute") as mock_execute:
            # Mock empty query result
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = None
            mock_execute.return_value = mock_result

            result = await handler.retry_failed_import(import_id, mock_context)

            assert result is None

    @pytest.mark.asyncio
    async def test_handle_import_success(self, mock_db_session, mock_context, sample_store_request):
        """Test successful import handling with orchestration"""
        handler = ImportStorageHandler(mock_db_session, mock_context.client_account_id)

        # Mock the complex orchestration dependencies
        with patch("app.services.data_import.import_storage_handler.ImportTransactionManager") as mock_transaction_manager_class:
            mock_transaction_manager = AsyncMock()
            mock_transaction_manager_class.return_value = mock_transaction_manager
            +
            # Properly mock async context manager for transaction()
            cm = AsyncMock()
            cm.__aenter__.return_value = None
            cm.__aexit__.return_value = None
            mock_transaction_manager.transaction.return_value = cm

            with patch("app.services.data_import.import_storage_handler.ImportStorageOperations") as mock_storage_ops_class:
                mock_storage_ops = AsyncMock()
                mock_data_import = Mock()
                mock_data_import.id = "44444444-4444-4444-4444-444444444444"
                mock_data_import.total_records = 2
                mock_data_import.master_flow_id = "55555555-5555-5555-5555-555555555555"
                mock_storage_ops.store_import_data.return_value = mock_data_import
                mock_storage_ops_class.return_value = mock_storage_ops

                with patch("app.services.data_import.import_storage_handler.MasterFlowOrchestrator") as mock_orchestrator_class:
                    mock_orchestrator = AsyncMock()
                    mock_orchestrator.create_flow.return_value = "55555555-5555-5555-5555-555555555555"
                    mock_orchestrator_class.return_value = mock_orchestrator

                    with patch("app.services.data_import.import_storage_handler.DiscoveryFlowService") as mock_discovery_service_class:
                        mock_discovery_service = AsyncMock()
                        mock_discovery_service.create_discovery_flow.return_value = None
                        mock_discovery_service_class.return_value = mock_discovery_service

                        with patch("app.services.data_import.import_storage_handler.BackgroundExecutionService") as mock_background_service_class:
                            mock_background_service = AsyncMock()
                            mock_background_service.start_background_flow_execution.return_value = None
                            mock_background_service_class.return_value = mock_background_service
                            
                            result = await handler.handle_import(sample_store_request, mock_context)

                            assert result["success"] is True
                            assert "Data imported and discovery flow initiated successfully" in result["message"]

    @pytest.mark.asyncio
    async def test_handle_import_error(self, mock_db_session, mock_context, sample_store_request):
        """Test error handling in handle_import"""
        handler = ImportStorageHandler(mock_db_session, mock_context.client_account_id)

        with patch("app.services.data_import.import_storage_handler.ImportTransactionManager") as mock_transaction_manager_class:
            mock_transaction_manager = AsyncMock()
            mock_transaction_manager_class.return_value = mock_transaction_manager
            mock_transaction_manager.transaction.side_effect = Exception("Transaction failed")

            result = await handler.handle_import(sample_store_request, mock_context)

            assert result["success"] is False
            assert "Failed to store import data" in result["message"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
