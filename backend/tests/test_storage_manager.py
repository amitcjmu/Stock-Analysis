"""
Unit tests for ImportStorageManager

Tests the database storage manager for data import operations including:
- Database storage operations and CRUD
- Data persistence and retrieval
- Storage optimization and indexing
- Raw record management
- Field mapping creation and management
- Import status tracking and updates
- Master flow linkage operations
- Error handling and recovery
"""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DatabaseError
from app.models.data_import import DataImport, ImportFieldMapping, RawImportRecord
from app.services.data_import.storage_manager import ImportStorageManager


class TestImportStorageManager:
    """Test the ImportStorageManager functionality"""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session for testing"""
        mock_session = AsyncMock(spec=AsyncSession)
        return mock_session

    @pytest.fixture
    def storage_manager(self, mock_db_session):
        """Create ImportStorageManager with mocked dependencies"""
        return ImportStorageManager(
            db=mock_db_session, client_account_id="test_client_123"
        )

    @pytest.fixture
    def sample_import_data(self):
        """Sample data for testing import operations"""
        return {
            "import_id": uuid.uuid4(),
            "engagement_id": "engagement_123",
            "user_id": "user_456",
            "filename": "test_data.csv",
            "file_size": 1024,
            "file_type": "text/csv",
            "intended_type": "servers",
        }

    @pytest.fixture
    def sample_file_data(self):
        """Sample CSV file data for testing"""
        return [
            {
                "server_name": "server001",
                "ip_address": "192.168.1.10",
                "operating_system": "Windows Server 2019",
                "memory_gb": "32",
                "cpu_cores": "8",
            },
            {
                "server_name": "server002",
                "ip_address": "192.168.1.11",
                "operating_system": "Ubuntu 20.04",
                "memory_gb": "16",
                "cpu_cores": "4",
            },
        ]

    @pytest.mark.asyncio
    async def test_find_or_create_import_new(
        self, storage_manager, mock_db_session, sample_import_data
    ):
        """Test creating a new import record when none exists"""
        # Mock no existing import found
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        # Call the method
        data_import = await storage_manager.find_or_create_import(**sample_import_data)

        # Verify new import was created
        assert isinstance(data_import, DataImport)
        assert data_import.id == sample_import_data["import_id"]
        assert data_import.client_account_id == "test_client_123"
        assert data_import.engagement_id == sample_import_data["engagement_id"]
        assert data_import.filename == sample_import_data["filename"]
        assert data_import.status == "pending"
        assert data_import.progress_percentage == 0.0

        # Verify database operations
        mock_db_session.add.assert_called_once()
        mock_db_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_or_create_import_existing(
        self, storage_manager, mock_db_session, sample_import_data
    ):
        """Test finding an existing import record"""
        # Mock existing import found
        existing_import = DataImport(
            id=sample_import_data["import_id"],
            client_account_id="test_client_123",
            status="in_progress",
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_import
        mock_db_session.execute.return_value = mock_result

        # Call the method
        data_import = await storage_manager.find_or_create_import(**sample_import_data)

        # Verify existing import was returned
        assert data_import is existing_import
        assert data_import.status == "in_progress"

        # Verify no new record was added
        mock_db_session.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_find_or_create_import_database_error(
        self, storage_manager, mock_db_session, sample_import_data
    ):
        """Test handling database errors during import creation"""
        # Mock database error
        mock_db_session.execute.side_effect = SQLAlchemyError(
            "Database connection failed"
        )

        # Should raise DatabaseError
        with pytest.raises(DatabaseError) as exc_info:
            await storage_manager.find_or_create_import(**sample_import_data)

        assert "Failed to find or create import record" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_store_raw_records_success(
        self, storage_manager, mock_db_session, sample_file_data
    ):
        """Test successfully storing raw import records"""
        # Create mock data import
        data_import = DataImport(id=uuid.uuid4(), client_account_id="test_client_123")

        # Call the method
        records_count = await storage_manager.store_raw_records(
            data_import=data_import,
            file_data=sample_file_data,
            engagement_id="engagement_123",
        )

        # Verify records were created
        assert records_count == 2
        assert mock_db_session.add.call_count == 2

        # Verify record properties
        added_records = [call.args[0] for call in mock_db_session.add.call_args_list]
        for i, record in enumerate(added_records):
            assert isinstance(record, RawImportRecord)
            assert record.data_import_id == data_import.id
            assert record.client_account_id == "test_client_123"
            assert record.engagement_id == "engagement_123"
            assert record.row_number == i + 1
            assert record.raw_data == sample_file_data[i]
            assert record.is_processed is False
            assert record.is_valid is True

    @pytest.mark.asyncio
    async def test_store_raw_records_empty_data(self, storage_manager, mock_db_session):
        """Test storing raw records with empty data"""
        data_import = DataImport(id=uuid.uuid4())

        records_count = await storage_manager.store_raw_records(
            data_import=data_import, file_data=[], engagement_id="engagement_123"
        )

        assert records_count == 0
        mock_db_session.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_store_raw_records_database_error(
        self, storage_manager, mock_db_session, sample_file_data
    ):
        """Test database error during raw record storage"""
        data_import = DataImport(id=uuid.uuid4())
        mock_db_session.add.side_effect = SQLAlchemyError("Insert failed")

        with pytest.raises(DatabaseError) as exc_info:
            await storage_manager.store_raw_records(
                data_import=data_import,
                file_data=sample_file_data,
                engagement_id="engagement_123",
            )

        assert "Failed to store raw records" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_field_mappings_success(
        self, storage_manager, mock_db_session, sample_file_data
    ):
        """Test successful field mapping creation"""
        data_import = DataImport(id=uuid.uuid4(), client_account_id="test_client_123")

        # Mock the intelligent mapping functions
        with patch(
            "app.services.data_import.storage_manager.intelligent_field_mapping"
        ) as mock_mapping, patch(
            "app.services.data_import.storage_manager.calculate_mapping_confidence"
        ) as mock_confidence:

            # Configure mocks
            mock_mapping.side_effect = lambda field: (
                f"mapped_{field}" if "server" in field else None
            )
            mock_confidence.return_value = 0.85

            # Call the method
            mappings_count = await storage_manager.create_field_mappings(
                data_import=data_import,
                file_data=sample_file_data,
                master_flow_id="flow_123",
            )

            # Verify mappings were created
            assert mappings_count == 5  # 5 fields in sample data
            assert mock_db_session.add.call_count == 5

            # Verify mapping properties
            added_mappings = [
                call.args[0] for call in mock_db_session.add.call_args_list
            ]
            for mapping in added_mappings:
                assert isinstance(mapping, ImportFieldMapping)
                assert mapping.data_import_id == data_import.id
                assert mapping.client_account_id == "test_client_123"
                assert mapping.status == "suggested"
                assert mapping.master_flow_id == "flow_123"

                # Check specific field mappings
                if "server" in mapping.source_field:
                    assert mapping.target_field == f"mapped_{mapping.source_field}"
                    assert mapping.confidence_score == 0.85
                    assert mapping.match_type == "intelligent"
                else:
                    assert mapping.target_field == "UNMAPPED"
                    assert mapping.confidence_score == 0.3
                    assert mapping.match_type == "unmapped"

    @pytest.mark.asyncio
    async def test_create_field_mappings_empty_data(
        self, storage_manager, mock_db_session
    ):
        """Test field mapping creation with empty data"""
        data_import = DataImport(id=uuid.uuid4())

        mappings_count = await storage_manager.create_field_mappings(
            data_import=data_import, file_data=[]
        )

        assert mappings_count == 0
        mock_db_session.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_import_status_completed(self, storage_manager):
        """Test updating import status to completed"""
        data_import = DataImport(
            id=uuid.uuid4(), status="in_progress", progress_percentage=50.0
        )

        await storage_manager.update_import_status(
            data_import=data_import,
            status="completed",
            total_records=100,
            processed_records=100,
        )

        assert data_import.status == "completed"
        assert data_import.total_records == 100
        assert data_import.processed_records == 100
        assert data_import.progress_percentage == 100.0
        assert data_import.completed_at is not None
        assert isinstance(data_import.completed_at, datetime)

    @pytest.mark.asyncio
    async def test_update_import_status_failed(self, storage_manager):
        """Test updating import status to failed with error details"""
        data_import = DataImport(
            id=uuid.uuid4(), status="in_progress", progress_percentage=25.0
        )

        error_details = {
            "error_code": "VALIDATION_FAILED",
            "details": "Invalid data format",
        }

        await storage_manager.update_import_status(
            data_import=data_import,
            status="failed",
            total_records=100,
            processed_records=25,
            error_message="Validation failed",
            error_details=error_details,
        )

        assert data_import.status == "failed"
        assert (
            data_import.progress_percentage == 25.0
        )  # Keeps existing progress on failure
        assert data_import.error_message == "Validation failed"
        assert data_import.error_details == error_details

    @pytest.mark.asyncio
    async def test_update_import_status_discovery_initiated(self, storage_manager):
        """Test updating import status to discovery initiated"""
        data_import = DataImport(id=uuid.uuid4(), status="pending")

        await storage_manager.update_import_status(
            data_import=data_import, status="discovery_initiated", total_records=50
        )

        assert data_import.status == "discovery_initiated"
        assert data_import.progress_percentage == 10.0  # Discovery flow started

    @pytest.mark.asyncio
    async def test_get_import_by_id_success(self, storage_manager, mock_db_session):
        """Test successfully retrieving import by ID"""
        import_id = str(uuid.uuid4())
        expected_import = DataImport(id=import_id, status="completed")

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = expected_import
        mock_db_session.execute.return_value = mock_result

        result = await storage_manager.get_import_by_id(import_id)

        assert result is expected_import
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_import_by_id_not_found(self, storage_manager, mock_db_session):
        """Test retrieving non-existent import"""
        import_id = str(uuid.uuid4())

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        result = await storage_manager.get_import_by_id(import_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_import_by_id_database_error(
        self, storage_manager, mock_db_session
    ):
        """Test database error during import retrieval"""
        import_id = str(uuid.uuid4())
        mock_db_session.execute.side_effect = SQLAlchemyError("Query failed")

        result = await storage_manager.get_import_by_id(import_id)

        assert result is None  # Should handle error gracefully

    @pytest.mark.asyncio
    async def test_get_raw_records_success(self, storage_manager, mock_db_session):
        """Test successfully retrieving raw records"""
        import_id = uuid.uuid4()
        expected_records = [
            RawImportRecord(id=uuid.uuid4(), row_number=1),
            RawImportRecord(id=uuid.uuid4(), row_number=2),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = expected_records
        mock_db_session.execute.return_value = mock_result

        records = await storage_manager.get_raw_records(import_id, limit=100)

        assert records == expected_records
        assert len(records) == 2

    @pytest.mark.asyncio
    async def test_get_raw_records_with_limit(self, storage_manager, mock_db_session):
        """Test retrieving raw records with custom limit"""
        import_id = uuid.uuid4()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute.return_value = mock_result

        await storage_manager.get_raw_records(import_id, limit=50)

        # Verify the query was called with correct limit
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_raw_records_database_error(
        self, storage_manager, mock_db_session
    ):
        """Test database error during raw record retrieval"""
        import_id = uuid.uuid4()
        mock_db_session.execute.side_effect = SQLAlchemyError("Query failed")

        records = await storage_manager.get_raw_records(import_id)

        assert records == []  # Should return empty list on error

    @pytest.mark.asyncio
    async def test_update_raw_records_with_cleansed_data_success(
        self, storage_manager, mock_db_session
    ):
        """Test successfully updating raw records with cleansed data"""
        import_id = uuid.uuid4()
        cleansed_data = [
            {
                "id": uuid.uuid4(),
                "server_name": "CLEAN_SERVER001",
                "ip_address": "192.168.1.10",
                "is_valid": True,
            },
            {
                "id": uuid.uuid4(),
                "server_name": "CLEAN_SERVER002",
                "ip_address": "192.168.1.11",
                "is_valid": False,
                "validation_errors": ["Invalid memory format"],
            },
        ]

        records_updated = await storage_manager.update_raw_records_with_cleansed_data(
            data_import_id=import_id, cleansed_data=cleansed_data
        )

        assert records_updated == 2
        assert mock_db_session.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_update_raw_records_missing_id(
        self, storage_manager, mock_db_session
    ):
        """Test updating raw records with missing ID fields"""
        import_id = uuid.uuid4()
        cleansed_data = [
            {"server_name": "SERVER001"},  # Missing ID
            {"id": uuid.uuid4(), "server_name": "SERVER002"},  # Has ID
        ]

        records_updated = await storage_manager.update_raw_records_with_cleansed_data(
            data_import_id=import_id, cleansed_data=cleansed_data
        )

        assert records_updated == 1  # Only one record had valid ID
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_link_master_flow_to_import_success(
        self, storage_manager, mock_db_session
    ):
        """Test successfully linking master flow to import"""
        import_id = uuid.uuid4()
        master_flow_id = uuid.uuid4()

        # Mock the flow existence check
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = master_flow_id
        mock_db_session.execute.return_value = mock_result

        await storage_manager.link_master_flow_to_import(import_id, master_flow_id)

        # Should have executed 4 update statements (DataImport, RawImportRecord, ImportFieldMapping + the lookup)
        assert mock_db_session.execute.call_count == 4

    @pytest.mark.asyncio
    async def test_link_master_flow_nonexistent_flow(
        self, storage_manager, mock_db_session
    ):
        """Test linking non-existent master flow"""
        import_id = uuid.uuid4()
        master_flow_id = uuid.uuid4()

        # Mock flow not found
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        with pytest.raises(ValueError) as exc_info:
            await storage_manager.link_master_flow_to_import(import_id, master_flow_id)

        assert f"Master flow with flow_id {master_flow_id} not found" in str(
            exc_info.value
        )

    @pytest.mark.asyncio
    async def test_link_master_flow_database_error(
        self, storage_manager, mock_db_session
    ):
        """Test database error during master flow linking"""
        import_id = uuid.uuid4()
        master_flow_id = uuid.uuid4()

        mock_db_session.execute.side_effect = SQLAlchemyError("Update failed")

        with pytest.raises(SQLAlchemyError):
            await storage_manager.link_master_flow_to_import(import_id, master_flow_id)


class TestStorageManagerIntegration:
    """Integration tests for storage manager operations"""

    @pytest.mark.asyncio
    async def test_full_import_workflow(self):
        """Test complete import workflow from creation to completion"""
        mock_db_session = AsyncMock()
        storage_manager = ImportStorageManager(mock_db_session, "client_123")

        # Mock database responses
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None  # No existing import
        mock_db_session.execute.return_value = mock_result

        import_data = {
            "import_id": uuid.uuid4(),
            "engagement_id": "eng_123",
            "user_id": "user_456",
            "filename": "servers.csv",
            "file_size": 2048,
            "file_type": "text/csv",
            "intended_type": "servers",
        }

        file_data = [
            {"server_name": "web01", "ip": "10.0.1.10"},
            {"server_name": "db01", "ip": "10.0.1.20"},
        ]

        # Step 1: Create import
        data_import = await storage_manager.find_or_create_import(**import_data)
        assert data_import.status == "pending"

        # Step 2: Store raw records
        with patch(
            "app.services.data_import.storage_manager.intelligent_field_mapping"
        ) as mock_mapping:
            mock_mapping.return_value = None

            records_count = await storage_manager.store_raw_records(
                data_import, file_data, "eng_123"
            )
            assert records_count == 2

            # Step 3: Create field mappings
            mappings_count = await storage_manager.create_field_mappings(
                data_import, file_data
            )
            assert mappings_count == 2

        # Step 4: Update to completed
        await storage_manager.update_import_status(
            data_import, "completed", total_records=2, processed_records=2
        )
        assert data_import.status == "completed"
        assert data_import.progress_percentage == 100.0

    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self):
        """Test error handling and recovery during import operations"""
        mock_db_session = AsyncMock()
        storage_manager = ImportStorageManager(mock_db_session, "client_123")

        data_import = DataImport(id=uuid.uuid4(), status="in_progress")

        # Simulate processing failure
        await storage_manager.update_import_status(
            data_import=data_import,
            status="failed",
            total_records=100,
            processed_records=25,
            error_message="Processing failed at record 26",
            error_details={"error_type": "validation_error", "record_id": 26},
        )

        assert data_import.status == "failed"
        assert data_import.error_message == "Processing failed at record 26"
        assert data_import.error_details["error_type"] == "validation_error"

    @pytest.mark.asyncio
    async def test_concurrent_operations_handling(self):
        """Test handling of concurrent storage operations"""
        mock_db_session = AsyncMock()
        storage_manager = ImportStorageManager(mock_db_session, "client_123")

        # Simulate concurrent import creations
        import_id = uuid.uuid4()

        # First call succeeds
        mock_result1 = MagicMock()
        mock_result1.scalar_one_or_none.return_value = None

        # Second call finds existing import
        existing_import = DataImport(id=import_id, status="in_progress")
        mock_result2 = MagicMock()
        mock_result2.scalar_one_or_none.return_value = existing_import

        mock_db_session.execute.side_effect = [mock_result1, mock_result2]

        import_data = {
            "import_id": import_id,
            "engagement_id": "eng_123",
            "user_id": "user_456",
            "filename": "test.csv",
            "file_size": 1024,
            "file_type": "text/csv",
            "intended_type": "servers",
        }

        # First call creates new import
        data_import1 = await storage_manager.find_or_create_import(**import_data)
        assert data_import1.status == "pending"

        # Reset mock for second storage manager instance
        storage_manager2 = ImportStorageManager(mock_db_session, "client_123")

        # Second call finds existing import
        data_import2 = await storage_manager2.find_or_create_import(**import_data)
        assert data_import2 is existing_import
        assert data_import2.status == "in_progress"

    @pytest.mark.asyncio
    async def test_performance_with_large_datasets(self):
        """Test storage manager performance with large datasets"""
        mock_db_session = AsyncMock()
        storage_manager = ImportStorageManager(mock_db_session, "client_123")

        data_import = DataImport(id=uuid.uuid4())

        # Simulate large dataset (1000 records)
        large_dataset = [
            {"id": i, "name": f"item_{i}", "value": f"value_{i}"} for i in range(1000)
        ]

        # Should handle large dataset without issues
        records_count = await storage_manager.store_raw_records(
            data_import, large_dataset, "eng_123"
        )

        assert records_count == 1000
        assert mock_db_session.add.call_count == 1000

    @pytest.mark.asyncio
    async def test_data_validation_during_storage(self):
        """Test data validation during storage operations"""
        mock_db_session = AsyncMock()
        storage_manager = ImportStorageManager(mock_db_session, "client_123")

        # Test with invalid data types that should be handled gracefully
        invalid_data = [
            {"field1": None, "field2": ""},  # Null and empty values
            {"field1": "valid", "field2": 12345},  # Mixed types
            {},  # Empty record
        ]

        data_import = DataImport(id=uuid.uuid4())

        # Should handle invalid data gracefully
        records_count = await storage_manager.store_raw_records(
            data_import, invalid_data, "eng_123"
        )

        assert records_count == 3  # All records stored despite invalid data

        # Verify all records were added
        added_records = [call.args[0] for call in mock_db_session.add.call_args_list]
        assert len(added_records) == 3

        for i, record in enumerate(added_records):
            assert record.raw_data == invalid_data[i]
            assert record.is_valid is True  # Initially marked as valid
