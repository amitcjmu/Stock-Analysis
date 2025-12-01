# Asset-Based Questionnaire Deduplication - Schema Migration Pattern

**Date**: November 6, 2025
**Context**: Users answering same questions multiple times across collection flows

---

## Problem

Questionnaires were 1:1 with `collection_flow_id` → same asset selected in 3 different flows = user answers same 10 questions 3 times.

## Architecture Decision

**Questionnaires should be per-asset, not per-flow** (shared across flows within same engagement).

## Schema Migration Strategy

### 1. Add asset_id Column (Nullable for Backward Compatibility)

```sql
-- backend/alembic/versions/128_add_asset_id_to_questionnaires.py
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'migration'
        AND table_name = 'adaptive_questionnaires'
        AND column_name = 'asset_id'
    ) THEN
        -- Add column
        ALTER TABLE migration.adaptive_questionnaires
        ADD COLUMN asset_id UUID;

        -- Add foreign key
        ALTER TABLE migration.adaptive_questionnaires
        ADD CONSTRAINT fk_adaptive_questionnaires_asset_id
        FOREIGN KEY (asset_id) REFERENCES migration.assets(id) ON DELETE CASCADE;

        -- Add index for lookups
        CREATE INDEX idx_adaptive_questionnaires_asset_id
        ON migration.adaptive_questionnaires(asset_id)
        WHERE asset_id IS NOT NULL;
    END IF;
END $$;
```

### 2. Make collection_flow_id Nullable

```sql
-- Flows can now share questionnaires
ALTER TABLE migration.adaptive_questionnaires
ALTER COLUMN collection_flow_id DROP NOT NULL;
```

### 3. Add Partial Unique Constraint

**Key Pattern**: `WHERE asset_id IS NOT NULL` allows gradual migration

```sql
CREATE UNIQUE INDEX uq_questionnaire_per_asset_per_engagement
ON migration.adaptive_questionnaires(engagement_id, asset_id)
WHERE asset_id IS NOT NULL;  -- Partial index: only enforces when populated
```

**Why Partial**:
- Existing questionnaires have `asset_id = NULL` during migration
- New questionnaires get `asset_id` populated
- Constraint only applies to new records
- Allows gradual backfill without conflicts

### 4. Backfill Existing Questionnaires

**Conservative Strategy**: Only backfill single-asset flows

```sql
DO $$
DECLARE
    questionnaire_record RECORD;
    selected_assets UUID[];
BEGIN
    FOR questionnaire_record IN
        SELECT q.id, q.collection_flow_id, cf.flow_metadata
        FROM migration.adaptive_questionnaires q
        JOIN migration.collection_flows cf ON q.collection_flow_id = cf.id
        WHERE q.asset_id IS NULL
    LOOP
        -- Extract selected_asset_ids from JSON
        selected_assets := ARRAY(
            SELECT jsonb_array_elements_text(
                questionnaire_record.flow_metadata->'selected_asset_ids'
            )::UUID
        );

        -- Only backfill if exactly ONE asset
        IF array_length(selected_assets, 1) = 1 THEN
            UPDATE migration.adaptive_questionnaires
            SET asset_id = selected_assets[1]
            WHERE id = questionnaire_record.id;
        ELSE
            -- Skip multi-asset flows (let user regenerate)
            RAISE NOTICE 'Skipping multi-asset flow: %', questionnaire_record.id;
        END IF;
    END LOOP;
END $$;
```

## Deduplication Logic

### Get-or-Create Pattern

```python
# backend/app/api/v1/endpoints/collection_crud_questionnaires/deduplication.py

async def get_existing_questionnaire_for_asset(
    engagement_id: UUID,
    asset_id: UUID,
    db: AsyncSession,
) -> Optional[AdaptiveQuestionnaire]:
    """Check if questionnaire already exists for this asset in this engagement."""
    result = await db.execute(
        select(AdaptiveQuestionnaire).where(
            AdaptiveQuestionnaire.engagement_id == engagement_id,
            AdaptiveQuestionnaire.asset_id == asset_id,
            AdaptiveQuestionnaire.completion_status != "failed",  # Retry on failure
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        logger.info(f"♻️ Reusing questionnaire {existing.id} for asset {asset_id}")
    return existing
```

### Integration at Creation Point

```python
# Before creating new questionnaire:
existing = await get_existing_questionnaire_for_asset(
    context.engagement_id,
    asset_id,
    db
)

if existing:
    should_reuse, reason = await should_reuse_questionnaire(existing)
    if should_reuse:
        log_questionnaire_reuse(existing, flow.id, asset_id)
        return [build_questionnaire_response(existing)]  # Reuse

# Only create new if no existing found
pending_questionnaire = AdaptiveQuestionnaire(
    engagement_id=context.engagement_id,
    asset_id=asset_id,  # NEW: Link to asset
    collection_flow_id=flow.id,  # Keep for audit trail
    ...
)
```

## Reuse Decision Matrix

```python
def should_reuse_questionnaire(q: AdaptiveQuestionnaire) -> tuple[bool, str]:
    """Determine if existing questionnaire should be reused."""
    status = q.completion_status

    if status == "completed":
        return True, "User already answered - reusing responses"

    if status == "in_progress":
        return True, "Let user continue where they left off"

    if status == "pending":
        return True, "Generation in progress - reusing pending record"

    if status == "ready":
        return True, "Generated but not answered - reusing questions"

    # "failed" filtered out by caller - triggers regeneration
```

## Multi-Tenant Scoping

**Critical**: Unique constraint is per `(engagement_id, asset_id)`, NOT globally

**Rationale**: Same asset in different engagements has different business context
- Engagement A: Asset ABC for financial migration (HIPAA compliance)
- Engagement B: Asset ABC for infrastructure audit (no compliance)

## Rollout Strategy

### Phase 1: Schema Migration (Non-Breaking)
1. Add `asset_id` column (nullable)
2. Backfill single-asset flows
3. Deploy with feature flag OFF

### Phase 2: Enable Deduplication
1. Update questionnaire generation to use get-or-create
2. Enable for new flows only (old flows use legacy path)
3. Monitor reuse metrics

### Phase 3: Cleanup (90 days later)
1. Make `asset_id` NOT NULL (after all questionnaires have it)
2. Remove `collection_flow_id` FK (keep column for audit)

## Key Patterns

### Partial Unique Constraints for Gradual Migration
```sql
CREATE UNIQUE INDEX name ON table(col1, col2)
WHERE col2 IS NOT NULL;  -- Only enforces when populated
```

### Conservative Backfill Logic
- Skip edge cases (multi-asset flows)
- Use `RAISE NOTICE` for audit trail
- Don't fail migration on backfill errors

### Nullable FKs During Transition
- Old records: `collection_flow_id NOT NULL, asset_id NULL`
- New records: `collection_flow_id NULL, asset_id NOT NULL`
- Both valid during migration

## Files

- Migration: `backend/alembic/versions/128_add_asset_id_to_questionnaires.py`
- Model: `backend/app/models/collection_flow/adaptive_questionnaire_model.py:65-70`
- Logic: `backend/app/api/v1/endpoints/collection_crud_questionnaires/deduplication.py`
- Design: `/docs/technical/ASSET_BASED_QUESTIONNAIRE_DEDUPLICATION.md`

## When to Apply

- Cross-workflow resource deduplication
- Multi-tenant systems with shared resources
- Gradual schema migrations requiring backward compatibility
- Forms/questionnaires that should persist across sessions
