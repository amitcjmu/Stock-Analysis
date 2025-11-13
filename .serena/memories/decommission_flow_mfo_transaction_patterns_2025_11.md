# Decommission Flow MFO Transaction and Endpoint Patterns (Nov 2025)

## Problem: 500 Error on "Approve & Continue" Button
**Error**: "A transaction is already begun on this Session"
**Location**: Decommission Planning page → Approve button
**Root Cause**: Nested transaction blocks in MFO lifecycle functions

## ❌ WRONG Pattern: Nested Transactions with FastAPI
```python
# lifecycle.py - CAUSES 500 ERROR
async def resume_decommission_flow(
    flow_id: UUID,
    client_account_id: UUID,
    engagement_id: UUID,
    phase: str | None,
    user_input: Dict[str, Any] | None,
    db: AsyncSession,
) -> Dict[str, Any]:
    try:
        async with db.begin():  # ❌ ERROR: FastAPI get_db() already manages transaction
            # ... query and update logic ...
            # Transaction commits automatically on context exit
```

## ✅ CORRECT Pattern: Explicit Commit with FastAPI
```python
# lifecycle.py - FIXED
async def resume_decommission_flow(
    flow_id: UUID,
    client_account_id: UUID,
    engagement_id: UUID,
    phase: str | None,
    user_input: Dict[str, Any] | None,
    db: AsyncSession,
) -> Dict[str, Any]:
    try:
        # ATOMIC TRANSACTION: Both master and child updated together
        # Note: FastAPI's get_db() dependency manages the transaction context
        # We don't need explicit db.begin() as the session auto-commits on success

        # Get both master and child flows
        query = (
            select(CrewAIFlowStateExtensions, DecommissionFlow)
            .join(DecommissionFlow, DecommissionFlow.master_flow_id == CrewAIFlowStateExtensions.flow_id)
            .where(CrewAIFlowStateExtensions.flow_id == flow_id)
        )
        result = await db.execute(query)
        row = result.first()

        # ... validation and update logic ...

        # Commit the transaction (FastAPI's get_db handles this automatically)
        await db.commit()

        # Refresh both objects to ensure they're attached to the session
        await db.refresh(master_flow)
        await db.refresh(child_flow)

        # Return updated unified state
        return await get_decommission_status_via_mfo(flow_id, db, client_account_id, engagement_id)
```

## Key Pattern: Match create.py Transaction Style
**Reference File**: `mfo_integration/create.py` already had correct pattern with comments
**Applied To**:
- `lifecycle.py`: resume, pause, cancel functions (lines 54-377)
- `updates.py`: update_decommission_phase_via_mfo (lines 75-189)

## Secondary Problem: Wrong Endpoint Called
**Issue**: Button called `/resume` endpoint for a "running" flow (should only resume "paused" flows)
**Solution**: Created dedicated phase update endpoint

### New Endpoint Architecture
```python
# flow_management.py:288-351
@router.post("/{flow_id}/phases/{phase_name}", response_model=DecommissionFlowStatusResponse)
async def update_phase_status_endpoint(
    flow_id: str,
    phase_name: str,  # decommission_planning, data_migration, system_shutdown
    request: UpdatePhaseRequest,
    # ... dependencies ...
):
    """Update decommission phase status via MFO."""
    result = await update_decommission_phase_via_mfo(
        flow_id=UUID(flow_id),
        phase_name=phase_name,
        phase_status=request.phase_status,  # pending/running/completed/failed
        phase_data=request.phase_data,
        db=db,
    )
    return DecommissionFlowStatusResponse(**result)
```

### New Request Schema
```python
# schemas/decommission_flow/requests.py:137-172
class UpdatePhaseRequest(BaseModel):
    """Request schema for updating decommission phase status."""

    phase_status: str = Field(
        ...,
        description="New status for the phase (pending/running/completed/failed)",
    )

    phase_data: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Optional phase-specific data to store",
    )

    @field_validator("phase_status")
    @classmethod
    def validate_phase_status(cls, v):
        valid_statuses = ["pending", "running", "completed", "failed"]
        if v not in valid_statuses:
            raise ValueError(f"Invalid phase_status. Must be one of: {', '.join(valid_statuses)}")
        return v
```

## Frontend Integration Pattern

### API Service Layer
```typescript
// decommissionFlowService.ts:121-258
export interface UpdatePhaseRequest {
  phase_status: "pending" | "running" | "completed" | "failed";
  phase_data?: Record<string, unknown>;
}

async updatePhaseStatus(
  flowId: string,
  phaseName: DecommissionPhase,
  params: UpdatePhaseRequest
): Promise<DecommissionFlowStatusResponse> {
  return apiCall(`/decommission-flow/${flowId}/phases/${phaseName}`, {
    method: "POST",
    body: JSON.stringify(params),
  });
}
```

### React Query Hook
```typescript
// useDecommissionFlow.ts:238-280
export function useUpdatePhaseStatus(): UseMutationResult<
  DecommissionFlowStatusResponse,
  Error,
  { flowId: string; phaseName: DecommissionPhase; params: UpdatePhaseRequest },
  unknown
> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ flowId, phaseName, params }) =>
      decommissionFlowService.updatePhaseStatus(flowId, phaseName, params),
    onSuccess: (data, variables) => {
      // Update cache optimistically
      queryClient.setQueryData(decommissionFlowKeys.status(variables.flowId), data);
      // Trigger refetch
      queryClient.invalidateQueries({ queryKey: decommissionFlowKeys.status(variables.flowId) });
    },
  });
}
```

### Component Usage (Planning.tsx)
```typescript
// OLD (WRONG): Called resume endpoint for running flow
const resumeFlowMutation = useResumeDecommissionFlow();
await resumeFlowMutation.mutateAsync({ flowId, params: { phase: 'decommission_planning' } });

// NEW (CORRECT): Update phase status directly
const updatePhaseMutation = useUpdatePhaseStatus();
await updatePhaseMutation.mutateAsync({
  flowId,
  phaseName: 'decommission_planning',
  params: {
    phase_status: 'completed',
    phase_data: { planning_approved: true },
  },
});
```

## Testing Verification
**Tool**: Playwright MCP browser automation
**Flow**:
1. Navigate to `/decommission/planning?flow_id=<UUID>`
2. Wait for page load and systems display
3. Click "Approve & Continue" button
4. Verify success toast appears
5. Confirm navigation to `/decommission/data-migration`
6. Check database for phase status = "completed"

## Files Modified (8 total)
**Backend (5)**:
- `api/v1/endpoints/decommission_flow/flow_management.py` - New endpoint
- `api/v1/endpoints/decommission_flow/mfo_integration/lifecycle.py` - Transaction fix
- `api/v1/endpoints/decommission_flow/mfo_integration/updates.py` - Transaction fix
- `schemas/decommission_flow/requests.py` - New UpdatePhaseRequest schema
- `schemas/decommission_flow/__init__.py` - Export new schema

**Frontend (3)**:
- `lib/api/decommissionFlowService.ts` - New service function
- `hooks/decommissionFlow/useDecommissionFlow.ts` - New React Query hook + type import fix
- `pages/decommission/Planning.tsx` - Use new hook instead of resume

## Pre-commit Issues
**Black Formatting**: Auto-reformatted 3 Python files during commit
**TypeScript Lint**: Fixed `@typescript-eslint/consistent-type-imports` violations
**Solution**: Separated type-only imports with `import type` syntax

## Generalization Rules
1. **FastAPI Transaction Management**: NEVER use `async with db.begin()` in functions called by FastAPI endpoints - get_db() already manages transactions
2. **MFO Pattern Consistency**: Follow create.py transaction pattern (explicit commit + refresh) in all MFO lifecycle/update functions
3. **Endpoint Specificity**: Create dedicated endpoints for specific operations (phase updates) rather than overloading generic endpoints (resume)
4. **Type Import Separation**: Use `import type` for TypeScript type-only imports to satisfy ESLint rules
5. **Cache Management**: React Query hooks must invalidate queries after mutations to trigger refetch

## ADR References
- **ADR-006**: Master Flow Orchestrator pattern (two-table architecture)
- **ADR-012**: Flow status separation (master lifecycle vs child operational)
- **ADR-027**: Phase names match FlowTypeConfig exactly

## Commit Hash
`ff31668fa` on branch `feature/decommission-flow-v2.5.0`
