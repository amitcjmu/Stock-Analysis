# Issue #980: Quick Reference - Database Data Flow Disconnect

## The Problem in 30 Seconds

**What's broken:** Questionnaire responses are saved to database, but Asset fields never get updated.

**Root cause:** The `resolved_value` field in `collection_data_gaps` table is EMPTY, even when gaps are marked as "resolved".

**Impact:** Users collect data, but readiness scores stay at 0% and Asset records remain incomplete.

---

## The Missing Link

```python
# Current code (BROKEN):
# File: backend/app/api/v1/endpoints/collection_crud_helpers.py:296

gap.resolution_status = "resolved"
gap.resolved_at = datetime.utcnow()
gap.resolved_by = "manual_submission"
# ❌ MISSING LINE: gap.resolved_value = ...

# Fixed code:
gap.resolution_status = "resolved"
gap.resolved_at = datetime.utcnow()
gap.resolved_by = "manual_submission"
gap.resolved_value = json.dumps(value.get("value", value)) if isinstance(value, dict) else str(value)  # ✅ ADD THIS
```

---

## Data Flow Diagram

```
┌──────────────────────────────────────────────┐
│ 1. User Submits Questionnaire Response      │
│    "What OS?" → "Linux"                      │
└────────────────┬─────────────────────────────┘
                 ↓
┌──────────────────────────────────────────────┐
│ 2. Saved to collection_questionnaire_        │
│    responses                                 │
│    ✅ response_value = {"value": "Linux"}    │
└────────────────┬─────────────────────────────┘
                 ↓
┌──────────────────────────────────────────────┐
│ 3. resolve_data_gaps() marks gap as resolved │
│    ✅ resolution_status = 'resolved'         │
│    ❌ resolved_value = '' (EMPTY!)           │ ← PROBLEM HERE
└────────────────┬─────────────────────────────┘
                 ↓
┌──────────────────────────────────────────────┐
│ 4. apply_asset_writeback() tries to update  │
│    Asset fields                              │
│    ❌ field_updates = {} (empty dict)        │ ← NO DATA TO WRITE
│    ❌ Assets not updated                     │
└────────────────┬─────────────────────────────┘
                 ↓
┌──────────────────────────────────────────────┐
│ 5. Asset remains incomplete                  │
│    ❌ operating_system = NULL                │
│    ❌ assessment_readiness_score = 0%        │
└──────────────────────────────────────────────┘
```

---

## SQL Proof of Problem

### Check Responses (Data IS Saved)

```sql
SELECT
    question_id,
    response_value::text,
    created_at
FROM migration.collection_questionnaire_responses
ORDER BY created_at DESC
LIMIT 3;
```

**Result:**
```
question_id     | response_value                 | created_at
----------------+--------------------------------+---------------------------
technology_stack| {"value": ["python"]}          | 2025-11-09 18:21:06
architecture_pattern | {"value": "microservices"}| 2025-11-09 18:21:06
business_owner  | {"value": ["executive_c_level"]}| 2025-11-09 18:21:06
```
✅ **Data IS being saved**

### Check Gaps (Value NOT Copied)

```sql
SELECT
    field_name,
    resolution_status,
    LENGTH(COALESCE(resolved_value, '')) AS value_length
FROM migration.collection_data_gaps
WHERE resolution_status = 'resolved'
ORDER BY updated_at DESC
LIMIT 3;
```

**Result:**
```
field_name          | resolution_status | value_length
--------------------+-------------------+-------------
technology_stack    | resolved          | 0
architecture_pattern| resolved          | 0
business_owner      | resolved          | 0
```
❌ **resolved_value is EMPTY (length = 0)**

### Check Assets (Never Updated)

```sql
SELECT
    name,
    operating_system,
    business_criticality,
    assessment_readiness_score
FROM migration.assets
WHERE id = '778f9a98-1ed9-4acd-8804-bdcec659ac00';
```

**Result:**
```
name              | operating_system | business_criticality | assessment_readiness_score
------------------+------------------+----------------------+---------------------------
Analytics Engine  | NULL             | Low                  | 0.4
```
❌ **Asset fields remain NULL**

---

## The Fix (3 Lines of Code)

**File:** `/Users/chocka/CursorProjects/migrate-ui-orchestrator/backend/app/api/v1/endpoints/collection_crud_helpers.py`

**Line:** 296

**Before:**
```python
if gap:
    gap.resolution_status = "resolved"
    gap.resolved_at = datetime.utcnow()
    gap.resolved_by = "manual_submission"
    gaps_resolved += 1
```

**After:**
```python
if gap:
    gap.resolution_status = "resolved"
    gap.resolved_at = datetime.utcnow()
    gap.resolved_by = "manual_submission"

    # ✅ FIX: Populate resolved_value with response data
    if isinstance(value, dict):
        # Extract "value" key from {"value": "Linux"} format
        gap.resolved_value = json.dumps(value.get("value", value))
    elif isinstance(value, list):
        gap.resolved_value = json.dumps(value)
    else:
        gap.resolved_value = str(value)

    gaps_resolved += 1
```

**Import needed:**
```python
import json  # Add to top of file if not already present
```

---

## Manual Data Repair (Run After Fix)

```sql
-- Backfill resolved_value for already-resolved gaps
UPDATE migration.collection_data_gaps g
SET
    resolved_value = r.response_value::text,
    updated_at = NOW()
FROM migration.collection_questionnaire_responses r
WHERE r.gap_id = g.id
AND g.resolution_status = 'resolved'
AND (g.resolved_value IS NULL OR g.resolved_value = '')
AND r.response_value IS NOT NULL;

-- Verify repair
SELECT COUNT(*) AS gaps_repaired
FROM migration.collection_data_gaps
WHERE resolution_status = 'resolved'
AND resolved_value IS NOT NULL
AND resolved_value != '';
```

---

## Testing the Fix

### 1. Apply Code Fix

```bash
# Edit the file
vim backend/app/api/v1/endpoints/collection_crud_helpers.py

# Add the 6 lines shown above at line 296
```

### 2. Restart Backend

```bash
docker-compose restart migration_backend
docker logs -f migration_backend
```

### 3. Test Questionnaire Submission

1. Navigate to Collection Flow UI
2. Submit a questionnaire response (e.g., "Operating System" → "Linux")
3. Check database:

```sql
-- Verify resolved_value is now populated
SELECT
    field_name,
    resolution_status,
    resolved_value,
    updated_at
FROM migration.collection_data_gaps
WHERE resolution_status = 'resolved'
ORDER BY updated_at DESC
LIMIT 1;
```

**Expected Result:**
```
field_name       | resolution_status | resolved_value | updated_at
-----------------+-------------------+----------------+---------------------------
operating_system | resolved          | "Linux"        | 2025-11-09 20:00:00
```
✅ **resolved_value now has data!**

### 4. Verify Asset Update

```sql
-- Check if Asset was updated
SELECT
    name,
    operating_system,
    assessment_readiness_score,
    updated_at
FROM migration.assets
WHERE id = '<your-asset-id>'
ORDER BY updated_at DESC;
```

**Expected Result:**
```
name              | operating_system | assessment_readiness_score | updated_at
------------------+------------------+----------------------------+---------------------------
Analytics Engine  | Linux            | 0.6                        | 2025-11-09 20:00:01
```
✅ **Asset field updated!**
✅ **Readiness score improved!**

---

## Files Involved

| File | Purpose | Change Needed |
|------|---------|---------------|
| `backend/app/api/v1/endpoints/collection_crud_helpers.py:296` | Gap resolution | ✅ Add `gap.resolved_value = ...` |
| `backend/app/services/flow_configs/collection_handlers/asset_handlers.py:158-174` | Asset writeback | ℹ️ Already queries responses, should work after fix |
| `backend/app/api/v1/endpoints/collection_crud_update_commands/questionnaire_submission.py:220` | Submission handler | ℹ️ Calls fixed function, no change needed |

---

## Architecture Context

### Database Tables

```
collection_questionnaire_responses
├── response_value JSONB  ← Data IS saved here ✅
├── gap_id FK
└── asset_id FK

collection_data_gaps
├── field_name
├── resolution_status
└── resolved_value TEXT  ← Data NOT saved here ❌ (THE BUG)

assets
├── operating_system     ← Should be updated from gaps
├── business_criticality
└── assessment_readiness_score
```

### Data Flow

```
User Input
    ↓
response_value (JSONB)          ← ✅ Saved
    ↓
resolved_value (TEXT)           ← ❌ NOT copied (BUG)
    ↓
Asset fields (VARCHAR/INT)      ← ❌ Not updated
```

---

## References

- **Full Analysis:** `/docs/analysis/ISSUE_980_DATABASE_ARCHITECTURE_GAP_ANALYSIS.md`
- **Issue:** #980 - Intelligent Gap Detection Data Flow
- **Related ADR:** ADR-012 (Flow Status Management Separation)
- **Related Service:** `AssetReadinessService` (backend/app/services/assessment/asset_readiness_service.py)

---

**Last Updated:** 2025-11-09
**Severity:** HIGH - Core feature broken
**Effort:** 2 hours (code fix + testing)
