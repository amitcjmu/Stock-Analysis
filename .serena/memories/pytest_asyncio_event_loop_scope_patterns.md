# Pytest-Asyncio Event Loop Scope Patterns

## Problem: "RuntimeError: Event loop is closed"

Tests fail with event loop errors when using `httpx.AsyncClient` or other async fixtures with incorrect scope.

## Root Cause

pytest-asyncio defaults to `asyncio_default_test_loop_scope=function`, meaning each test gets its own event loop. Session-scoped async fixtures try to use a closed loop on subsequent tests.

**CRITICAL**: In pytest-asyncio 0.23+, you MUST explicitly set `asyncio_default_fixture_loop_scope` in pytest.ini.

## Solution: Configuration + Fixture Scope

### Step 1: Add to pytest.ini (REQUIRED)
```ini
[tool:pytest]
asyncio_mode = auto
asyncio_default_fixture_loop_scope = function
```

### Step 2: Match Fixture Scope to Event Loop Scope

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

## Test Execution Location (CRITICAL)

**WRONG**: Running from `/app/back_end/backend/integration/`
**CORRECT**: Running from `/app/back_end` or project root

```bash
# Correct command inside Docker container
cd /app/back_end
pytest tests/backend/integration/test_asset_inventory_api.py -v
```

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

## Files Updated (December 2025)

- `tests/pytest.ini:73-74` - Added asyncio_default_fixture_loop_scope = function
- `backend/pytest.ini:17-18` - Added asyncio_default_fixture_loop_scope = function
