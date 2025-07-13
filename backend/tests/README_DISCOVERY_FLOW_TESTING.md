# Discovery Flow Testing Guide

This guide provides instructions for setting up and running tests for the Discovery Flow implementation.

## Development Environment Setup

### Prerequisites
- Docker and Docker Compose installed
- Python 3.9+ (for running tests locally)
- DeepInfra API key (for LLM testing)

### 1. Start Development Environment

```bash
# Start all services in development mode
docker-compose -f docker-compose.dev.yml up -d

# Check that services are running
docker-compose -f docker-compose.dev.yml ps

# View logs
docker-compose -f docker-compose.dev.yml logs -f backend
```

### 2. Environment Variables

Create a `.env.dev` file in the `backend/` directory:

```env
# Database
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/migration_db

# DeepInfra API
DEEPINFRA_API_KEY=your_deepinfra_api_key_here

# CrewAI Configuration
CREWAI_ENABLED=true
ENABLE_REAL_CREWAI=true

# Development Settings
DEBUG=true
LOG_LEVEL=DEBUG
ENVIRONMENT=development

# Test Settings
TEST_MODE=true
MOCK_LLM_RESPONSES=false  # Set to true to use mocked responses
```

### 3. Install Test Dependencies

```bash
# Access the backend container
docker exec -it migration_backend_dev bash

# Install test dependencies
pip install pytest pytest-asyncio pytest-mock pytest-cov httpx

# Or from outside the container
docker exec migration_backend_dev pip install pytest pytest-asyncio pytest-mock pytest-cov httpx
```

## Test Structure

### Test Files

- `tests/fixtures/discovery_flow_fixtures.py` - Test data and fixtures
- `tests/test_discovery_flow_base.py` - Base test class with common utilities
- `tests/integration/test_discovery_agent_decisions.py` - Agent decision integration tests

### Key Test Fixtures

1. **Mock CMDB Data** - Sample server, application, and database data
2. **Field Mapping Suggestions** - Expected mapping suggestions from agents
3. **Agent Decisions** - Expected agent decision outcomes
4. **SSE Event Sequences** - Sample event streams for testing

## Running Tests

### Run All Discovery Flow Tests

```bash
# Inside the container
docker exec -it migration_backend_dev pytest tests/ -v -k "discovery"

# Run with coverage
docker exec -it migration_backend_dev pytest tests/ -v -k "discovery" --cov=app --cov-report=html
```

### Run Specific Test Categories

```bash
# Unit tests only
docker exec -it migration_backend_dev pytest tests/ -v -m "unit"

# Integration tests only
docker exec -it migration_backend_dev pytest tests/ -v -m "integration"

# Tests requiring LLM
docker exec -it migration_backend_dev pytest tests/ -v -m "requires_llm"

# Slow tests (>5 seconds)
docker exec -it migration_backend_dev pytest tests/ -v -m "slow"
```

### Run Individual Test Files

```bash
# Run agent decision tests
docker exec -it migration_backend_dev pytest tests/integration/test_discovery_agent_decisions.py -v

# Run with specific test
docker exec -it migration_backend_dev pytest tests/integration/test_discovery_agent_decisions.py::TestDiscoveryAgentDecisions::test_data_validation_agent_decisions -v
```

## Testing SSE Events

The Discovery Flow uses Server-Sent Events for real-time updates. To test SSE:

### Manual SSE Testing

```bash
# Start an SSE client to monitor events
curl -N -H "X-Client-Account-ID: 99999" \
     -H "X-Engagement-ID: 99999" \
     -H "X-User-ID: 12345678-1234-5678-1234-567812345678" \
     -H "Authorization: Bearer test-token" \
     http://localhost:8000/api/v1/unified-discovery/flow/events/{flow_id}
```

### Automated SSE Testing

The test suite includes SSE event collection and verification:

```python
# Example from test
events = []
event_task = asyncio.create_task(self._collect_sse_events(flow_id, events))
# ... trigger flow actions ...
await asyncio.sleep(5)  # Collect events
event_task.cancel()
# Verify events
```

## Test Data Management

### Creating Test Data

```python
from tests.fixtures.discovery_flow_fixtures import (
    create_test_discovery_flow,
    create_test_data_import,
    get_mock_file_content
)

# Create a test flow
flow = create_test_discovery_flow()

# Generate test CSV
csv_content = get_mock_file_content("csv")

# Generate test JSON
json_content = get_mock_file_content("json")
```

### Performance Testing

For performance testing with large datasets:

```python
from tests.fixtures.discovery_flow_fixtures import PERFORMANCE_TEST_DATA

# Get 1000 server records
large_dataset = PERFORMANCE_TEST_DATA["large_dataset"]
```

## Debugging Tests

### Enable Detailed Logging

```bash
# Run with debug logging
docker exec -it migration_backend_dev pytest tests/ -v -s --log-cli-level=DEBUG
```

### Database State Inspection

```bash
# Connect to database
docker exec -it migration_postgres_dev psql -U postgres -d migration_db

# Check discovery flows
SELECT flow_id, status, current_phase FROM discovery_flows;

# Check data imports
SELECT import_id, flow_id, status FROM data_imports;
```

### View Test Coverage Report

```bash
# Generate HTML coverage report
docker exec -it migration_backend_dev pytest tests/ --cov=app --cov-report=html

# Coverage report will be in htmlcov/index.html
```

## Common Issues and Solutions

### 1. LLM API Timeout

**Issue**: Tests fail with DeepInfra timeout
**Solution**: 
- Check your API key is valid
- Increase timeout in test configuration
- Use `MOCK_LLM_RESPONSES=true` for faster testing

### 2. Database Connection Issues

**Issue**: Tests can't connect to database
**Solution**:
- Ensure postgres service is healthy: `docker-compose -f docker-compose.dev.yml ps`
- Check database logs: `docker-compose -f docker-compose.dev.yml logs postgres`

### 3. SSE Event Collection Hanging

**Issue**: SSE tests hang indefinitely
**Solution**:
- Add timeout to event collection
- Ensure flow is actually generating events
- Check backend logs for errors

## Writing New Tests

### Test Template

```python
@pytest.mark.asyncio
class TestNewDiscoveryFeature(BaseDiscoveryFlowTest):
    
    @integration_test
    @requires_llm
    async def test_new_feature(self, mock_deepinfra_llm):
        """Test description."""
        # 1. Create flow
        flow = await self.create_discovery_flow()
        
        # 2. Upload test data
        content = get_mock_file_content("csv")
        await self.upload_file(flow["flow_id"], content)
        
        # 3. Wait for phase
        await self.wait_for_phase(flow["flow_id"], "target_phase")
        
        # 4. Verify results
        status = await self.get_flow_status(flow["flow_id"])
        assert "expected_field" in status
```

### Best Practices

1. **Use fixtures** - Leverage the provided test fixtures for consistency
2. **Mock external services** - Mock LLM and storage services when possible
3. **Test edge cases** - Include tests for error scenarios
4. **Verify agent decisions** - Check that agents make logical decisions
5. **Test SSE events** - Verify real-time updates work correctly
6. **Clean up** - Ensure tests clean up after themselves

## CI/CD Integration

For CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run Discovery Flow Tests
  run: |
    docker-compose -f docker-compose.test.yml up -d
    docker exec migration_backend_test pytest tests/ -v -m "not slow"
    docker-compose -f docker-compose.test.yml down
```

## Additional Resources

- [Discovery Flow Architecture](../docs/architecture/DISCOVERY_FLOW_COMPLETE_ARCHITECTURE.md)
- [CrewAI Development Guide](../docs/development/CrewAI_Development_Guide.md)
- [API Documentation](../docs/api/discovery_flow_api.md)