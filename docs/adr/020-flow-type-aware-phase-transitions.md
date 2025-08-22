# ADR-020: Flow-Type Aware Phase Transition Architecture

## Status
Proposed

## Context

The current phase transition system in the Master Flow Orchestrator (MFO) is hardcoded for Discovery flow phases only. When Collection flows were integrated with MFO, they failed to progress beyond the first phase because:

1. **PhaseTransitionAgent** only recognizes Discovery phases (data_import, field_mapping, data_cleansing, etc.)
2. **DecisionUtils.get_next_phase()** returns "complete" for any unrecognized phase
3. **ExecutionEnginePhaseUtils** uses hardcoded phase transitions instead of the flow registry

This architectural limitation prevents any non-Discovery flow from executing properly through MFO, even though the flow registry contains correct phase configurations for all flow types.

### Current Problems

- Collection flow stops after `platform_detection` phase, marking itself as "complete"
- Assessment and other flows would face the same issue
- Adaptive questionnaire generation never executes because the flow terminates prematurely
- The flow registry's phase configurations are ignored in favor of hardcoded values

### Root Cause Analysis

The issue stems from the original design assumption that MFO would primarily handle Discovery flows. When the architecture expanded to support multiple flow types (per ADR-006), the phase transition logic wasn't updated to be flow-type aware.

## Decision

We will refactor the phase transition system to be fully flow-type aware by:

1. **Enhancing PhaseTransitionAgent** to use the flow registry for phase navigation
2. **Updating ExecutionEnginePhaseUtils** to query flow configurations dynamically
3. **Creating flow-specific decision agents** when needed for complex phase logic
4. **Maintaining backward compatibility** with existing Discovery flows

### Implementation Strategy

#### 1. Flow Registry Integration
- Pass flow registry to all phase management components
- Use `FlowTypeConfig.get_next_phase()` for determining phase progression
- Fall back to existing logic only when registry lookup fails

#### 2. Agent Architecture Updates
```python
# PhaseTransitionAgent becomes flow-aware
class PhaseTransitionAgent:
    def __init__(self, flow_registry: FlowTypeRegistry = None):
        self.flow_registry = flow_registry
        
    def get_next_phase(self, current_phase: str, flow_type: str):
        if self.flow_registry:
            config = self.flow_registry.get_flow_config(flow_type)
            return config.get_next_phase(current_phase)
        # Fallback to legacy behavior
```

#### 3. Flow-Specific Decision Logic
- Discovery: Complex multi-phase validation (existing)
- Collection: Gap analysis → questionnaire generation logic
- Assessment: Risk scoring → recommendation logic
- Each flow type can have custom decision agents while sharing the base infrastructure

## Consequences

### Positive
- **Extensibility**: New flow types automatically work with MFO
- **Consistency**: All flows use the same phase transition mechanism
- **Maintainability**: Phase configurations centralized in flow registry
- **Flexibility**: Each flow can have custom decision logic when needed
- **Reliability**: No more hardcoded phase names scattered across codebase

### Negative
- **Complexity**: Additional abstraction layer for phase transitions
- **Testing**: Need comprehensive tests for each flow type's progression
- **Migration**: Existing flows need validation to ensure compatibility

### Risks and Mitigations
- **Risk**: Breaking existing Discovery flow logic
  - **Mitigation**: Implement changes with fallback to existing behavior
- **Risk**: Performance impact from registry lookups
  - **Mitigation**: Cache flow configurations during execution
- **Risk**: Inconsistent phase naming across flows
  - **Mitigation**: Enforce naming conventions in flow registry validation

## Implementation Phases

### Phase 1: Core Refactoring (Immediate)
- Update ExecutionEnginePhaseUtils to accept flow_registry
- Modify get_default_next_phase to use flow registry
- Add flow_type parameter propagation through execution chain

### Phase 2: Agent Enhancement (Short-term)
- Refactor PhaseTransitionAgent for flow-type awareness
- Create CollectionPhaseTransitionAgent for collection-specific logic
- Update DecisionUtils to be flow-type aware

### Phase 3: Full Integration (Medium-term)
- Migrate all hardcoded phase transitions to flow registry
- Create flow-specific decision agents for Assessment, Planning, etc.
- Implement comprehensive phase transition testing

## Related ADRs
- ADR-006: Master Flow Orchestrator (introduces multi-flow architecture)
- ADR-011: Flow-Based Architecture Evolution
- ADR-015: Persistent Multi-Tenant Agent Architecture
- ADR-016: Collection Flow Intelligent Data Enrichment

## References
- [Flow Type Registry Implementation](../../backend/app/services/flow_type_registry.py)
- [Phase Transition Agent](../../backend/app/services/crewai_flows/agents/decision/phase_transition.py)
- [Collection Flow Phases](../../backend/app/services/data_collection/collection_flow_registration.py)