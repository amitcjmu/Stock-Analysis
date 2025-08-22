# Collection Flow Implementation Plan

## Executive Summary

This document outlines the implementation plan for fixing the Collection flow's phase transition issues and ensuring proper execution of all phases, particularly the questionnaire generation functionality.

## Current State Analysis

### Problems Identified
1. **Critical Context Key Mismatch**: PhaseTransitionAgent receives empty phase_name due to key mismatch
2. **Phase Transition Failure**: Collection flow stops after `platform_detection` phase
3. **Hardcoded Logic**: PhaseTransitionAgent only recognizes Discovery flow phases
4. **Registry Ignored**: Flow registry's phase configurations are not being used
5. **No Questionnaires**: Adaptive questionnaire generation never executes
6. **Missing Phase Registration**: questionnaire_generation exists in crew handlers but not in flow config
7. **Frontend Navigation Gap**: Collection phases missing from UI route sequences

### Root Causes
- **Critical Bug**: ExecutionEngineAgentHandlers sets `completed_phase` but PhaseTransitionAgent reads `phase_name`
- PhaseTransitionAgent is Discovery-specific
- DecisionUtils.get_next_phase() returns "complete" for unrecognized phases
- ExecutionEnginePhaseUtils uses hardcoded phase transitions and doesn't receive flow_registry
- Flow registry integration is incomplete
- questionnaire_generation phase not properly registered in collection flow config
- Frontend PHASE_SEQUENCES missing collection flow routes

## Implementation Phases

### Phase 1: Critical Fixes (Day 1 - URGENT)
**Goal**: Fix showstopper bugs preventing any flow progression

#### 1.1 Fix Context Key Mismatch (CRITICAL)
- [ ] Fix ExecutionEngineAgentHandlers to use consistent `phase_name` key
- [ ] Verify PhaseTransitionAgent reads correct context key
- [ ] Test post-execution decision with proper phase name

#### 1.2 Add Missing questionnaire_generation Phase Registration
- [ ] Add PhaseConfig for questionnaire_generation in collection_flow_config.py
- [ ] Insert questionnaire_generation between gap_analysis and manual_collection
- [ ] Verify crew handlers align with registered phases

#### 1.3 Wire Flow Registry Through Components
- [ ] Pass flow_registry from ExecutionEngineCore to ExecutionEnginePhaseUtils
- [ ] Update get_default_next_phase to accept flow_type parameter
- [ ] Implement registry-driven phase lookup with fallback
- [ ] Use lambda closure pattern for flow-type aware fallback function

### Phase 2: Flow-Type Aware Architecture (Day 1-2)
**Goal**: Eliminate hardcoded Discovery-only logic

#### 2.1 Update PhaseTransitionAgent
- [ ] Add flow_registry parameter to constructor
- [ ] Implement flow-type aware decision logic using registry
- [ ] Create Collection-specific transition logic
- [ ] Maintain Discovery flow backward compatibility

#### 2.2 Update DecisionUtils and Related Components
- [ ] Make DecisionUtils.get_next_phase() flow-type aware or Discovery-only
- [ ] Update RouteDecisionTool to use FlowTypeRegistry
- [ ] Remove hardcoded Discovery phase sequences from shared utils

### Phase 3: Frontend and Persistence (Day 2)
**Goal**: Enable UI navigation and questionnaire storage

#### 3.1 Fix Frontend Navigation
- [ ] Add collection to PHASE_SEQUENCES in src/config/flowRoutes.ts
- [ ] Define complete phase sequence: ['platform_detection', 'automated_collection', 'gap_analysis', 'questionnaire_generation', 'manual_collection', 'synthesis']
- [ ] Ensure FLOW_PHASE_ROUTES.collection has route functions for all phases
- [ ] Test UI navigation through Collection phases

#### 3.2 Implement Questionnaire Persistence
- [ ] Create questionnaire repository/service for database storage
- [ ] Update ExecutionEngineCollectionCrews._execute_questionnaire_generation to persist questionnaires
- [ ] Add API endpoint to fetch questionnaires for Collection flows
- [ ] Link questionnaires to collection child flow records

#### 3.3 Collection Phase Logic Enhancement
- [ ] Implement gap analysis → questionnaire_generation decision logic
- [ ] Handle questionnaire_generation → manual_collection transition
- [ ] Ensure proper phase result formatting for UI consumption
- [ ] Add synthesis phase implementation

### Phase 4: Testing & Validation (Day 3)
**Goal**: Comprehensive testing of Collection flow

#### 4.1 Unit Tests
- [ ] Test registry-driven get_default_next_phase for all flow types
- [ ] Test PhaseTransitionAgent flow-type aware decisions
- [ ] Test Collection-specific gap → questionnaire transitions
- [ ] Test context key consistency in post-execution decisions
- [ ] Test fallback mechanisms for registry failures

#### 4.2 Integration Tests
- [ ] Create pytest test in `/tests/backend/test_collection_flow_phases.py`
- [ ] Test complete Collection flow execution through all phases
- [ ] Verify questionnaire generation and persistence
- [ ] Test phase persistence and recovery scenarios
- [ ] Test no regression in Discovery flow execution

#### 4.3 E2E Tests (using Playwright MCP)
- [ ] Create Playwright test in `/tests/e2e/collection-flow-complete.spec.ts`
- [ ] Test UI navigation through all Collection phases
- [ ] Verify questionnaire display and form interaction
- [ ] Test user submission of adaptive questionnaire responses
- [ ] Validate complete flow from platform_detection to synthesis

### Phase 5: Documentation & Deployment (Day 4)
**Goal**: Document changes and prepare for deployment

#### 5.1 Documentation Updates
- [ ] Update Collection flow documentation with new phases
- [ ] Document phase transition architecture changes
- [ ] Update API documentation for questionnaire endpoints
- [ ] Create troubleshooting guide for phase transition issues

#### 5.2 Migration & Deployment
- [ ] Create migration script for existing Collection flows
- [ ] Update Docker configurations if needed
- [ ] Prepare rollback plan with specific revert steps
- [ ] Deploy to staging environment and validate

## Technical Details

### File Changes Required

#### Backend Core Files
```
backend/app/services/flow_orchestration/
├── execution_engine_core.py           # Pass flow_registry to ExecutionEnginePhaseUtils
├── execution_engine_phase_utils.py    # Accept flow_registry, implement flow-type aware get_default_next_phase
├── execution_engine_agents.py         # Fix context key mismatch: use phase_name consistently
└── execution_engine_crew_collection.py # Already updated for persistent agents
```

#### Agent Files
```
backend/app/services/crewai_flows/agents/decision/
├── phase_transition.py     # Add flow_registry param, implement flow-type aware decisions
├── utils.py                # Update DecisionUtils.get_next_phase() or restrict to Discovery
└── collection_transition.py # NEW: Collection-specific agent (optional)
```

#### Flow Configuration
```
backend/app/services/flow_configs/
├── collection_flow_config.py          # Add questionnaire_generation PhaseConfig
└── route_decision_tool.py             # Update to use FlowTypeRegistry
```

#### Frontend Files
```
src/config/
├── flowRoutes.ts                       # Add collection to PHASE_SEQUENCES
└── [collection-phase-routes].ts       # Ensure route functions exist for all phases
```

### Code Snippets

#### Critical Context Key Fix
```python
# In ExecutionEngineAgentHandlers.get_post_execution_decision()
agent_context = {
    "flow_id": master_flow.flow_id,
    "flow_type": master_flow.flow_type,
    "phase_name": phase_name,  # Changed from "completed_phase"
    "phase_result": phase_result,
    "flow_state": flow_state or {},
    "flow_history": master_flow.flow_persistence_data or {},
}
```

#### Flow-Aware ExecutionEngineCore
```python
# In ExecutionEngineCore.__init__()
self.phase_utils = ExecutionEnginePhaseUtils(master_repo, self.flow_registry)

# In ExecutionEngineCore.execute_phase()
post_decision = await self.agents.get_post_execution_decision(
    master_flow,
    phase_name,
    phase_result,
    flow_state,
    lambda name: self.phase_utils.get_default_next_phase(name, flow_type=master_flow.flow_type)
)
```

#### Updated get_default_next_phase
```python
def get_default_next_phase(self, current_phase: str, flow_type: str = None) -> str:
    """Get default next phase using FlowTypeRegistry"""
    if flow_type and self.flow_registry:
        try:
            flow_config = self.flow_registry.get_flow_config(flow_type)
            next_phase = flow_config.get_next_phase(current_phase)
            return next_phase if next_phase else "completed"
        except Exception as e:
            logger.warning(f"Failed to get next phase from registry: {e}")
    
    # Fallback for Discovery flows
    return self._legacy_phase_transitions.get(current_phase, "completed")
```

#### Flow-Aware PhaseTransitionAgent
```python
class PhaseTransitionAgent(BaseDecisionAgent):
    def __init__(self, flow_registry: FlowTypeRegistry = None):
        super().__init__(...)
        self.flow_registry = flow_registry
    
    def _make_transition_decision(self, current_phase: str, analysis: Dict[str, Any]) -> AgentDecision:
        # Use flow registry for next phase if available
        flow_type = analysis.get("flow_type")
        if flow_type and self.flow_registry:
            try:
                flow_config = self.flow_registry.get_flow_config(flow_type)
                next_phase = flow_config.get_next_phase(current_phase)
                if next_phase:
                    return AgentDecision(
                        action=PhaseAction.PROCEED,
                        next_phase=next_phase,
                        confidence=0.8,
                        reasoning=f"Registry-driven transition: {current_phase} → {next_phase}"
                    )
            except Exception as e:
                logger.warning(f"Registry lookup failed: {e}")
        
        # Fallback to existing logic
        # ... existing phase-specific logic
```

#### Frontend Phase Sequences
```typescript
// In src/config/flowRoutes.ts
export const PHASE_SEQUENCES: Record<FlowType, string[]> = {
  discovery: ['data_import', 'attribute_mapping', 'data_cleansing', 'inventory', 'dependencies'],
  collection: ['platform_detection', 'automated_collection', 'gap_analysis', 'questionnaire_generation', 'manual_collection', 'synthesis'],
  assessment: ['migration_readiness', 'business_impact', 'technical_assessment', 'tech_debt'],
  // ... other flows
};
```

## Success Criteria

### Functional Requirements
- [ ] Collection flow executes all phases sequentially
- [ ] Questionnaires are generated based on gap analysis
- [ ] UI displays adaptive questionnaire forms
- [ ] User can submit questionnaire responses
- [ ] Flow completes successfully with synthesis

### Non-Functional Requirements
- [ ] No regression in Discovery flow
- [ ] Phase transitions complete within 5 seconds
- [ ] All flows use flow registry for configuration
- [ ] System maintains backward compatibility

## Risk Mitigation

### Risk 1: Breaking Discovery Flow
**Mitigation**: Implement all changes with fallback logic to existing behavior

### Risk 2: Performance Impact
**Mitigation**: Cache flow configurations during execution

### Risk 3: Incomplete Migration
**Mitigation**: Gradual rollout with feature flags

## Timeline

| Day | Tasks | Deliverables |
|-----|-------|-------------|
| Day 1 | Core infrastructure updates | Flow-aware phase transitions |
| Day 2 | Collection-specific logic | Working questionnaire generation |
| Day 3 | Testing & validation | Comprehensive test suite |
| Day 4 | Documentation & deployment | Production-ready code |

## Rollback Plan

If issues are discovered after deployment:
1. Revert to previous git commit
2. Restore database to pre-migration state
3. Clear Redis cache
4. Restart all services
5. Monitor for 30 minutes

## Review Checklist

Before proceeding with implementation:
- [ ] ADR-020 reviewed and approved
- [ ] Implementation plan reviewed by team
- [ ] Test strategy approved
- [ ] Rollback plan validated
- [ ] Resources allocated

## References

- [ADR-020: Flow-Type Aware Phase Transition Architecture](../../adr/020-flow-type-aware-phase-transitions.md)
- [ADR-015: Persistent Multi-Tenant Agent Architecture](../../adr/015-persistent-multi-tenant-agent-architecture.md)
- [Collection Flow Documentation](../../e2e-flows/02_Collection/)
- [Discovery Flow Summary](../../e2e-flows/01_Discovery/00_Discovery_Flow_Summary.md)