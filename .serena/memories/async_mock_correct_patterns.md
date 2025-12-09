# Async Mock Correct Patterns

## Problem: TypeError 'coroutine' object is not subscriptable
**Root Cause**: AsyncMock returning coroutines instead of data values
**Files Affected**: test_asset_write_back.py (14 failures)

## Pattern 1: Database Result Mocking

### ❌ INCORRECT - Creates Intermediate Mocks
```python
scalars_mock = AsyncMock()
scalars_mock.all = AsyncMock(return_value=asset_ids)
asset_result = AsyncMock()
asset_result.scalars = AsyncMock(return_value=scalars_mock)
mock_db.execute.return_value = asset_result
```

### ✅ CORRECT - Direct Chain Assignment
```python
asset_result = AsyncMock()
asset_result.scalars.return_value.all.return_value = asset_ids
mock_db.execute.return_value = asset_result
```

## Pattern 2: Async Method Mocking

### ❌ INCORRECT - Returns Coroutine
```python
mock_obj.fetchall = AsyncMock(mock_data)  # Wrong!
```

### ✅ CORRECT - Explicit return_value
```python
mock_obj.fetchall = AsyncMock(return_value=mock_data)
```

## Pattern 3: Event Loop Context
**Problem**: RuntimeError: There is no current event loop
**Solution**: Mock asyncio.create_task
```python
with patch("asyncio.create_task"):
    # Code that triggers auto-flush
    registry.record_metric("Service", "metric", value)
```

## Pattern 4: SQLAlchemy Synchronous Methods (Added Dec 2025)

**Problem**: "coroutine object has no attribute" errors with `scalar_one_or_none()` and `scalars()`
**Root Cause**: These SQLAlchemy methods are SYNCHRONOUS - only `execute()` is async

### ❌ INCORRECT - Using AsyncMock for sync methods
```python
mock_result = AsyncMock()
mock_result.scalar_one_or_none = AsyncMock(return_value=None)  # WRONG!
mock_result.scalars = AsyncMock(return_value=Mock(all=Mock(return_value=[])))  # WRONG!
session.execute = AsyncMock(return_value=mock_result)
```

### ✅ CORRECT - Regular Mock for sync, AsyncMock only for execute()
```python
mock_result = Mock()  # Regular Mock, not AsyncMock
mock_result.scalar_one_or_none = Mock(return_value=None)  # Sync method
mock_result.scalars = Mock(return_value=Mock(all=Mock(return_value=[])))  # Sync method
session.execute = AsyncMock(return_value=mock_result)  # Only execute() is async
```

**Helper Pattern for DB Sessions:**
```python
def setup_mock_db_session_empty():
    """Create properly mocked async database session that returns empty results."""
    session = AsyncMock()

    # Mock execute to return proper async result
    # IMPORTANT: scalar_one_or_none is NOT async in SQLAlchemy - use regular Mock
    mock_result = Mock()
    mock_result.scalar_one_or_none = Mock(return_value=None)
    mock_result.scalars = Mock(return_value=Mock(all=Mock(return_value=[])))

    session.execute = AsyncMock(return_value=mock_result)

    return session
```

**Reference**: This pattern was identified fixing Issue #1193 regression tests in `test_intelligent_gap_scanner.py`.

## Key Rule: AsyncMock Chaining
When mocking SQLAlchemy-style chains:
1. Create single root AsyncMock
2. Chain return_value assignments
3. Never create intermediate mock objects
4. Match exact method chain from production code
5. **CRITICAL**: Only use AsyncMock for truly async methods (`execute()`)

## Testing After Fix
```bash
# Verify fixes in Docker
docker exec migration_backend pytest backend/tests/services/test_asset_write_back.py -v
# All 14 tests should pass
```
