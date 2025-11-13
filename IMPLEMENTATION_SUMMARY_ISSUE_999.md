# Implementation Summary: Assessment Flow Zombie Recovery (Issue #999)

## Overview

This implementation adds a comprehensive recovery mechanism for "zombie" assessment flows - flows stuck at high completion percentages with empty results due to background tasks never executing.

## Problem Analysis

### Symptoms
- Assessment flows show 100% progress
- `phase_results` dictionary is empty: `{}`
- `agent_insights` array is empty: `[]`
- Asset table has no 6R recommendations: `six_r_strategy: NULL`
- No `[ISSUE-999]` log entries indicating background task execution

### Root Cause
The original fix (PR #1001) correctly added background task queueing in resume endpoints. However, flows created BEFORE this fix never had their resume endpoints called, leaving them permanently stuck as zombies.

## Solution Architecture

### Two-Layer Recovery System

#### 1. Manual Recovery Endpoint
**File**: `/backend/app/api/v1/endpoints/assessment_flow/recovery.py` (NEW)

**Endpoint**: `POST /api/v1/assessment-flow/{flow_id}/recover`

**Features**:
- Detects zombie flows using three criteria:
  - Progress >= 80%
  - Empty phase_results
  - Empty agent_insights
- Queues background task to re-execute agents for current phase
- Returns detailed status including zombie detection results
- Safe to call multiple times (idempotent)

**Key Functions**:
- `is_zombie_flow()`: Core detection logic
- `recover_stuck_assessment_flow()`: Main recovery endpoint

#### 2. Automatic Recovery on Resume
**File**: `/backend/app/api/v1/master_flows/assessment/lifecycle_endpoints.py` (MODIFIED)

**Location**: Lines 96-117 in `resume_assessment_flow_via_mfo()`

**Features**:
- Transparent zombie detection before resuming any flow
- Auto-queues recovery if zombie detected
- No frontend changes required
- Logs warnings with `[ISSUE-999-ZOMBIE]` prefix

## Files Modified

### New Files
1. **recovery.py** (230 lines)
   - Recovery endpoint implementation
   - Zombie detection logic
   - Background task queueing

2. **ASSESSMENT_FLOW_RECOVERY.md** (Documentation)
   - Comprehensive recovery mechanism documentation
   - Testing procedures
   - Monitoring guidelines

3. **test_assessment_flow_recovery.py** (Manual test script)
   - Test harness for both recovery mechanisms
   - Database state verification
   - End-to-end recovery testing

### Modified Files
1. **lifecycle_endpoints.py**
   - Added zombie detection logic (lines 96-117)
   - Logs auto-recovery warnings

2. **assessment_flow_router.py**
   - Registered recovery router
   - Updated initialization log message

## Implementation Details

### Zombie Detection Criteria
```python
is_zombie = (
    progress >= 80 and
    (not phase_results or phase_results == {}) and
    (not agent_insights or agent_insights == [])
)
```

### Recovery Process Flow
1. **Detection**: Identify zombie using three criteria
2. **Validation**: Parse current phase to AssessmentPhase enum
3. **Queue Task**: Add `continue_assessment_flow()` to background tasks
4. **Agent Execution**: Background task runs CrewAI agents
5. **Store Results**: Populate phase_results, agent_insights, 6R recommendations
6. **Frontend Refresh**: Next poll shows populated data

### Multi-Tenant Security
- Uses `RequestContext` for client_account_id and engagement_id
- All database queries properly scoped
- Audit trail via user_id parameter

### Error Handling
- Graceful degradation if flow not found
- Validation of UUID formats
- Invalid phase detection
- Comprehensive logging with issue tags

## Verification

### Pre-commit Checks
All files pass pre-commit validation:
- ✅ recovery.py: All checks passed
- ✅ lifecycle_endpoints.py: All checks passed (after black formatting)
- ✅ assessment_flow_router.py: All checks passed

### Syntax Validation
- ✅ recovery.py: Python syntax OK
- ✅ lifecycle_endpoints.py: Python syntax OK

### Import Validation
- ✅ Recovery router imports successfully in backend container
- ✅ Lifecycle endpoints import successfully in backend container

## Testing

### Manual Testing Script
**Location**: `backend/tests/manual/test_assessment_flow_recovery.py`

**Tests**:
1. Manual recovery via `/recover` endpoint
2. Automatic recovery on resume
3. Database state verification
4. Log pattern validation

### Test Flow ID
- **Zombie Flow**: `8bdaa388-75a7-4059-81f6-d29af2037538`
- **Status**: 100% progress, empty results
- **Phase**: recommendation_generation

### Expected Log Patterns
```
[ISSUE-999-RECOVERY] 🧟 ZOMBIE FLOW DETECTED: <flow_id> at 100% with EMPTY results
[ISSUE-999-RECOVERY] ✅ Recovery task queued for zombie flow <flow_id>
[ISSUE-999] 🚀 BACKGROUND TASK STARTED: Assessment flow agent execution
[ISSUE-999] ✅ BACKGROUND TASK COMPLETED: Assessment flow completed successfully
```

## API Reference

### Manual Recovery Endpoint

**Request**:
```bash
POST /api/v1/assessment-flow/{flow_id}/recover
Authorization: Bearer <token>
```

**Response (Zombie Detected)**:
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

**Response (Not Zombie)**:
```json
{
  "message": "Flow does not appear to be stuck",
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

## Safety Features

1. **No Direct State Mutations**: Recovery only queues tasks, doesn't modify flow state
2. **Idempotent**: Safe to call multiple times
3. **Tenant Isolated**: Multi-tenant security via RequestContext
4. **Audit Trail**: Comprehensive logging with issue tags
5. **Graceful Degradation**: Errors don't worsen flow state

## Monitoring

### Key Metrics
- **Zombie Detection Rate**: Percentage of flows flagged as zombies
- **Recovery Success Rate**: Percentage of successful recoveries
- **Time to Recovery**: Duration from detection to completion
- **False Positives**: Non-zombie flows incorrectly flagged

### Log Monitoring Commands
```bash
# Monitor recovery attempts
docker logs migration_backend -f | grep "ISSUE-999-RECOVERY"

# Monitor auto-recovery on resume
docker logs migration_backend -f | grep "ISSUE-999-ZOMBIE"

# Monitor background task execution
docker logs migration_backend -f | grep "ISSUE-999"
```

## Database Verification

### Check Flow State
```sql
SELECT
  id,
  progress,
  current_phase,
  jsonb_array_length(agent_insights) as insight_count,
  jsonb_object_keys(phase_results) as phase_keys
FROM migration.assessment_flows
WHERE id = '8bdaa388-75a7-4059-81f6-d29af2037538';
```

### Check 6R Recommendations
```sql
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

## Deployment Checklist

- [x] Create recovery endpoint (recovery.py)
- [x] Add zombie detection to resume endpoint (lifecycle_endpoints.py)
- [x] Register recovery router (assessment_flow_router.py)
- [x] Pass all pre-commit checks
- [x] Verify syntax and imports
- [x] Create comprehensive documentation
- [x] Create manual test script
- [x] Backend container running and stable
- [ ] Test with actual zombie flow (requires authentication)
- [ ] Monitor logs for successful recovery
- [ ] Verify results in database
- [ ] Update frontend (optional - recovery works without changes)

## Future Enhancements

1. **Batch Recovery**: Endpoint to recover all zombie flows at once
2. **Smart Phase Detection**: Auto-detect which phase needs recovery
3. **Partial Recovery**: Only re-execute failed phases
4. **Proactive Monitoring**: Background job to detect zombies
5. **Recovery History**: Track attempts in database
6. **Frontend Integration**: Add "Recover" button to flow details page

## References

- **GitHub Issue**: #999 - Assessment flow zombie flows
- **Original Fix**: PR #1001 - Background task queueing
- **Related Documentation**:
  - `/docs/guidelines/ASSESSMENT_FLOW_RECOVERY.md`
  - `/backend/tests/manual/test_assessment_flow_recovery.py`
- **Code Files**:
  - `/backend/app/api/v1/endpoints/assessment_flow/recovery.py`
  - `/backend/app/api/v1/master_flows/assessment/lifecycle_endpoints.py`
  - `/backend/app/api/v1/endpoints/assessment_flow_router.py`

## Success Criteria

✅ **Completed**:
1. Manual recovery endpoint implemented
2. Automatic recovery on resume implemented
3. All pre-commit checks pass
4. Comprehensive documentation created
5. Test script provided
6. Backend stable and running

⏳ **Pending User Action**:
1. Test recovery with actual zombie flow
2. Verify database results after recovery
3. Monitor production logs
4. Optional: Add frontend "Recover" button

## Notes

- Recovery mechanism is **backward compatible** - works with existing flows
- **No database migrations required** - uses existing columns
- **No frontend changes required** - recovery is transparent
- Safe to deploy immediately - no breaking changes
- Recovery is idempotent - safe to retry on failure
