"""
Unit Tests for DynamicQuestionEngine

Tests the dynamic question filtering service including asset-type filtering,
agent pruning, dependency tracking, and question re-emergence.

Coverage Target: 90%+

Per Issue #783 and design doc Section 8.1.
Rewritten based on actual implementation.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID, uuid4
from datetime import datetime

from app.services.collection.dynamic_question_engine import DynamicQuestionEngine
from app.core.context import RequestContext
from app.models.collection_flow import (
    AdaptiveQuestionnaire,
    CollectionQuestionRules,
    CollectionAnswerHistory,
)
from app.schemas.collection import (
    DynamicQuestionsResponse,
    DependencyChangeResponse,
    QuestionDetail,
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
def sample_question_rules():
    """Sample question rules for different asset types"""
    rules = []
    # Application questions
    for i in range(5):
        rule = Mock(spec=CollectionQuestionRules)
        rule.question_id = f"app_{i:02d}_question"
        rule.question_text = f"Application Question {i}"
        rule.question_type = "MCQ"
        rule.answer_options = ["Option1", "Option2", "Option3"]
        rule.asset_type = "Application"
        rule.is_applicable = True
        rule.is_required = i < 3  # First 3 are required
        rule.weight = 10 if i < 3 else 5
        rule.section = "General"
        rule.display_order = i
        rules.append(rule)

    # Server questions
    for i in range(5):
        rule = Mock(spec=CollectionQuestionRules)
        rule.question_id = f"server_{i:02d}_question"
        rule.question_text = f"Server Question {i}"
        rule.question_type = "MCQ"
        rule.answer_options = ["Option1", "Option2"]
        rule.asset_type = "Server"
        rule.is_applicable = True
        rule.is_required = i < 2
        rule.weight = 10 if i < 2 else 5
        rule.section = "Infrastructure"
        rule.display_order = i
        rules.append(rule)

    return rules


class TestDynamicQuestionEngine:
    """Test DynamicQuestionEngine class"""

    def test_initialization(self, mock_db_session, mock_context):
        """Test service initialization"""
        service = DynamicQuestionEngine(db=mock_db_session, context=mock_context)

        assert service.db == mock_db_session
        assert service.context == mock_context
        assert service.question_rules_repo is not None
        assert service.questionnaire_repo is not None
        assert service.answer_history_repo is not None
        assert len(service.CRITICAL_FIELDS) == 5

    def test_critical_fields_constant(self, mock_db_session, mock_context):
        """Test CRITICAL_FIELDS constant values"""
        service = DynamicQuestionEngine(db=mock_db_session, context=mock_context)

        assert "os_version" in service.CRITICAL_FIELDS
        assert "ip_address" in service.CRITICAL_FIELDS
        assert "decommission_status" in service.CRITICAL_FIELDS
        assert "hosting_platform" in service.CRITICAL_FIELDS
        assert "database_type" in service.CRITICAL_FIELDS

    @pytest.mark.asyncio
    async def test_get_filtered_questions_by_asset_type(
        self, mock_db_session, mock_context, sample_question_rules
    ):
        """Test filtering questions by asset type"""
        service = DynamicQuestionEngine(db=mock_db_session, context=mock_context)
        child_flow_id = uuid4()
        asset_id = uuid4()

        # Mock rules repository to return only Application rules
        app_rules = [r for r in sample_question_rules if r.asset_type == "Application"]
        service.question_rules_repo.get_by_filters = AsyncMock(return_value=app_rules)
        service.questionnaire_repo.get_by_filters = AsyncMock(return_value=[])

        result = await service.get_filtered_questions(
            child_flow_id=child_flow_id,
            asset_id=asset_id,
            asset_type="Application",
            include_answered=False,
            refresh_agent_analysis=False,
        )

        assert isinstance(result, DynamicQuestionsResponse)
        assert result.asset_type == "Application"
        assert result.total_questions == 5
        assert len(result.questions) == 5
        assert result.agent_status == "not_requested"
        assert result.fallback_used is False
        assert result.include_answered is False

    @pytest.mark.asyncio
    async def test_empty_asset_type(self, mock_db_session, mock_context):
        """Test handling None/empty asset type"""
        service = DynamicQuestionEngine(db=mock_db_session, context=mock_context)
        child_flow_id = uuid4()
        asset_id = uuid4()

        result = await service.get_filtered_questions(
            child_flow_id=child_flow_id,
            asset_id=asset_id,
            asset_type=None,
            include_answered=False,
            refresh_agent_analysis=False,
        )

        assert isinstance(result, DynamicQuestionsResponse)
        assert result.asset_type is None
        assert len(result.questions) == 0
        assert result.total_questions == 0
        assert result.agent_status == "not_requested"

    @pytest.mark.asyncio
    async def test_get_filtered_questions_exclude_answered(
        self, mock_db_session, mock_context, sample_question_rules
    ):
        """Test filtering out already answered questions"""
        service = DynamicQuestionEngine(db=mock_db_session, context=mock_context)
        child_flow_id = uuid4()
        asset_id = uuid4()

        app_rules = [r for r in sample_question_rules if r.asset_type == "Application"]
        service.question_rules_repo.get_by_filters = AsyncMock(return_value=app_rules)

        # Mock questionnaire with some answered questions in responses_collected
        questionnaire = Mock(spec=AdaptiveQuestionnaire)
        questionnaire.responses_collected = {
            "app_00_question": "Answer 0",
            "app_01_question": "Answer 1",
            "app_02_question": "Answer 2",
        }
        service.questionnaire_repo.get_by_filters = AsyncMock(return_value=[questionnaire])

        result = await service.get_filtered_questions(
            child_flow_id=child_flow_id,
            asset_id=asset_id,
            asset_type="Application",
            include_answered=False,
            refresh_agent_analysis=False,
        )

        assert isinstance(result, DynamicQuestionsResponse)
        # Should exclude the 3 answered questions
        assert len(result.questions) == 2
        # Remaining questions should be app_03 and app_04
        question_ids = {q.question_id for q in result.questions}
        assert "app_03_question" in question_ids
        assert "app_04_question" in question_ids

    @pytest.mark.asyncio
    async def test_get_filtered_questions_include_answered(
        self, mock_db_session, mock_context, sample_question_rules
    ):
        """Test including already answered questions"""
        service = DynamicQuestionEngine(db=mock_db_session, context=mock_context)
        child_flow_id = uuid4()
        asset_id = uuid4()

        app_rules = [r for r in sample_question_rules if r.asset_type == "Application"]
        service.question_rules_repo.get_by_filters = AsyncMock(return_value=app_rules)

        questionnaire = Mock(spec=AdaptiveQuestionnaire)
        questionnaire.responses_collected = {"app_00_question": "Answer 0"}
        service.questionnaire_repo.get_by_filters = AsyncMock(return_value=[questionnaire])

        result = await service.get_filtered_questions(
            child_flow_id=child_flow_id,
            asset_id=asset_id,
            asset_type="Application",
            include_answered=True,
            refresh_agent_analysis=False,
        )

        assert isinstance(result, DynamicQuestionsResponse)
        # Should include all questions regardless of answered status
        assert len(result.questions) == 5
        assert result.include_answered is True

    @pytest.mark.asyncio
    async def test_agent_pruning_success(
        self, mock_db_session, mock_context, sample_question_rules
    ):
        """Test successful agent-based question pruning"""
        service = DynamicQuestionEngine(db=mock_db_session, context=mock_context)
        child_flow_id = uuid4()
        asset_id = uuid4()

        app_rules = [r for r in sample_question_rules if r.asset_type == "Application"]
        service.question_rules_repo.get_by_filters = AsyncMock(return_value=app_rules)
        service.questionnaire_repo.get_by_filters = AsyncMock(return_value=[])

        # Mock multi_model_service to return only 2 question IDs
        with patch("app.services.collection.dynamic_question_engine.multi_model_service") as mock_mms:
            mock_mms.generate_response = AsyncMock(
                return_value="app_00_question, app_02_question"
            )

            result = await service.get_filtered_questions(
                child_flow_id=child_flow_id,
                asset_id=asset_id,
                asset_type="Application",
                include_answered=False,
                refresh_agent_analysis=True,
            )

            assert isinstance(result, DynamicQuestionsResponse)
            assert result.agent_status == "completed"
            assert result.fallback_used is False
            # Should only return the 2 questions from agent pruning
            assert len(result.questions) == 2
            question_ids = {q.question_id for q in result.questions}
            assert "app_00_question" in question_ids
            assert "app_02_question" in question_ids

    @pytest.mark.asyncio
    async def test_agent_pruning_timeout_fallback(
        self, mock_db_session, mock_context, sample_question_rules
    ):
        """Test fallback when agent pruning times out"""
        service = DynamicQuestionEngine(db=mock_db_session, context=mock_context)
        child_flow_id = uuid4()
        asset_id = uuid4()

        app_rules = [r for r in sample_question_rules if r.asset_type == "Application"]
        service.question_rules_repo.get_by_filters = AsyncMock(return_value=app_rules)
        service.questionnaire_repo.get_by_filters = AsyncMock(return_value=[])

        # Mock timeout
        with patch("app.services.collection.dynamic_question_engine.multi_model_service") as mock_mms:
            import asyncio
            mock_mms.generate_response = AsyncMock(
                side_effect=asyncio.TimeoutError("Agent timeout")
            )

            result = await service.get_filtered_questions(
                child_flow_id=child_flow_id,
                asset_id=asset_id,
                asset_type="Application",
                include_answered=False,
                refresh_agent_analysis=True,
            )

            assert isinstance(result, DynamicQuestionsResponse)
            assert result.agent_status == "fallback"
            assert result.fallback_used is True
            # Should return all questions (graceful degradation)
            assert len(result.questions) == 5

    @pytest.mark.asyncio
    async def test_agent_pruning_error_fallback(
        self, mock_db_session, mock_context, sample_question_rules
    ):
        """Test fallback when agent pruning fails with error"""
        service = DynamicQuestionEngine(db=mock_db_session, context=mock_context)
        child_flow_id = uuid4()
        asset_id = uuid4()

        app_rules = [r for r in sample_question_rules if r.asset_type == "Application"]
        service.question_rules_repo.get_by_filters = AsyncMock(return_value=app_rules)
        service.questionnaire_repo.get_by_filters = AsyncMock(return_value=[])

        # Mock error
        with patch("app.services.collection.dynamic_question_engine.multi_model_service") as mock_mms:
            mock_mms.generate_response = AsyncMock(
                side_effect=Exception("LLM service unavailable")
            )

            result = await service.get_filtered_questions(
                child_flow_id=child_flow_id,
                asset_id=asset_id,
                asset_type="Application",
                include_answered=False,
                refresh_agent_analysis=True,
            )

            assert isinstance(result, DynamicQuestionsResponse)
            assert result.agent_status == "fallback"
            assert result.fallback_used is True
            assert len(result.questions) == 5

    @pytest.mark.asyncio
    async def test_handle_dependency_change_critical_field(
        self, mock_db_session, mock_context
    ):
        """Test dependency change for critical field"""
        service = DynamicQuestionEngine(db=mock_db_session, context=mock_context)
        asset_id = uuid4()

        # Mock questionnaire with responses
        questionnaire = Mock(spec=AdaptiveQuestionnaire)
        questionnaire.id = uuid4()
        questionnaire.responses_collected = {
            "tech_stack": "Linux 18.04",
            "supported_versions": "EOL",
        }
        service.questionnaire_repo.get_by_filters = AsyncMock(return_value=[questionnaire])
        service.answer_history_repo.create_no_commit = AsyncMock()

        result = await service.handle_dependency_change(
            changed_asset_id=asset_id,
            changed_field="os_version",  # Critical field
            old_value="Linux 18.04",
            new_value="Linux 20.04",
        )

        assert isinstance(result, DependencyChangeResponse)
        assert result.changed_field == "os_version"
        assert result.old_value == "Linux 18.04"
        assert result.new_value == "Linux 20.04"
        assert len(result.reopened_question_ids) == 3  # tech_stack, supported_versions, patch_status
        assert "Critical field change" in result.reason
        assert asset_id in result.affected_assets

    @pytest.mark.asyncio
    async def test_handle_dependency_change_non_critical_fallback(
        self, mock_db_session, mock_context
    ):
        """Test dependency change for non-critical field with agent timeout"""
        service = DynamicQuestionEngine(db=mock_db_session, context=mock_context)
        asset_id = uuid4()

        questionnaire = Mock(spec=AdaptiveQuestionnaire)
        questionnaire.id = uuid4()
        questionnaire.responses_collected = {}
        service.questionnaire_repo.get_by_filters = AsyncMock(return_value=[questionnaire])
        service.answer_history_repo.create_no_commit = AsyncMock()

        # Mock agent timeout
        with patch(
            "app.services.collection.dynamic_question_engine.TenantScopedAgentPool"
        ) as mock_pool:
            import asyncio
            mock_pool.get_agent = AsyncMock(
                side_effect=asyncio.TimeoutError("Agent timeout")
            )

            result = await service.handle_dependency_change(
                changed_asset_id=asset_id,
                changed_field="app_name",  # Non-critical
                old_value="OldApp",
                new_value="NewApp",
            )

            assert isinstance(result, DependencyChangeResponse)
            assert result.changed_field == "app_name"
            assert "Fallback" in result.reason
            assert result.reopened_question_ids == []  # No hardcoded dependency for app_name

    @pytest.mark.asyncio
    async def test_get_db_questions(
        self, mock_db_session, mock_context, sample_question_rules
    ):
        """Test _get_db_questions private method"""
        service = DynamicQuestionEngine(db=mock_db_session, context=mock_context)

        app_rules = [r for r in sample_question_rules if r.asset_type == "Application"]
        service.question_rules_repo.get_by_filters = AsyncMock(return_value=app_rules)

        result = await service._get_db_questions("Application")

        assert len(result) == 5
        assert all(isinstance(q, dict) for q in result)
        assert all("question_id" in q for q in result)
        assert all("question_text" in q for q in result)
        # Should be sorted by display_order
        assert result[0]["question_id"] == "app_00_question"
        assert result[-1]["question_id"] == "app_04_question"

    @pytest.mark.asyncio
    async def test_apply_inheritance(self, mock_db_session, mock_context):
        """Test _apply_inheritance returns base questions (placeholder)"""
        service = DynamicQuestionEngine(db=mock_db_session, context=mock_context)

        base_questions = [
            {"question_id": "q1", "question_text": "Q1"},
            {"question_id": "q2", "question_text": "Q2"},
        ]

        result = await service._apply_inheritance(base_questions, "Database")

        # Currently just returns base_questions (TODO in implementation)
        assert result == base_questions

    @pytest.mark.asyncio
    async def test_parse_question_ids(self, mock_db_session, mock_context):
        """Test _parse_question_ids helper"""
        service = DynamicQuestionEngine(db=mock_db_session, context=mock_context)

        response = "app_01_question, app_03_question, server_02_question"
        result = service._parse_question_ids(response)

        assert len(result) == 3
        assert "app_01_question" in result
        assert "app_03_question" in result
        assert "server_02_question" in result

    @pytest.mark.asyncio
    async def test_get_questionnaire(self, mock_db_session, mock_context):
        """Test _get_questionnaire helper"""
        service = DynamicQuestionEngine(db=mock_db_session, context=mock_context)
        child_flow_id = uuid4()
        asset_id = uuid4()

        questionnaire = Mock(spec=AdaptiveQuestionnaire)
        questionnaire.id = uuid4()
        service.questionnaire_repo.get_by_filters = AsyncMock(return_value=[questionnaire])

        result = await service._get_questionnaire(child_flow_id, asset_id)

        assert result == questionnaire

    @pytest.mark.asyncio
    async def test_get_questionnaire_not_found(self, mock_db_session, mock_context):
        """Test _get_questionnaire when not found"""
        service = DynamicQuestionEngine(db=mock_db_session, context=mock_context)
        child_flow_id = uuid4()
        asset_id = uuid4()

        service.questionnaire_repo.get_by_filters = AsyncMock(return_value=[])

        result = await service._get_questionnaire(child_flow_id, asset_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_reopen_dependent_questions_fallback(
        self, mock_db_session, mock_context
    ):
        """Test _reopen_dependent_questions_fallback with critical field"""
        service = DynamicQuestionEngine(db=mock_db_session, context=mock_context)
        asset_id = uuid4()

        questionnaire = Mock(spec=AdaptiveQuestionnaire)
        questionnaire.id = uuid4()
        questionnaire.responses_collected = {
            "tech_stack": "Linux",
            "supported_versions": "v1",
        }
        service.questionnaire_repo.get_by_filters = AsyncMock(return_value=[questionnaire])
        service.answer_history_repo.create_no_commit = AsyncMock()

        result = await service._reopen_dependent_questions_fallback(asset_id, "os_version")

        # Should return dependent questions for os_version
        assert len(result) == 3
        assert "tech_stack" in result
        assert "supported_versions" in result
        assert "patch_status" in result

    @pytest.mark.asyncio
    async def test_batch_reopen_questions(self, mock_db_session, mock_context):
        """Test _batch_reopen_questions helper"""
        service = DynamicQuestionEngine(db=mock_db_session, context=mock_context)
        asset_id = uuid4()

        questionnaire = Mock(spec=AdaptiveQuestionnaire)
        questionnaire.id = uuid4()
        questionnaire.responses_collected = {
            "q1": "Answer1",
            "q2": "Answer2",
        }
        service.questionnaire_repo.get_by_filters = AsyncMock(return_value=[questionnaire])
        service.answer_history_repo.create_no_commit = AsyncMock()

        await service._batch_reopen_questions(
            asset_id=asset_id,
            question_ids=["q1", "q2"],
            reason="Field changed",
        )

        # Should remove both questions from responses_collected
        assert "q1" not in questionnaire.responses_collected
        assert "q2" not in questionnaire.responses_collected
        # Should create 2 history records
        assert service.answer_history_repo.create_no_commit.call_count == 2
