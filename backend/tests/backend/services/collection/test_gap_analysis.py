"""
Unit tests for IncrementalGapAnalyzer.

Tests gap analysis operations including:
- Incremental gap calculation based on answered questions
- Weight-based progress tracking
- Critical vs non-critical gap detection
- Fast vs thorough analysis modes
"""

import pytest
from uuid import UUID, uuid4
from unittest.mock import AsyncMock, MagicMock

from app.services.collection.incremental_gap_analyzer import IncrementalGapAnalyzer
from app.core.context import RequestContext
from app.schemas.collection import GapAnalysisResponse


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
    """Create IncrementalGapAnalyzer instance."""
    return IncrementalGapAnalyzer(db=mock_db_session, context=mock_context)


class TestAnalyzeGaps:
    """Tests for analyze_gaps method."""

    @pytest.mark.asyncio
    async def test_analyze_gaps_no_answers(self, service, mock_db_session):
        """Test gap analysis when no questions are answered."""
        # Arrange
        child_flow_id = uuid4()
        asset_id = uuid4()

        # Mock all questions unanswered
        mock_questions_result = MagicMock()
        mock_questions_result.fetchall.return_value = [
            (f"q_{i}", f"Question {i}", True, 10, "Section") for i in range(10)
        ]

        # Mock no answers
        mock_answers_result = MagicMock()
        mock_answers_result.fetchall.return_value = []

        mock_db_session.execute.side_effect = [
            mock_questions_result,
            mock_answers_result,
        ]

        # Act
        result = await service.analyze_gaps(
            child_flow_id=child_flow_id,
            asset_id=asset_id,
            analysis_mode="fast",
        )

        # Assert
        assert isinstance(result, GapAnalysisResponse)
        assert result.total_gaps == 10
        assert len(result.gaps) == 10
        assert result.progress_metrics.completion_percent == 0
        assert result.progress_metrics.total_weight == 100  # 10 * 10

    @pytest.mark.asyncio
    async def test_analyze_gaps_partial_completion(self, service, mock_db_session):
        """Test gap analysis with partial completion."""
        # Arrange
        child_flow_id = uuid4()
        asset_id = uuid4()

        # Mock 10 questions (5 answered, 5 unanswered)
        mock_questions_result = MagicMock()
        mock_questions_result.fetchall.return_value = [
            (f"q_{i}", f"Question {i}", i % 2 == 0, 10, "Section") for i in range(10)
        ]

        # Mock 5 answers
        mock_answers_result = MagicMock()
        mock_answers_result.fetchall.return_value = [
            (f"q_{i}", "Answer") for i in range(0, 10, 2)  # Even questions answered
        ]

        mock_db_session.execute.side_effect = [
            mock_questions_result,
            mock_answers_result,
        ]

        # Act
        result = await service.analyze_gaps(
            child_flow_id=child_flow_id,
            asset_id=asset_id,
            analysis_mode="fast",
        )

        # Assert
        assert result.total_gaps == 5  # 5 unanswered
        assert result.progress_metrics.completion_percent == 50
        assert result.progress_metrics.answered_weight == 50
        assert result.progress_metrics.total_weight == 100

    @pytest.mark.asyncio
    async def test_analyze_gaps_full_completion(self, service, mock_db_session):
        """Test gap analysis with 100% completion."""
        # Arrange
        child_flow_id = uuid4()
        asset_id = uuid4()

        # Mock all questions answered
        question_ids = [f"q_{i}" for i in range(10)]
        mock_questions_result = MagicMock()
        mock_questions_result.fetchall.return_value = [
            (qid, f"Question {i}", True, 10, "Section")
            for i, qid in enumerate(question_ids)
        ]

        # Mock all answers
        mock_answers_result = MagicMock()
        mock_answers_result.fetchall.return_value = [
            (qid, "Answer") for qid in question_ids
        ]

        mock_db_session.execute.side_effect = [
            mock_questions_result,
            mock_answers_result,
        ]

        # Act
        result = await service.analyze_gaps(
            child_flow_id=child_flow_id,
            asset_id=asset_id,
            analysis_mode="fast",
        )

        # Assert
        assert result.total_gaps == 0
        assert len(result.gaps) == 0
        assert result.progress_metrics.completion_percent == 100

    @pytest.mark.asyncio
    async def test_analyze_critical_gaps_only(self, service, mock_db_session):
        """Test filtering for critical gaps only."""
        # Arrange
        child_flow_id = uuid4()
        asset_id = uuid4()

        # Mock mix of critical and non-critical questions
        mock_questions_result = MagicMock()
        mock_questions_result.fetchall.return_value = [
            ("q_1", "Critical Q1", True, 10, "Section"),  # Critical
            ("q_2", "Non-critical Q2", False, 5, "Section"),  # Not critical
            ("q_3", "Critical Q3", True, 10, "Section"),  # Critical
            ("q_4", "Non-critical Q4", False, 5, "Section"),  # Not critical
        ]

        # Mock no answers
        mock_answers_result = MagicMock()
        mock_answers_result.fetchall.return_value = []

        mock_db_session.execute.side_effect = [
            mock_questions_result,
            mock_answers_result,
        ]

        # Act
        result = await service.analyze_gaps(
            child_flow_id=child_flow_id,
            asset_id=asset_id,
            analysis_mode="fast",
            critical_only=True,
        )

        # Assert
        # Should only return critical gaps
        assert result.total_gaps == 2
        assert all(gap.is_critical for gap in result.gaps)


class TestAnalysisModes:
    """Tests for fast vs thorough analysis modes."""

    @pytest.mark.asyncio
    async def test_fast_mode_analysis(self, service, mock_db_session):
        """Test fast mode uses simple calculations."""
        # Arrange
        child_flow_id = uuid4()
        asset_id = uuid4()

        mock_questions_result = MagicMock()
        mock_questions_result.fetchall.return_value = [
            ("q_1", "Question 1", True, 10, "Section"),
        ]

        mock_answers_result = MagicMock()
        mock_answers_result.fetchall.return_value = []

        mock_db_session.execute.side_effect = [
            mock_questions_result,
            mock_answers_result,
        ]

        # Act
        result = await service.analyze_gaps(
            child_flow_id=child_flow_id,
            asset_id=asset_id,
            analysis_mode="fast",
        )

        # Assert
        assert result.analysis_mode == "fast"
        # Fast mode should be quick
        assert result.total_gaps == 1

    @pytest.mark.asyncio
    async def test_thorough_mode_analysis(self, service, mock_db_session):
        """Test thorough mode includes dependency analysis."""
        # Arrange
        child_flow_id = uuid4()
        asset_id = uuid4()

        # Mock questions
        mock_questions_result = MagicMock()
        mock_questions_result.fetchall.return_value = [
            ("q_1", "Question 1", True, 10, "Section"),
            ("q_2", "Question 2 (depends on Q1)", True, 10, "Section"),
        ]

        # Mock Q1 answered, Q2 not
        mock_answers_result = MagicMock()
        mock_answers_result.fetchall.return_value = [("q_1", "Answer")]

        # Mock dependency rules
        mock_dependencies_result = MagicMock()
        mock_dependencies_result.fetchall.return_value = [
            ("q_2", "q_1"),  # Q2 depends on Q1
        ]

        mock_db_session.execute.side_effect = [
            mock_questions_result,
            mock_answers_result,
            mock_dependencies_result,  # Extra query for thorough mode
        ]

        # Act
        result = await service.analyze_gaps(
            child_flow_id=child_flow_id,
            asset_id=asset_id,
            analysis_mode="thorough",
        )

        # Assert
        assert result.analysis_mode == "thorough"
        # Should detect Q2 gap with dependency info
        q2_gap = next((g for g in result.gaps if g.question_id == "q_2"), None)
        assert q2_gap is not None
        assert q2_gap.depends_on == ["q_1"]


class TestWeightedProgress:
    """Tests for weight-based progress calculations."""

    @pytest.mark.asyncio
    async def test_weighted_progress_calculation(self, service, mock_db_session):
        """Test progress calculation respects question weights."""
        # Arrange
        child_flow_id = uuid4()
        asset_id = uuid4()

        # Mock questions with different weights
        mock_questions_result = MagicMock()
        mock_questions_result.fetchall.return_value = [
            ("q_critical", "Critical Question", True, 50, "Section"),  # High weight
            ("q_normal", "Normal Question", True, 10, "Section"),  # Normal weight
            ("q_minor", "Minor Question", False, 5, "Section"),  # Low weight
        ]

        # Mock critical question answered, others not
        mock_answers_result = MagicMock()
        mock_answers_result.fetchall.return_value = [("q_critical", "Answer")]

        mock_db_session.execute.side_effect = [
            mock_questions_result,
            mock_answers_result,
        ]

        # Act
        result = await service.analyze_gaps(
            child_flow_id=child_flow_id,
            asset_id=asset_id,
            analysis_mode="fast",
        )

        # Assert
        # Total weight = 50 + 10 + 5 = 65
        # Answered weight = 50
        # Completion = 50/65 * 100 = 76.9%
        assert result.progress_metrics.total_weight == 65
        assert result.progress_metrics.answered_weight == 50
        assert result.progress_metrics.completion_percent == 77  # Rounded

    @pytest.mark.asyncio
    async def test_zero_weight_questions(self, service, mock_db_session):
        """Test handling of questions with zero weight."""
        # Arrange
        child_flow_id = uuid4()
        asset_id = uuid4()

        mock_questions_result = MagicMock()
        mock_questions_result.fetchall.return_value = [
            ("q_1", "Question 1", True, 0, "Section"),  # Zero weight
            ("q_2", "Question 2", True, 10, "Section"),
        ]

        mock_answers_result = MagicMock()
        mock_answers_result.fetchall.return_value = []

        mock_db_session.execute.side_effect = [
            mock_questions_result,
            mock_answers_result,
        ]

        # Act
        result = await service.analyze_gaps(
            child_flow_id=child_flow_id,
            asset_id=asset_id,
            analysis_mode="fast",
        )

        # Assert
        assert result.progress_metrics.total_weight == 10
        assert result.total_gaps == 2
