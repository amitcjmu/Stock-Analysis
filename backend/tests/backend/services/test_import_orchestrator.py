"""
Unit Tests for UnifiedImportOrchestrator

Tests the unified import orchestrator including CSV/JSON parsing,
field mapping suggestions, and import execution.

Coverage Target: 90%+

Per Issue #783 and design doc Section 8.1.
Rewritten based on actual implementation.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID, uuid4
from fastapi import UploadFile

from app.services.collection.unified_import_orchestrator.orchestrator import (
    UnifiedImportOrchestrator,
)
from app.services.collection.unified_import_orchestrator.data_classes import (
    ImportAnalysis,
    FieldMapping,
    ImportTask,
)
from app.core.context import RequestContext
from app.models.collection_flow import CollectionBackgroundTasks


@pytest.fixture
def mock_db_session():
    """Mock database session"""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def mock_context():
    """Mock RequestContext"""
    return RequestContext(
        client_account_id=1,
        engagement_id=1,
        user_id=uuid4(),
    )


@pytest.fixture
def sample_csv_data():
    """Sample parsed CSV data"""
    return [
        {
            "app_name": "MyApp1",
            "language": "Python",
            "database": "PostgreSQL",
            "owner": "John",
        },
        {
            "app_name": "MyApp2",
            "language": "Java",
            "database": "MySQL",
            "owner": "Jane",
        },
        {
            "app_name": "MyApp3",
            "language": "Python",
            "database": "MongoDB",
            "owner": "Bob",
        },
    ]


@pytest.fixture
def sample_json_data():
    """Sample parsed JSON data"""
    return [
        {"server_name": "web-01", "os": "Linux", "cpu": 8, "ram": 32},
        {"server_name": "db-01", "os": "Linux", "cpu": 16, "ram": 64},
        {"server_name": "app-01", "os": "Windows", "cpu": 4, "ram": 16},
    ]


@pytest.fixture
def mock_csv_file():
    """Mock CSV UploadFile"""
    file = Mock(spec=UploadFile)
    file.filename = "applications.csv"
    return file


@pytest.fixture
def mock_json_file():
    """Mock JSON UploadFile"""
    file = Mock(spec=UploadFile)
    file.filename = "servers.json"
    return file


class TestUnifiedImportOrchestrator:
    """Test UnifiedImportOrchestrator class"""

    def test_initialization(self, mock_db_session, mock_context):
        """Test service initialization"""
        service = UnifiedImportOrchestrator(db=mock_db_session, context=mock_context)

        assert service.db == mock_db_session
        assert service.context == mock_context
        assert service.custom_attributes_repo is not None
        assert service.background_tasks_repo is not None
        assert "application" in service.STANDARD_FIELDS
        assert "server" in service.STANDARD_FIELDS
        assert "database" in service.STANDARD_FIELDS

    def test_standard_fields_coverage(self, mock_db_session, mock_context):
        """Test STANDARD_FIELDS constant coverage"""
        service = UnifiedImportOrchestrator(db=mock_db_session, context=mock_context)

        # Application fields
        assert "app_name" in service.STANDARD_FIELDS["application"]
        assert "application_name" in service.STANDARD_FIELDS["application"]
        assert "owner" in service.STANDARD_FIELDS["application"]

        # Server fields
        assert "server_name" in service.STANDARD_FIELDS["server"]
        assert "hostname" in service.STANDARD_FIELDS["server"]
        assert "ip_address" in service.STANDARD_FIELDS["server"]

        # Database fields
        assert "db_name" in service.STANDARD_FIELDS["database"]
        assert "db_type" in service.STANDARD_FIELDS["database"]

    @pytest.mark.asyncio
    async def test_analyze_import_file_csv(
        self, mock_db_session, mock_context, mock_csv_file, sample_csv_data
    ):
        """Test CSV file analysis"""
        service = UnifiedImportOrchestrator(db=mock_db_session, context=mock_context)

        # Mock parse_csv to return parsed data
        with patch(
            "app.services.collection.unified_import_orchestrator.orchestrator.parse_csv",
            AsyncMock(return_value=sample_csv_data),
        ):
            # Mock field mapping
            with patch.object(
                service,
                "_suggest_field_mapping",
                AsyncMock(
                    return_value=FieldMapping(
                        csv_column="app_name",
                        suggested_field="app_name",
                        confidence=0.95,
                        suggestions=[
                            {"field": "app_name", "confidence": 0.95, "method": "fuzzy"}
                        ],
                    )
                ),
            ):
                # Mock validation
                with patch.object(
                    service, "_validate_data", AsyncMock(return_value=[])
                ):
                    result = await service.analyze_import_file(
                        file=mock_csv_file, import_type="application"
                    )

                    assert isinstance(result, ImportAnalysis)
                    assert result.file_name == "applications.csv"
                    assert result.total_rows == 3
                    assert len(result.detected_columns) == 4
                    assert result.import_batch_id is not None
                    assert isinstance(result.import_batch_id, UUID)

    @pytest.mark.asyncio
    async def test_analyze_import_file_json(
        self, mock_db_session, mock_context, mock_json_file, sample_json_data
    ):
        """Test JSON file analysis"""
        service = UnifiedImportOrchestrator(db=mock_db_session, context=mock_context)

        with patch(
            "app.services.collection.unified_import_orchestrator.orchestrator.parse_json",
            AsyncMock(return_value=sample_json_data),
        ):
            with patch.object(
                service,
                "_suggest_field_mapping",
                AsyncMock(
                    return_value=FieldMapping(
                        csv_column="server_name",
                        suggested_field="server_name",
                        confidence=1.0,
                        suggestions=[],
                    )
                ),
            ):
                with patch.object(
                    service, "_validate_data", AsyncMock(return_value=[])
                ):
                    result = await service.analyze_import_file(
                        file=mock_json_file, import_type="server"
                    )

                    assert isinstance(result, ImportAnalysis)
                    assert result.file_name == "servers.json"
                    assert result.total_rows == 3

    @pytest.mark.asyncio
    async def test_analyze_import_file_unsupported_format(
        self, mock_db_session, mock_context
    ):
        """Test error on unsupported file format"""
        service = UnifiedImportOrchestrator(db=mock_db_session, context=mock_context)

        file = Mock(spec=UploadFile)
        file.filename = "data.xlsx"

        with pytest.raises(ValueError, match="Unsupported file format"):
            await service.analyze_import_file(file=file, import_type="application")

    @pytest.mark.asyncio
    async def test_analyze_import_file_empty_file(
        self, mock_db_session, mock_context, mock_csv_file
    ):
        """Test error on empty file"""
        service = UnifiedImportOrchestrator(db=mock_db_session, context=mock_context)

        with patch(
            "app.services.collection.unified_import_orchestrator.orchestrator.parse_csv",
            AsyncMock(return_value=[]),
        ):
            with pytest.raises(ValueError, match="empty or could not be parsed"):
                await service.analyze_import_file(
                    file=mock_csv_file, import_type="application"
                )

    @pytest.mark.asyncio
    async def test_execute_import_fast_mode(
        self, mock_db_session, mock_context, sample_csv_data
    ):
        """Test import execution in fast mode"""
        service = UnifiedImportOrchestrator(db=mock_db_session, context=mock_context)
        child_flow_id = uuid4()
        import_batch_id = uuid4()

        # Mock task creation
        mock_task = Mock(spec=CollectionBackgroundTasks)
        mock_task.id = uuid4()
        service.background_tasks_repo.create_no_commit = AsyncMock(
            return_value=mock_task
        )

        result = await service.execute_import(
            child_flow_id=child_flow_id,
            import_batch_id=import_batch_id,
            file_data=sample_csv_data,
            confirmed_mappings={"app_name": "app_01_name"},
            import_type="application",
            overwrite_existing=False,
            gap_recalculation_mode="fast",
        )

        assert isinstance(result, ImportTask)
        assert result.id == mock_task.id
        assert result.status == "pending"
        assert result.progress_percent == 0
        assert result.current_stage == "queued"
        service.background_tasks_repo.create_no_commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_import_thorough_mode(
        self, mock_db_session, mock_context, sample_csv_data
    ):
        """Test import execution in thorough mode"""
        service = UnifiedImportOrchestrator(db=mock_db_session, context=mock_context)
        child_flow_id = uuid4()
        import_batch_id = uuid4()

        mock_task = Mock(spec=CollectionBackgroundTasks)
        mock_task.id = uuid4()
        service.background_tasks_repo.create_no_commit = AsyncMock(
            return_value=mock_task
        )

        result = await service.execute_import(
            child_flow_id=child_flow_id,
            import_batch_id=import_batch_id,
            file_data=sample_csv_data,
            confirmed_mappings={},
            import_type="server",
            overwrite_existing=True,
            gap_recalculation_mode="thorough",
        )

        assert isinstance(result, ImportTask)
        # Verify task creation params
        call_kwargs = service.background_tasks_repo.create_no_commit.call_args.kwargs
        assert call_kwargs["child_flow_id"] == child_flow_id
        assert call_kwargs["task_type"] == "bulk_import"
        assert call_kwargs["status"] == "pending"
        assert call_kwargs["input_params"]["gap_recalculation_mode"] == "thorough"
        assert call_kwargs["input_params"]["overwrite_existing"] is True

    @pytest.mark.asyncio
    async def test_suggest_field_mapping_high_confidence_fuzzy(
        self, mock_db_session, mock_context, sample_csv_data
    ):
        """Test field mapping with high confidence fuzzy match"""
        service = UnifiedImportOrchestrator(db=mock_db_session, context=mock_context)

        result = await service._suggest_field_mapping(
            csv_column="app_name", import_type="application", data=sample_csv_data
        )

        assert isinstance(result, FieldMapping)
        assert result.csv_column == "app_name"
        assert result.suggested_field == "app_name"
        assert result.confidence >= 0.8  # High confidence fuzzy match
        assert len(result.suggestions) > 0

    @pytest.mark.asyncio
    async def test_suggest_field_mapping_llm_fallback(
        self, mock_db_session, mock_context, sample_csv_data
    ):
        """Test field mapping with LLM when fuzzy match is low"""
        service = UnifiedImportOrchestrator(db=mock_db_session, context=mock_context)

        # Mock multi_model_service
        with patch(
            "app.services.collection.unified_import_orchestrator.orchestrator.multi_model_service"
        ) as mock_mms:
            mock_mms.generate_response = AsyncMock(return_value="business_unit")

            result = await service._suggest_field_mapping(
                csv_column="department",  # Won't match fuzzy well (< 0.8)
                import_type="application",
                data=sample_csv_data,
            )

            assert isinstance(result, FieldMapping)
            assert result.csv_column == "department"
            assert result.suggested_field == "business_unit"
            assert result.confidence == 0.7  # LLM confidence
            mock_mms.generate_response.assert_called_once()

    @pytest.mark.asyncio
    async def test_suggest_field_mapping_llm_unmapped(
        self, mock_db_session, mock_context, sample_csv_data
    ):
        """Test field mapping when LLM returns unmapped"""
        service = UnifiedImportOrchestrator(db=mock_db_session, context=mock_context)

        with patch(
            "app.services.collection.unified_import_orchestrator.orchestrator.multi_model_service"
        ) as mock_mms:
            mock_mms.generate_response = AsyncMock(return_value="unmapped")

            result = await service._suggest_field_mapping(
                csv_column="unknown_field",
                import_type="application",
                data=sample_csv_data,
            )

            assert result.suggested_field is None
            assert result.confidence == 0.3

    @pytest.mark.asyncio
    async def test_suggest_field_mapping_llm_error_fallback(
        self, mock_db_session, mock_context, sample_csv_data
    ):
        """Test fallback to fuzzy when LLM fails"""
        service = UnifiedImportOrchestrator(db=mock_db_session, context=mock_context)

        with patch(
            "app.services.collection.unified_import_orchestrator.orchestrator.multi_model_service"
        ) as mock_mms:
            mock_mms.generate_response = AsyncMock(
                side_effect=Exception("LLM unavailable")
            )

            result = await service._suggest_field_mapping(
                csv_column="custom_field",
                import_type="application",
                data=sample_csv_data,
            )

            # Should fall back to fuzzy match result
            assert isinstance(result, FieldMapping)
            assert result.csv_column == "custom_field"

    def test_fuzzy_match_field_exact_match(self, mock_db_session, mock_context):
        """Test exact fuzzy match"""
        service = UnifiedImportOrchestrator(db=mock_db_session, context=mock_context)

        result = service._fuzzy_match_field("app_name", "application")

        assert result["field"] == "app_name"
        assert result["confidence"] == 1.0
        assert result["method"] == "fuzzy"

    def test_fuzzy_match_field_substring_match(self, mock_db_session, mock_context):
        """Test substring fuzzy match"""
        service = UnifiedImportOrchestrator(db=mock_db_session, context=mock_context)

        # "appname" after normalization matches "app_name" exactly, so it's 1.0
        result = service._fuzzy_match_field("appname", "application")

        assert result["confidence"] == 1.0  # Exact match after normalization
        assert result["method"] == "fuzzy"
        assert result["field"] == "app_name"

    def test_fuzzy_match_field_no_match(self, mock_db_session, mock_context):
        """Test no fuzzy match"""
        service = UnifiedImportOrchestrator(db=mock_db_session, context=mock_context)

        result = service._fuzzy_match_field("unknown_field", "application")

        assert result["confidence"] == 0.0
        assert result["method"] == "fuzzy"

    @pytest.mark.asyncio
    async def test_validate_data_missing_required(
        self, mock_db_session, mock_context, sample_csv_data
    ):
        """Test validation warning for missing required field"""
        service = UnifiedImportOrchestrator(db=mock_db_session, context=mock_context)

        # Mappings without required 'app_name'
        mappings = [
            FieldMapping(
                csv_column="language",
                suggested_field="language",
                confidence=0.9,
                suggestions=[],
            )
        ]

        warnings = await service._validate_data(
            sample_csv_data, mappings, "application"
        )

        assert len(warnings) > 0
        assert any("Required field 'app_name'" in w for w in warnings)

    @pytest.mark.asyncio
    async def test_validate_data_duplicates(self, mock_db_session, mock_context):
        """Test validation warning for duplicate entries"""
        service = UnifiedImportOrchestrator(db=mock_db_session, context=mock_context)

        # Data with duplicate app names
        data = [
            {"app_name": "App1", "language": "Python"},
            {"app_name": "App1", "language": "Java"},  # Duplicate
            {"app_name": "App2", "language": "Go"},
        ]

        mappings = [
            FieldMapping(
                csv_column="app_name",
                suggested_field="app_name",
                confidence=1.0,
                suggestions=[],
            )
        ]

        warnings = await service._validate_data(data, mappings, "application")

        assert len(warnings) > 0
        assert any("Duplicate entries" in w for w in warnings)
        assert any("App1" in w for w in warnings)

    @pytest.mark.asyncio
    async def test_validate_data_no_warnings(
        self, mock_db_session, mock_context, sample_csv_data
    ):
        """Test validation with no warnings"""
        service = UnifiedImportOrchestrator(db=mock_db_session, context=mock_context)

        mappings = [
            FieldMapping(
                csv_column="app_name",
                suggested_field="app_name",
                confidence=1.0,
                suggestions=[],
            ),
            FieldMapping(
                csv_column="language",
                suggested_field="language",
                confidence=0.9,
                suggestions=[],
            ),
        ]

        warnings = await service._validate_data(
            sample_csv_data, mappings, "application"
        )

        # No missing required fields, no duplicates
        assert len(warnings) == 0
