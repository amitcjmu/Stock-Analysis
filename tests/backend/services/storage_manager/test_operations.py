"""
Unit Tests for Import Storage Operations

Tests the key methods in the operations module without database operations,
transaction management, or tenant isolation complexity.

Coverage:
- ImportStorageOperations class methods
- store_import_data
- find_or_create_import
- update_import_status
- get_import_by_id
- get_import_data
- link_master_flow_to_import
- update_import_with_flow_id
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.services.data_import.storage_manager.operations import ImportStorageOperations
from app.core.exceptions import DatabaseError


@pytest.fixture
def mock_db_session():
    """Mock database session"""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def sample_file_content():
    """Sample file content as bytes"""
    return b'[{"hostname": "server1", "ip": "192.168.1.1", "type": "server"}]'


@pytest.fixture
def sample_parsed_data():
    """Sample parsed JSON data"""
    return [{"hostname": "server1", "ip": "192.168.1.1", "type": "server"}]


@pytest.fixture
def sample_data_import():
    """Sample DataImport object"""
    mock_import = Mock()
    mock_import.id = uuid.uuid4()
    mock_import.client_account_id = "11111111-1111-1111-1111-111111111111"
    mock_import.engagement_id = "22222222-2222-2222-2222-222222222222"
    mock_import.import_name = "test_data.csv Import"
    mock_import.import_type = "cmdb"
    mock_import.filename = "test_data.csv"
    mock_import.file_size = 1024
    mock_import.mime_type = "application/json"
    mock_import.source_system = "cmdb"
    mock_import.status = "processing"
    mock_import.progress_percentage = 0.0
    mock_import.total_records = 0
    mock_import.processed_records = 0
    mock_import.failed_records = 0
    mock_import.imported_by = "33333333-3333-3333-3333-333333333333"
    return mock_import


class TestImportStorageOperations:
    """Test ImportStorageOperations class"""

    def test_initialization(self, mock_db_session):
        """Test operations initialization"""
        client_account_id = "11111111-1111-1111-1111-111111111111"
        operations = ImportStorageOperations(mock_db_session, client_account_id)

        assert operations.db == mock_db_session
        assert operations.client_account_id == client_account_id

    @pytest.mark.asyncio
    async def test_store_import_data_success(self, mock_db_session, sample_file_content, sample_parsed_data):
        """Test successful import data storage"""
        operations = ImportStorageOperations(mock_db_session, "11111111-1111-1111-1111-111111111111")

        with patch("app.services.data_import.storage_manager.operations.extract_records_from_data") as mock_extract:
            mock_extract.return_value = sample_parsed_data

            with patch.object(operations, "store_raw_records") as mock_store_raw:
                mock_store_raw.return_value = 1

                result = await operations.store_import_data(
                    file_content=sample_file_content,
                    filename="test_data.csv",
                    file_content_type="application/json",
                    import_type="cmdb",
                    status="processing",
                    engagement_id="22222222-2222-2222-2222-222222222222",
                    imported_by="33333333-3333-3333-3333-333333333333",
                )

                assert result is not None
                assert result.total_records == 1
                mock_store_raw.assert_called_once()
                mock_db_session.add.assert_called_once()
                mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_store_import_data_empty_records(self, mock_db_session, sample_file_content):
        """Test handling when no valid records are extracted"""
        operations = ImportStorageOperations(mock_db_session, "11111111-1111-1111-1111-111111111111")

        with patch("app.services.data_import.storage_manager.operations.extract_records_from_data") as mock_extract:
            mock_extract.return_value = []  # Empty records

            result = await operations.store_import_data(
                file_content=sample_file_content,
                filename="test_data.csv",
                file_content_type="application/json",
                import_type="cmdb",
                status="processing",
            )

            assert result is not None
            assert result.total_records == 0

    @pytest.mark.asyncio
    async def test_store_import_data_error(self, mock_db_session, sample_file_content):
        """Test error handling in store_import_data"""
        operations = ImportStorageOperations(mock_db_session, "11111111-1111-1111-1111-111111111111")

        with patch("app.services.data_import.storage_manager.operations.extract_records_from_data") as mock_extract:
            mock_extract.side_effect = Exception("JSON parsing failed")

            with pytest.raises(DatabaseError) as exc_info:
                await operations.store_import_data(
                    file_content=sample_file_content,
                    filename="test_data.csv",
                    file_content_type="application/json",
                    import_type="cmdb",
                )

            assert "Failed to store import data" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_find_or_create_import_existing(self, mock_db_session, sample_data_import):
        """Test finding existing import"""
        operations = ImportStorageOperations(mock_db_session, "11111111-1111-1111-1111-111111111111")
        import_id = sample_data_import.id

        with patch.object(operations.db, "execute") as mock_execute:
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = sample_data_import
            mock_execute.return_value = mock_result

            result = await operations.find_or_create_import(
                import_id=import_id,
                engagement_id="22222222-2222-2222-2222-222222222222",
                user_id="33333333-3333-3333-3333-333333333333",
                filename="test_data.csv",
                file_size=1024,
                file_type="text/csv",
                intended_type="cmdb",
            )

            assert result == sample_data_import
            mock_db_session.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_find_or_create_import_new(self, mock_db_session):
        """Test creating new import when none exists"""
        operations = ImportStorageOperations(mock_db_session, "11111111-1111-1111-1111-111111111111")
        import_id = uuid.uuid4()

        with patch.object(operations.db, "execute") as mock_execute:
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = None  # No existing import
            mock_execute.return_value = mock_result

            result = await operations.find_or_create_import(
                import_id=import_id,
                engagement_id="22222222-2222-2222-2222-222222222222",
                user_id="33333333-3333-3333-3333-333333333333",
                filename="test_data.csv",
                file_size=1024,
                file_type="text/csv",
                intended_type="cmdb",
            )

            assert result is not None
            assert result.id == import_id
            mock_db_session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_or_create_import_error(self, mock_db_session):
        """Test error handling in find_or_create_import"""
        operations = ImportStorageOperations(mock_db_session, "11111111-1111-1111-1111-111111111111")
        import_id = uuid.uuid4()

        with patch.object(operations.db, "execute") as mock_execute:
            mock_execute.side_effect = Exception("Database error")

            with pytest.raises(DatabaseError) as exc_info:
                await operations.find_or_create_import(
                    import_id=import_id,
                    engagement_id="22222222-2222-2222-2222-222222222222",
                    user_id="33333333-3333-3333-3333-333333333333",
                    filename="test_data.csv",
                    file_size=1024,
                    file_type="text/csv",
                    intended_type="cmdb",
                )

            assert "Failed to find or create import record" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_import_status_success(self, mock_db_session, sample_data_import):
        """Test successful import status update"""
        operations = ImportStorageOperations(mock_db_session, "11111111-1111-1111-1111-111111111111")

        await operations.update_import_status(
            data_import=sample_data_import,
            status="completed",
            total_records=10,
            processed_records=10,
            error_message=None,
        )

        assert sample_data_import.status == "completed"
        assert sample_data_import.total_records == 10
        assert sample_data_import.processed_records == 10
        assert sample_data_import.progress_percentage == 100.0

    @pytest.mark.asyncio
    async def test_update_import_status_with_error(self, mock_db_session, sample_data_import):
        """Test import status update with error"""
        operations = ImportStorageOperations(mock_db_session, "11111111-1111-1111-1111-111111111111")

        await operations.update_import_status(
            data_import=sample_data_import,
            status="failed",
            total_records=10,
            processed_records=5,
            error_message="Processing failed",
            error_details={"error_code": "PROC_001"},
        )

        assert sample_data_import.status == "failed"
        assert sample_data_import.error_message == "Processing failed"
        assert sample_data_import.error_details == {"error_code": "PROC_001"}

    @pytest.mark.asyncio
    async def test_update_import_status_error(self, mock_db_session, sample_data_import):
        """Test error handling in update_import_status"""
        operations = ImportStorageOperations(mock_db_session, "11111111-1111-1111-1111-111111111111")

        # Simulate an error by making the data_import object raise an exception
        sample_data_import.status = Mock(side_effect=Exception("Attribute error"))

        with pytest.raises(DatabaseError) as exc_info:
            await operations.update_import_status(
                data_import=sample_data_import,
                status="completed",
            )

        assert "Failed to update import status" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_import_by_id_success(self, mock_db_session, sample_data_import):
        """Test successful retrieval of import by ID"""
        operations = ImportStorageOperations(mock_db_session, "11111111-1111-1111-1111-111111111111")
        import_id = str(sample_data_import.id)

        with patch.object(operations.db, "execute") as mock_execute:
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = sample_data_import
            mock_execute.return_value = mock_result

            result = await operations.get_import_by_id(import_id)

            assert result == sample_data_import

    @pytest.mark.asyncio
    async def test_get_import_by_id_not_found(self, mock_db_session):
        """Test handling when import is not found"""
        operations = ImportStorageOperations(mock_db_session, "11111111-1111-1111-1111-111111111111")
        import_id = str(uuid.uuid4())

        with patch.object(operations.db, "execute") as mock_execute:
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = None
            mock_execute.return_value = mock_result

            result = await operations.get_import_by_id(import_id)

            assert result is None

    @pytest.mark.asyncio
    async def test_get_import_by_id_error(self, mock_db_session):
        """Test error handling in get_import_by_id"""
        operations = ImportStorageOperations(mock_db_session, "11111111-1111-1111-1111-111111111111")
        import_id = str(uuid.uuid4())

        with patch.object(operations.db, "execute") as mock_execute:
            mock_execute.side_effect = Exception("Database error")

            result = await operations.get_import_by_id(import_id)

            assert result is None

    @pytest.mark.asyncio
    async def test_get_import_data_success(self, mock_db_session, sample_data_import):
        """Test successful retrieval of complete import data"""
        operations = ImportStorageOperations(mock_db_session, "11111111-1111-1111-1111-111111111111")
        import_id = str(sample_data_import.id)

        with patch.object(operations, "get_import_by_id") as mock_get_import:
            mock_get_import.return_value = sample_data_import

            with patch.object(operations, "get_raw_records") as mock_get_raw:
                mock_raw_record = Mock()
                mock_raw_record.raw_data = {"hostname": "server1", "ip": "192.168.1.1"}
                mock_get_raw.return_value = [mock_raw_record]

                result = await operations.get_import_data(import_id)

                assert result["success"] is True
                assert len(result["data"]) == 1
                assert result["import_metadata"]["import_id"] == import_id

    @pytest.mark.asyncio
    async def test_get_import_data_not_found(self, mock_db_session):
        """Test handling when import data is not found"""
        operations = ImportStorageOperations(mock_db_session, "11111111-1111-1111-1111-111111111111")
        import_id = str(uuid.uuid4())

        with patch.object(operations, "get_import_by_id") as mock_get_import:
            mock_get_import.return_value = None

            result = await operations.get_import_data(import_id)

            assert result is None

    @pytest.mark.asyncio
    async def test_get_import_data_error(self, mock_db_session):
        """Test error handling in get_import_data"""
        operations = ImportStorageOperations(mock_db_session, "11111111-1111-1111-1111-111111111111")
        import_id = str(uuid.uuid4())

        with patch.object(operations, "get_import_by_id") as mock_get_import:
            mock_get_import.side_effect = Exception("Database error")

            result = await operations.get_import_data(import_id)

            assert result is None

    @pytest.mark.asyncio
    async def test_link_master_flow_to_import_success(self, mock_db_session):
        """Test successful linking of master flow to import"""
        operations = ImportStorageOperations(mock_db_session, "11111111-1111-1111-1111-111111111111")
        data_import_id = uuid.uuid4()
        master_flow_id = uuid.uuid4()

        with patch.object(operations.db, "execute") as mock_execute:
            # Mock the flow lookup
            mock_result1 = Mock()
            mock_result1.scalar_one_or_none.return_value = master_flow_id
            # Mock the update operations
            mock_result2 = Mock()
            mock_result2.rowcount = 1
            mock_execute.side_effect = [mock_result1, mock_result2, mock_result2, mock_result2]

            await operations.link_master_flow_to_import(data_import_id, master_flow_id)

            mock_db_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_link_master_flow_to_import_flow_not_found(self, mock_db_session):
        """Test handling when master flow is not found"""
        operations = ImportStorageOperations(mock_db_session, "11111111-1111-1111-1111-111111111111")
        data_import_id = uuid.uuid4()
        master_flow_id = uuid.uuid4()

        with patch.object(operations.db, "execute") as mock_execute:
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = None  # Flow not found
            mock_execute.return_value = mock_result

            with pytest.raises(ValueError) as exc_info:
                await operations.link_master_flow_to_import(data_import_id, master_flow_id)

            assert f"Master flow with flow_id {master_flow_id} not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_import_with_flow_id_success(self, mock_db_session):
        """Test successful update of import with flow ID"""
        operations = ImportStorageOperations(mock_db_session, "11111111-1111-1111-1111-111111111111")
        data_import_id = uuid.uuid4()
        flow_id = "55555555-5555-5555-5555-555555555555"

        with patch.object(operations.db, "execute") as mock_execute:
            mock_result = Mock()
            mock_result.rowcount = 1
            mock_execute.return_value = mock_result

            await operations.update_import_with_flow_id(data_import_id, flow_id)

            mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_import_with_flow_id_error(self, mock_db_session):
        """Test error handling in update_import_with_flow_id"""
        operations = ImportStorageOperations(mock_db_session, "11111111-1111-1111-1111-111111111111")
        data_import_id = uuid.uuid4()
        flow_id = "55555555-5555-5555-5555-555555555555"

        with patch.object(operations.db, "execute") as mock_execute:
            mock_execute.side_effect = Exception("Database error")

            with pytest.raises(DatabaseError) as exc_info:
                await operations.update_import_with_flow_id(data_import_id, flow_id)

            assert "Failed to update import with flow ID" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
