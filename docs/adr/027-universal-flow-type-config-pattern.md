# ADR-027: Universal FlowTypeConfig Pattern and Discovery Phase Consolidation

## Status
Proposed

## Context

### Current State Problems

1. **Multiple Phase Definition Patterns**
   - Discovery uses `PHASE_SEQUENCES` enum-based pattern
   - Collection/Assessment use `FlowTypeConfig` rich configuration pattern
   - New developers confused about which pattern to use
   - Maintenance burden on both code paths

2. **Scattered Phase Definitions**
   ```
   backend/app/utils/flow_constants/flow_states.py           # PHASE_SEQUENCES
   backend/app/services/flow_configs/discovery_phase_constants.py  # Duplicate
   backend/app/services/crewai_flows/unified_discovery_flow/flow_config.py  # PHASE_ORDER
   backend/app/services/flow_continuation/simple_flow_router.py  # PHASE_PROGRESSION
   backend/app/services/agents/flow_processing/tools/route_decision.py  # ROUTE_MAPPING
   backend/app/services/flow_orchestration/transition_utils.py  # discovery_phases
   backend/app/services/discovery/phase_persistence_helpers/base.py  # transitions
   src/config/flowRoutes.ts  # Frontend hardcoded
   ```

3. **Discovery Phase Scope Conflict**
   - `flow_states.py`: Discovery includes `dependency_analysis` and `tech_debt_analysis`
   - `transition_utils.py`: Discovery ends at `asset_inventory`
   - Product decision: Move dependency/tech_debt to Assessment flow
   - No authoritative source enforcing this

4. **Discovery Missing FlowTypeConfig Benefits**
   - No validators, pre/post handlers
   - No retry configuration
   - No timeout management
   - No rich metadata for UI
   - Ad-hoc logic scattered across services

5. **Frontend/Backend Drift**
   - Frontend uses `attribute_mapping`, backend uses `field_mapping`
   - Frontend omits `tech_debt` from discovery sequence
   - No API contract for phase definitions

## Decision

### 1. FlowTypeConfig as Universal Pattern

**All flows SHALL use `FlowTypeConfig` pattern exclusively.**

```python
# backend/app/services/flow_configs/{flow}_flow_config.py
def get_{flow}_flow_config() -> FlowTypeConfig:
    return FlowTypeConfig(
        name="flow_name",
        phases=[
            PhaseConfig(...),
            PhaseConfig(...),
        ],
        child_flow_service=ChildFlowService,  # Per ADR-025
        capabilities=FlowCapabilities(...),
    )
```

**Benefits**:
- Single pattern to learn/maintain
- Rich validation, retry, timeout configuration
- Metadata for UI rendering
- Pre/post handler hooks
- Consistent with ADR-025 child_flow_service mandate

### 2. Canonical Discovery Phase Sequence

**Discovery flow SHALL contain ONLY these phases** (dependency/tech_debt moved to Assessment):

```python
CANONICAL_DISCOVERY_PHASES = [
    "initialization",
    "data_import",
    "data_validation",
    "field_mapping",
    "data_cleansing",
    "asset_inventory",
    "finalization",
]
```

**Rationale**:
- Dependency analysis requires relationships between assets (Assessment concern)
- Tech debt assessment requires business context and priorities (Assessment concern)
- Discovery focuses on data acquisition and normalization
- Cleaner separation of concerns

**Database Impact**:
- Keep `dependency_analysis_completed` and `tech_debt_assessment_completed` flags for backward compatibility
- Mark as deprecated in schema comments
- Assessment flow will populate these fields going forward

### 3. Assessment Flow Expansion

**Assessment SHALL include these phases**:

```python
CANONICAL_ASSESSMENT_PHASES = [
    "initialization",
    "readiness_assessment",
    "complexity_analysis",
    "dependency_analysis",      # ← Moved from Discovery
    "tech_debt_assessment",     # ← Moved from Discovery
    "risk_assessment",
    "recommendation_generation",
    "finalization",
]
```

### 4. Phase Naming Standard

**All phase names SHALL follow these rules**:

| Context | Format | Example |
|---------|--------|---------|
| Python Enum | `UPPER_SNAKE_CASE` | `FlowPhase.FIELD_MAPPING` |
| Database | `snake_case` | `field_mapping_completed` |
| API/JSON | `snake_case` | `"field_mapping"` |
| Frontend | `snake_case` | `"field_mapping"` |
| Display | `Title Case` | `"Field Mapping"` |

**Alias Compatibility Layer**:
```python
# backend/app/services/flow_configs/phase_aliases.py
PHASE_ALIASES = {
    "discovery": {
        "attribute_mapping": "field_mapping",
        "inventory": "asset_inventory",
        "dependencies": "dependency_analysis",
        "tech_debt": "tech_debt_assessment",
        # ... other legacy names
    },
    # ... other flows
}
```

### 5. Single Source of Truth

**FlowTypeConfig SHALL be the authoritative source**:

```python
# Query phases for any flow
config = get_flow_config(flow_type)
phases = [phase.name for phase in config.phases]

# Phase validation
def is_valid_phase(flow_type: str, phase: str) -> bool:
    config = get_flow_config(flow_type)
    phase_names = [p.name for p in config.phases]
    return phase in phase_names or phase in get_aliases(flow_type)
```

**Deprecation Path**:
```python
# backend/app/utils/flow_constants/flow_states.py
@deprecated("Use get_flow_config() instead")
PHASE_SEQUENCES: Dict[FlowType, List[FlowPhase]] = {
    # Kept for backward compatibility only
    # Will be removed in v3.0.0
}
```

### 6. API Contract for Phases

**Backend SHALL expose phases via REST API**:

```python
GET /api/v1/flow-metadata/phases
{
    "discovery": {
        "phases": ["initialization", "data_import", ...],
        "phase_details": [
            {
                "name": "data_import",
                "display_name": "Data Import",
                "order": 1,
                "estimated_duration_minutes": 10,
                "can_pause": true,
                "can_skip": false
            },
            ...
        ]
    },
    ...
}
```

**Frontend SHALL fetch from API**:
```typescript
// src/hooks/useFlowPhases.ts
export function useFlowPhases(flowType: FlowType) {
    return useQuery(['flow-phases', flowType], () =>
        apiCall(`/api/v1/flow-metadata/phases/${flowType}`)
    );
}
```

### 7. Migration Strategy

**Phased migration** to minimize risk:

1. **Phase 1**: Create Discovery FlowTypeConfig (parallel path)
2. **Phase 2**: Feature flag to switch between old/new
3. **Phase 3**: Move all consumers to new path
4. **Phase 4**: Remove old path, deprecate PHASE_SEQUENCES
5. **Phase 5**: Frontend migration to API-driven phases

## Consequences

### Positive

1. **Single Pattern**: One way to define flows, easier onboarding
2. **Rich Metadata**: All flows get validators, retries, timeouts
3. **Consistency**: Backend/frontend synchronized via API
4. **Maintainability**: Changes in one place propagate everywhere
5. **Clarity**: Dependency/tech_debt clearly in Assessment
6. **Extensibility**: Easy to add new phases/flows

### Negative

1. **Migration Effort**: 3-5 days to complete migration
2. **Risk**: Could break existing flows if not careful
3. **Testing**: Must verify all phase transitions still work
4. **Documentation**: Need to update all docs/guides

### Mitigation

1. **Feature Flags**: A/B test new implementation
2. **Comprehensive Tests**: Integration tests for all flows
3. **Rollback Plan**: Keep old code until proven stable
4. **Monitoring**: Track phase transitions, flag anomalies

## Implementation Plan

See detailed implementation plan document.

## References

- ADR-025: Child Flow Service Pattern
- ADR-012: Flow Status Management Separation
- [FlowTypeConfig Pattern Documentation]
- [Collection Flow Implementation] (proven example)
- [Assessment Flow Implementation] (proven example)

## Approval

- [ ] Product Owner: Phase scope change (dependency/tech_debt to Assessment)
- [ ] Architecture Review: Universal FlowTypeConfig pattern
- [ ] Tech Lead: Implementation approach
- [ ] QA Lead: Testing strategy

## Timeline

- ADR Approval: [Date]
- Implementation Start: [Date]
- Phase 1 Complete: [Date + 2 days]
- Phase 5 Complete: [Date + 5 days]
- Old Code Removal: [Date + 10 days]
