"""
Pytest Markers for Test Categorization

Custom pytest markers for organizing and filtering tests across the migration
orchestration system. Supports categorization by architecture patterns,
test types, performance characteristics, and agent-related testing.

Generated with CC for standardized test organization.
"""

import pytest

# Architecture Pattern Markers

def pytest_configure(config):
    """Configure custom pytest markers."""

    # Architecture Pattern Markers
    config.addinivalue_line(
        "markers",
        "mfo: Tests aligned with Master Flow Orchestrator (MFO) pattern - tests the two-table architecture and centralized flow coordination"
    )

    config.addinivalue_line(
        "markers",
        "legacy: Tests for legacy code that needs updating to MFO pattern - marks code requiring migration"
    )

    # Test Type Markers
    config.addinivalue_line(
        "markers",
        "integration: Integration tests that require multiple components - tests cross-service interactions"
    )

    config.addinivalue_line(
        "markers",
        "unit: Unit tests for isolated component testing - tests single functions/classes"
    )

    config.addinivalue_line(
        "markers",
        "e2e: End-to-end tests covering complete user workflows - tests full application flows"
    )

    config.addinivalue_line(
        "markers",
        "api: API endpoint tests - tests REST API functionality and contracts"
    )

    # Performance and Load Testing
    config.addinivalue_line(
        "markers",
        "slow: Slow running tests (>30 seconds) - tests that require extended execution time"
    )

    config.addinivalue_line(
        "markers",
        "performance: Performance benchmark tests - tests that measure execution speed and resource usage"
    )

    config.addinivalue_line(
        "markers",
        "load: Load testing for concurrent operations - tests system behavior under stress"
    )

    # Agent and AI Testing
    config.addinivalue_line(
        "markers",
        "agent: Agent-related tests using TenantScopedAgentPool - tests CrewAI agent functionality"
    )

    config.addinivalue_line(
        "markers",
        "agent_memory: Tests for agent memory and learning systems - tests persistent agent state"
    )

    config.addinivalue_line(
        "markers",
        "llm: Tests requiring LLM integration - tests that need actual language model calls"
    )

    # Database and Data Testing
    config.addinivalue_line(
        "markers",
        "database: Tests requiring database operations - tests that need actual DB connections"
    )

    config.addinivalue_line(
        "markers",
        "tenant_isolation: Tests verifying multi-tenant data isolation - tests security boundaries"
    )

    config.addinivalue_line(
        "markers",
        "migration: Database migration tests - tests schema changes and data migrations"
    )

    # Flow and Workflow Testing
    config.addinivalue_line(
        "markers",
        "discovery_flow: Discovery workflow tests - tests asset discovery and analysis flows"
    )

    config.addinivalue_line(
        "markers",
        "assessment_flow: Assessment workflow tests - tests migration assessment flows"
    )

    config.addinivalue_line(
        "markers",
        "collection_flow: Collection workflow tests - tests data collection and questionnaire flows"
    )

    config.addinivalue_line(
        "markers",
        "planning_flow: Planning workflow tests - tests migration planning and wave management"
    )

    # Security and Compliance
    config.addinivalue_line(
        "markers",
        "security: Security-focused tests - tests authentication, authorization, and data protection"
    )

    config.addinivalue_line(
        "markers",
        "compliance: Compliance validation tests - tests adherence to regulatory requirements"
    )

    config.addinivalue_line(
        "markers",
        "audit: Audit trail and logging tests - tests for compliance tracking and monitoring"
    )

    # Infrastructure and Deployment
    config.addinivalue_line(
        "markers",
        "docker: Tests requiring Docker containers - tests that need containerized services"
    )

    config.addinivalue_line(
        "markers",
        "redis: Tests requiring Redis cache - tests that need Redis for caching or queuing"
    )

    config.addinivalue_line(
        "markers",
        "external_api: Tests calling external services - tests that need third-party API access"
    )

    # Quality and Validation
    config.addinivalue_line(
        "markers",
        "data_quality: Data validation and quality tests - tests for data integrity and consistency"
    )

    config.addinivalue_line(
        "markers",
        "field_mapping: Field mapping intelligence tests - tests for automated field mapping logic"
    )

    config.addinivalue_line(
        "markers",
        "regression: Regression tests for critical functionality - tests to prevent feature breakage"
    )

    # Development and Debugging
    config.addinivalue_line(
        "markers",
        "debug: Tests for debugging specific issues - temporary tests for troubleshooting"
    )

    config.addinivalue_line(
        "markers",
        "smoke: Smoke tests for basic functionality - quick tests to verify system health"
    )

    config.addinivalue_line(
        "markers",
        "mock: Tests using extensive mocking - tests that simulate external dependencies"
    )

    # Async and Concurrency
    config.addinivalue_line(
        "markers",
        "async_test: Async/await test functions - tests that use asynchronous execution"
    )

    config.addinivalue_line(
        "markers",
        "concurrent: Tests for concurrent operations - tests that verify thread/async safety"
    )

    # Browser and Frontend
    config.addinivalue_line(
        "markers",
        "browser: Browser-based tests using Playwright - tests that require browser automation"
    )

    config.addinivalue_line(
        "markers",
        "frontend: Frontend component tests - tests for React components and UI logic"
    )


# Marker Combinations for Common Test Scenarios

# Use these marker combinations for standard test scenarios:

"""
Common Marker Combinations:

1. MFO Integration Test:
   @pytest.mark.mfo
   @pytest.mark.integration
   @pytest.mark.database
   @pytest.mark.async_test

2. Agent Performance Test:
   @pytest.mark.agent
   @pytest.mark.performance
   @pytest.mark.slow
   @pytest.mark.tenant_isolation

3. Discovery Flow E2E:
   @pytest.mark.discovery_flow
   @pytest.mark.e2e
   @pytest.mark.mfo
   @pytest.mark.agent

4. Legacy Migration Test:
   @pytest.mark.legacy
   @pytest.mark.regression
   @pytest.mark.database

5. Security Compliance Test:
   @pytest.mark.security
   @pytest.mark.compliance
   @pytest.mark.tenant_isolation
   @pytest.mark.audit

6. Quick Smoke Test:
   @pytest.mark.smoke
   @pytest.mark.unit
   @pytest.mark.mock

Example Usage in Test Files:

```python
import pytest

@pytest.mark.mfo
@pytest.mark.integration
@pytest.mark.database
@pytest.mark.async_test
async def test_mfo_flow_creation_with_child_flows(
    demo_tenant_context,
    mock_async_session,
    sample_master_flow_data
):
    # Test MFO pattern with proper two-table architecture
    pass

@pytest.mark.agent
@pytest.mark.performance
@pytest.mark.slow
@pytest.mark.tenant_isolation
async def test_tenant_scoped_agent_pool_performance(
    mock_tenant_scoped_agent_pool,
    tenant_isolation_test_data
):
    # Test agent pool performance across multiple tenants
    pass

@pytest.mark.legacy
@pytest.mark.regression
@pytest.mark.database
def test_legacy_endpoint_backward_compatibility():
    # Ensure legacy endpoints still work during migration
    pass
```

Running Tests by Markers:

```bash
# Run only MFO-aligned tests
pytest -m "mfo"

# Run integration tests but skip slow ones
pytest -m "integration and not slow"

# Run all agent tests with tenant isolation
pytest -m "agent and tenant_isolation"

# Run smoke tests for quick validation
pytest -m "smoke"

# Run all discovery flow tests
pytest -m "discovery_flow"

# Run regression tests only
pytest -m "regression"

# Run performance tests (usually slow)
pytest -m "performance" --timeout=300

# Run all tests except external API calls
pytest -m "not external_api"
```

Marker Validation:
The markers are configured to help organize tests by:

1. **Architecture Alignment**: mfo vs legacy
2. **Test Scope**: unit, integration, e2e
3. **Performance Impact**: slow, performance, load
4. **Component Focus**: agent, database, frontend
5. **Workflow Type**: discovery_flow, assessment_flow, etc.
6. **Quality Assurance**: security, compliance, regression
7. **Infrastructure Needs**: docker, redis, external_api

This organization enables:
- Selective test execution during development
- Performance-aware CI/CD pipelines
- Compliance verification workflows
- Architecture migration tracking
- Debugging and troubleshooting support
"""


# Helper functions for marker validation

def is_mfo_test(item):
    """Check if a test is marked as MFO-aligned."""
    return item.get_closest_marker("mfo") is not None


def is_slow_test(item):
    """Check if a test is marked as slow."""
    return item.get_closest_marker("slow") is not None


def requires_database(item):
    """Check if a test requires database access."""
    return item.get_closest_marker("database") is not None


def requires_agent(item):
    """Check if a test requires agent functionality."""
    return item.get_closest_marker("agent") is not None


def is_tenant_isolation_test(item):
    """Check if a test validates tenant isolation."""
    return item.get_closest_marker("tenant_isolation") is not None
