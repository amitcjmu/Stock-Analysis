"""
Unit tests for CollectionBulkAnswerService.

Tests bulk answer operations including:
- Preview functionality with conflict detection
- Bulk answer submission with chunked processing
- Conflict resolution strategies
- Error handling and transaction rollback
"""

import pytest
from uuid import UUID, uuid4
from unittest.mock import AsyncMock, MagicMock

from app.services.collection.bulk_answer import CollectionBulkAnswerService
from app.core.context import RequestContext
from app.schemas.collection import (
    BulkAnswerPreviewResponse,
    BulkAnswerSubmitResponse,
    ConflictDetail,
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
    session.rollback = AsyncMock()
    return session


@pytest.fixture
def service(mock_db_session, mock_context):
    """Create CollectionBulkAnswerService instance."""
    return CollectionBulkAnswerService(db=mock_db_session, context=mock_context)


class TestPreviewBulkAnswers:
    """Tests for preview_bulk_answers method."""

    @pytest.mark.asyncio
    async def test_preview_no_conflicts(self, service, mock_db_session):
        """Test preview when no conflicts exist."""
        # Arrange
        child_flow_id = uuid4()
        asset_ids = [uuid4() for _ in range(5)]
        question_ids = [uuid4() for _ in range(3)]

        # Mock database query - no existing answers
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_db_session.execute.return_value = mock_result

        # Act
        result = await service.preview_bulk_answers(
            child_flow_id=child_flow_id,
            asset_ids=asset_ids,
            question_ids=question_ids,
        )

        # Assert
        assert isinstance(result, BulkAnswerPreviewResponse)
        assert result.total_assets == 5
        assert result.total_questions == 3
        assert result.potential_conflicts == 0
        assert len(result.conflicts) == 0

    @pytest.mark.asyncio
    async def test_preview_with_conflicts(self, service, mock_db_session):
        """Test preview when conflicts are detected."""
        # Arrange
        child_flow_id = uuid4()
        asset_ids = [uuid4() for _ in range(5)]
        question_ids = [uuid4() for _ in range(2)]

        # Mock existing answers with different values
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            (question_ids[0], asset_ids[0], "Value A"),
            (question_ids[0], asset_ids[1], "Value B"),
            (question_ids[0], asset_ids[2], "Value A"),
        ]
        mock_db_session.execute.return_value = mock_result

        # Act
        result = await service.preview_bulk_answers(
            child_flow_id=child_flow_id,
            asset_ids=asset_ids,
            question_ids=question_ids,
        )

        # Assert
        assert result.potential_conflicts > 0
        assert len(result.conflicts) > 0
        conflict = result.conflicts[0]
        assert isinstance(conflict, ConflictDetail)
        assert conflict.question_id == str(question_ids[0])
        assert conflict.conflict_count == 2  # Two different values

    @pytest.mark.asyncio
    async def test_preview_empty_asset_list(self, service):
        """Test preview with empty asset list raises ValueError."""
        with pytest.raises(ValueError, match="asset_ids cannot be empty"):
            await service.preview_bulk_answers(
                child_flow_id=uuid4(), asset_ids=[], question_ids=[uuid4()]
            )

    @pytest.mark.asyncio
    async def test_preview_empty_question_list(self, service):
        """Test preview with empty question list raises ValueError."""
        with pytest.raises(ValueError, match="question_ids cannot be empty"):
            await service.preview_bulk_answers(
                child_flow_id=uuid4(), asset_ids=[uuid4()], question_ids=[]
            )


class TestSubmitBulkAnswers:
    """Tests for submit_bulk_answers method."""

    @pytest.mark.asyncio
    async def test_submit_success_single_chunk(self, service, mock_db_session):
        """Test successful submission with single chunk."""
        # Arrange
        child_flow_id = uuid4()
        asset_ids = [uuid4() for _ in range(50)]  # Under chunk size
        answers = [
            {"question_id": str(uuid4()), "answer_value": "Test Answer"}
            for _ in range(3)
        ]

        # Mock questionnaire queries
        mock_questionnaire_result = MagicMock()
        mock_questionnaire_result.scalar.return_value = uuid4()
        mock_db_session.execute.side_effect = [
            mock_questionnaire_result
        ] * 50  # One per asset

        # Act
        result = await service.submit_bulk_answers(
            child_flow_id=child_flow_id,
            asset_ids=asset_ids,
            answers=answers,
            conflict_resolution_strategy="overwrite",
        )

        # Assert
        assert isinstance(result, BulkAnswerSubmitResponse)
        assert result.success is True
        assert result.assets_updated == 50
        assert result.questions_answered == 3
        assert len(result.updated_questionnaire_ids) == 50
        assert not result.failed_chunks

    @pytest.mark.asyncio
    async def test_submit_chunked_processing(self, service, mock_db_session):
        """Test submission with multiple chunks."""
        # Arrange
        child_flow_id = uuid4()
        asset_ids = [uuid4() for _ in range(250)]  # Multiple chunks
        answers = [{"question_id": str(uuid4()), "answer_value": "Test"}]

        # Mock questionnaire queries
        mock_questionnaire_result = MagicMock()
        mock_questionnaire_result.scalar.return_value = uuid4()
        mock_db_session.execute.side_effect = [mock_questionnaire_result] * 250

        # Act
        result = await service.submit_bulk_answers(
            child_flow_id=child_flow_id,
            asset_ids=asset_ids,
            answers=answers,
            conflict_resolution_strategy="overwrite",
        )

        # Assert
        assert result.success is True
        assert result.assets_updated == 250
        # Should have processed 3 chunks (100 + 100 + 50)
        assert mock_db_session.commit.call_count >= 3

    @pytest.mark.asyncio
    async def test_submit_with_chunk_failure(self, service, mock_db_session):
        """Test submission handles chunk failures gracefully."""
        # Arrange
        child_flow_id = uuid4()
        asset_ids = [uuid4() for _ in range(150)]
        answers = [{"question_id": str(uuid4()), "answer_value": "Test"}]

        # Mock success for first chunk, failure for second
        call_count = 0

        def mock_execute_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if 101 <= call_count <= 200:  # Second chunk fails
                raise Exception("Database error in chunk 2")
            result = MagicMock()
            result.scalar.return_value = uuid4()
            return result

        mock_db_session.execute.side_effect = mock_execute_side_effect

        # Act
        result = await service.submit_bulk_answers(
            child_flow_id=child_flow_id,
            asset_ids=asset_ids,
            answers=answers,
            conflict_resolution_strategy="overwrite",
        )

        # Assert
        assert not result.success  # Overall failed due to chunk failure
        assert result.failed_chunks is not None
        assert len(result.failed_chunks) > 0
        # Rollback should be called for failed chunk
        assert mock_db_session.rollback.call_count >= 1

    @pytest.mark.asyncio
    async def test_submit_skip_conflict_strategy(self, service, mock_db_session):
        """Test skip conflict resolution strategy."""
        # Arrange
        child_flow_id = uuid4()
        asset_ids = [uuid4() for _ in range(10)]
        answers = [{"question_id": str(uuid4()), "answer_value": "New Value"}]

        # Mock some questionnaires with existing answers
        def mock_execute_side_effect(*args, **kwargs):
            sql = str(args[0])
            result = MagicMock()
            if "questionnaire_id" in sql.lower():
                result.scalar.return_value = uuid4()
            elif "existing_answer" in sql.lower():
                # Half have existing answers
                result.scalar.return_value = "Old Value" if len(sql) % 2 == 0 else None
            return result

        mock_db_session.execute.side_effect = mock_execute_side_effect

        # Act
        result = await service.submit_bulk_answers(
            child_flow_id=child_flow_id,
            asset_ids=asset_ids,
            answers=answers,
            conflict_resolution_strategy="skip",
        )

        # Assert
        assert result.success is True
        # Should skip assets with existing answers
        assert result.assets_updated < 10


class TestConflictResolution:
    """Tests for conflict resolution strategies."""

    @pytest.mark.asyncio
    async def test_overwrite_strategy(self, service, mock_db_session):
        """Test overwrite strategy replaces existing answers."""
        # Arrange
        child_flow_id = uuid4()
        asset_ids = [uuid4()]
        question_id = uuid4()
        answers = [{"question_id": str(question_id), "answer_value": "New Value"}]

        # Mock existing answer
        mock_questionnaire_result = MagicMock()
        mock_questionnaire_result.scalar.return_value = uuid4()

        mock_existing_answer = MagicMock()
        mock_existing_answer.scalar.return_value = "Old Value"

        mock_db_session.execute.side_effect = [
            mock_questionnaire_result,
            mock_existing_answer,
        ]

        # Act
        result = await service.submit_bulk_answers(
            child_flow_id=child_flow_id,
            asset_ids=asset_ids,
            answers=answers,
            conflict_resolution_strategy="overwrite",
        )

        # Assert
        assert result.success is True
        # Should have updated the answer (not skipped)
        assert result.assets_updated == 1


class TestErrorHandling:
    """Tests for error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_invalid_child_flow_id(self, service, mock_db_session):
        """Test handling of invalid child_flow_id."""
        # Arrange
        mock_db_session.execute.side_effect = Exception("Flow not found")

        # Act & Assert
        with pytest.raises(Exception):
            await service.submit_bulk_answers(
                child_flow_id=uuid4(),
                asset_ids=[uuid4()],
                answers=[{"question_id": str(uuid4()), "answer_value": "Test"}],
                conflict_resolution_strategy="overwrite",
            )

    @pytest.mark.asyncio
    async def test_transaction_rollback_on_error(self, service, mock_db_session):
        """Test transaction rollback on error."""
        # Arrange
        mock_db_session.commit.side_effect = Exception("Commit failed")

        # Act
        with pytest.raises(Exception):
            await service.submit_bulk_answers(
                child_flow_id=uuid4(),
                asset_ids=[uuid4()],
                answers=[{"question_id": str(uuid4()), "answer_value": "Test"}],
                conflict_resolution_strategy="overwrite",
            )

        # Assert
        assert mock_db_session.rollback.called


class TestProgressTracking:
    """Tests for progress tracking during bulk operations."""

    @pytest.mark.asyncio
    async def test_progress_updates_per_chunk(self, service, mock_db_session):
        """Test that progress is tracked per chunk."""
        # Arrange
        asset_ids = [uuid4() for _ in range(250)]
        answers = [{"question_id": str(uuid4()), "answer_value": "Test"}]

        # Mock successful operations
        mock_result = MagicMock()
        mock_result.scalar.return_value = uuid4()
        mock_db_session.execute.return_value = mock_result

        # Act
        result = await service.submit_bulk_answers(
            child_flow_id=uuid4(),
            asset_ids=asset_ids,
            answers=answers,
            conflict_resolution_strategy="overwrite",
        )

        # Assert
        assert result.assets_updated == 250
        # Should commit after each chunk
        assert mock_db_session.commit.call_count >= 3
