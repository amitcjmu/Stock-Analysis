# Bug #801: Questionnaire Status Flow - Root Cause Analysis Pattern

## Problem: Endless Loading Loop Despite Successful Generation
**Symptom**: Frontend shows LoadingStateDisplay indefinitely even though backend successfully generated questions
**Root Cause**: Backend sets `completion_status='pending'` after generation instead of `'ready'`

## Investigation Pattern Used

### 1. Backend Log Analysis
```bash
# Check if generation actually succeeded
docker logs migration_backend --tail 100 --follow | grep -i questionnaire

# Key evidence found:
# "Successfully generated 12 questions for flow b3412c2b..."
# "Updated questionnaire 69a8f794-b29c-422f-b82a-71ae98027729 status to pending"
```

### 2. Database State Verification
```bash
# Find correct table name first
docker exec migration_postgres psql -U postgres -d migration_db -c "\dt migration.*" | grep questionnaire

# Query questionnaire state
docker exec migration_postgres psql -U postgres -d migration_db -c "
SELECT id, collection_flow_id, completion_status,
       jsonb_array_length(questions) as question_count,
       created_at, updated_at
FROM migration.adaptive_questionnaires
WHERE id = '69a8f794-b29c-422f-b82a-71ae98027729';
"

# Result showed: completion_status='pending', question_count=12
# This confirmed backend set wrong status despite having questions
```

### 3. Cross-Reference Flow IDs
```bash
# Collection flows use two-column pattern: id (PK) vs flow_id (business key)
docker exec migration_postgres psql -U postgres -d migration_db -c "
SELECT id, flow_id FROM migration.collection_flows
WHERE flow_id = 'b3412c2b-ad0f-4990-9773-f7a65003878b';
"

# Result: id=49869bf1 (FK in questionnaire), flow_id=b3412c2b (user-facing)
```

## Fix Applied

**File**: `backend/app/api/v1/endpoints/collection_crud_questionnaires/commands.py:214`

```python
# BEFORE (Bug):
await _update_questionnaire_status(
    questionnaire_id,
    "pending",  # 🔍 BUG#668: Questionnaire needs user input, not "ready"
    questions,
    db=db,
)

# AFTER (Fixed):
await _update_questionnaire_status(
    questionnaire_id,
    "ready",  # FIX BUG#801: Set to "ready" when questions are generated
    questions,
    db=db,
)
```

## Impact Analysis Process

### Search All Status Dependencies
```python
# Backend search
mcp__serena__search_for_pattern(
    substring_pattern='completion_status.*=.*"pending"',
    relative_path="backend/app"
)

mcp__serena__search_for_pattern(
    substring_pattern='completion_status.*==.*"pending"',
    relative_path="backend/app"
)

# Frontend search
grep -rn "completion_status.*===.*['\"]pending['\"]" src --include="*.ts" --include="*.tsx"
grep -rn "completion_status.*===.*['\"]ready['\"]" src --include="*.ts" --include="*.tsx"
```

### Found One Frontend Update Needed
**File**: `src/hooks/collection/adaptive-form/useSubmitHandler.ts:267`

```typescript
// Multi-questionnaire workflow - find next incomplete questionnaire
const nextQuestionnaire = updatedQuestionnaires.find(
  (q) =>
    q.completion_status === "ready" ||  // Added for backend fix compatibility
    q.completion_status === "pending" ||
    q.completion_status === "in_progress",
) || updatedQuestionnaires[0];
```

## Correct Status Flow

```
1. 'pending'   → Questionnaire record created (before generation)
2. 'ready'     → Questions generated, awaiting user input ✅ Fix
3. 'completed' → User submitted responses
```

**Not**:
```
❌ 'pending' when questions exist and awaiting user input (old bug)
```

## Key Learnings

1. **Frontend validation was CORRECT**: Checking `status=='ready' AND questions.length > 0` prevented blank forms
2. **Backend logs + database state** = definitive proof (not assumptions)
3. **Status semantics matter**: "pending" = backend processing, "ready" = user action needed
4. **Always check impact**: One backend change required one frontend compatibility update

## When to Apply This Pattern

- Frontend shows correct loading state but never transitions
- Backend logs show success but frontend doesn't reflect it
- Suspected status/state mismatch between frontend and backend
- Need to verify generation actually completed vs. stuck

## Related Files
- `backend/app/api/v1/endpoints/collection_crud_questionnaires/commands.py`
- `backend/app/api/v1/endpoints/collection_serializers/core.py` (status_line generation)
- `src/hooks/collection/useQuestionnairePolling.ts` (polling + validation logic)
- `src/hooks/collection/adaptive-form/useSubmitHandler.ts` (multi-questionnaire workflows)
