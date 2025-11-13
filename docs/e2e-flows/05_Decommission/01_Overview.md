# Decommission Flow - Overview and Initiation

**Last Updated:** 2025-11-06
**Purpose:** Detailed guide for the Decommission dashboard, flow initiation, and system selection

## 📋 Overview

The Decommission Flow Overview page serves as the entry point for safely retiring IT systems. Users can:

1. View systems eligible for decommission (6R strategy = "Retire")
2. Review existing decommission flows and their progress
3. Select systems for decommission
4. Initialize new decommission flows with strategic configurations
5. Monitor active decommission operations

**URL Path**: `/decommission`
**Component**: `src/pages/Decommission.tsx`
**Hook**: `src/hooks/decommissionFlow/useDecommissionFlow.ts`

## 🎯 Page Objectives

### Primary Goals
- **Safety First**: Prevent accidental decommissioning through clear warnings and confirmations
- **Visibility**: Show all systems eligible for decommission with rationale
- **Tracking**: Display active and completed decommission flows
- **Strategic Planning**: Allow users to configure decommission strategy (cost vs. risk vs. compliance)

### Key Features
- Multi-select system picker with dependency warnings
- Strategic configuration (immediate, scheduled, or phased execution)
- Rollback capability indicator
- Approval workflow management
- Real-time flow status updates via HTTP polling (NO WebSockets)

## 🏗️ Component Architecture

### React Component Structure
```typescript
// Main Component
<Decommission>
  <DashboardHeader />
  <MetricsCards />
  <SystemSelectionTable />
  <StrategyConfiguration />
  <ActiveFlowsList />
  <InitializeFlowButton />
</Decommission>
```

### State Management (React Query)
```typescript
// Hooks used (snake_case fields throughout)
const { data: eligibleSystems } = useQuery({
  queryKey: ['eligible-systems'],
  queryFn: () => decommissionFlowService.getEligibleSystems(),
  staleTime: 60000,  // 1 minute - systems don't change frequently
});

const { data: activeFlows } = useQuery({
  queryKey: ['decommission-flows', 'active'],
  queryFn: () => decommissionFlowService.listDecommissionFlows({
    status: 'initialized,decommission_planning,data_migration,system_shutdown'
  }),
  refetchInterval: 15000,  // 15 seconds - monitor active flows
});

const initializeFlow = useMutation({
  mutationFn: (params: InitializeDecommissionFlowRequest) =>
    decommissionFlowService.initializeDecommissionFlow(params),
  onSuccess: (data) => {
    // Navigate to flow detail page with master_flow_id
    navigate(`/decommission/flow/${data.flow_id}`);
  }
});
```

## 📊 Data Flow Sequence

### 1. Page Load
```
User navigates to /decommission
  ↓
React component mounts
  ↓
useQuery hooks trigger API calls in parallel:
  - GET /api/v1/decommission-flow/eligible-systems
  - GET /api/v1/decommission-flow/?status=...
  ↓
Display dashboard with eligible systems and active flows
```

### 2. Eligible Systems Query

**Endpoint**: `GET /api/v1/decommission-flow/eligible-systems`

**Backend Flow**:
```python
# backend/app/api/v1/endpoints/decommission_flow/queries.py
@router.get("/eligible-systems")
async def get_eligible_systems(
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
) -> List[EligibleSystemResponse]:
    """
    Get systems eligible for decommission based on:
    1. 6R strategy = 'Retire' from Assessment flow
    2. decommission_eligible flag = true
    3. Not already in active decommission flow

    CRITICAL: Uses multi-tenant scoping for security.
    """
    # Query assets with tenant scoping
    stmt = select(Asset).where(
        Asset.client_account_id == context.client_account_id,
        Asset.engagement_id == context.engagement_id,
        or_(
            Asset.six_r_strategy == "Retire",
            Asset.decommission_eligible == True
        )
    )

    result = await db.execute(stmt)
    assets = result.scalars().all()

    # Filter out systems already in active decommission flows
    decom_repo = DecommissionFlowRepository(db, context.client_account_id, context.engagement_id)
    active_flows = await decom_repo.get_active_flows()

    systems_in_decommission = set()
    for flow in active_flows:
        systems_in_decommission.update(flow.selected_system_ids)

    # Build response with snake_case fields
    eligible = []
    for asset in assets:
        if asset.id not in systems_in_decommission:
            eligible.append(EligibleSystemResponse(
                asset_id=str(asset.id),
                asset_name=asset.asset_name,
                six_r_strategy=asset.six_r_strategy,
                annual_cost=asset.estimated_annual_cost or 0,
                decommission_eligible=asset.decommission_eligible or False,
                grace_period_end=asset.grace_period_end,
                retirement_reason=asset.retirement_reason or "Assessment recommends retirement"
            ))

    return eligible
```

**Response Shape** (snake_case):
```json
[
  {
    "asset_id": "uuid-here",
    "asset_name": "Legacy CRM System",
    "six_r_strategy": "Retire",
    "annual_cost": 45000.00,
    "decommission_eligible": true,
    "grace_period_end": "2025-12-31T00:00:00Z",
    "retirement_reason": "End of life, high maintenance cost"
  }
]
```

### 3. System Selection

**UI Component**: `SystemSelectionTable`

**Features**:
- Multi-select checkbox with system details
- Shows retirement reason and annual cost
- Dependency warnings (if system has dependencies not selected)
- Grace period indicators (time remaining before required decommission)
- Total cost savings calculation

**Dependency Warning Logic**:
```typescript
// Check if selected system has dependencies
const checkDependencies = async (systemIds: string[]) => {
  for (const systemId of systemIds) {
    const dependencies = await assetApi.getDependencies(systemId);

    const unselectedDeps = dependencies.filter(
      dep => !systemIds.includes(dep.dependent_asset_id)
    );

    if (unselectedDeps.length > 0) {
      // Show warning modal
      setWarnings(prev => ({
        ...prev,
        [systemId]: `This system has ${unselectedDeps.length} dependencies not selected for decommission. Consider adding: ${unselectedDeps.map(d => d.dependent_asset_name).join(', ')}`
      }));
    }
  }
};
```

### 4. Strategy Configuration

**UI Component**: `StrategyConfiguration`

**Configuration Options**:

```typescript
interface DecommissionStrategy {
  // Priority: What's most important?
  priority: 'cost_savings' | 'risk_reduction' | 'compliance';

  // Execution Mode: When to decommission?
  execution_mode: 'immediate' | 'scheduled' | 'phased';

  // Safety: Enable rollback during planning/migration?
  rollback_enabled: boolean;

  // Approvals: Required stakeholder approvals
  stakeholder_approvals?: string[];
}
```

**Strategy Examples**:

1. **Aggressive Cost Savings** (Immediate Execution)
   ```json
   {
     "priority": "cost_savings",
     "execution_mode": "immediate",
     "rollback_enabled": true,
     "stakeholder_approvals": ["Finance", "IT Manager"]
   }
   ```

2. **Conservative Risk Reduction** (Phased Execution)
   ```json
   {
     "priority": "risk_reduction",
     "execution_mode": "phased",
     "rollback_enabled": true,
     "stakeholder_approvals": ["CIO", "Security Lead", "Compliance Officer"]
   }
   ```

3. **Compliance-Driven** (Scheduled Execution)
   ```json
   {
     "priority": "compliance",
     "execution_mode": "scheduled",
     "rollback_enabled": false,
     "stakeholder_approvals": ["Legal", "Compliance Officer"]
   }
   ```

### 5. Flow Initialization

**Trigger**: User clicks "Initialize Decommission Flow" button

**Frontend Request**:
```typescript
// ✅ CORRECT: POST with request body (snake_case fields)
const initializeFlow = async () => {
  const params: InitializeDecommissionFlowRequest = {
    selected_system_ids: selectedSystemIds,  // ✅ snake_case
    flow_name: `Decommission ${selectedSystemIds.length} systems - ${new Date().toISOString()}`,
    decommission_strategy: {
      priority: strategy.priority,
      execution_mode: strategy.execution_mode,
      rollback_enabled: strategy.rollback_enabled,
      stakeholder_approvals: strategy.stakeholder_approvals
    }
  };

  const response = await decommissionFlowService.initializeDecommissionFlow(params);

  // Navigate to flow detail page (uses master_flow_id)
  navigate(`/decommission/flow/${response.flow_id}`);
};
```

**Backend Endpoint**:
```python
# backend/app/api/v1/endpoints/decommission_flow/flow_management.py
@router.post("/initialize")
async def initialize_decommission_flow(
    request: InitializeDecommissionFlowRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
    mfo: MasterFlowOrchestrator = Depends(get_mfo)
) -> DecommissionFlowResponse:
    """
    Initialize decommission flow with MFO pattern (ADR-006).

    Creates:
    1. Master flow in crewai_flow_state_extensions (lifecycle)
    2. Child flow in decommission_flows (operational state)
    3. Decommission plans for each selected system

    Returns master_flow_id for all subsequent operations.
    """
    try:
        # Atomic transaction for master + child flow creation
        async with db.begin():
            # 1. Create master flow via MFO
            master_flow_id = await mfo.create_flow(
                flow_type="decommission",
                configuration={
                    "selected_system_ids": [str(s) for s in request.selected_system_ids],
                    "decommission_strategy": request.decommission_strategy.dict(),
                    "flow_name": request.flow_name
                },
                atomic=True  # Prevents internal commits
            )

            await db.flush()  # Makes master_flow_id available for FK

            # 2. Create child flow via DecommissionChildFlowService
            child_service = DecommissionChildFlowService(db, context)
            child_flow = await child_service.create_child_flow(
                master_flow_id=master_flow_id,
                flow_name=request.flow_name or f"Decommission {len(request.selected_system_ids)} systems",
                selected_system_ids=[uuid.UUID(s) for s in request.selected_system_ids],
                created_by=context.user_id,
                decommission_strategy=request.decommission_strategy.dict()
            )

            # 3. Create decommission plans for each system
            for system_id in request.selected_system_ids:
                plan = DecommissionPlan(
                    flow_id=child_flow.flow_id,
                    client_account_id=context.client_account_id,
                    engagement_id=context.engagement_id,
                    system_id=uuid.UUID(system_id),
                    system_name="TBD",  # Populated by agent in planning phase
                    risk_level="pending",
                    dependencies=[],
                    approval_status="pending"
                )
                db.add(plan)

            await db.commit()

        # 4. Initiate background execution
        background_service = BackgroundExecutionService(db)
        await background_service.start_flow_execution(master_flow_id)

        # 5. Return response with master_flow_id
        return DecommissionFlowResponse(
            flow_id=str(master_flow_id),  # ✅ master_flow_id as primary identifier
            status="initialized",
            current_phase="decommission_planning",
            next_phase="decommission_planning",
            selected_systems=request.selected_system_ids,
            message=f"Decommission flow initialized for {len(request.selected_system_ids)} systems"
        )

    except Exception as e:
        logger.error(f"Failed to initialize decommission flow: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize decommission flow: {str(e)}"
        )
```

## 🎨 UI Components Breakdown

### Metrics Cards

Displays high-level decommission statistics:

```typescript
interface DecommissionMetrics {
  systems_eligible: number;          // ✅ snake_case
  estimated_annual_savings: number;  // ✅ snake_case
  active_flows: number;              // ✅ snake_case
  systems_decommissioned: number;    // ✅ snake_case (lifetime)
}
```

**Calculation**:
- **Systems Eligible**: Count from `getEligibleSystems()`
- **Estimated Annual Savings**: Sum of `annual_cost` for selected systems
- **Active Flows**: Count from `listDecommissionFlows()` with status filtering
- **Systems Decommissioned**: Aggregate from completed flows

### Active Flows List

Displays decommission flows in progress:

```typescript
<FlowCard>
  <FlowName>{flow.flow_name}</FlowName>
  <SystemCount>{flow.system_count} systems</SystemCount>
  <PhaseIndicator>
    {flow.current_phase === 'decommission_planning' && <PlanningIcon />}
    {flow.current_phase === 'data_migration' && <MigrationIcon />}
    {flow.current_phase === 'system_shutdown' && <ShutdownIcon />}
  </PhaseIndicator>
  <ProgressBar value={calculateProgress(flow.phase_progress)} />
  <Actions>
    <ViewButton onClick={() => navigate(`/decommission/flow/${flow.flow_id}`)}>
      View Details
    </ViewButton>
    {flow.status !== 'completed' && (
      <PauseButton onClick={() => pauseFlow(flow.flow_id)}>
        Pause
      </PauseButton>
    )}
  </Actions>
</FlowCard>
```

**Progress Calculation**:
```typescript
const calculateProgress = (phase_progress: PhaseProgress): number => {
  const phases = ['decommission_planning', 'data_migration', 'system_shutdown'];
  let completed = 0;

  phases.forEach(phase => {
    if (phase_progress[phase] === 'completed') {
      completed++;
    } else if (phase_progress[phase] === 'in_progress') {
      completed += 0.5;  // Partial credit for in-progress
    }
  });

  return (completed / phases.length) * 100;
};
```

## 🔄 Polling Strategy

**NO WEBSOCKETS** - Uses HTTP polling per Railway deployment requirements:

```typescript
// Active flow status polling
const { data: flowStatus } = useQuery({
  queryKey: ['decommission-flow-status', flowId],
  queryFn: () => decommissionFlowService.getDecommissionFlowStatus(flowId),
  enabled: !!flowId && flowId !== 'XXXXXXXX-def0-def0-def0-XXXXXXXXXXXX',
  refetchInterval: (data) => {
    if (!data) return false;

    // Aggressive polling during active phases
    if (data.status === 'decommission_planning' ||
        data.status === 'data_migration' ||
        data.status === 'system_shutdown') {
      return 5000;  // 5 seconds
    }

    // Slower polling for completed/failed
    if (data.status === 'completed' || data.status === 'failed') {
      return false;  // Stop polling
    }

    // Default polling for other states
    return 15000;  // 15 seconds
  },
  staleTime: 0,  // Always fetch fresh status
});
```

## 🚨 Error Handling

### Validation Errors

```typescript
// System selection validation
if (selectedSystemIds.length === 0) {
  toast.error('Please select at least one system for decommission');
  return;
}

if (selectedSystemIds.length > 50) {
  toast.error('Cannot decommission more than 50 systems in a single flow. Please create multiple flows.');
  return;
}

// Strategy validation
if (!strategy.priority) {
  toast.error('Please select a decommission priority');
  return;
}

if (strategy.execution_mode === 'scheduled' && !strategy.scheduled_date) {
  toast.error('Please select a scheduled date for decommission execution');
  return;
}
```

### API Error Handling

```typescript
const initializeFlow = useMutation({
  mutationFn: decommissionFlowService.initializeDecommissionFlow,
  onError: (error: any) => {
    if (error.response?.status === 400) {
      toast.error(`Validation error: ${error.response.data.detail}`);
    } else if (error.response?.status === 409) {
      toast.error('Some selected systems are already in an active decommission flow');
    } else if (error.response?.status === 403) {
      toast.error('You do not have permission to decommission systems');
    } else {
      toast.error('Failed to initialize decommission flow. Please try again.');
    }
  },
  onSuccess: (data) => {
    toast.success(`Decommission flow initialized for ${data.selected_systems.length} systems`);
    navigate(`/decommission/flow/${data.flow_id}`);
  }
});
```

## 🎓 Best Practices

### DO ✅
- Use snake_case for ALL field names (matching backend)
- Poll with smart intervals based on flow state
- Show dependency warnings before initialization
- Validate system selection before API call
- Use master_flow_id for navigation and operations
- Display clear cost savings estimates
- Provide rollback option during planning/migration

### DON'T ❌
- Don't use camelCase field names (breaks API contract)
- Don't use WebSockets (not supported on Railway)
- Don't allow decommissioning systems with unresolved dependencies
- Don't skip approval workflows for critical systems
- Don't reference child flow IDs in UI (use master_flow_id)
- Don't allow immediate execution without confirmation
- Don't bypass strategy configuration

## 📝 Implementation Notes

### Multi-Tenant Security
All API calls automatically include:
```typescript
headers: {
  'X-Client-Account-ID': clientAccountId,
  'X-Engagement-ID': engagementId
}
```

### UUID Handling
```typescript
// Frontend receives string UUIDs
const systemIds: string[] = selectedSystems.map(s => s.asset_id);

// Backend converts to UUID type
system_ids: List[uuid.UUID] = [uuid.UUID(s) for s in request.selected_system_ids]
```

### Date Formatting
```typescript
// ISO 8601 format for all dates
const gracePeriodEnd = new Date(system.grace_period_end).toLocaleDateString();
const createdAt = new Date(flow.created_at).toLocaleString();
```

---

**Next Steps**: After initializing a flow, users navigate to the [Decommission Planning Phase](./02_Decommission_Planning.md) to review and approve the decommission plan generated by AI agents.
