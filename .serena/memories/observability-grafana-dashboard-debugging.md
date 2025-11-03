# Grafana Dashboard Debugging - Observability Stack

## Problem: Dashboard Shows "No Data" Despite Working Backend

**Symptom**: Grafana dashboards appear broken but backend logs show data exists.

**Root Cause Pattern**: Default time ranges don't match actual data timestamps.

**Solution**:
```json
// In Grafana dashboard JSON (e.g., llm-costs.json):
"time": {
  "from": "now-30d",  // Was: "now-24h" - too narrow
  "to": "now"
}
```

**When to Check**:
- Dashboard shows "No Data" but database has records
- Check `SELECT MAX(created_at) FROM table` to find latest data timestamp
- Adjust time range to encompass actual data

---

## Problem: Negative Flow Durations in Metrics

**Symptom**: `updated_at` timestamp BEFORE `created_at` causing impossible negative durations.

**Root Cause**: Child entity creation copying parent's old timestamps:
```python
# WRONG - Copies old timestamps from parent
child_flow = ChildFlow(
    created_at=parent_flow.created_at,  # Old time
    updated_at=parent_flow.updated_at   # Even older!
)
```

**Fix - Let SQLAlchemy Defaults Work**:
```python
# CORRECT - Omit timestamps, use database defaults
child_flow = ChildFlow(
    # created_at and updated_at omitted
    # SQLAlchemy model has server_default=func.now()
)
```

**Alternative - Explicit Current Time**:
```python
from datetime import datetime
child_flow = ChildFlow(
    created_at=datetime.utcnow(),
    updated_at=datetime.utcnow()
)
```

**When to Apply**: Any entity creation that derives from existing records.

---

## Problem: LiteLLM Callbacks Not Firing

**Symptom**: LLM calls execute but tracking callback never invoked.

**Root Cause**: Using deprecated `litellm.callbacks` instead of modern callback lists.

**Fix**:
```python
# WRONG - Legacy API
litellm.callbacks = [callback_instance]

# CORRECT - Modern API (LiteLLM 1.72+)
if not hasattr(litellm, 'success_callback') or litellm.success_callback is None:
    litellm.success_callback = []
litellm.success_callback.append(callback_instance)

if not hasattr(litellm, 'failure_callback') or litellm.failure_callback is None:
    litellm.failure_callback = []
litellm.failure_callback.append(callback_instance)
```

**Key Pattern**: Always APPEND to preserve existing callbacks (e.g., DeepInfra fixes).

**Verification**:
```python
# In startup logs, look for:
logger.info("✅ LiteLLM tracking callback installed")

# Then check callback is invoked:
# Should see log_success_event() calls in logs
```

---

## Grafana Pie Chart Field Naming

**Problem**: Pie chart only shows one category despite query returning multiple.

**Root Cause**: Grafana expects specific field names for pie chart data.

**Fix**:
```sql
-- WRONG - Generic names
SELECT flow_type, COUNT(*) AS count
FROM table GROUP BY flow_type;

-- CORRECT - Grafana-friendly names
SELECT
  flow_type AS metric,      -- Grafana recognizes "metric"
  COUNT(*)::float AS value  -- Grafana recognizes "value"
FROM table
GROUP BY flow_type
ORDER BY value DESC;
```

**Applies to**: Grafana pie chart panels in dashboard JSON.

---

## Multi-Agent Parallel Triage Pattern

**Use Case**: Three unrelated issues need investigation simultaneously.

**Pattern**:
```typescript
// Launch 3 triage agents in parallel
<invoke name="Task">
  <parameter name="subagent_type">issue-triage-coordinator
