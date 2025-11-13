# Bug #668: Collection-Assessment Circular Loop Fix

## Problem
Assessment flows → Collection flows → immediate auto-completion → back to Assessment (infinite loop)

## Root Cause
Questionnaires created with `completion_status="ready"` treated as completed by frontend, triggering automatic transition back to assessment.

## Solution
Change questionnaire initial status from "ready" to "pending" to require user input.

### Code Fix
**File**: `backend/app/api/v1/endpoints/collection_crud_questionnaires/commands.py`

```python
# Line 214 - BEFORE (Broken)
await _update_questionnaire_status(
    questionnaire_id,
    "ready",  # Frontend expects "ready"
    questions,
    db=db,
)

# Line 214 - AFTER (Fixed)
await _update_questionnaire_status(
    questionnaire_id,
    "pending",  # 🔍 BUG#668: Questionnaire needs user input, not "ready"
    questions,
    db=db,
)
```

### Questionnaire Lifecycle States
- `"pending"` → Awaiting user input (form displays, no auto-transition)
- `"completed"` → User submitted form (can transition to assessment)
- ~~`"ready"`~~ → WRONG, causes circular loop

### Verification Query
```sql
SELECT id, completion_status, questions
FROM migration.adaptive_questionnaires
WHERE collection_flow_id = 'flow_uuid';
-- Should show completion_status='pending' for newly generated questionnaires
```

## Impact
Fixes infinite loop, allows users to actually fill out questionnaires before assessment transition.
