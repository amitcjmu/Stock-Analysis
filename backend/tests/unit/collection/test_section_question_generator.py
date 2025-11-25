"""
Unit tests for SectionQuestionGenerator.

Tests the tool-free question generation architecture including:
- Clear, unambiguous prompts with NO TOOLS
- TRUE gaps only filtering
- Cross-section deduplication
- Data awareness context formatting
- Intelligent option generation
- JSON parsing with dirtyjson fallback
- Multi-tenant scoping and observability

CC Generated for Issue #1113 - SectionQuestionGenerator (Tool-Free)
Per ADR-037: Intelligent Gap Detection and Questionnaire Generation Architecture
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.models.asset.models import Asset
from app.services.collection.gap_analysis.models import DataSource, IntelligentGap
from app.services.collection.gap_analysis.section_question_generator import (
    SectionQuestionGenerator,
)


@pytest.fixture
def mock_asset():
    """Create a mock Asset for testing."""
    asset = MagicMock(spec=Asset)
    asset.id = uuid4()
    asset.name = "Test Server 01"
    asset.asset_type = "Application Server"
    asset.operating_system = "IBM AIX 7.3"
    asset.environment_type = "Production"
    return asset


@pytest.fixture
def mock_asset_linux():
    """Create a mock Linux asset for testing."""
    asset = MagicMock(spec=Asset)
    asset.id = uuid4()
    asset.name = "Linux DB 01"
    asset.asset_type = "Database Server"
    asset.operating_system = "Red Hat Enterprise Linux 8"
    asset.environment_type = "Production"
    return asset


@pytest.fixture
def infrastructure_true_gaps():
    """Create TRUE gaps for infrastructure section."""
    return [
        IntelligentGap(
            field_id="cpu_count",
            field_name="CPU Count",
            priority="critical",
            data_found=[],  # TRUE gap - no data anywhere
            is_true_gap=True,
            confidence_score=1.0,
            section="infrastructure",
        ),
        IntelligentGap(
            field_id="memory_gb",
            field_name="Memory (GB)",
            priority="high",
            data_found=[],
            is_true_gap=True,
            confidence_score=0.98,
            section="infrastructure",
        ),
        IntelligentGap(
            field_id="disk_space_gb",
            field_name="Disk Space (GB)",
            priority="medium",
            data_found=[],
            is_true_gap=True,
            confidence_score=0.95,
            section="infrastructure",
        ),
    ]


@pytest.fixture
def resilience_true_gaps():
    """Create TRUE gaps for resilience section."""
    return [
        IntelligentGap(
            field_id="backup_frequency",
            field_name="Backup Frequency",
            priority="critical",
            data_found=[],
            is_true_gap=True,
            confidence_score=1.0,
            section="resilience",
        ),
        IntelligentGap(
            field_id="disaster_recovery_plan",
            field_name="Disaster Recovery Plan",
            priority="high",
            data_found=[],
            is_true_gap=True,
            confidence_score=0.97,
            section="resilience",
        ),
    ]


@pytest.fixture
def mixed_gaps_infrastructure():
    """
    Create MIXED gaps (TRUE + data-exists-elsewhere) for infrastructure.

    Only TRUE gaps should generate questions.
    """
    return [
        # TRUE gap
        IntelligentGap(
            field_id="cpu_count",
            field_name="CPU Count",
            priority="critical",
            data_found=[],
            is_true_gap=True,
            confidence_score=1.0,
            section="infrastructure",
        ),
        # Data exists elsewhere - should NOT generate question
        IntelligentGap(
            field_id="operating_system",
            field_name="Operating System",
            priority="critical",
            data_found=[
                DataSource(
                    source_type="custom_attributes",
                    field_path="custom_attributes.os",
                    value="IBM AIX 7.3",
                    confidence=0.95,
                )
            ],
            is_true_gap=False,
            confidence_score=0.05,
            section="infrastructure",
        ),
    ]


@pytest.fixture
def data_map_with_coverage(mock_asset):
    """Create data map from DataAwarenessAgent."""
    return {
        "flow_id": str(uuid4()),
        "assets": [
            {
                "asset_id": str(mock_asset.id),
                "asset_name": mock_asset.name,
                "data_coverage": {
                    "standard_columns": 60,
                    "custom_attributes": 30,
                    "enrichment_data": 10,
                    "environment": 15,
                    "canonical_apps": 5,
                    "related_assets": 0,
                },
                "true_gaps": [
                    {
                        "field": "cpu_count",
                        "priority": "critical",
                        "section": "infrastructure",
                        "checked_sources": 6,
                        "found_in": [],
                    }
                ],
                "data_exists_elsewhere": [
                    {
                        "field": "operating_system",
                        "found_in": "custom_attributes.os",
                        "value": "IBM AIX 7.3",
                        "no_question_needed": True,
                    },
                    {
                        "field": "hostname",
                        "found_in": "custom_attributes.host",
                        "value": "test-server-01",
                        "no_question_needed": True,
                    },
                ],
            }
        ],
        "cross_asset_patterns": {
            "common_gaps": ["cpu_count", "memory_gb"],
            "common_data_sources": ["custom_attributes"],
            "recommendations": [
                "Use custom_attributes for additional fields",
                "Populate enrichment_data for resilience info",
            ],
        },
    }


@pytest.fixture
def valid_llm_response():
    """Create valid LLM response JSON."""
    return json.dumps(
        [
            {
                "field_id": "cpu_count",
                "question_text": "How many CPU cores does this asset have?",
                "field_type": "number",
                "required": True,
                "priority": "critical",
                "options": None,
                "help_text": "Total number of physical CPU cores",
                "section": "infrastructure",
            },
            {
                "field_id": "memory_gb",
                "question_text": "What is the total memory in GB?",
                "field_type": "number",
                "required": True,
                "priority": "high",
                "options": None,
                "help_text": "Total RAM in gigabytes",
                "section": "infrastructure",
            },
        ]
    )


class TestSectionQuestionGenerator:
    """Test suite for SectionQuestionGenerator."""

    @pytest.mark.asyncio
    async def test_generate_questions_basic(
        self,
        mock_asset,
        infrastructure_true_gaps,
        data_map_with_coverage,
        valid_llm_response,
    ):
        """Test basic question generation for single section."""
        generator = SectionQuestionGenerator()

        with patch(
            "app.services.collection.gap_analysis.section_question_generator.multi_model_service.generate_response",
            new_callable=AsyncMock,
        ) as mock_llm:
            mock_llm.return_value = {
                "response": valid_llm_response,
                "tokens_used": 150,
            }

            questions = await generator.generate_questions_for_section(
                asset=mock_asset,
                section_id="infrastructure",
                true_gaps=infrastructure_true_gaps,
                data_map=data_map_with_coverage,
                previously_asked_questions=[],
                client_account_id=1,
                engagement_id=123,
            )

        # Assertions
        assert len(questions) == 2
        assert questions[0]["field_id"] == "cpu_count"
        assert questions[0]["section"] == "infrastructure"
        assert questions[1]["field_id"] == "memory_gb"

        # Verify LLM was called with correct metadata
        mock_llm.assert_called_once()
        call_args = mock_llm.call_args
        assert call_args.kwargs["task_type"] == "questionnaire_generation"
        assert call_args.kwargs["client_account_id"] == 1
        assert call_args.kwargs["engagement_id"] == 123
        assert (
            call_args.kwargs["metadata"]["feature_context"]
            == "section_question_generator"
        )
        assert call_args.kwargs["metadata"]["section_id"] == "infrastructure"
        assert call_args.kwargs["metadata"]["gap_count"] == 3

    @pytest.mark.asyncio
    async def test_no_gaps_returns_empty_list(self, mock_asset, data_map_with_coverage):
        """Test that empty gaps list returns empty questions."""
        generator = SectionQuestionGenerator()

        questions = await generator.generate_questions_for_section(
            asset=mock_asset,
            section_id="infrastructure",
            true_gaps=[],  # No gaps
            data_map=data_map_with_coverage,
            previously_asked_questions=[],
            client_account_id=1,
            engagement_id=123,
        )

        assert questions == []

    @pytest.mark.asyncio
    async def test_filters_gaps_to_section_only(
        self,
        mock_asset,
        infrastructure_true_gaps,
        resilience_true_gaps,
        data_map_with_coverage,
        valid_llm_response,
    ):
        """Test that gaps are filtered to current section only."""
        generator = SectionQuestionGenerator()

        # Mix infrastructure + resilience gaps
        all_gaps = infrastructure_true_gaps + resilience_true_gaps

        with patch(
            "app.services.collection.gap_analysis.section_question_generator.multi_model_service.generate_response",
            new_callable=AsyncMock,
        ) as mock_llm:
            mock_llm.return_value = {
                "response": valid_llm_response,
                "tokens_used": 150,
            }

            await generator.generate_questions_for_section(
                asset=mock_asset,
                section_id="infrastructure",  # Only infrastructure
                true_gaps=all_gaps,
                data_map=data_map_with_coverage,
                previously_asked_questions=[],
                client_account_id=1,
                engagement_id=123,
            )

        # Check that prompt only includes infrastructure gaps
        call_args = mock_llm.call_args
        prompt = call_args.args[0] if call_args.args else call_args.kwargs["prompt"]

        # Should include infrastructure fields
        assert "CPU Count" in prompt
        assert "Memory (GB)" in prompt

        # Should NOT include resilience fields
        assert "Backup Frequency" not in prompt
        assert "Disaster Recovery Plan" not in prompt

    @pytest.mark.asyncio
    async def test_cross_section_deduplication(
        self,
        mock_asset,
        infrastructure_true_gaps,
        data_map_with_coverage,
        valid_llm_response,
    ):
        """Test that previously asked questions are passed to LLM for deduplication."""
        generator = SectionQuestionGenerator()

        previously_asked = [
            "What is the Operating System?",
            "What is the Environment Type?",
        ]

        with patch(
            "app.services.collection.gap_analysis.section_question_generator.multi_model_service.generate_response",
            new_callable=AsyncMock,
        ) as mock_llm:
            mock_llm.return_value = {
                "response": valid_llm_response,
                "tokens_used": 150,
            }

            await generator.generate_questions_for_section(
                asset=mock_asset,
                section_id="infrastructure",
                true_gaps=infrastructure_true_gaps,
                data_map=data_map_with_coverage,
                previously_asked_questions=previously_asked,
                client_account_id=1,
                engagement_id=123,
            )

        # Check that prompt includes previous questions
        call_args = mock_llm.call_args
        prompt = call_args.args[0] if call_args.args else call_args.kwargs["prompt"]

        assert "Questions Already Asked in Other Sections" in prompt
        assert "What is the Operating System?" in prompt
        assert "What is the Environment Type?" in prompt
        assert "DO NOT DUPLICATE" in prompt

    @pytest.mark.asyncio
    async def test_prompt_includes_do_not_use_tools(
        self,
        mock_asset,
        infrastructure_true_gaps,
        data_map_with_coverage,
        valid_llm_response,
    ):
        """Test that prompt explicitly says DO NOT use tools."""
        generator = SectionQuestionGenerator()

        with patch(
            "app.services.collection.gap_analysis.section_question_generator.multi_model_service.generate_response",
            new_callable=AsyncMock,
        ) as mock_llm:
            mock_llm.return_value = {
                "response": valid_llm_response,
                "tokens_used": 150,
            }

            await generator.generate_questions_for_section(
                asset=mock_asset,
                section_id="infrastructure",
                true_gaps=infrastructure_true_gaps,
                data_map=data_map_with_coverage,
                previously_asked_questions=[],
                client_account_id=1,
                engagement_id=123,
            )

        # Check prompt
        call_args = mock_llm.call_args
        prompt = call_args.args[0] if call_args.args else call_args.kwargs["prompt"]

        assert "DO NOT use any tools" in prompt
        assert "generate JSON directly" in prompt
        assert "Maximum 5-8 questions" in prompt

    @pytest.mark.asyncio
    async def test_prompt_includes_asset_context(
        self,
        mock_asset,
        infrastructure_true_gaps,
        data_map_with_coverage,
        valid_llm_response,
    ):
        """Test that prompt includes asset context for intelligent options."""
        generator = SectionQuestionGenerator()

        with patch(
            "app.services.collection.gap_analysis.section_question_generator.multi_model_service.generate_response",
            new_callable=AsyncMock,
        ) as mock_llm:
            mock_llm.return_value = {
                "response": valid_llm_response,
                "tokens_used": 150,
            }

            await generator.generate_questions_for_section(
                asset=mock_asset,
                section_id="infrastructure",
                true_gaps=infrastructure_true_gaps,
                data_map=data_map_with_coverage,
                previously_asked_questions=[],
                client_account_id=1,
                engagement_id=123,
            )

        # Check prompt includes asset context
        call_args = mock_llm.call_args
        prompt = call_args.args[0] if call_args.args else call_args.kwargs["prompt"]

        assert mock_asset.name in prompt
        assert mock_asset.asset_type in prompt
        assert mock_asset.operating_system in prompt
        assert mock_asset.environment_type in prompt

    @pytest.mark.asyncio
    async def test_prompt_includes_data_coverage(
        self,
        mock_asset,
        infrastructure_true_gaps,
        data_map_with_coverage,
        valid_llm_response,
    ):
        """Test that prompt includes data coverage from DataAwarenessAgent."""
        generator = SectionQuestionGenerator()

        with patch(
            "app.services.collection.gap_analysis.section_question_generator.multi_model_service.generate_response",
            new_callable=AsyncMock,
        ) as mock_llm:
            mock_llm.return_value = {
                "response": valid_llm_response,
                "tokens_used": 150,
            }

            await generator.generate_questions_for_section(
                asset=mock_asset,
                section_id="infrastructure",
                true_gaps=infrastructure_true_gaps,
                data_map=data_map_with_coverage,
                previously_asked_questions=[],
                client_account_id=1,
                engagement_id=123,
            )

        # Check prompt includes data coverage
        call_args = mock_llm.call_args
        prompt = call_args.args[0] if call_args.args else call_args.kwargs["prompt"]

        assert "Data Coverage" in prompt
        assert "standard_columns: 60% coverage" in prompt
        assert "custom_attributes: 30% coverage" in prompt
        assert "Data found in other sources" in prompt
        assert "operating_system" in prompt
        assert "custom_attributes.os" in prompt

    @pytest.mark.asyncio
    async def test_parse_llm_response_with_markdown(
        self, mock_asset, infrastructure_true_gaps, data_map_with_coverage
    ):
        """Test JSON parsing strips markdown code blocks."""
        generator = SectionQuestionGenerator()

        # LLM response wrapped in markdown
        question_data = [
            {
                "field_id": "cpu_count",
                "question_text": "How many CPU cores?",
                "field_type": "number",
                "required": True,
                "priority": "critical",
                "options": None,
                "help_text": "CPU count",
                "section": "infrastructure",
            }
        ]
        markdown_response = f"```json\n{json.dumps(question_data)}\n```"

        with patch(
            "app.services.collection.gap_analysis.section_question_generator.multi_model_service.generate_response",
            new_callable=AsyncMock,
        ) as mock_llm:
            mock_llm.return_value = {
                "response": markdown_response,
                "tokens_used": 150,
            }

            questions = await generator.generate_questions_for_section(
                asset=mock_asset,
                section_id="infrastructure",
                true_gaps=infrastructure_true_gaps,
                data_map=data_map_with_coverage,
                previously_asked_questions=[],
                client_account_id=1,
                engagement_id=123,
            )

        assert len(questions) == 1
        assert questions[0]["field_id"] == "cpu_count"

    @pytest.mark.asyncio
    async def test_parse_llm_response_with_dirtyjson_fallback(
        self, mock_asset, infrastructure_true_gaps, data_map_with_coverage
    ):
        """
        Test dirtyjson fallback for malformed JSON.

        Note: dirtyjson may not be installed in all environments.
        If not installed, the code will raise ValueError which is expected behavior.
        """
        generator = SectionQuestionGenerator()

        # Malformed JSON (trailing comma after last object in array)
        # Standard json.loads() will fail, dirtyjson can handle it
        malformed_json = """[
    {
        "field_id": "cpu_count",
        "question_text": "How many CPU cores?",
        "field_type": "number",
        "required": true,
        "priority": "critical",
        "options": null,
        "help_text": "CPU count",
        "section": "infrastructure"
    },
]"""

        with patch(
            "app.services.collection.gap_analysis.section_question_generator.multi_model_service.generate_response",
            new_callable=AsyncMock,
        ) as mock_llm:
            mock_llm.return_value = {
                "response": malformed_json,
                "tokens_used": 150,
            }

            try:
                # Try importing dirtyjson to see if it's available
                import dirtyjson  # noqa: F401

                # If dirtyjson is available, test should parse successfully
                questions = await generator.generate_questions_for_section(
                    asset=mock_asset,
                    section_id="infrastructure",
                    true_gaps=infrastructure_true_gaps,
                    data_map=data_map_with_coverage,
                    previously_asked_questions=[],
                    client_account_id=1,
                    engagement_id=123,
                )
                assert len(questions) == 1
                assert questions[0]["field_id"] == "cpu_count"
            except ModuleNotFoundError:
                # dirtyjson not installed - expect ValueError
                pytest.skip("dirtyjson not installed, skipping fallback test")

    @pytest.mark.asyncio
    async def test_parse_llm_response_empty_raises_error(
        self, mock_asset, infrastructure_true_gaps, data_map_with_coverage
    ):
        """Test that empty LLM response raises ValueError."""
        generator = SectionQuestionGenerator()

        with patch(
            "app.services.collection.gap_analysis.section_question_generator.multi_model_service.generate_response",
            new_callable=AsyncMock,
        ) as mock_llm:
            mock_llm.return_value = {"response": "", "tokens_used": 0}

            with pytest.raises(ValueError, match="Empty response from LLM"):
                await generator.generate_questions_for_section(
                    asset=mock_asset,
                    section_id="infrastructure",
                    true_gaps=infrastructure_true_gaps,
                    data_map=data_map_with_coverage,
                    previously_asked_questions=[],
                    client_account_id=1,
                    engagement_id=123,
                )

    @pytest.mark.asyncio
    async def test_parse_llm_response_non_list_raises_error(
        self, mock_asset, infrastructure_true_gaps, data_map_with_coverage
    ):
        """Test that non-list JSON raises ValueError."""
        generator = SectionQuestionGenerator()

        # LLM returns object instead of array
        invalid_response = json.dumps({"error": "I couldn't generate questions"})

        with patch(
            "app.services.collection.gap_analysis.section_question_generator.multi_model_service.generate_response",
            new_callable=AsyncMock,
        ) as mock_llm:
            mock_llm.return_value = {
                "response": invalid_response,
                "tokens_used": 50,
            }

            with pytest.raises(ValueError, match="must be a JSON array"):
                await generator.generate_questions_for_section(
                    asset=mock_asset,
                    section_id="infrastructure",
                    true_gaps=infrastructure_true_gaps,
                    data_map=data_map_with_coverage,
                    previously_asked_questions=[],
                    client_account_id=1,
                    engagement_id=123,
                )

    @pytest.mark.asyncio
    async def test_filters_invalid_questions(
        self, mock_asset, infrastructure_true_gaps, data_map_with_coverage
    ):
        """Test that questions missing required fields are filtered out."""
        generator = SectionQuestionGenerator()

        # Mix of valid and invalid questions
        mixed_response = json.dumps(
            [
                {
                    "field_id": "cpu_count",
                    "question_text": "How many CPU cores?",
                    "field_type": "number",
                    "required": True,
                    "priority": "critical",
                    "section": "infrastructure",
                },
                {
                    "field_id": "memory_gb",
                    # Missing question_text, field_type, required
                    "priority": "high",
                    "section": "infrastructure",
                },
                {
                    "field_id": "disk_space_gb",
                    "question_text": "Disk space?",
                    "field_type": "number",
                    "required": True,
                    "priority": "medium",
                    "section": "infrastructure",
                },
            ]
        )

        with patch(
            "app.services.collection.gap_analysis.section_question_generator.multi_model_service.generate_response",
            new_callable=AsyncMock,
        ) as mock_llm:
            mock_llm.return_value = {
                "response": mixed_response,
                "tokens_used": 200,
            }

            questions = await generator.generate_questions_for_section(
                asset=mock_asset,
                section_id="infrastructure",
                true_gaps=infrastructure_true_gaps,
                data_map=data_map_with_coverage,
                previously_asked_questions=[],
                client_account_id=1,
                engagement_id=123,
            )

        # Only 2 valid questions should be returned
        assert len(questions) == 2
        assert questions[0]["field_id"] == "cpu_count"
        assert questions[1]["field_id"] == "disk_space_gb"

    @pytest.mark.asyncio
    async def test_sanitizes_nan_infinity_values(
        self, mock_asset, infrastructure_true_gaps, data_map_with_coverage
    ):
        """Test that NaN and Infinity values are sanitized per ADR-029."""
        generator = SectionQuestionGenerator()

        # LLM response with NaN/Infinity (happens with confidence scores)
        response_with_nan = [
            {
                "field_id": "cpu_count",
                "question_text": "How many CPU cores?",
                "field_type": "number",
                "required": True,
                "priority": "critical",
                "section": "infrastructure",
                "confidence_score": float("nan"),  # Will be sanitized to None
            }
        ]

        with patch(
            "app.services.collection.gap_analysis.section_question_generator.multi_model_service.generate_response",
            new_callable=AsyncMock,
        ) as mock_llm:
            mock_llm.return_value = {
                "response": json.dumps(response_with_nan),
                "tokens_used": 150,
            }

            questions = await generator.generate_questions_for_section(
                asset=mock_asset,
                section_id="infrastructure",
                true_gaps=infrastructure_true_gaps,
                data_map=data_map_with_coverage,
                previously_asked_questions=[],
                client_account_id=1,
                engagement_id=123,
            )

        # NaN should be converted to None
        assert questions[0]["confidence_score"] is None

    @pytest.mark.asyncio
    async def test_format_data_coverage_no_asset_data(self):
        """Test formatting when asset data is None."""
        generator = SectionQuestionGenerator()

        result = generator._format_data_coverage(None)

        assert result == "No data coverage information available"

    @pytest.mark.asyncio
    async def test_format_data_coverage_with_coverage(
        self, data_map_with_coverage, mock_asset
    ):
        """Test formatting with coverage data."""
        generator = SectionQuestionGenerator()

        asset_data = data_map_with_coverage["assets"][0]
        result = generator._format_data_coverage(asset_data)

        assert "Data Coverage:" in result
        assert "standard_columns: 60% coverage" in result
        assert "custom_attributes: 30% coverage" in result
        assert "Data found in other sources (2 fields):" in result
        assert "operating_system" in result
        assert "custom_attributes.os" in result

    @pytest.mark.asyncio
    async def test_format_section_gaps(self, infrastructure_true_gaps):
        """Test formatting of section gaps."""
        generator = SectionQuestionGenerator()

        result = generator._format_section_gaps(infrastructure_true_gaps)

        assert "CPU Count" in result
        assert "priority: critical" in result
        assert "confidence: 1.00" in result
        assert "Memory (GB)" in result
        assert "priority: high" in result

    @pytest.mark.asyncio
    async def test_format_previous_questions_empty(self):
        """Test formatting when no previous questions."""
        generator = SectionQuestionGenerator()

        result = generator._format_previous_questions([])

        assert result == "None (this is the first section)"

    @pytest.mark.asyncio
    async def test_format_previous_questions_with_questions(self):
        """Test formatting with previous questions."""
        generator = SectionQuestionGenerator()

        questions = [
            "What is the Operating System?",
            "What is the Environment Type?",
        ]

        result = generator._format_previous_questions(questions)

        assert "What is the Operating System?" in result
        assert "What is the Environment Type?" in result
        assert result.count("  - ") == 2

    @pytest.mark.asyncio
    async def test_multi_tenant_scoping(
        self,
        mock_asset,
        infrastructure_true_gaps,
        data_map_with_coverage,
        valid_llm_response,
    ):
        """Test that multi-tenant scoping is passed correctly."""
        generator = SectionQuestionGenerator()

        client_account_id = 999
        engagement_id = 888

        with patch(
            "app.services.collection.gap_analysis.section_question_generator.multi_model_service.generate_response",
            new_callable=AsyncMock,
        ) as mock_llm:
            mock_llm.return_value = {
                "response": valid_llm_response,
                "tokens_used": 150,
            }

            await generator.generate_questions_for_section(
                asset=mock_asset,
                section_id="infrastructure",
                true_gaps=infrastructure_true_gaps,
                data_map=data_map_with_coverage,
                previously_asked_questions=[],
                client_account_id=client_account_id,
                engagement_id=engagement_id,
            )

        # Verify multi-tenant scoping
        call_args = mock_llm.call_args
        assert call_args.kwargs["client_account_id"] == client_account_id
        assert call_args.kwargs["engagement_id"] == engagement_id

    @pytest.mark.asyncio
    async def test_observability_metadata(
        self,
        mock_asset,
        infrastructure_true_gaps,
        data_map_with_coverage,
        valid_llm_response,
    ):
        """Test that observability metadata is included."""
        generator = SectionQuestionGenerator()

        with patch(
            "app.services.collection.gap_analysis.section_question_generator.multi_model_service.generate_response",
            new_callable=AsyncMock,
        ) as mock_llm:
            mock_llm.return_value = {
                "response": valid_llm_response,
                "tokens_used": 150,
            }

            await generator.generate_questions_for_section(
                asset=mock_asset,
                section_id="infrastructure",
                true_gaps=infrastructure_true_gaps,
                data_map=data_map_with_coverage,
                previously_asked_questions=["Prev Q1"],
                client_account_id=1,
                engagement_id=123,
            )

        # Verify observability metadata
        call_args = mock_llm.call_args
        metadata = call_args.kwargs["metadata"]

        assert metadata["feature_context"] == "section_question_generator"
        assert metadata["asset_id"] == str(mock_asset.id)
        assert metadata["asset_name"] == mock_asset.name
        assert metadata["section_id"] == "infrastructure"
        assert metadata["gap_count"] == 3
        assert metadata["previously_asked_count"] == 1

    @pytest.mark.asyncio
    async def test_only_true_gaps_generate_questions(
        self,
        mock_asset,
        mixed_gaps_infrastructure,
        data_map_with_coverage,
        valid_llm_response,
    ):
        """Test that only TRUE gaps generate questions (not data-exists-elsewhere)."""
        generator = SectionQuestionGenerator()

        with patch(
            "app.services.collection.gap_analysis.section_question_generator.multi_model_service.generate_response",
            new_callable=AsyncMock,
        ) as mock_llm:
            mock_llm.return_value = {
                "response": valid_llm_response,
                "tokens_used": 150,
            }

            await generator.generate_questions_for_section(
                asset=mock_asset,
                section_id="infrastructure",
                true_gaps=mixed_gaps_infrastructure,  # 1 TRUE + 1 data-elsewhere
                data_map=data_map_with_coverage,
                previously_asked_questions=[],
                client_account_id=1,
                engagement_id=123,
            )

        # Check that only TRUE gap is in prompt
        call_args = mock_llm.call_args
        prompt = call_args.args[0] if call_args.args else call_args.kwargs["prompt"]

        # Should include TRUE gap
        assert "CPU Count" in prompt
        # Check for the bold markdown format that's actually in the prompt
        assert "**TRUE Gaps for This Section** (1 gaps)" in prompt

        # Metadata should reflect only TRUE gaps
        metadata = call_args.kwargs["metadata"]
        assert metadata["gap_count"] == 1  # Only 1 TRUE gap

    @pytest.mark.asyncio
    async def test_handles_large_data_elsewhere_list(
        self, mock_asset, infrastructure_true_gaps, data_map_with_coverage
    ):
        """Test that large data_exists_elsewhere list is truncated in prompt."""
        generator = SectionQuestionGenerator()

        # Add many data-exists-elsewhere fields
        asset_data = data_map_with_coverage["assets"][0]
        asset_data["data_exists_elsewhere"] = [
            {"field": f"field_{i}", "found_in": "source", "value": f"value_{i}"}
            for i in range(20)
        ]

        valid_response = json.dumps(
            [
                {
                    "field_id": "cpu_count",
                    "question_text": "CPU?",
                    "field_type": "number",
                    "required": True,
                    "priority": "critical",
                    "section": "infrastructure",
                }
            ]
        )

        with patch(
            "app.services.collection.gap_analysis.section_question_generator.multi_model_service.generate_response",
            new_callable=AsyncMock,
        ) as mock_llm:
            mock_llm.return_value = {"response": valid_response, "tokens_used": 150}

            await generator.generate_questions_for_section(
                asset=mock_asset,
                section_id="infrastructure",
                true_gaps=infrastructure_true_gaps,
                data_map=data_map_with_coverage,
                previously_asked_questions=[],
                client_account_id=1,
                engagement_id=123,
            )

        # Check that prompt is truncated (first 5 shown)
        call_args = mock_llm.call_args
        prompt = call_args.args[0] if call_args.args else call_args.kwargs["prompt"]

        assert "field_0" in prompt
        assert "field_4" in prompt
        assert "... and 15 more fields" in prompt
        assert "field_19" not in prompt  # Truncated
