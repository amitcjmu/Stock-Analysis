# Two-Stage Questionnaire Deduplication Architecture
Date: 2025-11-19
Context: PR #1070 - Bug #10 Investigation

## Problem
During Bug #10 investigation (duplicate questions in questionnaires), `deduplication_service.py` reported "0 duplicates removed" when 8 duplicates clearly existed. This revealed a misunderstood two-stage architecture.

## Architecture Discovery

### Stage 1: Cross-Asset Deduplication (deduplication_service.py)
**Purpose**: Deduplicate questions common across multiple assets
**Mechanism**: Merges `asset_ids` for questions with identical `field_id`

**Location**: `backend/app/api/v1/endpoints/collection_crud_questionnaires/deduplication_service.py`

**Code**:
```python
def deduplicate_common_questions(sections, assets):
    question_map: Dict[str, dict] = {}

    for section in sections:
        for question in section.get("questions", []):
            field_id = question.get("field_id")
            composite_key = f"{section_id}:{field_id}"

            if composite_key in question_map:
                # Duplicate found - MERGE asset_ids
                existing = question_map[composite_key]
                existing_asset_ids = set(existing.get("metadata", {}).get("asset_ids", []))
                new_asset_ids = set(question.get("metadata", {}).get("asset_ids", []))
                merged_asset_ids = list(existing_asset_ids | new_asset_ids)

                existing["metadata"]["asset_ids"] = merged_asset_ids
```

**Example**:
```
Asset 1: "What is the OS?" (field_id: "operating_system")
Asset 2: "What is the OS?" (field_id: "operating_system")

After Stage 1: "What is the OS?" (applies to: [Asset 1, Asset 2])
```

**Why Bug #10 Showed "0 duplicates"**: This stage only handles cross-asset scenarios. Bug #10 involved within-asset duplicates (same field_id multiple times for ONE asset).

### Stage 2: Within-Asset Deduplication (commands.py flattening)
**Purpose**: Remove duplicate questions within a single asset's questionnaire
**Mechanism**: Filters questions by `field_id` using set membership

**Location**: `backend/app/api/v1/endpoints/collection_crud_questionnaires/commands/start_generation.py:486-511`

**Code**:
```python
# CC FIX Bug #10: Deduplicate questions by field_id at flattening stage
seen_field_ids: Set[str] = set()
deduplicated_questions = []

for question in all_questions:
    field_id = question.get("field_id") or question.get("field_name")

    if field_id in seen_field_ids:
        logger.debug(f"Skipping duplicate question for field_id: {field_id}")
        continue

    seen_field_ids.add(field_id)
    deduplicated_questions.append(question)

if original_count != deduplicated_count:
    logger.info(
        f"Removed {original_count - deduplicated_count} duplicate questions "
        f"during flattening ({original_count} → {deduplicated_count} questions)"
    )
```

**Example**:
```
Asset 1 before Stage 2:
- "What is the business criticality?" (field_id: "business_criticality_score")
- "What is the business criticality?" (field_id: "business_criticality_score") [DUPLICATE]

After Stage 2:
- "What is the business criticality?" (field_id: "business_criticality_score")
```

## Why Both Stages Are Necessary

**Stage 1 Benefits**:
- Optimizes questionnaires for multi-asset scenarios
- Reduces question count (ask once, apply to many)
- Improves user experience
- Maintains referential integrity with `asset_ids` array

**Stage 2 Benefits**:
- Prevents agent errors from reaching users
- Ensures within-asset question uniqueness
- Provides monitoring/logging for quality control
- Catches CrewAI agent duplicate generation

## When to Debug Each Stage

**Stage 1 (Cross-Asset)**:
- Multiple assets selected in flow
- Questions should be asked once for all assets
- `applies_to_count` should be > 1

**Stage 2 (Within-Asset)**:
- Single asset questionnaire has duplicates
- Same `field_id` appears multiple times
- Agent generated redundant questions

## Verification Commands

```bash
# Check cross-asset deduplication
docker exec -it migration_postgres psql -U postgres -d migration_db -c "
SELECT
  q.field_id,
  jsonb_array_length(q.metadata->'asset_ids') as asset_count
FROM migration.adaptive_questionnaires aq,
     jsonb_array_elements(aq.questions) q
WHERE aq.id = 'questionnaire-id'
  AND jsonb_array_length(q.metadata->'asset_ids') > 1;
"

# Check within-asset duplicates
docker exec -it migration_postgres psql -U postgres -d migration_db -c "
SELECT
  COALESCE(q.field_id, q.field_name) AS field,
  COUNT(*) as duplicate_count
FROM migration.adaptive_questionnaires aq,
     jsonb_array_elements(aq.questions) q
WHERE aq.id = 'questionnaire-id'
GROUP BY COALESCE(q.field_id, q.field_name)
HAVING COUNT(*) > 1;
"
```

## Documentation Reference
Full architecture documented in:
`/docs/architecture/QUESTIONNAIRE_DEDUPLICATION_ARCHITECTURE.md`

## Related Memories
- `collection_questionnaire_generation_fix_complete_2025_30` - Earlier generation fixes
- `multi-tenant-questionnaire-deduplication-pattern` - Deduplication scoping
