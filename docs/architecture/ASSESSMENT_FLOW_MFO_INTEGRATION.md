# Assessment Flow MFO Integration

**Status**: Production
**Last Updated**: October 28, 2025
**Related ADRs**: ADR-006 (Master Flow Orchestrator), ADR-012 (Flow Status Management Separation)

---

## Overview

This document describes how Assessment Flow integrates with the Master Flow Orchestrator (MFO) per ADR-006. Assessment Flow provides cloud readiness assessment and 6R migration recommendations as part of the enterprise migration workflow.

## Architecture

### Two-Table Pattern (ADR-012)

Assessment Flow implements the standard MFO two-table pattern:

#### Master Table: `crewai_flow_state_extensions`

Stores high-level lifecycle state:
- `flow_type`: "assessment"
- `status`: "running" | "paused" | "completed" | "failed"
- `client_account_id`: Multi-tenant isolation
- `engagement_id`: Project-level scoping
- Used for: Cross-flow coordination, lifecycle management

#### Child Table: `assessment_flows`

Stores operational state:
- `flow_id`: Links to master flow (UUID, foreign key)
- `current_phase`: "architecture_standards" | "tech_debt_analysis" | "sixr_decisions"
- `phase_status`: "pending" | "in_progress" | "completed"
- `selected_application_ids`: List of applications being assessed (JSONB array)
- `phase_data`: Phase-specific data (JSONB)
- Used for: Operational decisions, UI state, phase progression

### State Management

**Query Pattern**:
- Frontend: Always query child flow (`assessment_flows`) for UI display
- Agents: Use child flow status for operational decisions
- MFO: Updates both master and child flows atomically

**Status Synchronization**:
```python
async def update_assessment_status(
    flow_id: UUID,
    child_status: str,
    master_status: str,
    db: AsyncSession
):
    """Atomic update of both master and child flow status."""
    async with db.begin():
        # Update child flow first (detailed state)
        await update_child_flow(flow_id, child_status)

        # Update master flow (lifecycle state)
        await update_master_flow(flow_id, master_status)
```

## MFO Integration Layer

### File: `backend/app/api/v1/endpoints/assessment_flow/mfo_integration.py`

The MFO integration layer provides unified access to assessment flows through the Master Flow Orchestrator.

#### Key Functions

**1. Create Assessment Flow**
```python
async def create_assessment_via_mfo(
    client_account_id: UUID,
    engagement_id: UUID,
    application_ids: List[UUID],
    parameters: Optional[Dict[str, Any]],
    db: AsyncSession
) -> dict:
    """
    Create assessment flow through MFO.

    Flow:
    1. Register master flow in crewai_flow_state_extensions
    2. Create child assessment flow in assessment_flows table
    3. Link via flow_id
    4. Return unified state

    Returns:
        {
            "flow_id": "uuid",
            "master_flow_id": "uuid",
            "status": "running",
            "current_phase": "architecture_standards",
            "selected_applications": [...]
        }
    """
    async with db.begin():
        # Create master flow
        master_flow = CrewAIFlowStateExtension(
            flow_id=uuid4(),
            flow_type="assessment",
            status="running",
            client_account_id=client_account_id,
            engagement_id=engagement_id
        )
        db.add(master_flow)
        await db.flush()

        # Create child flow linked to master
        child_flow = AssessmentFlow(
            flow_id=master_flow.flow_id,
            current_phase="architecture_standards",
            phase_status="in_progress",
            selected_application_ids=application_ids,
            client_account_id=client_account_id,
            engagement_id=engagement_id
        )
        db.add(child_flow)
        await db.commit()

    return serialize_assessment_flow(master_flow, child_flow)
```

**2. Get Assessment Status**
```python
async def get_assessment_status_via_mfo(
    flow_id: UUID,
    client_account_id: UUID,
    engagement_id: UUID,
    db: AsyncSession
) -> dict:
    """
    Get assessment status from both master and child tables.

    Returns unified view:
    - Master flow: running/paused/completed (lifecycle)
    - Child flow: current_phase, operational state (details)
    """
    # Query both tables with tenant scoping
    master_flow = await get_master_flow(flow_id, client_account_id, engagement_id, db)
    child_flow = await get_child_flow(flow_id, client_account_id, engagement_id, db)

    return {
        "flow_id": str(flow_id),
        "master_status": master_flow.status,
        "current_phase": child_flow.current_phase,
        "phase_status": child_flow.phase_status,
        "selected_applications": child_flow.selected_application_ids,
        "phase_data": child_flow.phase_data
    }
```

**3. Update Assessment Flow**
```python
async def update_assessment_via_mfo(
    flow_id: UUID,
    updates: dict,
    client_account_id: UUID,
    engagement_id: UUID,
    db: AsyncSession
) -> dict:
    """
    Update assessment flow through MFO coordination.

    Atomic update of both master and child tables.
    """
    async with db.begin():
        # Update child flow operational state
        if "current_phase" in updates:
            await update_child_phase(flow_id, updates["current_phase"], db)

        # Update master flow lifecycle if needed
        if "status" in updates:
            await update_master_status(flow_id, updates["status"], db)

        await db.commit()

    return await get_assessment_status_via_mfo(
        flow_id, client_account_id, engagement_id, db
    )
```

**4. Pause/Resume Assessment Flow**
```python
async def pause_assessment_flow(
    flow_id: UUID,
    client_account_id: UUID,
    engagement_id: UUID,
    db: AsyncSession
) -> dict:
    """Pause assessment flow (lifecycle operation)."""
    return await update_assessment_via_mfo(
        flow_id,
        {"status": "paused"},
        client_account_id,
        engagement_id,
        db
    )

async def resume_assessment_flow(
    flow_id: UUID,
    client_account_id: UUID,
    engagement_id: UUID,
    db: AsyncSession
) -> dict:
    """Resume assessment flow (lifecycle operation)."""
    return await update_assessment_via_mfo(
        flow_id,
        {"status": "running"},
        client_account_id,
        engagement_id,
        db
    )
```

**5. Complete Assessment Flow**
```python
async def complete_assessment_flow(
    flow_id: UUID,
    client_account_id: UUID,
    engagement_id: UUID,
    db: AsyncSession
) -> dict:
    """
    Mark assessment flow as completed (terminal state).

    Updates both master and child flows atomically.
    """
    async with db.begin():
        # Verify all phases complete
        child_flow = await get_child_flow(flow_id, client_account_id, engagement_id, db)

        if child_flow.current_phase != "sixr_decisions":
            raise ValueError("Cannot complete: Assessment not in final phase")

        # Update both flows to completed
        await update_child_flow_status(flow_id, "completed", db)
        await update_master_flow_status(flow_id, "completed", db)

        await db.commit()

    return await get_assessment_status_via_mfo(
        flow_id, client_account_id, engagement_id, db
    )
```

## API Endpoints

All Assessment Flow endpoints route through `/api/v1/assessment-flow/*`:

### Create Assessment Flow
```http
POST /api/v1/assessment-flow/initialize
Content-Type: application/json

{
  "application_ids": ["uuid1", "uuid2"],
  "parameters": {
    "business_value": 8,
    "technical_complexity": 6,
    "migration_urgency": 7
  }
}

Response:
{
  "flow_id": "uuid",
  "master_flow_id": "uuid",
  "status": "running",
  "current_phase": "architecture_standards",
  "selected_applications": [...]
}
```

### Get Assessment Status
```http
GET /api/v1/assessment-flow/{flow_id}/status

Response:
{
  "flow_id": "uuid",
  "master_status": "running",
  "current_phase": "sixr_decisions",
  "phase_status": "in_progress",
  "selected_applications": [...]
}
```

### Get 6R Recommendations
```http
GET /api/v1/assessment-flow/{flow_id}/sixr-decisions
GET /api/v1/assessment-flow/{flow_id}/sixr-decisions?app_id={uuid}

Response:
{
  "flow_id": "uuid",
  "recommendations": [
    {
      "app_id": "uuid",
      "recommended_strategy": "rehost",
      "reasoning": "Low complexity application...",
      "confidence_level": 0.85,
      "alternatives": [...]
    }
  ]
}
```

### Accept Recommendation
```http
POST /api/v1/assessment-flow/{flow_id}/sixr-decisions/{app_id}/accept
Content-Type: application/json

{
  "strategy": "rehost",
  "reasoning": "Accepted agent recommendation",
  "confidence_level": 0.85
}

Response:
{
  "success": true,
  "flow_id": "uuid",
  "app_id": "uuid",
  "strategy": "rehost",
  "message": "Recommendation accepted and asset updated"
}
```

### Export Assessment Results
```http
POST /api/v1/assessment-flow/{flow_id}/export?format={json|pdf|excel}

Response:
{
  "export_id": "uuid",
  "format": "pdf",
  "download_url": "/api/v1/exports/{export_id}/download",
  "expires_at": "2025-10-29T00:00:00Z"
}
```

### Pause/Resume Flow
```http
POST /api/v1/assessment-flow/{flow_id}/pause
POST /api/v1/assessment-flow/{flow_id}/resume

Response:
{
  "flow_id": "uuid",
  "master_status": "paused" | "running",
  "message": "Flow paused/resumed successfully"
}
```

## Frontend Integration

### API Client: `src/lib/api/assessmentFlow.ts`

```typescript
interface AssessmentFlowCreateRequest {
  application_ids: string[];  // UUIDs
  parameters?: {
    business_value: number;
    technical_complexity: number;
    migration_urgency: number;
  };
}

interface AssessmentFlowResponse {
  flow_id: string;
  master_flow_id: string;
  status: 'running' | 'paused' | 'completed';
  current_phase: string;
  phase_status: string;
  selected_applications: Array<{id: string; name: string}>;
}

class AssessmentFlowApiClient {
  async createAssessmentFlow(
    request: AssessmentFlowCreateRequest
  ): Promise<string> {
    const response = await apiClient.post<{flow_id: string}>(
      '/assessment-flow/initialize',
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
    reasoning: string,
    confidence_level: number
  ): Promise<void> {
    await apiClient.post(
      `/assessment-flow/${flowId}/sixr-decisions/${appId}/accept`,
      {
        strategy,
        reasoning,
        confidence_level
      }
    );
  }

  async exportResults(
    flowId: string,
    format: 'json' | 'pdf' | 'excel'
  ): Promise<ExportResponse> {
    return await apiClient.post(
      `/assessment-flow/${flowId}/export?format=${format}`
    );
  }
}

export const assessmentFlowApi = new AssessmentFlowApiClient();
```

### React Hook: `src/hooks/useAssessmentFlow.ts`

```typescript
export function useAssessmentFlow(flowId?: string) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['assessment-flow', flowId],
    queryFn: () => assessmentFlowApi.getAssessmentStatus(flowId!),
    enabled: !!flowId,
    refetchInterval: (data) =>
      data?.status === 'running' ? 5000 : false,
    staleTime: 0  // Always fresh for status
  });

  const acceptRecommendation = useMutation({
    mutationFn: (params: {
      appId: string;
      strategy: string;
      reasoning: string;
      confidence_level: number;
    }) =>
      assessmentFlowApi.acceptRecommendation(
        flowId!,
        params.appId,
        params.strategy,
        params.reasoning,
        params.confidence_level
      ),
    onSuccess: () => {
      queryClient.invalidateQueries(['assessment-flow', flowId]);
    }
  });

  const exportResults = useMutation({
    mutationFn: (format: 'json' | 'pdf' | 'excel') =>
      assessmentFlowApi.exportResults(flowId!, format)
  });

  return {
    flow: data,
    isLoading,
    error,
    acceptRecommendation,
    exportResults
  };
}
```

## Multi-Tenant Scoping

All Assessment Flow operations enforce multi-tenant isolation:

```python
# Every query includes tenant scoping
query = select(AssessmentFlow).where(
    AssessmentFlow.flow_id == flow_id,
    AssessmentFlow.client_account_id == context.client_account_id,
    AssessmentFlow.engagement_id == context.engagement_id
)
```

Frontend includes tenant headers on all requests:
```typescript
const headers = {
  'X-Client-Account-ID': clientAccountId,
  'X-Engagement-ID': engagementId
};
```

## Phase Progression

Assessment Flow progresses through three phases:

1. **Architecture Standards** (Initial Phase)
   - Analyzes application architecture
   - Identifies patterns and anti-patterns
   - Generates architecture assessment report

2. **Tech Debt Analysis** (Middle Phase)
   - Evaluates technical debt
   - Risk assessment
   - Modernization opportunities

3. **6R Decisions** (Final Phase)
   - 6R strategy recommendations (Rehost, Replatform, Refactor, etc.)
   - Confidence scoring
   - Alternative strategies
   - Accept recommendation → Updates `Asset.six_r_strategy`

## Migration from 6R Analysis

**Deprecated**: `/api/v1/6r/*` endpoints (September 9, 2025)
**Replacement**: `/api/v1/assessment-flow/*` endpoints
**Migration Completed**: October 28, 2025 (Phases 1-6)

### What Changed
- Removed duplicate 6R Analysis implementation (87 files deleted)
- Enabled Assessment Flow as single source of truth
- Integrated strategy crew with Assessment Flow via MFO
- All 6R recommendations now through Assessment Flow

### Why
- Eliminated redundant code paths
- Proper MFO architecture compliance (ADR-006)
- Single source of truth for 6R recommendations
- Better multi-tenant isolation and state management

## Error Handling

Assessment Flow uses structured error responses:

```json
{
  "status": "error",
  "error_code": "ASSESSMENT_FLOW_NOT_FOUND",
  "message": "Assessment flow not found",
  "details": {
    "flow_id": "uuid",
    "client_account_id": 1,
    "engagement_id": 1
  }
}
```

Common error codes:
- `ASSESSMENT_FLOW_NOT_FOUND`: Flow does not exist or access denied
- `ASSESSMENT_FLOW_NOT_IN_PHASE`: Operation not valid for current phase
- `ASSESSMENT_FLOW_ALREADY_COMPLETED`: Cannot modify completed flow
- `INVALID_APPLICATION_ID`: Application not found or not accessible

## Testing

### E2E Test Flow
```python
async def test_complete_assessment_flow_with_mfo():
    """E2E test: Discovery → Assessment → 6R Recommendations → Wave Planning"""

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

## References

- **ADR-006**: Master Flow Orchestrator
- **ADR-012**: Flow Status Management Separation
- **Migration Plan**: `/docs/planning/ASSESSMENT_FLOW_MFO_MIGRATION_PLAN.md`
- **Migration Summary**: `/docs/planning/ASSESSMENT_FLOW_MFO_MIGRATION_SUMMARY.md`
- **API Patterns**: `/docs/guidelines/API_REQUEST_PATTERNS.md`
- **CLAUDE.md**: Assessment Flow Architecture section

## Key Takeaways

1. **MFO Integration**: All assessment operations route through Master Flow Orchestrator
2. **Two-Table Pattern**: Master for lifecycle, child for operational state
3. **Multi-Tenant**: All operations enforce client_account_id + engagement_id scoping
4. **Atomic Updates**: Master and child flows updated in single transaction
5. **Single Source of Truth**: Assessment Flow is the only way to get 6R recommendations
6. **Deprecated**: `/api/v1/6r/*` endpoints return HTTP 410 Gone
