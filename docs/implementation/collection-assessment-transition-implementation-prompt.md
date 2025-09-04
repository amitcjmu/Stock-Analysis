# Collection to Assessment Transition - Implementation Prompt

## Overview
You are tasked with implementing a critical fix for the collection flow endless loop issue and establishing a proper transition mechanism from Collection to Assessment phase. The implementation plan has been thoroughly reviewed and validated by multiple CC agents and GPT5.

## Critical Context
- **PROBLEM**: Users are stuck in an endless loop between `/collection/adaptive-forms?flowId={id}` and `/collection/progress/{id}`
- **ROOT CAUSE**: No transition mechanism exists from collection completion to assessment initiation
- **SOLUTION**: Implement UI gating + dedicated transition endpoint WITHOUT modifying existing `continueFlow`

## Implementation Plan Location
The complete, validated implementation plan is at:
`/docs/planning/collection-flow/collection-to-assessment-transition-plan-v2.md`

## Implementation Phases

### Phase 1: Immediate UI Loop Fix (CRITICAL - Do First)
**Files to modify:**
- `src/hooks/collection/useProgressMonitoring.ts`
- `src/pages/collection/Progress.tsx`

**Key changes:**
1. Add gating logic to detect `flow?.status === 'completed'` or `flow?.assessment_ready === true`
2. Show "Go to Assessment" CTA instead of "Continue" for completed flows
3. Navigate to `/assessment/overview` (existing route)

### Phase 2: Backend Transition Endpoint
**Files to create/modify:**
- CREATE: `backend/app/api/v1/endpoints/collection_transition.py`
- CREATE: `backend/app/services/collection_transition_service.py`
- CREATE: `backend/app/schemas/collection_transition.py`
- MODIFY: `backend/app/api/v1/router_registry.py`

**Key requirements:**
- Use `get_db` from `app.core.database` (NOT `get_async_db`)
- Use correct field names: `flow_name`, `flow_metadata`
- Use `AgentConfiguration.get_agent_config("readiness_assessor")` for safe agent config
- Implement proper tenant scoping in all queries
- Use `await db.flush()` in transactions (no manual commit)

### Phase 3: Frontend Integration
**Files to modify:**
- `src/services/api/collection-flow.ts`
- `src/pages/collection/Progress.tsx`

**Key requirements:**
- Add `transitionToAssessment()` method using `apiCall` utility
- Use `toast` hook from `@/components/ui/use-toast` (NOT showNotification)
- All interfaces use snake_case fields
- Navigate to `/assessment/${assessment_flow_id}/architecture` after transition

### Phase 4: Database Migration
**File to create:**
- `backend/alembic/versions/048_add_assessment_transition_tracking.py`

**Key requirements:**
- Idempotent column checks using information_schema
- Add pgvector column for gap analysis embeddings (1024 dimensions)
- Proper rollback with index cleanup
- Schema should be 'migration'

## Validation Requirements

### Unit Tests
1. Test UI gating prevents calling continueFlow when completed
2. Test transition endpoint with proper tenant scoping
3. Test migration idempotency
4. Test error handling for not_ready responses

### E2E Test Flow
1. Complete a collection flow
2. Verify progress page shows "Go to Assessment" CTA
3. Click CTA → verify navigation to `/assessment/overview`
4. Verify assessment readiness is detected
5. Start assessment → verify navigation to `/assessment/{flowId}/architecture`

## Git Workflow

### Branch Setup
```bash
# Create feature branch from main
git checkout main
git pull origin main
git checkout -b feature/collection-assessment-transition

# Commit strategy
# Commit 1: UI loop fix (Phase 1)
# Commit 2: Backend transition service (Phase 2)  
# Commit 3: Frontend integration (Phase 3)
# Commit 4: Database migration (Phase 4)
# Commit 5: Tests and validation
```

### PR Description Template
```markdown
## Fix Collection to Assessment Transition & Endless Loop

### Problem
Users were getting stuck in an endless loop when trying to continue completed collection flows. The system lacked a proper transition mechanism from collection to assessment phase.

### Solution
Implemented a comprehensive transition system with:
1. **Immediate UI gating** to stop the loop
2. **Dedicated transition endpoint** that doesn't modify existing APIs
3. **Agent-driven readiness assessment** without hardcoded thresholds
4. **Proper route alignment** with existing assessment pages

### Changes
- ✅ UI gating in Progress page to detect completion
- ✅ New `/transition-to-assessment` endpoint
- ✅ CollectionTransitionService with tenant scoping
- ✅ Frontend integration with toast notifications
- ✅ Idempotent database migration with pgvector support

### Testing
- [ ] Manual testing of collection flow completion
- [ ] E2E test with Playwright validation
- [ ] Migration tested on local database
- [ ] No breaking changes to existing APIs

### Architecture Alignment
- Uses existing `GapAnalysisSummaryService`
- Leverages `TenantScopedAgentPool` for AI decisions
- Maintains backward compatibility
- No modifications to `continueFlow` endpoint

Fixes: Collection flow endless loop issue
Related: collection-to-assessment-transition-plan-v2.md
```

## Important Constraints

### DO NOT:
- ❌ Modify the existing `continueFlow` endpoint
- ❌ Use `get_async_db` (use `get_db` instead)
- ❌ Use camelCase in API responses (use snake_case)
- ❌ Use hardcoded thresholds (use agent-driven decisions)
- ❌ Create new assessment routes (use existing ones)
- ❌ Use `showNotification` (use `toast` hook)

### MUST DO:
- ✅ Fix the loop IMMEDIATELY with UI gating (Phase 1 first)
- ✅ Create dedicated transition endpoint (don't modify existing)
- ✅ Use proper tenant scoping in all database queries
- ✅ Follow existing codebase patterns exactly
- ✅ Test with Playwright before creating PR
- ✅ Maintain backward compatibility

## Success Criteria
1. Users can no longer get stuck in the collection flow loop
2. Completed collections show "Go to Assessment" CTA
3. Transition to assessment works seamlessly
4. All existing functionality remains unaffected
5. Code passes all linting and type checks
6. Playwright E2E tests validate the flow

## Additional Resources
- Full implementation plan: `/docs/planning/collection-flow/collection-to-assessment-transition-plan-v2.md`
- Collection flow model: `backend/app/models/collection_flow.py`
- Assessment flow model: `backend/app/models/assessment_flow/core_models.py`
- Existing routes: `src/App.tsx` (lines 284-312 for assessment routes)

## Contact for Questions
If you encounter any blockers or need clarification:
1. Review the v2 plan document thoroughly
2. Check the "Critical Implementation Corrections" section
3. Validate against existing patterns in the codebase
4. Use CC agents for specific domain expertise