# Legacy Code Paths for Deprecation

> **Document Created**: 2025-11-19
> **Context**: Collection Flow Questionnaire Generation Bug Fixes (#10)
> **Investigation**: Identified unused code paths while fixing duplicate questions issue

## Executive Summary

During the investigation of Bug #10 (duplicate questions in questionnaires), we discovered that the **actual code path** for collection flow questionnaire generation differs from what we initially thought. This led to fixes being applied to unused/legacy code paths before finding the correct code path.

## Legacy/Unused Code Paths

### 1. `questionnaire_helpers.py` - Not Used in Current Collection Flows

**File**: `backend/app/services/child_flow_services/questionnaire_helpers.py`

**Status**: ❌ NOT USED by current collection flow endpoints

**Why Fixed**: We initially thought this was the questionnaire creation code path based on function names and imports. Fixed `target_gaps` population logic (lines 160-187).

**Actual Usage**: This file appears to be part of an older architecture (possibly legacy tier_1 flows or discontinued patterns).

**Evidence**:
- Not imported by `collection_crud_questionnaires/commands.py` (the actual code path)
- Functions `prepare_gap_data()`, `generate_questionnaires()`, `persist_questionnaires()` are not called
- Contains patterns that match current code but are not in the active execution path

**Recommendation**:
- Mark file with deprecation warning comment at top
- Create GitHub issue to remove or refactor for ADR-025 compliance
- Search codebase for any remaining imports/calls (likely none)

**Code Fixed (but unused)**:
```python
# Lines 160-187: target_gaps population from persisted_gaps
target_gaps = []
for gap in persisted_gaps:
    target_gaps.append({
        "field_name": gap.field_name,
        "gap_type": gap.gap_type,
        "gap_category": gap.gap_category,
        "asset_id": str(gap.asset_id),
        "priority": gap.priority,
        "impact_on_sixr": gap.impact_on_sixr,
    })
```

---

### 2. `gap_persistence.py::persist_ai_questionnaires()` - Not Used by Current Flows

**File**: `backend/app/services/collection/gap_analysis/gap_persistence.py`

**Function**: `persist_ai_questionnaires()` (lines 133-236)

**Status**: ❌ NOT USED by current collection flow endpoints

**Why Fixed**: Initially thought this was the AI tier (tier_2) questionnaire persistence path. Fixed `target_gaps` population from AI analysis result (lines 184-215).

**Actual Usage**: This function is designed to persist questionnaires from the **AI gap analysis result** (`result_dict` parameter), but the current collection flow uses a different pattern:
- Current: `_generate_questionnaires_per_section()` → per-asset/per-section generation → Redis caching
- Legacy: Gap analysis returns full questionnaire structure → direct persistence

**Evidence**:
- Not called by `collection_crud_questionnaires/commands.py`
- Takes `result_dict` with questionnaire sections, but current pattern generates sections separately
- Contains AI enhancement patterns (adaptive questionnaires) that are now handled differently

**Recommendation**:
- Verify if `persist_ai_questionnaires()` is called anywhere in tier_2 flows
- If not used, mark as deprecated or remove
- If used by assessment flows, document and preserve

**Code Fixed (but unused)**:
```python
# Lines 184-215: target_gaps population from AI analysis result
target_gaps = []
gaps_by_priority = result_dict.get("gaps", {})
for priority_level, gaps in gaps_by_priority.items():
    if isinstance(gaps, list):
        for gap in gaps:
            target_gaps.append({
                "field_name": gap.get("field_name"),
                "gap_type": gap.get("gap_type", "missing_field"),
                "gap_category": gap.get("gap_category", "unknown"),
                "asset_id": gap.get("asset_id"),
                "priority": priority_level,
                "impact_on_sixr": gap.get("impact_on_sixr", "medium"),
            })
```

---

## Actual Code Path (For Reference)

**Current Active Code Path for Collection Flow Questionnaire Generation**:

```
User triggers collection → POST /api/v1/collection-crud-questionnaires/execute
    ↓
collection_crud_questionnaires/commands.py::execute_questionnaires()
    ↓
_start_agent_generation() (background task)
    ↓
_generate_questionnaires_per_section()
    ↓
Per-asset, per-section generation with Redis caching (ADR-035)
    ↓
deduplicate_common_questions() (cross-asset deduplication)
    ↓
Flatten sections and deduplicate by field_id (Bug #10 fix)
    ↓
update_questionnaire_status() → Store in adaptive_questionnaires table
```

**Key Files in Active Code Path**:
- `backend/app/api/v1/endpoints/collection_crud_questionnaires/commands.py`
- `backend/app/api/v1/endpoints/collection_crud_questionnaires/_generate_per_section.py`
- `backend/app/api/v1/endpoints/collection_crud_questionnaires/deduplication_service.py`
- `backend/app/api/v1/endpoints/collection_crud_questionnaires/section_helpers.py`

---

## Action Items

### Immediate (Before Next Release)
- [ ] Add deprecation warning comments to top of `questionnaire_helpers.py`
- [ ] Search for any imports of `questionnaire_helpers.py` functions
- [ ] Verify if `gap_persistence.py::persist_ai_questionnaires()` is used anywhere

### Short-Term (Next Sprint)
- [ ] Create GitHub issue: "Remove legacy questionnaire generation code paths"
- [ ] Audit all files in `backend/app/services/child_flow_services/` for usage
- [ ] Document ADR explaining evolution from legacy to current pattern

### Long-Term (Tech Debt)
- [ ] Modularize `commands.py` (currently 471 lines, exceeds 400-line limit)
- [ ] Consider extracting deduplication logic to separate service module
- [ ] Consolidate questionnaire persistence patterns across all flow types

---

## Lessons Learned

### 1. Follow Backend Logs to Find Actual Code Paths
**Problem**: We initially searched for function names in the codebase and made assumptions about which code was executing.

**Solution**: Backend logs showed the actual function calls:
```
Created pending questionnaire 30de4532... for asset 22222222... in flow 9ef77fc6...
```

This log message led us to `collection_crud_questionnaires/commands.py`, the actual code path.

**Lesson**: **ALWAYS check backend logs** to verify which code is executing before assuming a code path.

### 2. Test After Each Fix
**Problem**: We fixed `questionnaire_helpers.py` and `gap_persistence.py`, but testing showed `target_gaps` was still empty.

**Solution**: Testing revealed the fixes were in the wrong files. We then traced logs to find the actual code path.

**Lesson**: **Test immediately after each fix** to verify it's in the right code path. Don't batch fixes across multiple files without verification.

### 3. Distinguish Between "Code That Exists" and "Code That Executes"
**Problem**: Both legacy files had similar function signatures and patterns, making them look like valid code paths.

**Solution**: Use dynamic analysis (logs, database queries, grep for log messages) instead of static analysis (code reading).

**Lesson**: **Legacy code can look correct but not execute**. Use runtime evidence (logs, database) to verify code paths.

---

## Related Documents

- **ADR-025**: Collection Flow Child Service Migration
- **ADR-035**: Per-Asset, Per-Section Questionnaire Generation
- **Bug #10**: Duplicate Questions in Generated Questionnaires
- **Migration 130**: Canonical Applications Backfill (placeholder asset IDs)

---

## Appendix: How We Found the Actual Code Path

### Step 1: Database Query to Find Questionnaire
```sql
SELECT id, created_at FROM migration.adaptive_questionnaires
WHERE collection_flow_id = '9ae66037-a987-4403-8cec-b6a0c36030bc'
ORDER BY created_at DESC LIMIT 1;

-- Result: 30de4532-c42a-4c26-a1ce-548a0b101558
```

### Step 2: Search Logs for Questionnaire ID
```bash
docker logs migration_backend 2>&1 | grep -A5 -B5 "30de4532-c42a-4c26-a1ce-548a0b101558"

-- Found: "Created pending questionnaire 30de4532... for asset 22222222... in flow 9ef77fc6..."
```

### Step 3: Grep for Log Message Source
```bash
grep -r "Created pending questionnaire" backend/app/

-- Found: backend/app/api/v1/endpoints/collection_crud_questionnaires/commands.py:210
```

### Step 4: Read Actual Code Path
```python
# commands.py:210
logger.info(
    f"Created pending questionnaire {questionnaire_id} for asset {asset_id} in flow {flow_db_id}"
)
```

This led us to the correct code path and the correct fix location (line 486-511).

---

**End of Document**
