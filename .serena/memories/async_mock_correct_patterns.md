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

## Key Rule: AsyncMock Chaining
When mocking SQLAlchemy-style chains:
1. Create single root AsyncMock
2. Chain return_value assignments
3. Never create intermediate mock objects
4. Match exact method chain from production code

## Testing After Fix
```bash
# Verify fixes in Docker
docker exec migration_backend pytest backend/tests/services/test_asset_write_back.py -v
# All 14 tests should pass
```