# Questionnaire Patterns Master

**Last Updated**: 2025-12-05
**Version**: 1.1
**Consolidates**: 14 memories
**Status**: Active

---

## Quick Reference

> **Top 5 patterns to know:**
> 1. **Two-Stage Deduplication**: Cross-asset (merge asset_ids) + within-asset (field_id uniqueness)
> 2. **Race Condition Fix**: Wait for `manual_collection` phase before polling questionnaires
> 3. **Multi-Tenant Scoping**: Always scope by (client_account_id, engagement_id, asset_id)
> 4. **Failed Retry Pattern**: UPDATE failed questionnaires instead of INSERT (avoids constraint violation)
> 5. **Bootstrap Field Transformation**: Normalize bootstrap fields to standard question format

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture Patterns](#architecture-patterns)
3. [Common Patterns](#common-patterns)
4. [Bug Fix Patterns](#bug-fix-patterns)
5. [Anti-Patterns](#anti-patterns)
6. [Code Templates](#code-templates)
7. [Troubleshooting](#troubleshooting)
8. [Related Documentation](#related-documentation)
9. [Consolidated Sources](#consolidated-sources)

---

## Overview

### What This Covers
Questionnaire generation, deduplication, persistence, and display patterns for the Collection Flow's adaptive data collection system. Includes AI agent questionnaire generation and multi-tenant scoping.

### When to Reference
- Implementing questionnaire generation endpoints
- Debugging duplicate questions issues
- Fixing questionnaire display problems
- Handling failed questionnaire retries
- Implementing multi-tenant deduplication

### Key Files in Codebase
- `backend/app/api/v1/endpoints/collection_crud_questionnaires/`
- `backend/app/models/collection_flow/adaptive_questionnaire_model.py`
- `src/hooks/collection/useAdaptiveFormFlow.ts`
- `src/hooks/collection/useQuestionnairePolling.ts`

---

## Architecture Patterns

### Pattern 1: Two-Stage Deduplication Architecture

**Purpose**: Ensure question uniqueness across assets AND within individual assets.

**Stage 1: Cross-Asset Deduplication** (`deduplication_service.py`)
- Merges questions common across multiple assets
- Uses `field_id` as dedup key
- Maintains `asset_ids` array for multi-asset questions

```python
def deduplicate_common_questions(sections, assets):
    question_map: Dict[str, dict] = {}

    for section in sections:
        for question in section.get("questions", []):
            field_id = question.get("field_id")
            composite_key = f"{section_id}:{field_id}"

            if composite_key in question_map:
                # MERGE asset_ids for duplicate questions
                existing_asset_ids = set(existing["metadata"]["asset_ids"])
                new_asset_ids = set(question["metadata"]["asset_ids"])
                existing["metadata"]["asset_ids"] = list(existing_asset_ids | new_asset_ids)
            else:
                question_map[composite_key] = question
```

**Stage 2: Within-Asset Deduplication** (`start_generation.py`)
- Removes duplicate questions within single asset
- Uses set membership for O(1) dedup
- Catches CrewAI agent duplicate generation errors

```python
seen_field_ids: Set[str] = set()
deduplicated_questions = []

for question in all_questions:
    field_id = question.get("field_id") or question.get("field_name")
    if field_id in seen_field_ids:
        logger.debug(f"Skipping duplicate: {field_id}")
        continue
    seen_field_ids.add(field_id)
    deduplicated_questions.append(question)
```

**When to Debug Each**:
- Stage 1: Multiple assets, `applies_to_count > 1`
- Stage 2: Single asset has duplicates, same `field_id` appears multiple times

**Source**: Consolidated from `two_stage_questionnaire_deduplication_architecture_2025_11`

---

### Pattern 2: Multi-Tenant Isolation Hierarchy

**Levels**:
- **Organization**: `client_account_id`
- **Project**: `engagement_id`
- **Asset**: `asset_id`

**Unique Constraint**: `(client_account_id, engagement_id, asset_id)`

```python
async def get_existing_questionnaire(
    client_account_id: UUID,
    engagement_id: UUID,
    asset_id: UUID,
    db: AsyncSession,
) -> Optional[AdaptiveQuestionnaire]:
    return await db.execute(
        select(AdaptiveQuestionnaire).where(
            AdaptiveQuestionnaire.client_account_id == client_account_id,
            AdaptiveQuestionnaire.engagement_id == engagement_id,
            AdaptiveQuestionnaire.asset_id == asset_id,
            AdaptiveQuestionnaire.completion_status != "failed",
        )
    ).scalar_one_or_none()
```

**Source**: Consolidated from `multi-tenant-questionnaire-deduplication-pattern`

---

## Common Patterns

### Pattern 3: Failed Questionnaire Retry (UPDATE not INSERT)

**Problem**: Retrying failed questionnaire causes unique constraint violation.

**Why**: Deduplication query excludes `completion_status = 'failed'`, then INSERT hits constraint.

**Solution**: Check for failed separately, UPDATE instead of INSERT:

```python
# After checking for reusable questionnaires...
failed_result = await db.execute(
    select(AdaptiveQuestionnaire).where(
        AdaptiveQuestionnaire.client_account_id == context.client_account_id,
        AdaptiveQuestionnaire.engagement_id == context.engagement_id,
        AdaptiveQuestionnaire.asset_id == asset_id,
        AdaptiveQuestionnaire.completion_status == "failed",
    )
)
failed_questionnaire = failed_result.scalar_one_or_none()

if failed_questionnaire:
    # UPDATE existing record instead of INSERT
    failed_questionnaire.completion_status = "pending"
    failed_questionnaire.collection_flow_id = flow.id
    failed_questionnaire.updated_at = datetime.now(timezone.utc)
    await db.commit()

    # Trigger regeneration
    task = asyncio.create_task(_background_generate(failed_questionnaire.id, ...))
    return  # Skip INSERT
```

**Source**: Consolidated from `multi-tenant-questionnaire-deduplication-pattern`

---

### Pattern 4: Asset-Aware Generation Enforcement

**Problem**: Blank forms when no assets selected, making gap analysis impossible.

**Solution**: Verify assets before generation:

```python
selected_asset_ids = flow.collection_config.get("selected_asset_ids", [])
selected_app_ids = flow.collection_config.get("selected_application_ids", [])

if not selected_app_ids and not selected_asset_ids:
    logger.warning(f"No assets selected for flow {flow_id}")
    return [bootstrap_questionnaire_with_asset_selection_required()]
```

**Source**: Consolidated from `asset_aware_questionnaire_generation_2025_24`

---

### Pattern 5: Questionnaire Response Persistence

**API Endpoints**:
- POST `/collection/flows/{flow_id}/questionnaires/{questionnaire_id}/responses` - Save
- GET `/collection/flows/{flow_id}/questionnaires/{questionnaire_id}/responses` - Retrieve

**Database Schema** (`collection_questionnaire_responses`):
- `collection_flow_id` - FK to collection_flows.id (INTEGER, not UUID!)
- `question_id` - Field/question identifier
- `response_value` - JSON value of response
- `confidence_score` - Validation confidence
- `validation_status` - Current validation status

**Key Note**: Flow IDs in frontend are UUIDs, map to integer IDs in database.

**Source**: Consolidated from `questionnaire_persistence_fix_complete`

---

### Pattern 6: Bootstrap Field Transformation (Added 2025-12-05)

**Problem**: Bootstrap questionnaires use different field structure, causing infinite "Generating Questionnaire" hang.

**Root Cause**: Bootstrap fields have `{id, name, type}` but frontend expects `{field_id, question_text, input_type}`.

**Solution**: Transform bootstrap fields to standard question format in backend:

```python
def _transform_bootstrap_fields_to_questions(fields: List[dict]) -> List[dict]:
    """Transform bootstrap questionnaire fields to standard question format.

    Bootstrap questionnaires (asset_selection phase) use a different field structure:
    - `id` instead of `field_id`
    - `name` instead of `question_text`
    - `type` instead of `input_type`
    - `description` instead of `help_text`

    Issue #1202/#1203 Fix: Without this transformation, the frontend's conversion fails
    silently, leaving the UI in an infinite "Generating Questionnaire" state.
    """
    transformed = []
    for field in fields:
        transformed.append({
            "field_id": field.get("id", ""),
            "question_text": field.get("name", ""),
            "input_type": field.get("type", "multiselect"),
            "help_text": field.get("description", ""),
            "required": field.get("required", True),
            "options": field.get("options", []),
            "category": "asset_selection",  # Ensure proper section grouping
            "validation": field.get("validation", {}),
        })
    return transformed
```

**Usage**: Apply when returning bootstrap questionnaire responses:

```python
return [
    AdaptiveQuestionnaireResponse(
        id="bootstrap_asset_selection",
        questions=_transform_bootstrap_fields_to_questions(
            bootstrap_q.get("fields", [])
        ),
        # ... other fields
    )
]
```

**Key Files**:
- `backend/app/api/v1/endpoints/collection_crud_questionnaires/queries.py`
- `backend/app/services/collection/asset_selection_bootstrap.py`

**Source**: Issue #1202/#1203 fix (2025-12-05)

---

## Bug Fix Patterns

### Bug: "0/0 fields" Instead of Questionnaire Display (Issue #677)

**Date Fixed**: November 2025
**Symptoms**: Collection flow shows "0/0 fields" instead of generated questionnaire

**Root Causes**:
1. Frontend polled too early (phase still `questionnaire_generation`)
2. Background task interrupted, phase never transitioned

**Frontend Fix** - Wait for phase signal:
```typescript
const { data: questionnaires } = useQuery({
  queryKey: ['questionnaires', flowId],
  queryFn: () => collectionService.getQuestionnaires(flowId),
  refetchInterval: 5000,
  enabled: !!flowId && currentPhase === 'manual_collection'  // Wait for ready
});

if (currentPhase === 'questionnaire_generation') {
  return { questionnaires: [], status: 'Generating with AI...', isLoading: true };
}
```

**Backend Fix** - Defensive phase transition:
```python
# In get_adaptive_questionnaires endpoint
if existing_questionnaires and flow.current_phase == "questionnaire_generation":
    has_questions = any(q.questions and len(q.questions) > 0 for q in existing_questionnaires)

    if has_questions:
        logger.warning(f"Defensive phase transition for {flow_id}")
        await db.execute(
            sql_update(CollectionFlow)
            .where(CollectionFlow.flow_id == UUID(flow_id))
            .values(current_phase="manual_collection", status="paused")
        )
        await db.commit()
```

**Source**: Consolidated from `issue-677-questionnaire-display-race-condition-fix`

---

### Bug: Infinite "Generating Questionnaire" Hang (Issues #1202, #1203)

**Date Fixed**: December 2025
**Symptoms**: UI shows "Generating Questionnaire" forever in asset_selection phase

**Root Cause**: Bootstrap questionnaire field structure mismatch:
- Bootstrap uses: `{id, name, type, description}`
- Frontend expects: `{field_id, question_text, input_type, help_text}`

**Why It Hangs**:
1. Backend returns bootstrap fields without transformation
2. Frontend's `convertQuestionnairesToFormData` fails silently
3. Error caught but state not updated → `formData=null`
4. Polling continues indefinitely (`!state.formData` stays true)
5. UI stuck showing "Generating Questionnaire"

**Backend Fix** - Transform bootstrap fields (see Pattern 6):
```python
questions=_transform_bootstrap_fields_to_questions(
    bootstrap_q.get("fields", [])
)
```

**Frontend Fix** - Don't silently swallow errors:
```typescript
} catch (error) {
  console.error('Failed to convert questionnaire:', error);

  // Update state with error to stop polling and show error UI
  setState((prev) => ({
    ...prev,
    isLoading: false,
    error: error instanceof Error ? error.message : 'Failed to process questionnaire',
    questionnaires: questionnaires,
  }));

  toast({
    title: "Questionnaire Error",
    description: "Failed to process the questionnaire. Please try refreshing the page.",
    variant: "destructive",
  });
}
```

**Key Files Changed**:
- `backend/app/api/v1/endpoints/collection_crud_questionnaires/queries.py`
- `src/hooks/collection/useAdaptiveFormFlow.ts`

**Source**: Issues #1202, #1203 fix (2025-12-05)

---

### Bug: Duplicate Questions Despite Deduplication

**Date Fixed**: November 2025 (Bug #10)
**Symptoms**: `deduplication_service.py` reports "0 duplicates removed" when duplicates exist

**Root Cause**: Two-stage architecture misunderstanding
- Stage 1 handles cross-asset duplicates only
- Stage 2 handles within-asset duplicates

**Solution**: Implement Stage 2 deduplication at flattening step (see Pattern 1).

**Source**: Consolidated from `two_stage_questionnaire_deduplication_architecture_2025_11`

---

### Bug: Unique Constraint Violation on Retry

**Date Fixed**: November 2025
**Symptoms**: `duplicate key violates unique constraint "uq_questionnaire_per_asset_per_engagement"`

**Root Cause**: Deduplication excludes failed, INSERT hits constraint

**Solution**: UPDATE failed records instead of INSERT (see Pattern 3).

**Source**: Consolidated from `multi-tenant-questionnaire-deduplication-pattern`

---

## Anti-Patterns

### Don't: Poll Questionnaires Before Phase Transition

**Why it's bad**: AI agent takes 30-60s, causes "0/0 fields" display.

**Wrong**:
```typescript
enabled: !!flowId  // Polls immediately
```

**Right**:
```typescript
enabled: !!flowId && currentPhase === 'manual_collection'
```

---

### Don't: INSERT for Retry After Failure

**Why it's bad**: Unique constraint violation.

**Wrong**:
```python
# Create new questionnaire on retry
new_questionnaire = AdaptiveQuestionnaire(...)
db.add(new_questionnaire)
```

**Right**:
```python
# UPDATE existing failed record
failed_questionnaire.completion_status = "pending"
await db.commit()
```

---

### Don't: Use UUID flow_id as Database FK

**Why it's bad**: Schema uses integer IDs.

**Wrong**:
```python
collection_flow_id=flow.flow_id  # UUID
```

**Right**:
```python
collection_flow_id=str(flow.id)  # Integer PK
```

---

### Don't: Silently Swallow Conversion Errors

**Why it's bad**: Causes infinite polling loops with no error visibility.

**Wrong**:
```typescript
} catch (error) {
  console.error('Failed to convert questionnaire:', error);
  // State never updated - polling continues forever
}
```

**Right**:
```typescript
} catch (error) {
  console.error('Failed to convert questionnaire:', error);
  setState((prev) => ({
    ...prev,
    error: error.message,
    isLoading: false,
  }));
  showErrorToast();
}
```

---

## Code Templates

### Template 1: Questionnaire Generation Endpoint

```python
@router.post("/{flow_id}/questionnaires/generate")
async def generate_questionnaire(
    flow_id: str,
    db: AsyncSession = Depends(get_async_db),
    context: RequestContext = Depends(get_request_context),
):
    # 1. Get flow with tenant scoping
    flow = await get_collection_flow(flow_id, db, context)
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")

    # 2. Check asset selection
    asset_ids = flow.collection_config.get("selected_asset_ids", [])
    if not asset_ids:
        return {"error": "No assets selected"}

    # 3. Check for existing (non-failed) questionnaire
    existing = await get_existing_questionnaire(
        context.client_account_id, context.engagement_id, asset_ids[0], db
    )
    if existing:
        return {"questionnaire_id": str(existing.id), "reused": True}

    # 4. Check for failed questionnaire (UPDATE instead of INSERT)
    failed = await get_failed_questionnaire(
        context.client_account_id, context.engagement_id, asset_ids[0], db
    )
    if failed:
        failed.completion_status = "pending"
        await db.commit()
        questionnaire_id = failed.id
    else:
        # 5. Create new questionnaire
        new_q = AdaptiveQuestionnaire(...)
        db.add(new_q)
        await db.commit()
        questionnaire_id = new_q.id

    # 6. Trigger background generation
    asyncio.create_task(background_generate(questionnaire_id, ...))

    return {"questionnaire_id": str(questionnaire_id)}
```

---

### Template 2: Frontend Phase-Aware Polling

```typescript
export function useQuestionnairePolling(flowId: string) {
  // Poll phase first
  const { data: flowDetails } = useQuery({
    queryKey: ['flow-details', flowId],
    queryFn: () => collectionService.getFlowDetails(flowId),
    refetchInterval: 2000,
    enabled: !!flowId,
  });

  const currentPhase = flowDetails?.current_phase;
  const isReady = currentPhase === 'manual_collection';

  // Only poll questionnaires when ready
  const { data: questionnaires } = useQuery({
    queryKey: ['questionnaires', flowId],
    queryFn: () => collectionService.getQuestionnaires(flowId),
    refetchInterval: 5000,
    enabled: !!flowId && isReady,
  });

  if (!isReady) {
    return {
      questionnaires: [],
      isLoading: true,
      status: 'Generating questionnaire with AI agent...',
    };
  }

  return { questionnaires, isLoading: false, status: 'ready' };
}
```

---

## Troubleshooting

### Issue: "0/0 fields" displayed

**Diagnosis**:
```sql
SELECT current_phase, status FROM migration.collection_flows WHERE flow_id = 'xxx';
```

**If phase = 'questionnaire_generation'**: Phase transition stuck. Check backend logs, apply defensive fix.

**If phase = 'manual_collection'**: Frontend not polling. Check `enabled` condition.

---

### Issue: Infinite "Generating Questionnaire" hang

**Diagnosis**:
1. Check browser console for conversion errors
2. Check flow phase: `SELECT current_phase FROM migration.collection_flows WHERE flow_id = 'xxx';`
3. If phase = 'asset_selection', check bootstrap questionnaire structure

**If bootstrap has wrong field names**: Apply `_transform_bootstrap_fields_to_questions()` fix.

**If error silently caught**: Apply frontend error handling fix.

---

### Issue: Duplicate questions in questionnaire

**Diagnosis**:
```sql
SELECT q.field_id, COUNT(*) as count
FROM migration.adaptive_questionnaires aq,
     jsonb_array_elements(aq.questions) q
WHERE aq.id = 'xxx'
GROUP BY q.field_id
HAVING COUNT(*) > 1;
```

**Fix**: Apply Stage 2 deduplication at flattening step.

---

### Issue: Constraint violation on retry

**Diagnosis**: Error message contains `uq_questionnaire_per_asset_per_engagement`

**Fix**: Implement failed questionnaire UPDATE pattern (Pattern 3).

---

## Related Documentation

| Resource | Location | Purpose |
|----------|----------|---------|
| ADR-030 | `/docs/adr/030-adaptive-questionnaire-generation.md` | Questionnaire architecture |
| ADR-034 | `/docs/adr/034-questionnaire-deduplication.md` | Deduplication decision |
| Collection Flow Master | `.serena/memories/collection_flow_patterns_master.md` | Parent flow patterns |

---

## Consolidated Sources

| Original Memory | Date | Key Contribution |
|-----------------|------|------------------|
| `two_stage_questionnaire_deduplication_architecture_2025_11` | 2025-11 | Two-stage dedup |
| `asset_aware_questionnaire_generation_2025_24` | 2025-10 | Asset enforcement |
| `questionnaire_persistence_fix_complete` | 2025-09 | Persistence |
| `issue-677-questionnaire-display-race-condition-fix` | 2025-11 | Race condition fix |
| `multi-tenant-questionnaire-deduplication-pattern` | 2025-11 | Multi-tenant scoping |
| `asset_aware_questionnaire_fix_2025_24` | 2025-10 | Asset awareness |
| `asset_based_questionnaire_deduplication_schema_2025_11` | 2025-11 | Schema patterns |
| `asset_questionnaire_deduplication_implementation_2025_11` | 2025-11 | Implementation |
| `bug_801_questionnaire_status_flow_analysis` | 2025-10 | Status analysis |
| `intelligent-questionnaire-context-aware-options` | 2025-10 | Context awareness |
| `issue_980_questionnaire_wiring_complete_2025_11` | 2025-11 | Wiring complete |
| `questionnaire_persistence_investigation_summary` | 2025-08 | Investigation |
| `questionnaire_persistence_resolution_2025_08` | 2025-08 | Resolution |
| Issues #1202, #1203 fix | 2025-12 | Bootstrap field transformation |

**Archive Location**: `.serena/archive/questionnaire/`

---

## Changelog

| Date | Change | Author |
|------|--------|--------|
| 2025-11-30 | Initial consolidation of 13 memories | Claude Code |
| 2025-12-05 | Added Pattern 6 (Bootstrap Field Transformation) and Bug Fix for Issues #1202/#1203 | Claude Code |

---

## Search Keywords

questionnaire, deduplication, adaptive_form, generation, persistence, race_condition, multi_tenant, asset_aware, phase_transition, bootstrap, field_transformation, silent_error
