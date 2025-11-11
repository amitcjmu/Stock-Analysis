# Status Filter Exclusion Pattern for Flow Lifecycle States

**Date**: November 6, 2025
**Context**: Collection flow form submission 404 error resolution

---

## Problem

Form submission returned 404 after completion because `COMPLETED` flows were excluded from status queries, preventing assessment transition workflow.

## Root Cause

Status filter treated COMPLETED/CANCELLED/FAILED as equivalent "ended" states:
```python
# WRONG: All "ended" states treated the same
CollectionFlow.status.notin_([
    CollectionFlowStatus.COMPLETED.value,
    CollectionFlowStatus.CANCELLED.value,
    CollectionFlowStatus.FAILED.value,
])
```

But these states have different semantics:
- **COMPLETED**: Successfully finished, needs to be queryable for next phase (assessment transition)
- **CANCELLED**: User aborted, should not be queryable
- **FAILED**: System error, should not be queryable

## Solution

Separate exclusion lists with parameter control:

```python
# backend/app/api/v1/endpoints/collection_crud_queries/status.py
async def get_collection_flow(
    flow_id: str,
    db: AsyncSession,
    current_user: User,
    context: RequestContext,
    include_completed: bool = True,  # Defaults to True for backward compat
) -> CollectionFlowResponse:
    """Get collection flow by ID.

    Args:
        include_completed: If True, allows querying COMPLETED flows (for assessment transition).
                          If False, excludes COMPLETED (for active flow lists).
    """
    # Build status exclusion list based on semantic requirements
    excluded_statuses = [
        CollectionFlowStatus.CANCELLED.value,  # Always exclude
        CollectionFlowStatus.FAILED.value,      # Always exclude
    ]

    if not include_completed:
        excluded_statuses.append(CollectionFlowStatus.COMPLETED.value)

    result = await db.execute(
        select(CollectionFlow).where(
            (CollectionFlow.flow_id == flow_uuid) | (CollectionFlow.id == flow_uuid),
            CollectionFlow.engagement_id == context.engagement_id,
            CollectionFlow.status.notin_(excluded_statuses),
        )
    )
    return result.scalar_one_or_none()
```

## Usage Pattern

**Default behavior** (most common case):
```python
# Allow querying completed flows for assessment transition
flow = await get_collection_flow(flow_id, db, user, context)  # include_completed=True (default)
```

**Active flows only** (for "in-progress" lists):
```python
# Exclude completed flows from active workflow lists
active_flows = await get_collection_flow(flow_id, db, user, context, include_completed=False)
```

## Key Principle

**Flow states require semantic differentiation** - not all terminal states should be excluded from queries.

Decision matrix:
- **COMPLETED** → Queryable (allows workflow progression to next phase)
- **CANCELLED** → Never queryable (user intentionally aborted)
- **FAILED** → Never queryable (system error, cannot progress)
- **PAUSED** → Queryable (waiting for user input, resumable)

## When to Apply

- Any workflow system with terminal states
- Post-completion access requirements vary by state type
- Need backward-compatible status filtering
- Multi-phase workflows requiring cross-phase queries

## Related Patterns

- **Validators** can still block execution of completed flows (separate concern)
- **Lifecycle hooks** determine state transitions
- **ADR-012** defines flow status vs phase separation

## Files

- `backend/app/api/v1/endpoints/collection_crud_queries/status.py:76-122`
- Related: `collection_validators.py` (execution validators)
