# Collection Flow Diagnostic Fixes - September 2025

## Critical Architecture Violations Fixed

### 1. Persistent Agent Architecture (ADR-015)
**Problem**: Agents created per-execution instead of persistent multi-tenant pattern
**Solution**: Use TenantScopedAgentPool for singleton agents per (client_id, engagement_id)
```python
# WRONG - Per-execution pattern
class GapAnalysisAgent(BaseDiscoveryCrew):
    pass

# CORRECT - Persistent agent
agent = await TenantScopedAgentPool.get_collection_gap_agent(
    context.client_account_id,
    context.engagement_id
)
```
**Files**: `backend/app/services/persistent_agents/tenant_scoped_agent_pool.py`

### 2. WebSocket Removal for Vercel/Railway
**Problem**: WebSocket code incompatible with deployment platform
**Solution**: Complete removal, use HTTP/2 polling with Redis
```typescript
// Remove ALL WebSocket references
// Replace with HTTP polling
const useCollectionStatePolling = (flowId: string) => {
    useEffect(() => {
        const pollInterval = setInterval(async () => {
            const state = await fetch(`/api/v1/collection/flows/${flowId}/state`);
        }, 2000);
    }, [flowId]);
};
```

### 3. Application Selection Storage Fix
**Problem**: Only updates JSON, not normalized tables
**Location**: `backend/app/api/v1/endpoints/collection_applications.py`
**Solution**: Use deduplication service with Asset names
```python
# Load Asset objects to get names
assets = await db.execute(
    select(Application)
    .where(Application.application_id.in_(application_ids))
)
for asset in assets.scalars():
    await dedup_service.deduplicate_application(
        application_name=asset.name,  # Use name, not ID
        collection_flow_id=collection_flow.id
    )
```

### 4. Transaction Boundary Fix
**Problem**: Orphaned flows on MFO failure
**Location**: `backend/app/api/v1/endpoints/collection_crud_create_commands.py`
**Solution**: Single transaction with context manager
```python
async with db.begin():  # Let context manager handle commit/rollback
    collection_flow = CollectionFlow(...)
    db.add(collection_flow)
    await db.flush()  # Get ID without commit

    master_flow_id = await orchestrator.create_flow(...)
    if not master_flow_id:
        raise ValueError("MFO creation failed")  # Auto-rollback

    collection_flow.master_flow_id = master_flow_id
    # Context manager commits on success
```

### 5. Gap Analysis Summary Model
**Problem**: Serializer mismatch with actual model structure
**Model**: `CollectionGapAnalysis` has summary fields, not per-gap
**Solution**: New serializer matching actual structure
```python
class CollectionGapAnalysisSummaryResponse(BaseModel):
    completeness_percentage: float
    critical_gaps: List[Dict[str, Any]]  # JSONB list
    recommended_actions: Dict[str, Any]
    attributes_analyzed: int
    collection_difficulty_score: float
```

## Key Diagnostic Findings

### Empty Database Tables Root Cause
1. `collection_flow_applications`: Selection only updates JSON config
2. `collection_gap_analysis`: Gap results stored in wrong location (JSON field)
3. Fix: Dual storage pattern during transition (JSON + normalized tables)

### Blank Forms Loading Issue
1. Gap analysis agent not executing (non-persistent pattern)
2. No automatic phase transitions after selection
3. Frontend fallback exists but not receiving gap data

### Flow State Mismatch
- 2 flows in `crewai_flow_state_extensions`
- 1 flow in collection overview
- Cause: Orphaned flows from failed MFO integration

## Implementation Priority
**P0 (48 hours)**: Application storage, MFO transactions, Remove mock fallbacks
**P1 (3-5 days)**: Persistent agents, HTTP polling, Gap summary service
**P2 (1 week)**: Redis monitoring, Error recovery

## Validation Queries
```sql
-- Verify application selection persisted
SELECT COUNT(*) FROM migration.collection_flow_applications
WHERE collection_flow_id = ?;  -- Should be > 0

-- Verify gap analysis populated
SELECT COUNT(*) FROM migration.collection_gap_analysis
WHERE collection_flow_id = ?;  -- Should be > 0

-- No orphaned flows
SELECT COUNT(*) FROM migration.collection_flows
WHERE master_flow_id IS NULL AND status != 'failed';  -- Should be 0
```

## Files Requiring Updates
- `backend/app/api/v1/endpoints/collection_applications.py`
- `backend/app/api/v1/endpoints/collection_crud_create_commands.py`
- `backend/app/services/ai_analysis/gap_analysis_agent.py`
- `backend/app/services/persistent_agents/tenant_scoped_agent_pool.py`
- `src/hooks/collection/useAdaptiveFormFlow.ts`
- Remove ALL WebSocket references in collection components

## Success Metrics
- 100% → <5% failure rate after all fixes
- All collection flows have master_flow_id
- Gap analysis executes with persistent agents
- Forms display questionnaires from gap data
