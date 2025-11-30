# Pytest-Asyncio Event Loop Scope Patterns

## Problem: "RuntimeError: Event loop is closed"

Tests fail with event loop errors when using `httpx.AsyncClient` or other async fixtures with incorrect scope.

## Root Cause

pytest-asyncio defaults to `asyncio_default_test_loop_scope=function`, meaning each test gets its own event loop. Session-scoped async fixtures try to use a closed loop on subsequent tests.

## Solution: Match Fixture Scope to Event Loop Scope

```python
# ❌ WRONG - Session scope conflicts with function-scoped event loops
@pytest_asyncio.fixture(scope="session")
async def api_client():
    client = httpx.AsyncClient(base_url="http://localhost:8000")
    yield client
    await client.aclose()  # Fails - event loop closed!

# ✅ CORRECT - Function scope matches event loop lifecycle
@pytest_asyncio.fixture(scope="function")
async def api_client():
    """Create HTTP client for API testing.

    Note: Using function scope to avoid event loop lifecycle issues.
    Each test gets its own client instance and event loop.
    """
    client = httpx.AsyncClient(base_url="http://localhost:8000", timeout=30.0)
    try:
        yield client
    finally:
        await client.aclose()
```

## Additional Fix: Deprecated asyncio.get_event_loop()

```python
# ❌ DEPRECATED in Python 3.10+
timestamp = asyncio.get_event_loop().time()

# ✅ CORRECT - Use get_running_loop() inside async context
timestamp = asyncio.get_running_loop().time()
```

## Symptoms Indicating This Issue

1. First test passes, subsequent tests fail with "Event loop is closed"
2. Error occurs in fixture teardown (`await client.aclose()`)
3. Traceback shows `pytest_asyncio/plugin.py` in finalizer

## Related: Patch Path Errors

When mocking modules with late imports, patch the actual import location:

```python
# If module uses: from app.core.database import AsyncSessionLocal
# Inside a function (late import)

# ❌ WRONG - Module doesn't have this attribute at module level
with patch("app.services.flow_tracker.AsyncSessionLocal"):
    ...

# ✅ CORRECT - Patch where it's actually imported from
with patch("app.core.database.AsyncSessionLocal"):
    ...
```

## Conftest Modularization for Test Fixtures

When conftest.py exceeds 400 lines, split into `fixtures/` subpackage:

```
tests/backend/integration/
├── conftest.py              # Main config + MFO fixtures (134 lines)
├── fixtures/
│   ├── __init__.py          # Re-exports all fixtures
│   ├── api_fixtures.py      # HTTP clients, auth headers
│   ├── db_fixtures.py       # Database engine/session
│   ├── model_fixtures.py    # User, Client, Engagement
│   └── test_utils.py        # BaseIntegrationTest, monitors
```

Main conftest.py imports and re-exports:
```python
from tests.backend.integration.fixtures import (
    api_client, frontend_client, auth_headers,
    test_engine, test_session, test_user, ...
)
```
