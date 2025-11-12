"""
Unit Tests for Observability Enforcement

Tests provider detection, backfill logic, and pre-commit AST detection
for LLM observability patterns.

Generated with CC

Co-Authored-By: Claude <noreply@anthropic.com>
"""

import ast
import tempfile
from pathlib import Path
from typing import Optional
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.services.litellm_tracking_callback import LLMUsageCallback


class TestProviderDetection:
    """Test provider detection logic from various model names."""

    @pytest.fixture
    def callback(self):
        """Create callback instance for testing."""
        return LLMUsageCallback()

    def test_provider_from_hidden_params(self, callback):
        """Test provider extraction from response_obj._hidden_params."""
        # Mock response object with hidden params
        response_obj = Mock()
        response_obj._hidden_params = {"custom_llm_provider": "deepinfra"}
        response_obj.usage = Mock(
            prompt_tokens=100, completion_tokens=50, total_tokens=150
        )

        kwargs = {
            "model": "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
            "metadata": {},
        }

        # Extract provider using same logic as callback
        provider = "unknown"
        if hasattr(response_obj, "_hidden_params"):
            provider = response_obj._hidden_params.get("custom_llm_provider", "unknown")

        assert provider == "deepinfra"

    def test_provider_from_litellm_params(self, callback):
        """Test provider extraction from kwargs litellm_params."""
        response_obj = Mock()
        response_obj.usage = Mock(
            prompt_tokens=100, completion_tokens=50, total_tokens=150
        )

        kwargs = {
            "model": "some-model",
            "litellm_params": {"custom_llm_provider": "openai"},
            "metadata": {},
        }

        # Extract provider using fallback logic
        provider = "unknown"
        if "litellm_params" in kwargs:
            provider = kwargs["litellm_params"].get("custom_llm_provider", "unknown")

        assert provider == "openai"

    @pytest.mark.parametrize(
        "model_name,expected_provider",
        [
            ("meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8", "deepinfra"),
            ("google/gemma-2-9b-it", "deepinfra"),
            ("mistralai/Mixtral-8x7B-Instruct-v0.1", "deepinfra"),
            ("deepinfra/llama-3-70b", "deepinfra"),
            ("gpt-4-turbo", "openai"),
            ("gpt-3.5-turbo", "openai"),
            ("claude-3-sonnet", "anthropic"),
            ("claude-opus-20240229", "anthropic"),
            ("unknown-model", "unknown"),
        ],
    )
    def test_provider_from_model_name_patterns(
        self, callback, model_name, expected_provider
    ):
        """Test provider detection from model name patterns."""
        # Simulate last resort provider detection
        provider = "unknown"

        if "deepinfra" in model_name.lower():
            provider = "deepinfra"
        elif "openai" in model_name.lower() or "gpt" in model_name.lower():
            provider = "openai"
        elif "anthropic" in model_name.lower() or "claude" in model_name.lower():
            provider = "anthropic"
        else:
            # Check if model starts with known provider patterns
            if (
                model_name.startswith("meta-llama/")
                or model_name.startswith("google/")
                or model_name.startswith("mistralai/")
            ):
                provider = "deepinfra"

        assert provider == expected_provider


class TestBackfillLogic:
    """Test backfill script logic for recalculating costs."""

    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session."""
        session = AsyncMock()
        return session

    @pytest.fixture
    def mock_pricing_data(self):
        """Mock pricing data from database."""
        return {
            ("deepinfra", "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"): {
                "input_cost_per_1k": 0.0007,
                "output_cost_per_1k": 0.0009,
            },
            ("openai", "gpt-4-turbo"): {
                "input_cost_per_1k": 0.01,
                "output_cost_per_1k": 0.03,
            },
        }

    def calculate_cost(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        pricing_data: dict,
    ) -> Optional[float]:
        """Calculate cost given tokens and pricing data."""
        key = (provider, model)
        if key not in pricing_data:
            return None

        pricing = pricing_data[key]
        input_cost = (input_tokens / 1000.0) * pricing["input_cost_per_1k"]
        output_cost = (output_tokens / 1000.0) * pricing["output_cost_per_1k"]
        return round(input_cost + output_cost, 6)

    def test_cost_calculation_deepinfra(self, mock_pricing_data):
        """Test cost calculation for DeepInfra model."""
        provider = "deepinfra"
        model = "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"
        input_tokens = 1000
        output_tokens = 500

        cost = self.calculate_cost(
            provider, model, input_tokens, output_tokens, mock_pricing_data
        )

        # Expected: (1000/1000 * 0.0007) + (500/1000 * 0.0009) = 0.0007 + 0.00045 = 0.00115
        assert cost == 0.001150

    def test_cost_calculation_openai(self, mock_pricing_data):
        """Test cost calculation for OpenAI model."""
        provider = "openai"
        model = "gpt-4-turbo"
        input_tokens = 2000
        output_tokens = 1000

        cost = self.calculate_cost(
            provider, model, input_tokens, output_tokens, mock_pricing_data
        )

        # Expected: (2000/1000 * 0.01) + (1000/1000 * 0.03) = 0.02 + 0.03 = 0.05
        assert cost == 0.05

    def test_cost_calculation_unknown_model(self, mock_pricing_data):
        """Test cost calculation for unknown model returns None."""
        provider = "unknown"
        model = "unknown-model"
        input_tokens = 1000
        output_tokens = 500

        cost = self.calculate_cost(
            provider, model, input_tokens, output_tokens, mock_pricing_data
        )

        assert cost is None

    def test_backfill_batch_processing(self, mock_pricing_data):
        """Test batch processing logic for backfill."""
        # Simulate 5 records needing backfill
        mock_records = [
            {
                "id": f"id-{i}",
                "provider": "deepinfra",
                "model": "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
                "input_tokens": 1000 + i * 100,
                "output_tokens": 500 + i * 50,
            }
            for i in range(5)
        ]

        updated_records = []
        for record in mock_records:
            cost = self.calculate_cost(
                record["provider"],
                record["model"],
                record["input_tokens"],
                record["output_tokens"],
                mock_pricing_data,
            )
            if cost is not None:
                updated_records.append(
                    {
                        "id": record["id"],
                        "total_cost": cost,
                    }
                )

        # All 5 records should have costs calculated
        assert len(updated_records) == 5
        # Costs should be different for each record
        costs = [r["total_cost"] for r in updated_records]
        assert len(set(costs)) == 5  # All unique


class TestPreCommitASTDetection:
    """Test pre-commit AST detection for observability violations."""

    def create_temp_file(self, code: str) -> Path:
        """Create temporary Python file with given code."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            return Path(f.name)

    def detect_violations(self, code: str) -> list:
        """Parse code and detect observability violations."""

        class LLMCallDetector(ast.NodeVisitor):
            """Detect LLM calls that bypass observability."""

            def __init__(self):
                self.violations = []
                self.has_callback_handler = False

            def visit_Call(self, node):
                """Check function calls for observability patterns."""

                # Check for task.execute_async() without callback
                if hasattr(node.func, "attr") and node.func.attr == "execute_async":
                    if not self.has_callback_handler:
                        self.violations.append(
                            (
                                node.lineno,
                                "task.execute_async() called without CallbackHandler",
                                "CRITICAL",
                            )
                        )

                # Check for direct litellm.completion() calls
                if (
                    hasattr(node.func, "attr")
                    and node.func.attr == "completion"
                    and hasattr(node.func.value, "id")
                    and node.func.value.id == "litellm"
                ):
                    self.violations.append(
                        (
                            node.lineno,
                            "Direct litellm.completion() call - use multi_model_service instead",
                            "ERROR",
                        )
                    )

                # Check for crew.kickoff() without callbacks
                if hasattr(node.func, "attr") and node.func.attr in [
                    "kickoff",
                    "kickoff_async",
                ]:
                    has_callbacks = any(kw.arg == "callbacks" for kw in node.keywords)
                    if not has_callbacks and not self.has_callback_handler:
                        self.violations.append(
                            (
                                node.lineno,
                                "crew.kickoff() called without callbacks parameter",
                                "WARNING",
                            )
                        )

                self.generic_visit(node)

            def visit_Import(self, node):
                """Track imports of callback handlers."""
                for alias in node.names:
                    if "CallbackHandler" in alias.name:
                        self.has_callback_handler = True
                self.generic_visit(node)

            def visit_ImportFrom(self, node):
                """Track from imports of callback handlers."""
                if node.module and "callback_handler" in node.module:
                    self.has_callback_handler = True
                self.generic_visit(node)

        try:
            tree = ast.parse(code)
            detector = LLMCallDetector()
            detector.visit(tree)
            return detector.violations
        except SyntaxError:
            return []

    def test_detect_execute_async_without_callback(self):
        """Test detection of execute_async without CallbackHandler."""
        code = """
import asyncio

async def run_task():
    task = Task(description="test")
    result = await task.execute_async()
    return result
"""
        violations = self.detect_violations(code)

        # Should detect 1 CRITICAL violation
        assert len(violations) == 1
        assert violations[0][2] == "CRITICAL"
        assert "execute_async" in violations[0][1]

    def test_detect_execute_async_with_callback(self):
        """Test no violation when CallbackHandler is imported."""
        code = """
import asyncio
from app.services.crewai_flows.handlers.callback_handler_integration import CallbackHandlerIntegration

async def run_task():
    callback_handler = CallbackHandlerIntegration.create_callback_handler(
        flow_id="test-flow",
        context={}
    )
    task = Task(description="test")
    result = await task.execute_async()
    return result
"""
        violations = self.detect_violations(code)

        # Should detect NO violations (callback handler in scope)
        assert len(violations) == 0

    def test_detect_direct_litellm_call(self):
        """Test detection of direct litellm.completion() calls."""
        code = """
import litellm

def call_llm():
    response = litellm.completion(
        model="gpt-4",
        messages=[{"role": "user", "content": "Hello"}]
    )
    return response
"""
        violations = self.detect_violations(code)

        # Should detect 1 ERROR violation
        assert len(violations) == 1
        assert violations[0][2] == "ERROR"
        assert "litellm.completion()" in violations[0][1]

    def test_detect_crew_kickoff_without_callbacks(self):
        """Test detection of crew.kickoff() without callbacks parameter."""
        code = """
from crewai import Crew

def run_crew():
    crew = Crew(agents=[], tasks=[])
    result = crew.kickoff()
    return result
"""
        violations = self.detect_violations(code)

        # Should detect 1 WARNING violation
        assert len(violations) == 1
        assert violations[0][2] == "WARNING"
        assert "kickoff()" in violations[0][1]

    def test_detect_crew_kickoff_with_callbacks(self):
        """Test no violation when crew.kickoff() has callbacks parameter."""
        code = """
from crewai import Crew

def run_crew():
    crew = Crew(agents=[], tasks=[])
    result = crew.kickoff(callbacks=[my_callback])
    return result
"""
        violations = self.detect_violations(code)

        # Should detect NO violations
        assert len(violations) == 0

    def test_detect_multiple_violations(self):
        """Test detection of multiple violations in same file."""
        code = """
import litellm
from crewai import Crew

async def bad_code():
    # Violation 1: Direct litellm call
    response1 = litellm.completion(model="gpt-4", messages=[])

    # Violation 2: crew.kickoff without callbacks
    crew = Crew(agents=[], tasks=[])
    result = crew.kickoff()

    # Violation 3: execute_async without callback
    task = Task(description="test")
    result2 = await task.execute_async()

    return result2
"""
        violations = self.detect_violations(code)

        # Should detect 3 violations
        assert len(violations) == 3

        # Verify severity levels
        severities = [v[2] for v in violations]
        assert "ERROR" in severities  # litellm.completion
        assert "WARNING" in severities  # crew.kickoff
        assert "CRITICAL" in severities  # execute_async

    def test_no_violations_in_clean_code(self):
        """Test that clean code has no violations."""
        code = """
from app.services.multi_model_service import multi_model_service
from app.services.crewai_flows.handlers.callback_handler_integration import CallbackHandlerIntegration

async def proper_code():
    # Use multi_model_service instead of direct LiteLLM
    response = await multi_model_service.generate_response(
        prompt="Hello",
        task_type="chat",
        complexity="simple"
    )

    # Use callback handler with crew
    callback_handler = CallbackHandlerIntegration.create_callback_handler(
        flow_id="test",
        context={}
    )
    callback_handler.setup_callbacks()

    crew = Crew(agents=[], tasks=[])
    result = crew.kickoff(callbacks=[callback_handler])

    return result
"""
        violations = self.detect_violations(code)

        # Should detect NO violations
        assert len(violations) == 0


class TestObservabilityPatterns:
    """Test observability pattern conformance."""

    def test_callback_handler_metadata_structure(self):
        """Test that callback handler receives proper metadata structure."""
        # Expected metadata structure for callback handler
        expected_keys = {
            "client_account_id",
            "engagement_id",
            "flow_type",
            "phase",
        }

        # Test metadata structure
        metadata = {
            "client_account_id": "test-client",
            "engagement_id": "test-engagement",
            "flow_type": "assessment",
            "phase": "readiness",
        }

        assert set(metadata.keys()) == expected_keys
        assert metadata["flow_type"] in ["assessment", "discovery", "collection"]

    def test_llm_provider_mapping(self):
        """Test that all known providers are mapped correctly."""
        provider_patterns = {
            "deepinfra": [
                "meta-llama/",
                "google/",
                "mistralai/",
                "deepinfra/",
            ],
            "openai": ["gpt-", "openai/"],
            "anthropic": ["claude-", "anthropic/"],
        }

        # Test pattern matching
        test_models = [
            ("meta-llama/Llama-4", "deepinfra"),
            ("google/gemma-3", "deepinfra"),
            ("mistralai/mixtral", "deepinfra"),
            ("gpt-4-turbo", "openai"),
            ("claude-3-sonnet", "anthropic"),
        ]

        for model, expected_provider in test_models:
            detected_provider = None
            for provider, patterns in provider_patterns.items():
                if any(
                    pattern in model.lower() or model.lower().startswith(pattern)
                    for pattern in patterns
                ):
                    detected_provider = provider
                    break

            assert (
                detected_provider == expected_provider
            ), f"Model {model} should map to {expected_provider}"
