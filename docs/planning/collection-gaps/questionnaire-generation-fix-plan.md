# Collection Flow Questionnaire Generation Fix - Implementation Plan

## Problem Summary
The collection flow is bypassing questionnaire generation after asset selection, jumping directly to completion instead of generating questionnaires to address identified data gaps. Additionally, gap analysis is not asset-type aware, using only application-centric attributes.

## Root Causes
1. **Questionnaire Skip Logic**: `should_skip_detailed_questionnaire()` returns `true` for TIER_1 flows with "detailed" questionnaire type
2. **Asset-Type Limitation**: Gap analysis uses fixed "critical attributes framework" focused only on applications

## Solution Overview
Implement smart questionnaire skip logic and agent-first generation with proper persistence, tenant isolation, and asset-type awareness.

## Implementation Details

### 1. Fix Skip Logic (`questionnaire_utilities.py`)
```python
def should_skip_detailed_questionnaire(state, questionnaire_type):
    # Never skip if gaps exist
    # TIER_1 always needs questionnaires
    # TIER_3 can skip only with no gaps AND feature flag
```

**Key Changes:**
- Add comprehensive audit logging
- Check gap count from `state.gap_analysis_results`
- Use feature flag `collection.gaps.skip_tier3_no_gaps`
- Log all decisions with flow_id and reason

### 2. Update Questionnaire Endpoint (`collection_crud_questionnaires.py`)

**Replace current `get_adaptive_questionnaires` function:**
- Add tenant-scoped queries (include `client_account_id` and `engagement_id`)
- Create `_start_agent_generation` to insert pending records
- Implement `_background_generate` with fresh AsyncSession
- Return List[AdaptiveQuestionnaireResponse] to maintain compatibility

**Critical Safety Features:**
- Set tenant fields on insert
- Guard all updates with tenant WHERE clauses
- Check rowcount > 0 before commit
- Use `asyncio.wait_for` (Python 3.10 compatible)

**Required Imports:**
```python
from uuid import uuid4
from sqlalchemy import update
import asyncio
```

### 3. Enhance Serializer (`collection_serializers.py`)

**Update `build_questionnaire_response`:**
- Include `completion_status` field
- Add optional `status_line` for UI display
- Calculate estimated time for pending states

### 4. Feature Flags Enhancement (`feature_flags.py`)

**Add without breaking existing behavior:**
- Environment variable override capability
- `log_feature_flags()` function for startup
- Keep `PERMANENT_FEATURES` intact

**Feature Flags:**
- `collection.gaps.v2_agent_questionnaires` (default: true)
- `collection.gaps.bootstrap_fallback` (default: true)
- `collection.gaps.skip_tier3_no_gaps` (default: false)

### 5. Frontend Polling Update

**Update React Query in questionnaire component:**
```typescript
refetchInterval: (data) => {
    if (data?.[0]?.completion_status === 'pending') return 5000;
    return false; // Stop on ready/fallback/failed
}
```

**Render based on `completion_status`:**
- "pending" → Show loader with estimated time
- "ready" → Display questionnaire
- "fallback" → Show bootstrap with alert
- "failed" → Show error state

### 6. Asset-Type Awareness (Future Enhancement)

While not immediately required for the skip logic fix, the plan includes provisions for:
- Using `Asset.asset_type` from database as primary source
- Config-driven overlay loader for critical attributes
- Tenant-specific overrides for attribute frameworks

## State Flow

```
1. User selects asset
2. Gap analysis runs → identifies gaps
3. Questionnaire generation:
   - If gaps exist → Never skip
   - If TIER_1 → Never skip
   - If TIER_3 + no gaps + flag → Skip
   - Otherwise → Generate
4. If generating:
   - Create pending record (with tenant fields)
   - Start background task
   - Return pending response
   - Frontend polls
5. Background task:
   - Use fresh AsyncSession
   - Generate with 30s timeout
   - Update to ready/fallback/failed (with tenant guards)
   - Check rowcount
6. Frontend:
   - Polls while pending
   - Displays result when ready
```

## Database Considerations

**No migrations needed** - Reuse existing:
- `AdaptiveQuestionnaire.completion_status` for states
- Model already has `client_account_id` and `engagement_id`

**Completion Status Values:**
- "pending" - Agent is generating
- "ready" - Questions populated (formerly "completed")
- "fallback" - Using bootstrap
- "failed" - Generation failed

## Testing Checklist

- [ ] TIER_1 with gaps → generates questionnaires (not skipped)
- [ ] TIER_3 with no gaps + flag enabled → skips correctly
- [ ] Pending → Ready lifecycle works with polling
- [ ] Tenant isolation prevents cross-tenant access
- [ ] Bootstrap fallback triggers on timeout when flag enabled
- [ ] Audit logs capture all decisions
- [ ] Frontend displays correct state for each completion_status

## Files to Modify

1. `backend/app/services/crewai_flows/unified_collection_flow_modules/phase_handlers/questionnaire_utilities.py`
2. `backend/app/api/v1/endpoints/collection_crud_questionnaires.py`
3. `backend/app/api/v1/endpoints/collection_serializers.py`
4. `backend/app/core/feature_flags.py`
5. `backend/app/main.py` (add startup logging)
6. Frontend questionnaire component (check `completion_status`)

## Observability

**Events to emit:**
- `questionnaire_generation_started`
- `questionnaire_generation_ready`
- `questionnaire_generation_fallback`
- `questionnaire_generation_failed`

**Logs to capture:**
- Skip decisions with inputs and reasons
- Pending record creation
- Background task outcomes
- Tenant guard failures (rowcount = 0)

## Rollback Plan

All changes are feature-flag controlled:
- Disable `collection.gaps.v2_agent_questionnaires` to revert to sync generation
- Disable `collection.gaps.skip_tier3_no_gaps` to prevent any skipping
- Frontend gracefully handles all states

## Success Criteria

1. TIER_1 flows generate questionnaires when gaps exist
2. No more direct jump from asset selection to completion
3. Agent-generated questionnaires appear after polling
4. Tenant isolation maintained throughout
5. Audit trail shows clear decision reasoning