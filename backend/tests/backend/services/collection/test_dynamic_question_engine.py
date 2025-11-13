"""
Unit tests for DynamicQuestionEngine.

Tests dynamic question filtering operations including:
- Asset-type-specific question filtering
- Answer status filtering (answered vs unanswered)
- Agent-based question pruning
- Dependency change detection and reopening
"""

import pytest
from uuid import UUID, uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.collection.dynamic_question_engine import DynamicQuestionEngine
from app.core.context import RequestContext
from app.schemas.collection import (
    DynamicQuestionsResponse,
    DependencyChangeResponse,
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
    """Create DynamicQuestionEngine instance."""
    return DynamicQuestionEngine(db=mock_db_session, context=mock_context)


class TestAssetTypeFiltering:
    """Tests for asset-type-specific question filtering."""

    @pytest.mark.asyncio
    async def test_filter_application_questions(self, service, mock_db_session):
        """Test filtering questions for Application asset type."""
        # Arrange
        child_flow_id = uuid4()
        asset_id = uuid4()

        # Mock asset with Application type
        mock_asset_result = MagicMock()
        mock_asset_result.scalar_one_or_none.return_value = MagicMock(
            asset_type="Application"
        )

        # Mock 5 Application questions
        mock_questions_result = MagicMock()
        mock_questions_result.fetchall.return_value = [
            (f"app_0{i}_question", f"App Question {i}", "text", "Basic Info", 10, True)
            for i in range(1, 6)
        ]

        # Mock no answers
        mock_answers_result = MagicMock()
        mock_answers_result.fetchall.return_value = []

        mock_db_session.execute.side_effect = [
            mock_asset_result,
            mock_questions_result,
            mock_answers_result,
        ]

        # Act
        result = await service.get_filtered_questions(
            child_flow_id=child_flow_id,
            asset_id=asset_id,
            include_answered=False,
        )

        # Assert
        assert isinstance(result, DynamicQuestionsResponse)
        assert result.asset_type == "Application"
        assert result.total_questions == 5
        assert all(q.question_id.startswith("app_") for q in result.questions)

    @pytest.mark.asyncio
    async def test_filter_server_questions(self, service, mock_db_session):
        """Test filtering questions for Server asset type."""
        # Arrange
        child_flow_id = uuid4()
        asset_id = uuid4()

        mock_asset_result = MagicMock()
        mock_asset_result.scalar_one_or_none.return_value = MagicMock(
            asset_type="Server"
        )

        mock_questions_result = MagicMock()
        mock_questions_result.fetchall.return_value = [
            (f"server_0{i}_question", f"Server Question {i}", "text", "Basic", 10, True)
            for i in range(1, 6)
        ]

        mock_answers_result = MagicMock()
        mock_answers_result.fetchall.return_value = []

        mock_db_session.execute.side_effect = [
            mock_asset_result,
            mock_questions_result,
            mock_answers_result,
        ]

        # Act
        result = await service.get_filtered_questions(
            child_flow_id=child_flow_id,
            asset_id=asset_id,
            include_answered=False,
        )

        # Assert
        assert result.asset_type == "Server"
        assert all(q.question_id.startswith("server_") for q in result.questions)


class TestAnswerStatusFiltering:
    """Tests for answer status filtering."""

    @pytest.mark.asyncio
    async def test_exclude_answered_questions(self, service, mock_db_session):
        """Test filtering out already answered questions."""
        # Arrange
        child_flow_id = uuid4()
        asset_id = uuid4()

        mock_asset_result = MagicMock()
        mock_asset_result.scalar_one_or_none.return_value = MagicMock(
            asset_type="Application"
        )

        # Mock 5 questions total
        mock_questions_result = MagicMock()
        mock_questions_result.fetchall.return_value = [
            (f"q_{i}", f"Question {i}", "text", "Section", 10, True)
            for i in range(1, 6)
        ]

        # Mock 2 questions answered
        mock_answers_result = MagicMock()
        mock_answers_result.fetchall.return_value = [
            ("q_1", "Answer 1"),
            ("q_3", "Answer 3"),
        ]

        mock_db_session.execute.side_effect = [
            mock_asset_result,
            mock_questions_result,
            mock_answers_result,
        ]

        # Act
        result = await service.get_filtered_questions(
            child_flow_id=child_flow_id,
            asset_id=asset_id,
            include_answered=False,
        )

        # Assert
        # Should only return 3 unanswered questions
        assert result.total_questions == 3
        unanswered_ids = {q.question_id for q in result.questions}
        assert unanswered_ids == {"q_2", "q_4", "q_5"}

    @pytest.mark.asyncio
    async def test_include_answered_questions(self, service, mock_db_session):
        """Test including answered questions for review."""
        # Arrange
        child_flow_id = uuid4()
        asset_id = uuid4()

        mock_asset_result = MagicMock()
        mock_asset_result.scalar_one_or_none.return_value = MagicMock(
            asset_type="Application"
        )

        mock_questions_result = MagicMock()
        mock_questions_result.fetchall.return_value = [
            (f"q_{i}", f"Question {i}", "text", "Section", 10, True)
            for i in range(1, 6)
        ]

        mock_answers_result = MagicMock()
        mock_answers_result.fetchall.return_value = [
            ("q_1", "Answer 1"),
            ("q_3", "Answer 3"),
        ]

        mock_db_session.execute.side_effect = [
            mock_asset_result,
            mock_questions_result,
            mock_answers_result,
        ]

        # Act
        result = await service.get_filtered_questions(
            child_flow_id=child_flow_id,
            asset_id=asset_id,
            include_answered=True,
        )

        # Assert
        # Should return all 5 questions
        assert result.total_questions == 5
        answered_count = sum(1 for q in result.questions if q.is_answered)
        assert answered_count == 2


class TestAgentPruning:
    """Tests for agent-based question pruning."""

    @pytest.mark.asyncio
    async def test_agent_pruning_success(self, service, mock_db_session):
        """Test successful agent-based question pruning."""
        # Arrange
        child_flow_id = uuid4()
        asset_id = uuid4()

        mock_asset_result = MagicMock()
        mock_asset_result.scalar_one_or_none.return_value = MagicMock(
            asset_type="Application",
            asset_name="Test App",
        )

        mock_questions_result = MagicMock()
        mock_questions_result.fetchall.return_value = [
            (f"q_{i}", f"Question {i}", "text", "Section", 10, True)
            for i in range(1, 11)  # 10 questions
        ]

        mock_answers_result = MagicMock()
        mock_answers_result.fetchall.return_value = []

        mock_db_session.execute.side_effect = [
            mock_asset_result,
            mock_questions_result,
            mock_answers_result,
        ]

        # Mock agent pruning to remove 3 questions
        with patch.object(
            service, "_invoke_pruning_agent", new_callable=AsyncMock
        ) as mock_agent:
            mock_agent.return_value = ["q_2", "q_5", "q_8"]  # Questions to remove

            # Act
            result = await service.get_filtered_questions(
                child_flow_id=child_flow_id,
                asset_id=asset_id,
                include_answered=False,
                refresh_agent_analysis=True,
            )

            # Assert
            assert result.agent_status == "completed"
            assert result.total_questions == 7  # 10 - 3 removed
            remaining_ids = {q.question_id for q in result.questions}
            assert "q_2" not in remaining_ids
            assert "q_5" not in remaining_ids
            assert "q_8" not in remaining_ids

    @pytest.mark.asyncio
    async def test_agent_pruning_fallback(self, service, mock_db_session):
        """Test graceful fallback when agent pruning fails."""
        # Arrange
        child_flow_id = uuid4()
        asset_id = uuid4()

        mock_asset_result = MagicMock()
        mock_asset_result.scalar_one_or_none.return_value = MagicMock(
            asset_type="Server"
        )

        mock_questions_result = MagicMock()
        mock_questions_result.fetchall.return_value = [
            (f"q_{i}", f"Question {i}", "text", "Section", 10, True)
            for i in range(1, 6)
        ]

        mock_answers_result = MagicMock()
        mock_answers_result.fetchall.return_value = []

        mock_db_session.execute.side_effect = [
            mock_asset_result,
            mock_questions_result,
            mock_answers_result,
        ]

        # Mock agent failure
        with patch.object(
            service, "_invoke_pruning_agent", new_callable=AsyncMock
        ) as mock_agent:
            mock_agent.side_effect = Exception("Agent unavailable")

            # Act
            result = await service.get_filtered_questions(
                child_flow_id=child_flow_id,
                asset_id=asset_id,
                include_answered=False,
                refresh_agent_analysis=True,
            )

            # Assert
            assert result.agent_status == "fallback"
            assert result.total_questions == 5  # All questions returned


class TestDependencyHandling:
    """Tests for dependency change detection."""

    @pytest.mark.asyncio
    async def test_detect_os_change(self, service, mock_db_session):
        """Test detecting OS change and reopening dependent questions."""
        # Arrange
        child_flow_id = uuid4()
        asset_id = uuid4()

        # Mock current asset with old OS
        mock_old_asset = MagicMock()
        mock_old_asset.scalar_one_or_none.return_value = MagicMock(
            operating_system="Windows"
        )

        # Mock dependent questions
        mock_deps_result = MagicMock()
        mock_deps_result.fetchall.return_value = [
            ("patching_schedule", "operating_system"),
            ("security_baseline", "operating_system"),
        ]

        mock_db_session.execute.side_effect = [
            mock_old_asset,
            mock_deps_result,
        ]

        # Act
        result = await service.detect_dependency_changes(
            child_flow_id=child_flow_id,
            asset_id=asset_id,
            changed_field="operating_system",
            new_value="Linux",
        )

        # Assert
        assert isinstance(result, DependencyChangeResponse)
        assert result.changed_field == "operating_system"
        assert result.old_value == "Windows"
        assert result.new_value == "Linux"
        assert len(result.reopened_question_ids) == 2
        assert "patching_schedule" in result.reopened_question_ids

    @pytest.mark.asyncio
    async def test_no_dependencies_found(self, service, mock_db_session):
        """Test when changed field has no dependencies."""
        # Arrange
        child_flow_id = uuid4()
        asset_id = uuid4()

        mock_asset_result = MagicMock()
        mock_asset_result.scalar_one_or_none.return_value = MagicMock(
            asset_name="Old Name"
        )

        mock_deps_result = MagicMock()
        mock_deps_result.fetchall.return_value = []  # No dependencies

        mock_db_session.execute.side_effect = [
            mock_asset_result,
            mock_deps_result,
        ]

        # Act
        result = await service.detect_dependency_changes(
            child_flow_id=child_flow_id,
            asset_id=asset_id,
            changed_field="asset_name",
            new_value="New Name",
        )

        # Assert
        assert len(result.reopened_question_ids) == 0
        assert result.reason == "No dependent questions found"
