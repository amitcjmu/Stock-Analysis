"""
Unit tests for observability tenant context propagation in data import processors.

Tests that LLM calls include client_account_id and engagement_id for proper
cost tracking and FinOps dashboard accuracy.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.core.context import RequestContext
from app.services.data_import.service_handlers.infrastructure_processor import (
    InfrastructureProcessor,
)
from app.services.data_import.service_handlers.sensitive_data_processor import (
    SensitiveDataProcessor,
)


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    return MagicMock()


@pytest.fixture
def test_context():
    """Create a test RequestContext with known tenant IDs."""
    return RequestContext(
        client_account_id=uuid4(),
        engagement_id=uuid4(),
        user_id=str(uuid4()),
        flow_id=str(uuid4()),
    )


@pytest.mark.asyncio
async def test_infrastructure_processor_llm_call_includes_tenant_context(
    mock_db_session, test_context
):
    """Verify InfrastructureProcessor LLM calls include client_account_id and engagement_id for cost tracking."""
    with patch(
        "app.services.data_import.service_handlers.infrastructure_processor.multi_model_service"
    ) as mock_service:
        mock_service.generate_response = AsyncMock()

        processor = InfrastructureProcessor(mock_db_session, test_context)

        await processor.validate_data(
            data_import_id=uuid4(),
            raw_records=[{"cpu_utilization": 75.5, "memory_gb": 16}],
            processing_config={},
        )

        # Assert multi_model_service was called with tenant context
        mock_service.generate_response.assert_called_once()
        call_kwargs = mock_service.generate_response.call_args.kwargs
        assert call_kwargs["client_account_id"] == test_context.client_account_id
        assert call_kwargs["engagement_id"] == test_context.engagement_id
        assert "prompt" in call_kwargs
        assert "task_type" in call_kwargs
        assert call_kwargs["task_type"] == "performance_analysis"


@pytest.mark.asyncio
async def test_sensitive_data_processor_llm_call_includes_tenant_context(
    mock_db_session, test_context
):
    """Verify SensitiveDataProcessor LLM calls include client_account_id and engagement_id for cost tracking."""
    with patch(
        "app.services.data_import.service_handlers.sensitive_data_processor.multi_model_service"
    ) as mock_service:
        mock_service.generate_response = AsyncMock()

        processor = SensitiveDataProcessor(mock_db_session, test_context)

        await processor.validate_data(
            data_import_id=uuid4(),
            raw_records=[{"classification": "confidential", "scope": "financial"}],
            processing_config={},
        )

        # Assert multi_model_service was called with tenant context
        mock_service.generate_response.assert_called_once()
        call_kwargs = mock_service.generate_response.call_args.kwargs
        assert call_kwargs["client_account_id"] == test_context.client_account_id
        assert call_kwargs["engagement_id"] == test_context.engagement_id
        assert "prompt" in call_kwargs
        assert "task_type" in call_kwargs
        assert call_kwargs["task_type"] == "compliance_validation"
