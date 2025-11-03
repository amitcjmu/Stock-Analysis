"""
Unit tests for questionnaire caching functionality.

Tests the Phase 3 implementation of questionnaire template caching
and batch deduplication for Collection Flow.

Per BULK_UPLOAD_ENRICHMENT_ARCHITECTURE_ANALYSIS.md Part 6.2
"""

import logging
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.services.crewai_flows.memory.tenant_memory_manager import (
    LearningScope,
    TenantMemoryManager,
)
from app.services.ai_analysis.questionnaire_generator.tools.generation import (
    QuestionnaireGenerationTool,
)
from app.services.ai_analysis.questionnaire_generator.service.processors import (
    QuestionnaireProcessor,
)

logger = logging.getLogger(__name__)


class TestQuestionnaireTemplateCaching:
    """Test TenantMemoryManager questionnaire caching methods"""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        return MagicMock()

    @pytest.fixture
    def mock_crewai_service(self):
        """Mock CrewAI service"""
        return MagicMock()

    @pytest.fixture
    def memory_manager(self, mock_db_session, mock_crewai_service):
        """Create TenantMemoryManager instance"""
        return TenantMemoryManager(mock_crewai_service, mock_db_session)

    @pytest.mark.asyncio
    async def test_store_questionnaire_template(self, memory_manager, mock_db_session):
        """Test storing questionnaire template in cache"""
        # Mock the underlying store_learning method
        with patch.object(
            memory_manager, "store_learning", new_callable=AsyncMock
        ) as mock_store:
            mock_store.return_value = str(uuid4())

            # Test data
            client_account_id = 1
            engagement_id = 1
            asset_type = "database"
            gap_pattern = "backup_strategy_replication_config"
            questions = [
                {
                    "question_id": "q1",
                    "question_text": "What is the backup strategy for {asset_name}?",
                    "field_type": "text",
                },
                {
                    "question_id": "q2",
                    "question_text": "Describe replication configuration for {asset_name}?",
                    "field_type": "textarea",
                },
            ]
            metadata = {"generated_by": "QuestionGenerationTool"}

            # Store template
            await memory_manager.store_questionnaire_template(
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                asset_type=asset_type,
                gap_pattern=gap_pattern,
                questions=questions,
                metadata=metadata,
            )

            # Verify store_learning was called with correct parameters
            assert mock_store.called
            call_args = mock_store.call_args
            assert call_args.kwargs["client_account_id"] == client_account_id
            assert call_args.kwargs["engagement_id"] == engagement_id
            assert call_args.kwargs["scope"] == LearningScope.CLIENT
            assert call_args.kwargs["pattern_type"] == "questionnaire_template"

            # Verify pattern_data structure
            pattern_data = call_args.kwargs["pattern_data"]
            assert pattern_data["cache_key"] == f"{asset_type}_{gap_pattern}"
            assert pattern_data["questions"] == questions
            assert pattern_data["asset_type"] == asset_type
            assert pattern_data["gap_pattern"] == gap_pattern
            assert pattern_data["question_count"] == 2
            assert "generated_at" in pattern_data

            logger.info(
                f"✅ Test passed: store_questionnaire_template stored cache_key='{pattern_data['cache_key']}'"
            )

    @pytest.mark.asyncio
    async def test_retrieve_questionnaire_template_cache_hit(self, memory_manager):
        """Test retrieving questionnaire template - cache hit scenario"""
        # Mock retrieve_similar_patterns to return a cached template
        with patch.object(
            memory_manager, "retrieve_similar_patterns", new_callable=AsyncMock
        ) as mock_retrieve:
            mock_questions = [
                {"question_id": "q1", "question_text": "Cached question 1"},
                {"question_id": "q2", "question_text": "Cached question 2"},
            ]

            mock_retrieve.return_value = [
                {
                    "pattern_id": str(uuid4()),
                    "pattern_type": "questionnaire_template",
                    "pattern_data": {
                        "cache_key": "database_backup_strategy_replication_config",
                        "questions": mock_questions,
                        "usage_count": 5,
                        "metadata": {},
                    },
                    "similarity": 0.98,
                }
            ]

            # Retrieve template
            result = await memory_manager.retrieve_questionnaire_template(
                client_account_id=1,
                engagement_id=1,
                asset_type="database",
                gap_pattern="backup_strategy_replication_config",
            )

            # Verify cache hit
            assert result["cache_hit"] is True
            assert result["questions"] == mock_questions
            assert result["usage_count"] == 6  # Incremented
            assert result["similarity"] == 0.98

            logger.info(
                f"✅ Test passed: retrieve_questionnaire_template cache HIT "
                f"(usage_count={result['usage_count']}, similarity={result['similarity']})"
            )

    @pytest.mark.asyncio
    async def test_retrieve_questionnaire_template_cache_miss(self, memory_manager):
        """Test retrieving questionnaire template - cache miss scenario"""
        # Mock retrieve_similar_patterns to return empty list
        with patch.object(
            memory_manager, "retrieve_similar_patterns", new_callable=AsyncMock
        ) as mock_retrieve:
            mock_retrieve.return_value = []

            # Retrieve template
            result = await memory_manager.retrieve_questionnaire_template(
                client_account_id=1,
                engagement_id=1,
                asset_type="server",
                gap_pattern="cpu_cores_memory_gb",
            )

            # Verify cache miss
            assert result["cache_hit"] is False
            assert result["questions"] == []
            assert result["usage_count"] == 0
            assert result["similarity"] == 0

            logger.info("✅ Test passed: retrieve_questionnaire_template cache MISS")


class TestQuestionGenerationWithCaching:
    """Test QuestionnaireGenerationTool caching integration"""

    @pytest.fixture
    def question_tool(self):
        """Create QuestionnaireGenerationTool instance"""
        return QuestionnaireGenerationTool()

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        return MagicMock()

    @pytest.mark.asyncio
    async def test_generate_questions_for_asset_cache_hit(
        self, question_tool, mock_db_session
    ):
        """Test question generation with cache hit"""
        # Mock memory manager to return cached questions
        mock_memory_manager = MagicMock()
        mock_memory_manager.retrieve_questionnaire_template = AsyncMock(
            return_value={
                "cache_hit": True,
                "questions": [
                    {"question_id": "q1", "question_text": "Cached question 1"},
                    {"question_id": "q2", "question_text": "Cached question 2"},
                ],
                "usage_count": 10,
                "similarity": 0.95,
            }
        )

        question_tool._memory_manager = mock_memory_manager

        # Generate questions
        questions = await question_tool.generate_questions_for_asset(
            asset_id=str(uuid4()),
            asset_type="database",
            gaps=["backup_strategy", "replication_config"],
            client_account_id=1,
            engagement_id=1,
            db_session=mock_db_session,
        )

        # Verify cache was used
        assert len(questions) == 2
        assert mock_memory_manager.retrieve_questionnaire_template.called
        # Store should NOT be called on cache hit
        assert (
            not hasattr(mock_memory_manager, "store_questionnaire_template")
            or not mock_memory_manager.store_questionnaire_template.called
        )

        logger.info(
            f"✅ Test passed: generate_questions_for_asset used cache (returned {len(questions)} questions)"
        )

    @pytest.mark.asyncio
    async def test_generate_questions_for_asset_cache_miss(
        self, question_tool, mock_db_session
    ):
        """Test question generation with cache miss (generates fresh)"""
        # Mock memory manager to return cache miss
        mock_memory_manager = MagicMock()
        mock_memory_manager.retrieve_questionnaire_template = AsyncMock(
            return_value={
                "cache_hit": False,
                "questions": [],
                "usage_count": 0,
                "similarity": 0,
            }
        )
        mock_memory_manager.store_questionnaire_template = AsyncMock(
            return_value=str(uuid4())
        )

        question_tool._memory_manager = mock_memory_manager

        # Mock _arun to simulate question generation
        mock_generated_questions = [
            {"question_id": "q1", "question_text": "Generated question 1"},
            {"question_id": "q2", "question_text": "Generated question 2"},
            {"question_id": "q3", "question_text": "Generated question 3"},
        ]

        with patch.object(
            question_tool,
            "_arun",
            new_callable=AsyncMock,
            return_value={
                "status": "success",
                "questionnaires": [{"questions": mock_generated_questions}],
            },
        ):
            # Generate questions
            questions = await question_tool.generate_questions_for_asset(
                asset_id=str(uuid4()),
                asset_type="server",
                gaps=["cpu_cores", "memory_gb", "os"],
                client_account_id=1,
                engagement_id=1,
                db_session=mock_db_session,
            )

            # Verify fresh generation occurred
            assert len(questions) == 3
            assert mock_memory_manager.retrieve_questionnaire_template.called
            # Store SHOULD be called on cache miss
            assert mock_memory_manager.store_questionnaire_template.called

            logger.info(
                f"✅ Test passed: generate_questions_for_asset generated fresh "
                f"({len(questions)} questions) and stored in cache"
            )

    def test_create_gap_pattern(self, question_tool):
        """Test gap pattern creation (deterministic sorting)"""
        gaps1 = ["cpu_cores", "memory_gb", "os"]
        gaps2 = ["os", "cpu_cores", "memory_gb"]  # Different order
        gaps3 = ["backup_strategy", "replication_config"]

        pattern1 = question_tool._create_gap_pattern(gaps1)
        pattern2 = question_tool._create_gap_pattern(gaps2)
        pattern3 = question_tool._create_gap_pattern(gaps3)

        # Same gaps, different order should produce same pattern
        assert pattern1 == pattern2
        assert pattern1 == "cpu_cores_memory_gb_os"

        # Different gaps should produce different pattern
        assert pattern3 == "backup_strategy_replication_config"
        assert pattern1 != pattern3

        logger.info(
            f"✅ Test passed: gap patterns are deterministic (pattern1={pattern1}, pattern3={pattern3})"
        )

    def test_customize_questions(self, question_tool):
        """Test question customization for specific asset"""
        cached_questions = [
            {
                "question_id": "q1",
                "question_text": "What is the backup strategy for {asset_name}?",
                "metadata": {"asset_id": "old_id"},
            },
            {
                "question_id": "q2",
                "question_text": "Describe configuration for {asset_name}",
                "metadata": {},
            },
        ]

        asset_id = str(uuid4())
        asset_name = "Production Database"

        customized = question_tool._customize_questions(
            cached_questions, asset_id, asset_name
        )

        # Verify customization
        assert len(customized) == 2
        assert "Production Database" in customized[0]["question_text"]
        assert asset_id in customized[0]["metadata"]["asset_id"]
        assert "Production Database" in customized[1]["question_text"]

        logger.info(
            f"✅ Test passed: questions customized for asset_name='{asset_name}'"
        )


class TestBatchDeduplication:
    """Test batch processing with deduplication"""

    @pytest.fixture
    def processor(self):
        """Create QuestionnaireProcessor instance"""
        return QuestionnaireProcessor(agents=[], tasks=[], name="test_processor")

    @pytest.fixture
    def question_tool(self):
        """Create mock question generation tool"""
        tool = MagicMock()
        tool.generate_questions_for_asset = AsyncMock(
            return_value=[
                {"question_id": "q1", "question_text": "Question 1"},
                {"question_id": "q2", "question_text": "Question 2"},
            ]
        )
        tool._customize_questions = MagicMock(
            side_effect=lambda qs, aid, aname=None: qs  # Return unchanged for simplicity
        )
        return tool

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        return MagicMock()

    @pytest.mark.asyncio
    async def test_batch_deduplication_basic(
        self, processor, question_tool, mock_db_session
    ):
        """Test basic batch deduplication (same asset type + gaps)"""
        # 100 servers with identical gaps
        assets = [
            {
                "asset_id": str(uuid4()),
                "asset_type": "server",
                "missing_fields": ["cpu_cores", "memory_gb", "os"],
                "asset_name": f"Server-{i}",
            }
            for i in range(100)
        ]

        # Process batch
        result = await processor.process_asset_batch_with_deduplication(
            assets=assets,
            question_generator_tool=question_tool,
            client_account_id=1,
            engagement_id=1,
            db_session=mock_db_session,
        )

        # Verify deduplication
        assert len(result) == 100  # All assets have questionnaires
        # Should only generate once (all servers have same gap pattern)
        assert question_tool.generate_questions_for_asset.call_count == 1

        logger.info(
            "✅ Test passed: 100 identical servers → 1 generation call "
            "(99% deduplication)"
        )

    @pytest.mark.asyncio
    async def test_batch_deduplication_mixed_patterns(
        self, processor, question_tool, mock_db_session
    ):
        """Test batch deduplication with multiple gap patterns"""
        # 50 servers with pattern A, 30 databases with pattern B, 20 apps with pattern C
        assets = (
            [
                {
                    "asset_id": str(uuid4()),
                    "asset_type": "server",
                    "missing_fields": ["cpu_cores", "memory_gb"],
                    "asset_name": f"Server-{i}",
                }
                for i in range(50)
            ]
            + [
                {
                    "asset_id": str(uuid4()),
                    "asset_type": "database",
                    "missing_fields": ["backup_strategy", "replication_config"],
                    "asset_name": f"DB-{i}",
                }
                for i in range(30)
            ]
            + [
                {
                    "asset_id": str(uuid4()),
                    "asset_type": "application",
                    "missing_fields": ["framework", "language"],
                    "asset_name": f"App-{i}",
                }
                for i in range(20)
            ]
        )

        # Process batch
        result = await processor.process_asset_batch_with_deduplication(
            assets=assets,
            question_generator_tool=question_tool,
            client_account_id=1,
            engagement_id=1,
            db_session=mock_db_session,
        )

        # Verify deduplication
        assert len(result) == 100  # All assets have questionnaires
        # Should generate 3 times (3 unique patterns)
        assert question_tool.generate_questions_for_asset.call_count == 3

        # Calculate deduplication ratio
        dedup_ratio = (1 - 3 / 100) * 100
        logger.info(
            f"✅ Test passed: 100 mixed assets → 3 generation calls "
            f"({dedup_ratio:.0f}% deduplication)"
        )

    @pytest.mark.asyncio
    async def test_empty_asset_list(self, processor, question_tool, mock_db_session):
        """Test handling of empty asset list"""
        result = await processor.process_asset_batch_with_deduplication(
            assets=[],
            question_generator_tool=question_tool,
            client_account_id=1,
            engagement_id=1,
            db_session=mock_db_session,
        )

        assert result == {}
        assert question_tool.generate_questions_for_asset.call_count == 0

        logger.info("✅ Test passed: empty asset list handled correctly")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])
