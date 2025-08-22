# Collection Flow Implementation Plan

## Executive Summary

This document outlines the implementation plan for fixing the Collection flow's phase transition issues and ensuring proper execution of all phases, particularly the questionnaire generation functionality.

## Current State Analysis

### Problems Identified
1. **Phase Transition Failure**: Collection flow stops after `platform_detection` phase
2. **Hardcoded Logic**: PhaseTransitionAgent only recognizes Discovery flow phases
3. **Registry Ignored**: Flow registry's phase configurations are not being used
4. **No Questionnaires**: Adaptive questionnaire generation never executes

### Root Causes
- PhaseTransitionAgent is Discovery-specific
- DecisionUtils.get_next_phase() returns "complete" for unrecognized phases
- ExecutionEnginePhaseUtils uses hardcoded phase transitions
- Flow registry integration is incomplete

## Implementation Phases

### Phase 1: Core Infrastructure Updates (Day 1)
**Goal**: Enable flow-type aware phase transitions

#### 1.1 Update ExecutionEnginePhaseUtils
- [x] Add flow_registry parameter to constructor
- [ ] Update get_default_next_phase to use flow registry
- [ ] Pass flow_type through execution chain
- [ ] Add fallback for backward compatibility

#### 1.2 Update ExecutionEngineCore
- [ ] Pass flow_registry to ExecutionEnginePhaseUtils
- [ ] Propagate flow_type in phase execution context
- [ ] Update agent context with flow_type information

#### 1.3 Update PhaseTransitionAgent
- [ ] Add flow_registry parameter
- [ ] Create flow-type aware decision logic
- [ ] Update get_post_execution_decision method
- [ ] Maintain Discovery flow compatibility

### Phase 2: Collection-Specific Logic (Day 2)
**Goal**: Implement Collection flow phase transitions

#### 2.1 Create CollectionPhaseTransitionAgent
- [ ] Extend BaseDecisionAgent
- [ ] Implement Collection-specific phase logic:
  - platform_detection → automated_collection
  - automated_collection → gap_analysis
  - gap_analysis → questionnaire_generation
  - questionnaire_generation → manual_collection
  - manual_collection → synthesis
- [ ] Handle gap analysis results for questionnaire generation

#### 2.2 Update ExecutionEngineCollectionCrews
- [ ] Verify persistent agent usage (already done)
- [ ] Ensure proper phase result formatting
- [ ] Add questionnaire storage logic
- [ ] Implement synthesis phase

### Phase 3: Testing & Validation (Day 3)
**Goal**: Comprehensive testing of Collection flow

#### 3.1 Unit Tests
- [ ] Test phase transition logic for all flow types
- [ ] Test flow registry integration
- [ ] Test fallback mechanisms
- [ ] Test Collection-specific transitions

#### 3.2 Integration Tests
- [ ] Create pytest test in `/tests/backend/test_collection_flow_phases.py`
- [ ] Test complete Collection flow execution
- [ ] Verify questionnaire generation
- [ ] Test phase persistence and recovery

#### 3.3 E2E Tests
- [ ] Create Playwright test in `/tests/e2e/collection-flow-complete.spec.ts`
- [ ] Test UI navigation through all phases
- [ ] Verify questionnaire display
- [ ] Test user interaction with adaptive forms

### Phase 4: Documentation & Deployment (Day 4)
**Goal**: Document changes and prepare for deployment

#### 4.1 Documentation Updates
- [ ] Update Collection flow documentation
- [ ] Document phase transition architecture
- [ ] Update API documentation
- [ ] Create troubleshooting guide

#### 4.2 Migration & Deployment
- [ ] Create migration script for existing flows
- [ ] Update Docker configurations
- [ ] Prepare rollback plan
- [ ] Deploy to staging environment

## Technical Details

### File Changes Required

#### Backend Core Files
```
backend/app/services/flow_orchestration/
├── execution_engine_core.py           # Pass flow_registry to components
├── execution_engine_phase_utils.py    # Use flow registry for transitions
├── execution_engine_agents.py         # Update agent context
└── execution_engine_crew_collection.py # Already updated for persistent agents
```

#### Agent Files
```
backend/app/services/crewai_flows/agents/decision/
├── phase_transition.py     # Make flow-type aware
├── utils.py                # Update DecisionUtils
└── collection_transition.py # NEW: Collection-specific agent
```

#### Flow Registry
```
backend/app/services/
├── flow_type_registry.py                     # Already has correct logic
└── data_collection/collection_flow_registration.py # Verify phase config
```

### Code Snippets

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

#### Collection Phase Transition Logic
```python
class CollectionPhaseTransitionAgent(BaseDecisionAgent):
    def analyze_gap_analysis_results(self, results):
        """Determine questionnaire requirements from gap analysis"""
        gaps = results.get("gaps_identified", [])
        if gaps:
            return AgentDecision(
                action=PhaseAction.PROCEED,
                next_phase="questionnaire_generation",
                confidence=0.9,
                reasoning="Gaps identified, generating adaptive questionnaires"
            )
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