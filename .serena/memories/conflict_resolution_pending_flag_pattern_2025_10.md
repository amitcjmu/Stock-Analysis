# Conflict Resolution Pending Flag Pattern

## Problem
Asset conflict resolution endpoint rejected valid requests because validation checked `flow.status != "paused"`, but flows could have various statuses (`assessment_ready`, `running`, etc.) while waiting for conflict resolution.

**Root Cause**: Status field reflects Master Flow lifecycle (ADR-012), NOT operational state. The authoritative indicator for "waiting for user to resolve conflicts" is the `conflict_resolution_pending` flag in `phase_state`, not the status field.

## The Correct Pattern

### Use Flag, Not Status
```python
# ❌ WRONG - Checks status field
if flow.status != "paused":
    raise HTTPException(
        status_code=400,
        detail="Flow must be paused to resolve conflicts"
    )

# ✅ CORRECT - Checks conflict_resolution_pending flag
conflict_pending = (
    flow.phase_state
    and flow.phase_state.get("conflict_resolution_pending") is True
)
if not conflict_pending:
    raise HTTPException(
        status_code=400,
        detail="No conflicts pending resolution"
    )
```

### Why Status Field is Unreliable

Per ADR-012, status reflects **Master Flow lifecycle**, not operational details:
- `initialized` - Flow created
- `running` - Actively executing phases
- `paused` - User-initiated pause (generic)
- `completed` - All phases done
- `failed` - Unrecoverable error

A flow can be:
- `status="running"` with `conflict_resolution_pending=True` (auto-paused by agent)
- `status="assessment_ready"` with `conflict_resolution_pending=True` (legacy status)
- `status="paused"` with `conflict_resolution_pending=False` (user manually paused)

### The phase_state Structure
```python
# Set when conflicts detected
flow.phase_state = {
    "conflict_resolution_pending": True,
    "conflict_count": 21,
    "conflicts": [...],
    "paused_at": "2025-10-13T03:15:00Z",
    "paused_by": "asset_inventory_agent"
}

# Cleared after resolution
flow.phase_state = {}  # or None
```

## Implementation Pattern

### Setting the Flag (Agent Side)
```python
# In asset inventory agent after detecting conflicts
phase_result = {
    "status": "paused",
    "crew_results": {
        "assets_created": 21,
        "conflicts_detected": 21,
        "phase_state": {
            "conflict_resolution_pending": True,
            "conflict_count": 21,
            "conflicts": conflicts_list
        }
    }
}
```

### Checking the Flag (API Side)
```python
@router.post("/asset-conflicts/resolve")
async def resolve_conflicts(
    request: ConflictResolutionRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    # Get flow
    flow = await get_discovery_flow(request.flow_id, db, context)

    # Check flag, not status
    conflict_pending = (
        flow.phase_state
        and flow.phase_state.get("conflict_resolution_pending") is True
    )

    if not conflict_pending:
        return ConflictResolutionResponse(
            resolved_count=0,
            errors=["No conflicts pending resolution"]
        )

    # Resolve conflicts...

    # Clear flag after resolution
    flow.phase_state = {}
    await db.commit()
```

### Clearing the Flag (After Resolution)
```python
# After all conflicts resolved successfully
flow.phase_state = {}  # Clear entire phase_state
# OR keep other metadata
if flow.phase_state:
    flow.phase_state.pop("conflict_resolution_pending", None)
    flow.phase_state.pop("conflict_count", None)

await db.commit()
```

## Phase Transition Agent Integration

The Phase Transition Agent must recognize this flag as successful pause, not failure:

```python
# In get_post_execution_decision()
phase_status = phase_result.get("status")
crew_results = phase_result.get("crew_results", {})
conflict_pending = crew_results.get("phase_state", {}).get(
    "conflict_resolution_pending", False
)

# Paused for user action is SUCCESS, not failure
if phase_status == "paused" and conflict_pending:
    return AgentDecision(
        action=PhaseAction.PAUSE,
        next_phase=phase_name,  # Stay on same phase
        confidence=0.95,
        reasoning=f"Phase {phase_name} paused waiting for conflict resolution",
        metadata={
            "paused_for": "conflict_resolution",
            "conflict_count": crew_results.get("conflict_count", 0)
        }
    )
```

## Real Example: Asset Conflicts

**File**: `backend/app/api/v1/endpoints/asset_conflicts.py:226-248`

```python
# Validate flow is waiting for conflict resolution
conflict_pending = (
    flow.phase_state
    and flow.phase_state.get("conflict_resolution_pending") is True
)

if not conflict_pending:
    logger.warning(
        f"⚠️ Flow {flow_id} no longer has conflict_resolution_pending flag"
    )
    return ConflictResolutionResponse(
        resolved_count=0,
        total_requested=len(request.resolutions),
        errors=[
            f"Flow {flow_id} is no longer waiting for conflict resolution. "
            "Conflicts may have already been resolved."
        ],
    )

logger.info(
    f"✅ Flow validation passed: {len(conflict_ids)} conflicts belong to "
    f"flow {flow_id} (status: {flow.status}, conflict_resolution_pending: true)"
)
```

## UI Integration

Frontend checks the same flag to display conflict resolution UI:

```typescript
// Check if flow needs conflict resolution
const needsConflictResolution =
  flow.phase_state?.conflict_resolution_pending === true;

// Show conflict resolution banner
{needsConflictResolution && (
  <ConflictResolutionBanner
    flowId={flow.flow_id}
    conflictCount={flow.phase_state.conflict_count}
    onResolve={handleResolveConflicts}
  />
)}
```

## Common Mistakes

### Mistake 1: Checking Status Instead of Flag
```python
# ❌ WRONG
if flow.status == "paused":
    # Allow conflict resolution

# Problem: Flow might be "running" or "assessment_ready" with conflicts
```

### Mistake 2: Not Clearing Flag After Resolution
```python
# ❌ WRONG
# Resolve conflicts but don't clear flag
flow.conflicts.update(...)
await db.commit()

# Problem: Flag still true, UI shows stale "resolve conflicts" prompt
```

### Mistake 3: Treating Paused-for-Conflicts as Failure
```python
# ❌ WRONG
if phase_status == "paused":
    return AgentDecision(
        action=PhaseAction.FAIL,
        reasoning="Phase failed: Unknown error"
    )

# Problem: Agent treats expected user interaction as failure
```

## Testing Pattern

```python
async def test_conflict_resolution_validates_flag():
    # Create flow with conflicts
    flow = await create_flow_with_conflicts(
        status="running",  # Not "paused"!
        phase_state={
            "conflict_resolution_pending": True,
            "conflict_count": 5
        }
    )

    # Should allow resolution despite status="running"
    response = await resolve_conflicts(
        flow_id=flow.flow_id,
        resolutions=[...]
    )

    assert response.resolved_count == 5

    # Verify flag cleared
    refreshed_flow = await get_flow(flow.flow_id)
    assert refreshed_flow.phase_state.get("conflict_resolution_pending") is None
```

## Key Takeaway

**Operational flags > Status field** for user interactions. Status reflects lifecycle, flags reflect current operational state.

## Related Patterns
- ADR-012: Flow Status Management Separation
- Phase Transition Agent decision logic
- Frontend cache invalidation after resolution
