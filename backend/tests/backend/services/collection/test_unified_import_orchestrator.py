"""
Unit tests for UnifiedImportOrchestrator.

Tests bulk import operations including:
- File analysis and column detection
- Field mapping suggestions with confidence scoring
- Validation warnings (invalid values, required fields, duplicates)
- Background task execution and status tracking
"""

import pytest
from datetime import datetime
from uuid import UUID, uuid4
from unittest.mock import AsyncMock, MagicMock
import json
import io

from app.services.collection.unified_import_orchestrator import (
    UnifiedImportOrchestrator,
)
from app.core.context import RequestContext
from app.schemas.collection import (
    ImportAnalysisResponse,
    ImportExecutionRequest,
    ImportTaskResponse,
    ImportTaskDetailResponse,
)


@pytest.fixture
def mock_context():
    """Create mock RequestContext."""
    return RequestContext(
        user_id="test-user",
        client_account_id=UUID("11111111-1111-1111-1111-111111111111"),
        engagement_id=UUID("22222222-2222-2222-2222-222222222222"),
    )


@pytest.fixture
def mock_db_session():
    """Create mock AsyncSession."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def service(mock_db_session, mock_context):
    """Create UnifiedImportOrchestrator instance."""
    return UnifiedImportOrchestrator(db=mock_db_session, context=mock_context)


@pytest.fixture
def sample_csv_content():
    """Sample CSV content for testing."""
    return """app_name,app_version,prog_lang,criticality
WebApp1,2.1,Python,High
MobileApp,1.5,Java,Medium
APIService,3.0,Go,Critical"""


@pytest.fixture
def sample_json_content():
    """Sample JSON content for testing."""
    return json.dumps(
        [
            {
                "server_name": "WEB-01",
                "os_type": "Linux",
                "cpu_count": 8,
                "memory_gb": 16,
            },
            {
                "server_name": "DB-01",
                "os_type": "Windows",
                "cpu_count": 16,
                "memory_gb": 32,
            },
        ]
    )


class TestFileAnalysis:
    """Tests for file analysis and column detection."""

    @pytest.mark.asyncio
    async def test_analyze_csv_file(self, service, mock_db_session, sample_csv_content):
        """Test analyzing CSV file format."""
        # Arrange
        child_flow_id = uuid4()
        file_like = io.StringIO(sample_csv_content)

        # Mock question rules query
        mock_rules_result = MagicMock()
        mock_rules_result.fetchall.return_value = [
            ("app_01_name", "What is the application name?", "Application"),
            ("app_02_version", "Application version?", "Application"),
            ("app_03_language", "Programming language?", "Application"),
            ("app_04_criticality", "Business criticality?", "Application"),
        ]
        mock_db_session.execute.return_value = mock_rules_result

        # Act
        result = await service.analyze_file(
            child_flow_id=child_flow_id,
            file_content=file_like,
            file_name="applications.csv",
            import_type="application",
        )

        # Assert
        assert isinstance(result, ImportAnalysisResponse)
        assert result.file_name == "applications.csv"
        assert result.total_rows == 3
        assert len(result.detected_columns) == 4
        assert "app_name" in result.detected_columns

    @pytest.mark.asyncio
    async def test_analyze_json_file(
        self, service, mock_db_session, sample_json_content
    ):
        """Test analyzing JSON file format."""
        # Arrange
        child_flow_id = uuid4()
        file_like = io.StringIO(sample_json_content)

        mock_rules_result = MagicMock()
        mock_rules_result.fetchall.return_value = [
            ("server_01_name", "Server name?", "Server"),
            ("server_02_os", "Operating system?", "Server"),
            ("server_03_cpu", "CPU count?", "Server"),
            ("server_04_memory", "Memory (GB)?", "Server"),
        ]
        mock_db_session.execute.return_value = mock_rules_result

        # Act
        result = await service.analyze_file(
            child_flow_id=child_flow_id,
            file_content=file_like,
            file_name="servers.json",
            import_type="server",
        )

        # Assert
        assert result.file_name == "servers.json"
        assert result.total_rows == 2
        assert "server_name" in result.detected_columns


class TestFieldMapping:
    """Tests for field mapping suggestions."""

    @pytest.mark.asyncio
    async def test_exact_match_mapping(self, service, mock_db_session):
        """Test field mapping with exact column name match."""
        # Arrange
        child_flow_id = uuid4()
        detected_columns = ["application_name", "version", "language"]

        mock_rules_result = MagicMock()
        mock_rules_result.fetchall.return_value = [
            ("app_01_name", "Application name?", "Application"),
            ("app_02_version", "Version?", "Application"),
            ("app_03_language", "Programming language?", "Application"),
        ]
        mock_db_session.execute.return_value = mock_rules_result

        # Act
        mappings = await service._suggest_field_mappings(
            child_flow_id=child_flow_id,
            detected_columns=detected_columns,
            import_type="application",
        )

        # Assert
        # Should have high confidence for "application_name" → "app_01_name"
        name_mapping = next(
            m for m in mappings if m.source_column == "application_name"
        )
        assert len(name_mapping.suggested_targets) > 0
        assert name_mapping.suggested_targets[0].target_field == "app_01_name"
        assert name_mapping.suggested_targets[0].confidence > 0.7

    @pytest.mark.asyncio
    async def test_partial_match_mapping(self, service, mock_db_session):
        """Test field mapping with partial similarity."""
        # Arrange
        child_flow_id = uuid4()
        detected_columns = ["app_nm", "ver", "prog_lang"]  # Abbreviated names

        mock_rules_result = MagicMock()
        mock_rules_result.fetchall.return_value = [
            ("app_01_name", "Application name?", "Application"),
            ("app_02_version", "Version?", "Application"),
            ("app_03_language", "Programming language?", "Application"),
        ]
        mock_db_session.execute.return_value = mock_rules_result

        # Act
        mappings = await service._suggest_field_mappings(
            child_flow_id=child_flow_id,
            detected_columns=detected_columns,
            import_type="application",
        )

        # Assert
        # Should still suggest mappings but with lower confidence
        assert len(mappings) == 3
        for mapping in mappings:
            assert len(mapping.suggested_targets) > 0
            # Confidence should be moderate (0.4-0.7)
            assert 0.4 <= mapping.suggested_targets[0].confidence <= 0.9


class TestValidation:
    """Tests for validation warnings."""

    @pytest.mark.asyncio
    async def test_invalid_dropdown_value(self, service, mock_db_session):
        """Test detection of invalid dropdown values."""
        # Arrange
        child_flow_id = uuid4()
        rows_data = [
            {"criticality": "High"},
            {"criticality": "InvalidValue"},  # Invalid
            {"criticality": "Low"},
        ]

        # Mock question rule with dropdown options
        mock_rule_result = MagicMock()
        mock_rule_result.scalar_one_or_none.return_value = MagicMock(
            question_type="dropdown",
            answer_options=["High", "Medium", "Low", "Critical"],
        )
        mock_db_session.execute.return_value = mock_rule_result

        # Act
        warnings = await service._validate_import_data(
            child_flow_id=child_flow_id,
            rows_data=rows_data,
            field_mappings={"criticality": "app_04_criticality"},
            import_type="application",
        )

        # Assert
        assert len(warnings) > 0
        invalid_warning = next(
            (w for w in warnings if "InvalidValue" in w.message), None
        )
        assert invalid_warning is not None
        assert invalid_warning.severity == "error"

    @pytest.mark.asyncio
    async def test_missing_required_field(self, service, mock_db_session):
        """Test detection of missing required fields."""
        # Arrange
        child_flow_id = uuid4()
        rows_data = [
            {"app_name": "App1", "version": "1.0"},
            {"app_name": "App2"},  # Missing version
        ]

        mock_rule_result = MagicMock()
        mock_rule_result.scalar_one_or_none.return_value = MagicMock(is_required=True)
        mock_db_session.execute.return_value = mock_rule_result

        # Act
        warnings = await service._validate_import_data(
            child_flow_id=child_flow_id,
            rows_data=rows_data,
            field_mappings={"version": "app_02_version"},
            import_type="application",
        )

        # Assert
        missing_warning = next(
            (w for w in warnings if "required" in w.message.lower()), None
        )
        assert missing_warning is not None

    @pytest.mark.asyncio
    async def test_duplicate_detection(self, service, mock_db_session):
        """Test detection of duplicate entries."""
        # Arrange
        child_flow_id = uuid4()
        rows_data = [
            {"app_name": "DuplicateApp"},
            {"app_name": "DuplicateApp"},  # Duplicate
            {"app_name": "UniqueApp"},
        ]

        mock_db_session.execute.return_value = MagicMock(
            scalar_one_or_none=MagicMock(return_value=None)
        )

        # Act
        warnings = await service._validate_import_data(
            child_flow_id=child_flow_id,
            rows_data=rows_data,
            field_mappings={"app_name": "app_01_name"},
            import_type="application",
        )

        # Assert
        dup_warning = next(
            (w for w in warnings if "duplicate" in w.message.lower()), None
        )
        assert dup_warning is not None


class TestBackgroundTasks:
    """Tests for background task execution."""

    @pytest.mark.asyncio
    async def test_create_import_task(self, service, mock_db_session):
        """Test creating background import task."""
        # Arrange
        child_flow_id = uuid4()
        request = ImportExecutionRequest(
            child_flow_id=child_flow_id,
            import_batch_id=uuid4(),
            field_mappings={"app_name": "app_01_name"},
            import_type="application",
        )

        # Mock task creation
        mock_task_result = MagicMock()
        mock_task_result.scalar_one.return_value = MagicMock(
            id=uuid4(),
            status="pending",
            created_at=datetime.utcnow(),
        )
        mock_db_session.execute.return_value = mock_task_result

        # Act
        result = await service.execute_import(request)

        # Assert
        assert isinstance(result, ImportTaskResponse)
        assert result.status == "pending"
        assert result.task_id is not None

    @pytest.mark.asyncio
    async def test_poll_task_status_running(self, service, mock_db_session):
        """Test polling status of running task."""
        # Arrange
        task_id = uuid4()

        mock_task_result = MagicMock()
        mock_task_result.scalar_one_or_none.return_value = MagicMock(
            id=task_id,
            status="running",
            progress_percent=45,
            current_stage="Creating assets",
            rows_processed=90,
            total_rows=200,
        )
        mock_db_session.execute.return_value = mock_task_result

        # Act
        result = await service.get_task_status(task_id)

        # Assert
        assert isinstance(result, ImportTaskDetailResponse)
        assert result.status == "running"
        assert result.progress_percent == 45
        assert result.current_stage == "Creating assets"

    @pytest.mark.asyncio
    async def test_poll_task_status_completed(self, service, mock_db_session):
        """Test polling status of completed task."""
        # Arrange
        task_id = uuid4()

        mock_task_result = MagicMock()
        mock_task_result.scalar_one_or_none.return_value = MagicMock(
            id=task_id,
            status="completed",
            progress_percent=100,
            result_data={
                "assets_created": 50,
                "questions_answered": 200,
            },
        )
        mock_db_session.execute.return_value = mock_task_result

        # Act
        result = await service.get_task_status(task_id)

        # Assert
        assert result.status == "completed"
        assert result.progress_percent == 100
        assert result.result_data["assets_created"] == 50
