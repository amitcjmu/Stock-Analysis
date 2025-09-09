# Async/Await Error Patterns and Solutions

## Common Error: "object dict can't be used in 'await' expression"
This error occurs when trying to await a synchronous function that returns a dict.

## Root Cause Analysis

### Check Function Definition
```python
# If function is defined without async:
def initialize_all_flows() -> dict:
    return {"status": "initialized"}

# DON'T await it:
result = await initialize_all_flows()  # ERROR!
result = initialize_all_flows()        # CORRECT
```

### Check Return Type
```python
# Async functions return coroutines/awaitables
async def get_data() -> dict:  # Can be awaited
    return {"data": "value"}

# Sync functions return objects directly  
def get_data() -> dict:  # Cannot be awaited
    return {"data": "value"}
```

## How to Fix

### 1. Remove Unnecessary Await
```python
# BEFORE - Error
flow_init_result = await initialize_all_flows()

# AFTER - Fixed
flow_init_result = initialize_all_flows()
```

### 2. Make Function Async if Needed
```python
# If function needs to be async
async def initialize_all_flows() -> dict:
    await some_async_operation()
    return {"status": "initialized"}
```

### 3. Check Cascade Effects
When removing await, check if parent functions need adjustment:
```python
async def parent_function():
    # If child is sync, don't await
    result = child_sync_function()
    
    # If child is async, must await
    result = await child_async_function()
```

## Git Investigation Pattern
To find where error was introduced:
```bash
# Find when await was added to sync function
git log -S "await initialize_all_flows" --oneline

# Show the diff
git show <commit-hash>

# Blame specific line
git blame -L 63,63 path/to/file.py
```

## Prevention
- IDE should highlight awaiting non-awaitable
- Type hints help: `-> Awaitable[dict]` vs `-> dict`
- Run mypy for static type checking