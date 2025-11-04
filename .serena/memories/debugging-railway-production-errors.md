# Debugging Railway/Vercel Production Errors

## Pattern: Transaction Phase vs Background Phase Errors

**Key Insight**: Error location determines fix location.

### Error Analysis Process

1. **Identify Error Phase**
```
Error in logs → During transaction OR After transaction?
├─ During transaction: Fix BEFORE background execution starts
└─ After transaction: Fix IN background execution service
```

2. **Transaction Phase Indicators**
```
✅ Transaction failed, rolling back
✅ Transaction rolled back successfully
✅ Building error response
```

3. **Background Phase Indicators**
```
✅ Background flow execution started
✅ Creating CrewAI service with fresh session
✅ CREWAI DISCOVERY FLOW INITIALIZATION
```

## Example: Import Flow Error Location

**Error Logs**:
```
🗳️ Data import record created with raw records: ec5fe5e5-...
✅ Flow Lifecycle Manager initialized for client 11111111-...
Error instantiating LLM from environment/fallback: OPENAI_API_KEY is required
❌ Transaction failed, rolling back
```

**Analysis**:
- "Data import record created" = IN transaction
- "Flow Lifecycle Manager initialized" = MFO created IN transaction
- "Transaction failed" = Error happened BEFORE commit
- **Fix location**: Before MFO creation (NOT in background service)

## Search Commands for Root Cause

### 1. Find Error Source in Codebase
```bash
# Where does the error message come from?
docker exec migration_backend bash -c "cd /app && grep -r 'Error instantiating LLM' ."
# Result: venv/lib/python3.11/site-packages/crewai/utilities/llm_utils.py
```

### 2. Find Call Stack Leading to Error
```bash
# Search for log messages BEFORE the error
grep -B10 "Error instantiating LLM" logs.txt
# Look for: what function was called? what class initialized?
```

### 3. Trace Code Path
```python
# From logs: "Flow Lifecycle Manager initialized"
# Search codebase:
grep -r "Flow Lifecycle Manager initialized" backend/
# Result: backend/app/services/flow_orchestration/lifecycle_manager.py:49

# This tells us: FlowLifecycleManager.__init__ ran before error
# FlowLifecycleManager is part of MasterFlowOrchestrator.__init__
```

### 4. Find MFO Instantiation Points
```bash
grep -rn "MasterFlowOrchestrator(" backend/app/services/data_import/
# Shows: import_storage_handler.py:290
```

### 5. Check Git History for When Code Changed
```bash
git blame backend/app/services/master_flow_orchestrator/core.py | grep -A5 "initialize_all_flows"
# Shows: c29baeca9b (Aug 21, 2025) added initialize_all_flows()

git log --oneline --since="8 weeks ago" --all -- <file>
# Shows: timeline of changes to file
```

## Fix Verification Pattern

**Wrong Approach**:
```python
# ❌ Fix in background execution when error is in transaction
async def _run_discovery_flow(...):
    ensure_crewai_environment()  # Too late - transaction already failed
```

**Correct Approach**:
```python
# ✅ Fix BEFORE the code that causes error
async def handle_import(...):
    async with transaction_manager.transaction():
        ensure_crewai_environment()  # BEFORE MFO creation
        orchestrator = MasterFlowOrchestrator(self.db, context)
```

## Railway/Vercel Specific Issues

### Environment Variable Inheritance
- **Startup env vars** may not propagate to:
  - Async background tasks
  - New transaction contexts
  - Subprocess/thread execution

### Solution: Explicit Initialization
```python
# Don't rely on startup initialization
# Call ensure_crewai_environment() at each boundary:
# 1. Startup (lifecycle.py)
# 2. Transaction start (import_storage_handler.py)
# 3. Background task start (background_execution_service.py)
# 4. Agent creation (manager.py)
```

## Diagnostic Workflow

```
1. Analyze error logs → Identify phase (transaction vs background)
   ↓
2. Search codebase → Find error message source
   ↓
3. Trace call stack → Find what code ran before error
   ↓
4. Check git blame → When was problematic code added?
   ↓
5. Verify fix location → BEFORE the error-causing code
   ↓
6. Test fix → Check logs show new initialization message
```

## Testing Production Fixes

**Before Fix**:
```
Error instantiating LLM from environment/fallback: OPENAI_API_KEY is required
❌ Transaction failed, rolling back
```

**After Fix**:
```
✅ CrewAI environment configured for MFO initialization
✅ Flow Lifecycle Manager initialized for client...
[No error - transaction succeeds]
```

## Common Pitfalls

1. **Fixing wrong phase**: Background fix when error is in transaction
2. **Missing initialization**: Only fixing one code path, missing others
3. **Relying on startup**: Assuming startup env vars persist everywhere
4. **Incomplete testing**: Not testing the specific failing code path
