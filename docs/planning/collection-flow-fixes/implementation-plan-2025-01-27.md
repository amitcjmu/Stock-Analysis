# Collection Flow Fix Implementation Plan
Created: 2025-01-27

## Executive Summary
The Collection flow currently starts at GAP_ANALYSIS phase instead of ASSET_SELECTION when initiated from alternate entry points (Adaptive Forms/Bulk Import). This causes assets to never be selected, gap analysis to run without targets, and questionnaires to never be generated. This plan addresses these issues with minimal, surgical changes.

## Root Cause Analysis

### Current Problems
1. **Wrong Start Phase**: Non-Discovery flows start at `GAP_ANALYSIS` instead of `ASSET_SELECTION`
   - Location: `backend/app/api/v1/endpoints/collection_crud_create_commands.py:380-396`
   - Impact: Assets are never selected, breaking the entire flow

2. **No Asset Selection Bootstrap**: System doesn't generate asset selection UI when no assets exist
   - Missing: Bootstrap questionnaire generation in asset_selection phase
   - Impact: Users can't select assets even if phase was correct

3. **Premature Questionnaire Skipping**: Skip logic prevents generation even when gaps exist
   - Location: Questionnaire generation handlers
   - Impact: Valid questionnaires aren't created

4. **Missing Phase Transition**: No automatic progression from ASSET_SELECTION to GAP_ANALYSIS
   - Missing: Phase transition after asset POST
   - Impact: Flow stalls after asset selection

## Implementation Tasks

### Phase 1: Fix Start Phase Configuration (Priority: CRITICAL)

#### Task 1.1: Update create_collection_flow
**File**: `backend/app/api/v1/endpoints/collection_crud_create_commands.py`
**Changes**:
```python
# Line 351-371: Change phase initialization
phase_state = {
    "current_phase": CollectionPhase.ASSET_SELECTION.value,  # Changed from GAP_ANALYSIS
    "phase_history": [
        {
            "phase": CollectionPhase.ASSET_SELECTION.value,  # Changed
            "started_at": datetime.now(timezone.utc).isoformat(),
            "status": "active",
            "metadata": {
                "started_directly": True,
                "reason": "Collection flow starts with asset selection",  # Updated
            },
        }
    ],
    "phase_metadata": {
        "asset_selection": {  # Changed from gap_analysis
            "started_directly": True,
            "requires_user_selection": True,
        }
    },
}

# Line 380: Update status
status=CollectionFlowStatus.ASSET_SELECTION.value,  # Changed from GAP_ANALYSIS

# Line 383: Update current_phase
current_phase=CollectionPhase.ASSET_SELECTION.value,  # Changed from GAP_ANALYSIS

# Line 396: Update start_phase
"start_phase": "asset_selection",  # Changed from gap_analysis
```

#### Task 1.2: Update ensure_collection_flow
**File**: `backend/app/api/v1/endpoints/collection_crud_execution/queries.py`
**Changes**:
- Similar changes to set initial phase to ASSET_SELECTION
- Update default CollectionFlowCreate parameters

### Phase 2: Implement Asset Selection Bootstrap (Priority: HIGH)

#### Task 2.1: Create Bootstrap Questionnaire Generator
**File**: Create `backend/app/services/collection/asset_selection_bootstrap.py`
**Implementation**:
```python
async def generate_asset_selection_bootstrap(
    flow: CollectionFlow,
    db: AsyncSession,
    context: RequestContext
) -> dict:
    """Generate bootstrap questionnaire for asset selection when no assets exist."""

    # Check if assets already selected
    selected_apps = flow.collection_config.get("selected_application_ids", [])
    if selected_apps:
        return {"status": "assets_already_selected", "count": len(selected_apps)}

    # Generate bootstrap questionnaire
    questionnaire = {
        "questionnaire_id": "bootstrap_asset_selection",
        "title": "Select Applications for Collection",
        "description": "Choose applications to analyze for data gaps",
        "type": "asset_selection",
        "fields": await get_available_applications(db, context),
        "required": True,
        "phase": "asset_selection"
    }

    # Store in flow's questionnaire state
    await store_bootstrap_questionnaire(flow, questionnaire, db)

    return {
        "status": "bootstrap_generated",
        "questionnaire_id": questionnaire["questionnaire_id"]
    }
```

#### Task 2.2: Integrate Bootstrap into Phase Runner
**File**: `backend/app/services/phases/handlers/collection/asset_selection_handler.py`
**Changes**:
- Add bootstrap generation when entering asset_selection phase
- Check for empty selected_application_ids
- Generate and serve bootstrap questionnaire

### Phase 3: Fix Phase Transition Logic (Priority: HIGH)

#### Task 3.1: Add Transition After Asset Selection
**File**: `backend/app/api/v1/endpoints/collection.py`
**Location**: POST `/flows/{flow_id}/applications` endpoint
**Changes**:
```python
# After successful asset selection and DB commit:
if flow.current_phase == CollectionPhase.ASSET_SELECTION.value:
    # Transition to GAP_ANALYSIS
    from app.services.master_flow_orchestrator import MasterFlowOrchestrator
    orchestrator = MasterFlowOrchestrator(db, context)

    await orchestrator.update_phase(
        master_flow_id=str(flow.master_flow_id),
        new_phase="gap_analysis",
        metadata={"transitioned_after": "asset_selection"}
    )

    # Update collection flow
    flow.current_phase = CollectionPhase.GAP_ANALYSIS.value
    flow.status = CollectionFlowStatus.GAP_ANALYSIS.value
    await db.commit()
```

### Phase 4: Fix Questionnaire Generation (Priority: MEDIUM)

#### Task 4.1: Update Skip Logic
**File**: `backend/app/services/collection/questionnaire_skip_logic.py`
**Changes**:
```python
def should_skip_detailed_questionnaire(
    flow: CollectionFlow,
    gaps: List[DataGap]
) -> bool:
    """Never skip if gaps exist or assets just selected."""

    # Never skip if gaps found
    if gaps:
        return False

    # Never skip if assets were just selected
    phase_history = flow.phase_state.get("phase_history", [])
    last_phase = phase_history[-1] if phase_history else {}
    if last_phase.get("phase") == "asset_selection":
        return False

    # Apply tier-specific rules
    tier = flow.automation_tier
    if tier in [AutomationTier.TIER_1, AutomationTier.TIER_2]:
        return False  # Never skip for lower tiers

    return flow.collection_config.get("skip_questionnaires", False)
```

### Phase 5: Testing & Validation (Priority: HIGH)

#### Task 5.1: Create E2E Test for Alternate Entry Points
**File**: Create `tests/e2e/collection-alternate-entry.spec.ts`
**Test Cases**:
1. Start from Collection Overview → Adaptive Forms
2. Start from Collection Overview → Bulk Import
3. Verify asset selection UI appears
4. Verify gap analysis runs after selection
5. Verify questionnaires are generated

#### Task 5.2: Backend Integration Tests
**File**: Create `backend/tests/integration/test_collection_alternate_flow.py`
**Test Cases**:
1. Test flow creation starts at ASSET_SELECTION
2. Test bootstrap questionnaire generation
3. Test phase transition after asset POST
4. Test questionnaire generation after gaps

### Phase 6: Documentation Updates (Priority: LOW)

#### Task 6.1: Update Collection Flow Callstack
**File**: `docs/development/callstack/collection-flow-callstack.md`
**Updates**:
- Add "Alternate Entry Points" section
- Document ASSET_SELECTION as starting phase
- Clarify Discovery → Collection is optional
- Document bootstrap questionnaire flow

## Implementation Sequence

### Day 1: Critical Backend Fixes
1. Fix create_collection_flow start phase (Task 1.1)
2. Fix ensure_collection_flow start phase (Task 1.2)
3. Quick smoke test

### Day 2: Asset Selection Bootstrap
1. Implement bootstrap generator (Task 2.1)
2. Integrate into phase handler (Task 2.2)
3. Test bootstrap generation

### Day 3: Phase Transitions & Questionnaires
1. Add transition logic (Task 3.1)
2. Fix questionnaire skip logic (Task 4.1)
3. Integration testing

### Day 4: Testing & Documentation
1. E2E tests (Task 5.1)
2. Backend tests (Task 5.2)
3. Documentation updates (Task 6.1)

## Risk Mitigation

### Feature Flag Approach
```python
# config/feature_flags.py
COLLECTION_FLOW_FIXES = {
    "use_asset_selection_start": os.getenv("FF_COLLECTION_ASSET_START", "true") == "true",
    "enable_bootstrap_questionnaire": os.getenv("FF_BOOTSTRAP_QUESTIONNAIRE", "true") == "true",
    "auto_phase_transition": os.getenv("FF_AUTO_PHASE_TRANSITION", "true") == "true"
}
```

### Rollback Strategy
1. All changes behind feature flags
2. Database migrations are idempotent
3. Can revert to GAP_ANALYSIS start if needed
4. Existing flows unaffected

## Success Criteria

### Functional Requirements
- [ ] Collection flows start at ASSET_SELECTION when initiated from overview
- [ ] Asset selection UI appears and functions
- [ ] Selected assets persist in collection_config
- [ ] Flow transitions to GAP_ANALYSIS after selection
- [ ] Gap analysis runs on selected assets
- [ ] Questionnaires generate for identified gaps

### Non-Functional Requirements
- [ ] No breaking changes to existing flows
- [ ] Performance unchanged (< 2s response times)
- [ ] All tests passing
- [ ] Documentation updated

## Monitoring & Verification

### Key Metrics to Track
1. **Phase Distribution**: Count of flows by starting phase
2. **Asset Selection Rate**: % of flows with selected_application_ids
3. **Questionnaire Generation**: Count of questionnaires per flow
4. **Flow Completion Rate**: % reaching synthesis phase

### SQL Queries for Verification
```sql
-- Check phase distribution
SELECT
    current_phase,
    COUNT(*) as flow_count,
    AVG(CASE WHEN collection_config->>'selected_application_ids' != '[]'
         THEN 1 ELSE 0 END) as has_assets_ratio
FROM migration.collection_flows
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY current_phase;

-- Check questionnaire generation
SELECT
    cf.flow_id,
    cf.current_phase,
    COUNT(q.questionnaire_id) as questionnaire_count
FROM migration.collection_flows cf
LEFT JOIN migration.questionnaires q ON cf.flow_id = q.flow_id
WHERE cf.created_at > NOW() - INTERVAL '7 days'
GROUP BY cf.flow_id, cf.current_phase;
```

## Appendix: File Locations

### Backend Files to Modify
- `/backend/app/api/v1/endpoints/collection_crud_create_commands.py`
- `/backend/app/api/v1/endpoints/collection_crud_execution/queries.py`
- `/backend/app/api/v1/endpoints/collection.py`
- `/backend/app/services/phases/handlers/collection/asset_selection_handler.py`

### Frontend Files (No Changes Required)
- `/src/pages/collection/Index.tsx` - Already handles flow creation correctly
- `/src/components/collection/EnhancedApplicationSelection.tsx` - Already POSTs assets

### New Files to Create
- `/backend/app/services/collection/asset_selection_bootstrap.py`
- `/backend/tests/integration/test_collection_alternate_flow.py`
- `/tests/e2e/collection-alternate-entry.spec.ts`

## Notes for Implementation

1. **Preserve Backward Compatibility**: Existing flows in GAP_ANALYSIS phase continue to work
2. **Atomic Transactions**: All DB changes within transaction boundaries
3. **Logging**: Add detailed logging at each phase transition
4. **Error Handling**: Graceful fallbacks if bootstrap fails

## Review Checklist

- [ ] ADR-006 compliance (Master Flow Orchestrator)
- [ ] Multi-tenant scoping maintained
- [ ] Atomic transactions preserved
- [ ] No breaking changes to API contracts
- [ ] Feature flags implemented
- [ ] Tests written and passing
- [ ] Documentation updated