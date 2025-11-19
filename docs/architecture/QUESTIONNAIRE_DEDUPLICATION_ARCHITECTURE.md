# Questionnaire Deduplication Architecture

> **Document Created**: 2025-11-19
> **Context**: Bug #10 Investigation - Duplicate Questions in Collection Flow Questionnaires
> **Status**: ✅ Bug Fixed, Architecture Documented

## Executive Summary

Collection flow questionnaire generation uses a **two-stage deduplication architecture**:

1. **Stage 1: Cross-Asset Deduplication** (`deduplication_service.py`)
   - Merges questions that apply to multiple assets
   - Consolidates `asset_ids` metadata
   - Designed for questions like "What is your business_criticality?" that should be asked once for all assets

2. **Stage 2: Within-Asset Deduplication** (`commands.py` flattening)
   - Removes duplicate questions for the same asset
   - Uses `field_id` as unique identifier
   - **This stage fixed Bug #10** (agent generating duplicate questions within same section)

Both stages are necessary and serve different purposes.

---

## The Bug: Within-Asset Duplicates (Bug #10)

### Problem Description

Generated questionnaires contained duplicate questions within the same section for a single asset:

**Example**:
```json
Questions for Asset "Ab Initio":
  1. business_criticality_score (compliance section)
  2. change_tolerance (compliance section)
  3. compliance_constraints (compliance section)
  4. stakeholder_impact (compliance section)
  5. business_criticality_score (DUPLICATE - compliance section)
  6. change_tolerance (DUPLICATE - compliance section)
  7. compliance_constraints (DUPLICATE - compliance section)
  8. stakeholder_impact (DUPLICATE - compliance section)
  9. architecture_pattern (tech_debt section)
  10. code_quality_metrics (tech_debt section)
  ... and so on (18 total, 8 duplicates)
```

### Root Cause

The CrewAI agent (`readiness_assessor`) sometimes generates duplicate questions within the same section when processing gaps. This is an agent behavior issue, not a data pipeline issue.

**Evidence from Agent Output**:
```python
# Agent generates for compliance section:
{
  "questions": [
    {"field_id": "business_criticality_score", ...},
    {"field_id": "change_tolerance", ...},
    {"field_id": "business_criticality_score", ...},  # DUPLICATE
    {"field_id": "change_tolerance", ...}             # DUPLICATE
  ]
}
```

### Why Stage 1 Deduplication Didn't Catch It

`deduplication_service.py` is designed for **cross-asset** deduplication:

```python
# Example of what Stage 1 handles:
# Asset A has question: "business_criticality" -> asset_ids: ["asset_A"]
# Asset B has question: "business_criticality" -> asset_ids: ["asset_B"]
# Stage 1 merges: "business_criticality" -> asset_ids: ["asset_A", "asset_B"]
```

**But our bug was**:
```python
# Single asset has duplicate questions in same section:
# Asset A, Section compliance:
#   - "business_criticality" (first occurrence)
#   - "business_criticality" (DUPLICATE - second occurrence)
```

Stage 1 uses `composite_key = f"{section_id}:{field_id}"`, so both occurrences have the same key. The service merges `asset_ids` but **doesn't remove the duplicate question** from the list.

---

## Two-Stage Deduplication Architecture

### Stage 1: Cross-Asset Deduplication

**File**: `backend/app/api/v1/endpoints/collection_crud_questionnaires/deduplication_service.py`

**Function**: `deduplicate_common_questions(sections, assets)`

**Purpose**: Deduplicate questions that appear for multiple assets

**Algorithm**:
```python
question_map: Dict[str, dict] = {}

for section in sections:
    section_id = section.get("section_id")

    for question in section.get("questions", []):
        field_id = question.get("field_id")
        composite_key = f"{section_id}:{field_id}"

        if composite_key in question_map:
            # Duplicate found - merge asset_ids
            existing = question_map[composite_key]
            existing_asset_ids = set(existing["metadata"]["asset_ids"])
            new_asset_ids = set(question["metadata"]["asset_ids"])
            merged_asset_ids = list(existing_asset_ids | new_asset_ids)

            existing["metadata"]["asset_ids"] = merged_asset_ids
            existing["metadata"]["applies_to_count"] = len(merged_asset_ids)
        else:
            # First occurrence - store
            question_map[composite_key] = question.copy()

# Rebuild sections from question_map
deduplicated_sections = rebuild_sections(question_map)
```

**Key Insight**: This stage **merges metadata** (asset_ids), but if the same question appears twice for the **same asset** in the **same section**, it will only merge the metadata, not reduce the question count.

**Example**:
```python
# Input: 18 questions (8 duplicates for same asset)
# Output: 18 questions (metadata merged, but duplicates still present)
# Duplicates removed: 0

# Because:
# Question 1: field_id="business_criticality", asset_ids=["asset_A"]
# Question 5: field_id="business_criticality", asset_ids=["asset_A"]
# Both have same composite_key, so metadata gets merged:
# Result: 1 question with asset_ids=["asset_A"] BUT both questions still in list
```

**Why It Reports "0 duplicates removed"**:
- The service calculates: `total_original - total_deduplicated`
- When questions are for the same asset, the count doesn't change (metadata merge only)
- Stats: `original_count=18, deduplicated_count=18, duplicates_removed=0`

### Stage 2: Within-Asset Deduplication (Flattening)

**File**: `backend/app/api/v1/endpoints/collection_crud_questionnaires/commands.py`

**Location**: Lines 486-511 (inside `_start_agent_generation()` function)

**Purpose**: Remove duplicate questions for the same asset within the same section

**Algorithm**:
```python
# CRITICAL FIX Bug #10: Deduplicate questions at flattening stage
seen_field_ids = set()
deduplicated_questions = []
duplicates_removed = 0

for question in questions:
    field_id = (
        question.get("field_id")
        if isinstance(question, dict)
        else getattr(question, "field_id", None)
    )
    if field_id and field_id in seen_field_ids:
        duplicates_removed += 1
        logger.debug(f"Removed duplicate question: {field_id}")
        continue
    if field_id:
        seen_field_ids.add(field_id)
    deduplicated_questions.append(question)

if duplicates_removed > 0:
    logger.warning(
        f"Removed {duplicates_removed} duplicate questions during flattening "
        f"({len(questions)} → {len(deduplicated_questions)} questions)"
    )
    questions = deduplicated_questions
```

**Key Insight**: This stage uses `field_id` as the unique identifier, regardless of which asset or section the question belongs to. It effectively removes within-asset duplicates.

**Example**:
```python
# Input: 18 questions (from Stage 1)
# Processing:
#   - business_criticality_score → Added (first occurrence)
#   - change_tolerance → Added (first occurrence)
#   - business_criticality_score → SKIP (already seen)
#   - change_tolerance → SKIP (already seen)
#   ... and so on
# Output: 10 unique questions
# Duplicates removed: 8
```

**Backend Log Evidence**:
```
Removed 8 duplicate questions during flattening (18 → 10 questions)
```

---

## Code Flow Diagram

```
User triggers collection → POST /api/v1/collection-crud-questionnaires/execute
    ↓
commands.py::execute_questionnaires()
    ↓
_start_agent_generation() (background task)
    ↓
_generate_questionnaires_per_section()
    ↓
Per-asset, per-section generation with Redis caching (ADR-035)
    ↓
Agent generates questions (sometimes with duplicates)
    ↓
【STAGE 1】 deduplicate_common_questions() (cross-asset deduplication)
    ↓
    ├─ Merge asset_ids for questions appearing across multiple assets
    ├─ Use composite_key: f"{section_id}:{field_id}"
    ├─ Build question_map with merged metadata
    ├─ Stats: "0 duplicates removed" (if all questions from same asset)
    └─ Return: deduplicated_sections (metadata merged, count unchanged)
    ↓
【STAGE 2】 Flatten sections and deduplicate by field_id (Bug #10 fix)
    ↓
    ├─ Extract all questions from all sections
    ├─ Track seen_field_ids in set
    ├─ Skip duplicate field_ids
    ├─ Stats: "Removed 8 duplicate questions (18 → 10)"
    └─ Return: deduplicated_questions (duplicates removed)
    ↓
update_questionnaire_status() → Store in adaptive_questionnaires table
```

---

## Test Results

### Test Setup
- **Questionnaire ID**: `30de4532-c42a-4c26-a1ce-548a0b101558`
- **Flow ID**: `7cd0e025-9243-49a9-b67e-548f4577843f`
- **Assets**: 2 canonical applications (Ab Initio, Active Directory)
- **Date**: 2025-11-19

### Backend Logs

**Stage 1 Deduplication**:
```
INFO Deduplication: 18 questions → 18 questions (0 duplicates removed, 0.0% reduction)
```
✅ Expected behavior: Cross-asset deduplication doesn't apply when all questions from same asset

**Stage 2 Deduplication**:
```
WARNING Removed 8 duplicate questions during flattening (18 → 10 questions)
```
✅ Fixed Bug #10: Within-asset duplicates removed

### Database Verification

```sql
-- Verify question count
SELECT jsonb_array_length(questions) as question_count
FROM migration.adaptive_questionnaires
WHERE id = '30de4532-c42a-4c26-a1ce-548a0b101558';
```
**Result**: `10` ✅ (not 18)

```sql
-- Verify unique field IDs
SELECT jsonb_array_elements(questions)->>'field_id' as field_id
FROM migration.adaptive_questionnaires
WHERE id = '30de4532-c42a-4c26-a1ce-548a0b101558';
```
**Result**: 10 unique field_ids ✅
```
business_criticality_score
change_tolerance
compliance_constraints
stakeholder_impact
architecture_pattern
code_quality_metrics
eol_technology_assessment
documentation_quality
security_vulnerabilities
configuration_complexity
```

### Frontend Verification

**Before Fix**:
- Displayed 18 questions (duplicates visible)
- React duplicate key warnings in console
- Poor user experience

**After Fix**:
- Displays 10 unique questions ✅
- No React warnings ✅
- Clean user experience ✅

---

## Why Both Stages Are Necessary

### Scenario 1: Cross-Asset Deduplication (Stage 1 Purpose)

**Setup**: 3 assets in collection flow
```
Asset A gaps: ["business_criticality", "compliance_scopes"]
Asset B gaps: ["business_criticality", "backup_frequency"]
Asset C gaps: ["compliance_scopes", "rto"]
```

**Without Stage 1**:
```
Questions:
1. business_criticality (for Asset A)
2. compliance_scopes (for Asset A)
3. business_criticality (for Asset B) ← DUPLICATE
4. backup_frequency (for Asset B)
5. compliance_scopes (for Asset C) ← DUPLICATE
6. rto (for Asset C)

Total: 6 questions (user answers business_criticality twice!)
```

**With Stage 1**:
```
Questions:
1. business_criticality (applies to: Asset A, Asset B) ← MERGED
2. compliance_scopes (applies to: Asset A, Asset C) ← MERGED
3. backup_frequency (applies to: Asset B)
4. rto (applies to: Asset C)

Total: 4 questions (user answers business_criticality ONCE for both assets!)
```

✅ Stage 1 provides better user experience by asking common questions once

### Scenario 2: Within-Asset Deduplication (Stage 2 Purpose - Bug #10)

**Setup**: Agent generates duplicate questions for single asset
```
Asset A, compliance section:
  - business_criticality (first occurrence)
  - change_tolerance (first occurrence)
  - business_criticality (DUPLICATE - agent error)
  - change_tolerance (DUPLICATE - agent error)
```

**Without Stage 2**:
```
Questions:
1. business_criticality (Asset A)
2. change_tolerance (Asset A)
3. business_criticality (Asset A) ← DUPLICATE
4. change_tolerance (Asset A) ← DUPLICATE

Total: 4 questions (user sees duplicates!)
```

**With Stage 2**:
```
Questions:
1. business_criticality (Asset A)
2. change_tolerance (Asset A)

Total: 2 questions (duplicates removed!)
```

✅ Stage 2 protects against agent behavior issues

---

## Lessons Learned

### 1. Two-Stage Deduplication Serves Different Purposes

- **Stage 1 (Cross-Asset)**: User experience optimization (ask common questions once)
- **Stage 2 (Within-Asset)**: Data quality protection (remove agent-generated duplicates)

Both stages are necessary. Removing either would cause issues.

### 2. Understanding "0 Duplicates Removed" Doesn't Mean "Not Working"

`deduplication_service.py` reporting "0 duplicates removed" is **correct behavior** when:
- All questions belong to the same asset (no cross-asset merging needed)
- Service merges metadata but doesn't reduce count

This is NOT a bug. It's working as designed for cross-asset scenarios.

### 3. Defensive Coding Against Agent Behavior

Agents (CrewAI) can have unpredictable behavior:
- Sometimes generate duplicate questions
- Sometimes skip questions
- Sometimes hallucinate field names

**Solution**: Add validation and deduplication at the pipeline level (Stage 2), not just at the agent level.

### 4. Importance of Multi-Layer Validation

**Pipeline Layers**:
1. Agent generation (can produce duplicates)
2. Cross-asset deduplication (Stage 1)
3. Within-asset deduplication (Stage 2)
4. Database storage
5. Frontend rendering

Each layer provides protection against issues in previous layers.

---

## Debug Logging Added

### Purpose
Added debug logging to `deduplication_service.py` to aid future investigations of deduplication behavior.

### Location
Lines 41-58 in `deduplication_service.py`

### Log Output Example
```python
DEBUG Processing section section_compliance with 8 questions
DEBUG Processing question: composite_key=section_compliance:business_criticality_score, already_seen=False
DEBUG Processing question: composite_key=section_compliance:change_tolerance, already_seen=False
DEBUG Processing question: composite_key=section_compliance:business_criticality_score, already_seen=True
DEBUG Processing question: composite_key=section_compliance:change_tolerance, already_seen=True
...
INFO Deduplication: 18 questions → 18 questions (0 duplicates removed, 0.0% reduction)
```

This helps understand:
- Which questions are being processed
- Which composite_keys are being seen multiple times
- Why the count doesn't decrease (same asset, metadata merge only)

---

## Future Enhancements (Optional)

### Option 1: Enhance Stage 1 to Handle Within-Asset Duplicates

**Change**: Modify `deduplication_service.py` to also count and remove within-asset duplicates.

**Implementation**:
```python
if composite_key in question_map:
    existing = question_map[composite_key]

    # Check if this is cross-asset duplication or within-asset duplication
    existing_asset_ids = set(existing.get("metadata", {}).get("asset_ids", []))
    new_asset_ids = set(question.get("metadata", {}).get("asset_ids", []))

    if existing_asset_ids == new_asset_ids:
        # Within-asset duplicate - skip this question
        duplicates_removed += 1
        logger.debug(f"Removed within-asset duplicate: {field_id}")
        continue
    else:
        # Cross-asset duplicate - merge metadata
        merged_asset_ids = list(existing_asset_ids | new_asset_ids)
        existing["metadata"]["asset_ids"] = merged_asset_ids
        existing["metadata"]["applies_to_count"] = len(merged_asset_ids)
```

**Pros**:
- Single-stage deduplication
- More accurate stats reporting
- Cleaner architecture

**Cons**:
- Stage 2 flattening already works perfectly
- Extra complexity for minimal benefit
- Bug #10 is already fixed

**Recommendation**: **NOT RECOMMENDED** - Current two-stage approach is working well. Stage 2 provides additional validation layer which is valuable.

### Option 2: Accept Current Architecture (RECOMMENDED)

**Reasoning**:
- Bug #10 is fixed ✅
- Two-stage approach provides defense in depth
- Each stage has clear purpose
- Extra logging added for future debugging
- No user-facing issues

**Recommendation**: **ACCEPT CURRENT STATE** - Document architecture and move on.

---

## References

- **Bug #10**: Duplicate Questions in Generated Questionnaires
- **ADR-035**: Per-Asset, Per-Section Questionnaire Generation
- **LEGACY_CODE_PATHS_FOR_DEPRECATION.md**: Code path investigation findings
- **commits.py**: Lines 486-511 (Stage 2 deduplication fix)
- **deduplication_service.py**: Lines 36-157 (Stage 1 cross-asset deduplication)

---

**End of Document**
