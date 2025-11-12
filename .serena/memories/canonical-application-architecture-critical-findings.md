# Canonical Application Architecture - Critical Findings (Bug #999)

**Date**: 2025-11-12
**Context**: Bug #999 investigation revealed critical architectural gap in canonical application system
**Impact**: 82% of assets orphaned, 6R recommendations not persisting

## Critical Architectural Gap

### The Problem
Two separate code paths for collection flows with **different behaviors**:

#### Path 1: Bulk CSV Import ✅ WORKS
**File**: `backend/app/api/v1/endpoints/collection_bulk_import.py:79-203`

Flow:
1. Asset created with `application_name`
2. `CanonicalApplication.find_or_create_canonical()` called → Deduplication
3. `CollectionFlowApplication` junction record created
4. Links: `asset_id` → `canonical_application_id`

#### Path 2: Questionnaire Submission ❌ BROKEN
**File**: `backend/app/api/v1/endpoints/collection_crud_update_commands/questionnaire_submission.py`

Flow:
1. Asset.application_name updated (via `apply_asset_writeback()`)
2. ❌ **NEVER** calls `find_or_create_canonical()`
3. ❌ **NEVER** creates junction record
4. Asset orphaned - no link to canonical app

### Evidence
```sql
-- Test tenant (client_account_id: 11111111-1111-1111-1111-111111111111)
Total assets: 134
Assets with junction records: 24 (18%)
Orphaned assets: 110 (82%)
```

**Impact**: Assessment flows cannot map 6R recommendations to assets because junction table lookup returns empty.

## Race Condition in Canonical App Creation

### The Bug
**File**: `backend/app/models/canonical_applications/canonical_application.py:179-245`

**Problem**: Multiple concurrent collection flows can create duplicate canonical apps.

**Scenario**:
```python
# Flow A checks for "SAP ERP" → Not found
# Flow B checks for "SAP ERP" → Not found
# Flow A inserts "SAP ERP" → Success
# Flow B inserts "SAP ERP" → IntegrityError (violates UNIQUE constraint)
```

**Current Handling** (WRONG):
```python
except Exception as canon_error:
    logger.error(f"Failed canonical deduplication: {canon_error}")
    # Don't fail the entire import - continue with next asset ← WRONG!
```

Result: Asset imported WITHOUT junction record → Orphaned

### The Fix
Add retry logic with up to 3 attempts:
```python
for attempt in range(3):
    try:
        # Try SELECT
        existing = await db.execute(select(cls).where(...))
        if existing:
            return existing

        # Try INSERT
        new_canonical = cls(...)
        db.add(new_canonical)
        await db.commit()
        return new_canonical

    except IntegrityError as e:
        await db.rollback()
        if "uq_canonical_apps_tenant_name" in str(e):
            continue  # Race condition - retry SELECT
        else:
            raise
```

## Junction Table Architecture

### Design (CORRECT)

```
Assets Table (application_name field)
         ↓ (linked via)
collection_flow_applications (junction table)
         ├─ asset_id (FK → assets.id)
         ├─ collection_flow_id (FK → collection_flows.id, NOT NULL)
         ├─ canonical_application_id (FK → canonical_applications.id)
         ├─ deduplication_method (audit: 'bulk_import', 'questionnaire_auto', 'migration_backfill')
         ├─ match_confidence (deduplication confidence score)
         └─ collection_status (pending/validated/rejected)
                  ↓ (points to)
    canonical_applications (master registry)
         ├─ normalized_name (UNIQUE per tenant - deduplication key)
         ├─ name_hash (MD5 of normalized_name for exact matching)
         └─ name_embedding (vector(384) for fuzzy matching)
```

### Why Junction Table (Not Direct FK)?

1. **Audit Trail**: Tracks WHICH collection flow performed the mapping
2. **Deduplication Metadata**: Method, confidence, timestamp preserved
3. **Separation of Concerns**: Assets exist before canonicalization
4. **Multi-Flow Support**: Same asset can be processed by multiple flows (each gets junction record)
5. **Flexible Mapping**: Supports one-to-many (one canonical app → multiple assets)

### Database Constraints
```sql
-- NO UNIQUE constraint on asset_id (intentional - allows multiple flows per asset)
-- UNIQUE constraint on (client_account_id, engagement_id, normalized_name) in canonical_applications
--   → This is WHY race conditions matter (second INSERT fails)
```

## Assessment Flow Application Groups

### Current Implementation
**File**: `backend/app/services/assessment/application_resolver.py:96-238`

**Query**:
```sql
SELECT
  Asset.id,
  CollectionFlowApplication.canonical_application_id,
  CanonicalApplication.canonical_name
FROM assets
LEFT JOIN collection_flow_applications ON assets.id = collection_flow_applications.asset_id
LEFT JOIN canonical_applications ON collection_flow_applications.canonical_application_id = canonical_applications.id
WHERE assets.id IN (selected_asset_ids)
```

**Logic**:
```python
if junction_record_exists:
    group_by_canonical_app_id  # Create application_asset_groups
else:
    treat_as_unmapped  # Creates "unmapped-{asset_id}" group
```

**Storage** (`assessment_flows.application_asset_groups`):
```json
[{
  "canonical_application_id": "uuid",
  "canonical_application_name": "Analytics Engine",
  "asset_ids": ["uuid1", "uuid2"],  ← Multiple assets per canonical app
  "asset_count": 2,
  "confidence_score": 1.0
}]
```

**When It Works**:
- ✅ Bulk import path (has junction records)
- ❌ Questionnaire path (NO junction records) ← **Bug #999**

## Bug #999 Root Cause Chain

1. User fills questionnaire → application_name = "Analytics Engine"
2. Questionnaire path updates `Asset.application_name` ✅
3. BUT questionnaire path **SKIPS** canonical app creation ❌
4. No junction record created ❌
5. Assessment flow queries junction table → Empty result ❌
6. Assessment flow creates "unmapped-{asset_id}" groups
7. 6R recommendation agent generates:
   ```json
   {
     "application_id": "canonical-app-uuid",
     "application_name": "Analytics Engine",
     "six_r_strategy": "replatform"
   }
   ```
8. `_update_assets_with_recommendations()` tries to update by `application_name` ❌
9. SQL: `UPDATE assets WHERE application_name = 'Analytics Engine'` → 0 rows (mismatch or empty field)
10. Result: `assets_updated_count: 0` ❌

**Fix Required**: Use junction table for reliable asset_id lookup (Phase 3).

## Data Migration Challenge

### The Constraint Problem
`collection_flow_applications.collection_flow_id` is **NOT NULL** (FK constraint).

**Issue**: 110 orphaned assets need junction records, but they may not have an associated collection flow.

### Solution: "System Migration" Collection Flow
```sql
-- Create special collection flow for backfilled assets
INSERT INTO migration.collection_flows (
    id,
    flow_name,
    status,
    ...
) VALUES (
    gen_random_uuid(),
    'System Migration - Canonical App Backfill',
    'completed',
    ...
);

-- Use this flow_id for all backfilled junction records
INSERT INTO migration.collection_flow_applications (
    collection_flow_id,  ← Points to System Migration flow
    asset_id,
    canonical_application_id,
    deduplication_method,  ← 'migration_backfill' for audit trail
    ...
)
```

**Benefits**:
- Preserves referential integrity (NOT NULL constraint satisfied)
- Audit trail preserved (can identify backfilled vs real collection flow)
- Idempotent (can be run multiple times)
- Reversible (downgrade deletes `WHERE deduplication_method = 'migration_backfill'`)

## Testing Strategy

### Critical Test Cases

1. **Race Condition Handling**:
   ```python
   # Start 10 concurrent flows creating "SAP ERP"
   tasks = [find_or_create_canonical("SAP ERP") for _ in range(10)]
   results = await asyncio.gather(*tasks)

   # Assert: Exactly 1 canonical app created, 9 found existing
   # Assert: No IntegrityErrors propagated
   ```

2. **Questionnaire → Assessment Flow**:
   ```python
   # Submit questionnaire with application_name
   # Verify: Junction record created
   # Create assessment flow
   # Verify: Application appears in application_asset_groups
   ```

3. **Data Migration Idempotency**:
   ```python
   # Run migration twice
   # Verify: Same number of junction records (no duplicates)
   # Verify: All orphaned assets now have canonical apps
   ```

## Implementation Checklist

- [ ] Phase 1: Add retry logic to `find_or_create_canonical()` (4 hours)
- [ ] Phase 2: Add canonicalization to questionnaire submission (6 hours)
- [ ] Phase 3: Update asset update logic to use junction table (8 hours)
- [ ] Phase 4: Create data migration script with System Migration flow (4 hours)
- [ ] Write unit tests for race conditions (2 hours)
- [ ] Write integration tests for questionnaire → assessment flow (2 hours)
- [ ] E2E test: collection flow → assessment flow → 6R persist (2 hours)
- [ ] Documentation: Update ADR-036 with findings (DONE)

**Total Estimated Effort**: 28 hours (~3.5 days)

## Key Files Reference

**Models**:
- `backend/app/models/canonical_applications/canonical_application.py` - CanonicalApplication model
- `backend/app/models/canonical_applications/collection_flow_app.py` - CollectionFlowApplication junction table

**Bulk Import** (works correctly):
- `backend/app/api/v1/endpoints/collection_bulk_import.py:79-203`

**Questionnaire** (broken):
- `backend/app/api/v1/endpoints/collection_crud_update_commands/questionnaire_submission.py`
- `backend/app/api/v1/endpoints/collection_crud_update_commands/questionnaire_helpers.py:229-276`
- `backend/app/services/flow_configs/collection_handlers/asset_handlers.py:157-365`

**Assessment Resolution**:
- `backend/app/services/assessment/application_resolver.py:65-238`

**Asset Update** (needs fix):
- `backend/app/services/flow_orchestration/execution_engine_crew_assessment/recommendation_executor_asset_update.py`

## Related ADRs

- **ADR-036**: Canonical Application Junction Table Architecture (this ADR)
- **ADR-034**: Asset-Centric Questionnaire Deduplication
- **ADR-012**: Flow Status Management Separation

## Lessons Learned

1. **Always check both code paths**: Bulk import worked, questionnaire didn't
2. **Race conditions in distributed systems**: Concurrent flows need retry logic
3. **Data migration planning**: NOT NULL constraints require creative solutions
4. **Junction tables are intentional**: Don't bypass with direct FK
5. **Deduplication is critical**: 82% orphaned assets shows importance of canonical apps
