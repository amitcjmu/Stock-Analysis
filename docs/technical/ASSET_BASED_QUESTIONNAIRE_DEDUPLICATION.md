# Asset-Based Questionnaire Deduplication Design

**Date**: November 6, 2025
**Status**: Implementation in Progress
**Branch**: `fix/collection-flow-issues-20251106`

---

## Problem Statement

**Current Architecture**: Questionnaires are 1:1 with `collection_flow_id`
- Each collection flow generates its own questionnaire
- If Asset ABC is selected in 3 different collection flows, user answers the same questions 3 times
- No reuse across flows for the same asset

**User Requirement**:
> "Questionnaires should be associated to the context-based asset, not repeated with every collection flow"

---

## Current Schema

```sql
-- adaptive_questionnaires table
CREATE TABLE migration.adaptive_questionnaires (
    id UUID PRIMARY KEY,
    client_account_id UUID NOT NULL,
    engagement_id UUID NOT NULL,
    collection_flow_id UUID NOT NULL,  -- ❌ 1:1 relationship
    questions JSONB NOT NULL,
    completion_status VARCHAR(50) NOT NULL DEFAULT 'pending',
    responses_collected JSONB NOT NULL DEFAULT '{}',
    ...
    FOREIGN KEY (collection_flow_id) REFERENCES migration.collection_flows(id) ON DELETE CASCADE
);
```

**Problem**: No `asset_id` column, questionnaires tied to flows, not assets.

---

## Proposed Schema Changes

### Option A: Direct Asset Foreign Key (Simplest)

```sql
ALTER TABLE migration.adaptive_questionnaires
ADD COLUMN asset_id UUID REFERENCES migration.assets(id) ON DELETE CASCADE;

-- Composite unique constraint: One questionnaire per (engagement, asset)
ALTER TABLE migration.adaptive_questionnaires
ADD CONSTRAINT uq_questionnaire_per_asset_per_engagement
UNIQUE (engagement_id, asset_id);

-- Make collection_flow_id nullable (for backward compat during migration)
ALTER TABLE migration.adaptive_questionnaires
ALTER COLUMN collection_flow_id DROP NOT NULL;
```

**Advantages**:
- Simple schema
- Direct asset lookup
- Deduplication enforced by unique constraint

**Disadvantages**:
- Breaks existing 1:1 flow relationship
- Need migration strategy for existing questionnaires

### Option B: Many-to-Many Join Table (More Flexible)

```sql
-- Keep adaptive_questionnaires keyed by asset_id
ALTER TABLE migration.adaptive_questionnaires
ADD COLUMN asset_id UUID NOT NULL REFERENCES migration.assets(id) ON DELETE CASCADE,
ALTER COLUMN collection_flow_id DROP NOT NULL;

-- New join table to track which flows use which questionnaires
CREATE TABLE migration.collection_flow_questionnaires (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    collection_flow_id UUID NOT NULL REFERENCES migration.collection_flows(id) ON DELETE CASCADE,
    questionnaire_id UUID NOT NULL REFERENCES migration.adaptive_questionnaires(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_flow_questionnaire UNIQUE (collection_flow_id, questionnaire_id)
);

-- Index for reverse lookups
CREATE INDEX idx_flow_questionnaires_flow ON migration.collection_flow_questionnaires(collection_flow_id);
CREATE INDEX idx_flow_questionnaires_questionnaire ON migration.collection_flow_questionnaires(questionnaire_id);
```

**Advantages**:
- Explicit many-to-many relationship
- Can track which flows use which questionnaires
- Audit trail of questionnaire usage

**Disadvantages**:
- More complex queries
- Additional join table to maintain

---

## Recommended Approach: **Option A with Migration Strategy**

### Migration Steps

#### 1. Add asset_id column (nullable for backward compat)
```sql
ALTER TABLE migration.adaptive_questionnaires
ADD COLUMN asset_id UUID REFERENCES migration.assets(id) ON DELETE CASCADE;
```

#### 2. Backfill asset_id for existing questionnaires
```python
# For each existing questionnaire:
# - Look up collection_flow.flow_metadata['selected_asset_ids']
# - If only one asset selected, set asset_id
# - If multiple assets, SKIP (let user re-generate)
```

#### 3. Add unique constraint (after backfill)
```sql
ALTER TABLE migration.adaptive_questionnaires
ADD CONSTRAINT uq_questionnaire_per_asset_per_engagement
UNIQUE (engagement_id, asset_id)
WHERE asset_id IS NOT NULL;  -- Partial unique index
```

#### 4. Update questionnaire generation logic
```python
async def get_or_create_questionnaire(
    engagement_id: UUID,
    asset_id: UUID,
    collection_flow_id: UUID,  # For backward compat
    db: AsyncSession
) -> AdaptiveQuestionnaire:
    # Check if questionnaire already exists for this asset
    existing = await db.execute(
        select(AdaptiveQuestionnaire).where(
            AdaptiveQuestionnaire.engagement_id == engagement_id,
            AdaptiveQuestionnaire.asset_id == asset_id,
            AdaptiveQuestionnaire.completion_status != "failed"
        )
    )
    questionnaire = existing.scalar_one_or_none()

    if questionnaire:
        logger.info(f"Reusing existing questionnaire {questionnaire.id} for asset {asset_id}")
        return questionnaire

    # Generate new questionnaire for this asset
    questionnaire = AdaptiveQuestionnaire(
        engagement_id=engagement_id,
        asset_id=asset_id,
        collection_flow_id=collection_flow_id,  # Keep for now
        ...
    )
    db.add(questionnaire)
    await db.commit()
    return questionnaire
```

---

## Frontend Impact

### Current Flow
```typescript
// Fetch questionnaires by collection_flow_id
const { data } = useQuery({
  queryKey: ["questionnaires", flowId],
  queryFn: () => apiCall(`/collection/flows/${flowId}/questionnaires`)
});
```

### New Flow
```typescript
// Fetch questionnaires by asset_id (or still by flow_id for backward compat)
const { data } = useQuery({
  queryKey: ["questionnaires", flowId, selectedAssetId],
  queryFn: () => apiCall(`/collection/questionnaires?engagement_id=${engagementId}&asset_id=${selectedAssetId}`)
});
```

**Backward Compatibility**: Keep flow-based endpoint as fallback:
- If `asset_id` in questionnaire, use asset-based query
- If `asset_id` is NULL (legacy), use flow-based query

---

## UX Changes

### Before (Current)
1. User creates Collection Flow A, selects Asset ABC
2. System generates Questionnaire 1 for Flow A
3. User answers 10 questions
4. User creates Collection Flow B, selects Asset ABC **again**
5. System generates Questionnaire 2 for Flow B
6. User answers **THE SAME 10 QUESTIONS AGAIN** ❌

### After (Proposed)
1. User creates Collection Flow A, selects Asset ABC
2. System checks: "Does Asset ABC already have a questionnaire?"
   - NO → Generate Questionnaire 1, link to Asset ABC
3. User answers 10 questions
4. User creates Collection Flow B, selects Asset ABC **again**
5. System checks: "Does Asset ABC already have a questionnaire?"
   - **YES** → Reuse Questionnaire 1 ✅
6. User sees **ALREADY COMPLETED** status (or can update answers)

---

## Edge Cases

### 1. Questionnaire Already Completed
**Scenario**: Flow A completed questionnaire for Asset ABC. Flow B selects Asset ABC.

**Solution**: Show questionnaire in read-only mode with "Edit" button
- User can review existing answers
- User can click "Edit" to update if data changed

### 2. Questionnaire In Progress
**Scenario**: Flow A has incomplete questionnaire for Asset ABC. Flow B selects Asset ABC.

**Solution**: Allow concurrent editing (optimistic locking)
- Show warning: "Another flow is collecting data for this asset"
- Last write wins (or implement conflict resolution)

### 3. Failed Questionnaire
**Scenario**: Flow A failed to generate questionnaire for Asset ABC. Flow B selects Asset ABC.

**Solution**: Retry generation
- Treat `completion_status='failed'` as non-existent
- Generate new questionnaire

### 4. Different Engagement Context
**Scenario**: Engagement X has Asset ABC. Engagement Y imports Asset ABC (shared asset).

**Solution**: **Separate questionnaires per engagement**
- Unique constraint: `(engagement_id, asset_id)`
- Same asset in different engagements = different compliance/business context

---

## Implementation Checklist

- [ ] Create Alembic migration for schema changes
- [ ] Add asset_id column (nullable)
- [ ] Backfill asset_id for existing questionnaires (data migration)
- [ ] Update `adaptive_questionnaire_model.py` with asset_id field
- [ ] Modify questionnaire generation logic (get_or_create pattern)
- [ ] Update queries to check for existing questionnaires by asset_id
- [ ] Add unique constraint `(engagement_id, asset_id)`
- [ ] Update frontend to handle asset-based questionnaire lookups
- [ ] Add UI indicator for "questionnaire reused" vs "newly generated"
- [ ] Write integration tests for deduplication logic
- [ ] Document in user guide: "Questionnaires are per-asset, not per-flow"

---

## Testing Plan

### Unit Tests
```python
async def test_questionnaire_deduplication():
    # Create Flow A with Asset ABC
    flow_a = create_collection_flow(selected_assets=[asset_abc_id])
    q1 = await get_or_create_questionnaire(engagement_id, asset_abc_id, flow_a.id)

    # Create Flow B with same Asset ABC
    flow_b = create_collection_flow(selected_assets=[asset_abc_id])
    q2 = await get_or_create_questionnaire(engagement_id, asset_abc_id, flow_b.id)

    # Should return SAME questionnaire
    assert q1.id == q2.id
```

### Integration Tests
```python
async def test_cross_flow_questionnaire_persistence():
    # Complete questionnaire in Flow A
    await submit_questionnaire_responses(flow_a_id, asset_abc_id, responses)

    # Query questionnaire from Flow B
    questionnaire = await get_questionnaire(flow_b_id, asset_abc_id)

    # Should show completed with responses from Flow A
    assert questionnaire.completion_status == "completed"
    assert questionnaire.responses_collected == responses
```

---

## Rollout Strategy

### Phase 1: Schema Migration (Non-Breaking)
1. Add `asset_id` column (nullable)
2. Backfill asset_id for single-asset flows
3. Deploy with feature flag OFF

### Phase 2: Enable Deduplication Logic
1. Update questionnaire generation to check for existing by asset_id
2. Enable feature flag for new flows only (old flows use legacy path)
3. Monitor for issues

### Phase 3: Cleanup Legacy
1. After 90 days, deprecate flow-based questionnaire lookup
2. Make `asset_id` NOT NULL (after all questionnaires have it)
3. Remove `collection_flow_id` foreign key (keep column for audit)

---

## Security Considerations

### Multi-Tenant Isolation
- Always scope queries by `engagement_id` AND `asset_id`
- Never allow cross-engagement questionnaire access
- Asset ACLs: Ensure user has permission to view asset before showing questionnaire

### Data Privacy
- Questionnaire responses may contain sensitive data (compliance, business criticality)
- Reusing questionnaires means multiple flows see same responses
- **This is DESIRED behavior** - avoids duplicate data entry

---

## Next Steps

1. **Create Alembic Migration**: Add `asset_id` column
2. **Implement get_or_create Logic**: Check for existing questionnaire by asset_id
3. **Update Frontend**: Handle asset-based questionnaire display
4. **Test End-to-End**: Verify deduplication works across flows
5. **Document**: Update user guide with new behavior

---

**Decision**: Proceeding with **Option A** - Direct asset_id foreign key with partial unique constraint.
