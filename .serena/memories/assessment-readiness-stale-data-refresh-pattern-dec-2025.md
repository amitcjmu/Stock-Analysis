# Assessment Readiness Stale Data Refresh Pattern - December 2025

## Problem
Pre-computed `application_asset_groups` in AssessmentFlow table contains stale `readiness_summary` cached at flow creation time. This causes UI to show "0 ready / 0 blocked" despite database having correct asset readiness values.

## Root Cause
API uses cached application groups from DB without refreshing from current asset state.

## Solution: Refresh Helper Function

```python
# backend/app/api/v1/master_flows/assessment/info_endpoints/readiness_utils.py
async def refresh_readiness_for_groups(
    db: AsyncSession,
    application_groups: list,
    client_account_id: Any,
    engagement_id: Any,
) -> list:
    """Refresh readiness_summary from current asset state."""
    # Collect all asset IDs from groups
    all_asset_ids = set()
    for group in application_groups:
        all_asset_ids.update(group.get("asset_ids", []))

    # Query current asset readiness state (CRITICAL: multi-tenant scoping)
    stmt = select(Asset).where(
        Asset.id.in_([UUID(aid) for aid in all_asset_ids]),
        Asset.client_account_id == UUID(client_account_id),
        Asset.engagement_id == UUID(engagement_id),
    )
    result = await db.execute(stmt)
    assets = {str(a.id): a for a in result.scalars().all()}

    # Recalculate readiness_summary per group
    for group in application_groups:
        ready = not_ready = 0
        for aid in group.get("asset_ids", []):
            asset = assets.get(str(aid))
            if asset and asset.assessment_readiness == "ready":
                ready += 1
            else:
                not_ready += 1
        group["readiness_summary"] = {"ready": ready, "not_ready": not_ready}

    return application_groups
```

## Usage in Endpoint

```python
# In queries.py
if flow.application_asset_groups:
    application_groups = await refresh_readiness_for_groups(
        db, flow.application_asset_groups,
        context.client_account_id, context.engagement_id
    )
```

## Related Fix: Pydantic Gap Report Objects

**Problem**: `build_ready_report()` passing empty lists to fields expecting Pydantic objects.

```python
# WRONG - Validation error
column_gaps=[]

# CORRECT - Proper Pydantic objects
column_gaps = ColumnGapReport(
    missing_attributes=[], empty_attributes=[],
    null_attributes=[], completeness_score=1.0
)
```

## Qodo Bot Fix: Explicit None Check for Zero Score

**Problem**: `score or 0.85` treats `0.0` as falsy.

```python
# WRONG
overall_completeness = float(getattr(asset, "score", 0.85) or 0.85)

# CORRECT
score = getattr(asset, "assessment_readiness_score", None)
overall_completeness = float(score if score is not None else 0.85)
```

## Qodo Bot Fix: Explicit Readiness Status Filter

**Problem**: `!== 'ready'` captures unknown statuses.

```typescript
// WRONG
.filter((a) => a.assessment_readiness !== 'ready')

// CORRECT - explicit statuses
.filter((a) =>
  a.assessment_readiness === 'not_ready' ||
  a.assessment_readiness === 'in_progress'
)
```

## Key Files
- `backend/app/api/v1/master_flows/assessment/info_endpoints/readiness_utils.py` (NEW)
- `backend/app/api/v1/master_flows/assessment/info_endpoints/analysis_queries.py` (NEW)
- `backend/app/services/assessment/readiness_helpers.py` (NEW)
- `src/components/assessment/shared/ApplicationGroupCard.tsx`

## PR Reference
PR #1215 - fix/assessment-readiness-display-ux
