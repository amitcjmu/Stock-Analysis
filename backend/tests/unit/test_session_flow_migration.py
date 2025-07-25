"""
Test session to flow ID migration
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.orm import Session

# Mock the services and models since they may not exist yet
# These tests validate the session to flow migration pattern


@pytest.fixture
def mock_db_session():
    """Create mock database session"""
    session = MagicMock(spec=Session)
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.add = MagicMock()
    session.query = MagicMock()
    return session


@pytest.fixture
def compatibility_service(mock_db_session):
    """Create SessionFlowCompatibilityService instance"""
    return SessionFlowCompatibilityService(mock_db_session)


@pytest.fixture
def sample_data_import():
    """Sample data import with session_id"""
    return DataImport(
        id=1,
        session_id="test-session-123",
        flow_id=None,
        client_account_id=1,
        original_filename="test.csv",
        file_path="/tmp/test.csv",
        file_size=1024,
        status="completed",
    )


@pytest.fixture
def sample_raw_records():
    """Sample raw import records"""
    return [
        RawImportRecord(
            id=1,
            data_import_id=1,
            session_id="test-session-123",
            flow_id=None,
            raw_data={"hostname": "server1"},
            client_account_id=1,
        ),
        RawImportRecord(
            id=2,
            data_import_id=1,
            session_id="test-session-123",
            flow_id=None,
            raw_data={"hostname": "server2"},
            client_account_id=1,
        ),
    ]


class TestSessionFlowMigration:
    """Test cases for session to flow migration"""

    @pytest.mark.asyncio
    async def test_migrate_data_import(
        self, compatibility_service, mock_db_session, sample_data_import
    ):
        """Test migrating data import from session to flow"""
        # Arrange
        new_flow_id = str(uuid.uuid4())
        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            sample_data_import
        )

        # Act
        result = await compatibility_service.migrate_data_import(
            session_id="test-session-123", new_flow_id=new_flow_id
        )

        # Assert
        assert result is True
        assert sample_data_import.flow_id == new_flow_id
        mock_db_session.commit.assert_called_once()

        # Verify query was made correctly
        mock_db_session.query.assert_called_with(DataImport)

    @pytest.mark.asyncio
    async def test_migrate_raw_records(
        self, compatibility_service, mock_db_session, sample_raw_records
    ):
        """Test migrating raw records from session to flow"""
        # Arrange
        new_flow_id = str(uuid.uuid4())
        mock_db_session.query.return_value.filter.return_value.all.return_value = (
            sample_raw_records
        )

        # Act
        result = await compatibility_service.migrate_raw_records(
            session_id="test-session-123", new_flow_id=new_flow_id
        )

        # Assert
        assert result == 2  # Number of records migrated
        for record in sample_raw_records:
            assert record.flow_id == new_flow_id
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_backward_compatibility_lookup(
        self, compatibility_service, mock_db_session
    ):
        """Test backward compatibility layer"""
        # Arrange
        expected_flow_id = str(uuid.uuid4())
        mock_data_import = MagicMock()
        mock_data_import.flow_id = expected_flow_id
        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            mock_data_import
        )

        # Act
        with patch("app.services.migration.session_to_flow.logger") as mock_logger:
            flow_id = await compatibility_service.get_flow_id_from_session(
                session_id="test-session-123"
            )

        # Assert
        assert flow_id == expected_flow_id
        mock_logger.warning.assert_called_once()
        assert "deprecated session_id lookup" in mock_logger.warning.call_args[0][0]

    @pytest.mark.asyncio
    async def test_migration_rollback(
        self, compatibility_service, mock_db_session, sample_data_import
    ):
        """Test migration can be rolled back safely"""
        # Arrange
        original_session_id = sample_data_import.session_id
        new_flow_id = str(uuid.uuid4())
        sample_data_import.flow_id = new_flow_id

        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            sample_data_import
        )

        # Simulate error during commit
        mock_db_session.commit.side_effect = Exception("Database error")

        # Act & Assert
        with pytest.raises(Exception, match="Database error"):
            await compatibility_service.migrate_data_import(
                session_id=original_session_id, new_flow_id=new_flow_id
            )

        # Verify rollback was called
        mock_db_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_migrate_nonexistent_session(
        self, compatibility_service, mock_db_session
    ):
        """Test migration with non-existent session ID"""
        # Arrange
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        # Act
        result = await compatibility_service.migrate_data_import(
            session_id="nonexistent-session", new_flow_id=str(uuid.uuid4())
        )

        # Assert
        assert result is False
        mock_db_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_batch_migration(self, compatibility_service, mock_db_session):
        """Test migrating multiple sessions in batch"""
        # Arrange
        session_flow_pairs = [
            ("session-1", str(uuid.uuid4())),
            ("session-2", str(uuid.uuid4())),
            ("session-3", str(uuid.uuid4())),
        ]

        # Mock successful migrations
        with patch.object(
            compatibility_service, "migrate_data_import", return_value=True
        ) as mock_migrate_data:
            with patch.object(
                compatibility_service, "migrate_raw_records", return_value=5
            ) as mock_migrate_raw:
                # Act
                results = await compatibility_service.batch_migrate(session_flow_pairs)

        # Assert
        assert len(results) == 3
        assert all(result["success"] for result in results)
        assert mock_migrate_data.call_count == 3
        assert mock_migrate_raw.call_count == 3

    @pytest.mark.asyncio
    async def test_data_integrity_validation(
        self, compatibility_service, mock_db_session, sample_data_import
    ):
        """Test data integrity after migration"""
        # Arrange
        new_flow_id = str(uuid.uuid4())
        original_data = {
            "session_id": sample_data_import.session_id,
            "client_account_id": sample_data_import.client_account_id,
            "original_filename": sample_data_import.original_filename,
        }

        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            sample_data_import
        )

        # Act
        await compatibility_service.migrate_data_import(
            session_id=original_data["session_id"], new_flow_id=new_flow_id
        )

        # Assert - verify critical data preserved
        assert sample_data_import.flow_id == new_flow_id
        assert (
            sample_data_import.session_id == original_data["session_id"]
        )  # Should be preserved
        assert (
            sample_data_import.client_account_id == original_data["client_account_id"]
        )
        assert (
            sample_data_import.original_filename == original_data["original_filename"]
        )

    @pytest.mark.asyncio
    async def test_concurrent_migration_protection(
        self, compatibility_service, mock_db_session
    ):
        """Test protection against concurrent migration attempts"""
        # Arrange
        session_id = "test-session-123"
        flow_id_1 = str(uuid.uuid4())
        flow_id_2 = str(uuid.uuid4())

        sample_import = DataImport(
            id=1, session_id=session_id, flow_id=None, client_account_id=1
        )

        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            sample_import
        )

        # Act - simulate concurrent migrations
        result_1 = await compatibility_service.migrate_data_import(
            session_id, flow_id_1
        )

        # Second migration should detect existing flow_id
        sample_import.flow_id = flow_id_1  # Simulate first migration completed
        result_2 = await compatibility_service.migrate_data_import(
            session_id, flow_id_2
        )

        # Assert
        assert result_1 is True
        assert result_2 is False  # Should reject second migration
        assert sample_import.flow_id == flow_id_1  # Should keep original flow_id
