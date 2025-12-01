# Asset-Based Questionnaire Deduplication - Complete Implementation

**Date**: November 6, 2025
**Context**: Collection Flow Fix #2 - Prevent users from re-answering same questions for same asset across flows
**Status**: ✅ Backend implementation COMPLETE, ready for migration and E2E testing

---

## Problem Statement

**Before**: One questionnaire per `collection_flow_id`
- User selects Asset ABC in Flow A → answers 20 questions
- User creates Flow B, selects Asset ABC again → answers SAME 20 questions
- User creates Flow C, selects Asset ABC again → answers SAME 20 questions **AGAIN**
- Result: Terrible UX, wasted time, data inconsistency

**After**: One questionnaire per `(engagement_id, asset_id)` - cross-flow deduplication
- User selects Asset ABC in Flow A → answers 20 questions
- User creates Flow B, selects Asset ABC → ♻️ REUSES existing questionnaire
- User creates Flow C, selects Asset ABC → ♻️ REUSES existing questionnaire
- Result: Single source of truth, no duplicate data entry

---

## Architecture Decision

### Option A (CHOSEN): Direct FK to assets table
```sql
ALTER TABLE adaptive_questionnaires ADD COLUMN asset_id UUID REFERENCES assets(id);
CREATE UNIQUE INDEX ON (engagement_id, asset_id) WHERE asset_id IS NOT NULL;
```

**Why chosen**:
- ✅ Simple schema (one column, one index)
- ✅ Efficient query: `WHERE engagement_id = X AND asset_id = Y`
- ✅ Backward compatible: `asset_id` nullable during migration
- ✅ Natural multi-tenant isolation via engagement_id

### Option B (REJECTED): Many-to-Many join table
```sql
CREATE TABLE questionnaire_assets (
    questionnaire_id UUID REFERENCES adaptive_questionnaires(id),
    asset_id UUID REFERENCES assets(id),
    PRIMARY KEY (questionnaire_id, asset_id)
);
```

**Why rejected**:
- ❌ Extra table + extra joins
- ❌ More complex queries
- ❌ No significant benefit (one questionnaire per asset is the requirement)

---

## Implementation Files

### 1. Migration: `128_add_asset_id_to_questionnaires.py`

**Key Features**:
- ✅ Idempotent: Uses `DO $ BEGIN ... IF NOT EXISTS ... END $` pattern
- ✅ Partial unique constraint: `WHERE asset_id IS NOT NULL`
- ✅ Backfill logic: Populates `asset_id` for single-asset flows
- ✅ Multi-asset flows skipped: Let user regenerate (cannot determine which asset)
- ✅ Makes `collection_flow_id` nullable for asset-based questionnaires

**Backfill Strategy**:
```sql
FOR questionnaire_record IN
    SELECT q.id, cf.flow_metadata->'selected_asset_ids' as assets
    FROM adaptive_questionnaires q
    JOIN collection_flows cf ON q.collection_flow_id = cf.id
    WHERE q.asset_id IS NULL
LOOP
    IF array_length(assets, 1) = 1 THEN
        UPDATE adaptive_questionnaires SET asset_id = assets[1] WHERE id = questionnaire_record.id;
    ELSE
        -- Skip multi-asset flows (ambiguous which asset)
        RAISE NOTICE 'Skipping questionnaire % (multi-asset flow)', questionnaire_record.id;
    END IF;
END LOOP;
```

### 2. Model: `adaptive_questionnaire_model.py`

**Changes**:
```python
# Flow relationship (nullable for asset-based questionnaires)
collection_flow_id = Column(
    UUID(as_uuid=True),
    ForeignKey("collection_flows.id", ondelete="CASCADE"),
    nullable=True,  # Made nullable per migration 128
    index=True,
)

# Asset relationship (for cross-flow questionnaire deduplication)
asset_id = Column(
    UUID(as_uuid=True),
    ForeignKey("assets.id", ondelete="CASCADE"),
    nullable=True,  # Nullable during migration
    index=True,
)

def to_dict(self):
    return {
        ...
        "asset_id": str(self.asset_id) if self.asset_id else None,  # Added
        ...
    }
```

### 3. Deduplication Logic: `deduplication.py` (NEW FILE)

**Core Functions**:

```python
async def get_existing_questionnaire_for_asset(
    engagement_id: UUID,
    asset_id: UUID,
    db: AsyncSession,
) -> Optional[AdaptiveQuestionnaire]:
    """Check if questionnaire already exists for this asset."""
    result = await db.execute(
        select(AdaptiveQuestionnaire).where(
            AdaptiveQuestionnaire.engagement_id == engagement_id,
            AdaptiveQuestionnaire.asset_id == asset_id,
            AdaptiveQuestionnaire.completion_status != "failed",  # Failed = retry
        )
    )
    return result.scalar_one_or_none()

async def should_reuse_questionnaire(
    questionnaire: AdaptiveQuestionnaire,
) -> tuple[bool, str]:
    """Determine if existing questionnaire should be reused."""
    # completed → REUSE (user already answered)
    # in_progress → REUSE (let user continue)
    # pending → REUSE (generation in progress)
    # ready → REUSE (generated but not answered)
    # failed → REGENERATE (filtered out by caller)
    return True, f"Reusing {questionnaire.completion_status} questionnaire"
```

**Logging Functions** (for audit trail):
- `log_questionnaire_reuse()` - Logs when questionnaire is reused across flows
- `log_questionnaire_creation()` - Logs when new questionnaire is created

### 4. Integration: `commands.py` - Get-or-Create Pattern

**Before** (one questionnaire per flow):
```python
async def _start_agent_generation(...):
    questionnaire_id = uuid4()
    pending_questionnaire = AdaptiveQuestionnaire(
        id=questionnaire_id,
        collection_flow_id=flow.id,  # ← Only flow scoping
        ...
    )
    db.add(pending_questionnaire)
    return [build_questionnaire_response(pending_questionnaire)]
```

**After** (one questionnaire per asset, reused across flows):
```python
async def _start_agent_generation(...):
    from .deduplication import (
        get_existing_questionnaire_for_asset,
        should_reuse_questionnaire,
        log_questionnaire_reuse,
        log_questionnaire_creation,
    )

    # Extract selected_asset_ids from flow metadata
    selected_asset_ids = []
    if flow.flow_metadata and isinstance(flow.flow_metadata, dict):
        raw_ids = flow.flow_metadata.get("selected_asset_ids", [])
        selected_asset_ids = [UUID(aid) if isinstance(aid, str) else aid for aid in raw_ids]

    if not selected_asset_ids:
        logger.warning("No selected_asset_ids, falling back to existing_assets")
        selected_asset_ids = [asset.id for asset in existing_assets]

    questionnaire_responses = []

    for asset_id in selected_asset_ids:
        # Check for existing questionnaire
        existing = await get_existing_questionnaire_for_asset(
            context.engagement_id,
            asset_id,
            db,
        )

        if existing:
            should_reuse, reason = await should_reuse_questionnaire(existing)
            if should_reuse:
                log_questionnaire_reuse(existing, flow.id, asset_id)
                questionnaire_responses.append(
                    collection_serializers.build_questionnaire_response(existing)
                )
                continue  # Skip creation for this asset

        # No existing → create new with asset_id
        log_questionnaire_creation(asset_id, flow.id, "No existing questionnaire")

        questionnaire_id = uuid4()
        pending_questionnaire = AdaptiveQuestionnaire(
            id=questionnaire_id,
            collection_flow_id=flow.id,  # Audit trail: which flow triggered
            asset_id=asset_id,  # ← CRITICAL: Asset-based deduplication key
            ...
        )
        db.add(pending_questionnaire)
        questionnaire_responses.append(
            collection_serializers.build_questionnaire_response(pending_questionnaire)
        )

    return questionnaire_responses  # Can mix reused + newly created
```

### 5. Query Endpoints: `queries.py` + `__init__.py`

**New Function**:
```python
async def get_questionnaire_by_asset(
    engagement_id: UUID,
    asset_id: UUID,
    db: AsyncSession,
    context: RequestContext,
) -> AdaptiveQuestionnaireResponse:
    """Get questionnaire for specific asset (cross-flow lookup)."""
    existing = await get_existing_questionnaire_for_asset(
        engagement_id,
        asset_id,
        db,
    )
    if not existing:
        raise HTTPException(404, "No questionnaire for asset")
    return collection_serializers.build_questionnaire_response(existing)
```

**Exported in `__init__.py`**:
```python
__all__ = [
    "get_adaptive_questionnaires",
    "get_questionnaire_by_asset",  # ← NEW: Asset-based lookup
    "_background_tasks",
]
```

---

## Multi-Asset Flow Handling

**Scenario**: Flow B selects 3 assets (ABC, DEF, GHI)
- Asset ABC: Has existing questionnaire (completed) → ♻️ REUSE
- Asset DEF: Has existing questionnaire (in_progress) → ♻️ REUSE
- Asset GHI: No existing questionnaire → 🆕 CREATE NEW

**Result**: Flow B returns 3 questionnaires:
1. Existing questionnaire for ABC (status: completed, read-only)
2. Existing questionnaire for DEF (status: in_progress, editable)
3. New questionnaire for GHI (status: pending → ready)

**Code**:
```python
for asset_id in selected_asset_ids:
    existing = await get_existing_questionnaire_for_asset(engagement_id, asset_id, db)
    if existing:
        questionnaire_responses.append(build_questionnaire_response(existing))
        continue  # ← Skip creation
    # Create new questionnaire with asset_id
    questionnaire_responses.append(build_questionnaire_response(new_questionnaire))
```

---

## Multi-Tenant Isolation

**Enforcement Point**: Unique constraint on `(engagement_id, asset_id)`

**Why Safe**:
- Same asset in different engagements → SEPARATE questionnaires
- Same asset in different flows (same engagement) → SHARED questionnaire
- No cross-engagement data leakage

**Example**:
- Engagement A: Client XYZ, Asset "Prod-DB-01" → Questionnaire Q1
- Engagement B: Client ABC, Asset "Prod-DB-01" → Questionnaire Q2
- Same asset name, different tenants → Q1 ≠ Q2 (isolated)

---

## Backward Compatibility

### Phase 1: Schema migration (CURRENT)
- `asset_id` is nullable
- Existing questionnaires: `asset_id = NULL`, `collection_flow_id` populated
- New questionnaires: `asset_id` populated, `collection_flow_id` also populated (audit trail)

### Phase 2: Backfill (via migration)
- Single-asset flows: Backfill `asset_id` automatically
- Multi-asset flows: Skipped (user must regenerate)

### Phase 3: Transition period (90 days)
- Queries support both `collection_flow_id` and `asset_id`
- Old frontend: Uses flow-based lookup (still works)
- New frontend: Uses asset-based lookup

### Phase 4: Cleanup (after 90 days)
- Make `asset_id` NOT NULL
- Remove flow-based query endpoints
- Deprecate `collection_flow_id` (keep for audit only)

---

## Testing Scenarios

### Scenario 1: New asset, first time
1. Create Flow A, select Asset ABC
2. Generate questionnaire → `asset_id = ABC`, `completion_status = ready`
3. User answers questions → `completion_status = completed`

### Scenario 2: Same asset, different flow (REUSE)
1. Create Flow B, select Asset ABC
2. System checks: `get_existing_questionnaire_for_asset(engagement_id, ABC)`
3. Found existing with `completion_status = completed`
4. Reuse decision: `should_reuse_questionnaire()` → True
5. Return existing questionnaire (read-only)
6. Log: "♻️ Reusing questionnaire Q1 for asset ABC in flow B"

### Scenario 3: Same asset, partial completion (REUSE in-progress)
1. Create Flow A, select Asset ABC
2. Answer 5/20 questions → `completion_status = in_progress`
3. Create Flow B, select Asset ABC
4. System reuses in-progress questionnaire
5. User continues where they left off (questions 6-20)
6. Complete in Flow B → Both flows show SAME questionnaire as completed

### Scenario 4: Failed questionnaire (REGENERATE)
1. Create Flow A, select Asset ABC
2. Generation fails → `completion_status = failed`
3. Create Flow B, select Asset ABC
4. System checks: `completion_status != "failed"` filter → NO match
5. Creates NEW questionnaire (failed = non-existent)

---

## Frontend Integration (TODO)

### Display Changes Needed:

1. **Questionnaire List View**:
   ```jsx
   {questionnaire.collection_flow_id !== currentFlow.id && (
     <Badge variant="info">♻️ Reused from Flow {originalFlowName}</Badge>
   )}
   ```

2. **Completed Questionnaire**:
   ```jsx
   {questionnaire.completion_status === "completed" && (
     <InfoBox>
       This questionnaire was completed on {questionnaire.completed_at}.
       <Button onClick={handleEdit}>Edit Responses</Button>
     </InfoBox>
   )}
   ```

3. **In-Progress Questionnaire**:
   ```jsx
   {questionnaire.completion_status === "in_progress" && (
     <ProgressBar value={answeredCount / totalCount * 100} />
     <InfoBox>Continue where you left off ({answeredCount}/{totalCount} answered)</InfoBox>
   )}
   ```

### API Calls:

```typescript
// Option 1: Flow-based (backward compatible)
const questionnaires = await apiCall(`/api/collection/questionnaires?flow_id=${flowId}`)

// Option 2: Asset-based (new)
const questionnaire = await apiCall(
  `/api/collection/questionnaires?engagement_id=${engagementId}&asset_id=${assetId}`
)
```

---

## Logging and Audit Trail

**Reuse Event**:
```log
INFO: ♻️ Reusing questionnaire a1b2c3d4 for flow f5e6d7c8:
   Asset: 9a8b7c6d
   Status: completed
   Question Count: 22
   Original Flow: e4f5g6h7
   Created: 2025-11-05 14:30:22
   ✅ User will NOT have to re-answer questions
```

**Creation Event**:
```log
INFO: 🆕 Creating NEW questionnaire for flow f5e6d7c8:
   Asset: 9a8b7c6d
   Reason: No existing questionnaire found
```

---

## Next Steps

### Immediate:
1. **Run migration**: `docker exec migration_backend alembic upgrade head`
2. **Verify schema**: Check `idx_adaptive_questionnaires_engagement_asset` index exists
3. **Test backfill**: Verify single-asset flows have `asset_id` populated

### Short-term:
1. **Frontend**: Implement reuse badge and completion status handling
2. **E2E Test**: Create 2 flows with same asset, verify questionnaire reuse
3. **Metrics**: Track questionnaire reuse rate

### Long-term (90 days):
1. Make `asset_id` NOT NULL
2. Remove flow-based query fallbacks
3. Add dashboard: "Questionnaire Reuse Rate" metric

---

## Key Learnings

### What Worked:
- ✅ **Partial unique constraints** allow gradual migration
- ✅ **Get-or-create pattern** is clean and testable
- ✅ **Multi-asset loop** handles mixed reuse + creation elegantly
- ✅ **Logging functions** provide excellent audit trail

### What to Watch:
- ⚠️ **Concurrent edits**: Last write wins (acceptable for now)
- ⚠️ **Multi-asset flows**: Backfill skipped (user must regenerate)
- ⚠️ **Rollback complexity**: Need to restore `collection_flow_id` NOT NULL

### Anti-Patterns Avoided:
- ❌ **NOT** using many-to-many (over-engineering)
- ❌ **NOT** forcing immediate migration (backward compat preserved)
- ❌ **NOT** duplicating questionnaires on reuse (single source of truth)

---

**Reference**: COLLECTION_FLOW_FIXES_STATUS.md - Fix #2
