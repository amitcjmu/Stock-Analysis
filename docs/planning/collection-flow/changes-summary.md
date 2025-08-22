# Collection Flow Changes Summary

## Overview
This document summarizes all changes made to fix the Collection flow integration with Master Flow Orchestrator (MFO) and implement persistent agents per ADR-015.

## Changes Made (Chronological)

### 1. Initial MFO Integration Issues Fixed

#### Problem
Collection flow was not properly integrated with MFO, causing immediate failures when creating flows.

#### Files Changed
- `backend/app/api/v1/endpoints/collection_crud_create_commands.py`
  - Fixed to use `MasterFlowOrchestrator.create_flow()` directly
  - Added background execution initialization after flow creation
  - Removed legacy flow creation logic

### 2. Persistent Agent Architecture Implementation

#### Problem
Collection flow was attempting to use per-execution CrewAI crews instead of persistent agents as defined in ADR-015.

#### Files Changed
- `backend/app/services/flow_orchestration/execution_engine_crew_collection.py`
  - **Complete refactor** to use `TenantScopedAgentPool`
  - Replaced CrewAI crew instantiation with persistent agent pool initialization
  - Implemented all Collection phases with persistent agents:
    - platform_detection (uses data_analyst agent)
    - automated_collection (uses quality_assessor agent)
    - gap_analysis (uses business_value_analyst agent)
    - questionnaire_generation (uses field_mapper and pattern_discovery agents)
    - manual_collection (awaits user input)

### 3. TenantScopedAgentPool Parameter Fix

#### Problem
`TenantScopedAgentPool.initialize_tenant_pool()` was called with incorrect parameter name.

#### Error
```
TypeError: initialize_tenant_pool() got an unexpected keyword argument 'tenant_id'
```

#### Fix
Changed from `tenant_id` to `client_id` parameter:
```python
agent_pool = await TenantScopedAgentPool.initialize_tenant_pool(
    client_id=str(master_flow.client_account_id),  # Fixed
    engagement_id=str(master_flow.engagement_id),
)
```

### 4. ServiceRegistry Instantiation Fix

#### Problem
Attempted to use non-existent `ServiceRegistry.get_instance()` method.

#### Files Changed
- `backend/app/services/flow_orchestration/execution_engine_crew.py`
  - Fixed ServiceRegistry instantiation with proper parameters:
  ```python
  self.service_registry = ServiceRegistry(
      db=self.db,
      context=self.context,
      audit_logger=None
  )
  ```

### 5. Flow State Attribute Error Fix

#### Problem
`CrewAIFlowStateExtensions` model doesn't have `current_phase` attribute.

#### Files Changed
- `backend/app/services/flow_orchestration/execution_engine_state_utils.py`
  - Added proper method checking:
  ```python
  if hasattr(master_flow, 'get_current_phase'):
      current_phase = master_flow.get_current_phase()
  elif master_flow.flow_persistence_data:
      current_phase = master_flow.flow_persistence_data.get('current_phase')
  ```

### 6. Phase Transition Issue (Partially Fixed)

#### Problem
Collection flow stops after `platform_detection` phase because PhaseTransitionAgent is hardcoded for Discovery flows only.

#### Root Cause Analysis
- `PhaseTransitionAgent` only recognizes Discovery phases
- `DecisionUtils.get_next_phase()` returns "complete" for unrecognized phases
- Flow registry phase configurations are ignored

#### Files Changed (Partial)
- `backend/app/services/flow_orchestration/execution_engine_phase_utils.py`
  - Added flow_registry parameter to constructor
  - Started updating `get_default_next_phase` (not complete)

## Current Status

### Working
✅ Collection flow creates successfully via MFO
✅ Background execution starts properly
✅ Platform detection phase executes with persistent agents
✅ Persistent agent pool initializes correctly
✅ Agents maintain state across executions

### Not Working
❌ Flow stops after platform_detection (marks as "complete")
❌ Gap analysis phase never executes
❌ Questionnaire generation never happens
❌ No adaptive forms displayed to user

## Next Steps (Per Implementation Plan)

1. **Complete Phase Transition Fix**
   - Finish updating ExecutionEnginePhaseUtils
   - Pass flow_registry from ExecutionEngineCore
   - Make PhaseTransitionAgent flow-type aware

2. **Implement Collection-Specific Logic**
   - Create CollectionPhaseTransitionAgent
   - Handle gap analysis → questionnaire generation transition
   - Store questionnaires in database

3. **Testing**
   - Unit tests for phase transitions
   - Integration tests for complete flow
   - E2E tests with Playwright

## Key Learnings

1. **Architecture Matters**: The MFO two-table design pattern must be followed exactly
2. **ADRs Are Critical**: ADR-015 clearly specified persistent agents, not per-execution crews
3. **Flow Registry Is Central**: All phase configurations should come from the registry
4. **No Hardcoding**: Phase names and transitions must be dynamic
5. **Test Everything**: Each flow type needs comprehensive testing

## References

- [ADR-015: Persistent Multi-Tenant Agent Architecture](../../adr/015-persistent-multi-tenant-agent-architecture.md)
- [ADR-020: Flow-Type Aware Phase Transition Architecture](../../adr/020-flow-type-aware-phase-transitions.md)
- [Implementation Plan](./implementation-plan.md)
- [Discovery Flow Summary](../../e2e-flows/01_Discovery/00_Discovery_Flow_Summary.md)