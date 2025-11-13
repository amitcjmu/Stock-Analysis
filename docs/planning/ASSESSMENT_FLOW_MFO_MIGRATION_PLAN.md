# Assessment Flow MFO Migration Plan - Option B

**Status**: Planning
**Priority**: P0 - Critical Architecture Fix
**Estimated Effort**: 4-5 weeks
**Issue**: #611 - Assessment Flow Complete - Treatments Visible

---

## Executive Summary

### Problem Statement
The codebase has **two parallel implementations** for 6R migration recommendations:

1. **Assessment Flow** (Original Design) - DISABLED since Sept 9, 2025
   - Uses `assessments` table
   - Endpoints: `/api/v1/assessment-flow/*`
   - Status: Commented out due to "MFO architecture violation"
   - Comprehensive data model with wave planning

2. **6R Analysis Flow** (Redundant Implementation) - ACTIVE
   - Uses `sixr_analyses`, `sixr_iterations`, `sixr_recommendations` tables
   - Endpoints: `/api/v1/6r/*`
   - Status: Production use, but violates architecture
   - Direct API calls, bypasses MFO

### Solution
**Remove 6R Analysis implementation entirely** and properly implement Assessment Flow with MFO integration.

### Benefits
- ✅ Single source of truth for 6R recommendations
- ✅ Proper MFO architecture compliance
- ✅ Comprehensive data model (includes wave planning)
- ✅ Prevents future confusion and duplicate code
- ✅ Aligns with ADR-006 (Master Flow Orchestrator)

---

## Migration Phases

### Phase 1: Code Audit and Protection (Week 1, Days 1-2)

**Objective**: Prevent accidental use of 6R Analysis during migration

#### Tasks

**1.1 Create Feature Flag to Disable 6R Analysis**
```python
# backend/app/core/feature_flags.py
SIXR_ANALYSIS_DEPRECATED = True  # Set to True to disable old 6R endpoints
```

**1.2 Add Deprecation Warnings**
- Add HTTP 410 Gone responses to all `/6r/*` endpoints
- Log warnings when old code paths are accessed
- Add frontend console warnings when old components load

**1.3 Document Current State**
- Export current `sixr_analyses` data for migration reference
- Document all existing 6R Analysis API contracts
- List all frontend components using `sixrApi`

**Deliverables**:
- [ ] Feature flag added to disable 6R endpoints
- [ ] Deprecation warnings on all 6R endpoints
- [ ] Current state documentation
- [ ] Data export SQL scripts

**Files to Modify**:
- `backend/app/core/feature_flags.py`
- `backend/app/api/v1/endpoints/sixr_analysis.py` (add deprecation)
- `docs/planning/SIXR_ANALYSIS_CURRENT_STATE.md` (create)

---

### Phase 2: Enable Assessment Flow with MFO Integration (Week 1-2)

**Objective**: Re-enable Assessment Flow and integrate with Master Flow Orchestrator

#### Tasks

**2.1 Enable Assessment Flow Router**
```python
# backend/app/api/v1/router_registry.py
# REMOVE these lines:
# # Direct assessment-flow endpoints violate MFO architecture principles
# # All assessment operations should go through Master Flow Orchestrator
# if ASSESSMENT_FLOW_AVAILABLE:
#     api_router.include_router(assessment_flow_router, prefix="/assessment-flow")

# ADD:
if ASSESSMENT_FLOW_AVAILABLE:
    api_router.include_router(assessment_flow_router, prefix="/assessment-flow")
    logger.info("✅ Assessment Flow API router included at /assessment-flow")
```

**2.2 Create MFO Integration Layer**

Create new file: `backend/app/api/v1/endpoints/assessment_flow/mfo_integration.py`

```python
"""
MFO Integration for Assessment Flow.
Routes assessment operations through Master Flow Orchestrator per ADR-006.
"""

async def create_assessment_via_mfo(
    client_account_id: UUID,
    engagement_id: UUID,
    application_ids: List[UUID],
    db: AsyncSession
) -> dict:
    """
    Create assessment flow through MFO.

    Flow:
    1. Register master flow in crewai_flow_state_extensions
    2. Create child assessment flow in assessment_flows table
    3. Link via flow_id
    4. Return unified state
    """
    # Implementation per ADR-006 two-table pattern
    pass

async def get_assessment_status_via_mfo(
    flow_id: UUID,
    db: AsyncSession
) -> dict:
    """
    Get assessment status from both master and child tables.

    Returns unified view:
    - Master flow: running/paused/completed
    - Child flow: current_phase, operational state
    """
    pass

async def update_assessment_via_mfo(
    flow_id: UUID,
    updates: dict,
    db: AsyncSession
) -> dict:
    """
    Update assessment flow through MFO coordination.
    """
    pass
```

**2.3 Update Assessment Flow Handlers to Use MFO**

Modify: `backend/app/api/v1/endpoints/assessment_flow/flow_management.py`

```python
from .mfo_integration import (
    create_assessment_via_mfo,
    get_assessment_status_via_mfo,
    update_assessment_via_mfo
)

@router.post("/assessment-flow/create")
async def create_assessment_flow(
    request: AssessmentFlowCreateRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """Create assessment flow through MFO."""
    return await create_assessment_via_mfo(
        client_account_id=context.client_account_id,
        engagement_id=context.engagement_id,
        application_ids=request.application_ids,
        db=db
    )
```

**2.4 Implement Two-Table Pattern**

Per ADR-012, ensure assessment flows use:
- **Master Table**: `crewai_flow_state_extensions` (lifecycle: running/paused/completed)
- **Child Table**: `assessment_flows` (operational: phases, UI state)

```python
# Master flow state
master_flow = CrewAIFlowStateExtension(
    flow_id=flow_id,
    flow_type="assessment",
    status="running",
    client_account_id=client_account_id,
    engagement_id=engagement_id
)

# Child assessment flow
child_flow = AssessmentFlow(
    flow_id=flow_id,  # Links to master
    current_phase="architecture_standards",
    phase_status="in_progress",
    selected_application_ids=application_ids
)
```

**Deliverables**:
- [ ] Assessment Flow router enabled in registry
- [ ] MFO integration layer created
- [ ] Two-table pattern implemented
- [ ] All assessment endpoints route through MFO
- [ ] Integration tests passing

**Files to Create**:
- `backend/app/api/v1/endpoints/assessment_flow/mfo_integration.py`

**Files to Modify**:
- `backend/app/api/v1/router_registry.py`
- `backend/app/api/v1/endpoints/assessment_flow/flow_management.py`
- `backend/app/api/v1/endpoints/assessment_flow/sixr_decisions.py`
- `backend/app/api/v1/endpoints/assessment_flow/tech_debt_analysis.py`

---

### Phase 3: Frontend Migration (Week 2-3)

**Objective**: Migrate frontend from 6R Analysis API to Assessment Flow API

#### Tasks

**3.1 Create Assessment Flow API Client**

Create: `src/lib/api/assessmentFlow.ts`

```typescript
/**
 * Assessment Flow API client.
 * Replaces sixrApi with MFO-integrated assessment endpoints.
 */

export interface AssessmentFlowCreateRequest {
  application_ids: string[];  // UUIDs
  parameters?: {
    business_value: number;
    technical_complexity: number;
    migration_urgency: number;
    // ... other parameters
  };
}

export interface AssessmentFlowResponse {
  flow_id: string;
  master_flow_id: string;  // From crewai_flow_state_extensions
  status: 'running' | 'paused' | 'completed';
  current_phase: string;
  applications: Array<{id: string; name: string}>;
  // ... other fields
}

class AssessmentFlowApiClient {
  async createAssessmentFlow(
    request: AssessmentFlowCreateRequest
  ): Promise<string> {
    const response = await apiClient.post<{flow_id: string}>(
      '/assessment-flow/create',
      request
    );
    return response.flow_id;
  }

  async getAssessmentStatus(flowId: string): Promise<AssessmentFlowResponse> {
    return await apiClient.get<AssessmentFlowResponse>(
      `/assessment-flow/${flowId}/status`
    );
  }

  async getSixRDecisions(
    flowId: string,
    appId?: string
  ): Promise<SixRDecisions> {
    const endpoint = appId
      ? `/assessment-flow/${flowId}/sixr-decisions?app_id=${appId}`
      : `/assessment-flow/${flowId}/sixr-decisions`;
    return await apiClient.get<SixRDecisions>(endpoint);
  }

  async acceptRecommendation(
    flowId: string,
    appId: string,
    strategy: string,
    reasoning: string
  ): Promise<void> {
    await apiClient.put(
      `/assessment-flow/${flowId}/sixr-decisions/${appId}`,
      { strategy, reasoning, confidence_level: 1.0 }
    );
  }

  // ... other methods
}

export const assessmentFlowApi = new AssessmentFlowApiClient();
```

**3.2 Migrate Treatment.tsx to Use Assessment Flow**

Modify: `src/pages/assess/Treatment.tsx`

```typescript
// OLD (Remove):
// import { sixrApi } from '@/lib/api/sixr';

// NEW:
import { assessmentFlowApi } from '@/lib/api/assessmentFlow';

// Replace all sixrApi calls with assessmentFlowApi
const handleCreateAnalysis = async () => {
  // OLD:
  // const analysisId = await sixrApi.createAnalysis(...)

  // NEW:
  const flowId = await assessmentFlowApi.createAssessmentFlow({
    application_ids: selectedAppIds,
    parameters: sliderParameters
  });

  // Navigate to assessment flow page
  router.push(`/assessment/${flowId}/sixr-review`);
};
```

**3.3 Update React Hooks**

Modify: `src/hooks/useSixRAnalysis.ts` → `src/hooks/useAssessmentFlow.ts`

```typescript
export function useAssessmentFlow(flowId?: string) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['assessment-flow', flowId],
    queryFn: () => assessmentFlowApi.getAssessmentStatus(flowId!),
    enabled: !!flowId,
    refetchInterval: (data) =>
      data?.status === 'running' ? 5000 : false
  });

  const acceptRecommendation = useMutation({
    mutationFn: (params: {appId: string; strategy: string; reasoning: string}) =>
      assessmentFlowApi.acceptRecommendation(
        flowId!,
        params.appId,
        params.strategy,
        params.reasoning
      ),
    onSuccess: () => {
      queryClient.invalidateQueries(['assessment-flow', flowId]);
    }
  });

  return {
    flow: data,
    isLoading,
    error,
    acceptRecommendation
  };
}
```

**3.4 Update Component Paths**

Rename/migrate:
- `src/components/sixr/*` → `src/components/assessment/recommendations/*`
- `src/types/api/sixr-strategy/*` → `src/types/api/assessment-flow/*`
- `src/utils/assessment/sixrHelpers.ts` → `src/utils/assessment/flowHelpers.ts`

**Deliverables**:
- [ ] Assessment Flow API client created
- [ ] Treatment.tsx migrated to assessment flow
- [ ] All sixrApi references removed from frontend
- [ ] Component paths updated
- [ ] TypeScript types aligned with backend schemas
- [ ] Frontend builds without errors

**Files to Create**:
- `src/lib/api/assessmentFlow.ts`
- `src/hooks/useAssessmentFlow.ts`

**Files to Modify**:
- `src/pages/assess/Treatment.tsx`
- `src/components/assessment/*` (move from sixr/)
- `src/types/api/assessment-flow/*`

**Files to Delete** (in Phase 5):
- `src/lib/api/sixr.ts`
- `src/hooks/useSixRAnalysis.ts`
- `src/components/sixr/*`

---

### Phase 4: Backend Code Removal (Week 3-4)

**Objective**: Remove all 6R Analysis backend code

#### Tasks

**4.1 Remove 6R Analysis Endpoints**

Delete files:
```
backend/app/api/v1/endpoints/sixr_analysis.py
backend/app/api/v1/endpoints/sixr_analysis_modular.py
backend/app/api/v1/endpoints/sixr_analysis_modular/* (entire directory)
backend/app/api/v1/endpoints/sixr_handlers/* (entire directory)
```

**4.2 Remove 6R Analysis Models**

Delete files:
```
backend/app/models/sixr_analysis/* (entire directory)
backend/app/schemas/sixr_analysis.py
```

**4.3 Remove 6R Analysis Services**

Delete files:
```
backend/app/services/sixr_engine_modular.py
backend/app/services/sixr_handlers/* (entire directory)
backend/app/services/tools/sixr_handlers/* (entire directory)
backend/app/services/tools/sixr_tools_modular.py
backend/app/services/tools/sixr_tools/* (entire directory)
```

**4.4 Remove 6R Analysis CrewAI Components**

**IMPORTANT**: Keep the strategy crew but integrate with Assessment Flow!

Move (don't delete):
```
# FROM:
backend/app/services/crewai_flows/crews/sixr_strategy_crew/*

# TO:
backend/app/services/crewai_flows/crews/assessment_strategy_crew/*
```

Update crew to work with Assessment model:
```python
# In assessment_strategy_crew/crew.py
async def analyze_assessment(
    assessment: Assessment,  # Not SixRAnalysis
    db: AsyncSession
) -> AssessmentRecommendation:
    """
    Analyze assessment and provide 6R recommendation.
    Works with Assessment model, not deprecated SixRAnalysis.
    """
    pass
```

**4.5 Remove 6R Analysis Scripts**

Delete files:
```
backend/app/scripts/seed_sixr_analysis_demo.py
backend/app/scripts/seed_sixr_questions.py
```

**4.6 Update Router Registry**

Modify: `backend/app/api/v1/router_registry.py`

```python
# REMOVE:
from app.api.v1.endpoints.sixr_analysis import router as sixr_router

# REMOVE:
api_router.include_router(sixr_router, prefix="/6r")

# Ensure Assessment Flow is registered:
if ASSESSMENT_FLOW_AVAILABLE:
    api_router.include_router(assessment_flow_router, prefix="/assessment-flow")
```

**4.7 Create Database Migration to Drop Tables**

Create: `backend/alembic/versions/111_remove_sixr_analysis_tables.py`

```python
"""
Remove deprecated 6R Analysis tables.

All 6R recommendations now use Assessment Flow with MFO integration.
Tables to drop: sixr_analyses, sixr_iterations, sixr_recommendations,
                sixr_analysis_parameters, sixr_qualifying_questions

Revision ID: 111
Revises: 110
Create Date: 2025-10-28
"""

def upgrade():
    # Export data first (if needed for historical reference)
    op.execute("""
        CREATE TABLE IF NOT EXISTS migration.sixr_analyses_archive AS
        SELECT * FROM migration.sixr_analyses;
    """)

    # Drop tables in correct order (respect foreign keys)
    op.drop_table('sixr_iterations', schema='migration')
    op.drop_table('sixr_recommendations', schema='migration')
    op.drop_table('sixr_analysis_parameters', schema='migration')
    op.drop_table('sixr_qualifying_questions', schema='migration')
    op.drop_table('sixr_analyses', schema='migration')

    logger.info("✅ Dropped deprecated 6R Analysis tables")

def downgrade():
    # No downgrade - this is a one-way migration
    # Historical data preserved in _archive tables
    raise NotImplementedError(
        "Downgrade not supported - use Assessment Flow going forward"
    )
```

**Deliverables**:
- [ ] All 6R Analysis endpoint files deleted
- [ ] All 6R Analysis model files deleted
- [ ] All 6R Analysis service files deleted
- [ ] Strategy crew migrated to Assessment Flow
- [ ] Router registry cleaned up
- [ ] Database migration to drop tables created
- [ ] Backend tests updated/removed
- [ ] No import errors in backend

**Files to Delete**: 72 files total (see audit above)

**Files to Migrate**:
- `backend/app/services/crewai_flows/crews/sixr_strategy_crew/*` → `assessment_strategy_crew/*`

**Files to Create**:
- `backend/alembic/versions/111_remove_sixr_analysis_tables.py`

---

### Phase 5: Frontend Code Removal (Week 4)

**Objective**: Remove all 6R Analysis frontend code

#### Tasks

**5.1 Remove 6R Analysis API Client**

Delete files:
```
src/lib/api/sixr.ts
src/hooks/useSixRAnalysis.ts
```

**5.2 Remove 6R Analysis Components**

Delete directories:
```
src/components/sixr/*
src/components/assessment/sixr-review/*
src/types/api/sixr-strategy/*
```

**5.3 Remove 6R Analysis Pages**

Delete files:
```
src/pages/assessment/[flowId]/sixr-review.tsx (if not migrated)
```

**5.4 Remove 6R Analysis Utilities**

Delete files:
```
src/utils/assessment/sixrHelpers.ts
```

**5.5 Update All Imports**

Search and replace across frontend:
```bash
# Find any remaining references
grep -r "sixrApi\|sixr-review\|SixRAnalysis" src/

# Replace with assessment flow equivalents
# Should return 0 results after cleanup
```

**5.6 Remove Test Files**

Delete:
```
src/__tests__/sixr/*.test.ts
src/__tests__/hooks/useSixRAnalysis.test.ts
```

**Deliverables**:
- [ ] All 6R Analysis frontend files deleted
- [ ] No import errors in frontend
- [ ] All tests passing
- [ ] No console warnings about missing modules

**Files to Delete**: ~15 files/directories

---

### Phase 6: Complete Assessment Flow Features (Week 4-5)

**Objective**: Implement missing features from #611

#### Tasks

**6.1 Implement Accept Recommendation in Assessment Flow**

Create: `backend/app/api/v1/endpoints/assessment_flow/recommendation_acceptance.py`

```python
@router.post("/{flow_id}/sixr-decisions/{app_id}/accept")
async def accept_sixr_recommendation(
    flow_id: str,
    app_id: str,
    request: AcceptRecommendationRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """
    Accept 6R recommendation and update asset.

    This replaces the old POST /6r/{analysis_id}/accept endpoint.
    """
    # Get assessment flow
    assessment_flow = await get_assessment_flow(flow_id, db, context)

    # Get 6R decision
    decision = await repository.get_sixr_decision(flow_id, app_id)

    # Update asset
    asset = await db.get(Asset, UUID(app_id))
    asset.six_r_strategy = request.strategy
    asset.migration_status = "analyzed"
    asset.updated_by = context.user_id

    await db.commit()

    return {
        "success": True,
        "flow_id": flow_id,
        "app_id": app_id,
        "strategy": request.strategy,
        "message": "Recommendation accepted and asset updated"
    }
```

**6.2 Implement Export Functionality**

Create: `backend/app/api/v1/endpoints/assessment_flow/export.py`

```python
@router.post("/{flow_id}/export")
async def export_assessment_results(
    flow_id: str,
    format: Literal["pdf", "excel", "json"],
    db: AsyncSession = Depends(get_db)
):
    """
    Export assessment results (Issue #722).

    Formats:
    - PDF: Executive summary with 6R recommendations
    - Excel: Detailed spreadsheet with all application data
    - JSON: Full assessment data for API integration
    """
    # Implementation
    pass
```

**6.3 Create E2E Tests**

Create: `backend/tests/e2e/test_assessment_flow_complete.py`

```python
async def test_complete_assessment_flow_with_mfo():
    """
    E2E test: Discovery → Assessment → 6R Recommendations → Wave Planning

    Per issue #721.
    """
    # 1. Complete discovery flow
    discovery_flow = await create_discovery_flow(client_account_id, engagement_id)

    # 2. Create assessment flow through MFO
    assessment_flow = await create_assessment_via_mfo(
        application_ids=discovery_flow.discovered_applications
    )

    # 3. Verify two-table pattern
    assert master_flow.status == "running"
    assert child_flow.current_phase == "architecture_standards"

    # 4. Progress through phases
    await progress_assessment_phase(assessment_flow.flow_id, "tech_debt_analysis")
    await progress_assessment_phase(assessment_flow.flow_id, "sixr_decisions")

    # 5. Verify 6R recommendations generated
    decisions = await get_sixr_decisions(assessment_flow.flow_id)
    assert len(decisions) > 0

    # 6. Accept recommendation
    await accept_sixr_recommendation(
        flow_id=assessment_flow.flow_id,
        app_id=decisions[0].app_id,
        strategy=decisions[0].recommended_strategy
    )

    # 7. Verify asset updated
    asset = await db.get(Asset, decisions[0].app_id)
    assert asset.six_r_strategy == decisions[0].recommended_strategy
    assert asset.migration_status == "analyzed"

    # 8. Mark flow complete
    await finalize_assessment_flow(assessment_flow.flow_id)

    # 9. Verify master flow status
    master_flow = await get_master_flow(assessment_flow.flow_id)
    assert master_flow.status == "completed"
```

**Deliverables**:
- [ ] Accept recommendation implemented in Assessment Flow
- [ ] Export functionality (PDF, Excel, JSON)
- [ ] E2E tests passing
- [ ] All #611 features complete

**Files to Create**:
- `backend/app/api/v1/endpoints/assessment_flow/recommendation_acceptance.py`
- `backend/app/api/v1/endpoints/assessment_flow/export.py`
- `backend/tests/e2e/test_assessment_flow_complete.py`

---

### Phase 7: Verification and Documentation (Week 5)

**Objective**: Ensure migration is complete and document new architecture

#### Tasks

**7.1 Code Cleanup Verification**

Run checks:
```bash
# Ensure no 6R Analysis references remain
grep -r "sixr_analyses\|SixRAnalysis\|sixrApi" backend/app/
grep -r "sixrApi\|useSixRAnalysis" src/

# Should return 0 results (or only comments/docs)

# Verify all tests pass
cd backend && python -m pytest tests/ -v
cd .. && npm run test

# Verify no import errors
cd backend && python -c "from app.api.v1.router_registry import api_router"
cd .. && npm run build
```

**7.2 Update Documentation**

Update files:
- `docs/adr/012-flow-status-management-separation.md` - Add Assessment Flow example
- `docs/guidelines/API_REQUEST_PATTERNS.md` - Update with /assessment-flow patterns
- `CLAUDE.md` - Remove 6R Analysis references, add Assessment Flow section
- `README.md` - Update architecture diagram

Create new:
- `docs/architecture/ASSESSMENT_FLOW_MFO_INTEGRATION.md` - Full integration guide
- `docs/api/ASSESSMENT_FLOW_ENDPOINTS.md` - API reference

**7.3 Update Issue #611**

Close sub-issues:
- #185 - Assess Flow complete - Treatments visible ✅
- #719 - Treatment Recommendations Display Polish ✅
- #720 - Treatment Approval Workflow ✅
- #721 - E2E Testing for Assessment → Treatment Flow ✅
- #722 - Treatment Export Functionality ✅

**Deliverables**:
- [ ] No 6R Analysis code references remain
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Issue #611 closed

---

## File Inventory

### Files to DELETE (Backend - 72 files)

**Endpoints**:
- `backend/app/api/v1/endpoints/sixr_analysis.py`
- `backend/app/api/v1/endpoints/sixr_analysis_modular.py`
- `backend/app/api/v1/endpoints/sixr_analysis_modular/*` (18 files)
- `backend/app/api/v1/endpoints/sixr_handlers/*` (5 files)

**Models**:
- `backend/app/models/sixr_analysis/*` (5 files)
- `backend/app/schemas/sixr_analysis.py`

**Services**:
- `backend/app/services/sixr_engine_modular.py`
- `backend/app/services/sixr_handlers/*` (3 files)
- `backend/app/services/tools/sixr_handlers/*` (5 files)
- `backend/app/services/tools/sixr_tools_modular.py`
- `backend/app/services/tools/sixr_tools/*` (10 files)

**CrewAI Tools** (to migrate, not delete):
- `backend/app/services/crewai_flows/tools/sixr_tools/*` (8 files)

**Scripts**:
- `backend/app/scripts/seed_sixr_analysis_demo.py`
- `backend/app/scripts/seed_sixr_questions.py`

### Files to DELETE (Frontend - 15 items)

**API Clients**:
- `src/lib/api/sixr.ts`
- `src/hooks/useSixRAnalysis.ts`

**Components**:
- `src/components/sixr/*` (entire directory)
- `src/components/assessment/sixr-review/*` (entire directory)

**Types**:
- `src/types/api/sixr-strategy/*` (entire directory)

**Utilities**:
- `src/utils/assessment/sixrHelpers.ts`

**Pages**:
- `src/pages/assessment/[flowId]/sixr-review.tsx` (verify not needed)

### Files to CREATE

**Backend**:
- `backend/app/api/v1/endpoints/assessment_flow/mfo_integration.py`
- `backend/app/api/v1/endpoints/assessment_flow/recommendation_acceptance.py`
- `backend/app/api/v1/endpoints/assessment_flow/export.py`
- `backend/alembic/versions/111_remove_sixr_analysis_tables.py`
- `backend/tests/e2e/test_assessment_flow_complete.py`

**Frontend**:
- `src/lib/api/assessmentFlow.ts`
- `src/hooks/useAssessmentFlow.ts`

**Documentation**:
- `docs/architecture/ASSESSMENT_FLOW_MFO_INTEGRATION.md`
- `docs/api/ASSESSMENT_FLOW_ENDPOINTS.md`
- `docs/planning/SIXR_ANALYSIS_CURRENT_STATE.md`

### Files to MODIFY

**Backend**:
- `backend/app/api/v1/router_registry.py` (enable assessment_flow_router)
- `backend/app/api/v1/endpoints/assessment_flow/flow_management.py`
- `backend/app/api/v1/endpoints/assessment_flow/sixr_decisions.py`
- `backend/app/api/v1/endpoints/assessment_flow/tech_debt_analysis.py`
- `backend/app/api/v1/endpoints/assessment_flow/finalization.py`

**Frontend**:
- `src/pages/assess/Treatment.tsx`
- `src/components/assessment/*` (various components)

**Documentation**:
- `CLAUDE.md`
- `docs/adr/012-flow-status-management-separation.md`
- `docs/guidelines/API_REQUEST_PATTERNS.md`

---

## Risk Mitigation

### Risk 1: Data Loss
**Mitigation**: Create archive tables before dropping sixr_analyses

```sql
CREATE TABLE migration.sixr_analyses_archive AS
SELECT * FROM migration.sixr_analyses;
```

### Risk 2: Frontend Breakage During Migration
**Mitigation**:
- Use feature flags to toggle between old/new implementation
- Deploy backend first with both endpoints active
- Migrate frontend incrementally
- Remove old code only after verification

### Risk 3: MFO Integration Complexity
**Mitigation**:
- Study existing Discovery Flow MFO integration (reference implementation)
- Use two-table pattern consistently (master + child)
- Add comprehensive logging
- Create detailed integration tests

### Risk 4: Missing Features in Assessment Flow
**Mitigation**:
- Audit 6R Analysis features before removal
- Port any missing functionality to Assessment Flow
- Get product team sign-off before deletion

---

## Success Criteria

### Functional
- [ ] Assessment Flow fully operational with MFO integration
- [ ] All #611 features complete (treatments visible, export, acceptance)
- [ ] Discovery → Assessment → 6R → Wave Planning flow working
- [ ] Zero 6R Analysis code references in codebase

### Technical
- [ ] Two-table pattern (master + child) implemented
- [ ] All endpoints route through MFO
- [ ] Multi-tenant scoping enforced
- [ ] All tests passing (backend + frontend)
- [ ] No deprecation warnings

### Documentation
- [ ] Architecture docs updated
- [ ] API reference complete
- [ ] Migration guide published
- [ ] Issue #611 closed

---

## Timeline

| Week | Phase | Deliverable |
|------|-------|-------------|
| Week 1, Days 1-2 | Phase 1 | Code audit complete, deprecation warnings added |
| Week 1, Days 3-5 | Phase 2 | Assessment Flow enabled with MFO integration |
| Week 2 | Phase 3 | Frontend migrated to Assessment Flow |
| Week 3 | Phase 4 | Backend 6R Analysis code removed |
| Week 4, Days 1-3 | Phase 5 | Frontend 6R Analysis code removed |
| Week 4, Days 4-5 | Phase 6 | Accept recommendation + export implemented |
| Week 5, Days 1-3 | Phase 6 | E2E tests complete |
| Week 5, Days 4-5 | Phase 7 | Verification and documentation |

**Total Effort**: 4-5 weeks (5 weeks recommended for thorough testing)

---

## Team Requirements

- **Backend Engineers**: 1-2 full-time
- **Frontend Engineer**: 1 full-time
- **QA Engineer**: 0.5 full-time (E2E testing)
- **DevOps**: 0.25 full-time (deployment coordination)

---

## Approval Checklist

Before starting migration:
- [ ] Product team approves Assessment Flow as single source of truth
- [ ] Architecture team approves MFO integration approach
- [ ] Engineering team commits resources (1-2 backend, 1 frontend)
- [ ] Timeline approved (4-5 weeks)
- [ ] Risk mitigation plan reviewed
- [ ] Data export/archive strategy confirmed

---

**Document Owner**: Architecture Team
**Last Updated**: 2025-10-28
**Status**: Awaiting Approval
