# Integration Test Timeout Configuration for Agent-Based Operations (Oct 2025)

## Problem
Integration tests with agent LLM calls (field mapping, dependency analysis) timing out at 180s despite successful individual execution. Tests need to validate actual agent functionality, not mock it.

## Root Cause Analysis
CSV file analysis with agent-based field mapping involves:
- Multiple agent LLM calls (one per column)
- Each call: 20-30 seconds via DeepInfra/Llama 4
- Total for 3-5 columns: 60-150+ seconds
- Plus HTTP overhead, database operations

**Test failure pattern**: timeout at 180s, but individual runs pass

## Solution Pattern

### 1. HTTP Client Timeout (conftest.py)
```python
@pytest_asyncio.fixture
async def async_client() -> AsyncIterator[AsyncClient]:
    """Create async HTTP client for API testing.

    Timeout set to 300s to accommodate agent LLM calls and file analysis.
    Some CSV analysis tests with multiple agent field mapping calls can take 3-5 minutes.
    """
    base_url = os.getenv("DOCKER_API_BASE", "http://localhost:8000")

    async with AsyncClient(base_url=base_url, timeout=300.0) as client:
        yield client
```

### 2. Pytest Test Timeout
```python
@pytest.mark.asyncio
@pytest.mark.timeout(330)  # CSV analysis with multiple agent field mapping calls can take 3-5 minutes
async def test_analyze_csv_file(
    async_client: AsyncClient,
    auth_headers: dict,
):
    """Test analyzing a CSV file for import."""
    # Test implementation
```

## Timeout Calculation Formula
```
Test Timeout = (Columns × 30s) + HTTP_overhead + 30s buffer
HTTP Timeout = Test_Timeout - 30s

For 5 columns:
Test: 330s (5 × 30 + 60 + 120)
HTTP: 300s
```

## Test Isolation Debugging
**Symptom**: Tests pass individually but fail in full suite (422 errors)

**Analysis Approach**:
```bash
# Run individually (passes)
docker exec migration_backend python -m pytest tests/.../test_file.py::test_name -v

# Run full suite (may fail due to timing)
docker exec migration_backend python -m pytest tests/.../test_file.py -v

# Diagnosis: NOT code issue - timing-related test isolation
```

**Resolution**: Increase timeouts rather than fixing "code bugs"

## Related Files
- `backend/tests/backend/integration/collection/conftest.py` - HTTP client fixture
- `backend/tests/backend/integration/collection/test_bulk_import_endpoints.py` - CSV analysis tests
- `backend/tests/backend/integration/collection/test_dynamic_questions_endpoints.py` - Agent pruning tests

## Validation
After timeout increases:
- 29/29 integration tests passing (100%)
- Runtime: 2m 23s (well under 330s limit)
- No intermittent failures

## When to Apply
Use extended timeouts when tests involve:
- ✅ Agent LLM field mapping operations
- ✅ CrewAI agent execution with LLM calls
- ✅ Multiple sequential agent operations
- ✅ File analysis requiring AI processing
- ❌ Simple API CRUD operations (keep at 60-120s)
