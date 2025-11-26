# Planning Flow Implementation Patterns - November 2025

## Session Context
PR #1157 - Plan Flow Wired Up milestone (#1141) - 15 sub-issues completed

## Key Patterns

### 1. Multi-Tenant ID Handling (UUID vs int)
**Problem**: Inconsistent tenant ID types causing query failures
**Solution**: Always use UUID for `client_account_id` and `engagement_id` per migration 115

```python
# ✅ CORRECT - UUID pattern
from uuid import UUID

client_account_id = context.client_account_id
self.client_account_uuid = (
    UUID(client_account_id) if isinstance(client_account_id, str) else client_account_id
) if client_account_id else None

# ✅ Pass UUID to repository
self.planning_repo = PlanningFlowRepository(
    db=db,
    client_account_id=self.client_account_uuid,  # UUID
    engagement_id=self.engagement_uuid,          # UUID
)

# ✅ Use UUID in SQLAlchemy queries
stmt = select(ProjectTimeline).where(
    and_(
        ProjectTimeline.client_account_id == client_account_uuid,  # NOT string
        ProjectTimeline.engagement_id == engagement_uuid,          # NOT string
    )
)
```

### 2. Database Query Variable Consistency
**Problem**: Using original string variables in SQL query instead of converted UUIDs
**Solution**: Match variable names between conversion and query

```python
# ❌ WRONG - Variable mismatch
client_account_uuid = UUID(client_account_id) if ... else ...
# Later uses original:
.where(ProjectTimeline.client_account_id == client_account_id)  # String!

# ✅ CORRECT - Consistent UUID variables
client_account_uuid = UUID(client_account_id) if ... else ...
.where(ProjectTimeline.client_account_id == client_account_uuid)  # UUID!
```

### 3. Security: Log Sanitization
**Problem**: Raw LLM output and PII in logs
**Solution**: Redact sensitive data from logs

```python
# ❌ WRONG - Exposes raw output
logger.debug(f"Raw output: {result_str[:200]}")

# ✅ CORRECT - Generic message only
logger.debug("Raw output parsing failed - check agent configuration")

# ❌ WRONG - PII in deprecated warning
logger.warning(f"Deprecated endpoint called by tenant {tenant_id}")

# ✅ CORRECT - No identifiers
logger.warning("DEPRECATED: /api/v1/plan/timeline - use /api/v1/plan/roadmap")
```

### 4. Frontend State Management Optimization
**Problem**: Redundant state updates before refetch
**Solution**: Let refetch handle state updates

```typescript
// ❌ WRONG - Redundant update then refetch
setWaves(updatedWaves);
refetchPlanningData();  // This will update waves anyway

// ✅ CORRECT - Single source of truth
// Persist to backend
await planningFlowApi.updateWavePlan(planning_flow_id, {...});
// Refresh data from server (handles state)
refetchPlanningData();
```

### 5. File Download Cleanup Timing
**Problem**: URL revocation before download completes in some browsers
**Solution**: Delay cleanup with setTimeout

```typescript
// ❌ WRONG - Immediate cleanup
const url = window.URL.createObjectURL(blob);
a.click();
window.URL.revokeObjectURL(url);  // Too fast!

// ✅ CORRECT - Delayed cleanup
a.click();
setTimeout(() => {
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}, 150);  // 150ms buffer
```

### 6. CrewAI Agent Integration (ADR Compliance)
**Required Pattern** for all agent tasks:

```python
# ADR-031: Observability
callback_handler = CallbackHandlerIntegration.create_callback_handler(
    flow_id=str(planning_flow_id),
    context={
        "client_account_id": str(client_account_uuid),
        "engagement_id": str(engagement_uuid),
        "flow_type": "planning",
        "phase": "wave_planning",
    },
)
callback_handler.setup_callbacks()
callback_handler._step_callback({"type": "starting", "task": "wave_planning"})

# Execute task
result = await task.execute_async()

# ADR-029: Safe JSON parsing
parsed_result = sanitize_for_json(parsed_result)

# ADR-024: Store learnings
await memory_manager.store_learning(
    client_account_id=client_account_uuid,
    engagement_id=engagement_uuid,
    scope=LearningScope.ENGAGEMENT,
    pattern_type="wave_planning",
    pattern_data={...}
)
```

## Files Structure Created

```
backend/app/services/planning/
├── wave_planning_service/
│   ├── __init__.py
│   ├── agent_integration.py  # CrewAI integration
│   ├── base.py               # Base service class
│   └── wave_logic.py         # Fallback logic
├── resource_allocation_service/
├── cost_estimation_service/
├── export_service/
│   ├── json_export.py
│   ├── pdf_export.py
│   └── excel_export.py
├── resource_service.py
└── timeline_service.py

backend/app/api/v1/endpoints/plan/
├── __init__.py
├── resources.py
├── roadmap.py
├── target.py
├── waveplanning.py
└── export.py
```

## Issue Closure Workflow

When closing milestone sub-issues:
1. List all issues in range: `gh issue list --state all --json number,title,state | jq '[.[] | select(.number >= X)]'`
2. Close with detailed comment: `gh issue close N -c "Implemented in PR #XXX: [specific changes]"`
3. Reference specific files/lines changed
4. Mention ADR compliance where applicable
