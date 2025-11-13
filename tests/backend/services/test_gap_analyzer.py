"""
Unit Tests for IncrementalGapAnalyzer

Tests the incremental gap analyzer including fast/thorough modes,
dependency traversal, and progress calculation.

Coverage Target: 90%+

Per Issue #783 and design doc Section 8.1.
Rewritten based on actual implementation.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from app.services.collection.incremental_gap_analyzer import (
    IncrementalGapAnalyzer,
    GapAnalysisResults,
)
from app.core.context import RequestContext
from app.models.collection_flow import AdaptiveQuestionnaire
from app.schemas.collection import GapAnalysisResponse


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
def sample_questionnaire():
    """Sample questionnaire with questions and responses"""
    q = Mock(spec=AdaptiveQuestionnaire)
    q.id = uuid4()
    q.questions = [
        {"id": "q1", "text": "Question 1", "section": "General", "weight": 40, "is_critical": True},
        {"id": "q2", "text": "Question 2", "section": "General", "weight": 40, "is_critical": False},
        {"id": "q3", "text": "Question 3", "section": "Technical", "weight": 40, "is_critical": False},
    ]
    q.responses_collected = {"q1": "Answer1"}  # Only q1 answered
    q.question_count = 3
    return q


class TestGapAnalysisResults:
    """Test GapAnalysisResults data class"""

    def test_initialization(self):
        """Test GapAnalysisResults initialization"""
        results = GapAnalysisResults(
            assets_analyzed=10,
            new_gaps_identified=5,
            gaps_closed=3,
            mode="fast",
        )

        assert results.assets_analyzed == 10
        assert results.new_gaps_identified == 5
        assert results.gaps_closed == 3
        assert results.mode == "fast"

    def test_to_dict(self):
        """Test to_dict serialization"""
        results = GapAnalysisResults(
            assets_analyzed=10,
            new_gaps_identified=5,
            gaps_closed=3,
            mode="thorough",
            dependency_depth_reached=2,
            total_dependencies_analyzed=15,
        )

        result_dict = results.to_dict()

        assert result_dict["assets_analyzed"] == 10
        assert result_dict["dependency_depth_reached"] == 2


class TestIncrementalGapAnalyzer:
    """Test IncrementalGapAnalyzer class"""

    def test_initialization(self, mock_db_session, mock_context):
        """Test service initialization"""
        service = IncrementalGapAnalyzer(db=mock_db_session, context=mock_context)

        assert service.db == mock_db_session
        assert service.MAX_DEPTH == 3
        assert service.MAX_ASSETS == 10_000

    @pytest.mark.asyncio
    async def test_analyze_gaps_with_questionnaire(
        self, mock_db_session, mock_context, sample_questionnaire
    ):
        """Test gap analysis for asset with questionnaire"""
        service = IncrementalGapAnalyzer(db=mock_db_session, context=mock_context)
        child_flow_id = uuid4()
        asset_id = uuid4()

        service.questionnaire_repo.get_by_filters = AsyncMock(
            return_value=[sample_questionnaire]
        )

        result = await service.analyze_gaps(
            child_flow_id=child_flow_id, asset_id=asset_id, mode="fast"
        )

        assert isinstance(result, GapAnalysisResponse)
        assert result.total_gaps == 2  # q2 and q3 unanswered
        assert result.progress_metrics.answered_questions == 1

    @pytest.mark.asyncio
    async def test_analyze_gaps_no_questionnaire(
        self, mock_db_session, mock_context
    ):
        """Test gap analysis when questionnaire doesn't exist"""
        service = IncrementalGapAnalyzer(db=mock_db_session, context=mock_context)
        service.questionnaire_repo.get_by_filters = AsyncMock(return_value=[])

        result = await service.analyze_gaps(
            child_flow_id=uuid4(), asset_id=uuid4(), mode="fast"
        )

        assert result.total_gaps == 0

    @pytest.mark.asyncio
    async def test_recalculate_fast_mode(
        self, mock_db_session, mock_context, sample_questionnaire
    ):
        """Test fast mode recalculation"""
        service = IncrementalGapAnalyzer(db=mock_db_session, context=mock_context)
        service.questionnaire_repo.get_by_filters = AsyncMock(
            return_value=[sample_questionnaire]
        )

        result = await service.recalculate_incremental(
            asset_ids=[uuid4(), uuid4()], mode="fast"
        )

        assert result.assets_analyzed == 2
        assert result.mode == "fast"

    @pytest.mark.asyncio
    async def test_recalculate_thorough_mode(
        self, mock_db_session, mock_context, sample_questionnaire
    ):
        """Test thorough mode with dependencies"""
        service = IncrementalGapAnalyzer(db=mock_db_session, context=mock_context)
        service.questionnaire_repo.get_by_filters = AsyncMock(
            return_value=[sample_questionnaire]
        )

        with patch.object(
            service, "_build_dependency_graph", AsyncMock(return_value={})
        ):
            result = await service.recalculate_incremental(
                asset_ids=[uuid4()], mode="thorough"
            )

            assert result.mode == "thorough"

    @pytest.mark.asyncio
    async def test_invalid_mode(self, mock_db_session, mock_context):
        """Test error on invalid mode"""
        service = IncrementalGapAnalyzer(db=mock_db_session, context=mock_context)

        with pytest.raises(ValueError, match="Invalid mode"):
            await service.recalculate_incremental(
                asset_ids=[uuid4()], mode="invalid"
            )

    @pytest.mark.asyncio
    async def test_identify_gaps(
        self, mock_db_session, mock_context, sample_questionnaire
    ):
        """Test gap identification"""
        service = IncrementalGapAnalyzer(db=mock_db_session, context=mock_context)

        gaps = await service._identify_gaps(sample_questionnaire)

        assert len(gaps) == 2
        gap_ids = [g["question_id"] for g in gaps]
        assert "q2" in gap_ids
        assert "q3" in gap_ids
