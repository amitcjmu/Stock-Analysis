"""
Test data fixtures for MFO testing.

Provides test data for tenant isolation, performance testing, and edge cases.
"""

from typing import Any, Dict, List

import pytest


@pytest.fixture
def tenant_isolation_test_data() -> List[Dict[str, str]]:
    """Test data for verifying tenant isolation in MFO operations."""
    return [
        {
            "tenant_name": "demo_corp",
            "client_account_id": "11111111-1111-1111-1111-111111111111",
            "engagement_id": "22222222-2222-2222-2222-222222222222",
            "user_id": "33333333-3333-3333-3333-333333333333",
            "expected_isolation": "complete",
        },
        {
            "tenant_name": "acme_corp",
            "client_account_id": "44444444-4444-4444-4444-444444444444",
            "engagement_id": "55555555-5555-5555-5555-555555555555",
            "user_id": "66666666-6666-6666-6666-666666666666",
            "expected_isolation": "complete",
        },
        {
            "tenant_name": "test_corp",
            "client_account_id": "77777777-7777-7777-7777-777777777777",
            "engagement_id": "88888888-8888-8888-8888-888888888888",
            "user_id": "99999999-9999-9999-9999-999999999999",
            "expected_isolation": "complete",
        },
    ]


@pytest.fixture
def mfo_performance_test_config() -> Dict[str, Any]:
    """Configuration for MFO performance testing scenarios."""
    return {
        "baseline_metrics": {
            "flow_creation_time_ms": 250,  # milliseconds
            "phase_transition_time_ms": 150,  # milliseconds
            "agent_execution_time_ms": 2000,  # milliseconds
            "database_query_time_ms": 50,  # milliseconds
        },
        "thresholds": {
            "memory_usage_mb": 256,  # MB
            "cpu_usage_percent": 80,  # %
            "concurrent_flows": 10,  # flows
            "database_connections": 5,  # connections
        },
        "load_test_scenarios": {
            "light": {"concurrent_flows": 3, "duration": 30},
            "medium": {"concurrent_flows": 7, "duration": 60},
            "heavy": {"concurrent_flows": 15, "duration": 120},
        },
    }
