# Assessment ↔ Collection Flow Readiness Transition Patterns

## Overview

This memory documents the complete flow of how assets transition between "not ready" and "ready" states across Assessment and Collection flows. Critical for debugging readiness issues.

## The User Journey

```
1. User starts "New Assessment" from Assessment Flow
   ↓
2. Modal shows assets grouped by readiness:
   - "Ready for Assessment" bucket (assessment_readiness='ready')
   - "Needs Data Collection" bucket (assessment_readiness='not_ready')
   ↓
3. User clicks "Refresh Readiness" link → Calls readiness_gaps endpoint
   ↓
4. For "not ready" assets, user starts Collection Flow
   ↓
5. IntelligentGapScanner finds TRUE gaps → Generates questionnaires
   ↓
6. User completes questionnaires
   ↓
7. Asset should transition to "ready" for assessment
```

## Two Readiness Tracking Systems

### 1. Collection Flow Level
- **Field**: `collection_flows.assessment_ready` (Boolean)
- **Set by**: `check_and_set_assessment_ready()` in `assessment_validation.py`
- **Criteria**: All selected assets have required attributes (business_criticality, environment) AND all questionnaires completed

### 2. Asset Level (THE MAIN ONE)
- **Fields**: `assets.assessment_readiness` AND `assets.sixr_ready`
- **Values**: `'ready'` or `'not_ready'`
- **Used by**: Start New Assessment modal to bucket assets
- **Set by**: Multiple places (see below)

## Where Asset Readiness Gets Updated

### 1. Questionnaire Submission (`questionnaire_submission.py`)
```python
# After user completes questionnaire with save_type='submit_complete'
await _update_asset_readiness(asset_ids_to_reanalyze, request_data, context, db)
# Sets assessment_readiness='ready' and sixr_ready='ready'

# CRITICAL: Must commit after since _update_asset_readiness stages but doesn't commit
if readiness_updated:
    await db.commit()
```

### 2. Assessment Validation (`assessment_validation.py`)
```python
# When collection flow becomes assessment_ready=True
await db.execute(
    update(Asset)
    .where(Asset.id.in_(asset_uuids), ...)
    .values(assessment_readiness="ready", sixr_ready="ready")
)
```

### 3. Background Task (`background_task.py`)
```python
# When IntelligentGapScanner finds NO TRUE gaps
# Asset is complete → No questionnaire needed → Mark ready immediately
asset.assessment_readiness = "ready"
asset.sixr_ready = "ready"
```

### 4. Refresh Readiness Button (`readiness_gaps.py`)
```python
# Called from Start New Assessment modal
# Checks questionnaire completion FIRST, then runs GapAnalyzer
if asset.id in assets_ready_by_questionnaire:
    is_ready = True  # Override GapAnalyzer
else:
    readiness_result = await readiness_service.analyze_asset_readiness(...)
    is_ready = readiness_result.is_ready_for_assessment

asset.assessment_readiness = "ready" if is_ready else "not_ready"
asset.sixr_ready = "ready" if is_ready else "not_ready"
```

## Common Bug Pattern: Asset Stays "Not Ready"

### Symptom
User completes questionnaire, but asset still shows in "Needs Data Collection" bucket.

### Root Causes (in order of likelihood)

1. **Missing Commit After Readiness Update**
   - `_update_asset_readiness()` stages but doesn't commit
   - Fix: Add explicit `await db.commit()` after the call

2. **GapAnalyzer vs IntelligentGapScanner Mismatch**
   - IntelligentGapScanner found data in source X (e.g., canonical_apps)
   - GapAnalyzer doesn't check source X → Reports gap
   - Fix: Check questionnaire completion BEFORE running GapAnalyzer

3. **Questionnaire Not Marked Completed**
   - `save_type='save_progress'` vs `save_type='submit_complete'`
   - Only `submit_complete` triggers readiness update
   - Fix: Ensure frontend sends correct save_type

4. **"No TRUE Gaps" Case Not Handled**
   - Questionnaire fails with "No questionnaires could be generated"
   - This is GOOD - asset has complete data
   - Must mark asset as ready, not leave in not_ready state

## Questionnaire Completion States

| Status | Meaning | Asset Readiness |
|--------|---------|-----------------|
| `pending` | Not started | `not_ready` |
| `ready` | Generated, awaiting user | `not_ready` |
| `in_progress` | User saving progress | `not_ready` |
| `completed` | User submitted | `ready` |
| `failed` + "No questionnaires" | No TRUE gaps found | `ready` ← Often missed! |
| `failed` + other error | Genuine failure | `not_ready` |

## Debug Queries

```sql
-- Check asset readiness status
SELECT id, name, assessment_readiness, sixr_ready
FROM migration.assets
WHERE canonical_application_id = '<uuid>';

-- Check questionnaire status for assets
SELECT aq.asset_id, aq.completion_status, aq.description,
       a.assessment_readiness
FROM migration.adaptive_questionnaires aq
JOIN migration.assets a ON aq.asset_id = a.id
WHERE aq.collection_flow_id = <flow_id>;

-- Find assets stuck in not_ready despite completed questionnaires
SELECT a.id, a.name, a.assessment_readiness, aq.completion_status
FROM migration.assets a
JOIN migration.adaptive_questionnaires aq ON aq.asset_id = a.id
WHERE aq.completion_status = 'completed'
AND a.assessment_readiness = 'not_ready';
```

## Key Files

| File | Purpose |
|------|---------|
| `readiness_gaps.py` | "Refresh Readiness" button endpoint |
| `questionnaire_submission.py` | Handles questionnaire submit |
| `questionnaire_helpers.py` | `_update_asset_readiness()` function |
| `assessment_validation.py` | `check_and_set_assessment_ready()` |
| `background_task.py` | Questionnaire generation background job |
| `asset_readiness_service.py` | Wrapper around GapAnalyzer |

## Fix Checklist

When debugging "asset won't transition to ready":

1. ☐ Check `assets.assessment_readiness` value in DB
2. ☐ Check `adaptive_questionnaires.completion_status` for this asset
3. ☐ If questionnaire is `completed`, check if commit happened after update
4. ☐ If questionnaire `failed`, check description for "No questionnaires"
5. ☐ Use "Refresh Readiness" button to force re-evaluation
6. ☐ Check backend logs for `_update_asset_readiness` execution
