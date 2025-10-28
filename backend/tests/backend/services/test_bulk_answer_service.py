"""
Unit Tests for CollectionBulkAnswerService

Tests the bulk answer service operations based on ACTUAL implementation.

Coverage Target: 90%+

Per Issue #783 and design doc Section 8.1.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from app.services.collection.bulk_answer.collection_bulk_answer_service import (
    CollectionBulkAnswerService,
)
from app.core.context import RequestContext
from app.models.collection_flow import AdaptiveQuestionnaire
from app.schemas.collection import (
    BulkAnswerPreviewResponse,
    BulkAnswerSubmitResponse,
)


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
def sample_asset_ids():
    """Sample asset UUIDs"""
    return [uuid4() for _ in range(5)]


@pytest.fixture
def sample_question_ids():
    """Sample question IDs"""
    return ["app_01_name", "app_02_language", "app_03_database"]


@pytest.fixture
def sample_answers():
    """Sample answer data"""
    return [
        {"question_id": "app_01_name", "answer_value": "Test App"},
        {"question_id": "app_02_language", "answer_value": "Python"},
        {"question_id": "app_03_database", "answer_value": "PostgreSQL"},
    ]


class TestCollectionBulkAnswerService:
    """Test CollectionBulkAnswerService class"""

    def test_initialization(self, mock_db_session, mock_context):
        """Test service initialization"""
        service = CollectionBulkAnswerService(db=mock_db_session, context=mock_context)

        assert service.db == mock_db_session
        assert service.context == mock_context
        assert service.questionnaire_repo is not None
        assert service.answer_history_repo is not None
        assert service.CHUNK_SIZE == 100

    @pytest.mark.asyncio
    async def test_preview_bulk_answers_no_conflicts(
        self, mock_db_session, mock_context, sample_asset_ids, sample_question_ids
    ):
        """Test preview with no conflicts"""
        service = CollectionBulkAnswerService(db=mock_db_session, context=mock_context)
        child_flow_id = uuid4()

        # Mock _get_existing_answers to return empty list (no existing answers)
        with patch.object(service, "_get_existing_answers", return_value=[]):
            result = await service.preview_bulk_answers(
                child_flow_id=child_flow_id,
                asset_ids=sample_asset_ids,
                question_ids=sample_question_ids,
            )

            assert isinstance(result, BulkAnswerPreviewResponse)
            assert len(result.conflicts) == 0
            assert result.total_assets == len(sample_asset_ids)
            assert result.total_questions == len(sample_question_ids)
            assert result.potential_conflicts == 0

    @pytest.mark.asyncio
    async def test_preview_bulk_answers_with_conflicts(
        self, mock_db_session, mock_context, sample_asset_ids, sample_question_ids
    ):
        """Test preview with conflicting answers"""
        service = CollectionBulkAnswerService(db=mock_db_session, context=mock_context)
        child_flow_id = uuid4()

        # Mock existing answers with different values (conflict)
        # Correct format: list of dicts with "asset_id" and "answer_value" keys
        existing_answers = [
            {"asset_id": sample_asset_ids[0], "answer_value": "Python"},
            {
                "asset_id": sample_asset_ids[1],
                "answer_value": "Java",
            },  # Different value = conflict
        ]

        with patch.object(
            service, "_get_existing_answers", return_value=existing_answers
        ):
            result = await service.preview_bulk_answers(
                child_flow_id=child_flow_id,
                asset_ids=sample_asset_ids,
                question_ids=sample_question_ids,
            )

            assert isinstance(result, BulkAnswerPreviewResponse)
            # Should have conflicts for each question (3 questions total)
            assert result.potential_conflicts == len(sample_question_ids)
            assert len(result.conflicts) == len(sample_question_ids)

    @pytest.mark.asyncio
    async def test_submit_bulk_answers_success(
        self, mock_db_session, mock_context, sample_asset_ids, sample_answers
    ):
        """Test successful bulk answer submission"""
        service = CollectionBulkAnswerService(db=mock_db_session, context=mock_context)
        child_flow_id = uuid4()

        # Create mock questionnaires
        mock_questionnaires = []
        for asset_id in sample_asset_ids:
            q = Mock(spec=AdaptiveQuestionnaire)
            q.id = uuid4()
            q.asset_id = asset_id
            q.responses_collected = {}
            q.last_bulk_update_at = None
            mock_questionnaires.append(q)

        # Mock _get_or_create_questionnaire to return one questionnaire per asset
        with patch.object(service, "_get_or_create_questionnaire") as mock_get:
            mock_get.side_effect = mock_questionnaires

            # Mock _record_answer_history
            with patch.object(
                service, "_record_answer_history", new_callable=AsyncMock
            ):
                result = await service.submit_bulk_answers(
                    child_flow_id=child_flow_id,
                    asset_ids=sample_asset_ids,
                    answers=sample_answers,
                    conflict_resolution_strategy="overwrite",
                )

                assert isinstance(result, BulkAnswerSubmitResponse)
                assert result.success is True
                assert result.total_assets == len(sample_asset_ids)
                assert result.assets_updated == len(sample_asset_ids)
                assert result.questions_answered == len(sample_answers)
                assert len(result.failed_chunks) == 0

    @pytest.mark.asyncio
    async def test_submit_bulk_answers_with_skip_strategy(
        self, mock_db_session, mock_context, sample_asset_ids, sample_answers
    ):
        """Test bulk answer submission with skip conflict strategy"""
        service = CollectionBulkAnswerService(db=mock_db_session, context=mock_context)
        child_flow_id = uuid4()

        # Create questionnaires with existing answers
        mock_questionnaires = []
        for i, asset_id in enumerate(sample_asset_ids):
            q = Mock(spec=AdaptiveQuestionnaire)
            q.id = uuid4()
            q.asset_id = asset_id
            # First asset has existing answer, others don't
            q.responses_collected = {"app_01_name": "Existing App"} if i == 0 else {}
            q.last_bulk_update_at = None
            mock_questionnaires.append(q)

        with patch.object(service, "_get_or_create_questionnaire") as mock_get:
            mock_get.side_effect = mock_questionnaires

            with patch.object(
                service, "_record_answer_history", new_callable=AsyncMock
            ):
                result = await service.submit_bulk_answers(
                    child_flow_id=child_flow_id,
                    asset_ids=sample_asset_ids,
                    answers=sample_answers,
                    conflict_resolution_strategy="skip",
                )

                assert isinstance(result, BulkAnswerSubmitResponse)
                assert result.success is True
                # All assets should be updated (questionnaires are updated, even if some answers skipped)
                assert result.assets_updated == len(sample_asset_ids)

    @pytest.mark.asyncio
    async def test_submit_bulk_answers_chunked_processing(
        self, mock_db_session, mock_context, sample_answers
    ):
        """Test chunked processing with > 100 assets"""
        service = CollectionBulkAnswerService(db=mock_db_session, context=mock_context)
        child_flow_id = uuid4()

        # Create 250 assets (should be processed in 3 chunks)
        large_asset_list = [uuid4() for _ in range(250)]
        mock_questionnaires = []
        for asset_id in large_asset_list:
            q = Mock(spec=AdaptiveQuestionnaire)
            q.id = uuid4()
            q.asset_id = asset_id
            q.responses_collected = {}
            q.last_bulk_update_at = None
            mock_questionnaires.append(q)

        with patch.object(service, "_get_or_create_questionnaire") as mock_get:
            mock_get.side_effect = mock_questionnaires

            with patch.object(
                service, "_record_answer_history", new_callable=AsyncMock
            ):
                result = await service.submit_bulk_answers(
                    child_flow_id=child_flow_id,
                    asset_ids=large_asset_list,
                    answers=sample_answers,
                    conflict_resolution_strategy="overwrite",
                )

                assert isinstance(result, BulkAnswerSubmitResponse)
                assert result.total_assets == 250
                assert result.assets_updated == 250
                # Should have processed 3 chunks (100, 100, 50)

    @pytest.mark.asyncio
    async def test_group_by_value(self, mock_db_session, mock_context):
        """Test answer grouping by value"""
        service = CollectionBulkAnswerService(db=mock_db_session, context=mock_context)

        # Create answers with same and different values
        # Correct format: list of dicts with "asset_id" and "answer_value" keys
        asset1 = uuid4()
        asset2 = uuid4()
        asset3 = uuid4()

        answers = [
            {"asset_id": asset1, "answer_value": "Python"},
            {"asset_id": asset2, "answer_value": "Python"},
            {"asset_id": asset3, "answer_value": "Java"},
        ]

        groups = service._group_by_value(answers)

        assert len(groups) == 2  # Two different values
        assert "Python" in groups
        assert "Java" in groups
        assert len(groups["Python"]) == 2
        assert len(groups["Java"]) == 1
        assert asset1 in groups["Python"]
        assert asset2 in groups["Python"]
        assert asset3 in groups["Java"]

    @pytest.mark.asyncio
    async def test_get_existing_answers(
        self, mock_db_session, mock_context, sample_asset_ids
    ):
        """Test retrieving existing answers"""
        service = CollectionBulkAnswerService(db=mock_db_session, context=mock_context)
        child_flow_id = uuid4()
        question_id = "app_01_name"

        # Create mock questionnaires with responses_collected
        mock_questionnaires = []
        for i, asset_id in enumerate(sample_asset_ids[:3]):  # Only first 3 have answers
            q = Mock(spec=AdaptiveQuestionnaire)
            q.asset_id = asset_id
            q.responses_collected = {question_id: f"Answer {i}"}
            mock_questionnaires.append(q)

        # Mock repository get_by_filters
        service.questionnaire_repo.get_by_filters = AsyncMock(
            return_value=mock_questionnaires
        )

        result = await service._get_existing_answers(
            child_flow_id=child_flow_id,
            asset_ids=sample_asset_ids,
            question_id=question_id,
        )

        assert len(result) == 3
        assert all(isinstance(ans, dict) for ans in result)
        assert all("asset_id" in ans and "answer_value" in ans for ans in result)

    @pytest.mark.asyncio
    async def test_get_or_create_questionnaire_existing(
        self, mock_db_session, mock_context
    ):
        """Test getting existing questionnaire"""
        service = CollectionBulkAnswerService(db=mock_db_session, context=mock_context)
        child_flow_id = uuid4()
        asset_id = uuid4()

        # Mock existing questionnaire
        existing_q = Mock(spec=AdaptiveQuestionnaire)
        existing_q.id = uuid4()
        existing_q.asset_id = asset_id

        service.questionnaire_repo.get_by_filters = AsyncMock(return_value=[existing_q])
        # Mock create to verify it's not called
        service.questionnaire_repo.create_no_commit = AsyncMock()

        result = await service._get_or_create_questionnaire(child_flow_id, asset_id)

        assert result == existing_q
        # Should not create new one
        service.questionnaire_repo.create_no_commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_or_create_questionnaire_new(self, mock_db_session, mock_context):
        """Test creating new questionnaire"""
        service = CollectionBulkAnswerService(db=mock_db_session, context=mock_context)
        child_flow_id = uuid4()
        asset_id = uuid4()

        # Mock no existing questionnaire
        service.questionnaire_repo.get_by_filters = AsyncMock(return_value=[])

        # Mock create
        new_q = Mock(spec=AdaptiveQuestionnaire)
        new_q.id = uuid4()
        new_q.asset_id = asset_id
        service.questionnaire_repo.create_no_commit = AsyncMock(return_value=new_q)

        result = await service._get_or_create_questionnaire(child_flow_id, asset_id)

        assert result == new_q
        service.questionnaire_repo.create_no_commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_should_apply_answer_no_existing(self, mock_db_session, mock_context):
        """Test should apply answer when no existing answer"""
        service = CollectionBulkAnswerService(db=mock_db_session, context=mock_context)

        q = Mock(spec=AdaptiveQuestionnaire)
        q.responses_collected = {}

        answer = {"question_id": "app_01_name", "answer_value": "Test"}

        result = await service._should_apply_answer(q, answer, "overwrite")
        assert result is True

    @pytest.mark.asyncio
    async def test_should_apply_answer_overwrite_strategy(
        self, mock_db_session, mock_context
    ):
        """Test should apply answer with overwrite strategy"""
        service = CollectionBulkAnswerService(db=mock_db_session, context=mock_context)

        q = Mock(spec=AdaptiveQuestionnaire)
        q.responses_collected = {"app_01_name": "Existing"}

        answer = {"question_id": "app_01_name", "answer_value": "New"}

        result = await service._should_apply_answer(q, answer, "overwrite")
        assert result is True

    @pytest.mark.asyncio
    async def test_should_apply_answer_skip_strategy(
        self, mock_db_session, mock_context
    ):
        """Test should skip answer with skip strategy"""
        service = CollectionBulkAnswerService(db=mock_db_session, context=mock_context)

        q = Mock(spec=AdaptiveQuestionnaire)
        q.responses_collected = {"app_01_name": "Existing"}

        answer = {"question_id": "app_01_name", "answer_value": "New"}

        result = await service._should_apply_answer(q, answer, "skip")
        assert result is False

    @pytest.mark.asyncio
    async def test_record_answer_history(self, mock_db_session, mock_context):
        """Test answer history recording"""
        service = CollectionBulkAnswerService(db=mock_db_session, context=mock_context)

        service.answer_history_repo.create_no_commit = AsyncMock()

        await service._record_answer_history(
            questionnaire_id=uuid4(),
            asset_id=uuid4(),
            answer={"question_id": "app_01_name", "answer_value": "Test"},
            source="bulk_operation",
        )

        service.answer_history_repo.create_no_commit.assert_called_once()

    def test_chunks(self, mock_db_session, mock_context):
        """Test chunking utility"""
        service = CollectionBulkAnswerService(db=mock_db_session, context=mock_context)

        items = list(range(250))
        chunks = list(service._chunks(items, 100))

        assert len(chunks) == 3
        assert len(chunks[0]) == 100
        assert len(chunks[1]) == 100
        assert len(chunks[2]) == 50

    def test_chunk_size_constant(self, mock_db_session, mock_context):
        """Test CHUNK_SIZE constant is correct"""
        service = CollectionBulkAnswerService(db=mock_db_session, context=mock_context)

        # Per GPT-5 recommendation in service docstring
        assert service.CHUNK_SIZE == 100

    @pytest.mark.asyncio
    async def test_empty_asset_list(
        self, mock_db_session, mock_context, sample_answers
    ):
        """Test handling empty asset list"""
        service = CollectionBulkAnswerService(db=mock_db_session, context=mock_context)
        child_flow_id = uuid4()

        result = await service.submit_bulk_answers(
            child_flow_id=child_flow_id,
            asset_ids=[],
            answers=sample_answers,
            conflict_resolution_strategy="overwrite",
        )

        assert isinstance(result, BulkAnswerSubmitResponse)
        assert result.total_assets == 0
        assert result.assets_updated == 0

    @pytest.mark.asyncio
    async def test_empty_answers_list(
        self, mock_db_session, mock_context, sample_asset_ids
    ):
        """Test handling empty answers list"""
        service = CollectionBulkAnswerService(db=mock_db_session, context=mock_context)
        child_flow_id = uuid4()

        # Create mock questionnaires
        mock_questionnaires = []
        for asset_id in sample_asset_ids:
            q = Mock(spec=AdaptiveQuestionnaire)
            q.id = uuid4()
            q.asset_id = asset_id
            q.responses_collected = {}
            q.last_bulk_update_at = None
            mock_questionnaires.append(q)

        with patch.object(service, "_get_or_create_questionnaire") as mock_get:
            mock_get.side_effect = mock_questionnaires

            result = await service.submit_bulk_answers(
                child_flow_id=child_flow_id,
                asset_ids=sample_asset_ids,
                answers=[],
                conflict_resolution_strategy="overwrite",
            )

            assert isinstance(result, BulkAnswerSubmitResponse)
            # Should still process all assets even with no answers
            assert result.total_assets == len(sample_asset_ids)
            assert result.questions_answered == 0
