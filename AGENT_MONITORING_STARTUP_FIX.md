# Agent Health Monitoring Startup Fix

## Problem Statement
The Agent Health dashboard was empty because the agent monitoring services were never being initialized at application startup. The monitoring code existed but was not being called during the FastAPI lifecycle.

## Root Cause
The `initialize_agent_monitoring()` function from `app/core/agent_monitoring_startup.py` was never called during application startup in `/backend/app/app_setup/lifecycle.py`.

## Solution Implemented

### 1. Added Monitoring Initialization to Lifecycle (PRIMARY FIX)

**File**: `/backend/app/app_setup/lifecycle.py`

**Changes Made**:

1. **Import Statement** (Line 12-15):
```python
from app.core.agent_monitoring_startup import (
    initialize_agent_monitoring,
    shutdown_agent_monitoring,
)
```

2. **Startup Initialization** (Line 141-152):
```python
# Initialize agent monitoring services
try:
    logging.getLogger(__name__).info("🔧 Initializing agent monitoring...")
    initialize_agent_monitoring()
    logging.getLogger(__name__).info(
        "✅ Agent monitoring initialized successfully"
    )
except Exception as e:  # pragma: no cover
    # Don't fail startup if monitoring fails - log and continue
    logging.getLogger(__name__).error(
        f"⚠️ Failed to initialize agent monitoring: {e}", exc_info=True
    )
```

3. **Shutdown Handler** (Line 224-232):
```python
# Shutdown agent monitoring
try:
    logging.getLogger(__name__).info("🛑 Shutting down agent monitoring...")
    shutdown_agent_monitoring()
    logging.getLogger(__name__).info("✅ Agent monitoring shut down successfully")
except Exception as e:  # pragma: no cover
    logging.getLogger(__name__).warning(
        "⚠️ Failed to shut down agent monitoring: %s", e
    )
```

**Placement Strategy**:
- Initialization placed **after** database initialization (to ensure DB is ready)
- Initialization placed **before** feature flags and other optional services
- Errors are caught and logged but don't fail startup (graceful degradation)

### 2. Fixed Seed Script Column Names (SECONDARY FIX)

**File**: `/backend/seeding/00_comprehensive_seed.py`

**Changes Made**:

1. **Fixed Import** (Line 27):
```python
from app.core.database import AsyncSessionLocal  # Was: get_db_session (doesn't exist)
```

2. **Fixed Tenant Constants** (Line 29-31):
```python
# Test tenant IDs
TEST_TENANT_1 = uuid.UUID("11111111-1111-1111-1111-111111111111")
TEST_TENANT_2 = uuid.UUID("22222222-2222-2222-2222-222222222222")
```

3. **Fixed agent_task_history Columns** (Line 415-471):

**Before** (Incorrect):
```python
INSERT INTO migration.agent_task_history (
    id, client_account_id, engagement_id,
    agent_name, task_type, task_description,
    status, duration_ms, input_data, output_data,
    error_message, created_at, completed_at
)
```

**After** (Correct - matches actual table schema):
```python
INSERT INTO migration.agent_task_history (
    id, flow_id, client_account_id, engagement_id,
    agent_name, agent_type, task_id, task_name, task_description,
    status, duration_seconds, started_at, completed_at,
    success, error_message
)
```

**Key Column Corrections**:
- Added `flow_id` (required foreign key to crewai_flow_state_extensions)
- Added `agent_type` (required field, set to "crew_member")
- Added `task_id` (required field, generated UUID)
- Changed `task_type` → `task_name` (column was renamed)
- Changed `duration_ms` → `duration_seconds` (column type/name changed)
- Changed `created_at` → `started_at` (column was renamed)
- Added `success` boolean field (required, derived from status)
- Removed `input_data` and `output_data` (not in current schema)

## Verification

### 1. Check Startup Logs
```bash
docker logs migration_backend 2>&1 | grep -A 10 "Initializing agent monitoring"
```

**Expected Output**:
```
2025-11-01 01:36:46,617 - app.app_setup.lifecycle - INFO - 🔧 Initializing agent monitoring...
2025-11-01 01:36:46,618 - app.services.agent_monitor - INFO - Agent monitoring started
2025-11-01 01:36:46,618 - app.core.agent_monitoring_startup - INFO - ✅ Agent monitor started successfully
2025-11-01 01:36:46,618 - apscheduler.scheduler - INFO - Added job "Daily Agent Performance Aggregation" to job store "default"
2025-11-01 01:36:46,618 - apscheduler.scheduler - INFO - Added job "Startup Yesterday Aggregation" to job store "default"
2025-11-01 01:36:46,618 - apscheduler.scheduler - INFO - Scheduler started
2025-11-01 01:36:46,618 - app.services.agent_performance_aggregation_service - INFO - Agent performance aggregation service started
2025-11-01 01:36:46,619 - app.core.agent_monitoring_startup - INFO - ✅ Agent performance aggregation service started successfully
2025-11-01 01:36:46,619 - app.core.agent_monitoring_startup - INFO - 🔍 Agent monitoring services initialized:
2025-11-01 01:36:46,619 - app.core.agent_monitoring_startup - INFO -    - Real-time task monitoring: ACTIVE
2025-11-01 01:36:46,619 - app.core.agent_monitoring_startup - INFO -    - Database persistence: ACTIVE
2025-11-01 01:36:46,619 - app.core.agent_monitoring_startup - INFO -    - Daily aggregation: SCHEDULED
2025-11-01 01:36:46,619 - app.core.agent_monitoring_startup - INFO -    - Pattern discovery: ENABLED
```

### 2. Verify Services Are Running
The following services should now be active:
- ✅ Agent Monitor (real-time task tracking)
- ✅ Database Writer Thread (persisting task history)
- ✅ Agent Performance Aggregation Service (daily metrics)
- ✅ APScheduler (scheduled jobs for aggregation)

### 3. Database Schema Validation
```bash
docker exec migration_postgres psql -U postgres -d migration_db -c "\d migration.agent_task_history"
```

Verify columns match the seed script inserts.

## What Gets Populated Now

### Tables That Will Start Receiving Data:
1. **agent_task_history** - When agents execute tasks (requires instrumentation - Phase 2B)
2. **agent_performance_daily** - Daily aggregation at 2 AM UTC
3. **agent_discovered_patterns** - When agents discover patterns (requires instrumentation - Phase 2B)

### Monitoring Features Now Active:
- Real-time task status tracking
- LLM call monitoring
- Task duration metrics
- Agent performance analytics
- Pattern discovery and storage
- Daily performance aggregation

## Next Steps (Deferred to Phase 2B)

### Agent Task Instrumentation
To populate the tables, we still need to instrument agent execution:

1. **Flow Handlers** - Add monitoring callbacks:
   - `/backend/app/services/crewai_flows/handlers/*`
   - Call `agent_monitor.start_task()` when agent tasks begin
   - Call `agent_monitor.update_task_status()` for status changes
   - Call `agent_monitor.complete_task()` when tasks finish

2. **CrewAI Callback Integration**:
   - Use `AgentHealthCallbackHandler` from `app/services/agent_health_callback_handler.py`
   - Integrate with CrewAI crew execution
   - Track LLM calls, thinking phases, and task execution

3. **Testing**:
   - Run a discovery flow
   - Check agent_task_history table gets populated
   - Verify frontend Agent Health dashboard shows data

## Impact

### Before Fix:
- ❌ Agent monitoring services never started
- ❌ Tables remain empty
- ❌ Agent Health dashboard shows "No data"
- ❌ No performance metrics available

### After Fix:
- ✅ Monitoring services start at application startup
- ✅ Background threads running (agent monitor + DB writer)
- ✅ Daily aggregation scheduled
- ✅ System ready to receive agent instrumentation data
- ✅ Graceful error handling (won't crash startup if monitoring fails)

## Testing Recommendations

### Immediate Testing:
```bash
# 1. Restart backend
cd config/docker && docker-compose restart backend

# 2. Check startup logs
docker logs migration_backend --tail 100 | grep "agent monitoring"

# 3. Verify health
curl http://localhost:8000/health

# 4. Check monitoring is active (should see log messages)
docker logs migration_backend -f
```

### After Phase 2B Instrumentation:
```bash
# 1. Start a discovery flow via UI or API
# 2. Query agent_task_history
docker exec migration_postgres psql -U postgres -d migration_db -c \
  "SELECT agent_name, task_name, status, duration_seconds FROM migration.agent_task_history ORDER BY started_at DESC LIMIT 10;"

# 3. Check Agent Health dashboard at http://localhost:8081/agent-health
```

## Files Modified

### Backend Files:
1. `/backend/app/app_setup/lifecycle.py` - Added monitoring startup/shutdown
2. `/backend/seeding/00_comprehensive_seed.py` - Fixed column names and imports

### No Changes Required:
- `/backend/app/core/agent_monitoring_startup.py` - Already correct
- `/backend/app/services/agent_monitor.py` - Already correct
- `/backend/app/services/agent_performance_aggregation_service.py` - Already correct

## References

### Database Schema:
- Table: `migration.agent_task_history`
- Columns: id, flow_id, agent_name, agent_type, task_id, task_name, task_description,
           started_at, completed_at, status, duration_seconds, success, result_preview,
           error_message, llm_calls_count, thinking_phases_count, token_usage,
           memory_usage_mb, confidence_score, client_account_id, engagement_id, created_at

### Architecture Documents:
- Agent Health Monitoring Design: `/docs/development/AGENT_HEALTH_MONITORING.md`
- Phase 2 Implementation Plan: `/docs/development/agent_health_monitoring_phase2.md`

## Compliance Notes

- Error handling follows graceful degradation pattern (ADR-010)
- Multi-tenant isolation maintained (client_account_id, engagement_id)
- Logging follows established patterns (emoji indicators + structured messages)
- No startup failures if monitoring has issues (resilience requirement)
- Thread-safe implementation using locks (concurrent execution support)

---

**Status**: ✅ **COMPLETE - Minimal Viable Implementation**

**Date**: 2025-10-31

**Next Phase**: Agent task instrumentation in flow execution handlers
