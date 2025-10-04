"""
Agent-related pytest fixtures for MFO testing.

Provides fixtures for mock agent pools, agent execution results, and agent behaviors.
"""

from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock

import pytest

from .base import DEMO_CLIENT_ACCOUNT_ID


@pytest.fixture
def mock_tenant_scoped_agent_pool():
    """Mock TenantScopedAgentPool for testing MFO agent interactions."""
    mock_pool = MagicMock()
    mock_pool.tenant_id = DEMO_CLIENT_ACCOUNT_ID

    # Mock agent with expected behavior
    mock_agent = MagicMock()
    mock_agent.execute = AsyncMock(
        return_value={
            "status": "completed",
            "result": {"analysis": "test result"},
            "confidence": 0.85,
            "execution_time": 1.23,
        }
    )

    # Mock pool methods
    mock_pool.get_agent = AsyncMock(return_value=mock_agent)
    mock_pool.release_agent = AsyncMock()
    mock_pool.get_pool_stats = AsyncMock(
        return_value={
            "active_agents": 2,
            "total_agents": 5,
            "memory_usage": 128.5,
        }
    )

    return mock_pool


@pytest.fixture
def mock_flow_execution_results() -> Dict[str, Any]:
    """Mock execution results for different flow phases."""
    return {
        "data_import": {
            "status": "completed",
            "records_processed": 1500,
            "data_quality_score": 0.92,
            "execution_time": 45.2,
            "agent_insights": {
                "data_completeness": 0.95,
                "schema_consistency": 0.89,
                "recommendations": ["Standardize date formats", "Validate email addresses"],
            },
        },
        "field_mapping": {
            "status": "completed",
            "mappings_created": 87,
            "confidence_score": 0.94,
            "execution_time": 32.1,
            "agent_insights": {
                "auto_mapped_fields": 72,
                "manual_review_required": 15,
                "recommendations": ["Review currency fields", "Validate address mappings"],
            },
        },
        "data_cleansing": {
            "status": "in_progress",
            "records_cleaned": 1200,
            "total_records": 1500,
            "execution_time": 28.7,
            "agent_insights": {
                "duplicates_found": 45,
                "null_values_handled": 123,
                "data_standardization": 0.87,
                "recommendations": ["Apply fuzzy matching", "Standardize naming conventions"],
            },
        },
        "asset_inventory": {
            "status": "pending",
            "dependencies_analyzed": 0,
            "execution_time": 0.0,
            "agent_insights": {
                "complexity_estimate": "medium",
                "estimated_duration": 60,
                "prerequisites": ["Complete data cleansing phase"],
            },
        },
        "dependency_analysis": {
            "status": "not_started",
            "execution_time": 0.0,
            "agent_insights": {
                "complexity_estimate": "high",
                "estimated_duration": 120,
                "prerequisites": ["Complete asset inventory"],
            },
        },
    }
