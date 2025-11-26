# Session Continuation: Assessment Readiness Bug Fixes - November 25, 2025

## Context for Next Session

This memory provides continuation context for debugging assessment/collection flow readiness issues.

## The Bug Fixed This Session

**Problem**: Assets don't transition to "Ready for Assessment" after questionnaire completion. The "Start New Assessment" modal shows "Ready for Assessment (0)" even after users complete all questionnaires.

**Root Cause**: Mismatch between two gap analysis systems:
1. **IntelligentGapScanner** (questionnaire generation) - Checks 6 data sources
2. **GapAnalyzer** (readiness assessment) - Checks 5 inspectors (different sources)

IntelligentGapScanner could find data in `canonical_applications` or `related_assets`, determine "no TRUE gaps", but GapAnalyzer (used by "Refresh Readiness" button) wouldn't check those sources and report "not ready".

## Fix Applied

**File**: `backend/app/api/v1/canonical_applications/router/readiness_gaps.py`

**Change**: Check questionnaire completion status BEFORE running GapAnalyzer:

```python
# Pre-fetch questionnaire completion status for all assets
assets_ready_by_questionnaire: set[UUID] = set()
for q in questionnaires:
    if q.completion_status == "completed":
        assets_ready_by_questionnaire.add(q.asset_id)
    elif q.completion_status == "failed":
        description = q.description or ""
        if "No questionnaires could be generated" in description:
            assets_ready_by_questionnaire.add(q.asset_id)

# In asset loop - questionnaire completion overrides GapAnalyzer
if asset.id in assets_ready_by_questionnaire:
    is_ready = True  # Trust IntelligentGapScanner's verdict
else:
    readiness_result = await readiness_service.analyze_asset_readiness(...)
    is_ready = readiness_result.is_ready_for_assessment
```

## Other Files Modified This Session

1. **`questionnaire_submission.py`** - Added commit after `_update_asset_readiness()`
2. **`questionnaire_helpers.py`** - `_update_asset_readiness()` sets both `assessment_readiness` and `sixr_ready`
3. **`assessment_validation.py`** - `check_and_set_assessment_ready()` updates asset-level readiness

## Test Data Context

**Tenant**: Canada Life
- 31 assets total
- 1 completed questionnaire
- 4 ready questionnaires
- 20 failed questionnaires (many "No questionnaires could be generated")
- All showing `assessment_readiness = 'not_ready'` in DB

## What Needs Testing

1. Click "Refresh Readiness" in Start New Assessment modal
2. Verify assets with completed questionnaires move to "Ready" bucket
3. Verify assets with "No TRUE gaps" failures also move to "Ready" bucket
4. Verify counts update correctly in modal

## Related Serena Memories

- `gap-analyzer-vs-intelligent-gap-scanner-architecture-2025-11` - Deep dive on the two systems
- `assessment-collection-flow-readiness-transition-patterns-2025-11` - State transition patterns
- `collection-flow-questionnaire-lifecycle-state-machine-2025-11` - Questionnaire states
- `adr-037-implementation-status-2025-11-25` - Per-section generation architecture

## User Preferences (This Session)

- Prefers `docker restart` over `docker-compose build` to save disk space
- Wants code-based fixes, not manual DB updates ("bandaid fixes")
- Values architectural understanding over quick patches
- Requested Serena memories for pattern recognition

## Branch Status

**Branch**: `bugfix/collection-flow-improvements-nov-2025`
**Status**: Uncommitted changes in multiple files
**Base**: `main` (after PR #1126 merge)

## Pickup Prompt for Next Session

```
Continue debugging assessment/collection flow readiness transition.

Previous session fixed: readiness_gaps.py to check questionnaire completion before GapAnalyzer.

Read these Serena memories first:
- gap-analyzer-vs-intelligent-gap-scanner-architecture-2025-11
- assessment-collection-flow-readiness-transition-patterns-2025-11
- session-continuation-assessment-readiness-bugs-2025-11-25

Test needed: Verify "Refresh Readiness" button now correctly marks assets as ready when:
1. They have completed questionnaires
2. They have "failed" questionnaires with "No questionnaires could be generated" (no TRUE gaps)

Use Canada Life tenant for testing.
```
