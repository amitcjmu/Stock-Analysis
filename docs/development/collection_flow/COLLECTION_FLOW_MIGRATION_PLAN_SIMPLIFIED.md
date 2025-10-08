# Collection Flow Migration Plan (Simplified)
## crew_class → child_flow_service - No Shims, No Over-Engineering

**Status**: Ready for Implementation (GPT5 Simplified)
**Updated**: 2025-10-07 (Complexity Removed)
**Priority**: High

---

## Core Principle: Simplicity

**Delete legacy immediately. Single execution path. Minimal patterns.**

---

## Critical ID Correction

**WRONG (Previous Plan)**:
- `collection_flows.id` = Integer PK ❌

**CORRECT (Actual Schema)**:
- `collection_flows.id` = **UUID PK** ✅
- `collection_flows.flow_id` = UUID (business ID for MFO) ✅

### ID Usage Rules

| Field | Type | When to Use |
|-------|------|-------------|
| `collection_flows.id` | UUID (PK) | **ALL FKs, DB persistence, background jobs** |
| `collection_flows.flow_id` | UUID | **Master orchestrator calls ONLY** |

**Examples**:
```python
# ✅ Correct - Use child PK (UUID)
await gap_service.execute_gap_analysis(
    collection_flow_id=child_flow.id  # UUID PK
)

# ✅ Correct - Use business UUID for MFO
await orchestrator.execute_phase(
    flow_id=str(child_flow.flow_id)  # Business UUID
)
```

---

## Migration Steps (3 Phases, ~1 hour)

### Phase 1: Create CollectionChildFlowService (20 min)

**File**: `backend/app/services/child_flow_services/collection.py`

```python
"""Collection Child Flow Service - Single execution path"""

import logging
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.repositories.collection_flow_repository import CollectionFlowRepository
from app.services.child_flow_services.base import BaseChildFlowService
from app.services.collection_flow.state_management import CollectionFlowStateService

logger = logging.getLogger(__name__)


class CollectionChildFlowService(BaseChildFlowService):
    """Service for collection flow child operations"""

    def __init__(self, db: AsyncSession, context: RequestContext):
        super().__init__(db, context)
        self.repository = CollectionFlowRepository(
            db=self.db,
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id,
        )
        self.state_service = CollectionFlowStateService(db, context)

    async def get_child_status(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """Get collection flow child status"""
        child_flow = await self.repository.get_by_master_flow_id(UUID(flow_id))
        if not child_flow:
            return None

        return {
            "status": child_flow.status,
            "current_phase": child_flow.current_phase,
            "progress_percentage": child_flow.progress_percentage,
            "automation_tier": child_flow.automation_tier,
            "collection_config": child_flow.collection_config,
            "phase_state": child_flow.phase_state,
        }

    async def get_by_master_flow_id(self, flow_id: str):
        """Get collection flow by master flow ID"""
        return await self.repository.get_by_master_flow_id(UUID(flow_id))

    async def execute_phase(
        self,
        flow_id: str,
        phase_name: str,
        phase_input: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute phase using persistent agents"""

        child_flow = await self.get_by_master_flow_id(flow_id)
        if not child_flow:
            raise ValueError(f"Collection flow not found for master flow {flow_id}")

        # Route to phase handler
        if phase_name == "asset_selection":
            return {"status": "awaiting_user_input", "phase": phase_name}

        elif phase_name == "gap_analysis":
            from app.services.collection.gap_analysis import GapAnalysisService

            gap_service = GapAnalysisService(self.db, self.context)
            result = await gap_service.execute_gap_analysis(
                collection_flow_id=child_flow.id,  # ✅ UUID PK
                phase_input=phase_input or {}
            )

            # Auto-progression (per GPT5: keep in service, not UI)
            from app.services.collection_flow.state_management import CollectionPhase

            gaps_persisted = result.get("gaps_persisted", 0)
            has_pending_gaps = result.get("has_pending_gaps", False)

            if gaps_persisted > 0:
                # Gaps persisted → generate questionnaires
                await self.state_service.transition_phase(
                    flow_id=child_flow.id,
                    new_phase=CollectionPhase.QUESTIONNAIRE_GENERATION
                )
            elif not has_pending_gaps:
                # No pending gaps → skip to assessment
                await self.state_service.transition_phase(
                    flow_id=child_flow.id,
                    new_phase=CollectionPhase.ASSESSMENT
                )
            else:
                # Job persisted zero but gaps still exist → remain in manual_collection
                await self.state_service.transition_phase(
                    flow_id=child_flow.id,
                    new_phase=CollectionPhase.MANUAL_COLLECTION
                )

            return result

        elif phase_name == "questionnaire_generation":
            from app.services.collection.questionnaire_generation import QuestionnaireGenerationService

            qg_service = QuestionnaireGenerationService(self.db, self.context)
            return await qg_service.generate_questionnaires(
                collection_flow_id=child_flow.id,  # ✅ UUID PK
                phase_input=phase_input or {}
            )

        elif phase_name == "manual_collection":
            return {"status": "awaiting_user_responses", "phase": phase_name}

        elif phase_name == "data_validation":
            from app.services.collection.validation import ValidationService

            validation_service = ValidationService(self.db, self.context)
            return await validation_service.validate_collected_data(
                collection_flow_id=child_flow.id,  # ✅ UUID PK
                phase_input=phase_input or {}
            )

        else:
            logger.info(f"Unknown phase '{phase_name}' - noop")
            return {"status": "success", "phase": phase_name, "execution_type": "noop"}
```

**Update**: `backend/app/services/child_flow_services/__init__.py`
```python
from .collection import CollectionChildFlowService  # ADD

__all__ = [
    "BaseChildFlowService",
    "CollectionChildFlowService",  # ADD
    "DiscoveryChildFlowService",
]
```

---

### Phase 2: Update Config & Delete Legacy (20 min)

#### 2.1 Update Flow Config

**File**: `backend/app/services/flow_configs/collection_flow_config.py`

**DELETE** (Lines 23-34):
```python
# DELETE THIS ENTIRE BLOCK
COLLECTION_FLOW_AVAILABLE = False
UnifiedCollectionFlow = None
try:
    from app.services.crewai_flows.unified_collection_flow import UnifiedCollectionFlow
    COLLECTION_FLOW_AVAILABLE = True
except ImportError:
    COLLECTION_FLOW_AVAILABLE = False
    UnifiedCollectionFlow = None
```

**ADD** (Top of file):
```python
from app.services.child_flow_services import CollectionChildFlowService
```

**REPLACE** (Line ~90):
```python
# OLD
crew_class=(UnifiedCollectionFlow if COLLECTION_FLOW_AVAILABLE else None),

# NEW
child_flow_service=CollectionChildFlowService,
```

#### 2.2 Delete UnifiedCollectionFlow (No Deprecation Window)

```bash
# Delete file immediately
rm backend/app/services/crewai_flows/unified_collection_flow.py

# Verify no imports remain
grep -r "UnifiedCollectionFlow" backend/ --exclude-dir=__pycache__
# Expected: No results
```

#### 2.3 Revert GapAnalysisAgent Placeholder

```bash
git revert 9516b6ed3 --no-commit
git commit -m "revert: Remove GapAnalysisAgent placeholder"
```

---

### Phase 3: Update MFO Resume Logic (20 min)

**File**: `backend/app/services/master_flow_orchestrator/operations/lifecycle_commands.py`

**Location**: Lines 309-379 in `_restore_and_resume_flow_from_state`

**REPLACE entire if/else block**:
```python
# Single path - check child_flow_service ONLY
if flow_config.child_flow_service:
    logger.info(f"Executing {master_flow.flow_type} via child_flow_service")

    child_service = flow_config.child_flow_service(self.db, self.context)
    current_phase = master_flow.get_current_phase() or "initialization"

    result = await child_service.execute_phase(
        flow_id=str(master_flow.flow_id),
        phase_name=current_phase,
        phase_input=resume_context or {}
    )

    return {
        "status": "resumed",
        "message": f"Flow resumed via child_flow_service",
        "current_phase": current_phase,
        "execution_result": result
    }
else:
    logger.error(f"No child_flow_service for flow type '{master_flow.flow_type}'")
    raise ValueError(f"Flow type '{master_flow.flow_type}' has no execution handler")
```

**Remove crew_class fallback entirely** - no legacy path.

---

## Tenant Scoping (Explicit Pattern)

**All repository lookups MUST filter by tenant context:**

```python
# ✅ Correct - explicit tenant scoping
repository = CollectionFlowRepository(
    db=db,
    client_account_id=context.client_account_id,
    engagement_id=context.engagement_id
)

# Repository internally filters all queries:
# .where(CollectionFlow.client_account_id == self.client_account_id)
# .where(CollectionFlow.engagement_id == self.engagement_id)
```

**No cross-tenant data leakage possible.**

---

## Background Job Simplification

### Minimal Pattern (Per GPT5)

**Endpoint**: `/api/v1/collection/flows/{flow_id}/analyze-gaps`

```python
@router.post("/{flow_id}/analyze-gaps", status_code=202)
async def analyze_gaps(
    flow_id: str,
    selected_gaps: List[Dict[str, Any]],
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_context)
):
    """Submit gaps for analysis - returns 202, enqueues worker"""

    # Validate count
    if len(selected_gaps) > 200:
        raise HTTPException(400, "Max 200 gaps per submission")

    # Explicit repository with tenant scoping (per GPT5)
    repository = CollectionFlowRepository(
        db=db,
        client_account_id=context.client_account_id,
        engagement_id=context.engagement_id
    )

    # Get child flow (tenant-scoped)
    child_flow = await repository.get_by_master_flow_id(UUID(flow_id))
    if not child_flow:
        raise HTTPException(404, "Flow not found")

    # Explicit Redis manager (per GPT5)
    redis = get_redis_manager().client

    # Rate limit: single Redis key with 10s TTL
    rate_limit_key = f"gap_analysis_rate_limit:{child_flow.id}"
    if await redis.exists(rate_limit_key):
        raise HTTPException(429, "Rate limited - wait 10s between submissions")
    await redis.setex(rate_limit_key, 10, "1")

    # Idempotency: reject if job already running
    job_key = f"gap_enhancement_job:{child_flow.id}"
    if await redis.exists(job_key):
        raise HTTPException(409, "Job already running for this flow")

    # Enqueue worker (pass primitives ONLY)
    background_worker.delay(
        client_account_id=str(context.client_account_id),
        engagement_id=str(context.engagement_id),
        collection_flow_id=str(child_flow.id),  # UUID PK
        flow_id=str(child_flow.flow_id),  # Business UUID
        selected_gaps=selected_gaps
    )

    return {
        "status": "accepted",
        "message": "Gap analysis enqueued",
        "job_id": str(child_flow.id)
    }
```

### Progress Endpoint (Single Key Pattern)

**Endpoint**: `/api/v1/collection/flows/{flow_id}/gap-analysis/progress`

```python
@router.get("/{flow_id}/gap-analysis/progress")
async def get_gap_analysis_progress(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_context)
):
    """Get progress - reads single job key"""

    # Explicit repository with tenant scoping (per GPT5)
    repository = CollectionFlowRepository(
        db=db,
        client_account_id=context.client_account_id,
        engagement_id=context.engagement_id
    )

    # Resolve child flow from master flow_id (tenant-scoped)
    child_flow = await repository.get_by_master_flow_id(UUID(flow_id))
    if not child_flow:
        raise HTTPException(404, "Flow not found")

    # Explicit Redis manager (per GPT5)
    redis = get_redis_manager().client

    # Read single job key
    job_key = f"gap_enhancement_job:{child_flow.id}"
    job_state = await redis.get(job_key)

    if not job_state:
        return {"status": "not_started"}

    state = json.loads(job_state)

    # Map fields as-is (no transformation)
    return {
        "status": state.get("status"),
        "processed": state.get("processed", 0),
        "total": state.get("total", 0),
        "percentage": state.get("percentage", 0.0),
        "current_asset": state.get("current_asset"),
        "errors": state.get("errors", [])
    }
```

### Worker Pattern (Sequential Processing)

```python
async def gap_enhancement_worker(
    client_account_id: str,
    engagement_id: str,
    collection_flow_id: str,  # UUID PK
    flow_id: str,  # Business UUID
    selected_gaps: List[Dict]
):
    """Process gaps sequentially - no per-asset concurrency"""

    job_key = f"gap_enhancement_job:{collection_flow_id}"

    # Create fresh DB session (per GPT5 - not request scope)
    async with AsyncSessionLocal() as db:
        try:
            # Explicit Redis manager
            redis = get_redis_manager().client

            # Initialize job state
            await redis.setex(job_key, 3600, json.dumps({
                "status": "running",
                "processed": 0,
                "total": len(selected_gaps),
                "percentage": 0.0
            }))

            # Get persistent agent (reuse across all assets)
            agent = await TenantScopedAgentPool.get_or_create_agent(
                client_id=client_account_id,
                engagement_id=engagement_id,
                agent_type="gap_analysis_specialist"
            )

            # Process sequentially
            for idx, gap in enumerate(selected_gaps):
                # Enhance via agent
                enhanced = await agent.enhance_gap(gap)

                # Upsert to DB (atomic per asset)
                async with db.begin():
                    await upsert_gap(
                        db=db,
                        collection_flow_id=UUID(collection_flow_id),  # UUID PK
                        field_name=gap["field_name"],
                        gap_type=gap["gap_type"],
                        asset_id=UUID(gap["asset_id"]),  # UUID cast (per GPT5)
                        enhanced_data=enhanced
                    )

            # Update progress
            await redis.setex(job_key, 3600, json.dumps({
                "status": "running",
                "processed": idx + 1,
                "total": len(selected_gaps),
                "percentage": ((idx + 1) / len(selected_gaps)) * 100,
                "current_asset": gap.get("asset_name")
            }))

            # Mark complete
            await redis.setex(job_key, 3600, json.dumps({
                "status": "completed",
                "processed": len(selected_gaps),
                "total": len(selected_gaps),
                "percentage": 100.0
            }))

        except Exception as e:
            await redis.setex(job_key, 3600, json.dumps({
                "status": "failed",
                "error": str(e)
            }))
            raise
```

---

## Persistence (Minimal Pattern)

```python
async def upsert_gap(
    db: AsyncSession,  # Explicit session (per GPT5)
    collection_flow_id: UUID,  # UUID PK
    field_name: str,
    gap_type: str,
    asset_id: UUID,  # UUID type (per GPT5)
    enhanced_data: Dict
):
    """Upsert gap with composite unique constraint"""

    # Sanitize numeric fields
    confidence = enhanced_data.get("confidence_score")
    if confidence:
        confidence = max(0.0, min(1.0, float(confidence)))

    stmt = insert(CollectionDataGap).values(
        collection_flow_id=collection_flow_id,  # UUID PK
        field_name=field_name,
        gap_type=gap_type,
        asset_id=asset_id,  # UUID type
        gap_description=enhanced_data.get("description"),
        confidence_score=confidence,
        source_agent="gap_analysis_specialist"
    ).on_conflict_do_update(
        index_elements=["collection_flow_id", "field_name", "gap_type", "asset_id"],
        set_={
            "gap_description": enhanced_data.get("description"),
            "confidence_score": confidence,
            "updated_at": func.now()
        }
    )

    await db.execute(stmt)
```

---

## Frontend Alignment

**Per GPT5: Ensure frontend consistency**

1. **Progress Polling**: Frontend polls `/api/v1/collection/flows/{flow_id}/gap-analysis/progress`
2. **Row Selection**: UI posts only selected gaps (user selection from table)
3. **No SSE/WebSockets**: Use HTTP polling with 2-5s interval
4. **Status Display**: Map `processed/total/percentage/current_asset` directly to UI

---

## Testing (Minimal Set)

```python
@pytest.mark.asyncio
async def test_gap_analysis_e2e():
    """Submit selected gaps → 202; progress increments; DB has upserts; phase advanced"""

    # 1. Submit gaps
    response = await client.post(f"/api/v1/collection/flows/{flow_id}/analyze-gaps", json={
        "selected_gaps": [{"field_name": "app_name", "gap_type": "missing", "asset_id": "123"}]
    })
    assert response.status_code == 202

    # 2. Check progress increments
    await asyncio.sleep(1)
    progress = await client.get(f"/api/v1/collection/flows/{flow_id}/gap-analysis/progress")
    assert progress.json()["processed"] > 0

    # 3. Wait for completion
    await wait_for_job_completion(flow_id)

    # 4. Verify DB has upserts
    gaps = await db.execute(select(CollectionDataGap).where(
        CollectionDataGap.collection_flow_id == child_flow.id
    ))
    assert len(gaps.all()) == 1

    # 5. Verify phase advanced
    child_flow = await repository.get_by_id(child_flow.id)
    assert child_flow.current_phase == "questionnaire_generation"


@pytest.mark.asyncio
async def test_gap_limit():
    """Submit >200 gaps → 400"""
    response = await client.post(f"/api/v1/collection/flows/{flow_id}/analyze-gaps", json={
        "selected_gaps": [{"field_name": f"field_{i}"} for i in range(201)]
    })
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_job_idempotency():
    """Second submission while job running → 409"""
    await client.post(f"/api/v1/collection/flows/{flow_id}/analyze-gaps", json={
        "selected_gaps": [{"field_name": "app_name"}]
    })

    response = await client.post(f"/api/v1/collection/flows/{flow_id}/analyze-gaps", json={
        "selected_gaps": [{"field_name": "app_name"}]
    })
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_rerun_no_duplicates():
    """Rerun same selection after completion → no duplicates"""
    await submit_and_wait([{"field_name": "app_name", "asset_id": "123"}])
    await submit_and_wait([{"field_name": "app_name", "asset_id": "123"}])

    gaps = await db.execute(select(CollectionDataGap))
    assert len(gaps.all()) == 1  # Upsert, not duplicate
```

---

## What's Removed (Complexity Elimination)

- ❌ Deprecation shims/windows
- ❌ Feature flags
- ❌ SSE/WebSockets
- ❌ Cancel endpoint
- ❌ Per-asset concurrency
- ❌ Secondary progress keys
- ❌ Passing RequestContext to background tasks
- ❌ Extra orchestration layers
- ❌ Separate idempotency endpoints

---

## Implementation Checklist

- [ ] Phase 1: Create CollectionChildFlowService
- [ ] Update `__init__.py` to export service
- [ ] Phase 2: Update collection_flow_config.py (remove crew_class, add child_flow_service)
- [ ] Delete UnifiedCollectionFlow.py immediately
- [ ] Revert GapAnalysisAgent placeholder
- [ ] Phase 3: Update MFO resume logic (single path only)
- [ ] Update all service signatures to use UUID for collection_flow_id
- [ ] Update background job to pass primitives only
- [ ] Implement single job key pattern for progress
- [ ] Add minimal test suite (4 tests)
- [ ] Verify no crew_class references remain
- [ ] Commit and test E2E

---

## Files Modified

**New (1)**:
- `backend/app/services/child_flow_services/collection.py`

**Modified (3)**:
- `backend/app/services/child_flow_services/__init__.py`
- `backend/app/services/flow_configs/collection_flow_config.py`
- `backend/app/services/master_flow_orchestrator/operations/lifecycle_commands.py`

**Deleted (2)**:
- `backend/app/services/crewai_flows/unified_collection_flow.py`
- `backend/app/services/ai_analysis/gap_analysis_agent.py` (revert)

**Total**: +200 lines, -150 lines = +50 net

---

## Success Criteria

- [ ] Collection flows create successfully
- [ ] Resume uses child_flow_service (no crew_class)
- [ ] Gap analysis uses persistent agents
- [ ] Background jobs work with primitives only
- [ ] Progress endpoint reads single job key
- [ ] Phase auto-progression works
- [ ] All 4 tests pass
- [ ] No crew_class warnings in logs

**Simplified. Elegant. Complete.** ✅
