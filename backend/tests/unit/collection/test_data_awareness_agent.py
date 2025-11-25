"""
Unit tests for DataAwarenessAgent.

Tests the ONE-TIME data mapping agent that analyzes data coverage across
all 6 sources before questionnaire generation.

CC Generated for Issue #1112 - DataAwarenessAgent (One-Time Per Flow)
Per ADR-037: Intelligent Gap Detection and Questionnaire Generation Architecture

Test Coverage:
- Data map creation with comprehensive inputs
- JSON sanitization for NaN/Infinity (ADR-029)
- Error handling for invalid inputs
- LLM response parsing (markdown stripping, dirtyjson fallback)
- Format helper methods
- Multi-tenant context preservation
- Observability via multi_model_service
- Empty asset handling
- Cross-asset pattern detection
"""

import json
from typing import Dict, List
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.models.asset.models import Asset
from app.services.collection.gap_analysis.data_awareness_agent import (
    DataAwarenessAgent,
)
from app.services.collection.gap_analysis.models import DataSource, IntelligentGap


class TestDataAwarenessAgentInitialization:
    """Test agent initialization."""

    def test_agent_instantiation(self):
        """Test agent can be instantiated without errors."""
        agent = DataAwarenessAgent()
        assert agent is not None


class TestCreateDataMap:
    """Test main create_data_map method."""

    @pytest.fixture
    def mock_assets(self) -> List[Asset]:
        """Create mock Asset objects for testing."""
        asset1 = MagicMock(spec=Asset)
        asset1.id = uuid4()
        asset1.name = "Consul Production"
        asset1.asset_type = "Application Server"
        asset1.custom_attributes = {"db_type": "PostgreSQL 14"}
        asset1.environment = "production"

        asset2 = MagicMock(spec=Asset)
        asset2.id = uuid4()
        asset2.name = "Redis Cache"
        asset2.asset_type = "Database"
        asset2.custom_attributes = {"memory": "8GB"}
        asset2.environment = "production"

        return [asset1, asset2]

    @pytest.fixture
    def mock_intelligent_gaps(
        self, mock_assets: List[Asset]
    ) -> Dict[str, List[IntelligentGap]]:
        """Create mock IntelligentGap objects for testing."""
        asset1_id = str(mock_assets[0].id)
        asset2_id = str(mock_assets[1].id)

        # Asset 1: TRUE gap for cpu_count, data-exists-elsewhere for database_type
        gap1_true = IntelligentGap(
            field_id="cpu_count",
            field_name="CPU Count",
            priority="critical",
            data_found=[],  # TRUE gap
            is_true_gap=True,
            confidence_score=1.0,
            section="infrastructure",
        )

        gap1_elsewhere = IntelligentGap(
            field_id="database_type",
            field_name="Database Type",
            priority="medium",
            data_found=[
                DataSource(
                    source_type="custom_attributes",
                    field_path="custom_attributes.db_type",
                    value="PostgreSQL 14",
                    confidence=0.95,
                )
            ],
            is_true_gap=False,
            confidence_score=0.05,
            section="dependencies",
        )

        # Asset 2: TRUE gap for memory_gb
        gap2_true = IntelligentGap(
            field_id="memory_gb",
            field_name="Memory GB",
            priority="high",
            data_found=[],  # TRUE gap
            is_true_gap=True,
            confidence_score=1.0,
            section="infrastructure",
        )

        return {
            asset1_id: [gap1_true, gap1_elsewhere],
            asset2_id: [gap2_true],
        }

    @pytest.fixture
    def mock_llm_response(self) -> Dict:
        """Create mock LLM response with valid data map."""
        return {
            "status": "success",
            "response": json.dumps(
                {
                    "flow_id": "abc-123",
                    "assets": [
                        {
                            "asset_id": "def-456",
                            "asset_name": "Consul Production",
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
                                    "field": "database_type",
                                    "found_in": "custom_attributes.db_type",
                                    "value": "PostgreSQL 14",
                                    "no_question_needed": True,
                                }
                            ],
                        },
                        {
                            "asset_id": "ghi-789",
                            "asset_name": "Redis Cache",
                            "data_coverage": {
                                "standard_columns": 40,
                                "custom_attributes": 20,
                                "enrichment_data": 5,
                                "environment": 10,
                                "canonical_apps": 0,
                                "related_assets": 0,
                            },
                            "true_gaps": [
                                {
                                    "field": "memory_gb",
                                    "priority": "high",
                                    "section": "infrastructure",
                                    "checked_sources": 6,
                                    "found_in": [],
                                }
                            ],
                            "data_exists_elsewhere": [],
                        },
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
            ),
            "tokens_used": 500,
            "model_used": "gemma3_4b",
        }

    @pytest.mark.asyncio
    async def test_create_data_map_success(
        self,
        mock_assets: List[Asset],
        mock_intelligent_gaps: Dict[str, List[IntelligentGap]],
        mock_llm_response: Dict,
    ):
        """Test successful data map creation."""
        agent = DataAwarenessAgent()

        with patch(
            "app.services.collection.gap_analysis.data_awareness_agent.multi_model_service.generate_response",
            new_callable=AsyncMock,
            return_value=mock_llm_response,
        ):
            data_map = await agent.create_data_map(
                flow_id="abc-123",
                assets=mock_assets,
                intelligent_gaps=mock_intelligent_gaps,
                client_account_id=1,
                engagement_id=123,
            )

        assert data_map is not None
        assert data_map["flow_id"] == "abc-123"
        assert len(data_map["assets"]) == 2
        assert "cross_asset_patterns" in data_map

        # Verify asset details
        asset1 = data_map["assets"][0]
        assert asset1["asset_name"] == "Consul Production"
        assert "data_coverage" in asset1
        assert len(asset1["true_gaps"]) == 1
        assert len(asset1["data_exists_elsewhere"]) == 1

        # Verify cross-asset patterns
        patterns = data_map["cross_asset_patterns"]
        assert "common_gaps" in patterns
        assert "common_data_sources" in patterns
        assert "recommendations" in patterns

    @pytest.mark.asyncio
    async def test_create_data_map_with_markdown_response(
        self,
        mock_assets: List[Asset],
        mock_intelligent_gaps: Dict[str, List[IntelligentGap]],
    ):
        """Test data map creation with LLM response wrapped in markdown."""
        agent = DataAwarenessAgent()

        # Mock LLM response with markdown code blocks (common issue)
        markdown_response = {
            "status": "success",
            "response": (
                "```json\n"
                + json.dumps(
                    {
                        "flow_id": "abc-123",
                        "assets": [],
                        "cross_asset_patterns": {
                            "common_gaps": [],
                            "common_data_sources": [],
                            "recommendations": [],
                        },
                    }
                )
                + "\n```"
            ),
            "tokens_used": 100,
        }

        with patch(
            "app.services.collection.gap_analysis.data_awareness_agent.multi_model_service.generate_response",
            new_callable=AsyncMock,
            return_value=markdown_response,
        ):
            data_map = await agent.create_data_map(
                flow_id="abc-123",
                assets=mock_assets,
                intelligent_gaps=mock_intelligent_gaps,
                client_account_id=1,
                engagement_id=123,
            )

        assert data_map is not None
        assert data_map["flow_id"] == "abc-123"

    @pytest.mark.asyncio
    async def test_create_data_map_with_nan_values(
        self,
        mock_assets: List[Asset],
        mock_intelligent_gaps: Dict[str, List[IntelligentGap]],
    ):
        """Test data map sanitization for NaN/Infinity (ADR-029)."""
        agent = DataAwarenessAgent()

        # Mock LLM response with NaN/Infinity (should be sanitized)
        response_with_nan = {
            "status": "success",
            "response": json.dumps(
                {
                    "flow_id": "abc-123",
                    "assets": [
                        {
                            "asset_id": "def-456",
                            "asset_name": "Test",
                            "data_coverage": {
                                "standard_columns": 60,
                                "custom_attributes": float("nan"),  # Invalid
                            },
                            "true_gaps": [],
                            "data_exists_elsewhere": [],
                        }
                    ],
                    "cross_asset_patterns": {
                        "common_gaps": [],
                        "common_data_sources": [],
                        "recommendations": [],
                    },
                }
            ),
            "tokens_used": 100,
        }

        with patch(
            "app.services.collection.gap_analysis.data_awareness_agent.multi_model_service.generate_response",
            new_callable=AsyncMock,
            return_value=response_with_nan,
        ):
            data_map = await agent.create_data_map(
                flow_id="abc-123",
                assets=mock_assets,
                intelligent_gaps=mock_intelligent_gaps,
                client_account_id=1,
                engagement_id=123,
            )

        # NaN should be converted to None by sanitize_for_json
        assert data_map["assets"][0]["data_coverage"]["custom_attributes"] is None

    @pytest.mark.asyncio
    async def test_create_data_map_empty_assets(self):
        """Test error handling for empty assets list."""
        agent = DataAwarenessAgent()

        with pytest.raises(ValueError, match="Assets list cannot be empty"):
            await agent.create_data_map(
                flow_id="abc-123",
                assets=[],
                intelligent_gaps={},
                client_account_id=1,
                engagement_id=123,
            )

    @pytest.mark.asyncio
    async def test_create_data_map_none_intelligent_gaps(
        self, mock_assets: List[Asset]
    ):
        """Test error handling for None intelligent_gaps."""
        agent = DataAwarenessAgent()

        with pytest.raises(
            ValueError, match="Intelligent gaps dictionary cannot be None"
        ):
            await agent.create_data_map(
                flow_id="abc-123",
                assets=mock_assets,
                intelligent_gaps=None,
                client_account_id=1,
                engagement_id=123,
            )

    @pytest.mark.asyncio
    async def test_create_data_map_empty_llm_response(
        self,
        mock_assets: List[Asset],
        mock_intelligent_gaps: Dict[str, List[IntelligentGap]],
    ):
        """Test error handling for empty LLM response."""
        agent = DataAwarenessAgent()

        empty_response = {"status": "success", "response": "", "tokens_used": 0}

        with patch(
            "app.services.collection.gap_analysis.data_awareness_agent.multi_model_service.generate_response",
            new_callable=AsyncMock,
            return_value=empty_response,
        ):
            with pytest.raises(
                Exception, match="Empty response from multi_model_service"
            ):
                await agent.create_data_map(
                    flow_id="abc-123",
                    assets=mock_assets,
                    intelligent_gaps=mock_intelligent_gaps,
                    client_account_id=1,
                    engagement_id=123,
                )

    @pytest.mark.asyncio
    async def test_create_data_map_invalid_json_response(
        self,
        mock_assets: List[Asset],
        mock_intelligent_gaps: Dict[str, List[IntelligentGap]],
    ):
        """Test error handling for malformed JSON response."""
        agent = DataAwarenessAgent()

        invalid_response = {
            "status": "success",
            "response": "This is not valid JSON {",
            "tokens_used": 50,
        }

        with patch(
            "app.services.collection.gap_analysis.data_awareness_agent.multi_model_service.generate_response",
            new_callable=AsyncMock,
            return_value=invalid_response,
        ):
            with pytest.raises(ValueError, match="Unable to parse LLM response"):
                await agent.create_data_map(
                    flow_id="abc-123",
                    assets=mock_assets,
                    intelligent_gaps=mock_intelligent_gaps,
                    client_account_id=1,
                    engagement_id=123,
                )

    @pytest.mark.asyncio
    async def test_create_data_map_multi_tenant_context(
        self,
        mock_assets: List[Asset],
        mock_intelligent_gaps: Dict[str, List[IntelligentGap]],
        mock_llm_response: Dict,
    ):
        """Test multi-tenant context is preserved in LLM call."""
        agent = DataAwarenessAgent()

        with patch(
            "app.services.collection.gap_analysis.data_awareness_agent.multi_model_service.generate_response",
            new_callable=AsyncMock,
            return_value=mock_llm_response,
        ) as mock_generate:
            await agent.create_data_map(
                flow_id="abc-123",
                assets=mock_assets,
                intelligent_gaps=mock_intelligent_gaps,
                client_account_id=1,
                engagement_id=123,
            )

            # Verify multi_model_service was called with correct parameters
            mock_generate.assert_called_once()
            call_kwargs = mock_generate.call_args.kwargs

            # Check prompt contains tenant context
            prompt = call_kwargs.get("prompt", "")
            assert "Client Account: 1" in prompt
            assert "Engagement: 123" in prompt

            # Check task_type and complexity
            assert call_kwargs.get("task_type") == "data_analysis"
            from app.services.multi_model_service import TaskComplexity

            assert call_kwargs.get("complexity") == TaskComplexity.SIMPLE


class TestFormatAssetsAndGaps:
    """Test _format_assets_and_gaps helper method."""

    def test_format_assets_and_gaps_with_data(self):
        """Test formatting with assets that have gaps."""
        agent = DataAwarenessAgent()

        asset1 = MagicMock(spec=Asset)
        asset1.id = uuid4()
        asset1.name = "Test Asset 1"
        asset1.asset_type = "Server"

        gap1 = IntelligentGap(
            field_id="cpu_count",
            field_name="CPU Count",
            priority="critical",
            data_found=[],
            is_true_gap=True,
            confidence_score=1.0,
            section="infrastructure",
        )

        gap2 = IntelligentGap(
            field_id="memory_gb",
            field_name="Memory GB",
            priority="high",
            data_found=[
                DataSource(
                    source_type="custom_attributes",
                    field_path="custom_attributes.memory",
                    value="8GB",
                    confidence=0.95,
                )
            ],
            is_true_gap=False,
            confidence_score=0.05,
            section="infrastructure",
        )

        intelligent_gaps = {str(asset1.id): [gap1, gap2]}

        result = agent._format_assets_and_gaps([asset1], intelligent_gaps)

        assert "Test Asset 1" in result
        assert "Server" in result
        assert "TRUE Gaps (1)" in result
        assert "CPU Count" in result
        assert "Data Exists Elsewhere (1)" in result
        assert "Memory GB" in result

    def test_format_assets_and_gaps_empty_gaps(self):
        """Test formatting with assets that have no gaps."""
        agent = DataAwarenessAgent()

        asset1 = MagicMock(spec=Asset)
        asset1.id = uuid4()
        asset1.name = "Test Asset 1"
        asset1.asset_type = "Server"

        intelligent_gaps = {str(asset1.id): []}

        result = agent._format_assets_and_gaps([asset1], intelligent_gaps)

        assert "Test Asset 1" in result
        assert "TRUE Gaps (0)" in result
        assert "Data Exists Elsewhere (0)" in result

    def test_format_assets_and_gaps_multiple_assets(self):
        """Test formatting with multiple assets."""
        agent = DataAwarenessAgent()

        asset1 = MagicMock(spec=Asset)
        asset1.id = uuid4()
        asset1.name = "Asset 1"
        asset1.asset_type = "Server"

        asset2 = MagicMock(spec=Asset)
        asset2.id = uuid4()
        asset2.name = "Asset 2"
        asset2.asset_type = "Database"

        intelligent_gaps = {str(asset1.id): [], str(asset2.id): []}

        result = agent._format_assets_and_gaps([asset1, asset2], intelligent_gaps)

        assert "Asset 1" in result
        assert "Asset 2" in result
        assert "---" in result  # Separator between assets


class TestFormatGaps:
    """Test _format_gaps helper method."""

    def test_format_gaps_with_data(self):
        """Test formatting TRUE gaps."""
        agent = DataAwarenessAgent()

        gaps = [
            IntelligentGap(
                field_id="cpu_count",
                field_name="CPU Count",
                priority="critical",
                data_found=[],
                is_true_gap=True,
                confidence_score=1.0,
                section="infrastructure",
            ),
            IntelligentGap(
                field_id="memory_gb",
                field_name="Memory GB",
                priority="high",
                data_found=[],
                is_true_gap=True,
                confidence_score=1.0,
                section="infrastructure",
            ),
        ]

        result = agent._format_gaps(gaps)

        assert "CPU Count" in result
        assert "critical" in result
        assert "infrastructure" in result
        assert "Memory GB" in result
        assert "high" in result

    def test_format_gaps_empty_list(self):
        """Test formatting with empty gaps list."""
        agent = DataAwarenessAgent()

        result = agent._format_gaps([])

        assert result == "  (none)"


class TestFormatDataSources:
    """Test _format_data_sources helper method."""

    def test_format_data_sources_with_data(self):
        """Test formatting data-exists-elsewhere gaps."""
        agent = DataAwarenessAgent()

        gaps = [
            IntelligentGap(
                field_id="database_type",
                field_name="Database Type",
                priority="medium",
                data_found=[
                    DataSource(
                        source_type="custom_attributes",
                        field_path="custom_attributes.db_type",
                        value="PostgreSQL 14",
                        confidence=0.95,
                    )
                ],
                is_true_gap=False,
                confidence_score=0.05,
                section="dependencies",
            ),
            IntelligentGap(
                field_id="hostname",
                field_name="Hostname",
                priority="critical",
                data_found=[
                    DataSource(
                        source_type="custom_attributes",
                        field_path="custom_attributes.host",
                        value="consul-prod-01",
                        confidence=0.95,
                    ),
                    DataSource(
                        source_type="standard_column",
                        field_path="assets.name",
                        value="Consul Production",
                        confidence=1.0,
                    ),
                ],
                is_true_gap=False,
                confidence_score=0.0,
                section="network",
            ),
        ]

        result = agent._format_data_sources(gaps)

        assert "Database Type" in result
        assert "custom_attributes.db_type=PostgreSQL 14" in result
        assert "Hostname" in result
        assert "custom_attributes.host=consul-prod-01" in result
        assert "assets.name=Consul Production" in result

    def test_format_data_sources_empty_list(self):
        """Test formatting with empty data sources list."""
        agent = DataAwarenessAgent()

        result = agent._format_data_sources([])

        assert result == "  (none)"

    def test_format_data_sources_multiple_sources_per_field(self):
        """Test formatting field with multiple data sources."""
        agent = DataAwarenessAgent()

        gap = IntelligentGap(
            field_id="hostname",
            field_name="Hostname",
            priority="critical",
            data_found=[
                DataSource(
                    source_type="custom_attributes",
                    field_path="custom_attributes.host",
                    value="host1",
                    confidence=0.95,
                ),
                DataSource(
                    source_type="standard_column",
                    field_path="assets.hostname",
                    value="host2",
                    confidence=1.0,
                ),
                DataSource(
                    source_type="environment",
                    field_path="assets.environment",
                    value="production",
                    confidence=0.85,
                ),
            ],
            is_true_gap=False,
            confidence_score=0.0,
            section="network",
        )

        result = agent._format_data_sources([gap])

        assert "Hostname" in result
        assert "custom_attributes.host=host1" in result
        assert "assets.hostname=host2" in result
        assert "assets.environment=production" in result


class TestObservabilityCompliance:
    """Test observability requirements (per CLAUDE.md)."""

    @pytest.mark.asyncio
    async def test_uses_multi_model_service(
        self,
    ):
        """Test that agent uses multi_model_service for LLM calls."""
        agent = DataAwarenessAgent()

        asset = MagicMock(spec=Asset)
        asset.id = uuid4()
        asset.name = "Test"
        asset.asset_type = "Server"

        mock_response = {
            "status": "success",
            "response": json.dumps(
                {
                    "flow_id": "test",
                    "assets": [],
                    "cross_asset_patterns": {
                        "common_gaps": [],
                        "common_data_sources": [],
                        "recommendations": [],
                    },
                }
            ),
            "tokens_used": 100,
        }

        with patch(
            "app.services.collection.gap_analysis.data_awareness_agent.multi_model_service.generate_response",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_generate:
            await agent.create_data_map(
                flow_id="test",
                assets=[asset],
                intelligent_gaps={},
                client_account_id=1,
                engagement_id=123,
            )

            # Verify multi_model_service was called (automatic observability)
            mock_generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_correct_task_complexity(self):
        """Test that agent uses correct task complexity."""
        agent = DataAwarenessAgent()

        asset = MagicMock(spec=Asset)
        asset.id = uuid4()
        asset.name = "Test"
        asset.asset_type = "Server"

        mock_response = {
            "status": "success",
            "response": json.dumps(
                {
                    "flow_id": "test",
                    "assets": [],
                    "cross_asset_patterns": {
                        "common_gaps": [],
                        "common_data_sources": [],
                        "recommendations": [],
                    },
                }
            ),
            "tokens_used": 100,
        }

        with patch(
            "app.services.collection.gap_analysis.data_awareness_agent.multi_model_service.generate_response",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_generate:
            await agent.create_data_map(
                flow_id="test",
                assets=[asset],
                intelligent_gaps={},
                client_account_id=1,
                engagement_id=123,
            )

            # Verify complexity is SIMPLE (single-phase analysis)
            call_kwargs = mock_generate.call_args.kwargs
            from app.services.multi_model_service import TaskComplexity

            assert call_kwargs.get("complexity") == TaskComplexity.SIMPLE
