# Assessment Flow Recovery Mechanism

**Related: GitHub Issue #999 - Assessment flow zombie flows**

## Problem Statement

Assessment flows can become "zombies" - stuck at 100% completion with empty results. This occurs when:
- Frontend shows progress: 100%
- But `phase_results` is empty: `{}`
- And `agent_insights` is empty: `[]`
- And Asset table has no 6R recommendations: `six_r_strategy: NULL`
- And logs show no `[ISSUE-999]` background task execution

## Root Cause

The original fix (PR #1001) correctly added background task queueing in the resume endpoint. However, flows created BEFORE this fix never had their resume endpoints called, leaving them permanently stuck as zombies.

## Solution: Two-Layer Recovery System

### 1. Manual Recovery Endpoint

**Purpose**: Allow users to manually trigger recovery for stuck flows.

**Endpoint**: `POST /api/v1/assessment-flow/{flow_id}/recover`

**Request**: No body required

**Response**:
```json
{
  "message": "Recovery initiated for stuck assessment flow",
  "flow_id": "8bdaa388-75a7-4059-81f6-d29af2037538",
  "progress": 100,
  "current_phase": "recommendation_generation",
  "recovery_queued": true,
  "zombie_detected": true,
  "recovery_action": "Re-executing agents for recommendation_generation phase"
}
```

**When NOT a Zombie**:
```json
{
  "message": "Flow does not appear to be stuck (zombie detection failed)",
  "flow_id": "flow-uuid",
  "progress": 45,
  "phase_results_count": 3,
  "agent_insights_count": 5,
  "recovery_needed": false,
  "zombie_criteria": {
    "progress_threshold": 80,
    "requires_empty_results": true,
    "requires_empty_insights": true
  }
}
```

### 2. Automatic Recovery on Resume

**Purpose**: Transparently recover zombie flows when users resume them.

**Location**: `/backend/app/api/v1/master_flows/assessment/lifecycle_endpoints.py`

**Mechanism**:
- Every `POST /{flow_id}/assessment/resume` call checks for zombie status BEFORE resuming
- If zombie detected, logs warning and forces agent re-execution
- No database state changes, just queues background task
- Transparent to frontend - works seamlessly

**Log Pattern**:
```
[ISSUE-999-ZOMBIE] 🧟 AUTO-RECOVERY: Detected zombie flow 8bdaa388-75a7-4059-81f6-d29af2037538
at 100% with EMPTY results. Current phase: recommendation_generation.
Will force agent re-execution...
```

## Zombie Detection Criteria

A flow is classified as a zombie if ALL conditions are true:
1. **High Completion**: `progress >= 80%` (indicates phase should be done)
2. **Empty Results**: `phase_results == {}` or `None` (no agent output)
3. **No Insights**: `agent_insights == []` or `None` (no analysis stored)

## Recovery Process

When recovery is triggered (manually or automatically):

1. **Detection**: Identify current phase from `assessment_flow.current_phase`
2. **Validation**: Parse phase string to `AssessmentPhase` enum
3. **Queue Task**: Add `continue_assessment_flow()` to background tasks with:
   - `flow_id`: Assessment flow UUID
   - `client_account_id`: Tenant isolation
   - `engagement_id`: Session isolation
   - `phase`: AssessmentPhase enum for current phase
   - `user_id`: Audit trail
4. **Agent Execution**: Background task:
   - Loads master flow and assessment flow from database
   - Initializes ExecutionEngineAssessmentCrews
   - Executes CrewAI agents for the current phase
   - Stores results in `phase_results`, `agent_insights`
   - Updates Asset table with 6R recommendations
5. **Frontend Refresh**: Next poll shows populated data

## Testing the Recovery

### Test with Zombie Flow 8bdaa388

```bash
# Manual recovery via API
curl -X POST http://localhost:8000/api/v1/assessment-flow/8bdaa388-75a7-4059-81f6-d29af2037538/recover \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"

# Check logs for recovery execution
docker logs migration_backend -f | grep "ISSUE-999-RECOVERY"

# Expected log sequence:
# 1. [ISSUE-999-RECOVERY] 🧟 ZOMBIE FLOW DETECTED: 8bdaa388 at 100% with EMPTY results
# 2. [ISSUE-999-RECOVERY] ✅ Recovery task queued for zombie flow 8bdaa388
# 3. [ISSUE-999] 🚀 BACKGROUND TASK STARTED: Assessment flow agent execution
# 4. [ISSUE-999] ✅ BACKGROUND TASK COMPLETED: Assessment flow 8bdaa388 phase recommendation_generation completed successfully
```

### Verify Results in Database

```sql
-- Check flow state after recovery
SELECT
  id,
  progress,
  current_phase,
  jsonb_array_length(agent_insights) as insight_count,
  jsonb_object_keys(phase_results) as phase_keys
FROM migration.assessment_flows
WHERE id = '8bdaa388-75a7-4059-81f6-d29af2037538';

-- Check if 6R recommendations were populated
SELECT
  id,
  name,
  six_r_strategy,
  confidence_score
FROM migration.assets
WHERE id IN (
  SELECT unnest(selected_application_ids)::uuid
  FROM migration.assessment_flows
  WHERE id = '8bdaa388-75a7-4059-81f6-d29af2037538'
);
```

## Frontend Integration

No frontend changes required! The recovery mechanism is transparent:

1. **Automatic Recovery**: When users click "Resume" on a zombie flow, recovery happens automatically
2. **Manual Recovery**: Frontend can add a "Recover" button that calls the `/recover` endpoint
3. **Progress Polling**: Existing progress polling will show updated results after agents complete

## Safety Features

- **No Database Mutations**: Recovery only queues tasks, doesn't modify flow state directly
- **Idempotent**: Safe to call recovery multiple times (agents will re-execute)
- **Tenant Isolated**: Uses RequestContext for multi-tenant security
- **Audit Trail**: All recovery attempts logged with `[ISSUE-999-RECOVERY]` prefix
- **Graceful Degradation**: If recovery fails, flow remains in current state (not worse)

## Monitoring

### Key Log Patterns

| Pattern | Meaning |
|---------|---------|
| `[ISSUE-999-RECOVERY] 🧟 ZOMBIE FLOW DETECTED` | Zombie detected in manual endpoint |
| `[ISSUE-999-ZOMBIE] 🧟 AUTO-RECOVERY` | Zombie detected in resume endpoint |
| `[ISSUE-999] 🚀 BACKGROUND TASK STARTED` | Agent execution beginning |
| `[ISSUE-999] ✅ BACKGROUND TASK COMPLETED` | Agents finished successfully |

### Metrics to Track

- **Zombie Detection Rate**: How many flows are zombies at recovery time
- **Recovery Success Rate**: Percentage of recoveries that complete successfully
- **Time to Recovery**: Duration from detection to agent completion
- **False Positives**: Flows flagged as zombies that weren't actually stuck

## Limitations

1. **Phase Identification**: Recovery assumes `current_phase` is accurate
2. **Agent Failures**: If agents fail during recovery, flow enters error state
3. **Partial Results**: If previous phases had partial results, they may be overwritten
4. **Resource Usage**: Recovery queues expensive agent execution (monitor cost)

## Future Improvements

1. **Smart Phase Detection**: Auto-detect which phase has empty results
2. **Partial Recovery**: Only re-execute phases that failed
3. **Batch Recovery**: Endpoint to recover all zombie flows in one call
4. **Proactive Detection**: Background job to detect zombies before users notice
5. **Recovery History**: Track recovery attempts in database for debugging

## References

- **GitHub Issue**: #999 - Assessment flow zombie flows
- **Original Fix**: PR #1001 - Added background task queueing
- **Recovery Implementation**: backend/app/api/v1/endpoints/assessment_flow/recovery.py
- **Auto-Recovery Logic**: backend/app/api/v1/master_flows/assessment/lifecycle_endpoints.py
- **Background Task**: backend/app/api/v1/endpoints/assessment_flow_processors/continuation.py
