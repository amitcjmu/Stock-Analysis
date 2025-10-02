"""
Unit Tests for Import Storage Handler API Endpoints

Tests the key methods in the API handler without database operations,
transaction management, or tenant isolation complexity.

Coverage:
- store_import_data endpoint
- get_latest_import endpoint
- get_import_by_id endpoint
- get_import_data_by_flow_id endpoint
- get_import_status endpoint
- cancel_import endpoint
- retry_failed_import endpoint
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from fastapi import HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.data_import.handlers.import_storage_handler import (
    store_import_data,
    get_latest_import,
    get_import_by_id,
    get_import_data_by_flow_id,
    get_import_status,
    cancel_import,
    retry_failed_import,
)
from app.core.context import RequestContext
from app.schemas.data_import_schemas import StoreImportRequest


@pytest.fixture
def mock_db_session():
    """Mock database session"""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def mock_request():
    """Mock FastAPI Request object"""
    request = Mock(spec=Request)
    request.headers = {
        "X-Client-Account-ID": "11111111-1111-1111-1111-111111111111",
        "X-Engagement-ID": "22222222-2222-2222-2222-222222222222",
        "X-User-ID": "33333333-3333-3333-3333-333333333333",
    }
    return request


@pytest.fixture
def mock_request_context():
    """Mock RequestContext for extract_context_from_request"""
    context = Mock()
    context.client_account_id = "11111111-1111-1111-1111-111111111111"
    context.engagement_id = "22222222-2222-2222-2222-222222222222"
    context.user_id = "33333333-3333-3333-3333-333333333333"
    return context


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
            "size": 1024,
            "type": "text/csv",
        },
        upload_context={
            "intended_type": "cmdb",
            "upload_timestamp": "2024-01-01T00:00:00Z",
        },
    )


@pytest.fixture
def sample_import_response():
    """Sample successful import response"""
    return {
        "success": True,
        "data_import_id": "44444444-4444-4444-4444-444444444444",
        "flow_id": "55555555-5555-5555-5555-555555555555",
        "records_stored": 2,
        "message": "Data imported and discovery flow initiated successfully.",
    }


class TestStoreImportData:
    """Test store_import_data endpoint"""

    @pytest.mark.asyncio
    async def test_store_import_success(
        self, mock_db_session, mock_context, sample_store_request, sample_import_response
    ):
        """Test successful import data storage"""
        with patch(
            "app.api.v1.endpoints.data_import.handlers.import_storage_handler.ImportStorageHandler"
        ) as mock_handler_class:
            mock_handler = AsyncMock()
            mock_handler.handle_import.return_value = sample_import_response
            mock_handler_class.return_value = mock_handler

            result = await store_import_data(
                store_request=sample_store_request,
                request=Mock(),
                db=mock_db_session,
                context=mock_context,
            )

            assert result == sample_import_response
            mock_handler_class.assert_called_once_with(mock_db_session, mock_context.client_account_id)
            mock_handler.handle_import.assert_called_once_with(sample_store_request, mock_context)

    @pytest.mark.asyncio
    async def test_store_import_failure(
        self, mock_db_session, mock_context, sample_store_request
    ):
        """Test import data storage failure"""
        with patch(
            "app.api.v1.endpoints.data_import.handlers.import_storage_handler.ImportStorageHandler"
        ) as mock_handler_class:
            mock_handler = AsyncMock()
            mock_handler.handle_import.side_effect = Exception("Database connection failed")
            mock_handler_class.return_value = mock_handler

            with pytest.raises(HTTPException) as exc_info:
                await store_import_data(
                    store_request=sample_store_request,
                    request=Mock(),
                    db=mock_db_session,
                    context=mock_context,
                )

            assert exc_info.value.status_code == 500
            assert "Failed to store import data" in str(exc_info.value.detail)


class TestGetLatestImport:
    """Test get_latest_import endpoint"""

    @pytest.mark.asyncio
    async def test_get_latest_import_success(self, mock_db_session, mock_request, mock_request_context):
        """Test successful retrieval of latest import"""
        sample_data = {
            "success": True,
            "data": [{"hostname": "server1", "ip": "192.168.1.1"}],
            "import_metadata": {
                "filename": "test_data.csv",
                "import_type": "cmdb",
                "record_count": 1,
            },
        }

        with patch(
            "app.api.v1.endpoints.data_import.handlers.import_storage_handler.extract_context_from_request"
        ) as mock_extract_context:
            mock_extract_context.return_value = mock_request_context

            with patch(
                "app.api.v1.endpoints.data_import.handlers.import_storage_handler.ImportStorageHandler"
            ) as mock_handler_class:
                mock_handler = AsyncMock()
                mock_handler.get_latest_import_data.return_value = sample_data
                mock_handler_class.return_value = mock_handler

                result = await get_latest_import(request=mock_request, db=mock_db_session)

                assert result == sample_data
                mock_handler.get_latest_import_data.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_latest_import_missing_context(self, mock_db_session, mock_request):
        """Test handling of missing context"""

        with patch(
            "app.api.v1.endpoints.data_import.handlers.import_storage_handler.extract_context_from_request"
        ) as mock_extract_context:
            mock_context = Mock()
            mock_context.client_account_id = None
            mock_context.engagement_id = None
            mock_extract_context.return_value = mock_context

            result = await get_latest_import(request=mock_request, db=mock_db_session)

            assert result["success"] is False
            assert "Missing client or engagement context" in result["message"]

    @pytest.mark.asyncio
    async def test_get_latest_import_no_data(self, mock_db_session, mock_request, mock_request_context):
        """Test handling when no import data exists"""
        with patch(
            "app.api.v1.endpoints.data_import.handlers.import_storage_handler.extract_context_from_request"
        ) as mock_extract_context:
            mock_extract_context.return_value = mock_request_context

            with patch(
                "app.api.v1.endpoints.data_import.handlers.import_storage_handler.ImportStorageHandler"
            ) as mock_handler_class:
                mock_handler = AsyncMock()
                mock_handler.get_latest_import_data.return_value = None
                mock_handler_class.return_value = mock_handler

                result = await get_latest_import(request=mock_request, db=mock_db_session)

                assert result["success"] is True
                assert "No import data available yet" in result["message"]
                assert result["data"] == []
                assert result["import_metadata"]["no_imports_exist"] is True

    @pytest.mark.asyncio
    async def test_get_latest_import_error(self, mock_db_session, mock_request):
        """Test error handling in get_latest_import"""
        with patch(
            "app.api.v1.endpoints.data_import.handlers.import_storage_handler.extract_context_from_request"
        ) as mock_extract_context:
            mock_extract_context.side_effect = Exception("Context extraction failed")

            result = await get_latest_import(request=mock_request, db=mock_db_session)

            assert result["success"] is False
            assert "Failed to retrieve latest import" in result["message"]


class TestGetImportById:
    """Test get_import_by_id endpoint"""

    @pytest.mark.asyncio
    async def test_get_import_by_id_success(self, mock_db_session):
        """Test successful retrieval of import by ID"""
        import_id = "44444444-4444-4444-4444-444444444444"
        sample_data = {
            "success": True,
            "data_import_id": import_id,
            "import_metadata": {"filename": "test_data.csv"},
            "data": [{"hostname": "server1"}],
        }

        with patch(
            "app.api.v1.endpoints.data_import.handlers.import_storage_handler.ImportStorageHandler"
        ) as mock_handler_class:
            mock_handler = AsyncMock()
            mock_handler.get_import_data.return_value = sample_data
            mock_handler_class.return_value = mock_handler

            result = await get_import_by_id(data_import_id=import_id, db=mock_db_session)

            assert result == sample_data
            mock_handler.get_import_data.assert_called_once_with(import_id)

    @pytest.mark.asyncio
    async def test_get_import_by_id_not_found(self, mock_db_session):
        """Test handling when import is not found"""
        import_id = "44444444-4444-4444-4444-444444444444"

        with patch(
            "app.api.v1.endpoints.data_import.handlers.import_storage_handler.ImportStorageHandler"
        ) as mock_handler_class:
            mock_handler = AsyncMock()
            mock_handler.get_import_data.return_value = None
            mock_handler_class.return_value = mock_handler

            with pytest.raises(HTTPException) as exc_info:
                await get_import_by_id(data_import_id=import_id, db=mock_db_session)

            assert exc_info.value.status_code == 404
            assert "Data import not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_import_by_id_error(self, mock_db_session):
        """Test error handling in get_import_by_id"""
        import_id = "44444444-4444-4444-4444-444444444444"

        with patch(
            "app.api.v1.endpoints.data_import.handlers.import_storage_handler.ImportStorageHandler"
        ) as mock_handler_class:
            mock_handler = AsyncMock()
            mock_handler.get_import_data.side_effect = Exception("Database error")
            mock_handler_class.return_value = mock_handler

            with pytest.raises(HTTPException) as exc_info:
                await get_import_by_id(data_import_id=import_id, db=mock_db_session)

            assert exc_info.value.status_code == 500
            assert "Failed to retrieve import" in str(exc_info.value.detail)


class TestGetImportStatus:
    """Test get_import_status endpoint"""

    @pytest.mark.asyncio
    async def test_get_import_status_success(self, mock_db_session):
        """Test successful retrieval of import status"""
        import_id = "44444444-4444-4444-4444-444444444444"
        status_data = {
            "import_id": import_id,
            "status": "completed",
            "filename": "test_data.csv",
            "record_count": 10,
        }

        with patch(
            "app.api.v1.endpoints.data_import.handlers.import_storage_handler.ImportStorageHandler"
        ) as mock_handler_class:
            mock_handler = AsyncMock()
            mock_handler.get_import_status.return_value = status_data
            mock_handler_class.return_value = mock_handler

            result = await get_import_status(import_id=import_id, db=mock_db_session)

            assert result == {"success": True, "import_status": status_data}
            mock_handler.get_import_status.assert_called_once_with(import_id)

    @pytest.mark.asyncio
    async def test_get_import_status_not_found(self, mock_db_session):
        """Test handling when import status is not found"""
        import_id = "44444444-4444-4444-4444-444444444444"

        with patch(
            "app.api.v1.endpoints.data_import.handlers.import_storage_handler.ImportStorageHandler"
        ) as mock_handler_class:
            mock_handler = AsyncMock()
            mock_handler.get_import_status.return_value = None
            mock_handler_class.return_value = mock_handler

            with pytest.raises(HTTPException) as exc_info:
                await get_import_status(import_id=import_id, db=mock_db_session)

            assert exc_info.value.status_code == 404
            assert "Import not found" in str(exc_info.value.detail)


class TestCancelImport:
    """Test cancel_import endpoint"""

    @pytest.mark.asyncio
    async def test_cancel_import_success(self, mock_db_session, mock_context):
        """Test successful import cancellation"""
        import_id = "44444444-4444-4444-4444-444444444444"

        with patch(
            "app.api.v1.endpoints.data_import.handlers.import_storage_handler.ImportStorageHandler"
        ) as mock_handler_class:
            mock_handler = AsyncMock()
            mock_handler.cancel_import.return_value = True
            mock_handler_class.return_value = mock_handler

            result = await cancel_import(
                import_id=import_id, db=mock_db_session, context=mock_context
            )

            assert result["success"] is True
            assert f"Import {import_id} cancelled successfully" in result["message"]
            mock_handler.cancel_import.assert_called_once_with(import_id, mock_context)

    @pytest.mark.asyncio
    async def test_cancel_import_not_found(self, mock_db_session, mock_context):
        """Test handling when import cannot be cancelled"""
        import_id = "44444444-4444-4444-4444-444444444444"

        with patch(
            "app.api.v1.endpoints.data_import.handlers.import_storage_handler.ImportStorageHandler"
        ) as mock_handler_class:
            mock_handler = AsyncMock()
            mock_handler.cancel_import.return_value = False
            mock_handler_class.return_value = mock_handler

            with pytest.raises(HTTPException) as exc_info:
                await cancel_import(
                    import_id=import_id, db=mock_db_session, context=mock_context
                )

            assert exc_info.value.status_code == 404
            assert "Import not found or could not be cancelled" in str(exc_info.value.detail)


class TestRetryFailedImport:
    """Test retry_failed_import endpoint"""

    @pytest.mark.asyncio
    async def test_retry_failed_import_success(self, mock_db_session, mock_context):
        """Test successful retry of failed import"""
        import_id = "44444444-4444-4444-4444-444444444444"
        retry_response = {
            "success": True,
            "message": f"Import {import_id} retry initiated successfully",
        }

        with patch(
            "app.api.v1.endpoints.data_import.handlers.import_storage_handler.ImportStorageHandler"
        ) as mock_handler_class:
            mock_handler = AsyncMock()
            mock_handler.retry_failed_import.return_value = retry_response
            mock_handler_class.return_value = mock_handler

            result = await retry_failed_import(
                import_id=import_id, db=mock_db_session, context=mock_context
            )

            assert result == retry_response
            mock_handler.retry_failed_import.assert_called_once_with(import_id, mock_context)

    @pytest.mark.asyncio
    async def test_retry_failed_import_not_found(self, mock_db_session, mock_context):
        """Test handling when import is not found for retry"""
        import_id = "44444444-4444-4444-4444-444444444444"

        with patch(
            "app.api.v1.endpoints.data_import.handlers.import_storage_handler.ImportStorageHandler"
        ) as mock_handler_class:
            mock_handler = AsyncMock()
            mock_handler.retry_failed_import.return_value = None
            mock_handler_class.return_value = mock_handler

            with pytest.raises(HTTPException) as exc_info:
                await retry_failed_import(
                    import_id=import_id, db=mock_db_session, context=mock_context
                )

            assert exc_info.value.status_code == 404
            assert "Import not found" in str(exc_info.value.detail)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
