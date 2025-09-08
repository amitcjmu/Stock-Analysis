# Discovery Flow Initialization Fixes - September 2025

## Critical Backend Fixes Applied

### 1. Async/Await Pattern Fix
**File**: `backend/app/api/v1/endpoints/unified_discovery/flow_initialization_handlers.py`
```python
# WRONG - initialize_all_flows() is synchronous
flow_init_result = await initialize_all_flows()

# CORRECT - Don't await synchronous functions
flow_init_result = initialize_all_flows()
```

### 2. Transaction Management Fix
```python
# WRONG - Nested transaction causes error
async with db.begin():
    orchestrator = MasterFlowOrchestrator(db, context)
    flow_id, flow_details = await orchestrator.create_flow(atomic=True)

# CORRECT - Let MFO handle transactions
orchestrator = MasterFlowOrchestrator(db, context)
flow_id, flow_details = await orchestrator.create_flow(atomic=False)
```

### 3. Parameter Naming Fix
```python
# MFO expects 'initial_state' not 'initial_data'
await orchestrator.create_flow(
    initial_state=initial_data,  # Not initial_data
    atomic=False
)
```

### 4. Missing Required Fields
```python
# DiscoveryFlow requires user_id
child_flow = DiscoveryFlow(
    flow_id=uuid.UUID(flow_id),
    master_flow_id=uuid.UUID(flow_id),
    client_account_id=context.client_account_id,
    engagement_id=context.engagement_id,
    user_id=context.user_id,  # Required field
    status="running",
    current_phase="data_ingestion"
)
```

## Frontend API Endpoint Fixes

### masterFlowService.ts
```typescript
// WRONG - Hardcoded path
}>("/flows/", backendRequest, {

// CORRECT - Use defined constant
}>(FLOW_ENDPOINTS.initialize, backendRequest, {
```

### Context Endpoints
```typescript
// WRONG - Missing /api/v1 prefix
apiCall('/context/me', {}, false)

// CORRECT
apiCall('/api/v1/context/me', {}, false)
```

## Key Patterns
- Always verify if a function is async before using await
- Check transaction boundaries to avoid nesting
- Use consistent parameter names across service boundaries
- Always include required database fields
- Use endpoint constants instead of hardcoded paths
