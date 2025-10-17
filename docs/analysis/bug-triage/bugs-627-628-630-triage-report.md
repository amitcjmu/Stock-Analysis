# Bug Triage Report: Issues #627, #628, #630

**Date**: October 17, 2025
**Triaged By**: Claude Code Agent
**Severity**: All CRITICAL
**Status**: Analysis Complete - Awaiting Implementation

---

## Executive Summary

Three critical bugs have been identified in the Collection → Assessment flow transition:

1. **Bug #627**: Collection Progress UI shows "Complete" despite database showing "Running" at 42.86%
2. **Bug #628**: Assessment API calls missing required multi-tenant security headers
3. **Bug #630**: Assessment master flow created without corresponding child flow (ADR-012 violation)

All three bugs represent architectural violations and must be fixed before production deployment.

---

## Bug #627: Collection Flow Shows "Complete" But Database Shows "Running"

### Severity: CRITICAL - Data Integrity Issue

### Summary
The Collection Progress page displays "Collection Complete" with an enabled "Start Assessment Phase" button, but the database shows:
- Status: `running` (not `completed`)
- Progress: 42.86% (not 100%)
- Current Phase: `questionnaire_generation` (not `finalization`)

This UI/DB state mismatch allows users to proceed to assessment with incomplete collection data.

### Root Cause Analysis

**Primary Issue**: Frontend logic in `Progress.tsx` lines 154-218 checks multiple conditions to show the "Collection Complete" view, but these conditions are incorrectly evaluating to true for running flows.

**Problematic Code** (`src/pages/collection/Progress.tsx:154`):
```typescript
// Phase 1 fix: Show assessment CTA for completed flows
if (showAssessmentCTA || currentFlow?.assessment_ready || currentFlow?.status === 'completed') {
  return (
    // Shows "Collection Complete" UI with "Start Assessment Phase" button
  )
}
```

**Analysis**:
1. **`showAssessmentCTA`** - Set by `useProgressMonitoring` hook at line 428:
   ```typescript
   const shouldShowAssessmentCTA = flow.status === 'completed' || flow.assessment_ready === true;
   ```

2. **Problem**: The `assessment_ready` flag is being set to `true` in the database even though collection is incomplete (42.86%).

3. **Backend Investigation**: Looking at `backend/app/services/collection_transition_service.py:45-56`, the readiness check:
   ```python
   # CRITICAL: Check assessment_ready flag first - overrides gap analysis
   if flow.assessment_ready:
       logger.info(f"✅ Flow {flow_id} has assessment_ready=true - bypassing gap analysis")
       return ReadinessResult(is_ready=True, ...)
   ```

4. **Root Cause**: The `assessment_ready` flag is being set prematurely, likely:
   - By a previous incomplete flow lifecycle operation
   - By a service that incorrectly interprets phase progression
   - By manual database modification (less likely)

### Files Involved

**Frontend**:
- `src/pages/collection/Progress.tsx:154-218` - Conditional rendering logic
- `src/hooks/collection/useProgressMonitoring.ts:428, 497-498` - Assessment CTA flag logic

**Backend**:
- `backend/app/models/collection_flow.py` - `assessment_ready` column definition
- `backend/app/services/collection_transition_service.py:45-56` - Readiness check
- Backend service that sets `assessment_ready=True` prematurely (needs investigation)

### Fix Recommendations

#### Fix 1: Strengthen Frontend Validation (Defensive Programming)

**File**: `src/pages/collection/Progress.tsx:154`

**Current Code**:
```typescript
if (showAssessmentCTA || currentFlow?.assessment_ready || currentFlow?.status === 'completed') {
```

**Recommended Fix**:
```typescript
// Only show assessment CTA if ALL conditions are met
if (
  (showAssessmentCTA || currentFlow?.assessment_ready || currentFlow?.status === 'completed') &&
  currentFlow?.progress >= 95 &&  // Require near-complete progress
  currentFlow?.status !== 'running' &&  // Explicitly exclude running flows
  currentFlow?.status !== 'paused'  // Explicitly exclude paused flows
) {
```

**Rationale**: Add defensive checks to prevent showing "Complete" for running flows, even if `assessment_ready` flag is incorrectly set.

#### Fix 2: Fix Backend Logic That Sets `assessment_ready`

**Action Required**: Search codebase for all locations that set `assessment_ready = True`:

```bash
grep -r "assessment_ready.*=.*True" backend/
```

**Expected Pattern**:
```python
# ❌ WRONG - Sets assessment_ready without checking completion
collection_flow.assessment_ready = True

# ✅ CORRECT - Only set when flow is actually complete
if (
    collection_flow.status == CollectionFlowStatus.completed and
    collection_flow.progress_percentage >= 95.0 and
    collection_flow.current_phase == "finalization"
):
    collection_flow.assessment_ready = True
```

**Files to Investigate**:
- `backend/app/services/collection_flow_service.py`
- `backend/app/services/collection_phase_progression_service.py`
- Any service that updates collection_flow records

#### Fix 3: Add Database Constraint (Long-term)

**File**: New Alembic migration

**Recommended Constraint**:
```python
# In migration file
op.execute("""
    ALTER TABLE migration.collection_flows
    ADD CONSTRAINT check_assessment_ready_requires_completion
    CHECK (
        assessment_ready = FALSE OR
        (
            assessment_ready = TRUE AND
            status = 'completed' AND
            progress_percentage >= 95.0
        )
    );
""")
```

**Rationale**: Prevent database from accepting invalid state at the database level.

### Testing Recommendations

1. **Unit Tests**:
   - Test `useProgressMonitoring` hook with `assessment_ready=true` but `status='running'`
   - Verify "Collection Complete" UI does NOT render for running flows

2. **Integration Tests**:
   - Create collection flow at 42.86% progress with `assessment_ready=true`
   - Navigate to Progress page
   - Assert: Should show "In Progress" UI, NOT "Collection Complete"

3. **E2E Tests**:
   - Complete a full collection flow
   - Verify `assessment_ready` flag is only set when `status='completed'`

---

## Bug #628: Assessment API Call Missing Required Multi-Tenant Headers

### Severity: CRITICAL - Security Violation

### Summary
The frontend makes an API call to `/api/v1/collection/assessment/{flowId}/unmapped-assets` without including required multi-tenant security headers (`X-Client-Account-Id` and `X-Engagement-Id`), resulting in 400 Bad Request errors and complete blocker for assessment workflow.

### Root Cause Analysis

**Primary Issue**: Direct `fetch()` call bypasses the `ApiClient` singleton that automatically adds authentication and multi-tenant headers.

**Problematic Code** (`src/components/assessment/AssetResolutionBanner.tsx:53-61`):
```typescript
const response = await fetch(
  `/api/v1/collection/assessment/${flowId}/unmapped-assets`,
  {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      // ❌ MISSING: X-Client-Account-Id and X-Engagement-Id headers
    },
  }
);
```

**Analysis**:
1. **ApiClient Pattern**: The codebase has a singleton `ApiClient` at `src/services/ApiClient.ts:34-148` that:
   - Automatically adds `Authorization: Bearer {token}` header (line 92-94)
   - Uses centralized configuration (line 60-67)
   - Handles errors consistently

2. **Problem**: `AssetResolutionBanner.tsx` uses raw `fetch()` instead of `ApiClient.getInstance()`

3. **Multi-Tenant Headers**: Per CLAUDE.md, ALL API calls must include:
   ```
   X-Client-Account-Id: {client.id}
   X-Engagement-Id: {engagement.id}
   ```

4. **Backend Enforcement**: Backend at `backend/app/api/v1/endpoints/collection_post_completion.py` (inferred) validates these headers and returns 400 if missing.

### Files Involved

**Frontend**:
- `src/components/assessment/AssetResolutionBanner.tsx:53-61` - Direct fetch() call
- `src/services/ApiClient.ts:34-148` - Centralized API client (not being used)
- `src/contexts/AuthContext.tsx` - Provides client/engagement context

**Backend**:
- `backend/app/api/v1/endpoints/collection_post_completion.py` (inferred) - Endpoint handler
- `backend/app/core/context.py` - Context extraction middleware

### Fix Recommendations

#### Fix 1: Use ApiClient Instead of Raw Fetch

**File**: `src/components/assessment/AssetResolutionBanner.tsx:40-79`

**Current Code**:
```typescript
queryFn: async (): Promise<UnmappedAsset[]> => {
  if (!client?.id || !engagement?.id) {
    console.warn('AssetResolutionBanner: Missing client/engagement context');
    return [];
  }

  try {
    // ❌ Direct fetch bypasses ApiClient
    const response = await fetch(
      `/api/v1/collection/assessment/${flowId}/unmapped-assets`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );
```

**Recommended Fix**:
```typescript
queryFn: async (): Promise<UnmappedAsset[]> => {
  if (!client?.id || !engagement?.id) {
    console.warn('AssetResolutionBanner: Missing client/engagement context');
    return [];
  }

  try {
    // ✅ Use ApiClient with multi-tenant headers
    const data = await apiClient.get<UnmappedAsset[]>(
      `/collection/assessment/${flowId}/unmapped-assets`,
      {
        headers: {
          'X-Client-Account-Id': client.id.toString(),
          'X-Engagement-Id': engagement.id.toString(),
        }
      }
    );

    return Array.isArray(data) ? data : [];
  } catch (error) {
    console.error('Failed to fetch unmapped assets:', error);
    return [];
  }
},
```

**Key Changes**:
1. Replace `fetch()` with `apiClient.get()`
2. Add `X-Client-Account-Id` and `X-Engagement-Id` headers
3. Remove manual response handling (ApiClient handles this)
4. Note: `apiClient` is already imported at line 12: `const apiClient = ApiClient.getInstance();`

#### Fix 2: Create Centralized API Service (Best Practice)

**New File**: `src/services/api/collectionAssessmentService.ts`

```typescript
import { ApiClient } from '../ApiClient';
import type { UnmappedAsset } from '@/types/collection/unmapped-assets';

const apiClient = ApiClient.getInstance();

export const collectionAssessmentService = {
  /**
   * Get unmapped assets for an assessment flow
   * Automatically includes multi-tenant headers
   */
  async getUnmappedAssets(
    assessmentFlowId: string,
    clientAccountId: number,
    engagementId: number
  ): Promise<UnmappedAsset[]> {
    return apiClient.get<UnmappedAsset[]>(
      `/collection/assessment/${assessmentFlowId}/unmapped-assets`,
      {
        headers: {
          'X-Client-Account-Id': clientAccountId.toString(),
          'X-Engagement-Id': engagementId.toString(),
        }
      }
    );
  },

  // Add other assessment-related endpoints here
};
```

**Then use in component**:
```typescript
import { collectionAssessmentService } from '@/services/api/collectionAssessmentService';

// In queryFn:
const data = await collectionAssessmentService.getUnmappedAssets(
  flowId,
  client.id,
  engagement.id
);
```

**Rationale**: Centralizes multi-tenant header logic, makes it reusable, and easier to maintain.

#### Fix 3: Add Global Axios Interceptor (Alternative Approach)

If the codebase wants to automatically add multi-tenant headers to ALL requests:

**File**: `src/services/ApiClient.ts:77-126` (in `request` method)

**Add after line 94**:
```typescript
// Add auth token if available
try {
  const token = tokenStorage.getToken();
  if (token && !headers['Authorization']) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  // ✅ ADD: Automatically add multi-tenant headers from auth context
  // Import from AuthContext storage
  const authState = getAuthStateFromStorage(); // Need to implement this helper
  if (authState?.client?.id && !headers['X-Client-Account-Id']) {
    headers['X-Client-Account-Id'] = authState.client.id.toString();
  }
  if (authState?.engagement?.id && !headers['X-Engagement-Id']) {
    headers['X-Engagement-Id'] = authState.engagement.id.toString();
  }
} catch (e) {
  // Ignore errors
}
```

**Pros**: All API calls automatically get multi-tenant headers
**Cons**: Requires accessing auth context from outside React component tree (non-trivial)

### Testing Recommendations

1. **Unit Tests**:
   - Test `collectionAssessmentService.getUnmappedAssets()` includes correct headers
   - Mock `ApiClient.get()` and verify header values

2. **Integration Tests**:
   - Make actual API call to unmapped-assets endpoint
   - Assert: Returns 200 OK (not 400 Bad Request)
   - Assert: Response includes expected unmapped assets data

3. **E2E Tests**:
   - Navigate to assessment page
   - Open browser DevTools Network tab
   - Assert: `/unmapped-assets` request includes `X-Client-Account-Id` and `X-Engagement-Id` headers
   - Assert: No 400 errors in console

---

## Bug #630: Assessment Master Flow Created Without Child Flow

### Severity: CRITICAL - Architectural Violation (ADR-012)

### Summary
When transitioning from collection to assessment, the system creates a master flow record in `crewai_flow_state_extensions` but fails to create the corresponding child flow record in `assessment_flows`. This violates the mandatory two-table pattern (ADR-012) and causes the frontend to fail with "No applications loaded yet" because there's no child flow data to display.

### Root Cause Analysis

**Primary Issue**: The `CollectionTransitionService.create_assessment_flow()` method creates assessment flows using `AssessmentFlowRepository.create_assessment_flow()`, which creates ONLY the child flow, not the master flow. However, somewhere in the flow a master flow IS being created (as evidenced by DB query showing master flow exists), suggesting a race condition or ordering issue.

**Analysis**:

1. **Transition Endpoint** (`backend/app/api/v1/endpoints/collection_transition.py:21-57`):
   ```python
   async def transition_to_assessment(flow_id: UUID, ...):
       # Validate readiness
       readiness = await transition_service.validate_readiness(flow_id)

       # Create assessment via MFO/Repository
       result = await transition_service.create_assessment_flow(flow_id)
   ```

2. **Transition Service** (`backend/app/services/collection_transition_service.py:186-282`):
   ```python
   async def create_assessment_flow(self, collection_flow_id: UUID):
       # Get collection flow
       collection_flow = await self._get_collection_flow(collection_flow_id)

       # Create assessment with MFO pattern
       assessment_flow_id = await assessment_repo.create_assessment_flow(
           engagement_id=str(self.context.engagement_id),
           selected_application_ids=selected_app_ids,
           created_by=str(self.context.user_id),
           collection_flow_id=str(collection_flow.id)
       )
   ```

3. **Problem**: `assessment_repo.create_assessment_flow()` likely creates ONLY the child flow. The master flow creation must happen ATOMICALLY with the child flow creation per ADR-012.

4. **Expected Pattern** (from coding-agent-guide.md):
   ```python
   # ✅ CORRECT - Atomic pattern
   async with db.begin():
       # Create master flow first
       master_flow_id = await orchestrator.create_flow(
           flow_type="assessment",
           ...
       )
       await db.flush()  # Makes ID available for child

       # Create child flow with master_flow_id FK
       child_flow = AssessmentFlow(
           master_flow_id=master_flow_id,
           ...
       )
       db.add(child_flow)
       await db.commit()  # Single commit for both
   ```

5. **Current Issue**: The code is likely creating child flow WITHOUT master_flow_id, then attempting to create master flow separately, OR creating master flow but not linking it to child flow.

### Files Involved

**Backend**:
- `backend/app/services/collection_transition_service.py:186-282` - create_assessment_flow method
- `backend/app/repositories/assessment_flow_repository.py` - create_assessment_flow method (needs investigation)
- `backend/app/services/master_flow_orchestrator/lifecycle_commands.py` - create_flow method
- `backend/app/models/assessment_flow/core_models.py` - AssessmentFlow model with master_flow_id FK

**Database Schema**:
- `migration.crewai_flow_state_extensions` - Master flow table
- `migration.assessment_flows` - Child flow table with `master_flow_id` FK to master table

### Fix Recommendations

#### Fix 1: Implement Atomic Two-Table Creation

**File**: `backend/app/services/collection_transition_service.py:186-282`

**Current Code** (simplified):
```python
async def create_assessment_flow(self, collection_flow_id: UUID):
    try:
        collection_flow = await self._get_collection_flow(collection_flow_id)

        # ❌ Creates only child flow
        assessment_flow_id = await assessment_repo.create_assessment_flow(
            engagement_id=str(self.context.engagement_id),
            selected_application_ids=selected_app_ids,
            ...
        )

        # Get the created assessment flow
        assessment_result = await self.db.execute(
            select(AssessmentFlow).where(AssessmentFlow.id == assessment_flow_id)
        )
        assessment_flow = assessment_result.scalar_one()

        return TransitionResult(
            assessment_flow_id=assessment_flow.id,
            ...
        )
```

**Recommended Fix**:
```python
async def create_assessment_flow(self, collection_flow_id: UUID):
    """
    Create assessment flow with proper two-table pattern.
    Creates both master flow AND child flow atomically.
    """
    try:
        collection_flow = await self._get_collection_flow(collection_flow_id)

        # ✅ STEP 1: Create master flow first
        from app.services.master_flow_orchestrator import MasterFlowOrchestrator

        orchestrator = MasterFlowOrchestrator(self.db, self.context)

        master_flow_id = await orchestrator.create_flow(
            flow_type="assessment",
            client_account_id=self.context.client_account_id,
            engagement_id=self.context.engagement_id,
            user_id=self.context.user_id,
            flow_config={
                "source_collection_flow_id": str(collection_flow.id),
                "transition_type": "collection_to_assessment",
            }
        )

        # Flush to get master_flow_id in DB (but don't commit yet)
        await self.db.flush()

        # ✅ STEP 2: Create child flow with master_flow_id FK
        from app.models.assessment_flow.core_models import AssessmentFlow
        from uuid import uuid4

        # Get selected application IDs
        selected_app_ids = []
        if (
            collection_flow.collection_config and
            collection_flow.collection_config.get("selected_application_ids")
        ):
            selected_app_ids = collection_flow.collection_config["selected_application_ids"]

        # Create child flow record
        assessment_flow = AssessmentFlow(
            id=uuid4(),
            master_flow_id=master_flow_id,  # ✅ Link to master flow
            client_account_id=self.context.client_account_id,
            engagement_id=self.context.engagement_id,
            flow_name=f"Assessment for {collection_flow.flow_name}",
            description=f"Assessment created from collection flow {collection_flow.flow_id}",
            status="initialized",
            current_phase="initialization",
            progress=0.0,
            configuration={
                "collection_flow_id": str(collection_flow.id),
                "selected_application_ids": [str(app_id) for app_id in selected_app_ids],
                "transition_date": datetime.utcnow().isoformat(),
            },
            flow_metadata={
                "source": "collection_transition",
                "created_by_service": "collection_transition_service",
            },
            started_at=datetime.utcnow(),
        )

        self.db.add(assessment_flow)

        # ✅ STEP 3: Flush to get child flow ID
        await self.db.flush()

        # Update collection flow with assessment linkage
        if hasattr(collection_flow, "assessment_flow_id"):
            collection_flow.assessment_flow_id = assessment_flow.id
            collection_flow.assessment_transition_date = datetime.utcnow()

        # Store bidirectional references in metadata
        current_metadata = getattr(collection_flow, "flow_metadata", {}) or {}
        collection_flow.flow_metadata = {
            **current_metadata,
            "assessment_handoff": {
                "assessment_flow_id": str(assessment_flow.id),
                "assessment_master_flow_id": str(master_flow_id),
                "transitioned_at": datetime.utcnow().isoformat(),
            },
        }

        # ✅ STEP 4: Commit transaction - both master and child created atomically
        await self.db.commit()

        logger.info(
            f"✅ Created assessment flow atomically: "
            f"master={master_flow_id}, child={assessment_flow.id}"
        )

        return TransitionResult(
            assessment_flow_id=assessment_flow.id,
            assessment_flow=assessment_flow,
            created_at=datetime.utcnow(),
        )

    except Exception as e:
        await self.db.rollback()
        logger.error(f"Failed to create assessment flow: {e}", exc_info=True)
        raise
```

**Key Changes**:
1. Create master flow FIRST using `MasterFlowOrchestrator`
2. Flush to get `master_flow_id` without committing
3. Create child flow with `master_flow_id` FK
4. Flush to get child flow ID
5. Update collection flow linkage
6. Commit ONCE for entire transaction (atomic)

#### Fix 2: Validate Two-Table Pattern After Creation

**Add validation method to service**:

```python
async def _validate_assessment_flow_creation(
    self,
    master_flow_id: UUID,
    child_flow_id: UUID
) -> bool:
    """
    Validate that both master and child flows exist and are linked.
    Per ADR-012, this is REQUIRED for all flows.
    """
    # Check master flow exists
    master_result = await self.db.execute(
        select(CrewAIFlowStateExtensions).where(
            CrewAIFlowStateExtensions.flow_id == master_flow_id
        )
    )
    master_flow = master_result.scalar_one_or_none()

    if not master_flow:
        raise ValueError(
            f"Master flow {master_flow_id} not found - violates ADR-012"
        )

    # Check child flow exists
    child_result = await self.db.execute(
        select(AssessmentFlow).where(
            AssessmentFlow.id == child_flow_id
        )
    )
    child_flow = child_result.scalar_one_or_none()

    if not child_flow:
        raise ValueError(
            f"Child flow {child_flow_id} not found - violates ADR-012"
        )

    # Check linkage
    if child_flow.master_flow_id != master_flow_id:
        raise ValueError(
            f"Child flow {child_flow_id} not linked to master flow {master_flow_id} - violates ADR-012"
        )

    logger.info(
        f"✅ Two-table pattern validated: master={master_flow_id}, child={child_flow_id}"
    )
    return True
```

**Call after creation**:
```python
# After creating both flows
await self._validate_assessment_flow_creation(master_flow_id, assessment_flow.id)
```

#### Fix 3: Add Database Foreign Key Constraint (If Not Present)

**New Alembic Migration**:

```python
"""
Add FK constraint for assessment_flows.master_flow_id

Revision ID: 095_assessment_master_flow_fk
"""

from alembic import op
import sqlalchemy as sa

def upgrade():
    # Check if FK already exists
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'fk_assessment_flows_master_flow_id'
            ) THEN
                ALTER TABLE migration.assessment_flows
                ADD CONSTRAINT fk_assessment_flows_master_flow_id
                FOREIGN KEY (master_flow_id)
                REFERENCES migration.crewai_flow_state_extensions(flow_id)
                ON DELETE RESTRICT;
            END IF;
        END
        $$;
    """)

    # Add NOT NULL constraint (if not already present)
    op.execute("""
        DO $$
        BEGIN
            ALTER TABLE migration.assessment_flows
            ALTER COLUMN master_flow_id SET NOT NULL;
        EXCEPTION
            WHEN others THEN
                -- Constraint may already exist
                NULL;
        END
        $$;
    """)

def downgrade():
    op.execute("""
        ALTER TABLE migration.assessment_flows
        DROP CONSTRAINT IF EXISTS fk_assessment_flows_master_flow_id;
    """)

    op.execute("""
        ALTER TABLE migration.assessment_flows
        ALTER COLUMN master_flow_id DROP NOT NULL;
    """)
```

**Rationale**: Enforces two-table pattern at database level, prevents orphaned child flows.

### Testing Recommendations

1. **Unit Tests**:
   ```python
   # Test atomic creation
   async def test_create_assessment_flow_atomic():
       result = await transition_service.create_assessment_flow(collection_flow_id)

       # Assert master flow exists
       master_flow = await db.get(CrewAIFlowStateExtensions, result.master_flow_id)
       assert master_flow is not None

       # Assert child flow exists
       child_flow = await db.get(AssessmentFlow, result.assessment_flow_id)
       assert child_flow is not None

       # Assert linkage
       assert child_flow.master_flow_id == master_flow.flow_id
   ```

2. **Integration Tests**:
   - Create collection flow
   - Transition to assessment
   - Query both `crewai_flow_state_extensions` and `assessment_flows`
   - Assert: Both exist and are linked

3. **E2E Tests**:
   - Complete collection flow
   - Click "Start Assessment Phase"
   - Navigate to assessment page
   - Assert: Assessment page loads with application data (not "No applications loaded yet")
   - Assert: No console errors

---

## Summary of All Fixes

### Immediate Actions (P0)

1. **Bug #630** (BLOCKER):
   - Implement atomic two-table creation in `collection_transition_service.py`
   - Add validation after creation
   - Test thoroughly before any other fixes

2. **Bug #628** (SECURITY):
   - Replace raw `fetch()` with `ApiClient` in `AssetResolutionBanner.tsx`
   - Add `X-Client-Account-Id` and `X-Engagement-Id` headers
   - Verify no other components use raw `fetch()`

3. **Bug #627** (DATA INTEGRITY):
   - Add defensive checks to `Progress.tsx` UI rendering
   - Investigate and fix backend service setting `assessment_ready=true` prematurely
   - Consider adding database constraint

### Testing Strategy

1. **Sequential Fix Order**:
   - Fix #630 first (enables assessment flow)
   - Fix #628 second (enables asset loading in assessment)
   - Fix #627 last (prevents premature transitions)

2. **Integration Testing**:
   - Test full collection → assessment transition
   - Verify no 400 errors
   - Verify "Collection Complete" only shows for completed flows
   - Verify assessment flow has both master and child records

3. **Regression Testing**:
   - Test existing completed collection flows
   - Test paused collection flows
   - Test failed collection flows
   - Verify no breaking changes to discovery or plan flows

---

## Code Review Checklist

Before marking these bugs as resolved:

- [ ] All three fixes implemented
- [ ] Unit tests passing for all changes
- [ ] Integration tests added and passing
- [ ] E2E test validates full collection → assessment flow
- [ ] No 400 errors in browser console
- [ ] No 404 errors for API endpoints
- [ ] Database queries show both master and child flows exist
- [ ] "Collection Complete" only shows for actually completed flows
- [ ] Assessment page loads with application data
- [ ] Multi-tenant headers present in all assessment API calls
- [ ] ADR-012 two-table pattern validated
- [ ] No breaking changes to other flows (discovery, plan)

---

## References

- **ADR-012**: Flow Status Management Separation (`/docs/adr/012-flow-status-management-separation.md`)
- **CLAUDE.md**: Multi-Tenant Security and Two-Table Pattern requirements
- **Coding Agent Guide**: `/docs/analysis/Notes/coding-agent-guide.md` - Missing Child Records & MFO Atomicity section
- **Bug Issues**: #627, #628, #630 on GitHub

---

**End of Triage Report**
